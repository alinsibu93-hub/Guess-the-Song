"""
game_timer.py — Non-blocking countdown timer for each game round.

Design:
  - Runs in a daemon thread so it never blocks the main loop.
  - Exposes `time_remaining` (float) and `is_expired` (bool).
  - Calls an optional `on_expire` callback when time runs out.
  - Can be paused and resumed (used when showing between-round screens).
"""

import threading
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class GameTimer:
    """
    Countdown timer that ticks in a background thread.

    Example:
        def on_expire():
            print("Time's up!")

        timer = GameTimer(duration=10, on_expire=on_expire)
        timer.start()

        while not timer.is_expired:
            print(f"  {timer.time_remaining:.1f}s left")
            time.sleep(0.5)
    """

    def __init__(
        self,
        duration: float,
        on_expire: Optional[Callable[[], None]] = None,
        tick_interval: float = 0.1,
    ) -> None:
        """
        Args:
            duration:      Total countdown seconds.
            on_expire:     Callable invoked once when timer hits zero.
            tick_interval: How often the background thread wakes (seconds).
        """
        self._duration = duration
        self._on_expire = on_expire
        self._tick_interval = tick_interval

        self._start_time: Optional[float] = None
        self._elapsed_at_pause: float = 0.0
        self._paused = False
        self._stopped = False

        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._expire_event = threading.Event()

    # ── Control ────────────────────────────────────────────────────────────

    def start(self) -> "GameTimer":
        """Start the countdown. Returns self for chaining."""
        with self._lock:
            self._start_time = time.monotonic()
            self._elapsed_at_pause = 0.0
            self._paused = False
            self._stopped = False
            self._expire_event.clear()

        self._thread = threading.Thread(
            target=self._run, daemon=True, name="GameTimer"
        )
        self._thread.start()
        logger.debug("Timer started: %.1f seconds", self._duration)
        return self

    def pause(self) -> None:
        """Freeze the countdown."""
        with self._lock:
            if not self._paused and not self._stopped:
                elapsed = time.monotonic() - self._start_time
                self._elapsed_at_pause += elapsed
                self._start_time = None
                self._paused = True

    def resume(self) -> None:
        """Continue a paused countdown."""
        with self._lock:
            if self._paused and not self._stopped:
                self._start_time = time.monotonic()
                self._paused = False

    def stop(self) -> None:
        """Cancel the timer without firing on_expire."""
        with self._lock:
            self._stopped = True
            self._expire_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def reset(self, new_duration: Optional[float] = None) -> None:
        """Stop and re-initialise (call start() again to use)."""
        self.stop()
        with self._lock:
            if new_duration is not None:
                self._duration = new_duration
            self._elapsed_at_pause = 0.0
            self._start_time = None
            self._paused = False
            self._stopped = False
            self._expire_event.clear()

    # ── State ──────────────────────────────────────────────────────────────

    @property
    def time_remaining(self) -> float:
        """Seconds left, clamped to [0, duration]."""
        with self._lock:
            if self._stopped:
                return 0.0
            elapsed = self._elapsed_at_pause
            if self._start_time is not None and not self._paused:
                elapsed += time.monotonic() - self._start_time
        return max(0.0, self._duration - elapsed)

    @property
    def is_expired(self) -> bool:
        return self._expire_event.is_set()

    @property
    def is_running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stopped
            and not self._expire_event.is_set()
        )

    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Block until timer expires or `timeout` seconds pass.
        Returns True if timer expired, False on timeout.
        """
        return self._expire_event.wait(timeout=timeout)

    # ── Internal ───────────────────────────────────────────────────────────

    def _run(self) -> None:
        """Background tick loop."""
        while True:
            time.sleep(self._tick_interval)
            with self._lock:
                if self._stopped:
                    return
                if self._paused or self._start_time is None:
                    continue
                elapsed = self._elapsed_at_pause + (
                    time.monotonic() - self._start_time
                )
                expired = elapsed >= self._duration

            if expired:
                self._expire_event.set()
                logger.debug("Timer expired.")
                if self._on_expire:
                    try:
                        self._on_expire()
                    except Exception:
                        logger.exception("on_expire callback raised an exception.")
                return
