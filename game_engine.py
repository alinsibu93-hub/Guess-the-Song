"""
game_engine.py — Core game loop and scoring.

GameEngine orchestrates:
  - SpotifyService  (track fetching)
  - AudioPlayer     (preview playback)
  - GameTimer       (per-round countdown)
  - ui              (all terminal output)

It is intentionally free of I/O concerns except for reading stdin via
the _read_input helper, which can be monkey-patched in tests.
"""

import difflib
import logging
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from config import GameConfig
from spotify_service import SpotifyService, TrackInfo, SpotifyFetchError
from audio_player import AudioPlayer, AudioError
from game_timer import GameTimer
import ui

logger = logging.getLogger(__name__)


# ── Data classes ───────────────────────────────────────────────────────────

@dataclass
class RoundResult:
    round_num: int
    track: TrackInfo
    user_title_guess: str
    user_artist_guess: str
    title_correct: bool
    artist_correct: bool
    timed_out: bool
    time_taken: float          # seconds from prompt to answer (0 if timed out)
    points_earned: int


@dataclass
class GameSession:
    config: GameConfig
    rounds: List[RoundResult] = field(default_factory=list)
    total_score: int = 0

    def add_result(self, result: RoundResult) -> None:
        self.rounds.append(result)
        self.total_score += result.points_earned

    def scoreboard_rows(self) -> list:
        return [
            {
                "round": r.round_num,
                "title": r.track.title,
                "correct": r.title_correct,
                "points": r.points_earned,
            }
            for r in self.rounds
        ]


# ── Matching helpers ───────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip punctuation edges."""
    return text.lower().strip(" .,!?-\"'")


def _title_matches(guess: str, correct: str, partial: bool, threshold: float) -> bool:
    """Return True if guess matches the correct title."""
    g = _normalize(guess)
    c = _normalize(correct)
    if g == c:
        return True
    if not g:
        return False
    if partial:
        ratio = difflib.SequenceMatcher(None, g, c).ratio()
        return ratio >= threshold
    return False


def _artist_matches(guess: str, correct: str) -> bool:
    """Lenient artist match: any significant word overlap."""
    g_words = set(_normalize(guess).split())
    c_words = set(_normalize(correct).split())
    if not g_words:
        return False
    common = g_words & c_words
    # Match if at least one non-trivial word (>2 chars) matches
    return any(len(w) > 2 for w in common)


# ── Input reading (non-blocking with timeout) ──────────────────────────────

class _TimedInput:
    """
    Read a line from stdin within a deadline.

    Works by running input() in a daemon thread. The main thread polls
    until the answer arrives or the timer expires.
    """

    def __init__(self) -> None:
        self._result: Optional[str] = None
        self._ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._result = None
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._read, daemon=True, name="InputThread"
        )
        self._thread.start()

    def _read(self) -> None:
        try:
            line = sys.stdin.readline()
            self._result = line.rstrip("\n")
        except EOFError:
            self._result = ""
        self._ready.set()

    def get(self, timeout: float) -> Optional[str]:
        """
        Wait up to `timeout` seconds for input.
        Returns the string, or None on timeout.
        """
        if self._ready.wait(timeout=timeout):
            return self._result
        return None

    def is_ready(self) -> bool:
        return self._ready.is_set()


# ── Game Engine ────────────────────────────────────────────────────────────

class GameEngine:
    """
    Drives the full game loop.

    Usage:
        engine = GameEngine(config)
        engine.run()
    """

    def __init__(self, config: GameConfig) -> None:
        self._cfg = config
        self._spotify = SpotifyService(
            config.spotify_client_id, config.spotify_client_secret
        )
        self._audio = AudioPlayer(backend=config.audio_backend)
        self._session: Optional[GameSession] = None

    # ── Public entry point ─────────────────────────────────────────────────

    def run(self) -> None:
        """Full game lifecycle: welcome → rounds → scoreboard."""
        self._session = GameSession(config=self._cfg)

        ui.show_welcome(self._cfg.difficulty, self._cfg.total_rounds)

        # Pre-fetch all tracks up front so we don't pause between rounds
        ui.section("Fetching tracks from Spotify…")
        try:
            tracks = self._spotify.fetch_rounds(
                self._cfg.spotify_artists, self._cfg.total_rounds
            )
        except SpotifyFetchError as exc:
            print(ui.red(f"\n  Error fetching tracks: {exc}"))
            print(ui.dim("  Check your credentials and internet connection."))
            return

        print(f"  {ui.green('✓')} Found {len(tracks)} tracks. Let's go!\n")

        for i, track in enumerate(tracks, start=1):
            result = self._play_round(i, track)
            self._session.add_result(result)
            time.sleep(1.0)   # brief pause between rounds

        ui.show_final_scoreboard(
            self._session.scoreboard_rows(),
            self._session.total_score,
            self._cfg.total_rounds,
        )
        self._audio.cleanup()

    # ── Round logic ────────────────────────────────────────────────────────

    def _play_round(self, round_num: int, track: TrackInfo) -> RoundResult:
        ui.show_round_header(round_num, self._cfg.total_rounds, self._session.total_score)

        # --- Play audio clip ---
        try:
            self._audio.load_and_play(track.preview_url, self._cfg.audio_clip_seconds)
        except AudioError as exc:
            print(ui.red(f"\n  Audio error: {exc}"))
            print(ui.dim("  Skipping audio — you can still guess!"))

        ui.show_playing(self._cfg.audio_clip_seconds, self._cfg.round_timeout_seconds)

        # --- Start timer ---
        timer = GameTimer(duration=float(self._cfg.round_timeout_seconds))
        timed_input = _TimedInput()

        print(f"  {ui.bold('Your guess (song title):')} ", end="", flush=True)
        timed_input.start()
        timer.start()
        round_start = time.monotonic()

        # Poll for input or expiry, updating the timer display
        guess: Optional[str] = None
        while not timer.is_expired:
            if timed_input.is_ready():
                guess = timed_input.get(timeout=0)
                break
            ui.show_timer_warning(timer.time_remaining)
            time.sleep(0.1)

        ui.clear_timer_line()
        timer.stop()
        self._audio.stop()

        timed_out = guess is None
        time_taken = time.monotonic() - round_start if not timed_out else 0.0
        title_guess = guess or ""

        # --- Evaluate title ---
        title_correct = _title_matches(
            title_guess,
            track.title,
            self._cfg.partial_match_enabled,
            self._cfg.partial_match_threshold,
        )

        # --- Artist guess (if title was correct and feature is on) ---
        artist_guess = ""
        artist_correct = False

        if title_correct and self._cfg.show_artist_prompt and not timed_out:
            print(f"  {ui.bold('Artist name (optional):')} ", end="", flush=True)
            try:
                artist_guess = input().strip()
            except (EOFError, KeyboardInterrupt):
                artist_guess = ""
            artist_correct = _artist_matches(artist_guess, track.artist)

        # --- Score ---
        if timed_out or not title_correct:
            points = self._cfg.points_timeout
        else:
            points = self._cfg.points_correct_title
            if artist_correct:
                points += self._cfg.points_correct_artist

        # --- Feedback ---
        ui.show_result(
            correct=title_correct,
            title_match=title_correct,
            artist_match=artist_correct,
            correct_title=track.title,
            correct_artist=track.artist,
            points_earned=points,
            timed_out=timed_out,
            time_taken=time_taken if not timed_out else None,
        )
        ui.show_score_update(self._session.total_score + points, points)

        # Hint: show album as a teaser for the next round
        if not title_correct and not timed_out:
            ui.show_hint(f"Album: {track.album}")

        input(ui.dim("\n  Press ENTER for next round…"))

        return RoundResult(
            round_num=round_num,
            track=track,
            user_title_guess=title_guess,
            user_artist_guess=artist_guess,
            title_correct=title_correct,
            artist_correct=artist_correct,
            timed_out=timed_out,
            time_taken=time_taken,
            points_earned=points,
        )
