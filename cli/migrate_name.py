#!/usr/bin/env python3
"""
migrate_name - move projects and the user's settings from a former name to the current one

    python3 cli/migrate_name.py ~/Projekte            # show what would change
    python3 cli/migrate_name.py --apply ~/Projekte    # do it
    python3 cli/migrate_name.py --apply --config      # the user's settings folder too

Former names are in core/brand.py (LEGACY_*); what moves is described in core/name_migration.py.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.brand import NAME  # noqa: E402
from core.name_migration import migrate_config, migrate_tree  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"Move projects and settings over to the name {NAME}")
    parser.add_argument("paths", nargs="*", help="Project trees to move over")
    parser.add_argument("--config", action="store_true", help="Also the user's settings folder (~/.config)")
    parser.add_argument("--apply", action="store_true", help="Change things (without: only show the plan)")
    args = parser.parse_args(argv)
    steps = []
    for path in args.paths:
        root = Path(path).expanduser()
        if not root.is_dir():
            print(f"Not a folder: {root}", file=sys.stderr)
            return 2
        steps += migrate_tree(root, apply=args.apply)
    if args.config:
        steps += migrate_config(apply=args.apply)
    for step in steps:
        print(step)
    if not steps:
        print("Nothing to move.")
    elif not args.apply:
        print("Nothing changed yet; run again with --apply.")
    return 1 if any(s.kind == "conflict" for s in steps) else 0


if __name__ == "__main__":
    sys.exit(main())
