"""
audio_player.py — Cross-platform audio playback module.

Responsibilities:
  - Downloading a preview URL to a temp file
  - Playing only the first N seconds of that clip
  - Stopping playback cleanly
  - Abstracting away the backend (pygame vs simpleaudio)

Backend selection order (when config.audio_backend == "auto"):
  1. pygame  — best cross-platform support, handles MP3 natively
  2. simpleaudio — lightweight, no MP3 natively (needs pydub + ffmpeg)
"""

import io
import logging
import tempfile
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class AudioError(Exception):
    """Raised for any audio playback problem."""


# ── Abstract base ──────────────────────────────────────────────────────────

class _BasePlayer(ABC):
    """Interface every backend must implement."""

    @abstractmethod
    def play(self, filepath: str, duration_seconds: float) -> None:
        """Start playing `filepath`, stopping after `duration_seconds`."""

    @abstractmethod
    def stop(self) -> None:
        """Immediately stop playback."""

    @abstractmethod
    def is_playing(self) -> bool:
        """Return True while audio is active."""

    def cleanup(self) -> None:
        """Optional cleanup hook (called on game exit)."""


# ── pygame backend ─────────────────────────────────────────────────────────

class _PygamePlayer(_BasePlayer):
    """
    Uses pygame.mixer for MP3/OGG playback.
    pygame must be installed: pip install pygame
    """

    def __init__(self) -> None:
        try:
            import pygame
            self._pygame = pygame
        except ImportError as exc:
            raise AudioError(
                "pygame not installed. Run: pip install pygame"
            ) from exc

        if not pygame.get_init():
            pygame.init()
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def play(self, filepath: str, duration_seconds: float) -> None:
        self.stop()  # ensure nothing else is playing
        self._stop_event.clear()

        try:
            self._pygame.mixer.music.load(filepath)
            self._pygame.mixer.music.play()
        except self._pygame.error as exc:
            raise AudioError(f"pygame could not play file: {exc}") from exc

        # Spin up a watcher thread that stops music after `duration_seconds`
        def _watcher() -> None:
            deadline = time.monotonic() + duration_seconds
            while time.monotonic() < deadline:
                if self._stop_event.is_set():
                    break
                if not self._pygame.mixer.music.get_busy():
                    break
                time.sleep(0.05)
            self._pygame.mixer.music.stop()
            self._stop_event.set()

        self._thread = threading.Thread(target=_watcher, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._pygame.mixer.get_init():
            self._pygame.mixer.music.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def is_playing(self) -> bool:
        if not self._pygame.mixer.get_init():
            return False
        return self._pygame.mixer.music.get_busy()

    def cleanup(self) -> None:
        self.stop()
        self._pygame.mixer.quit()


# ── simpleaudio + pydub backend ────────────────────────────────────────────

class _SimpleAudioPlayer(_BasePlayer):
    """
    Uses simpleaudio for WAV playback and pydub+ffmpeg for MP3 decoding.
    Requires: pip install simpleaudio pydub
    And ffmpeg on PATH for MP3 support.
    """

    def __init__(self) -> None:
        try:
            import simpleaudio as sa
            self._sa = sa
        except ImportError as exc:
            raise AudioError(
                "simpleaudio not installed. Run: pip install simpleaudio"
            ) from exc
        try:
            from pydub import AudioSegment
            self._AudioSegment = AudioSegment
        except ImportError as exc:
            raise AudioError(
                "pydub not installed. Run: pip install pydub"
            ) from exc

        self._play_obj = None
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def play(self, filepath: str, duration_seconds: float) -> None:
        self.stop()
        self._stop_event.clear()

        try:
            segment = self._AudioSegment.from_file(filepath)
            clip_ms = int(duration_seconds * 1000)
            clip = segment[:clip_ms]

            # Convert to raw PCM
            raw = clip.raw_data
            sample_rate = clip.frame_rate
            num_channels = clip.channels
            bytes_per_sample = clip.sample_width

            self._play_obj = self._sa.play_buffer(
                raw, num_channels, bytes_per_sample, sample_rate
            )
        except Exception as exc:
            raise AudioError(f"simpleaudio playback failed: {exc}") from exc

        def _watcher() -> None:
            deadline = time.monotonic() + duration_seconds + 1
            while time.monotonic() < deadline:
                if self._stop_event.is_set():
                    break
                if self._play_obj and not self._play_obj.is_playing():
                    break
                time.sleep(0.05)
            if self._play_obj:
                self._play_obj.stop()
            self._stop_event.set()

        self._thread = threading.Thread(target=_watcher, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._play_obj:
            self._play_obj.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def is_playing(self) -> bool:
        return bool(self._play_obj and self._play_obj.is_playing())

    def cleanup(self) -> None:
        self.stop()


# ── Factory + public facade ────────────────────────────────────────────────

def _create_backend(preference: str) -> _BasePlayer:
    """Instantiate the requested backend, falling back gracefully."""
    order = (
        ["pygame", "simpleaudio"]
        if preference == "auto"
        else [preference]
    )
    last_error: Optional[Exception] = None
    for name in order:
        try:
            if name == "pygame":
                return _PygamePlayer()
            if name == "simpleaudio":
                return _SimpleAudioPlayer()
        except AudioError as exc:
            last_error = exc
            logger.warning("Backend '%s' unavailable: %s", name, exc)
    raise AudioError(
        f"No audio backend available. Last error: {last_error}"
    )


class AudioPlayer:
    """
    Public interface used by GameEngine.

    Example usage:
        player = AudioPlayer(backend="pygame")
        player.load_and_play(preview_url, clip_seconds=8)
        player.wait_until_done()
        player.stop()
    """

    def __init__(self, backend: str = "pygame") -> None:
        self._backend = _create_backend(backend)
        self._tmp_file: Optional[str] = None

    # ── Download helper ────────────────────────────────────────────────────

    def _download_preview(self, url: str) -> str:
        """Download audio to a temp file, return its path."""
        logger.debug("Downloading preview: %s", url)
        try:
            resp = requests.get(url, timeout=15, stream=True)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise AudioError(f"Failed to download preview: {exc}") from exc

        suffix = ".mp3" if "mp3" in url.lower() else ".ogg"
        tmp = tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, prefix="gts_preview_"
        )
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.flush()
        tmp.close()
        logger.debug("Preview saved to %s", tmp.name)
        return tmp.name

    # ── Public methods ─────────────────────────────────────────────────────

    def load_and_play(self, url: str, clip_seconds: float = 8.0) -> None:
        """
        Download `url` and immediately start playing up to `clip_seconds`.
        Non-blocking — returns while audio plays in background.
        """
        self._tmp_file = self._download_preview(url)
        self._backend.play(self._tmp_file, clip_seconds)

    def stop(self) -> None:
        """Stop playback immediately."""
        self._backend.stop()

    def is_playing(self) -> bool:
        return self._backend.is_playing()

    def wait_until_done(self) -> None:
        """Block until clip finishes naturally."""
        while self.is_playing():
            time.sleep(0.05)

    def cleanup(self) -> None:
        """Release resources (call on game exit)."""
        self._backend.cleanup()
        if self._tmp_file:
            import os
            try:
                os.unlink(self._tmp_file)
            except OSError:
                pass
