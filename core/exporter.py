#!/usr/bin/env python3
"""
exporter.py - MyOS export utilities.
Exports a subtree with project metadata, ACLs, and templates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Iterable
import logging
import os
import shutil
import socket

from core.project import ProjectConfig, ProjectFinder

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExportResult:
    package_path: Path
    export_root: Path
    subtree_path: Path
    zip_path: Optional[Path] = None


def export_subtree(
    source_path: Union[str, Path],
    output_dir: Union[str, Path],
    package_name: Optional[str] = None,
    zip_output: bool = False,
) -> ExportResult:
    """
    Export a subtree starting at source_path.

    Args:
        source_path: Path within a project to export.
        output_dir: Directory that will contain the export package folder.
        package_name: Optional folder name for the export package.
        zip_output: When True, also create a zip archive next to the folder.

    Returns:
        ExportResult with package_path, export_root, and subtree_path.
    """
    source_path = Path(source_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()

    export_root = ProjectFinder.find_nearest(source_path)
    if not export_root:
        raise ValueError(f"No project root found for {source_path}")

    export_root = export_root.resolve()
    subtree_rel = source_path.relative_to(export_root)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if package_name is None:
        date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        package_name = f"{export_root.name}_export_{date_stamp}"

    package_path = output_dir / package_name
    if package_path.exists():
        raise FileExistsError(f"Export path already exists: {package_path}")

    logger.debug("Exporting subtree %s from %s", subtree_rel, export_root)

    # Create package root
    package_path.mkdir(parents=True)

    # Copy subtree contents
    _copy_tree_no_symlinks(export_root / subtree_rel, package_path / subtree_rel)

    # Copy project .MyOS from export root
    _copy_tree_no_symlinks(export_root / ".MyOS", package_path / ".MyOS")

    # Add export metadata
    _write_export_metadata(
        project_md=package_path / ".MyOS" / "Project.md",
        reference_path=export_root,
        subtree_path=subtree_rel,
    )

    # Copy templates used by the project
    _copy_templates(export_root, package_path)

    zip_path: Optional[Path] = None
    if zip_output:
        zip_path = _zip_folder(package_path)
        shutil.rmtree(package_path)

    return ExportResult(
        package_path=zip_path if zip_output and zip_path else package_path,
        export_root=export_root,
        subtree_path=subtree_rel,
        zip_path=zip_path,
    )


def _copy_templates(export_root: Path, package_path: Path) -> None:
    config = ProjectConfig(export_root)
    if not config.templates:
        logger.debug("No templates configured for %s", export_root)
        return

    templates_source = _resolve_templates_dir(export_root)
    if not templates_source or not templates_source.exists():
        logger.warning("Templates directory not found for %s", export_root)
        return

    target_root = package_path / "Templates"
    target_root.mkdir(parents=True, exist_ok=True)

    for template_name in config.templates:
        source = templates_source / template_name
        if not source.exists():
            logger.warning("Template '%s' not found in %s", template_name, templates_source)
            continue
        _copy_tree_no_symlinks(source, target_root / template_name)


def _resolve_templates_dir(export_root: Path) -> Optional[Path]:
    env_dir = os.environ.get("MYOS_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return export_root / "Templates"


def _copy_tree_no_symlinks(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Source path not found: {src}")

    for root, dirs, files in os.walk(src, followlinks=False):
        root_path = Path(root)
        rel_root = root_path.relative_to(src)
        target_root = dst / rel_root
        target_root.mkdir(parents=True, exist_ok=True)

        # Filter out symlink dirs
        dirs[:] = [d for d in dirs if not (root_path / d).is_symlink()]

        for name in files:
            src_file = root_path / name
            if src_file.is_symlink():
                continue
            target_file = target_root / name
            shutil.copy2(src_file, target_file)


def _write_export_metadata(project_md: Path, reference_path: Path, subtree_path: Path) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    source_id = f"{os.getenv('USER', 'user')}@{socket.gethostname()}"

    export_block = (
        "\n# Export\n"
        f"ReferencePath: {reference_path}\n"
        f"Subtree: /{subtree_path.as_posix()}\n"
        f"ExportedAt: {timestamp}\n"
        f"Source: {source_id}\n"
    )

    if project_md.exists():
        project_md.write_text(project_md.read_text() + export_block)
    else:
        project_md.parent.mkdir(parents=True, exist_ok=True)
        project_md.write_text("# MyOS Project\n" + export_block)


def _zip_folder(folder: Path) -> Path:
    zip_path = shutil.make_archive(str(folder), "zip", root_dir=folder)
    return Path(zip_path)
