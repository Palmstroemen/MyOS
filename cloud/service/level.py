# level.py - the MyOS folders of a level and what a birth does, as the core service answers
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 8, step 2. For the row of MyOS
# folders in Files: which template folders a level holds, born or embryo, by the same code as
# Scope (core/localBlueprintLayer.py), with the rights of the person asking (ACLs.md, as Scope
# with enforcement on). A birth copies from the project's .MyOS/Embryos/, which the core keeps
# (core/cloud_embryos.py: the files and hidden folders of that template level). The browser
# then creates and copies with the user's own rights - Nextcloud checks them once more.

from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Optional, Union

from cloud.service.lens import may_for
from core.cloud_embryos import PAYLOAD, birth_contents
from core.localBlueprintLayer import Blueprint


def level(root: Union[str, Path], person: str, path: str) -> Optional[dict]:
    """{"folders": [{"name", "born"}]} for the folder at path (relative to root): born MyOS
    folders person may read, embryos person may create. None when there is no such folder."""
    root = Path(root).expanduser().resolve()
    folder = _folder(root, path)
    if folder is None or not folder.is_dir():
        return None
    project = _project_of(root, folder)
    if project is None:
        return {"folders": []}
    may = may_for(person)
    rel = _rel(folder, project)
    found = _blueprint(project).get_template_folders_at(rel, may_write=lambda r: may(project / r, "write"))
    folders = [{"name": name, "born": not embryo} for name, embryo in found
               if embryo or may(folder / name, "read")]
    return {"folders": sorted(folders, key=lambda f: f["name"].lower())}


def birth(root: Union[str, Path], person: str, path: str) -> Optional[dict]:
    """What the birth of the embryo at path does (paths relative to root): {"create": folders,
    the embryo's first, "copy": [{"from", "to"}]}. None unless path is an embryo whose parent
    is born; PermissionError when person may not create it there."""
    root = Path(root).expanduser().resolve()
    target = _folder(root, path)
    if target is None or target == root or target.exists() or not target.parent.is_dir():
        return None
    project = _project_of(root, target.parent)
    if project is None:
        return None
    rel = _rel(target, project)
    blueprint = _blueprint(project)
    if not blueprint.is_embryo(rel):
        return None
    if not may_for(person)(target, "write"):
        raise PermissionError(path)
    dirs, files = birth_contents(blueprint.birth_clinic.find_template_source(rel))
    to = "/" + target.relative_to(root).as_posix()
    payload = _in_root(root, project) + f"/{PAYLOAD}/{rel}"
    return {"create": [to] + [f"{to}/{d}" for d in dirs],
            "copy": [{"from": f"{payload}/{f}", "to": f"{to}/{f}"} for f in files]}


def _folder(root: Path, path: str) -> Optional[Path]:
    parts = [p for p in str(path or "/").split("/") if p]
    # Security: never out of the shadow, never into a hidden folder such as .MyOS.
    if any(p in (".", "..") or p.startswith(".") or "\\" in p for p in parts):
        return None
    return root.joinpath(*parts)


def _project_of(root: Path, folder: Path) -> Optional[Path]:
    """The nearest project up from folder, within root."""
    for candidate in [folder, *folder.parents]:
        if (candidate / ".MyOS" / "Project.md").is_file():
            return candidate
        if candidate == root:
            break
    return None


def _rel(folder: Path, project: Path) -> str:
    rel = folder.relative_to(project).as_posix()
    return "" if rel == "." else rel


def _in_root(root: Path, project: Path) -> str:
    rel = project.relative_to(root).as_posix()
    return "" if rel == "." else "/" + rel


def _blueprint(project: Path) -> Blueprint:
    with contextlib.redirect_stdout(io.StringIO()):  # Blueprint reports what it mounts
        return Blueprint(project)
