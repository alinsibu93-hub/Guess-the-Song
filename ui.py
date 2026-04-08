"""
ui.py — Terminal UI utilities.

Keeps all print/color/formatting logic out of GameEngine so the
engine can be tested without side effects.
"""

import sys
import os
import shutil
from typing import Optional


# ── ANSI color helpers (disabled automatically on Windows without color support)

def _supports_color() -> bool:
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # Enable VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except Exception:
            return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOR = _supports_color()


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def green(t: str) -> str:  return _c("32", t)
def red(t: str) -> str:    return _c("31", t)
def yellow(t: str) -> str: return _c("33", t)
def cyan(t: str) -> str:   return _c("36", t)
def bold(t: str) -> str:   return _c("1",  t)
def dim(t: str) -> str:    return _c("2",  t)


# ── Layout helpers ─────────────────────────────────────────────────────────

def _term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


def divider(char: str = "─") -> str:
    return char * min(_term_width(), 72)


def banner(text: str) -> None:
    width = min(_term_width(), 72)
    print()
    print(bold(divider("═")))
    print(bold(text.center(width)))
    print(bold(divider("═")))
    print()


def section(text: str) -> None:
    print()
    print(cyan(divider("─")))
    print(cyan(f"  {text}"))
    print(cyan(divider("─")))


# ── Game-specific screens ──────────────────────────────────────────────────

def show_welcome(difficulty: str, total_rounds: int) -> None:
    banner("🎵  GUESS THE SONG  🎵")
    print(f"  Difficulty : {bold(difficulty.upper())}")
    print(f"  Rounds     : {bold(str(total_rounds))}")
    print()
    print("  Listen to the audio clip and type the song title.")
    print("  You also earn bonus points for guessing the artist.")
    print()
    print(dim("  Press ENTER to start…"))
    input()


def show_round_header(round_num: int, total_rounds: int, score: int) -> None:
    section(
        f"Round {round_num}/{total_rounds}   |   Score: {bold(str(score))}"
    )


def show_playing(clip_seconds: float, timeout_seconds: int) -> None:
    print(f"\n  {cyan('♪')} Playing {clip_seconds:.0f}-second clip…")
    print(
        f"  You have {bold(str(timeout_seconds))} seconds to guess. "
        "Start typing any time!\n"
    )


def show_timer_warning(seconds_left: float) -> None:
    """Called by the engine to print an inline timer update."""
    bar_len = 20
    filled = int((seconds_left / 30) * bar_len)  # rough visual
    filled = max(0, min(bar_len, filled))
    bar = "█" * filled + "░" * (bar_len - filled)

    color = green if seconds_left > 5 else (yellow if seconds_left > 3 else red)
    sys.stdout.write(
        f"\r  {color(f'⏱  {seconds_left:4.1f}s')}  [{color(bar)}]   "
    )
    sys.stdout.flush()


def clear_timer_line() -> None:
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


def show_result(
    correct: bool,
    title_match: bool,
    artist_match: bool,
    correct_title: str,
    correct_artist: str,
    points_earned: int,
    timed_out: bool,
    time_taken: Optional[float],
) -> None:
    print()
    if timed_out:
        print(f"  {red('⏰  Time\'s up!')}  No points this round.")
    elif correct:
        print(f"  {green('✓  Correct!')}  +{bold(str(points_earned))} points")
        if artist_match:
            print(f"  {green('✓  Artist bonus!')}  You knew the artist too.")
    else:
        print(f"  {red('✗  Not quite.')}  You earned 0 points this round.")

    print()
    print(f"  The answer was: {bold(correct_title)} — {bold(correct_artist)}")
    if time_taken is not None and not timed_out:
        print(f"  Time taken: {time_taken:.1f}s")
    print()


def show_score_update(score: int, delta: int) -> None:
    if delta > 0:
        print(f"  {green('Score:')} {bold(str(score))}  (+{delta})")
    else:
        print(f"  {dim('Score:')} {dim(str(score))}")


def show_hint(hint_text: str) -> None:
    print(f"\n  {yellow('Hint:')} {hint_text}")


def show_final_scoreboard(
    rounds: list,  # list of dicts with round result info
    total_score: int,
    total_rounds: int,
) -> None:
    banner("GAME OVER — Final Scoreboard")
    print(f"  {'Round':<8} {'Song':<35} {'Points':>7}")
    print(f"  {divider('-')}")
    for r in rounds:
        status = green("✓") if r["correct"] else red("✗")
        title_short = r["title"][:33] + "…" if len(r["title"]) > 33 else r["title"]
        print(f"  {status} {r['round']:<6} {title_short:<35} {r['points']:>7}")
    print(f"  {divider('─')}")
    print(f"  {'TOTAL':<44} {bold(str(total_score)):>7}")
    print()

    pct = (total_score / (total_rounds * 150)) * 100  # 150 = max per round
    if pct >= 80:
        print(f"  {green('Outstanding!')} You really know your music. 🎸")
    elif pct >= 50:
        print(f"  {yellow('Not bad!')} Keep listening and you'll master it. 🎧")
    else:
        print(f"  {red('Better luck next time!')} Practice makes perfect. 🎵")
    print()


def prompt_difficulty() -> str:
    print("  Select difficulty:")
    print(f"    {bold('1')} — Easy   (15s clip, 20s timer)")
    print(f"    {bold('2')} — Normal (8s clip, 10s timer)  [default]")
    print(f"    {bold('3')} — Hard   (3s clip, 7s timer)")
    choice = input("\n  Your choice [1/2/3]: ").strip()
    mapping = {"1": "easy", "2": "normal", "3": "hard"}
    return mapping.get(choice, "normal")


def prompt_rounds() -> int:
    try:
        val = int(input("  How many rounds? [default 5]: ").strip() or "5")
        return max(1, min(val, 20))
    except ValueError:
        return 5


def ask_play_again() -> bool:
    ans = input("  Play again? [y/N]: ").strip().lower()
    return ans in ("y", "yes")
