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


def _trash(args) -> int:
    """List, restore or delete for good what is in a project's trash (via ScopeApi, so
    the same rights apply as in Scope)."""
    from core.scope_api import ScopeApi

    folder = str(Path(args.path).expanduser().resolve())
    api = ScopeApi(folder)
    if args.trash_command == "list":
        entries = api.trash_entries(folder)
        for entry in entries:
            kind = "folder" if entry["isDir"] else "file"
            print(f"{entry['name']}\t/{entry['original']}\t{entry['deletedAt']}\t{entry['deletedBy']}\t{kind}")
        if not entries:
            print("The trash is empty.")
        return 0
    if args.trash_command == "empty":
        if not args.yes:
            print("Error: emptying the trash deletes for good; confirm with --yes", file=sys.stderr)
            return 1
        result = api.trash_empty(folder)
        print(f"{result['deleted']} entries deleted for good, {result['skipped']} kept (no permission)")
        return 0
    result = api.trash_restore(folder, args.name) if args.trash_command == "restore" else api.trash_delete_finally(folder, args.name)
    if not result["ok"]:
        print(f"Error: {args.trash_command} {args.name!r} failed ({result['reason']})", file=sys.stderr)
        return 1
    print(f"Restored to {result['path']}" if args.trash_command == "restore" else f"Deleted {args.name} for good")
    return 0


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

    trash = sub.add_parser("trash", help="The project's trash: list, restore, delete for good, empty")
    trash_sub = trash.add_subparsers(dest="trash_command", required=True)
    trash_list = trash_sub.add_parser("list", help="List the trash of the project containing path")
    trash_list.add_argument("path", nargs="?", default=".", help="Any folder inside the project (default: .)")
    for name, text in (("restore", "Restore an entry to where it was deleted"),
                       ("delete", "Delete an entry of the trash for good")):
        cmd = trash_sub.add_parser(name, help=text)
        cmd.add_argument("name", help="Name in the trash (see: trash list)")
        cmd.add_argument("--in", dest="path", default=".", help="Any folder inside the project (default: .)")
    empty = trash_sub.add_parser("empty", help="Delete everything in the trash for good")
    empty.add_argument("--in", dest="path", default=".", help="Any folder inside the project (default: .)")
    empty.add_argument("--yes", action="store_true", help="Confirm: this cannot be undone")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    if args.command == "create":
        sys.exit(_create_project(args.path, create_missing=args.new))
    if args.command == "tidy":
        sys.exit(_tidy_project(args.path))
    if args.command == "trash":
        sys.exit(_trash(args))


if __name__ == "__main__":
    main()
