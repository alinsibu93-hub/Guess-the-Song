"""
main.py — Entry point for the Guess the Song API server.

Usage:
  python main.py [--host HOST] [--port PORT] [--debug]
"""

import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Guess the Song — API Backend")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Bind port (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode")
    args = parser.parse_args()

    # iTunes Search API requires no key / auth — no env-var check needed.
    from api import app
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
