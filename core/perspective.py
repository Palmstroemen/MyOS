#!/usr/bin/env python3
"""
perspective.py - MyOS perspective configuration handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterable, Tuple

from core.config.parser import MarkdownConfigParser


@dataclass(frozen=True)
class PerspectiveConfig:
    name: str
    scope: Optional[str]
    include: List[str]
    exclude: List[str]
    filters: List[str]
    flatten: bool
    groups: List[str]
    desk: Optional[str]

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "PerspectiveConfig":
        data = MarkdownConfigParser.parse_file(path)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "PerspectiveConfig":
        perspective = data.get("Perspective")
        meta = _normalize_section_dict(perspective)

        name = _first_value(meta, "Name")
        if not name:
            raise ValueError("Perspective requires a Name")

        scope = _first_value(meta, "Scope")

        include = _normalize_section_list(data.get("Include"))
        exclude = _normalize_section_list(data.get("Exclude"))
        filters = _normalize_section_list(data.get("Filter"))
        groups = _normalize_section_list(data.get("Group"))

        flatten_values = _normalize_section_list(data.get("Flatten"))
        flatten = False
        if flatten_values:
            flatten = flatten_values[0].lower() in {"true", "yes", "1"}

        desk_values = _normalize_section_list(data.get("Desk"))
        desk = desk_values[0] if desk_values else None

        return cls(
            name=name,
            scope=scope,
            include=include,
            exclude=exclude,
            filters=filters,
            flatten=flatten,
            groups=groups,
            desk=desk,
        )


def find_perspectives(start_path: Union[str, Path]) -> List[Tuple[Path, PerspectiveConfig]]:
    """
    Find perspective configs from the given path upwards.
    Order is most specific first.
    """
    start_path = Path(start_path).expanduser().resolve()
    if start_path.is_file():
        start_path = start_path.parent

    results: List[Tuple[Path, PerspectiveConfig]] = []
    for directory in _walk_up(start_path):
        candidates = [
            directory / "Perspective.md",
            directory / ".MyOS" / "Perspective.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                results.append((candidate, PerspectiveConfig.from_file(candidate)))
    return results


def resolve_active_perspective(
    cwd: Union[str, Path],
    manual: Optional[Union[str, Path]] = None,
) -> Optional[PerspectiveConfig]:
    """
    Resolve the active perspective.
    Manual perspectives override auto perspectives.
    """
    if manual:
        manual_path = Path(manual).expanduser().resolve()
        return PerspectiveConfig.from_file(manual_path)

    perspectives = find_perspectives(cwd)
    if not perspectives:
        return None
    return perspectives[0][1]


def _normalize_section_list(section: Any) -> List[str]:
    if section is None:
        return []
    if isinstance(section, list):
        return [str(item) for item in section if str(item).strip()]
    if isinstance(section, dict):
        items: List[str] = []
        for key, values in section.items():
            if isinstance(values, list):
                items.extend(str(v) for v in values)
            else:
                items.append(str(values))
        return [item for item in items if item.strip()]
    if isinstance(section, str):
        return [section] if section.strip() else []
    return []


def _normalize_section_dict(section: Any) -> Dict[str, List[str]]:
    if section is None:
        return {}
    if isinstance(section, dict):
        return {str(k): _normalize_section_list(v) for k, v in section.items()}
    if isinstance(section, list):
        result: Dict[str, List[str]] = {}
        for item in section:
            if isinstance(item, dict):
                for key, value in item.items():
                    result[str(key)] = _normalize_section_list(value)
        return result
    return {}


def _first_value(meta: Dict[str, List[str]], key: str) -> Optional[str]:
    values = meta.get(key)
    if not values:
        return None
    return values[0]


def _walk_up(start_path: Path) -> Iterable[Path]:
    current = start_path
    while True:
        yield current
        if current == current.parent:
            break
        current = current.parent
