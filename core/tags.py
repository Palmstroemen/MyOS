#!/usr/bin/env python3
"""
tags.py - MyOS tag storage utilities.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
import os

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
