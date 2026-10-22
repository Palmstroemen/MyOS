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
    virtual: bool = False  # a virtual folder (core/filing.py) not seen through


def xray_listing(
    folder: Union[str, Path],
    budget: int,
    *,
    extra: int = 0,
    may_read: Optional[Callable[[Path], bool]] = None,
    folders_shown: bool = True,
    virtual: Optional[Dict[str, List[Path]]] = None,
) -> List[XrayEntry]:
    """
    The entries of folder (hidden ones not), small subfolders replaced by their files
    while the listing has at most budget entries; extra counts entries the caller shows
    besides (e.g. embryos). may_read(path) says whether a folder may be looked into.
    With folders_shown False (folders hidden in the listing) only files take room.
    virtual: virtual folders (core/filing.py) by name with the loose files they group;
    they are seen through like real ones, and their files then simply show where they
    really lie - loose in folder.
    """
    folder = Path(folder)
    may_read = may_read or (lambda path: True)
    virtual = virtual or {}
    grouped = {f for files in virtual.values() for f in files}
    children = [child for child in sorted(folder.iterdir(), key=lambda p: p.name.lower())
                if not child.name.startswith(".") and child not in grouped]
    children += [folder / name for name in virtual if not (folder / name).exists()]
    shown = children if folders_shown else [c for c in children if not (c.is_dir() or c.name in virtual)]
    freed = 1 if folders_shown else 0  # the folder's own entry makes way for its files
    room = budget - len(shown) - extra
    candidates = []
    if room >= 0:
        for child in children:
            if child.name in virtual and not child.exists():
                files = virtual[child.name] if len(virtual[child.name]) <= room + freed else None
            elif child.is_symlink() or not child.is_dir():
                continue
            else:
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
        is_virtual = child.name in virtual and not child.exists()
        if child in opened:
            entries.extend(XrayEntry(f, "" if is_virtual else f.parent.relative_to(folder).as_posix())
                           for f in opened[child])
        else:
            entries.append(XrayEntry(child, virtual=is_virtual))
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
