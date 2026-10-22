# perspective_session.py - the lens: looking at the projects from a department
#
# See "Designdocument Perspective Resolver MVP.md", Part A. A lens is a department path
# (04_Finanz/Ausgangsrechnungen/2026) seen in a project. It does not change the CWD - where
# one is. Changing the CWD (left menu) makes the lens follow; moving the lens to another
# project (right menu, the CTD) leaves the CWD; taking the lens off brings one back to it.
#
# The session keeps its state as parts (project path below the projects root, lens path)
# rather than parsing CPD strings: projects may be nested (Wohnen/Garten). The CPD text is
# built from the parts, for display and the FUSE drive.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

from core.acl import _resolve_templates_dir, _template_folder_names
from core.project import ProjectConfig

Parts = Tuple[str, ...]


@dataclass(frozen=True)
class LensView:
    shown: Path          # the folder whose content is shown
    entries: List[Path]  # its folders and files (hidden ones not), sorted by name
    fallback: bool       # the lens' folder does not exist there: its nearest parent is shown


class PerspectiveSession:
    def __init__(self, projects_root: Union[str, Path]) -> None:
        self.projects_root = Path(projects_root).expanduser().resolve()
        self.active = False
        self.cwd: Optional[Path] = None
        self.lens: Parts = ()
        self._place: Parts = ()   # project (or, on the shelf, the way to projects) below the root
        self._shelf = False

    # --- state ---------------------------------------------------------------------

    @property
    def project(self) -> Optional[Parts]:
        """The project the lens looks into (None on the shelf or without a lens)."""
        return self._place if self.active and not self._shelf else None

    @property
    def cpd(self) -> str:
        """The lens as a path: /04_Finanz/Ausgangsrechnungen/2026/Projekte/Musikstudio."""
        if not self.active:
            return ""
        return "/" + "/".join((*self.lens, "Projekte", *self._place))

    @property
    def target(self) -> Optional[Path]:
        """The real folder the lens points at (where something dropped lands)."""
        if self.project is None:
            return None
        return self.projects_root.joinpath(*self._place, *self.lens)

    # --- gestures (Part A, A3) -------------------------------------------------------

    def set_cwd(self, path: Union[str, Path]) -> None:
        """The left menu: where one is. With a lens on, the lens follows into its project."""
        cwd = Path(path).expanduser().resolve()
        project = self._project_of(cwd)
        if project is None:
            raise ValueError(f"{cwd} is not inside a project below {self.projects_root}")
        self.cwd = cwd
        if self.active:
            self._place = project
            self._shelf = not project

    def put_on(self, lens: Sequence[str]) -> None:
        """Put on (or change) the lens of a department path, in the project looked at."""
        if self.cwd is None:
            raise ValueError("no CWD")
        lens = self._checked_parts(lens)
        place = self._place if self.active and not self._shelf else self._project_of(self.cwd)
        if not lens or lens[0] not in self._departments(self.projects_root.joinpath(*place)):
            raise ValueError(f"not a department: {'/'.join(lens)}")
        self.active, self.lens, self._place, self._shelf = True, lens, place, False

    def move_to_project(self, project: Sequence[str]) -> None:
        """The right menu: move the lens to another project; the CWD stays."""
        project = self._checked_parts(project)
        self._require_active()
        if not self._is_project(self.projects_root.joinpath(*project)):
            raise ValueError(f"not a project: {'/'.join(project)}")
        self._place, self._shelf = project, False

    def go_into(self, name: str) -> None:
        """Deeper into the department (the lens gets sharper)."""
        self._require_active()
        self.lens = self.lens + self._checked_parts([name])

    def to_shelf(self) -> None:
        """Up to the shelf: the department's folders of all projects."""
        self._require_active()
        self._place, self._shelf = (), True

    def into_shelf(self, name: str) -> None:
        """On the shelf, towards a project (folders on the way, e.g. Wohnen for Wohnen/Garten)."""
        self._require_active()
        if not self._shelf:
            raise ValueError("not on the shelf")
        place = self._place + self._checked_parts([name])
        folder = self.projects_root.joinpath(*place)
        if not (self._is_project(folder) or self._holds_project(folder)):
            raise ValueError(f"no project there: {'/'.join(place)}")
        self._place = place
        self._shelf = not self._is_project(folder)

    def take_off(self) -> Optional[Path]:
        """Take the lens off; returns the CWD one is back in."""
        self.active, self.lens, self._place, self._shelf = False, (), (), False
        return self.cwd

    # --- what the lens shows -------------------------------------------------------

    def listing(self) -> LensView:
        """The lens' content: on the shelf the projects (and folders leading to them);
        in a project the lens' folder, or its nearest existing parent (with folders)."""
        self._require_active()
        if self._shelf:
            folder = self.projects_root.joinpath(*self._place)
            entries = [p for p in _children(folder)
                       if p.is_dir() and (self._is_project(p) or self._holds_project(p))]
            return LensView(shown=folder, entries=entries, fallback=False)
        project_dir = self.projects_root.joinpath(*self._place)
        for depth in range(len(self.lens), -1, -1):
            folder = project_dir.joinpath(*self.lens[:depth])
            if folder.is_dir() and not folder.is_symlink():
                return LensView(shown=folder, entries=_children(folder), fallback=depth < len(self.lens))
        return LensView(shown=project_dir, entries=[], fallback=True)

    def desk_file(self) -> Optional[Path]:
        """The department's Desk.md while the lens is on (A5): the nearest one up the lens
        path - in the project, else in its template - never the project's own."""
        if self.project is None:
            return None
        project_dir = self.projects_root.joinpath(*self._place)
        templates = self._template_dirs(project_dir)
        for depth in range(len(self.lens), 0, -1):
            for base in [project_dir, *templates]:
                desk = base.joinpath(*self.lens[:depth], ".MyOS", "Desk.md")
                if desk.is_file() and not desk.is_symlink():
                    return desk
        return None

    # --- helpers ---------------------------------------------------------------------

    def _require_active(self) -> None:
        if not self.active:
            raise ValueError("no lens on")

    @staticmethod
    def _checked_parts(parts: Sequence[str]) -> Parts:
        # Security: lens and project paths stay below the projects root.
        checked = tuple(str(p) for p in parts)
        for part in checked:
            if not part or part in (".", "..") or "/" in part or "\\" in part or part.startswith("."):
                raise ValueError(f"invalid path part: {part!r}")
        return checked

    def _project_of(self, path: Path) -> Optional[Parts]:
        """The nearest project at or above path, as parts below the projects root."""
        if path != self.projects_root and self.projects_root not in path.parents:
            return None
        for candidate in [path, *path.parents]:
            if candidate == self.projects_root:
                return ()
            if self._is_project(candidate):
                return candidate.relative_to(self.projects_root).parts
        return None

    @staticmethod
    def _is_project(folder: Path) -> bool:
        return (folder / ".MyOS" / "Project.md").is_file()

    @staticmethod
    def _holds_project(folder: Path) -> bool:
        for current, dirs, _files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            if current != str(folder) and (Path(current) / ".MyOS" / "Project.md").is_file():
                return True
        return False

    def _template_dirs(self, project_dir: Path) -> List[Path]:
        templates_dir = _resolve_templates_dir(project_dir)
        if templates_dir is None:
            return []
        names = ProjectConfig(project_dir).get_effective_templates() or []
        return [templates_dir / name for name in names if (templates_dir / name).is_dir()]

    def _departments(self, project_dir: Path) -> set:
        names: set = set()
        for template in self._template_dirs(project_dir):
            names |= _template_folder_names(template)
        return names


def _children(folder: Path) -> List[Path]:
    try:
        items = list(folder.iterdir())
    except OSError:
        return []
    return sorted((p for p in items if not p.name.startswith(".")), key=lambda p: p.name.lower())
