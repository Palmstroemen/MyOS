#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myperspectivefs - mount the "Perspektiven" drive: the turned tree of a projects root
(/04_Finanz/Projekte/Job = Projekte/Job/04_Finanz; see core/perspective_fuse.py).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.perspective_fuse import mount_perspective_drive


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mount the MyOS perspective drive (turned tree)")
    parser.add_argument("--projects-root", "--project-root", dest="projects_root", required=True,
                        help="The projects root (the folder holding the projects, e.g. .../Projekte)")
    parser.add_argument("--mount-point", required=True,
                        help="Where the drive appears (e.g. .../Perspektiven next to Projekte)")
    parser.add_argument("--foreground", action="store_true", help="Run fuse in foreground")
    return parser.parse_args(args)


def main(argv=None) -> None:
    args = parse_args(argv)
    mount_perspective_drive(
        projects_root=str(Path(str(args.projects_root)).expanduser().resolve()),
        mount_point=str(Path(str(args.mount_point)).expanduser().resolve()),
        foreground=bool(args.foreground),
    )


if __name__ == "__main__":
    main()
