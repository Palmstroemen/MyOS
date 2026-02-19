#!/usr/bin/env python3
"""
sort.py - Persistent Sort.md parsing, validation, and rule resolution.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from core.project import find_config_in_parents

DATE_TOKENS = {"YYYY", "YY", "MM", "MMMM", "DD"}
ALL_TOKENS = DATE_TOKENS | {"ABC"}
_TOKEN_RE = re.compile(r"\{\{([A-Z]+)\}\}")
_KEY_VALUE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.+?)\s*$")
_HEADER_RE = re.compile(r"^\s*#{1,6}\s+Sort\s*$", re.IGNORECASE)

_VALID_APPLY_ON = {"create", "move", "both"}
_VALID_MATERIALIZATION = {"on_use"}
_VALID_CONFLICT = {"rename", "skip", "error"}
_VALID_DATE_SOURCES = {"exif_created", "frontmatter_date", "fs_mtime", "fs_created"}


@dataclass(frozen=True)
class SortRule:
    source_path: Path
    owner_root: Path
    root: str
    pattern: str
    date_sources: List[str]
    apply_on: str
    materialization: str
    conflict: str
    enabled: bool
    warnings: List[str] = field(default_factory=list)

    @property
    def root_path(self) -> Path:
        rel = self.root.strip("/")
        return self.owner_root if not rel else (self.owner_root / rel).resolve()


def parse_sort_config(path: Union[str, Path]) -> List[SortRule]:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists() or not config_path.is_file():
        return []
    owner_root = config_path.parent.parent
    try:
        text = config_path.read_text(encoding="utf-8")
    except Exception:
        return []
    sections = _parse_sort_sections(text)
    rules: List[SortRule] = []
    for section in sections:
        rule = _to_rule(section, source_path=config_path, owner_root=owner_root)
        if rule is not None:
            rules.append(rule)
    return rules


def resolve_effective_sort_rules(
    start_path: Union[str, Path],
    *,
    template_root: Optional[Union[str, Path]] = None,
    global_root: Optional[Union[str, Path]] = None,
    config_name: str = "Sort.md",
) -> List[SortRule]:
    target = Path(start_path).expanduser().resolve()
    if target.is_file():
        target = target.parent

    local = find_config_in_parents(
        target,
        config_name,
        require_project_marker=True,
        honor_inherit_not=True,
    )
    if local is not None:
        return parse_sort_config(local)

    if template_root is not None:
        template_cfg = Path(template_root).expanduser().resolve() / ".MyOS" / config_name
        if template_cfg.exists() and template_cfg.is_file():
            return parse_sort_config(template_cfg)

    if global_root is not None:
        global_cfg = Path(global_root).expanduser().resolve() / ".MyOS" / config_name
        if global_cfg.exists() and global_cfg.is_file():
            return parse_sort_config(global_cfg)

    return []


def validate_sort_rules(rules: Sequence[SortRule]) -> List[str]:
    messages: List[str] = []
    for idx, rule in enumerate(rules):
        prefix = f"rule[{idx}]"
        dynamic_segments = _pattern_segments(rule.pattern)
        if any(".." in seg for seg in dynamic_segments):
            messages.append(f"{prefix}: pattern must not contain '..'")
        token_hits = _extract_tokens(rule.pattern)
        unknown = [t for t in token_hits if t not in ALL_TOKENS]
        if unknown:
            messages.append(f"{prefix}: unknown tokens {unknown}")
        date_hits = [t for t in token_hits if t in DATE_TOKENS]
        if len(set(date_hits)) != len(date_hits):
            messages.append(f"{prefix}: duplicate date token in one pattern branch")
        if len(dynamic_segments) > 5:
            messages.append(f"{prefix}: warning high depth may create many subfolders")
    return messages


def iter_sort_rule_roots(rules: Sequence[SortRule]) -> Iterable[Path]:
    seen: set[str] = set()
    for rule in rules:
        root = rule.root_path
        key = str(root)
        if key in seen:
            continue
        seen.add(key)
        yield root


def _parse_sort_sections(text: str) -> List[Dict[str, str]]:
    sections: List[Dict[str, str]] = []
    active: Dict[str, str] = {}
    in_sort = False
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if _HEADER_RE.match(line):
            if active:
                sections.append(dict(active))
                active = {}
            in_sort = True
            continue
        if not in_sort:
            continue
        if not line:
            if active:
                sections.append(dict(active))
                active = {}
            in_sort = False
            continue
        match = _KEY_VALUE_RE.match(line.lstrip("#").strip())
        if not match:
            continue
        key = str(match.group(1) or "").strip().lower()
        value = str(match.group(2) or "").strip()
        if key and value:
            active[key] = value
    if active:
        sections.append(dict(active))
    return sections


def _to_rule(section: Dict[str, str], *, source_path: Path, owner_root: Path) -> Optional[SortRule]:
    root = _normalize_root(section.get("root"))
    pattern = _normalize_pattern(section.get("pattern"))
    if not root or not pattern:
        return None
    date_sources = _normalize_date_sources(section.get("datesource"))
    apply_on = _normalize_apply_on(section.get("applyon"))
    materialization = _normalize_materialization(section.get("materialization"))
    conflict = _normalize_conflict(section.get("conflict"))
    enabled = _normalize_enabled(section.get("enabled"))
    warnings: List[str] = []
    tokens = _extract_tokens(pattern)
    duplicate_date_tokens = [token for token in tokens if token in DATE_TOKENS and tokens.count(token) > 1]
    if duplicate_date_tokens:
        warnings.append("duplicate date token in pattern branch")
    if len(_pattern_segments(pattern)) > 5:
        warnings.append("high depth may create many subfolders")
    return SortRule(
        source_path=source_path,
        owner_root=owner_root,
        root=root,
        pattern=pattern,
        date_sources=date_sources,
        apply_on=apply_on,
        materialization=materialization,
        conflict=conflict,
        enabled=enabled,
        warnings=warnings,
    )


def _normalize_root(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    if ".." in text or "\\" in text:
        return None
    if not text.startswith("/"):
        text = f"/{text}"
    text = re.sub(r"/{2,}", "/", text)
    if text != "/":
        text = text.rstrip("/")
    return text


def _normalize_pattern(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return None
    if text.startswith("/"):
        text = text[1:]
    text = re.sub(r"/{2,}", "/", text.strip("/"))
    if not text:
        return None
    return text


def _normalize_date_sources(value: Optional[str]) -> List[str]:
    raw = str(value or "").strip()
    if not raw:
        return ["exif_created", "frontmatter_date", "fs_mtime"]
    values = [v.strip().lower() for v in raw.split(",") if v.strip()]
    normalized = [v for v in values if v in _VALID_DATE_SOURCES]
    return normalized or ["exif_created", "frontmatter_date", "fs_mtime"]


def _normalize_apply_on(value: Optional[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in _VALID_APPLY_ON else "both"


def _normalize_materialization(value: Optional[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in _VALID_MATERIALIZATION else "on_use"


def _normalize_conflict(value: Optional[str]) -> str:
    text = str(value or "").strip().lower()
    return text if text in _VALID_CONFLICT else "rename"


def _normalize_enabled(value: Optional[str]) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "on"}


def _extract_tokens(pattern: str) -> List[str]:
    return [str(m.group(1) or "").strip().upper() for m in _TOKEN_RE.finditer(str(pattern or "")) if m.group(1)]


def _pattern_segments(pattern: str) -> List[str]:
    return [seg for seg in str(pattern or "").split("/") if seg]


def format_token(token: str, dt: _dt.datetime, name: str) -> str:
    token_name = str(token or "").strip().upper()
    if token_name == "YYYY":
        return f"{dt.year:04d}"
    if token_name == "YY":
        return f"{dt.year % 100:02d}"
    if token_name == "MM":
        return f"{dt.month:02d}"
    if token_name == "MMMM":
        return dt.strftime("%B")
    if token_name == "DD":
        return f"{dt.day:02d}"
    if token_name == "ABC":
        letter = (str(name or "").strip()[:1] or "_").upper()
        return letter if "A" <= letter <= "Z" else "_"
    return ""
