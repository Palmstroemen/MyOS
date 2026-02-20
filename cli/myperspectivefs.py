#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myperspectivefs - mount flipped perspective FUSE adapter.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.perspective_fuse import mount_perspective_fuse


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mount MyOS perspective FUSE layer",
    )
    parser.add_argument("--project-root", required=True, help="Absolute project-root directory containing project branches")
    parser.add_argument("--mount-point", required=True, help="Mount point for perspective filesystem")
    parser.add_argument(
        "--start-real-path",
        help="Initial real path to derive CPD template-head (defaults to <project-root>/ProjektA when present)",
    )
    parser.add_argument("--perspective", default="flipped", choices=["flipped"], help="Perspective mode (v1 supports flipped)")
    parser.add_argument("--role", default=None, help="Optional ACL role for resolver checks")
    parser.add_argument("--foreground", action="store_true", help="Run fuse in foreground")
    return parser.parse_args(args)


def _choose_default_start(project_root: Path) -> Path:
    # MVP convenience: pick first directory under project_root if caller does not pass one.
    for child in sorted(project_root.iterdir(), key=lambda p: p.name.lower()):
        if child.is_dir() and not child.name.startswith("."):
            return child
    return project_root


def main(argv=None) -> None:
    args = parse_args(argv)
    project_root = Path(str(args.project_root)).expanduser().resolve()
    mount_point = Path(str(args.mount_point)).expanduser().resolve()
    start_real = (
        Path(str(args.start_real_path)).expanduser().resolve()
        if args.start_real_path
        else _choose_default_start(project_root)
    )
    mount_perspective_fuse(
        project_root=str(project_root),
        start_real_path=str(start_real),
        mount_point=str(mount_point),
        perspective_id=str(args.perspective),
        role=args.role,
        foreground=bool(args.foreground),
    )


if __name__ == "__main__":
    main()
