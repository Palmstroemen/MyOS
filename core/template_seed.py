# template_seed.py - a new project gets what its templates' root .MyOS holds
#
# Templates are ordinary folder structures. Whatever lies in Templates/<name>/.MyOS
# (ACLs.md, Desk.md, Color.md, ...) is copied into the .MyOS of a project when it is
# created, like the .MyOS of a template folder when an embryo is born. Nothing already in
# the project is overwritten; with several templates the first one that has a file wins.
# See "Designdocument ACLs.md", 10.

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List

from core.acl import _resolve_templates_dir, find_acl_project_root
from core.acl_edit import complete_people
from core.identity import acl_user_for
from core.project import ProjectConfig

logger = logging.getLogger(__name__)


def seed_from_templates(project_root: Path) -> List[Path]:
    """Copy the files of the templates' root .MyOS into project_root/.MyOS; the copies."""
    project_root = Path(project_root).resolve()
    # Before ACLs.md is copied: who the creator is and which ACLs governed the place so far.
    previous_root = find_acl_project_root(project_root)
    creator = acl_user_for(project_root)
    templates_dir = _resolve_templates_dir(project_root)
    if templates_dir is None:
        return []
    copied: List[Path] = []
    for name in ProjectConfig(project_root).get_effective_templates() or []:
        source_dir = templates_dir / name / ".MyOS"
        if source_dir.is_symlink() or not source_dir.is_dir():
            continue
        for source in sorted(source_dir.iterdir()):
            # Security: plain files only - no symlinks (they could point anywhere), no
            # folders (the template's own ACLs-history, Trash), no hidden drafts.
            if source.name.startswith(".") or source.is_symlink() or not source.is_file():
                continue
            target = project_root / ".MyOS" / source.name
            if target.exists() or target.is_symlink():
                continue
            shutil.copyfile(source, target)
            copied.append(target)
    acl_file = project_root / ".MyOS" / "ACLs.md"
    if acl_file in copied and previous_root is not None and previous_root != project_root:
        complete_people(acl_file, previous_root / ".MyOS" / "ACLs.md", creator)
    return copied
