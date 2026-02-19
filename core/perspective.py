#!/usr/bin/env python3
"""
perspective.py - MyOS perspective configuration handling.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterable, Tuple

from core.config.parser import MarkdownConfigParser

_INHERIT_VALUES = {"dynamic", "fix", "not"}


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
    inherit: str = "dynamic"
    flatten_set: bool = False
    desk_set: bool = False

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "PerspectiveConfig":
        data = MarkdownConfigParser.parse_file(path)
        return cls.from_data(data)

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> "PerspectiveConfig":
        perspective = data.get("Perspective")
        meta = _normalize_section_dict(perspective)

        name = _first_value_ci(meta, "Name")
        if not name:
            raise ValueError("Perspective requires a Name")

        scope = _first_value_ci(meta, "Scope")
        inherit = _normalize_inherit(_first_value_ci(meta, "Inherit"))

        include = _normalize_section_list(data.get("Include"))
        exclude = _normalize_section_list(data.get("Exclude"))
        filters = _normalize_section_list(data.get("Filter"))
        groups = _normalize_section_list(data.get("Group"))

        flatten_values = _normalize_section_list(data.get("Flatten"))
        flatten = False
        flatten_set = False
        if flatten_values:
            flatten_set = True
            flatten = flatten_values[0].lower() in {"true", "yes", "1"}

        desk_values = _normalize_section_list(data.get("Desk"))
        desk_set = bool(desk_values)
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
            inherit=inherit,
            flatten_set=flatten_set,
            desk_set=desk_set,
        )


@dataclass(frozen=True)
class PerspectiveLayer:
    source_path: Path
    scope_dir: Path
    config: PerspectiveConfig
    depth: int
    origin_type: str
    source_kind: str
    manual: bool = False


@dataclass(frozen=True)
class EffectivePerspective:
    config: PerspectiveConfig
    layers: List[PerspectiveLayer]
    mode: str
    manual_path: Optional[Path] = None

    def explain_chain(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for layer in self.layers:
            out.append(
                {
                    "name": layer.config.name,
                    "sourcePath": str(layer.source_path),
                    "scopeDir": str(layer.scope_dir),
                    "originType": layer.origin_type,
                    "sourceKind": layer.source_kind,
                    "depth": int(layer.depth),
                    "inherit": layer.config.inherit,
                    "manual": bool(layer.manual),
                }
            )
        return out


def find_perspectives(start_path: Union[str, Path]) -> List[Tuple[Path, PerspectiveConfig]]:
    """
    Find perspective configs from the given path upwards.
    Order is most specific first.
    """
    layers = find_perspectives_layers(start_path)
    return [(layer.source_path, layer.config) for layer in layers]


def find_perspectives_layers(
    start_path: Union[str, Path],
    *,
    template_root: Optional[Union[str, Path]] = None,
    project_root: Optional[Union[str, Path]] = None,
    global_root: Optional[Union[str, Path]] = None,
) -> List[PerspectiveLayer]:
    target = Path(start_path).expanduser().resolve()
    if target.is_file():
        target = target.parent

    template_root_path = _resolve_optional_path(template_root)
    project_root_path = _resolve_optional_path(project_root)
    global_root_path = _resolve_optional_path(global_root)

    layers: List[PerspectiveLayer] = []
    for depth, directory in enumerate(_walk_up(target)):
        for candidate, source_kind in _iter_perspective_candidates(directory):
            if not candidate.exists() or not candidate.is_file():
                continue
            try:
                cfg = PerspectiveConfig.from_file(candidate)
            except Exception:
                continue
            layers.append(
                PerspectiveLayer(
                    source_path=candidate.resolve(),
                    scope_dir=directory,
                    config=cfg,
                    depth=depth,
                    origin_type=_classify_origin_type(
                        candidate.resolve(),
                        template_root=template_root_path,
                        project_root=project_root_path,
                        global_root=global_root_path,
                    ),
                    source_kind=source_kind,
                    manual=False,
                )
            )
    return layers


def resolve_active_perspective(
    cwd: Union[str, Path],
    manual: Optional[Union[str, Path]] = None,
) -> Optional[PerspectiveConfig]:
    """
    Resolve the active perspective.
    Manual perspectives override auto perspectives.
    """
    effective = resolve_effective_perspective(cwd, manual=manual)
    if effective is None:
        return None
    return effective.config


def resolve_effective_perspective(
    cwd: Union[str, Path],
    manual: Optional[Union[str, Path]] = None,
    *,
    template_root: Optional[Union[str, Path]] = None,
    project_root: Optional[Union[str, Path]] = None,
    global_root: Optional[Union[str, Path]] = None,
) -> Optional[EffectivePerspective]:
    if manual:
        manual_path = Path(manual).expanduser().resolve()
        cfg = PerspectiveConfig.from_file(manual_path)
        layer = PerspectiveLayer(
            source_path=manual_path,
            scope_dir=manual_path.parent,
            config=cfg,
            depth=0,
            origin_type="manual",
            source_kind="manual",
            manual=True,
        )
        return EffectivePerspective(config=cfg, layers=[layer], mode="manual", manual_path=manual_path)

    layers = find_perspectives_layers(
        cwd,
        template_root=template_root,
        project_root=project_root,
        global_root=global_root,
    )
    if not layers:
        return None

    # Merge from least specific to most specific.
    merged_layers: List[PerspectiveLayer] = []
    include: List[str] = []
    exclude: List[str] = []
    filters: List[str] = []
    groups: List[str] = []
    flatten_value = False
    flatten_set = False
    desk_value: Optional[str] = None
    desk_set = False
    effective_name = ""
    effective_scope: Optional[str] = None
    effective_inherit = "dynamic"
    locked_by_fix = False

    for layer in reversed(layers):
        if locked_by_fix:
            break
        cfg = layer.config
        if cfg.inherit == "not":
            merged_layers = []
            include = []
            exclude = []
            filters = []
            groups = []
            flatten_value = False
            flatten_set = False
            desk_value = None
            desk_set = False
        merged_layers.append(layer)
        effective_name = cfg.name
        effective_scope = cfg.scope
        effective_inherit = cfg.inherit
        include = _append_dedup(include, cfg.include)
        exclude = _append_dedup(exclude, cfg.exclude)
        filters = _append_dedup(filters, cfg.filters)
        groups = _append_dedup(groups, cfg.groups)
        if cfg.flatten_set:
            flatten_value = bool(cfg.flatten)
            flatten_set = True
        if cfg.desk_set:
            desk_value = cfg.desk
            desk_set = True
        if cfg.inherit == "fix":
            locked_by_fix = True

    effective_cfg = PerspectiveConfig(
        name=effective_name or merged_layers[-1].config.name,
        scope=effective_scope,
        include=include,
        exclude=exclude,
        filters=filters,
        flatten=flatten_value,
        groups=groups,
        desk=desk_value,
        inherit=effective_inherit,
        flatten_set=flatten_set,
        desk_set=desk_set,
    )
    # Keep layers in specificity order for display.
    return EffectivePerspective(
        config=effective_cfg,
        layers=list(reversed(merged_layers)),
        mode="auto",
        manual_path=None,
    )


def project_entries(
    entries: List[Dict[str, Any]],
    *,
    cwd: Union[str, Path],
    perspective: Optional[EffectivePerspective],
    project_root: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    if not perspective:
        return list(entries or [])
    cfg = perspective.config
    cwd_path = Path(cwd).expanduser().resolve()
    project_root_path = _resolve_optional_path(project_root)

    projected: List[Dict[str, Any]] = []
    for raw in list(entries or []):
        item = dict(raw or {})
        name = str(item.get("name") or "").strip()
        raw_path = str(item.get("path") or "").strip()
        item_path = Path(raw_path).expanduser().resolve() if raw_path else (cwd_path / name).resolve()
        if not _matches_entry(item_path, name, cfg, cwd_path, project_root_path):
            continue
        item["path"] = str(item_path)
        item["originPath"] = str(item_path)
        item["perspectiveActive"] = True
        item["perspectiveName"] = cfg.name
        group_key = _group_key_for_entry(item, cfg.groups, cwd_path, project_root_path)
        if group_key:
            item["perspectiveGroup"] = group_key
        projected.append(item)

    if cfg.groups:
        projected.sort(
            key=lambda item: (
                str(item.get("perspectiveGroup") or ""),
                str(item.get("name") or "").lower(),
            )
        )
    return projected


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


def _first_value_ci(meta: Dict[str, List[str]], key: str) -> Optional[str]:
    lookup = str(key or "").strip().lower()
    for current_key, values in meta.items():
        if str(current_key or "").strip().lower() == lookup:
            if not values:
                return None
            return values[0]
    return None


def _normalize_inherit(value: Optional[str]) -> str:
    current = str(value or "").strip().lower()
    if current in _INHERIT_VALUES:
        return current
    return "dynamic"


def _append_dedup(existing: List[str], values: List[str]) -> List[str]:
    out = list(existing or [])
    seen = {str(item) for item in out}
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _resolve_optional_path(value: Optional[Union[str, Path]]) -> Optional[Path]:
    if value is None:
        return None
    try:
        return Path(value).expanduser().resolve()
    except Exception:
        return None


def _iter_perspective_candidates(directory: Path) -> Iterable[Tuple[Path, str]]:
    yield (directory / "Perspective.md", "folder")
    yield (directory / ".MyOS" / "Perspective.md", "myos")
    collection_dir = directory / ".MyOS" / "Perspectives"
    if collection_dir.exists() and collection_dir.is_dir():
        for child in sorted(collection_dir.iterdir(), key=lambda item: item.name.lower()):
            if child.is_file() and child.suffix.lower() == ".md":
                yield (child, "collection")


def _is_within(path: Path, root: Optional[Path]) -> bool:
    if root is None:
        return False
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _classify_origin_type(
    candidate: Path,
    *,
    template_root: Optional[Path],
    project_root: Optional[Path],
    global_root: Optional[Path],
) -> str:
    if _is_within(candidate, template_root):
        return "template"
    if _is_within(candidate, project_root):
        return "project"
    if _is_within(candidate, global_root):
        return "global"
    return "folder"


def _normalized_path_variants(path: Path, cwd: Path, project_root: Optional[Path], name: str) -> List[str]:
    abs_path = "/" + str(path).replace("\\", "/").lstrip("/")
    variants = [abs_path, str(path).replace("\\", "/"), name]
    try:
        rel_cwd = str(path.relative_to(cwd)).replace("\\", "/")
        variants.append(rel_cwd)
    except ValueError:
        pass
    if project_root is not None:
        try:
            rel_project = str(path.relative_to(project_root)).replace("\\", "/")
            variants.append(rel_project)
            variants.append("/" + rel_project.lstrip("/"))
        except ValueError:
            pass
    return [str(value or "") for value in variants if str(value or "")]


def _matches_rule(rule: str, variants: List[str]) -> bool:
    current = str(rule or "").strip()
    if not current:
        return False
    has_wildcard = any(token in current for token in ["*", "?", "["])
    is_path_rule = "/" in current or current.startswith("/")
    normalized_rule = current.replace("\\", "/")
    for variant in variants:
        token = variant.replace("\\", "/")
        if has_wildcard:
            if fnmatch(token, normalized_rule):
                return True
            continue
        if is_path_rule:
            prefix = normalized_rule.rstrip("/")
            if token == prefix or token.startswith(prefix + "/"):
                return True
            continue
        if token == normalized_rule or normalized_rule in token:
            return True
    return False


def _matches_entry(
    item_path: Path,
    name: str,
    cfg: PerspectiveConfig,
    cwd: Path,
    project_root: Optional[Path],
) -> bool:
    variants = _normalized_path_variants(item_path, cwd, project_root, name)

    includes = list(cfg.include or [])
    if includes:
        if not any(_matches_rule(rule, variants) for rule in includes):
            return False
    excludes = list(cfg.exclude or [])
    if excludes:
        if any(_matches_rule(rule, variants) for rule in excludes):
            return False
    filters = list(cfg.filters or [])
    if filters:
        if not any(_matches_rule(rule, variants) for rule in filters):
            return False
    return True


def _group_key_for_entry(
    entry: Dict[str, Any],
    groups: List[str],
    cwd: Path,
    project_root: Optional[Path],
) -> str:
    path_text = str(entry.get("path") or "")
    item_path = Path(path_text).expanduser().resolve() if path_text else cwd
    tags = [str(tag or "").strip() for tag in (entry.get("tags") or []) if str(tag or "").strip()]

    parts: List[str] = []
    for raw_group in groups or []:
        group = str(raw_group or "").strip().lower()
        if group == "project":
            if project_root is not None:
                parts.append(project_root.name or str(project_root))
            else:
                parts.append("project")
        elif group == "folder":
            parts.append(item_path.parent.name if item_path.parent else "")
        elif group == "tag":
            parts.append(tags[0] if tags else "")
        elif group == "tags":
            parts.append(tags[0] if tags else "")
        elif group == "date":
            parts.append(str(entry.get("mtimeDate") or ""))
        else:
            parts.append(group)
    return " | ".join([part for part in parts if part])


def _walk_up(start_path: Path) -> Iterable[Path]:
    current = start_path
    while True:
        yield current
        if current == current.parent:
            break
        current = current.parent
