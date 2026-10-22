# xray.py - X-ray view: look through small folders at their files
#
# While a listing still fits on screen (Scope: no scrollbar in the window, myls: the
# terminal's height), small folders are seen through: their files take the folder's place,
# each marked with the folder they lie in. Folders open smallest first (by their number of
# files, then by name), each completely or not at all, as long as the listing stays within
# the budget - predictable: a small folder is always seen through before a bigger one.
# Projects (a world of their own), empty, hidden and unreadable folders stay folders;
# symlinked folders are not followed.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union


@dataclass(frozen=True)
class XrayEntry:
    path: Path
    via: str = ""  # folder the file is seen through ("Finanz/2024"); "" for the folder's own


def xray_listing(
    folder: Union[str, Path],
    budget: int,
    *,
    extra: int = 0,
    may_read: Optional[Callable[[Path], bool]] = None,
    folders_shown: bool = True,
) -> List[XrayEntry]:
    """
    The entries of folder (hidden ones not), small subfolders replaced by their files
    while the listing has at most budget entries; extra counts entries the caller shows
    besides (e.g. embryos). may_read(path) says whether a folder may be looked into.
    With folders_shown False (folders hidden in the listing) only files take room.
    """
    folder = Path(folder)
    may_read = may_read or (lambda path: True)
    children = [child for child in sorted(folder.iterdir(), key=lambda p: p.name.lower())
                if not child.name.startswith(".")]
    shown = children if folders_shown else [c for c in children if not c.is_dir()]
    freed = 1 if folders_shown else 0  # the folder's own entry makes way for its files
    room = budget - len(shown) - extra
    candidates = []
    if room >= 0:
        for child in children:
            if child.is_symlink() or not child.is_dir():
                continue
            files = _visible_files(child, room + freed, may_read)
            if files:
                candidates.append((len(files), child.name.lower(), child, files))
    candidates.sort(key=lambda c: (c[0], c[1]))
    opened: Dict[Path, List[Path]] = {}
    for count, _, child, files in candidates:
        if count - freed > room:
            break
        room -= count - freed
        opened[child] = files
    entries: List[XrayEntry] = []
    for child in children:
        if child in opened:
            entries.extend(XrayEntry(f, f.parent.relative_to(folder).as_posix()) for f in opened[child])
        else:
            entries.append(XrayEntry(child))
    return entries


def _visible_files(folder: Path, limit: int, may_read: Callable[[Path], bool]) -> Optional[List[Path]]:
    """The files below folder, or None when it cannot be seen through: it holds a project,
    an unreadable or symlinked folder, or more than limit files."""
    files: List[Path] = []
    stack = [folder]
    while stack:
        current = stack.pop()
        # Security: never look into a folder the user may not read.
        if not may_read(current) or (current / ".MyOS" / "Project.md").exists():
            return None
        try:
            items = sorted(current.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return None
        for item in items:
            if item.name.startswith("."):
                continue
            if item.is_dir():
                if item.is_symlink():
                    return None
                stack.append(item)
            else:
                files.append(item)
                if len(files) > limit:
                    return None
    return files
