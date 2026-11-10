#!/usr/bin/env python3
"""
CLI launcher for the Styleire pSEO Static Site Generator & Interactive Management Dashboard.
Runs standard library ThreadingHTTPServer serving REST API and SPA frontend.
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.dashboard.server import run_server


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch Styleire pSEO Management Dashboard & Preview Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--host", default="127.0.0.1", help="Network host interface to bind")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port to listen on")
    parser.add_argument("--config", default="pseo_config.json", help="Path to dashboard config JSON file")
    parser.add_argument("--manifest", default="pseo_manifest.json", help="Path to pSEO manifest JSON file")
    args = parser.parse_args()

    print("=" * 72)
    print("Styleire pSEO Static Site Generator & Management Dashboard v2.0")
    print(f"Server URL: http://{args.host}:{args.port}")
    print(f"Config:     {os.path.abspath(args.config)}")
    print(f"Manifest:   {os.path.abspath(args.manifest)}")
    print("=" * 72)

    try:
        run_server(host=args.host, port=args.port, config_path=args.config, manifest_path=args.manifest)
    except KeyboardInterrupt:
        print("\n[INFO] Dashboard server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
