"""
config.py — Central configuration for Guess the Song.

All tuneable knobs live here so other modules never hard-code values.
"""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class GameConfig:
    # ── Round settings ─────────────────────────────────────────────────────
    total_rounds: int = 5
    round_timeout_seconds: int = 10        # how long the player has to guess
    audio_clip_seconds: float = 8.0        # how many seconds of preview to play

    # ── Scoring ────────────────────────────────────────────────────────────
    points_correct_title: int = 100
    points_correct_artist: int = 50        # bonus on top of title points
    points_timeout: int = 0

    # ── Matching ───────────────────────────────────────────────────────────
    partial_match_enabled: bool = True     # allow partial title match
    partial_match_threshold: float = 0.6   # minimum similarity ratio (0–1)

    # ── Spotify ────────────────────────────────────────────────────────────
    spotify_client_id: str = field(
        default_factory=lambda: os.getenv("SPOTIPY_CLIENT_ID", "")
    )
    spotify_client_secret: str = field(
        default_factory=lambda: os.getenv("SPOTIPY_CLIENT_SECRET", "")
    )
    spotify_redirect_uri: str = field(
        default_factory=lambda: os.getenv(
            "SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback"
        )
    )

    # Artist names used to source tracks via GET /artists/{id}/top-tracks.
    # No playlists, no Premium required — artist search is free-tier safe.
    # Add or remove names freely; the service resolves them to Spotify IDs at runtime.
    spotify_artists: List[str] = field(default_factory=lambda: [
        "Daft Punk", "Coldplay", "Adele", "The Weeknd", "Imagine Dragons",
        "Ed Sheeran", "Billie Eilish", "Ariana Grande", "Drake", "Taylor Swift",
        "Post Malone", "Eminem", "Rihanna", "Beyoncé", "Bruno Mars",
        "Lady Gaga", "Kendrick Lamar", "Dua Lipa", "Arctic Monkeys", "Queen",
    ])

    # ── Audio ──────────────────────────────────────────────────────────────
    audio_backend: str = "pygame"          # "pygame" | "simpleaudio" | "auto"

    # ── UI ─────────────────────────────────────────────────────────────────
    show_artist_prompt: bool = True        # ask for artist after title guess
    difficulty: str = "normal"            # "easy" | "normal" | "hard"

    def apply_difficulty(self) -> None:
        """Adjust settings based on difficulty."""
        if self.difficulty == "easy":
            self.audio_clip_seconds = 15.0
            self.round_timeout_seconds = 20
            self.partial_match_enabled = True
        elif self.difficulty == "hard":
            self.audio_clip_seconds = 3.0
            self.round_timeout_seconds = 7
            self.partial_match_enabled = False
