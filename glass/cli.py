from __future__ import annotations

import sys

from opencontext import cli as opencontext_cli


def main() -> int:
    """
    Thin wrapper around `opencontext.cli` so users can run `glass start <dd-mm>`.
    """
    argv = sys.argv[1:]
    original = list(sys.argv)

    if not argv or argv[0] in {"-h", "--help"}:
        try:
            sys.argv = ["opencontext", "glass", "--help"]
            return opencontext_cli.main()
        finally:
            sys.argv = original

    command = argv[0]
    if command != "start":
        print(f"Unknown glass command: {command}", file=sys.stderr)
        print("Usage: glass start <dd-mm> [options]", file=sys.stderr)
        return 1

    if len(argv) < 2:
        print("Missing <dd-mm> argument.", file=sys.stderr)
        print("Usage: glass start <dd-mm> [options]", file=sys.stderr)
        return 1

    date_token = argv[1]
    forwarded = ["opencontext", "glass", "start", "--date", date_token] + argv[2:]

    try:
        sys.argv = forwarded
        return opencontext_cli.main()
    finally:
        sys.argv = original


if __name__ == "__main__":
    sys.exit(main())
