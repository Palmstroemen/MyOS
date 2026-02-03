#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myimport - MyOS import CLI
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.importer import import_package


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MyOS import utility",
    )
    parser.add_argument("package", help="Path to export package (folder or zip)")
    parser.add_argument(
        "--target",
        help="Target root for adopt mode (or override restore)",
    )
    parser.add_argument(
        "--mode",
        choices=["adopt", "restore"],
        default="adopt",
        help="Import mode (default: adopt)",
    )
    parser.add_argument(
        "--conflict",
        choices=["merge", "overwrite", "skip"],
        default="merge",
        help="Conflict strategy (default: merge)",
    )
    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        result = import_package(
            args.package,
            target_root=args.target,
            mode=args.mode,
            conflict=args.conflict,
        )
        print(f"Imported into {result.import_root}")
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
