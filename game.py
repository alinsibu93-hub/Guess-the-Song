"""
game.py — In-memory game session management and guess-matching logic.

Supports two answer modes:
  multiple_choice — client sends choiceIndex (0-based)
  free_text       — client sends title + artist strings
"""

import difflib
import re
import threading
import time
import uuid
from typing import Dict, List, Optional

_SESSION_TTL_SECONDS = 3600  # sessions expire after 1 hour of inactivity
_EVICT_INTERVAL = 300        # minimum seconds between eviction sweeps


# ── Matching helpers (free_text mode) ─────────────────────────────────────

# Common words that shouldn't count as a meaningful artist-name match.
_STOP_WORDS = frozenset({"the", "a", "an", "of", "in", "and", "or", "ft", "feat"})


def _normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def _title_matches(guess: str, correct: str, partial: bool, threshold: float) -> bool:
    g, c = _normalize(guess), _normalize(correct)
    if not g:
        return False
    if g == c:
        return True
    if partial:
        return difflib.SequenceMatcher(None, g, c).ratio() >= threshold
    return False


def _artist_matches(guess: str, correct: str) -> bool:
    g_words = set(_normalize(guess).split())
    c_words = set(_normalize(correct).split())
    # Include 2-char names like "Ed"; exclude common stop words.
    meaningful = {w for w in g_words if len(w) >= 2 and w not in _STOP_WORDS}
    return bool(meaningful & c_words)


# ── Session ────────────────────────────────────────────────────────────────


class ChoiceIndexError(ValueError):
    pass


class WrongModeError(ValueError):
    pass


class EmptyGuessError(ValueError):
    pass


class GameSession:
    def __init__(self, rounds: List[dict], config: dict):
        self.session_id = str(uuid.uuid4())
        self.rounds = rounds
        self.config = config
        self.current_round = 0
        self.score = 0
        self.results: List[dict] = []
        self._last_active = time.monotonic()

    @property
    def mode(self) -> str:
        return self.config.get("mode", "multiple_choice")

    @property
    def is_complete(self) -> bool:
        return self.current_round >= len(self.rounds)

    def get_current_round_data(self) -> Optional[dict]:
        """Return public round data — title/artist never exposed before answer."""
        if self.is_complete:
            return None
        r = self.rounds[self.current_round]
        data: dict = {
            "finished": False,
            "roundNumber": self.current_round + 1,
            "totalRounds": len(self.rounds),
            "videoId": r["videoId"],
            "startTime": r["startTime"],
            "duration": r["duration"],
            "thumbnail": r.get("thumbnail"),
            "mode": self.mode,
        }
        if self.mode == "multiple_choice":
            data["choices"] = r.get("choices", [])
        return data

    def submit_answer(
        self,
        title_guess: str = "",
        artist_guess: str = "",
        choice_index: int = -1,
    ) -> dict:
        """
        Evaluate the player's answer for the current round.

        multiple_choice mode: pass choice_index (0-based index into choices list).
        free_text mode:       pass title_guess and optionally artist_guess.

        Raises:
          ValueError       — game is already complete
          ChoiceIndexError — choice_index out of range
          WrongModeError   — answer mode doesn't match session mode
        """
        if self.is_complete:
            raise ValueError("Game is already complete.")

        self._last_active = time.monotonic()

        r = self.rounds[self.current_round]
        partial = self.config.get("partialMatch", True)
        threshold = self.config.get("partialMatchThreshold", 0.6)
        pts_title = self.config.get("pointsTitle", 100)
        pts_artist = self.config.get("pointsArtist", 50)

        if self.mode == "multiple_choice":
            if choice_index < 0:
                raise WrongModeError(
                    "Session is in multiple_choice mode. Send { \"choiceIndex\": N }."
                )
            choices = r.get("choices", [])
            if choice_index >= len(choices):
                raise ChoiceIndexError(
                    f"choiceIndex {choice_index} is out of range "
                    f"(valid: 0–{len(choices) - 1})."
                )
            chosen = choices[choice_index]
            # MC: one choice covers both title and artist — all-or-nothing
            title_correct = _normalize(chosen["title"]) == _normalize(r["title"])
            artist_correct = _normalize(chosen["artist"]) == _normalize(r["artist"])
        else:
            # free_text mode
            if choice_index >= 0:
                raise WrongModeError(
                    "Session is in free_text mode. Send { \"title\": \"...\", \"artist\": \"...\" }."
                )
            if not title_guess:
                raise EmptyGuessError("'title' is required in free_text mode.")
            title_correct = _title_matches(title_guess, r["title"], partial, threshold)
            artist_correct = _artist_matches(artist_guess, r["artist"])

        points = 0
        if title_correct:
            points += pts_title
        if artist_correct:
            points += pts_artist

        self.score += points
        result = {
            "roundNumber": self.current_round + 1,
            "titleCorrect": title_correct,
            "artistCorrect": artist_correct,
            "correctTitle": r["title"],
            "correctArtist": r["artist"],
            "videoId": r["videoId"],
            "pointsEarned": points,
            "totalScore": self.score,
        }
        self.results.append(result)
        self.current_round += 1
        return result

    def get_final_results(self) -> dict:
        return {
            "sessionId": self.session_id,
            "totalScore": self.score,
            "totalRounds": len(self.rounds),
            "maxPossibleScore": len(self.rounds) * (
                self.config.get("pointsTitle", 100) + self.config.get("pointsArtist", 50)
            ),
            "rounds": self.results,
        }


# ── Session store ──────────────────────────────────────────────────────────

_sessions: Dict[str, GameSession] = {}
_lock = threading.Lock()
_last_evict: float = 0.0  # monotonic timestamp of the last eviction sweep


def create_session(rounds: List[dict], config: dict) -> GameSession:
    session = GameSession(rounds, config)
    with _lock:
        _evict_expired_locked()
        _sessions[session.session_id] = session
    return session


def get_session(session_id: str) -> Optional[GameSession]:
    with _lock:
        _maybe_evict_locked()
        session = _sessions.get(session_id)
        if session is not None:
            session._last_active = time.monotonic()
    return session


def _evict_expired_locked() -> None:
    """Remove stale sessions. Caller must hold _lock."""
    global _last_evict
    now = time.monotonic()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s._last_active > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _sessions[sid]
    _last_evict = now


def _maybe_evict_locked() -> None:
    """Run eviction only if _EVICT_INTERVAL seconds have elapsed. Caller must hold _lock."""
    if time.monotonic() - _last_evict >= _EVICT_INTERVAL:
        _evict_expired_locked()
