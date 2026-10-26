#!/usr/bin/env python3
"""Start SunTree hidden at login, ready for its shortcut (Ctrl+Alt+Space): writes the
autostart entry $XDG_CONFIG_HOME/autostart/myos-suntree.desktop (Cinnamon and GNOME read it).

    python3 SunTree/install_autostart.py <projects root>
    python3 SunTree/install_autostart.py --remove
"""

import os
import sys
from pathlib import Path

SUNTREE = Path(__file__).resolve().with_name("SunTree.py")
NAME = "myos-suntree.desktop"


def entry_path() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "autostart" / NAME


def _quoted(text: str) -> str:
    # Security: the Exec line is run at every login; refuse what its quoting cannot hold
    # rather than escape it (desktop entry spec: ", `, $ and \ need escapes).
    if any(c in text for c in '"`$\\\n'):
        raise ValueError(f"not a plain path: {text!r}")
    return f'"{text}"'


def install(projects_root: str) -> Path:
    root = Path(projects_root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"no such folder: {root}")
    target = entry_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=SunTree\n"
        "Comment=MyOS SunTree, ready for Ctrl+Alt+Space\n"
        f"Exec={_quoted(sys.executable)} {_quoted(str(SUNTREE))} {_quoted(str(root))}\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8")
    return target


def remove() -> bool:
    target = entry_path()
    if not target.exists():
        return False
    target.unlink()
    return True


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    if argv[1] == "--remove":
        print("removed" if remove() else "no autostart entry")
        return 0
    try:
        print(f"written: {install(argv[1])}")
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
