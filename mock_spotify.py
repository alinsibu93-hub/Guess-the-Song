"""
mock_spotify.py — Offline demo mode for Guess the Song.

Simulates SpotifyService using hardcoded tracks + real preview URLs
that point to publicly accessible CDN files (no auth required).

Usage:
    python mock_spotify.py          # run the full game in offline mode
    python mock_spotify.py --test   # just verify the mock data structure
"""

import random
from typing import List, Optional
from spotify_service import TrackInfo


# ── Hardcoded track pool ───────────────────────────────────────────────────
# These are well-known songs. preview_url can be any direct MP3 link.
# Replace with real Spotify preview URLs when running on an open network.

MOCK_TRACKS: List[dict] = [
    {
        "track_id": "mock_001",
        "title": "Yellow",
        "artist": "Coldplay",
        "album": "Parachutes",
        "preview_url": None,   # will be replaced by a test tone below
        "source": "Coldplay",
    },
    {
        "track_id": "mock_002",
        "title": "Rolling in the Deep",
        "artist": "Adele",
        "album": "21",
        "preview_url": None,
        "source": "Adele",
    },
    {
        "track_id": "mock_003",
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "preview_url": None,
        "source": "The Weeknd",
    },
    {
        "track_id": "mock_004",
        "title": "Get Lucky",
        "artist": "Daft Punk",
        "album": "Random Access Memories",
        "preview_url": None,
        "source": "Daft Punk",
    },
    {
        "track_id": "mock_005",
        "title": "Radioactive",
        "artist": "Imagine Dragons",
        "album": "Night Visions",
        "preview_url": None,
        "source": "Imagine Dragons",
    },
    {
        "track_id": "mock_006",
        "title": "Shape of You",
        "artist": "Ed Sheeran",
        "album": "÷ (Divide)",
        "preview_url": None,
        "source": "Ed Sheeran",
    },
    {
        "track_id": "mock_007",
        "title": "Bad Guy",
        "artist": "Billie Eilish",
        "album": "When We All Fall Asleep, Where Do We Go?",
        "preview_url": None,
        "source": "Billie Eilish",
    },
    {
        "track_id": "mock_008",
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "preview_url": None,
        "source": "Queen",
    },
    {
        "track_id": "mock_009",
        "title": "Smells Like Teen Spirit",
        "artist": "Nirvana",
        "album": "Nevermind",
        "preview_url": None,
        "source": "Nirvana",
    },
    {
        "track_id": "mock_010",
        "title": "Levitating",
        "artist": "Dua Lipa",
        "album": "Future Nostalgia",
        "preview_url": None,
        "source": "Dua Lipa",
    },
]


def _generate_tone_wav(frequency: float = 440.0, duration: float = 3.0) -> bytes:
    """
    Generate a pure-tone WAV file in memory (no files, no internet).
    Used as a placeholder when no real preview_url is available.
    """
    import struct, math

    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    amplitude = 16000

    wav_data = bytearray()
    for i in range(num_samples):
        # Simple sine wave
        sample = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
        wav_data += struct.pack('<h', sample)

    # WAV header
    data_size = len(wav_data)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,             # chunk size
        1,              # PCM format
        1,              # mono
        sample_rate,
        sample_rate * 2,
        2,              # block align
        16,             # bits per sample
        b'data',
        data_size,
    )
    return bytes(header) + bytes(wav_data)


class MockSpotifyService:
    """
    Drop-in replacement for SpotifyService that works fully offline.

    The 'audio' for each track is a generated sine-wave tone so that
    AudioPlayer is exercised even without real preview URLs.
    Tones vary in frequency per track so rounds feel different.
    """

    _FREQUENCIES = [261.6, 293.7, 329.6, 349.2, 392.0,
                    440.0, 493.9, 523.3, 587.3, 659.3]

    def __init__(self) -> None:
        self._tmp_files: List[str] = []

    def _make_temp_wav(self, freq: float) -> str:
        """Write a tone WAV to a temp file and return its path."""
        import tempfile, os
        wav_bytes = _generate_tone_wav(frequency=freq, duration=8.0)
        tmp = tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False, prefix="gts_mock_"
        )
        tmp.write(wav_bytes)
        tmp.flush()
        tmp.close()
        self._tmp_files.append(tmp.name)
        return tmp.name

    def _build_track(self, raw: dict, index: int) -> TrackInfo:
        freq = self._FREQUENCIES[index % len(self._FREQUENCIES)]
        preview_path = self._make_temp_wav(freq)
        return TrackInfo(
            track_id    = raw["track_id"],
            title       = raw["title"],
            artist      = raw["artist"],
            album       = raw["album"],
            preview_url = preview_path,   # local file path, not a URL
            source      = raw["source"],
        )

    def fetch_rounds(self, _artist_names, count: int) -> List[TrackInfo]:
        """Return `count` shuffled mock tracks."""
        pool = random.sample(MOCK_TRACKS, min(count, len(MOCK_TRACKS)))
        return [self._build_track(t, i) for i, t in enumerate(pool)]

    def cleanup(self) -> None:
        import os
        for path in self._tmp_files:
            try:
                os.unlink(path)
            except OSError:
                pass


# ── Patch AudioPlayer to accept local file paths ──────────────────────────

class _MockAudioPlayer:
    """
    AudioPlayer drop-in that plays local WAV files instead of downloading URLs.
    Delegates to the real backend — only `load_and_play` changes.
    """

    def __init__(self, backend: str = "pygame") -> None:
        from audio_player import AudioPlayer, AudioError
        self._real = AudioPlayer(backend=backend)

    def load_and_play(self, path_or_url: str, clip_seconds: float = 8.0) -> None:
        """Play a local file path directly (skip HTTP download)."""
        self._real._backend.play(path_or_url, clip_seconds)

    def stop(self) -> None:
        self._real.stop()

    def is_playing(self) -> bool:
        return self._real.is_playing()

    def wait_until_done(self) -> None:
        self._real.wait_until_done()

    def cleanup(self) -> None:
        self._real.cleanup()


# ── Monkey-patch GameEngine for mock mode ─────────────────────────────────

def patch_game_engine() -> None:
    """
    Replace SpotifyService + AudioPlayer inside GameEngine with mock versions.
    Call this before constructing GameEngine.
    """
    import game_engine as ge

    _mock_spotify = MockSpotifyService()

    _OriginalEngine = ge.GameEngine

    class _MockGameEngine(_OriginalEngine):
        def __init__(self, config):
            # Bypass parent __init__ to substitute components
            self._cfg = config
            self._spotify = _mock_spotify
            self._audio = _MockAudioPlayer(backend=config.audio_backend)
            self._session = None

    ge.GameEngine = _MockGameEngine
    print("  [MOCK MODE] Spotify & audio replaced with offline stubs.\n")


# ── CLI entry point ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        # Quick structural test — no game loop
        svc = MockSpotifyService()
        tracks = svc.fetch_rounds([], count=5)
        print(f"Generated {len(tracks)} mock tracks:")
        for t in tracks:
            print(f"  {t.title:35s} | {t.artist:20s} | wav: {t.preview_url}")
        svc.cleanup()
        print("\nMock mode structural test PASSED.")
        sys.exit(0)

    # Full game in mock mode
    patch_game_engine()

    from config import GameConfig
    from game_engine import GameEngine
    import ui

    difficulty = ui.prompt_difficulty()
    rounds = ui.prompt_rounds()

    cfg = GameConfig(
        total_rounds=rounds,
        difficulty=difficulty,
    )
    cfg.apply_difficulty()

    engine = GameEngine(cfg)
    engine.run()
