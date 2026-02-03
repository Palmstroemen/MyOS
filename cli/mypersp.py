#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mypersp - MyOS perspectives CLI
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.perspective import find_perspectives, resolve_active_perspective


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MyOS perspectives utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List perspectives from a path upwards")
    list_cmd.add_argument("path", nargs="?", default=".", help="Start path (default: .)")

    resolve_cmd = sub.add_parser("resolve", help="Resolve the active perspective")
    resolve_cmd.add_argument("path", nargs="?", default=".", help="CWD path (default: .)")
    resolve_cmd.add_argument("--manual", help="Manual perspective path override")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "list":
            _list_perspectives(args.path)
        elif args.command == "resolve":
            _resolve_perspective(args.path, args.manual)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _list_perspectives(path: str) -> None:
    results = find_perspectives(path)
    if not results:
        print("No perspectives found.")
        return
    for cfg_path, cfg in results:
        print(f"{cfg.name} ({cfg_path})")


def _resolve_perspective(path: str, manual: str | None) -> None:
    cfg = resolve_active_perspective(path, manual=manual)
    if not cfg:
        print("No active perspective.")
        return
    print(cfg.name)


if __name__ == "__main__":
    main()
