#!/usr/bin/env python3
"""
desk.py - MyOS desk profile discovery and parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from core.config.parser import MarkdownConfigParser
from core.perspective import find_filters


_TRUE_VALUES = {"true", "yes", "1", "on"}
_INHERIT_VALUES = {"dynamic", "fix", "not"}


@dataclass(frozen=True)
class DeskConfig:
    source_path: Path
    theme_preset: Optional[str]
    wallpaper_preset: Optional[str]
    wallpaper_path: Optional[str]
    dock_preset: Optional[str]
    recent_policy: Optional[str]
    inherit: str
    raw: Dict[str, Any]

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "DeskConfig":
        desk_path = Path(path).expanduser().resolve()
        data = MarkdownConfigParser.parse_file(desk_path)
        return cls.from_data(desk_path, data)

    @classmethod
    def from_data(cls, source_path: Path, data: Dict[str, Any]) -> "DeskConfig":
        section = data.get("Desk", {})
        normalized = _normalize_section_dict(section)
        inherit = _normalize_inherit(normalized.get("inherit"))
        return cls(
            source_path=source_path,
            theme_preset=_first(normalized, "themepreset"),
            wallpaper_preset=_first(normalized, "wallpaperpreset"),
            wallpaper_path=_first(normalized, "wallpaperpath"),
            dock_preset=_first(normalized, "dockpreset"),
            recent_policy=_first(normalized, "recentpolicy"),
            inherit=inherit,
            raw=dict(normalized),
        )


def find_desks(
    start_path: Union[str, Path],
    *,
    include_root_desk: bool = False,
) -> List[Tuple[Path, DeskConfig]]:
    """
    Find desk configs from the given path upwards.
    Order is most specific first.
    """
    try:
        target = Path(start_path).expanduser().resolve()
    except Exception:
        return []
    if target.is_file():
        target = target.parent
    results: List[Tuple[Path, DeskConfig]] = []
    for directory in _walk_up(target):
        for candidate in _desk_candidates(directory, include_root_desk=include_root_desk):
            if not candidate.exists():
                continue
            config = _try_parse_desk(candidate)
            if config is None:
                continue
            results.append((candidate, config))
    return results


def resolve_active_desk(
    cwd: Union[str, Path],
    *,
    manual: Optional[Union[str, Path]] = None,
    fallback: Optional[Union[str, Path]] = None,
    include_root_desk: bool = False,
    prefer_filter_desk: bool = True,
) -> Optional[DeskConfig]:
    """
    Resolve the active desk profile for a path.
    Precedence:
      1) manual desk file
      2) desk linked by active filter (optional)
      3) nearest ancestor desk profile
      4) fallback desk file
    """
    if manual:
        try:
            manual_path = Path(manual).expanduser().resolve()
        except Exception:
            manual_path = None
        parsed_manual = _try_parse_desk(manual_path) if manual_path is not None else None
        if parsed_manual is not None:
            return parsed_manual

    try:
        target = Path(cwd).expanduser().resolve()
    except Exception:
        target = None
    if target is None:
        if fallback:
            try:
                fallback_path = Path(fallback).expanduser().resolve()
            except Exception:
                return None
            return _try_parse_desk(fallback_path)
        return None
    if target.is_file():
        target = target.parent

    if prefer_filter_desk:
        filter_desk = _resolve_filter_desk(target)
        if filter_desk is not None:
            return filter_desk

    matches = find_desks(target, include_root_desk=include_root_desk)
    if matches:
        return matches[0][1]

    if fallback:
        try:
            fallback_path = Path(fallback).expanduser().resolve()
        except Exception:
            return None
        return _try_parse_desk(fallback_path)
    return None


def _resolve_filter_desk(cwd: Path) -> Optional[DeskConfig]:
    for filter_path, filter_cfg in find_filters(cwd):
        desk_ref = str(getattr(filter_cfg, "desk", "") or "").strip()
        if not desk_ref:
            continue
        base_dir = filter_path.parent.resolve()
        try:
            desk_path = (base_dir / desk_ref).expanduser().resolve()
        except Exception:
            continue
        # Security: filter desk references must stay inside their base dir.
        try:
            desk_path.relative_to(base_dir)
        except ValueError:
            continue
        parsed = _try_parse_desk(desk_path)
        if parsed is not None:
            return parsed
    return None


def _try_parse_desk(path: Optional[Path]) -> Optional[DeskConfig]:
    if path is None:
        return None
    # Security: disallow symlinked desk configs to prevent profile escape.
    if path.is_symlink():
        return None
    if not path.exists() or not path.is_file():
        return None
    try:
        parsed = DeskConfig.from_file(path)
    except Exception:
        return None
    if not _has_any_profile_value(parsed):
        return None
    return parsed


def _has_any_profile_value(config: DeskConfig) -> bool:
    return any(
        [
            config.theme_preset,
            config.wallpaper_preset,
            config.wallpaper_path,
            config.dock_preset,
            config.recent_policy,
        ]
    )


def _desk_candidates(directory: Path, *, include_root_desk: bool) -> List[Path]:
    candidates = [directory / ".MyOS" / "Desk.md"]
    if include_root_desk:
        candidates.append(directory / "Desk.md")
    return candidates


def _normalize_section_dict(section: Any) -> Dict[str, List[str]]:
    if section is None:
        return {}
    if isinstance(section, dict):
        return {str(key).strip().lower(): _normalize_to_list(value) for key, value in section.items()}
    if isinstance(section, list):
        result: Dict[str, List[str]] = {}
        for item in section:
            if isinstance(item, dict):
                for key, value in item.items():
                    result[str(key).strip().lower()] = _normalize_to_list(value)
        return result
    return {}


def _normalize_to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    else:
        values = [value]
    return [str(item).strip() for item in values if str(item).strip()]


def _normalize_inherit(values: Optional[List[str]]) -> str:
    if not values:
        return "dynamic"
    first = str(values[0]).strip().lower()
    if first in _INHERIT_VALUES:
        return first
    return "dynamic"


def _first(data: Dict[str, List[str]], key: str) -> Optional[str]:
    values = data.get(key.lower(), [])
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


def env_flag_is_true(value: Optional[str]) -> bool:
    return str(value or "").strip().lower() in _TRUE_VALUES
