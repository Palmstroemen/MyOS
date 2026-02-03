#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myproject - MyOS project CLI
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.project import ProjectConfig


def _create_project(path: str) -> int:
    try:
        project_path = Path(path).expanduser()
        ProjectConfig.create(project_path)
        print(f"Created project at {project_path.resolve()}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MyOS project management",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a project in a folder")
    create.add_argument("path", help="Folder to turn into a project")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    if args.command == "create":
        sys.exit(_create_project(args.path))


if __name__ == "__main__":
    main()
