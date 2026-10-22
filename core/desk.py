#!/usr/bin/env python3
"""
desk.py - MyOS desk profile discovery and parsing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from core.perspective import find_filters


_TRUE_VALUES = {"true", "yes", "1", "on"}
_INHERIT_VALUES = {"dynamic", "fix", "not"}


@dataclass(frozen=True)
class DeskConfig:
    source_path: Path
    theme_preset: Optional[str]
    project_icon: Optional[str]
    wallpaper_preset: Optional[str]
    wallpaper_path: Optional[str]
    recent_policy: Optional[str]
    inherit: str
    raw: Dict[str, Any]
    panel_theme: Optional[str] = None  # theme of the taskbar / panels (Cinnamon "Desktop" theme)
    # Programs pinned to the taskbar (.desktop ids, "## Taskbar" list); None: not set here,
    # () : none pinned.
    taskbar: Optional[Tuple[str, ...]] = None

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "DeskConfig":
        desk_path = Path(path).expanduser().resolve()
        try:
            text = desk_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # same as MarkdownConfigParser.parse_file
            text = desk_path.read_text(encoding="latin-1")
        return cls.from_data(desk_path, {"Desk": _desk_section(text)})

    @classmethod
    def from_data(cls, source_path: Path, data: Dict[str, Any]) -> "DeskConfig":
        section = data.get("Desk", {})
        normalized = _normalize_section_dict(section)
        inherit = _normalize_inherit(normalized.get("inherit"))
        return cls(
            source_path=source_path,
            theme_preset=_first(normalized, "themepreset"),
            project_icon=_first(normalized, "projecticon"),
            wallpaper_preset=_first(normalized, "wallpaperpreset"),
            wallpaper_path=_first(normalized, "wallpaperpath"),
            recent_policy=_first(normalized, "recentpolicy"),
            inherit=inherit,
            raw=dict(normalized),
            panel_theme=_first(normalized, "paneltheme"),
            taskbar=tuple(normalized["taskbar"]) if "taskbar" in normalized else None,
        )


def _desk_section(text: str) -> Dict[str, List[str]]:
    """
    "key: value" lines of the "# Desk" section, and the "- item" list under its
    "## Taskbar" subheading (as "Taskbar"; an empty list when the heading has no items).
    Unlike the general config parser, values may contain spaces ("PanelTheme: Linux
    Mint", paths with spaces) and blank lines or notes do not end the section (they would
    silently drop the settings below them); <!-- comments --> and " # ..." at the end of
    a line are ignored. Subheadings stay inside the section, a heading of the same or a
    higher level ends it.
    """
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    values: Dict[str, List[str]] = {}
    desk_level: Optional[int] = None  # heading level of "# Desk" while inside it
    in_taskbar = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if ": " not in heading:  # "#### inherit: not" is a property, not a heading
                level = len(stripped) - len(stripped.lstrip("#"))
                if heading.lower() == "desk":
                    desk_level, in_taskbar = level, False
                elif desk_level is not None and level > desk_level:
                    in_taskbar = heading.lower() == "taskbar"
                    if in_taskbar:
                        values["Taskbar"] = []
                else:
                    desk_level, in_taskbar = None, False
                continue
            stripped = heading
        if desk_level is None:
            continue
        if in_taskbar and stripped[:2] in ("- ", "* "):
            item = re.split(r"\s#", stripped[2:], maxsplit=1)[0].strip()
            if item:
                values["Taskbar"].append(item)
            continue
        key, sep, value = stripped.partition(":")
        value = re.split(r"\s#", value, maxsplit=1)[0].strip()
        if sep and key.strip() and " " not in key.strip() and value:
            values[key.strip()] = [value]
    return values


def find_desks(
    start_path: Union[str, Path],
    *,
    include_root_desk: bool = False,
    boundary: Optional[Path] = None,
) -> List[Tuple[Path, DeskConfig]]:
    """
    Find desk configs from the given path upwards.
    Order is most specific first. With a boundary (the top project of the projects
    tree) only folders inside it count: nothing outside, nothing above it.
    """
    try:
        target = Path(start_path).expanduser().resolve()
    except Exception:
        return []
    if target.is_file():
        target = target.parent
    results: List[Tuple[Path, DeskConfig]] = []
    if boundary is not None:
        boundary = Path(boundary).resolve()
        if target != boundary and boundary not in target.parents:
            return results
    for directory in _walk_up(target):
        if boundary is not None and directory != boundary and boundary not in directory.parents:
            break
        for candidate in _desk_candidates(directory, include_root_desk=include_root_desk):
            if not candidate.exists():
                continue
            config = _try_parse_desk(candidate)
            if config is None:
                if _blocks_inheritance(candidate):
                    return results  # "Inherit: not": nothing from further up
                continue
            results.append((candidate, config))
    return results


def _blocks_inheritance(path: Path) -> bool:
    """A Desk.md without own values that says "Inherit: not"."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        return DeskConfig.from_file(path).inherit == "not"
    except Exception:
        return False


def resolve_active_desk(
    cwd: Union[str, Path],
    *,
    manual: Optional[Union[str, Path]] = None,
    fallback: Optional[Union[str, Path]] = None,
    include_root_desk: bool = False,
    prefer_filter_desk: bool = True,
    boundary: Optional[Path] = None,
) -> Optional[DeskConfig]:
    """
    Resolve the active desk profile for a path.
    Precedence:
      1) manual desk file
      2) desk linked by active filter (optional)
      3) nearest ancestor desk profile
      4) fallback desk file
    """
    fallback_desk = _parse_path(fallback) if fallback else None
    if manual:
        parsed_manual = _parse_path(manual)
        if parsed_manual is not None:
            return _complete(parsed_manual, [fallback_desk])

    try:
        target = Path(cwd).expanduser().resolve()
    except Exception:
        target = None
    if target is None:
        return fallback_desk
    if target.is_file():
        target = target.parent

    chain = [config for _, config in find_desks(target, include_root_desk=include_root_desk, boundary=boundary)]
    cut = next((i for i, config in enumerate(chain) if config.inherit == "not"), None)
    if cut is not None:
        chain = chain[: cut + 1]  # "Inherit: not": nothing from further up
    if prefer_filter_desk:
        filter_desk = _resolve_filter_desk(target)
        if filter_desk is not None:
            chain.insert(0, filter_desk)
    if not chain:
        return fallback_desk
    return _complete(chain[0], chain[1:] + [fallback_desk])


def _parse_path(value: Union[str, Path]) -> Optional[DeskConfig]:
    try:
        path = Path(value).expanduser().resolve()
    except Exception:
        return None
    return _try_parse_desk(path)


# Settings a Desk.md may leave open; each one comes from the nearest desk above that has
# it, at last from the fallback (the user's own desktop). Otherwise the value of the
# project visited before would simply stay. ProjectIcon belongs to its project only.
_INHERITED_FIELDS = ("theme_preset", "panel_theme", "taskbar", "recent_policy")


def _complete(desk: DeskConfig, ancestors: List[Optional[DeskConfig]]) -> DeskConfig:
    """desk, with what it leaves open taken from ancestors (nearest first)."""
    donors = [config for config in ancestors if config is not None]
    values: Dict[str, Any] = {}
    for name in _INHERITED_FIELDS:
        # "is not None": an empty taskbar is a setting (nothing pinned), not a gap.
        values[name] = next((getattr(d, name) for d in [desk, *donors] if getattr(d, name) is not None), None)
    if not (desk.wallpaper_preset or desk.wallpaper_path):
        # Preset and path are one setting: a child's preset must not lose to a parent's path.
        donor = next((d for d in donors if d.wallpaper_preset or d.wallpaper_path), None)
        if donor is not None:
            values["wallpaper_path"] = donor.wallpaper_path
            values["wallpaper_preset"] = _portable_preset(donor)
    raw: Dict[str, Any] = {}
    for config in reversed(donors):
        raw.update(config.raw)
    raw.update(desk.raw)
    return replace(desk, raw=raw, **values)


def _portable_preset(donor: DeskConfig) -> Optional[str]:
    """The donor's wallpaper preset, made absolute: relative presets belong to its folder."""
    preset = str(donor.wallpaper_preset or "").strip()
    if not preset or Path(preset).expanduser().is_absolute():
        return preset or None
    base_dir = donor.source_path.parent.resolve()
    try:
        resolved = (base_dir / preset).resolve()
        # Security: same rule as the backend - a relative preset stays inside its desk folder.
        resolved.relative_to(base_dir)
    except (OSError, ValueError):
        return None
    return str(resolved)


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
            config.panel_theme,
            config.project_icon,
            config.wallpaper_preset,
            config.wallpaper_path,
            config.taskbar is not None,
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
