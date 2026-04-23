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

    if not os.getenv("YOUTUBE_API_KEY"):
        print("ERROR: YOUTUBE_API_KEY is not set.", file=sys.stderr)
        print("Create a .env file with:  YOUTUBE_API_KEY=your_key_here", file=sys.stderr)
        print(
            "Get a key at: https://console.cloud.google.com/apis/library/youtube.googleapis.com",
            file=sys.stderr,
        )
        sys.exit(1)

    from api import app
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
