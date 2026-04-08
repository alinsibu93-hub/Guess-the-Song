"""
main.py — Entry point for Guess the Song.

Run:
    python main.py
    python main.py --difficulty hard --rounds 3

Environment variables required (or set in .env):
    SPOTIPY_CLIENT_ID
    SPOTIPY_CLIENT_SECRET
"""

import argparse
import logging
import os
import sys

# Load .env file if python-dotenv is available (optional dependency)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env loading is optional; users can export vars manually

from config import GameConfig
from game_engine import GameEngine
import ui


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guess the Song — a Spotify-powered music quiz game."
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "normal", "hard"],
        default=None,
        help="Game difficulty (overrides interactive prompt)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Number of rounds (1–20, overrides interactive prompt)",
    )
    parser.add_argument(
        "--no-artist",
        action="store_true",
        help="Skip the artist-guess bonus round",
    )
    parser.add_argument(
        "--audio-backend",
        choices=["pygame", "simpleaudio", "auto"],
        default="pygame",
        help="Audio backend (default: pygame)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def _validate_credentials(cfg: GameConfig) -> bool:
    """Return False and print guidance if credentials are missing."""
    if not cfg.spotify_client_id or not cfg.spotify_client_secret:
        print(ui.red("\n  ✗  Spotify credentials not found.\n"))
        print("  Set the following environment variables:")
        print("    export SPOTIPY_CLIENT_ID='your_client_id'")
        print("    export SPOTIPY_CLIENT_SECRET='your_client_secret'")
        print()
        print("  Or create a .env file in this directory:")
        print("    SPOTIPY_CLIENT_ID=your_client_id")
        print("    SPOTIPY_CLIENT_SECRET=your_client_secret")
        print()
        print("  Get credentials at: https://developer.spotify.com/dashboard")
        print()
        return False
    return True


def main() -> int:
    args = _parse_args()
    _configure_logging(args.verbose)

    # ── Interactive setup (if not overridden by flags) ─────────────────────
    difficulty = args.difficulty
    rounds = args.rounds

    if difficulty is None:
        difficulty = ui.prompt_difficulty()
    if rounds is None:
        rounds = ui.prompt_rounds()

    # ── Build config ───────────────────────────────────────────────────────
    cfg = GameConfig(
        total_rounds=rounds,
        difficulty=difficulty,
        show_artist_prompt=not args.no_artist,
        audio_backend=args.audio_backend,
    )
    cfg.apply_difficulty()

    if not _validate_credentials(cfg):
        return 1

    # ── Game loop ──────────────────────────────────────────────────────────
    try:
        while True:
            engine = GameEngine(cfg)
            engine.run()
            if not ui.ask_play_again():
                break
    except KeyboardInterrupt:
        print(ui.dim("\n\n  Game interrupted. Goodbye!"))
    except Exception as exc:
        logging.exception("Unhandled error in game loop.")
        print(ui.red(f"\n  Fatal error: {exc}"))
        return 1

    print(ui.cyan("\n  Thanks for playing Guess the Song! 🎵\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
