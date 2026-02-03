#!/usr/bin/env python3
"""
importer.py - MyOS import utilities.
Imports a subtree from an export package with security checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, Dict
import logging
import os
import shutil
import tempfile
import zipfile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImportResult:
    import_root: Path
    subtree_path: Path


def import_package(
    package_path: Union[str, Path],
    target_root: Optional[Union[str, Path]] = None,
    mode: str = "adopt",
    conflict: str = "merge",
) -> ImportResult:
    """
    Import an export package into a target location.

    Args:
        package_path: Path to an export folder or zip archive.
        target_root: Target root when adopting or overriding restore.
        mode: "restore" or "adopt".
        conflict: "merge", "overwrite", or "skip".

    Returns:
        ImportResult describing the import.
    """
    package_path = Path(package_path).expanduser().resolve()

    if package_path.is_file() and package_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmpdir:
            extracted = Path(tmpdir) / "package"
            extracted.mkdir(parents=True, exist_ok=True)
            _safe_extract_zip(package_path, extracted)
            return _import_from_folder(extracted, target_root, mode, conflict)

    if package_path.is_dir():
        return _import_from_folder(package_path, target_root, mode, conflict)

    raise FileNotFoundError(f"Import package not found: {package_path}")


def _import_from_folder(
    package_root: Path,
    target_root: Optional[Union[str, Path]],
    mode: str,
    conflict: str,
) -> ImportResult:
    project_md = package_root / ".MyOS" / "Project.md"
    if not project_md.exists():
        raise ValueError("Invalid package: missing .MyOS/Project.md")

    metadata = _read_export_metadata(project_md)
    subtree = metadata.get("Subtree")
    if not subtree:
        raise ValueError("Missing Subtree in export metadata")

    subtree_path = _validate_subtree_path(subtree)
    source_subtree = package_root / subtree_path
    if not source_subtree.exists():
        raise FileNotFoundError(f"Subtree not found in package: {subtree_path}")

    import_root = _resolve_import_root(metadata, target_root, mode)
    dest_subtree = import_root / subtree_path
    _copy_tree_secure(source_subtree, dest_subtree, conflict)

    return ImportResult(import_root=import_root, subtree_path=subtree_path)


def _resolve_import_root(
    metadata: Dict[str, str],
    target_root: Optional[Union[str, Path]],
    mode: str,
) -> Path:
    if mode not in {"restore", "adopt"}:
        raise ValueError(f"Invalid mode: {mode}")

    if mode == "restore":
        ref = metadata.get("ReferencePath")
        if ref:
            ref_path = Path(ref)
            if ref_path.exists():
                return ref_path

    if target_root is None:
        raise ValueError("target_root is required for adopt mode or missing reference path")

    return Path(target_root).expanduser().resolve()


def _read_export_metadata(project_md: Path) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    for line in project_md.read_text().splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            if key in {"ReferencePath", "Subtree", "ExportedAt", "Source"}:
                metadata[key] = value.strip()
    return metadata


def _validate_subtree_path(subtree: str) -> Path:
    subtree = subtree.strip()
    if subtree.startswith("/"):
        subtree = subtree[1:]
    path = Path(subtree)
    if path.is_absolute():
        raise ValueError("Subtree path must be relative")
    if ".." in path.parts:
        raise ValueError("Subtree path traversal not allowed")
    return path


def _copy_tree_secure(src: Path, dst: Path, conflict: str) -> None:
    if conflict not in {"merge", "overwrite", "skip"}:
        raise ValueError(f"Invalid conflict mode: {conflict}")

    for root, dirs, files in os.walk(src, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(src)
        target_root = dst / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        for name in list(dirs):
            if (root_path / name).is_symlink():
                raise ValueError("Symlinked directories are not allowed in import")

        for name in files:
            src_file = root_path / name
            if src_file.is_symlink():
                raise ValueError("Symlinked files are not allowed in import")
            dest_file = target_root / name
            if dest_file.exists():
                if conflict == "skip" or conflict == "merge":
                    continue
                if conflict == "overwrite":
                    dest_file.unlink()
            shutil.copy2(src_file, dest_file)


def _safe_extract_zip(zip_path: Path, dest: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            name = member.filename
            if name.startswith(("/", "\\")) or ":" in name:
                raise ValueError("Unsafe path in zip archive")
            member_path = (dest / name).resolve()
            if not str(member_path).startswith(str(dest.resolve())):
                raise ValueError("Zip traversal detected")
            zf.extract(member, dest)
