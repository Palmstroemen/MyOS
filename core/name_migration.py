# name_migration.py - what carries a former name moves over to the current one (core/brand.py)
#
# A project tree: every settings folder under a former name (.MyOS) is renamed, the rules and
# settings in it that name it (ACLs.md: "/.MyOS/ACLs.md: change", its history, Embryos.json)
# are rewritten, and tags in extended attributes move to the new key. Documents are left as
# they are. The user's settings folder moves the same way. Without apply only the plan.

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Mapping, Optional, Set

from core import brand

TEXT_SUFFIXES = {".md", ".json", ".txt", ".conf", ".log"}


@dataclass(frozen=True)
class Step:
    kind: str  # rewrite, xattr, rename, conflict
    path: Path
    target: Optional[Path] = None
    detail: str = ""

    def __str__(self) -> str:
        target = f" -> {self.target}" if self.target else ""
        detail = f" ({self.detail})" if self.detail else ""
        return f"{self.kind:8} {self.path}{target}{detail}"


def _pattern(names: Iterable[str]) -> Optional[re.Pattern]:
    names = [n for n in names if n]
    if not names:
        return None
    return re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in names) + r")(?![\w.-])")


def _rewrite_files(files: Iterable[Path], apply: bool) -> List[Step]:
    """Text files naming a former settings folder: rewritten to the current one."""
    pattern = _pattern(brand.LEGACY_META_DIRS)
    steps: List[Step] = []
    if pattern is None:
        return steps
    for path in files:
        if path.suffix.lower() not in TEXT_SUFFIXES or path.is_symlink() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, count = pattern.subn(brand.META_DIR, text)
        if count:
            steps.append(Step("rewrite", path, detail=f"{count}x"))
            if apply:
                path.write_text(new, encoding="utf-8")
    return steps


def _walk(root: Path):
    """os.walk below root, sorted.
    Security: To avoid changing what lies outside the tree, symlinks are not followed and
    mounted drives (the perspective drive, other file systems) are not entered."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not os.path.ismount(os.path.join(dirpath, d)))
        yield Path(dirpath), dirnames, sorted(filenames)


def _files_below(folder: Path) -> List[Path]:
    return [dirpath / name for dirpath, _dirs, files in _walk(folder) for name in files]


def _xattrs(root: Path, apply: bool) -> List[Step]:
    """Extended attributes under a former prefix (user.myos.tags) move to the current one."""
    if not hasattr(os, "listxattr") or not brand.LEGACY_XATTR_PREFIXES:
        return []
    steps: List[Step] = []
    paths = [root]
    for dirpath, dirnames, filenames in _walk(root):
        paths.extend(dirpath / n for n in dirnames + filenames)
    for path in paths:
        if path.is_symlink():
            continue
        try:
            keys = os.listxattr(path)
        except OSError:
            continue
        for key in keys:
            prefix = next((p for p in brand.LEGACY_XATTR_PREFIXES if key.startswith(p)), None)
            if prefix is None:
                continue
            new_key = brand.XATTR_PREFIX + key[len(prefix):]
            steps.append(Step("xattr", path, detail=f"{key} -> {new_key}"))
            if apply:
                value = os.getxattr(path, key)
                if new_key not in keys:
                    os.setxattr(path, new_key, value)
                os.removexattr(path, key)
    return steps


def migrate_tree(root, apply: bool = False) -> List[Step]:
    """Move the project tree root over to the current name; what was (or would be) done.
    A settings folder whose parent already has one under the current name is a conflict and
    stays untouched, with everything in it."""
    root = Path(root)
    legacy: List[Path] = []
    for dirpath, dirnames, _files in _walk(root):
        for name in dirnames:
            path = dirpath / name
            if name in brand.LEGACY_META_DIRS and not path.is_symlink():
                legacy.append(path)
    conflicts = [p for p in legacy if (p.parent / brand.META_DIR).exists()]
    blocked: Set[Path] = set(conflicts)
    movable = [p for p in legacy if not any(c == p or c in p.parents for c in blocked)]

    files: List[Path] = []
    seen: Set[Path] = set()
    for folder in movable:
        for path in _files_below(folder):
            if path not in seen and not any(c in path.parents for c in blocked):
                seen.add(path)
                files.append(path)
    steps = _rewrite_files(files, apply)
    steps += _xattrs(root, apply)
    # Deepest first: renaming a folder keeps the paths of those above it valid.
    for folder in sorted(movable, key=lambda p: len(p.parts), reverse=True):
        target = folder.parent / brand.META_DIR
        steps.append(Step("rename", folder, target))
        if apply:
            folder.rename(target)
    steps += [Step("conflict", p, p.parent / brand.META_DIR, "both names exist") for p in conflicts]
    return steps


def migrate_config(env: Optional[Mapping[str, str]] = None, apply: bool = False) -> List[Step]:
    """Move the user's settings folder (~/.config/MyOS) over to the current name."""
    new = brand.config_dir(env)
    steps: List[Step] = []
    for name in brand.LEGACY_CONFIG_DIRS:
        old = new.parent / name
        if not old.is_dir() or old == new:
            continue
        if new.exists():
            steps.append(Step("conflict", old, new, "both names exist"))
            continue
        steps += _rewrite_files(_files_below(old), apply)
        steps.append(Step("rename", old, new))
        old_file = f"{name}.conf"
        has_file = (old / old_file).is_file()
        if apply:
            old.rename(new)
        if has_file:
            steps.append(Step("rename", new / old_file, new / f"{brand.CONFIG_DIR}.conf"))
            if apply:
                (new / old_file).rename(new / f"{brand.CONFIG_DIR}.conf")
    return steps
