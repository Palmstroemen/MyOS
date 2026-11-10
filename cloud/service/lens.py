# lens.py - what a turned path stands for, as the core service answers it
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 8.1. The meaning of a path comes
# from core/perspective_drive.py, the same as on the FUSE drive; the rights from ACLs.md, the
# same as in Scope (core/acl_view.py). The service reads a shadow tree (folders and .MyOS
# files, no documents): it names the real folder, the browser lists it with the user's rights.

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Union

from core.acl import find_acl_project_root
from core.acl_view import ACLView
from core.perspective_drive import PROJECTS, PerspectiveDrive
from core.perspective_session import is_project


def lens(root: Union[str, Path], person: str, path: str) -> Optional[dict]:
    """The answer for path in the turned tree of root, seen by person (lower-case key of
    "# Users"): {"path", "real": None, "entries": [{"name", "kind"}]} for a virtual level,
    {"path", "real": "/Job/04_Finanz", "fallback"} inside a project (real relative to root;
    fallback: the department folder is not born there, the project's own folder is shown).
    A project on the shelf carries its real department folder ("real") where it is born.
    None when there is nothing; PermissionError when person may not read it."""
    root = Path(root).expanduser().resolve()
    drive = PerspectiveDrive(root, may=may_for(person))
    path = "/" + "/".join(p for p in str(path or "/").split("/") if p)
    node = drive.node(path)
    if node is None:
        return None
    if node.real is not None:
        real = "/" + node.real.relative_to(root).as_posix()
        return {"path": path, "real": real.rstrip("/") or "/", "fallback": node.fallback is not None}
    entries = [{"name": name, "kind": _kind(root, path, name)} for name in drive.listdir(path)]
    if node.lens and PROJECTS in path.split("/"):
        # On the shelf: only projects one may read there, and ways leading to one.
        entries = [entry for entry in entries if _visible(drive, _child(path, entry["name"]))]
        if not entries and path.split("/")[-1] != PROJECTS:
            raise PermissionError(path)  # a way that leads to nothing one may read
        for entry in entries:
            shown = drive.node(_child(path, entry["name"])) if entry["kind"] == "project" else None
            if shown is not None and shown.fallback is None:
                entry["real"] = "/" + shown.real.relative_to(root).as_posix()
    return {"path": path, "real": None, "entries": entries}


def may_for(person: str) -> Callable[[Path, str], bool]:
    """may(path, action): whether person may act ("read", "write") on path in the shadow."""
    def may(path: Path, action: str) -> bool:
        if find_acl_project_root(path) is None:
            return True  # no ACLs.md: the platform's rights decide alone
        # Security: an ACLs.md that cannot be read allows nothing.
        view = ACLView.for_path(path)
        return view is not None and action in view.rights_for_user(person, path)
    return may


def _kind(root: Path, path: str, name: str) -> str:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "department"
    if PROJECTS not in parts:
        return "shelf" if name == PROJECTS else "folder"
    way = parts[parts.index(PROJECTS) + 1:]
    return "project" if is_project(root.joinpath(*way, name)) else "way"


def _visible(drive: PerspectiveDrive, path: str) -> bool:
    try:
        node = drive.node(path)
    except PermissionError:
        return False
    if node is None:
        return False
    if node.project is not None:
        return True
    return any(_visible(drive, _child(path, name)) for name in drive.listdir(path))


def _child(path: str, name: str) -> str:
    return path.rstrip("/") + "/" + name
