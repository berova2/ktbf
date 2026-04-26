"""Simple localhost server for static files.

Usage:
    python local_server.py --port 8000 --open
"""

from __future__ import annotations

import argparse
import os
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class NoCacheHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Serve static files with no-cache headers for local development."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve the current project on localhost for quick previews."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument(
        "--dir",
        default=str(Path(__file__).resolve().parent),
        help="Directory to serve (default: this script's folder)",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the site in your default browser after server starts",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    web_dir = Path(args.dir).resolve()

    if not web_dir.exists() or not web_dir.is_dir():
        raise SystemExit(f"Invalid directory: {web_dir}")

    os.chdir(web_dir)

    server = ThreadingHTTPServer((args.host, args.port), NoCacheHTTPRequestHandler)
    url = f"http://{args.host}:{args.port}/"

    print(f"Serving: {web_dir}")
    print(f"URL: {url}")
    print("Press Ctrl+C to stop.")

    if args.open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
