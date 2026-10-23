"""
Run the perspective daemon: python -m daemon
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root on path
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from daemon.perspective_daemon import run_daemon


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MyOS perspective daemon (FUSE + Unix socket API)")
    parser.add_argument("--projects-root", "--project-root", dest="projects_root", required=True,
                        help="The projects root (e.g. .../Projekte)")
    parser.add_argument("--mount-point", required=True, help="Where the drive appears (e.g. .../Perspektiven)")
    parser.add_argument("--socket-path", default=None,
                        help="Unix socket path (default: one per projects root in XDG_RUNTIME_DIR)")
    parser.add_argument("--foreground", action="store_true", help="Run in foreground")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_daemon(
        projects_root=args.projects_root,
        mount_point=args.mount_point,
        socket_path=args.socket_path,
        foreground=args.foreground,
    )


if __name__ == "__main__":
    main()
