#!/usr/bin/env python3
"""
tags.py - MyOS tag storage utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Union
import os

from core.project import find_config_in_parents

XATTR_KEY = "user.myos.tags"


def read_tags(path: Path) -> Dict[str, Optional[int]]:
    if not hasattr(os, "getxattr"):
        return {}
    try:
        raw = os.getxattr(str(path), XATTR_KEY)
    except (OSError, AttributeError):
        return {}
    try:
        value = raw.decode("utf-8").strip()
    except Exception:
        return {}
    if not value:
        return {}
    return _parse_tags(value)


def write_tags(path: Path, tags: Dict[str, Optional[int]]) -> None:
    if not hasattr(os, "setxattr"):
        raise RuntimeError("xattr not supported on this platform")
    value = _format_tags(tags)
    os.setxattr(str(path), XATTR_KEY, value.encode("utf-8"))


def _parse_tags(raw: str) -> Dict[str, Optional[int]]:
    tags: Dict[str, Optional[int]] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, val = item.split("=", 1)
            key = key.strip()
            val = val.strip()
            if not key:
                continue
            try:
                tags[key] = int(val)
            except ValueError:
                tags[key] = None
        else:
            tags[item] = None
    return tags


def _format_tags(tags: Dict[str, Optional[int]]) -> str:
    parts = []
    for key, val in tags.items():
        if val is None:
            parts.append(key)
        else:
            parts.append(f"{key}={val}")
    return ", ".join(parts)


def hash_line_tags(text: str) -> List[str]:
    """The tags of a Tags.md text: its lines "#Tag" ("# Tags", hashes then a space, is a
    Markdown heading, not a tag), sorted, each once."""
    tags: List[str] = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line.startswith("#") or line.lstrip("#")[:1].isspace():
            continue
        tag = line.lstrip("#").strip()
        if tag:
            tags.append(tag)
    return sorted(set(tags), key=str.lower)


def tag_list(path: Union[str, Path]) -> List[str]:
    """The tags of the Tags.md at path; none when it cannot be read."""
    try:
        return hash_line_tags(Path(path).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


def project_tags(folder: Union[str, Path]) -> List[str]:
    """The tags suggested in folder: those of the .MyOS/Tags.md of the nearest project up the
    path that has one - like other configs it inherits, a subproject without one takes its
    parent's."""
    tags_file = find_config_in_parents(Path(folder), "Tags.md", honor_inherit_not=False)
    return tag_list(tags_file) if tags_file is not None else []


def all_project_tags(root: Union[str, Path]) -> List[str]:
    """The tags of every project's Tags.md from root down (hidden folders such as .MyOS with
    its templates skipped), sorted, each once."""
    found = set()
    for folder, dirs, _files in os.walk(Path(root)):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        myos = Path(folder) / ".MyOS"
        if (myos / "Project.md").is_file() and (myos / "Tags.md").is_file():
            found.update(tag_list(myos / "Tags.md"))
    return sorted(found, key=str.lower)
