# perspective_drive.py - the FUSE drive's turned tree ("Perspektiven" next to "Projekte")
#
# See "Designdocument Perspective Resolver MVP.md", A6. The drive always shows the whole
# turned tree of the projects root, independent of any lens:
#
#   /                                   the departments (template folders: 00_Admin, ...)
#   /04_Finanz[/Ausgangsrechnungen...]  a department path: its template subfolders, Projekte
#   /04_Finanz/Projekte[/Wohnen]        the shelf: projects, and folders leading to them
#   /04_Finanz/Projekte/Job/...         = Projekte/Job/04_Finanz/... (real files)
#
# Without the department folder in a project, the project itself is shown (v1.1 fallback,
# with its folders). Saving there lands in the department folder, born on the way (with
# its template content). The first "Projekte" separates the department path from the way
# to the project. Within a project, subprojects are reached through the project.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from core.perspective_session import children, departments, holds_project, is_project, template_dirs

PROJECTS = "Projekte"
Parts = Tuple[str, ...]


@dataclass(frozen=True)
class DriveNode:
    is_dir: bool
    real: Optional[Path]         # the real file or folder; None for the virtual levels
    lens: Parts = ()             # department path
    project: Optional[Parts] = None
    rest: Parts = ()             # below the department path, inside the project
    fallback: Optional[Path] = None  # the department folder is missing: shown from here


class PerspectiveDrive:
    def __init__(self, projects_root: Union[str, Path],
                 may: Optional[Callable[[Path, str], bool]] = None) -> None:
        self.projects_root = Path(projects_root).expanduser().resolve()
        # may(real_path, action) with action "read" or "write": the caller's ACL check.
        self._may = may or (lambda path, action: True)

    # --- reading ---------------------------------------------------------------------

    def node(self, path: str) -> Optional[DriveNode]:
        """What a drive path stands for, or None when there is nothing. PermissionError
        when the real path may not be read (denied is never "missing")."""
        parts = _parts(path)
        if parts is None:
            return None
        if not parts:
            return DriveNode(is_dir=True, real=None)
        if parts[0] not in departments(self.projects_root):
            return None
        if PROJECTS not in parts:
            return DriveNode(is_dir=True, real=None, lens=parts)
        split = parts.index(PROJECTS)
        lens, way = parts[:split], parts[split + 1:]
        place: Parts = ()
        for index, name in enumerate(way):
            place = place + (name,)
            folder = self.projects_root.joinpath(*place)
            if is_project(folder):
                return self._inside(lens, place, way[index + 1:])
            if not holds_project(folder):
                return None
        return DriveNode(is_dir=True, real=None, lens=lens)  # the shelf (or the way along it)

    def listdir(self, path: str) -> List[str]:
        node = self.node(path)
        if node is None or not node.is_dir:
            raise FileNotFoundError(path)
        if node.real is not None:
            return [p.name for p in children(node.real)]
        parts = _parts(path) or ()
        if not parts:
            return sorted(departments(self.projects_root), key=str.lower)
        if PROJECTS not in parts:
            sub = {p.name for t in template_dirs(self.projects_root)
                   for p in children(t.joinpath(*parts)) if p.is_dir()}
            return sorted(sub | {PROJECTS}, key=str.lower)
        way = parts[parts.index(PROJECTS) + 1:]
        folder = self.projects_root.joinpath(*way)
        return [p.name for p in children(folder) if p.is_dir() and (is_project(p) or holds_project(p))]

    # --- writing ---------------------------------------------------------------------

    def target_for_create(self, path: str) -> Path:
        """The real path a file or folder created at path gets; the department folder is
        born on the way when needed. PermissionError on the virtual levels or without
        write access, FileNotFoundError when the parent is not there."""
        parts = _parts(path)
        if not parts:
            raise PermissionError(path)
        parent = self.node("/" + "/".join(parts[:-1]))
        if parent is None:
            raise FileNotFoundError(path)
        if parent.project is None:
            raise PermissionError(f"{path}: not inside a project")
        if parent.fallback is not None and not parent.rest:
            # The project itself is shown: saving goes into the department folder.
            folder = self._department_folder(parent)
        else:
            folder = parent.real
        target = folder / parts[-1]
        if not self._may(target, "write"):
            raise PermissionError(path)
        if parent.fallback is not None and not parent.rest:
            folder = self._materialize(parent)
        return folder / parts[-1]

    def may(self, real: Path, action: str) -> bool:
        """The ACL check this drive was given ("read" / "write" on a real path)."""
        return self._may(real, action)

    # --- helpers ---------------------------------------------------------------------

    def _inside(self, lens: Parts, place: Parts, rest: Parts) -> Optional[DriveNode]:
        project_dir = self.projects_root.joinpath(*place)
        department = project_dir.joinpath(*lens)
        if department.is_dir():
            real, fallback = department.joinpath(*rest), None
        else:
            fallback = next(p for p in [*department.parents] if p == project_dir or p.is_dir()
                            and project_dir in p.parents)
            real = fallback.joinpath(*rest)
        if real.is_symlink() or not real.exists():
            return None
        if not self._may(real, "read"):
            raise PermissionError(str(real))
        return DriveNode(is_dir=real.is_dir(), real=real, lens=lens, project=place, rest=rest, fallback=fallback)

    def _department_folder(self, node: DriveNode) -> Path:
        return self.projects_root.joinpath(*node.project, *node.lens)

    def _materialize(self, node: DriveNode) -> Path:
        """Create the department folder of node's project (embryos born with their content)."""
        from core.localBlueprintLayer import Blueprint  # late: heavy, only for writes

        project_dir = self.projects_root.joinpath(*node.project)
        try:
            return Blueprint(project_dir).materialize_dir("/".join(node.lens))
        except ValueError:  # no blueprint for this project: plain folders
            folder = self._department_folder(node)
            folder.mkdir(parents=True, exist_ok=True)
            return folder


def _parts(path: str) -> Optional[Parts]:
    """The parts of a drive path; None when a part is not allowed."""
    parts = tuple(p for p in str(path or "/").split("/") if p)
    # Security: no way out of the projects root, never into MyOS' own .MyOS. Other hidden
    # files are allowed (LibreOffice keeps its lock file next to the document).
    if any(p in (".", "..", ".MyOS") or "\\" in p for p in parts):
        return None
    return parts
