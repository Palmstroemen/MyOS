# cloud_embryos.py - a project's embryos for a cloud (the MyOS row in Nextcloud's Files app)
#
# MyOS stays the one place that resolves templates (Templates.md, inherited, .MyOS/Templates
# found upwards, several templates merged). Per project this computes a folder per embryo,
# .MyOS/Embryos/<embryo>/, holding what its birth copies, and .MyOS/Embryos.json - the
# template tree and the hash of each uploaded file, the sync's bookkeeping. The browser takes
# the embryos of a level from the folders it may read there (each is readable for who may
# read where it is born, as Scope shows an embryo) and copies on birth what one holds besides
# its visible subfolders, the deeper embryos.

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.localBlueprintLayer import Blueprint

MANIFEST = ".MyOS/Embryos.json"
PAYLOAD = ".MyOS/Embryos"


@dataclass
class EmbryoSet:
    path: str  # the project's folder, relative to the synced root ("/" for it)
    manifest: dict  # {"version": 2, "tree": {name: subtree}, "births": {embryo: {"dirs", "files"}}}
    payload: Dict[str, Path] = field(default_factory=dict)  # "<embryo>/<file>" -> template file


def embryo_sets(root: Path) -> List[EmbryoSet]:
    """The project at root and every subproject below it (dot folders skipped), root first."""
    root = Path(root)
    sets = [_embryo_set(root, "/")]
    for folder, dirs, _files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        for name in dirs:
            project = Path(folder) / name
            if (project / ".MyOS" / "Project.md").is_file():
                sets.append(_embryo_set(project, "/" + project.relative_to(root).as_posix()))
    return sets


def _embryo_set(project: Path, path: str) -> EmbryoSet:
    with contextlib.redirect_stdout(io.StringIO()):  # Blueprint reports what it mounts
        blueprint = Blueprint(project)
    births: Dict[str, dict] = {}
    payload: Dict[str, Path] = {}
    for embryo in _paths(blueprint.embryo_tree):
        source = blueprint.birth_clinic.find_template_source(embryo)
        dirs, files = birth_contents(source)
        if not files and not dirs:
            continue
        births[embryo] = {"dirs": dirs, "files": {rel: _sha256(source / rel) for rel in files}}
        payload.update({f"{embryo}/{rel}": source / rel for rel in files})
    manifest = {"version": 2, "tree": blueprint.embryo_tree, "births": births}
    return EmbryoSet(path, manifest, payload)


def _paths(tree: dict, prefix: str = "") -> List[str]:
    found = []
    for name, sub in sorted(tree.items()):
        path = f"{prefix}{name}"
        found.append(path)
        found.extend(_paths(sub, path + "/"))
    return found


def birth_contents(source: Path) -> Tuple[List[str], List[str]]:
    """
    What a birth from the template folder source copies (BirthClinic._copy_template_safely):
    the files of its level and its hidden folders (e.g. .MyOS) with all they hold; visible
    subfolders stay embryos. Returns (folders, files), relative and sorted.
    Security: symlinks are left out - a template must not hand out what they point to.
    """
    dirs: List[str] = []
    files: List[str] = []
    for item in sorted(source.iterdir()):
        if item.is_symlink():
            continue
        if item.is_dir():
            if item.name.startswith("."):
                dirs.append(item.name)
                _all_below(item, item.name, dirs, files)
        elif item.is_file():
            files.append(item.name)
    return sorted(dirs), sorted(files)


def _all_below(folder: Path, rel: str, dirs: List[str], files: List[str]) -> None:
    for item in sorted(folder.iterdir()):
        if item.is_symlink():
            continue
        if item.is_dir():
            dirs.append(f"{rel}/{item.name}")
            _all_below(item, f"{rel}/{item.name}", dirs, files)
        elif item.is_file():
            files.append(f"{rel}/{item.name}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class EmbryoChange:
    project: str  # EmbryoSet.path
    missing: bool = False  # the project's folder is not in the cloud (yet): left out
    manifest_changed: bool = False
    upload: List[str] = field(default_factory=list)  # payload paths to (re)upload
    remove: List[str] = field(default_factory=list)  # payload paths no birth copies any more


def _in_project(project: str, rel: str) -> str:
    return ("" if project == "/" else project) + "/" + rel


def _files(manifest) -> Dict[str, str]:
    """payload path -> sha256 of what a manifest says is uploaded."""
    births = manifest.get("births", {}) if isinstance(manifest, dict) else {}
    return {f"{embryo}/{rel}": sha for embryo, birth in births.items() for rel, sha in birth.get("files", {}).items()}


def compare(sets: List[EmbryoSet], cloud) -> List[EmbryoChange]:
    """
    What each project's embryos need in the cloud. cloud.get(path) gives a file's content or
    None, cloud.exists(path) whether an entry is there (paths relative to the Team folder).
    The manifest there records what was uploaded (it goes up last), so only files whose
    hash differs go up again.
    """
    changes = []
    for embryos in sets:
        if embryos.path != "/" and not cloud.exists(embryos.path):
            changes.append(EmbryoChange(embryos.path, missing=True))
            continue
        raw = cloud.get(_in_project(embryos.path, MANIFEST))
        try:
            there = json.loads(raw) if raw is not None else None
        except ValueError:
            there = None
        have, want = _files(there), _files(embryos.manifest)
        nothing = there is None and not embryos.manifest["tree"]  # no templates, none uploaded
        changes.append(EmbryoChange(
            embryos.path,
            manifest_changed=there != embryos.manifest and not nothing,
            upload=sorted(path for path, sha in want.items() if have.get(path) != sha),
            remove=sorted(path for path in have if path not in want),
        ))
    return changes


def send(embryos: EmbryoSet, change: EmbryoChange, cloud) -> None:
    """Upload the changed files, then the manifest, then remove what no birth copies."""
    if change.missing:
        return
    made = set()

    def folder(rel: str) -> None:
        parts = rel.split("/")
        for depth in range(1, len(parts) + 1):
            path = "/".join(parts[:depth])
            if path not in made:
                cloud.mkcol(_in_project(embryos.path, path))
                made.add(path)

    if change.manifest_changed or change.upload:
        folder(PAYLOAD)
    if change.manifest_changed:  # a folder per embryo, also where a birth copies nothing
        for embryo in _paths(embryos.manifest["tree"]):
            folder(f"{PAYLOAD}/{embryo}")
    for rel in change.upload:
        folder(f"{PAYLOAD}/{rel}".rsplit("/", 1)[0])
        cloud.put(_in_project(embryos.path, f"{PAYLOAD}/{rel}"), embryos.payload[rel].read_bytes())
    if change.manifest_changed:
        data = json.dumps(embryos.manifest, ensure_ascii=False, indent=1).encode()
        cloud.put(_in_project(embryos.path, MANIFEST), data)
    for rel in change.remove:
        cloud.delete(_in_project(embryos.path, f"{PAYLOAD}/{rel}"))


def cloud_paths(embryos: EmbryoSet) -> List[str]:
    """Every entry the upload of embryos creates (relative to the Team folder), parents first."""
    if not embryos.manifest["tree"] and not embryos.payload:
        return []
    paths = [_in_project(embryos.path, ".MyOS"), _in_project(embryos.path, MANIFEST), _in_project(embryos.path, PAYLOAD)]
    paths.extend(_in_project(embryos.path, f"{PAYLOAD}/{embryo}") for embryo in _paths(embryos.manifest["tree"]))
    for rel in sorted(embryos.payload):
        parts = rel.split("/")
        for depth in range(1, len(parts) + 1):
            path = _in_project(embryos.path, f"{PAYLOAD}/{'/'.join(parts[:depth])}")
            if path not in paths:
                paths.append(path)
    return paths


def readable_paths(sets: List[EmbryoSet]) -> List[Tuple[str, Optional[str]]]:
    """
    (path, reader) for core.acl_nextcloud.plan: each project's list of embryos for everyone
    with rights in it (None), each embryo's folder for who may read the folder it becomes -
    who may do nothing there sees neither the embryo nor its template.
    """
    found: List[Tuple[str, Optional[str]]] = []
    for embryos in sets:
        if not cloud_paths(embryos):
            continue
        found.append((_in_project(embryos.path, PAYLOAD), None))
        for embryo in _paths(embryos.manifest["tree"]):
            found.append((_in_project(embryos.path, f"{PAYLOAD}/{embryo}"), _in_project(embryos.path, embryo)))
    return found
