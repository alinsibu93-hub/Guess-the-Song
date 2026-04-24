"""
config.py — Central configuration for Guess the Song.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class GameConfig:
    # Audio source is iTunes Search API — no auth / API key required.
    # (Previously used YouTube Data API v3; removed 2024-04 due to
    # Chrome autoplay policy breaking playback reliability.)

    # ── Round settings ─────────────────────────────────────────────────────
    # total_rounds is intentionally absent — the client chooses it per-game (1-20).
    round_timeout_seconds: int = 10  # overridden by apply_difficulty()
    clip_duration_seconds: int = 8   # overridden by apply_difficulty()

    # ── Scoring ────────────────────────────────────────────────────────────
    points_correct_title: int = 100
    points_correct_artist: int = 50

    # ── Game mode ──────────────────────────────────────────────────────────
    choices_count: int = 4  # options presented in multiple_choice mode

    # ── Matching (free_text mode only) ─────────────────────────────────────
    partial_match_enabled: bool = True
    partial_match_threshold: float = 0.6

    # ── Song library ───────────────────────────────────────────────────────
    # Known (artist, title) pairs used to query iTunes Search API.
    # Exact titles ensure the scoring logic knows the canonical answer.
    song_library: List[Tuple[str, str]] = field(default_factory=lambda: [
        ("Daft Punk", "Get Lucky"),
        ("Daft Punk", "One More Time"),
        ("Coldplay", "Yellow"),
        ("Coldplay", "The Scientist"),
        ("Adele", "Rolling in the Deep"),
        ("Adele", "Hello"),
        ("The Weeknd", "Blinding Lights"),
        ("The Weeknd", "Starboy"),
        ("Imagine Dragons", "Believer"),
        ("Imagine Dragons", "Radioactive"),
        ("Ed Sheeran", "Shape of You"),
        ("Ed Sheeran", "Thinking Out Loud"),
        ("Billie Eilish", "bad guy"),
        ("Billie Eilish", "Happier Than Ever"),
        ("Ariana Grande", "thank u, next"),
        ("Ariana Grande", "7 rings"),
        ("Drake", "God's Plan"),
        ("Drake", "One Dance"),
        ("Taylor Swift", "Anti-Hero"),
        ("Taylor Swift", "Shake It Off"),
        ("Post Malone", "Circles"),
        ("Post Malone", "Rockstar"),
        ("Eminem", "Lose Yourself"),
        ("Eminem", "Not Afraid"),
        ("Rihanna", "Umbrella"),
        ("Rihanna", "We Found Love"),
        ("Beyoncé", "Halo"),
        ("Beyoncé", "Crazy in Love"),
        ("Bruno Mars", "Uptown Funk"),
        ("Bruno Mars", "Just the Way You Are"),
        ("Lady Gaga", "Bad Romance"),
        ("Lady Gaga", "Poker Face"),
        ("Kendrick Lamar", "HUMBLE."),
        ("Kendrick Lamar", "DNA."),
        ("Dua Lipa", "Levitating"),
        ("Dua Lipa", "Don't Start Now"),
        ("Arctic Monkeys", "Do I Wanna Know?"),
        ("Arctic Monkeys", "R U Mine?"),
        ("Queen", "Bohemian Rhapsody"),
        ("Queen", "Don't Stop Me Now"),
    ])

    def apply_difficulty(self, difficulty: str = "normal") -> None:
        if difficulty == "easy":
            self.clip_duration_seconds = 15
            self.round_timeout_seconds = 20
            self.partial_match_enabled = True
        elif difficulty == "hard":
            self.clip_duration_seconds = 3
            self.round_timeout_seconds = 7
            self.partial_match_enabled = False
        else:
            self.clip_duration_seconds = 8
            self.round_timeout_seconds = 10
            self.partial_match_enabled = True
