from __future__ import annotations

import argparse
from pathlib import Path

from .debug_server import serve
from .pipeline import run_build
from .utils import env_port


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build fictional city map packages")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Run a production-compatible map build")
    build.add_argument("--mode", choices=["prod", "dev"], required=True)
    build.add_argument("--clean", action="store_true", help="Delete existing outputs before building")

    serve_cmd = sub.add_parser("serve", help="Serve debug_map.html and existing outputs")
    serve_cmd.add_argument("--port", type=int, default=None)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "build":
        run_build(mode=args.mode, clean=args.clean)
        return

    if args.command == "serve":
        port = args.port if args.port is not None else env_port()
        serve(Path.cwd(), port)
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
