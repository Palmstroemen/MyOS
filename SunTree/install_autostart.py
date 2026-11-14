#!/usr/bin/env python3
"""Start SunTree hidden at login, ready for its shortcut (Ctrl+Alt+Space): writes the
autostart entry $XDG_CONFIG_HOME/autostart/seiton-suntree.desktop (Cinnamon and GNOME read it).
An entry under a former name (myos-suntree.desktop) is taken away, or SunTree would start twice.

    python3 SunTree/install_autostart.py <projects root>
    python3 SunTree/install_autostart.py --remove
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # started as a script: make core importable
    sys.path.insert(0, str(REPO_ROOT))

from core.brand import NAME as BRAND, file_name, legacy_file_names  # noqa: E402

SUNTREE = Path(__file__).resolve().with_name("SunTree.py")
NAME = file_name("suntree.desktop")
LEGACY_NAMES = legacy_file_names("suntree.desktop")


def entry_path(name: str = NAME) -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "autostart" / name


def _remove_former() -> bool:
    removed = False
    for name in LEGACY_NAMES:
        if entry_path(name).is_file():
            entry_path(name).unlink()
            removed = True
    return removed


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
        f"Comment={BRAND} SunTree, ready for Ctrl+Alt+Space\n"
        f"Exec={_quoted(sys.executable)} {_quoted(str(SUNTREE))} {_quoted(str(root))}\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8")
    _remove_former()
    return target


def remove() -> bool:
    former = _remove_former()
    target = entry_path()
    if not target.exists():
        return former
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
