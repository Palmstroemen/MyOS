#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myproject - MyOS project CLI
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.project import ProjectConfig


def _create_project(path: str, create_missing: bool = False) -> int:
    try:
        project_path = Path(path).expanduser()
        if project_path.exists():
            if not project_path.is_dir():
                raise ValueError(f"Target exists and is not a folder: {project_path}")
        else:
            if not create_missing:
                raise ValueError(
                    f"Target folder does not exist: {project_path} (use --new to create)"
                )
            project_path.mkdir(parents=True, exist_ok=True)
        ProjectConfig.create(project_path)
        print(f"Created project at {project_path.resolve()}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _sub_project_roots(project_root: Path) -> list:
    """Project roots nested below project_root (symlinks are not followed)."""
    roots = []
    for current, dirs, _files in os.walk(project_root, followlinks=False):
        current_path = Path(current)
        if current_path != project_root and (current_path / ".MyOS" / "Project.md").is_file():
            roots.append(current_path)
        dirs[:] = [d for d in dirs if d != ".MyOS"]
    return roots


def _tidy_project(path: str) -> int:
    """
    Turn unused born template folders back into embryos: in the project containing
    `path` and in every sub-project below it, each with its own templates.
    """
    try:
        from core.localBlueprintLayer import Blueprint

        blueprint = Blueprint(Path(path).expanduser())
        removed = blueprint.reabsorb_all()
        for sub_root in _sub_project_roots(blueprint.project_root):
            if sub_root.is_dir():
                removed.extend(Blueprint(sub_root).reabsorb_all())
        for folder in removed:
            print(f"Reabsorbed {folder}")
        print(f"{len(removed)} folder(s) turned back into embryos")
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
    create.add_argument(
        "--new",
        action="store_true",
        help="Create the folder if it does not exist",
    )

    tidy = sub.add_parser(
        "tidy",
        help="Turn born template folders that hold nothing of the user back into embryos",
    )
    tidy.add_argument("path", nargs="?", default=".", help="Any folder inside the project (default: .)")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    if args.command == "create":
        sys.exit(_create_project(args.path, create_missing=args.new))
    if args.command == "tidy":
        sys.exit(_tidy_project(args.path))


if __name__ == "__main__":
    main()
