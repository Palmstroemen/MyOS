#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myedit - MyOS config editor helper
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.project import resolve_cwp


SECTION_MAP = {
    "tags": "Tags.md",
    "templates": "Templates.md",
    "template": "Templates.md",
    "acl": "ACLs.md",
    "acls": "ACLs.md",
    "config": "Config.md",
}


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open the relevant MyOS config file in your editor.",
    )
    parser.add_argument("section", help="Config section (tags, templates, acl, config)")
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path inside a project (default: .)",
    )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        target = _resolve_target_file(args.section, args.path)
        _open_in_editor(target)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def _resolve_target_file(section: str, path: str) -> Path:
    key = section.strip().lower()
    if key not in SECTION_MAP:
        raise ValueError(f"Unknown section: {section}")

    cwp = resolve_cwp(Path(path))
    if not cwp:
        raise ValueError("No project found for path")

    myos_dir = cwp.path / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)

    target = myos_dir / SECTION_MAP[key]
    if not target.exists():
        target.write_text(f"# {target.stem}\n")
    return target


def _open_in_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR")
    if not editor:
        raise ValueError("EDITOR is not set")
    subprocess.run([editor, str(path)], check=False)


if __name__ == "__main__":
    main()
