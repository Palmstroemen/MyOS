# trash.py - one trash per project: .MyOS/Trash/ (see "Designdocument Trash.md")
#
# Deleting moves an entry into the trash of the project it belongs to (the nearest project
# of its parent folder, so a subproject has its own trash, and deleting a whole subproject
# puts it into its parent's). The layout follows the freedesktop trash: files/<name> and
# info/<name>.trashinfo with the project-relative Path, DeletionDate and, for MyOS,
# DeletedBy. Rights (delete at the original place) are checked by the caller.

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote, unquote

from core.project import ProjectFinder

TRASH_DIR = Path(".MyOS") / "Trash"
DEFAULT_RETENTION_DAYS = 30
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
_TRASH_DAYS = re.compile(r"^\s*trash_days\s*:\s*(\d+)\s*$", re.MULTILINE)


class TrashError(ValueError):
    """The entry cannot go to (or come back from) a project trash."""


@dataclass(frozen=True)
class TrashEntry:
    name: str  # name in the trash (unique there)
    original: str  # project-relative path it was deleted from (no leading /)
    deleted_at: datetime
    deleted_by: str
    is_dir: bool


def project_trash_root(path) -> Optional[Path]:
    """Project whose trash takes path (nearest project of its parent), or None."""
    target = Path(path).expanduser().absolute()
    return ProjectFinder.find_nearest(target.parent)


def _trash_dirs(project_root: Path):
    base = Path(project_root) / TRASH_DIR
    return base / "files", base / "info"


def move_to_trash(path, deleted_by: str) -> TrashEntry:
    """Move path into its project's trash and record where it came from."""
    target = Path(path).expanduser().absolute()
    root = project_trash_root(target)
    if root is None:
        raise TrashError(f"{target} is not in a MyOS project")
    rel = target.relative_to(root)
    # The project's own configuration (and the trash in it) is not deleted this way.
    if not rel.parts or rel.parts[0] == ".MyOS":
        raise TrashError(f"{target} cannot be moved to the trash")
    if not target.exists() and not target.is_symlink():
        raise TrashError(f"{target} does not exist")

    files, info = _trash_dirs(root)
    files.mkdir(parents=True, exist_ok=True)
    info.mkdir(parents=True, exist_ok=True)
    name = _unique_name(files, info, target.name)
    now = datetime.now().replace(microsecond=0)
    is_dir = target.is_dir() and not target.is_symlink()
    rel_text = "/".join(rel.parts)
    # Info first: if the move fails, the stray info is removed again.
    info_file = info / f"{name}.trashinfo"
    info_file.write_text(
        "[Trash Info]\n"
        f"Path={quote(rel_text)}\n"
        f"DeletionDate={now.strftime(_DATE_FORMAT)}\n"
        f"DeletedBy={deleted_by}\n",
        encoding="utf-8",
    )
    try:
        _move(target, files / name)
    except OSError:
        info_file.unlink(missing_ok=True)
        raise
    return TrashEntry(name, rel_text, now, str(deleted_by), is_dir)


def list_trash(project_root) -> List[TrashEntry]:
    files, info = _trash_dirs(Path(project_root))
    entries = []
    if not info.is_dir():
        return entries
    for info_file in sorted(info.glob("*.trashinfo")):
        name = info_file.name[: -len(".trashinfo")]
        stored = files / name
        if not (stored.exists() or stored.is_symlink()):
            continue
        fields = _read_info(info_file)
        try:
            deleted_at = datetime.strptime(fields.get("DeletionDate", ""), _DATE_FORMAT)
        except ValueError:
            deleted_at = datetime.fromtimestamp(info_file.stat().st_mtime)
        entries.append(TrashEntry(
            name=name,
            original=unquote(fields.get("Path", name)),
            deleted_at=deleted_at,
            deleted_by=fields.get("DeletedBy", ""),
            is_dir=stored.is_dir() and not stored.is_symlink(),
        ))
    return entries


def restore(project_root, name: str) -> Path:
    """Move an entry back; next to an existing entry of that name as "<name> (restored)"."""
    root = Path(project_root)
    entry = _entry(root, name)
    files, info = _trash_dirs(root)
    destination = root / entry.original
    # Security: the recorded path must stay inside the project (the .trashinfo is a
    # plain file anybody with write access could edit).
    if not destination.resolve().is_relative_to(root.resolve()) or ".." in Path(entry.original).parts:
        raise TrashError(f"invalid original path {entry.original!r}")
    if destination.exists() or destination.is_symlink():
        destination = _restored_name(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _move(files / name, destination)
    (info / f"{name}.trashinfo").unlink(missing_ok=True)
    return destination


def delete_finally(project_root, name: str) -> None:
    root = Path(project_root)
    _entry(root, name)
    files, info = _trash_dirs(root)
    stored = files / name
    if stored.is_dir() and not stored.is_symlink():
        shutil.rmtree(stored)
    else:
        stored.unlink()
    (info / f"{name}.trashinfo").unlink(missing_ok=True)


def cleanup(project_root, now: Optional[datetime] = None) -> List[str]:
    """Delete finally what is older than the project's retention; returns the names."""
    now = now or datetime.now()
    limit = timedelta(days=retention_days(project_root))
    removed = []
    for entry in list_trash(project_root):
        if now - entry.deleted_at > limit:
            delete_finally(project_root, entry.name)
            removed.append(entry.name)
    return removed


def retention_days(project_root) -> int:
    """trash_days from Project.md, inherited from parent projects; else 30."""
    current = ProjectFinder.find_nearest(Path(project_root).expanduser().absolute())
    while current is not None:
        try:
            text = (current / ".MyOS" / "Project.md").read_text(encoding="utf-8")
        except OSError:
            text = ""
        match = _TRASH_DAYS.search(text)
        if match:
            return int(match.group(1))
        parent = current.parent
        current = ProjectFinder.find_nearest(parent) if parent != current else None
    return DEFAULT_RETENTION_DAYS


def _entry(root: Path, name: str) -> TrashEntry:
    for entry in list_trash(root):
        if entry.name == name:
            return entry
    raise TrashError(f"{name!r} is not in the trash of {root}")


def _read_info(path: Path) -> dict:
    fields = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def _unique_name(files: Path, info: Path, name: str) -> str:
    candidate, n = name, 1
    while (files / candidate).exists() or (files / candidate).is_symlink() or (info / f"{candidate}.trashinfo").exists():
        n += 1
        candidate = f"{name}.{n}"
    return candidate


def _restored_name(destination: Path) -> Path:
    # Folders have no extension ("v1.2 (restored)"), files keep theirs ("notiz (restored).md").
    stem, suffix = (destination.name, "") if destination.is_dir() else (destination.stem, destination.suffix)
    candidate, n = destination.with_name(f"{stem} (restored){suffix}"), 1
    while candidate.exists() or candidate.is_symlink():
        n += 1
        candidate = destination.with_name(f"{stem} (restored {n}){suffix}")
    return candidate


def _move(source: Path, destination: Path) -> None:
    try:
        os.replace(source, destination)  # same filesystem: a rename, instant
    except OSError:
        shutil.move(str(source), str(destination))  # e.g. a mount point inside the project
