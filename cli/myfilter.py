#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myfilter - MyOS filters CLI
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.perspective import find_filters_layers, resolve_effective_filter

_STATE_FILE = Path("~/.cache/myos/myfilter_state.json").expanduser()


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MyOS filters utility",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_cmd = sub.add_parser("list", help="List filters from a path upwards")
    list_cmd.add_argument("path", nargs="?", default=".", help="Start path (default: .)")
    list_cmd.add_argument("--verbose", action="store_true", help="Show origin/depth details")

    resolve_cmd = sub.add_parser("resolve", help="Resolve the active filter")
    resolve_cmd.add_argument("path", nargs="?", default=".", help="CWD path (default: .)")
    resolve_cmd.add_argument("--manual", help="Manual filter path override")
    resolve_cmd.add_argument("--verbose", action="store_true", help="Show effective merge chain")

    activate_cmd = sub.add_parser("activate", help="Activate manual filter")
    activate_cmd.add_argument("filter", help="Path to filter file")

    sub.add_parser("clear", help="Clear manual filter override")

    show_cmd = sub.add_parser("show", help="Show effective filter details")
    show_cmd.add_argument("path", nargs="?", default=".", help="CWD path (default: .)")
    show_cmd.add_argument("--manual", help="Manual filter path override")
    show_cmd.add_argument("--verbose", action="store_true", help="Show effective merge chain")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "list":
            _list_filters(args.path, verbose=bool(getattr(args, "verbose", False)))
        elif args.command == "resolve":
            _resolve_filter(args.path, args.manual, verbose=bool(getattr(args, "verbose", False)))
        elif args.command == "activate":
            _activate_filter(getattr(args, "filter"))
        elif args.command == "clear":
            _clear_filter()
        elif args.command == "show":
            _show_filter(args.path, args.manual, verbose=bool(getattr(args, "verbose", False)))
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _list_filters(path: str, *, verbose: bool = False) -> None:
    results = find_filters_layers(path)
    if not results:
        print("No filters found.")
        return
    for layer in results:
        if verbose:
            print(
                f"{layer.config.name} ({layer.source_path}) "
                f"[origin={layer.origin_type}, depth={layer.depth}, inherit={layer.config.inherit}]"
            )
        else:
            print(f"{layer.config.name} ({layer.source_path})")


def _resolve_filter(path: str, manual: str | None, *, verbose: bool = False) -> None:
    effective = resolve_effective_filter(path, manual=(manual or _load_manual_override()))
    if not effective:
        print("No active filter.")
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


def _show_filter(path: str, manual: str | None, *, verbose: bool = False) -> None:
    _resolve_filter(path, manual, verbose=verbose or True)


def _activate_filter(filter_path: str) -> None:
    target = Path(str(filter_path)).expanduser().resolve()
    if not target.exists() or not target.is_file():
        raise ValueError("manual filter path does not exist")
    state = {"manualFilterPath": str(target)}
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Activated manual filter: {target}")


def _clear_filter() -> None:
    if _STATE_FILE.exists():
        _STATE_FILE.unlink()
    print("Manual filter cleared.")


def _load_manual_override() -> str | None:
    try:
        if not _STATE_FILE.exists():
            return None
        state = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        value = str(state.get("manualFilterPath") or "").strip()
        return value or None
    except Exception:
        return None


if __name__ == "__main__":
    main()
