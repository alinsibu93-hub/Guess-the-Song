"""
tests/test_timer.py — Unit tests for GameTimer.

Run with:  python -m pytest tests/ -v
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game_timer import GameTimer


class TestGameTimer:
    def test_expires_after_duration(self):
        timer = GameTimer(duration=0.3)
        timer.start()
        time.sleep(0.5)
        assert timer.is_expired

    def test_not_expired_immediately(self):
        timer = GameTimer(duration=2.0)
        timer.start()
        assert not timer.is_expired
        timer.stop()

    def test_time_remaining_decreases(self):
        timer = GameTimer(duration=2.0)
        timer.start()
        t1 = timer.time_remaining
        time.sleep(0.2)
        t2 = timer.time_remaining
        timer.stop()
        assert t2 < t1

    def test_stop_before_expire(self):
        fired = []
        timer = GameTimer(duration=1.0, on_expire=lambda: fired.append(1))
        timer.start()
        timer.stop()
        time.sleep(0.2)
        assert len(fired) == 0

    def test_on_expire_callback(self):
        fired = []
        timer = GameTimer(duration=0.2, on_expire=lambda: fired.append(True))
        timer.start()
        timer.wait(timeout=1.0)
        assert fired == [True]

    def test_pause_and_resume(self):
        timer = GameTimer(duration=1.0)
        timer.start()
        time.sleep(0.1)
        timer.pause()
        remaining_at_pause = timer.time_remaining
        time.sleep(0.3)   # time passes but timer is paused
        remaining_after_sleep = timer.time_remaining
        timer.stop()
        # Within small float tolerance, remaining shouldn't have changed much
        assert abs(remaining_at_pause - remaining_after_sleep) < 0.05

    def test_time_remaining_zero_after_expire(self):
        timer = GameTimer(duration=0.1)
        timer.start()
        time.sleep(0.4)
        assert timer.time_remaining == 0.0
