# perspective_session.py - the lens: looking at the projects from a department
#
# See "Designdocument Perspective Resolver MVP.md", Part A. A lens is a department path
# (04_Finanz/Ausgangsrechnungen/2026) seen in a project. Scope shows it framed in its one
# path line (A3): left of the frame the project (or the shelf), inside the frame the
# department path. Taking the lens off (✕) removes only the frame: one stays where the lens
# looked, which becomes the CWD.
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
        """Where one is without a lens. A lens on stays where it is."""
        cwd = Path(path).expanduser().resolve()
        if self._project_of(cwd) is None:
            raise ValueError(f"{cwd} is not inside a project below {self.projects_root}")
        self.cwd = cwd

    def put_on(self, lens: Sequence[str]) -> None:
        """Put on (or change) the lens of a department path, in the project looked at."""
        if self.cwd is None:
            raise ValueError("no CWD")
        place = self._place if self.active and not self._shelf else self._project_of(self.cwd)
        self._wear(place, lens)

    def look_at(self, path: Union[str, Path]) -> None:
        """Put on (or move) the lens to a folder of a project - born or embryo - given as a
        real path (Scope's MyOS-folder row shows such folders)."""
        if self.cwd is None:
            raise ValueError("no CWD")
        folder = Path(path).expanduser().resolve()
        place = self._project_of(folder)
        if not place:
            raise ValueError(f"not inside a project: {folder}")
        self._wear(place, folder.relative_to(self.projects_root.joinpath(*place)).parts)

    def move_to_project(self, project: Sequence[str]) -> None:
        """Left of the frame: move the lens to another project, keeping its depth."""
        project = self._checked_parts(project)
        self._require_active()
        if not is_project(self.projects_root.joinpath(*project)):
            raise ValueError(f"not a project: {'/'.join(project)}")
        self._place, self._shelf = project, False

    def move_to(self, path: Union[str, Path]) -> None:
        """Go somewhere with the lens on, given as a real path (the projects row, SunTree).
        The lens stays on until taken off: a project, or a folder inside one, moves it to
        that project, keeping its depth; a folder of projects (or the projects root) puts it
        on the shelf there."""
        folder = Path(path).expanduser().resolve()
        self._require_active()
        place = self._project_of(folder)
        if place is None:
            raise ValueError(f"not below the projects root: {folder}")
        if place:
            self._place, self._shelf = place, False
        else:
            self._place, self._shelf = folder.relative_to(self.projects_root).parts, True

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
        if not (is_project(folder) or holds_project(folder)):
            raise ValueError(f"no project there: {'/'.join(place)}")
        self._place = place
        self._shelf = not is_project(folder)

    def take_off(self) -> Optional[Path]:
        """Take the lens off (✕): one stays where it looked - its folder in the project
        (an embryo stays one), on the shelf the folder of projects. Returns the new CWD."""
        if self.active:
            self.cwd = self.target or self.projects_root.joinpath(*self._place)
        self.active, self.lens, self._place, self._shelf = False, (), (), False
        return self.cwd

    # --- what the lens shows -------------------------------------------------------

    def listing(self) -> LensView:
        """The lens' content: on the shelf the projects (and folders leading to them);
        in a project the lens' folder, or its nearest existing parent (with folders)."""
        self._require_active()
        shown, fallback = self.shown()
        if self._shelf:
            entries = [p for p in children(shown) if p.is_dir() and (is_project(p) or holds_project(p))]
            return LensView(shown=shown, entries=entries, fallback=False)
        return LensView(shown=shown, entries=children(shown), fallback=fallback)

    def shown(self) -> Tuple[Path, bool]:
        """The folder the lens shows, and whether it is the fallback (the lens' folder does
        not exist in the project: its nearest existing parent)."""
        self._require_active()
        if self._shelf:
            return self.projects_root.joinpath(*self._place), False
        project_dir = self.projects_root.joinpath(*self._place)
        for depth in range(len(self.lens), -1, -1):
            folder = project_dir.joinpath(*self.lens[:depth])
            if folder.is_dir() and not folder.is_symlink():
                return folder, depth < len(self.lens)
        return project_dir, True

    def bear(self) -> Path:
        """Create the lens' folder in its project (to drop or save into it); folders of
        the template are born with their content, as embryos are."""
        if self.project is None:
            raise ValueError("no project to bear the lens in")
        return bear_folder(self.projects_root.joinpath(*self._place), self.lens)

    def desk_file(self) -> Optional[Path]:
        """The department's Desk.md while the lens is on (A5): the nearest one up the lens
        path in the template - never the project's own. Birth copies .MyOS, so a project
        holds old copies of the template's Desk; one there counts only where the template
        has none for the department."""
        if self.project is None:
            return None
        project_dir = self.projects_root.joinpath(*self._place)
        for bases in (template_dirs(project_dir), [project_dir]):
            desk = self._nearest_lens_desk(bases)
            if desk is not None:
                return desk
        return None

    def desk_save_file(self) -> Optional[Path]:
        """Where a change of the desktop by the user goes while the lens is on: into the
        template's Desk that applies, else (born on the first change) the department's."""
        if self.project is None:
            return None
        templates = template_dirs(self.projects_root.joinpath(*self._place))
        if not templates:
            return None
        home = next((t for t in templates if (t / self.lens[0]).is_dir()), templates[0])
        return self._nearest_lens_desk(templates) or home / self.lens[0] / ".MyOS" / "Desk.md"

    def _nearest_lens_desk(self, bases: Sequence[Path]) -> Optional[Path]:
        for depth in range(len(self.lens), 0, -1):
            for base in bases:
                desk = base.joinpath(*self.lens[:depth], ".MyOS", "Desk.md")
                if desk.is_file() and not desk.is_symlink():
                    return desk
        return None

    # --- helpers ---------------------------------------------------------------------

    def _wear(self, place: Parts, lens: Sequence[str]) -> None:
        lens = self._checked_parts(lens)
        if not lens or lens[0] not in departments(self.projects_root.joinpath(*place)):
            raise ValueError(f"not a department: {'/'.join(lens)}")
        self.active, self.lens, self._place, self._shelf = True, lens, place, False

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
            if is_project(candidate):
                return candidate.relative_to(self.projects_root).parts
        return None


def bear_folder(project_dir: Path, lens: Sequence[str]) -> Path:
    """Create project_dir/<lens> (embryos on the way born with their template content)."""
    from core.localBlueprintLayer import Blueprint  # late: heavy, only for writes

    try:
        return Blueprint(project_dir).materialize_dir("/".join(lens))
    except ValueError:  # no blueprint for this project: plain folders
        folder = project_dir.joinpath(*lens)
        folder.mkdir(parents=True, exist_ok=True)
        return folder


def is_project(folder: Path) -> bool:
    return (folder / ".MyOS" / "Project.md").is_file()


def holds_project(folder: Path) -> bool:
    """Whether a project lies somewhere below folder (hidden folders not searched)."""
    for current, dirs, _files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        if current != str(folder) and (Path(current) / ".MyOS" / "Project.md").is_file():
            return True
    return False


def template_dirs(project_dir: Path) -> List[Path]:
    """The folders of the templates project_dir uses."""
    templates_dir = _resolve_templates_dir(project_dir)
    if templates_dir is None:
        return []
    names = ProjectConfig(project_dir).get_effective_templates() or []
    return [templates_dir / name for name in names if (templates_dir / name).is_dir()]


def departments(project_dir: Path) -> set:
    """The department names (template folders) of a project."""
    names: set = set()
    for template in template_dirs(project_dir):
        names |= _template_folder_names(template)
    return names


def children(folder: Path) -> List[Path]:
    """Folders and files in folder (hidden ones not), sorted by name."""
    return _children(folder)


def _children(folder: Path) -> List[Path]:
    try:
        items = list(folder.iterdir())
    except OSError:
        return []
    return sorted((p for p in items if not p.name.startswith(".")), key=lambda p: p.name.lower())
