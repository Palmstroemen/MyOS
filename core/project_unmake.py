# project_unmake.py - a project becomes an ordinary folder again (crossed-out P-Button)
#
# Creating a project remembers what it wrote into .MyOS (CREATED, names and checksums).
# Turning it back removes .MyOS when nothing of its own came since (changed rights, tags,
# a trash with entries, ...); otherwise only with consent, and then .MyOS is not deleted
# but goes into the parent project's trash as "Seiton settings". Not for the top project,
# not outside the projects tree; subprojects stay projects.

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Dict, List

from core import trash
from core.template_place import find_templates_dir
from core.brand import META_DIR, NAME

CREATED = ".created.json"  # in .MyOS: what creating the project wrote
SETTINGS_NAME = f"{NAME} settings"  # .seiton with settings of its own, in the parent's trash
_MARKER_BODY = "# MyOS Project"


class ProjectHasOwnSettings(Exception):
    """The project has settings of its own; turning it back needs consent (keep_own)."""

    def __init__(self, names: List[str]) -> None:
        super().__init__(", ".join(names))
        self.names = names


def record_created(project_root: Path) -> None:
    """Remember the files creating the project wrote into its .MyOS."""
    settings_dir = Path(project_root) / META_DIR
    files = {item.name: _checksum(item) for item in settings_dir.iterdir()
             if not item.name.startswith(".") and item.is_file() and not item.is_symlink()}
    (settings_dir / CREATED).write_text(json.dumps(files, indent=2, sort_keys=True), encoding="utf-8")


def can_unmake(path: Path) -> bool:
    """Whether path is a project that can become an ordinary folder again."""
    target = Path(path).expanduser().resolve()
    if not (target / META_DIR / "Project.md").is_file():
        return False
    if not any((parent / META_DIR / "Project.md").is_file() for parent in target.parents):
        return False  # the top project of the projects tree
    templates_dir = find_templates_dir(target)
    return templates_dir is None or templates_dir.resolve() not in target.parents


def own_settings(project_root: Path) -> List[str]:
    """Names in the project's .MyOS that creating it did not write (or that changed since)."""
    settings_dir = Path(project_root) / META_DIR
    created = _created(settings_dir)
    own = []
    for item in sorted(settings_dir.iterdir(), key=lambda p: p.name):
        if item.name.startswith("."):
            continue  # caches and drafts (.TagsHere.json, ...)
        if item.is_symlink():
            own.append(item.name)
        elif item.is_dir():
            if any(p.is_file() or p.is_symlink() for p in item.rglob("*")):
                own.append(item.name)
        elif item.name == "Project.md":
            if created.get(item.name) != _checksum(item) and _marker_body(item) != _MARKER_BODY:
                own.append(item.name)
        elif created.get(item.name) != _checksum(item):
            own.append(item.name)
    return own


def unmake_project(project_root: Path, user: str, keep_own: bool = False) -> None:
    """
    Make project_root an ordinary folder again. With settings of its own this needs
    keep_own (else ProjectHasOwnSettings): its .MyOS then goes into the parent project's
    trash as SETTINGS_NAME (restorable), instead of being deleted.
    """
    root = Path(project_root).expanduser().resolve()
    if not can_unmake(root):
        raise ValueError(f"{root} cannot become an ordinary folder")
    own = own_settings(root)
    settings_dir = root / META_DIR
    if not own:
        # Only what creating it wrote, caches and empty folders: nothing to keep.
        shutil.rmtree(settings_dir)
        return
    if not keep_own:
        raise ProjectHasOwnSettings(own)
    # Renamed first, so root is no project any more and its parent project takes it.
    settings = root / SETTINGS_NAME
    number = 2
    while settings.exists():
        settings = root / f"{SETTINGS_NAME} {number}"
        number += 1
    settings_dir.rename(settings)
    trash.move_to_trash(settings, deleted_by=user)


def _created(settings_dir: Path) -> Dict[str, str]:
    try:
        data = json.loads((settings_dir / CREATED).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _marker_body(path: Path) -> str:
    """Project.md without its front matter (PostFix keeps window positions there)."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            text = text[end + 5:]
    return text.strip()
