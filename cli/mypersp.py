#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mypersp - MyOS perspectives CLI
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.perspective import find_perspectives_layers, resolve_effective_perspective

_STATE_FILE = Path("~/.cache/myos/mypersp_state.json").expanduser()


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MyOS perspectives utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List perspectives from a path upwards")
    list_cmd.add_argument("path", nargs="?", default=".", help="Start path (default: .)")
    list_cmd.add_argument("--verbose", action="store_true", help="Show origin/depth details")

    resolve_cmd = sub.add_parser("resolve", help="Resolve the active perspective")
    resolve_cmd.add_argument("path", nargs="?", default=".", help="CWD path (default: .)")
    resolve_cmd.add_argument("--manual", help="Manual perspective path override")
    resolve_cmd.add_argument("--verbose", action="store_true", help="Show effective merge chain")

    activate_cmd = sub.add_parser("activate", help="Activate manual perspective")
    activate_cmd.add_argument("perspective", help="Path to perspective file")

    sub.add_parser("clear", help="Clear manual perspective override")

    show_cmd = sub.add_parser("show", help="Show effective perspective details")
    show_cmd.add_argument("path", nargs="?", default=".", help="CWD path (default: .)")
    show_cmd.add_argument("--manual", help="Manual perspective path override")
    show_cmd.add_argument("--verbose", action="store_true", help="Show effective merge chain")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "list":
            _list_perspectives(args.path, verbose=bool(getattr(args, "verbose", False)))
        elif args.command == "resolve":
            _resolve_perspective(args.path, args.manual, verbose=bool(getattr(args, "verbose", False)))
        elif args.command == "activate":
            _activate_perspective(args.perspective)
        elif args.command == "clear":
            _clear_perspective()
        elif args.command == "show":
            _show_perspective(args.path, args.manual, verbose=bool(getattr(args, "verbose", False)))
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _list_perspectives(path: str, *, verbose: bool = False) -> None:
    results = find_perspectives_layers(path)
    if not results:
        print("No perspectives found.")
        return
    for layer in results:
        if verbose:
            print(
                f"{layer.config.name} ({layer.source_path}) "
                f"[origin={layer.origin_type}, depth={layer.depth}, inherit={layer.config.inherit}]"
            )
        else:
            print(f"{layer.config.name} ({layer.source_path})")


def _resolve_perspective(path: str, manual: str | None, *, verbose: bool = False) -> None:
    effective = resolve_effective_perspective(path, manual=(manual or _load_manual_override()))
    if not effective:
        print("No active perspective.")
        return
    if not verbose:
        print(effective.config.name)
        return
    print(f"name: {effective.config.name}")
    print(f"mode: {effective.mode}")
    print(f"flatten: {str(bool(effective.config.flatten)).lower()}")
    print(f"groups: {', '.join(effective.config.groups) if effective.config.groups else '-'}")
    print("chain:")
    for item in effective.explain_chain():
        print(
            f"- {item.get('name')} :: {item.get('sourcePath')} "
            f"(origin={item.get('originType')}, depth={item.get('depth')}, inherit={item.get('inherit')})"
        )


def _show_perspective(path: str, manual: str | None, *, verbose: bool = False) -> None:
    _resolve_perspective(path, manual, verbose=verbose or True)


def _activate_perspective(perspective_path: str) -> None:
    target = Path(str(perspective_path)).expanduser().resolve()
    if not target.exists() or not target.is_file():
        raise ValueError("manual perspective path does not exist")
    state = {"manualPerspectivePath": str(target)}
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Activated manual perspective: {target}")


def _clear_perspective() -> None:
    if _STATE_FILE.exists():
        _STATE_FILE.unlink()
    print("Manual perspective cleared.")


def _load_manual_override() -> str | None:
    try:
        if not _STATE_FILE.exists():
            return None
        state = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        value = str(state.get("manualPerspectivePath") or "").strip()
        return value or None
    except Exception:
        return None


if __name__ == "__main__":
    main()
