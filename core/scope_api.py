from __future__ import annotations

from pathlib import Path
import functools
import grp
import os
import pwd
import stat
import subprocess
import sys
import re
import shutil
import json
import shlex
from typing import Callable, Iterable, List, Optional, Dict, Any, Tuple, TypedDict
from core.tags import read_tags
from core.acl import ACLAuthorizer, _resolve_templates_dir, find_acl_project_root, is_template_root
from core.acl_edit import (
    ACLEditError,
    ACLPersonExistsError,
    ACLSelfLockoutError,
    add_user,
    can_edit as acl_can_edit,
    check_move_rules,
    move_rules as move_acl_rules,
    own_rule as own_acl_rule,
    set_role_rights,
    set_user_roles,
)
from core.acl_view import ACLView
from core.identity import acl_user_for, claim_person, claimable_people
from core.project_unmake import ProjectHasOwnSettings, can_unmake, unmake_project
from core.xray import xray_listing
from core import trash
from core.project import find_config_in_parents
from core.acl_enforcement import ACLCheckRequest, ACLCheckResult, ACLEnforcementService
from core.desk import DeskConfig
from core.desk_service import DeskService
from core.perspective import (
    EffectiveFilter,
    apply_filter_projection,
    find_filters_layers,
    resolve_effective_filter,
)
from core.filing import destination_for, file_due, sorted_folder_for, sorted_folders, virtual_groups, virtual_listing

try:
    from core.localBlueprintLayer import Blueprint
    from core.project import ProjectConfig, notify_config_changed as notify_project_config_changed
except Exception:  # pragma: no cover - optional for non-MyOS paths
    Blueprint = None
    notify_project_config_changed = None


def _move_to_system_trash(path: Path) -> None:
    """
    Move path into the user's trash (freedesktop, via gio). Raises when that is not
    possible: deleting outside projects must never fall back to deleting for good.
    """
    gio = shutil.which("gio")
    if not gio:
        raise OSError("no system trash available (gio not found)")
    subprocess.run([gio, "trash", "--", str(path)], check=True, capture_output=True, timeout=30)


# The rule "Enable sorting" gives a folder (see "Designdocument Sort.md").
SORT_RULE_SEED = (
    "# Sort\n"
    "Pattern: {{YYYY}}/{{MM}}\n"
    "DateSource: exif, filename, frontmatter, modified\n"
    "NewLevelFrom: 20\n"
)


def find_project_root(start_path: Path) -> Optional[Path]:
    """Project root = directory that has .MyOS/Project.md. .MyOS/ alone is not enough."""
    start_path = start_path.resolve()
    for candidate in [start_path] + list(start_path.parents):
        if (candidate / ".MyOS" / "Project.md").exists():
            return candidate
    return None


def find_top_project_root(start_path: Path) -> Optional[Path]:
    start_path = start_path.resolve()
    found: Optional[Path] = None
    for candidate in [start_path] + list(start_path.parents):
        if (candidate / ".MyOS" / "Project.md").exists():
            found = candidate
    return found


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _read_markdown_tag_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return _extract_hash_line_tags_from_text(text)


def _extract_hash_line_tags_from_text(text: str) -> List[str]:
    tags: List[str] = []
    try:
        for raw in str(text or "").splitlines():
            line = raw.strip()
            if not line.startswith("#"):
                continue
            # "# Tags" (hashes, then a space) is a Markdown heading, not a tag.
            if line.lstrip("#")[:1].isspace():
                continue
            tag = line.lstrip("#").strip()
            if tag:
                tags.append(tag)
    except Exception:
        return []
    return sorted(set(tags), key=str.lower)


_MD_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")
_MD_TAG_RE = re.compile(r"(?<!\w)#([\w\-/]+)", re.UNICODE)
def _strip_wrapping_quotes(value: str) -> str:
    text = str(value or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1].strip()
    return text


def _normalize_tag_value(value: str) -> str:
    text = _strip_wrapping_quotes(value)
    while text.startswith("#"):
        text = text[1:]
    return text.strip()


@functools.lru_cache(maxsize=256)
def _user_name(uid: int) -> str:
    """Login name for a uid (list column "Besitzer"); the number if it has no name."""
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


@functools.lru_cache(maxsize=256)
def _group_name(gid: int) -> str:
    """Group name for a gid (list column "Gruppe"); the number if it has no name."""
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def _split_frontmatter(text: str) -> tuple[str, str]:
    raw = str(text or "")
    if not raw.startswith("---"):
        return "", raw
    lines = raw.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", raw
    closing = -1
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            closing = idx
            break
    if closing < 0:
        return "", raw
    frontmatter = "\n".join(lines[1:closing])
    body = "\n".join(lines[closing + 1 :])
    return frontmatter, body


def _parse_inline_frontmatter_tags(raw_value: str) -> List[str]:
    text = str(raw_value or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    values = []
    for chunk in text.split(","):
        tag = _normalize_tag_value(chunk)
        if tag:
            values.append(tag)
    return values


def _extract_frontmatter_tags(frontmatter: str) -> List[str]:
    lines = str(frontmatter or "").splitlines()
    tags: List[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            idx += 1
            continue
        key_match = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", stripped)
        if not key_match:
            idx += 1
            continue
        key = key_match.group(1).strip().lower()
        value = key_match.group(2)
        if key != "tags":
            idx += 1
            continue
        if value.strip():
            tags.extend(_parse_inline_frontmatter_tags(value))
            idx += 1
            continue
        idx += 1
        while idx < len(lines):
            candidate = lines[idx]
            if not candidate.strip():
                idx += 1
                continue
            list_match = re.match(r"^\s*-\s*(.+)$", candidate)
            if list_match:
                tag = _normalize_tag_value(list_match.group(1))
                if tag:
                    tags.append(tag)
                idx += 1
                continue
            if re.match(r"^\s*[A-Za-z0-9_-]+\s*:", candidate):
                break
            idx += 1
    return sorted(set(tags), key=str.lower)


def _extract_markdown_hashtags(text: str) -> List[str]:
    tags: List[str] = []
    for raw_line in str(text or "").splitlines():
        if _MD_HEADING_RE.match(raw_line):
            continue
        for match in _MD_TAG_RE.finditer(raw_line):
            tag = _normalize_tag_value(match.group(1))
            if tag:
                tags.append(tag)
    return sorted(set(tags), key=str.lower)


def _read_markdown_content_tags(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    frontmatter, body = _split_frontmatter(text)
    tags = _extract_frontmatter_tags(frontmatter)
    tags.extend(_extract_markdown_hashtags(body))
    return sorted(set(tags), key=str.lower)


_MD_TAG_CACHE_VERSION = 1
_MD_TAG_CACHE_FILE = ".TagsHere.json"
_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def _split_stem_and_ext(name: str) -> tuple[str, str]:
    file_name = str(name or "")
    dot = file_name.rfind(".")
    if dot <= 0:
        return file_name, ""
    return file_name[:dot], file_name[dot:]


def _normalize_hex_color(value: str) -> Optional[str]:
    text = str(value or "").strip()
    match = _HEX_COLOR_RE.match(text)
    if not match:
        return None
    return "#" + match.group(1).lower()


def _lighten_hex(color_hex: str, factor: float = 0.72) -> str:
    normalized = _normalize_hex_color(color_hex)
    if not normalized:
        return color_hex
    r = int(normalized[1:3], 16)
    g = int(normalized[3:5], 16)
    b = int(normalized[5:7], 16)
    rn = int(r + (255 - r) * factor)
    gn = int(g + (255 - g) * factor)
    bn = int(b + (255 - b) * factor)
    return f"#{rn:02x}{gn:02x}{bn:02x}"


def _longest_common_prefix(values: List[str]) -> str:
    if not values:
        return ""
    prefix = str(values[0] or "")
    for current in values[1:]:
        text = str(current or "")
        while prefix and not text.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            break
    return prefix


def _clean_entry_name(name: str, *, allow_empty: bool = False) -> Optional[str]:
    cleaned = str(name or "").strip()
    if not cleaned:
        return "" if allow_empty else None
    # // Security: reject control characters to avoid log/terminal injection.
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in cleaned):
        return None
    # // Security: enforce common filesystem-safe charset across platforms.
    if any(ch in cleaned for ch in '<>:"|?*'):
        return None
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        return None
    # // Security: reject pathological names that exceed common FS limits.
    if len(cleaned) > 255:
        return None
    return cleaned


class FolderEntry(TypedDict):
    name: str
    isProject: bool
    isEmbryo: bool
    folderType: int
    color: Optional[str]


class FileEntry(TypedDict):
    name: str
    isDir: bool
    path: str
    tags: List[str]


class FileEntryWithOptionalEmbryo(FileEntry, total=False):
    isEmbryo: bool
    sizeBytes: int
    modifiedTs: float
    accessedTs: float
    permissions: str
    owner: str
    group: str
    # Filled in later by Scope's live measurement (measure_folder_size).
    folderSizeBytes: int


class ScopeApi:
    FOLDER_TYPE_NORMAL = 0
    FOLDER_TYPE_BORN = 1
    FOLDER_TYPE_EMBRYO = 2

    def __init__(self, start_path: str) -> None:
        self.start_path = Path(start_path).expanduser().resolve()
        self.project_root = None
        self.blueprint = None
        self._blueprint_cache: Dict[str, Optional[Any]] = {}
        self._color_cache: Dict[str, Optional[str]] = {}
        self._root_default_project_color: Optional[str] = None
        self._acl_enforcement: Optional[ACLEnforcementService] = None
        # Project the ACL rules were loaded from: their paths are relative to it.
        self._acl_root: Optional[Path] = None
        # Who the user is depends on the project (core.identity); set_acl_enforcement may fix it.
        self._acl_user_override: Optional[str] = None
        self._acl_audit_events: List[Dict[str, Any]] = []
        self._acl_audit_file: Optional[Path] = None
        self._acl_audit_max_bytes: int = 262_144
        self._desk_service = DeskService()
        self.myos_root = find_top_project_root(self.start_path)
        self._set_project_root(find_project_root(self.start_path))
        self._configure_acl_from_env()
        self._refresh_desk_context(self.start_path)

    def _set_project_root(self, root: Optional[Path]) -> None:
        if root and root != getattr(self, "project_root", None):
            # Opening a project removes what has been in its trash longer than trash_days.
            try:
                trash.cleanup(root)
            except Exception:
                pass
        self.project_root = root
        self.blueprint = None
        self._color_cache = {}
        self._root_default_project_color = None
        if self.project_root and Blueprint is not None:
            try:
                self.blueprint = Blueprint(self.project_root)
                self._blueprint_cache[str(self.project_root)] = self.blueprint
            except Exception:
                self.blueprint = None
        if self.project_root:
            self._root_default_project_color = self._read_first_color(
                self.project_root, [".MyOS/Color.md", ".MyOS/Project.md"]
            )

    def get_start_path(self) -> str:
        return str(self.start_path)

    def get_project_root(self) -> Optional[str]:
        return str(self.project_root) if self.project_root else None

    def get_myos_root(self) -> Optional[str]:
        return str(self.myos_root) if self.myos_root else None

    def update_context(self, path: str, lens_desk: str = "", lens_desk_save: Optional[str] = None) -> None:
        """Be at path; with a lens on, its Desk (lens_desk) applies and changes of the
        desktop go to lens_desk_save (Designdocument Perspective Resolver MVP.md, A5)."""
        target = self._resolve_path(path)
        root = find_project_root(target)
        if root != self.project_root:
            self._set_project_root(root)
            self._configure_acl_from_env()
        self._refresh_desk_context(target, lens_desk or None, lens_desk_save)

    def _find_projects_root(self, target: Path) -> Optional[Path]:
        resolved_target = Path(target).expanduser().resolve()
        # Pick the nearest ancestor that provides a valid "Projekte" anchor
        # containing the target. This avoids CPD mixes in nested workspaces.
        for candidate in [resolved_target] + list(resolved_target.parents):
            marker = candidate / ".MyOS" / "Project.md"
            if not marker.exists():
                continue
            projects_dir = (candidate / "Projekte").resolve()
            if projects_dir.exists() and projects_dir.is_dir() and is_within(resolved_target, projects_dir):
                return projects_dir
            if candidate.name == "Projekte" and is_within(resolved_target, candidate):
                return candidate

        fallback = self.myos_root or find_top_project_root(resolved_target) or find_project_root(resolved_target)
        if fallback is None:
            return None
        root = Path(fallback).expanduser().resolve()
        if not is_within(resolved_target, root):
            return None
        projects_dir = (root / "Projekte").resolve()
        if projects_dir.exists() and projects_dir.is_dir() and is_within(resolved_target, projects_dir):
            return projects_dir
        if root.name == "Projekte":
            return root
        return root

    def _refresh_desk_context(self, target: Path, manual_desk: Optional[str] = None, desk_owner: Optional[str] = None) -> None:
        self._desk_service.refresh_context(target, manual_desk=manual_desk, desk_owner=desk_owner)

    def get_active_desk_profile(self) -> Dict[str, Optional[str]]:
        return self._desk_service.get_active_profile()

    def get_last_desk_result(self) -> Dict[str, Any]:
        return self._desk_service.get_last_result()

    def list_config_targets(self, path: str, config_name: str) -> List[Dict[str, str]]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._desk_service.is_safe_config_name(config_name):
            return [
                {
                    "id": "discard",
                    "label": "Nicht speichern",
                    "targetPath": "",
                    "configPath": "",
                    "exists": "0",
                }
            ]
        if not self._desk_service.supports_config(config_name):
            return [
                {
                    "id": "discard",
                    "label": "Nicht speichern",
                    "targetPath": "",
                    "configPath": "",
                    "exists": "0",
                }
            ]
        target = self._resolve_path(path)
        template_root: Optional[Path] = None
        root, blueprint = self._resolve_context_for_target(target)
        if root and blueprint is not None:
            templates_dir = getattr(blueprint, "templates_dir", None)
            if templates_dir:
                templates_base = Path(templates_dir).expanduser().resolve()
                for template_name in getattr(blueprint, "template_names", []):
                    candidate = (templates_base / str(template_name)).resolve()
                    if is_within(target, candidate):
                        template_root = candidate
                        break
        return self._desk_service.list_config_targets(
            target,
            config_name=config_name,
            global_root=self.myos_root,
            include_template_target=template_root is not None,
            template_root=template_root,
        )

    def ensure_project_config(self, path: str, config_name: str) -> Dict[str, Any]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._desk_service.is_safe_config_name(config_name):
            return {"ok": False, "reason": "invalid_config_name", "path": ""}
        target = self._resolve_path(path)
        root = find_project_root(target)
        if not root:
            return {"ok": False, "reason": "no_project_root", "path": ""}
        return self._desk_service.ensure_config_file(root, config_name=config_name)

    def capture_config_state(self, config_name: str) -> Dict[str, Any]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._desk_service.is_safe_config_name(config_name):
            return {"ok": False, "reason": "invalid_config_name", "path": ""}
        return self._desk_service.capture_config_state(config_name=config_name)

    def apply_config_state_to_target(self, path: str, config_name: str, target_id: str) -> Dict[str, Any]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._desk_service.is_safe_config_name(config_name):
            return {"ok": False, "reason": "invalid_config_name", "path": ""}
        target = self._resolve_path(path)
        options = self.list_config_targets(str(target), config_name)
        chosen = None
        for item in options:
            if str(item.get("id")) == str(target_id):
                chosen = item
                break
        if chosen is None:
            return {"ok": False, "reason": "target_not_found", "path": ""}
        if str(chosen.get("id")) == "discard":
            return {"ok": True, "reason": "discarded", "path": ""}
        target_path = str(chosen.get("targetPath") or "").strip()
        if not target_path:
            return {"ok": False, "reason": "missing_target_path", "path": ""}
        state_result = self._desk_service.capture_config_state(config_name=config_name)
        if not state_result.get("ok"):
            return {"ok": False, "reason": "capture_failed", "path": ""}
        return self._desk_service.write_config_from_state(
            Path(target_path),
            config_name=config_name,
            state=dict(state_result.get("state") or {}),
        )

    def has_local_config(self, path: str, config_name: str) -> bool:
        # Security: reject traversal/path-injection in config filenames.
        if not self._desk_service.is_safe_config_name(config_name):
            return False
        target = self._resolve_path(path)
        root = find_project_root(target)
        if not root:
            return False
        candidate = root / ".MyOS" / config_name
        return candidate.exists() and candidate.is_file()

    def find_config(self, path: str, config_name: str) -> Optional[str]:
        if not self._desk_service.is_safe_config_name(config_name):
            return None
        target = self._resolve_path(path)
        found = self._desk_service.find_config(target, config_name=config_name)
        return str(found) if found else None

    def list_filters(self, path: str) -> List[Dict[str, Any]]:
        target = self._resolve_path(path)
        roots = self._resolve_filter_roots_for_target(target)
        layers = find_filters_layers(
            target,
            template_root=roots.get("templateRoot"),
            project_root=roots.get("projectRoot"),
            global_root=roots.get("globalRoot"),
        )
        out: List[Dict[str, Any]] = []
        for layer in layers:
            out.append(
                {
                    "name": layer.config.name,
                    "path": str(layer.source_path),
                    "scopeDir": str(layer.scope_dir),
                    "originType": layer.origin_type,
                    "sourceKind": layer.source_kind,
                    "depth": int(layer.depth),
                    "inherit": layer.config.inherit,
                }
            )
        return out

    def resolve_active_filter(self, path: str) -> Dict[str, Any]:
        target = self._resolve_path(path)
        effective = self._resolve_effective_filter_for_target(target)
        if not effective:
            return {
                "active": False,
                "name": "",
                "mode": "auto",
                "path": "",
                "flatten": False,
                "groups": [],
                "chain": [],
                "lens": [],
            }
        first_path = effective.layers[0].source_path if effective.layers else None
        return {
            "active": True,
            "name": effective.config.name,
            "mode": effective.mode,
            "path": str(first_path) if first_path else "",
            "flatten": bool(effective.config.flatten),
            "groups": list(effective.config.groups or []),
            "chain": effective.explain_chain(),
            "lens": list(effective.config.lens),
        }

    def preview_sort_target_for_move(self, source_path: str, target_dir: str) -> Dict[str, Any]:
        """Where a file moved into target_dir would be filed (core.filing); ok only when it
        does not stay in target_dir."""
        try:
            source = self._resolve_path(source_path)
            target = self._resolve_path(target_dir)
        except Exception:
            return {"ok": False, "reason": "invalid_path", "target": ""}
        if not source.is_file():
            return {"ok": False, "reason": "missing_file", "target": ""}
        destination = destination_for(source, target)
        if destination == target.resolve():
            return {"ok": False, "reason": "stays", "target": ""}
        return {"ok": True, "reason": "filed", "target": str(destination)}

    def catch_up_filing(self, path: str) -> Dict[str, Any]:
        """File what is due in the sorted folder path belongs to (core.filing): whenever a
        folder is looked at. {ok, moved: [{source, destination}], skipped}."""
        try:
            folder = sorted_folder_for(self._resolve_path(path))
        except Exception:
            folder = None
        return self._file_due([folder] if folder is not None else [])

    def catch_up_filing_all(self, path: str) -> Dict[str, Any]:
        """File what is due in every sorted folder of the project tree path lies in (at
        Scope's start and once a day)."""
        try:
            root = find_top_project_root(self._resolve_path(path))
        except Exception:
            root = None
        return self._file_due(sorted_folders(root) if root is not None else [])

    def enable_sorting(self, path: str) -> Dict[str, Any]:
        """Give the folder path a sort rule (.MyOS/Sort.md, years and months by date);
        {ok, reason, path}: "exists", "no_project" (rules only inside projects)."""
        try:
            folder = self._resolve_path(path)
        except Exception:
            return {"ok": False, "reason": "invalid_path", "path": ""}
        rule_file = folder / ".MyOS" / "Sort.md"
        if not folder.is_dir() or find_project_root(folder) is None:
            return {"ok": False, "reason": "no_project", "path": ""}
        if rule_file.exists() or rule_file.is_symlink():
            return {"ok": False, "reason": "exists", "path": str(rule_file)}
        probe = self._acl_probe("write_dir", folder)
        if probe and probe.enforced and not probe.allowed:
            return {"ok": False, "reason": "permission", "path": ""}
        rule_file.parent.mkdir(exist_ok=True)
        rule_file.write_text(SORT_RULE_SEED, encoding="utf-8")
        return {"ok": True, "reason": "created", "path": str(rule_file)}

    def _file_due(self, folders: List[Path]) -> Dict[str, Any]:
        def may_write(path: Path) -> bool:
            # Security: filing moves files; only where the user may write.
            probe = self._acl_probe("write", path)
            return not (probe and probe.enforced and not probe.allowed)

        moved, skipped = [], []
        for folder in folders:
            report = file_due(folder, may_write=may_write)
            for source, destination in report.moved:
                self._acl_rules_follow(source, destination)
                moved.append({"source": str(source), "destination": str(destination)})
            skipped.extend({"source": str(source), "reason": reason} for source, reason in report.skipped)
        return {"ok": not skipped, "moved": moved, "skipped": skipped}

    def _resolve_filter_roots_for_target(self, target: Path) -> Dict[str, Optional[Path]]:
        template_root = self._resolve_template_root_for_target(target)
        project_root = find_project_root(target)
        return {
            "templateRoot": template_root,
            "projectRoot": project_root,
            "globalRoot": self.myos_root,
        }

    def _resolve_effective_filter_for_target(self, target: Path) -> Optional[EffectiveFilter]:
        roots = self._resolve_filter_roots_for_target(target)
        result = resolve_effective_filter(
            target,
            template_root=roots.get("templateRoot"),
            project_root=roots.get("projectRoot"),
            global_root=roots.get("globalRoot"),
        )
        return result

    def _list_entries_flattened(self, root_path: Path) -> List[FileEntryWithOptionalEmbryo]:
        entries: List[FileEntryWithOptionalEmbryo] = []
        stack: List[Path] = [root_path]
        while stack:
            current = stack.pop()
            try:
                children = sorted(current.iterdir(), key=lambda item: item.name.lower())
            except Exception:
                continue
            for child in reversed(children):
                if child.name.startswith("."):
                    continue
                acl_child = self._acl_probe("read_dir", child)
                if acl_child and acl_child.enforced and not acl_child.allowed:
                    continue
                if child.is_dir():
                    stack.append(child)
                    sidecar = self._read_folder_sidecar(child)
                    entry = self._build_file_entry(
                        name=child.name,
                        is_dir=True,
                        path=str(child),
                        tags=sidecar["tags"],
                    )
                    batch_info = self._get_folder_batch(child)
                    if batch_info["batch"]:
                        entry["batch"] = batch_info["batch"]
                    if batch_info["batchText"]:
                        entry["batchText"] = batch_info["batchText"]
                    entries.append(entry)
                else:
                    entries.append(
                        self._build_file_entry(
                            name=child.name,
                            is_dir=False,
                            path=str(child),
                            tags=self._read_entry_tags(child, None),
                        )
                    )
        entries.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))
        return entries

    def _resolve_path(self, path: str) -> Path:
        return Path(path).expanduser().resolve()

    def _resolve_context_for_target(self, target: Path) -> tuple[Optional[Path], Optional[Any]]:
        root = find_project_root(target)
        if not root:
            return None, None
        if self.project_root and root == self.project_root:
            return self.project_root, self.blueprint
        if Blueprint is None:
            return root, None
        key = str(root)
        if key in self._blueprint_cache:
            return root, self._blueprint_cache[key]
        try:
            bp = Blueprint(root)
        except Exception:
            bp = None
        self._blueprint_cache[key] = bp
        return root, bp

    def _resolve_template_root_for_target(self, target: Path) -> Optional[Path]:
        root, blueprint = self._resolve_context_for_target(target)
        if not root or blueprint is None:
            return None
        templates_dir = getattr(blueprint, "templates_dir", None)
        if not templates_dir:
            return None
        templates_base = Path(templates_dir).expanduser().resolve()
        for template_name in getattr(blueprint, "template_names", []):
            candidate = (templates_base / str(template_name)).resolve()
            if is_within(target, candidate):
                return candidate
        return None

    def _resolve_template_color_for_context(self, blueprint: Any, rel_path: str, name: str) -> Optional[str]:
        if not blueprint:
            return None
        parts = [p for p in rel_path.split("/") if p]
        parts.append(name)
        for template_name in blueprint.template_names:
            base = blueprint.templates_dir / template_name
            candidate = base.joinpath(*parts)
            if not candidate.exists():
                continue
            color = self._find_color_upwards(candidate, base)
            if color:
                return color
        return None

    def _resolve_project_color_with_root(self, path: Path, root: Optional[Path]) -> Optional[str]:
        if not path or not path.is_dir():
            return None
        if not root or not is_within(path, root):
            return self._resolve_project_color(path)
        current = path
        while True:
            color = self._resolve_direct_project_color(current)
            if color:
                return color
            if current == root or current == current.parent:
                break
            current = current.parent
        return None

    def _resolve_dir(self, path: str) -> Optional[Path]:
        try:
            target = self._resolve_path(path)
        except Exception:
            return None
        return target if target.is_dir() else None

    def _resolve_or_materialize_target_dir(self, target_dir: str) -> tuple[Optional[Path], str]:
        _dbg = os.environ.get("MYOS_DEBUG_BIRTH")
        if _dbg:
            print(f"[birth] _resolve_or_materialize_target_dir target_dir={target_dir!r}")
        try:
            target = self._resolve_path(target_dir)
        except Exception as e:
            if _dbg:
                print(f"[birth] _resolve_path failed: {e}")
            return None, "invalid_path"

        if target.is_dir():
            if _dbg:
                print(f"[birth] target already dir -> {target}")
            return target, ""

        acl_target = self._acl_probe("write_dir", target)
        if acl_target and acl_target.enforced and not acl_target.allowed:
            if _dbg:
                print("[birth] acl_denied_target")
            return None, "acl_denied_target"

        context_root, context_blueprint = self._resolve_context_for_target(target)
        if not context_root or context_blueprint is None:
            if _dbg:
                print(f"[birth] no context root/blueprint -> target_not_directory (root={context_root!r})")
            return None, "target_not_directory"
        if not is_within(target, context_root):
            if _dbg:
                print("[birth] target not within context_root -> target_not_directory")
            return None, "target_not_directory"

        rel_target = "" if target == context_root else str(target.relative_to(context_root))
        if not rel_target:
            if _dbg:
                print("[birth] rel_target empty -> target_not_directory")
            return None, "target_not_directory"

        is_embryo_target = bool(context_blueprint.is_embryo(rel_target))
        contains_embryos = bool(context_blueprint.contains_embryos(f"/{rel_target}"))
        if _dbg:
            print(f"[birth] rel_target={rel_target!r} is_embryo={is_embryo_target} contains_embryos={contains_embryos}")
        if not is_embryo_target and not contains_embryos:
            if _dbg:
                print("[birth] not embryo and not contains_embryos -> target_not_directory")
            return None, "target_not_directory"

        try:
            if _dbg:
                print(f"[birth] calling context_blueprint.mkdir(/{rel_target!r})")
            context_blueprint.mkdir(f"/{rel_target}", 0o755)
        except Exception as e:
            if _dbg:
                print(f"[birth] mkdir failed: {e}")
            return None, "target_not_directory"

        resolved = self._resolve_dir(str(target))
        if resolved is None:
            if _dbg:
                print("[birth] _resolve_dir after mkdir -> None")
            return None, "target_not_directory"
        if _dbg:
            print(f"[birth] resolved -> {resolved}")
        return resolved, ""

    def set_acl_enforcement(
        self,
        service: Optional[ACLEnforcementService],
        user: Optional[str] = None,
        root: Optional[str] = None,
    ) -> None:
        """Use service for ACL checks; its rule paths are relative to root (default: project)."""
        self._acl_enforcement = service
        self._acl_root = Path(root).expanduser().resolve() if root else (self.project_root or self.start_path)
        if user is not None and str(user).strip():
            self._acl_user_override = str(user).strip().lower()

    def acl_allows(self, action: str, path: Path) -> bool:
        """Whether the ACL checks allow action ("read", "write", "delete", ...) on path."""
        probe = self._acl_probe(action, Path(path))
        return not (probe and probe.enforced and not probe.allowed)

    def projects_root(self) -> Optional[Path]:
        """The projects root ("Projekte") of the start path, for the perspective daemon."""
        return self._find_projects_root(Path(self.get_start_path()).expanduser().resolve())

    def _acl_user_at(self, path) -> str:
        """The user ACLs are checked for at path (see core.identity)."""
        return self._acl_user_override or acl_user_for(path)

    def _acl_resource_path(self, resource: Path) -> str:
        """
        Path as written in ACLs.md: relative to the ACL project ("/" for its root).
        Paths outside that project stay absolute, so only global rules like "/*" match them.
        """
        try:
            absolute = Path(resource).expanduser().resolve()
        except OSError:
            return str(resource)
        if self._acl_root is None:
            return str(absolute)
        try:
            rel = absolute.relative_to(self._acl_root)
        except ValueError:
            return str(absolute)
        text = str(rel).replace("\\", "/")
        return "/" if text in ("", ".") else "/" + text

    def get_acl_audit_events(self) -> List[Dict[str, Any]]:
        return list(self._acl_audit_events)

    def clear_acl_audit_events(self) -> None:
        self._acl_audit_events.clear()

    def set_acl_audit_file(self, path: Optional[str] = None, max_bytes: int = 262_144) -> None:
        self._acl_audit_max_bytes = max(4_096, int(max_bytes or 262_144))
        if path and str(path).strip():
            self._acl_audit_file = Path(str(path)).expanduser().resolve()
            return
        if self.project_root:
            self._acl_audit_file = (self.project_root / ".MyOS" / "audit.log").resolve()
        else:
            self._acl_audit_file = None

    def _write_acl_audit_event(self, event: Dict[str, Any]) -> None:
        if self._acl_audit_file is None:
            return
        try:
            self._acl_audit_file.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(event, ensure_ascii=True, sort_keys=True) + "\n"
            encoded = line.encode("utf-8")
            if self._acl_audit_file.exists():
                current_size = self._acl_audit_file.stat().st_size
                if current_size + len(encoded) > self._acl_audit_max_bytes:
                    rotated = self._acl_audit_file.with_name(f"{self._acl_audit_file.name}.1")
                    # // Security: keep bounded on-disk logs to avoid storage exhaustion.
                    if rotated.exists():
                        rotated.unlink(missing_ok=True)
                    self._acl_audit_file.replace(rotated)
            with self._acl_audit_file.open("ab") as handle:
                handle.write(encoded)
        except Exception:
            return

    def _configure_acl_from_env(self) -> None:
        mode = str(os.environ.get("MYOS_ACL_MODE") or "off").strip().lower()
        if mode not in {"off", "monitor", "enforce"}:
            mode = "off"

        if mode == "off":
            self._acl_enforcement = None
            self._acl_audit_file = None
            return

        backend = str(os.environ.get("MYOS_ACL_BACKEND") or "auto").strip().lower() or "auto"
        if backend not in {"auto", "legacy", "casbin"}:
            backend = "auto"

        # Security: a subproject without its own ACLs.md is governed by its parent's
        # (rules inherit directly); checking it against no rules would hide everything.
        root = find_acl_project_root(self.project_root or self.start_path) or self.project_root or self.start_path
        try:
            # The folder rules apply again to the template folders of the current
            # subproject (ACLPolicy.for_context); update_context reconfigures this.
            authorizer = ACLAuthorizer.from_project(root, backend=backend, context=self.project_root)
        except Exception:
            self._acl_enforcement = None
            self._acl_audit_file = None
            return

        self._acl_enforcement = ACLEnforcementService(authorizer, mode=mode)
        self._acl_root = Path(root).resolve()

        audit_path = str(os.environ.get("MYOS_ACL_AUDIT_FILE") or "").strip()
        audit_enabled = str(os.environ.get("MYOS_ACL_AUDIT") or "").strip().lower() in {"1", "true", "yes", "on"}
        try:
            max_bytes = int(str(os.environ.get("MYOS_ACL_AUDIT_MAX_BYTES") or "262144").strip())
        except Exception:
            max_bytes = 262_144

        if audit_path:
            self.set_acl_audit_file(audit_path, max_bytes=max_bytes)
        elif audit_enabled:
            self.set_acl_audit_file(None, max_bytes=max_bytes)
        else:
            self._acl_audit_file = None

    def _on_acl_audit_event(self, event: Dict[str, Any]) -> None:
        # // Security: bound in-memory audit buffer to avoid unbounded growth.
        self._acl_audit_events.append(dict(event or {}))
        if len(self._acl_audit_events) > 1000:
            self._acl_audit_events = self._acl_audit_events[-1000:]
        self._write_acl_audit_event(dict(event or {}))

    def _acl_probe(self, action: str, resource: Path) -> Optional[ACLCheckResult]:
        if self._acl_enforcement is None:
            return None
        acl_action = {
            "read_dir": "read",
            "read_templates": "read",
            "open_markdown": "read",
            "create_folder": "write",
            "create_note": "write",
            "rename": "write",
            "write_dir": "write",
            "move": "write",
            "delete": "delete",
        }.get(str(action or "").strip().lower(), str(action or "read").strip().lower() or "read")
        user = self._acl_user_at(self._acl_root or resource)
        try:
            result = self._acl_enforcement.check(
                ACLCheckRequest(
                    user=user,
                    action=acl_action,
                    resource=self._acl_resource_path(resource),
                )
            )
            self._on_acl_audit_event(
                {
                    "user": user,
                    "action": str(action or "read"),
                    "resource": str(resource),
                    "mode": result.mode,
                    "policy_allowed": result.allowed if result.enforced else (result.reason != "monitor_override"),
                    "allowed": result.allowed,
                    "enforced": result.enforced,
                    "reason": result.reason,
                    "backend": self._acl_enforcement.authorizer.backend,
                }
            )
            return result
        except Exception:
            return None

    def list_children(
        self, path: str, include_embryos: bool = True, show_hidden: bool = False
    ) -> List[FolderEntry]:
        try:
            target = self._resolve_path(path)
        except Exception:
            return []
        context_root, context_blueprint = self._resolve_context_for_target(target)
        can_list_dirs = target.is_dir()
        can_list_virtual_embryos = bool(
            include_embryos
            and context_blueprint
            and context_root
            and is_within(target, context_root)
        )
        if not can_list_dirs and not can_list_virtual_embryos:
            return []
        if can_list_dirs:
            self._acl_probe("read_dir", target)
        entries: List[FolderEntry] = []
        parent_for_color = target if can_list_dirs else target.parent
        parent_color = self._resolve_project_color_with_root(parent_for_color, context_root)
        rel = ""
        if context_root and is_within(target, context_root):
            rel = "" if target == context_root else str(target.relative_to(context_root))
        if can_list_dirs:
            try:
                for child in sorted(target.iterdir()):
                    if not show_hidden and child.name.startswith("."):
                        continue
                    if child.is_dir():
                        acl_child = self._acl_probe("read_dir", child)
                        if acl_child and acl_child.enforced and not acl_child.allowed:
                            continue
                        rel_child = child.name if rel == "" else f"{rel}/{child.name}"
                        # Include born folders (physical dirs that were embryos): do not skip by template path.
                        # They are marked via folder_type=FOLDER_TYPE_BORN from _classify_folder_type.
                        is_project = self.is_project(str(child))
                        project_color = self._resolve_effective_project_color(child) if is_project else None
                        folder_type = self._classify_folder_type(
                            context_blueprint=context_blueprint,
                            rel_path=rel_child,
                            is_embryo=False,
                        )
                        entries.append(
                            self._build_folder_entry(
                                name=child.name,
                                is_project=is_project,
                                is_embryo=False,
                                folder_type=folder_type,
                                color=project_color,
                                folder_path=child,
                            )
                        )
            except Exception:
                return []

        if can_list_virtual_embryos:
            embryos = context_blueprint.get_embryos_at(rel)
            for name in embryos:
                if not show_hidden and name.startswith("."):
                    continue
                if not any(item["name"] == name for item in entries):
                    embryo_path = target / name
                    acl_embryo = self._acl_probe("read_dir", embryo_path)
                    if acl_embryo and acl_embryo.enforced and not acl_embryo.allowed:
                        continue
                    embryo_color = self._resolve_template_color_for_context(context_blueprint, rel, name)
                    embryo_rel = f"{rel}/{name}" if rel else name
                    entries.append(
                        self._build_folder_entry(
                            name=name,
                            is_project=False,
                            is_embryo=True,
                            folder_type=self.FOLDER_TYPE_EMBRYO,
                            color=(embryo_color or parent_color),
                            folder_path=embryo_path,
                            context_blueprint=context_blueprint,
                            embryo_rel_path=embryo_rel,
                        )
                    )
            entries.sort(key=lambda item: item["name"])

        return entries

    def list_templates(
        self, path: str, include_embryos: bool = True, show_hidden: bool = False
    ) -> List[FolderEntry]:
        try:
            target = self._resolve_path(path)
        except Exception:
            return []
        context_root, context_blueprint = self._resolve_context_for_target(target)
        can_list_virtual_embryos = bool(
            include_embryos
            and context_blueprint
            and context_root
            and is_within(target, context_root)
        )
        if not can_list_virtual_embryos:
            return []
        if target.is_dir():
            self._acl_probe("read_templates", target)
        if not include_embryos:
            return []
        if not context_blueprint or not context_root or not is_within(target, context_root):
            return []
        rel = "" if target == context_root else str(target.relative_to(context_root))
        try:
            parent_color = self._resolve_project_color_with_root(target, context_root)
            get_template_folders = getattr(
                context_blueprint, "get_template_folders_at", None
            )
            if callable(get_template_folders):
                template_folders = sorted(
                    get_template_folders(rel), key=lambda x: x[0]
                )
            else:
                embryos = sorted(context_blueprint.get_embryos_at(rel))
                template_folders = [(name, True) for name in embryos]
            result = []
            for name, is_embryo in template_folders:
                if not show_hidden and name.startswith("."):
                    continue
                embryo_color = self._resolve_template_color_for_context(
                    context_blueprint, rel, name
                )
                folder_path = target / name
                template_rel = f"{rel}/{name}" if rel else name
                result.append(
                    self._build_folder_entry(
                        name=name,
                        is_project=False,
                        is_embryo=is_embryo,
                        folder_type=(
                            self.FOLDER_TYPE_EMBRYO
                            if is_embryo
                            else self.FOLDER_TYPE_BORN
                        ),
                        color=(embryo_color or parent_color),
                        folder_path=folder_path,
                        context_blueprint=context_blueprint,
                        embryo_rel_path=template_rel if is_embryo else None,
                    )
                )
            return result
        except Exception:
            return []

    def list_entries_quick(
        self, path: str, show_hidden: bool = False
    ) -> List[FileEntryWithOptionalEmbryo]:
        """Minimal list for immediate display. No tags, no ACL, no embryos."""
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return []
        if not target.exists():
            return self._list_virtual(path)  # inside a virtual folder (core.filing)
        if not target.is_dir():
            return []
        entries: List[FileEntryWithOptionalEmbryo] = []
        try:
            for child in sorted(target.iterdir()):
                if not show_hidden and child.name.startswith("."):
                    continue
                is_dir = child.is_dir()
                entry = self._build_file_entry(
                    name=child.name,
                    is_dir=is_dir,
                    path=str(child),
                    tags=[],
                )
                if is_dir:
                    batch_info = self._get_folder_batch(child)
                    if batch_info["batch"]:
                        entry["batch"] = batch_info["batch"]
                    if batch_info["batchText"]:
                        entry["batchText"] = batch_info["batchText"]
                entries.append(entry)
        except Exception:
            return []
        entries.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))
        groups = virtual_groups(target)  # as the full listing shows them, without a flicker
        return self._with_virtual_folders(target, entries, groups) if groups else entries

    def list_entries(self, path: str) -> List[FileEntryWithOptionalEmbryo]:
        target = self._resolve_dir(path)
        if target is None:
            return self._list_virtual(path)  # inside a virtual folder of a sorted folder
        self._acl_probe("read_dir", target)
        self.catch_up_filing(str(target))  # a sorted folder is filed when it is looked at
        effective_filter = self._resolve_effective_filter_for_target(target)
        project_root = find_project_root(target)
        entries: List[FileEntryWithOptionalEmbryo] = []
        md_tag_cache = self._load_markdown_tag_cache(target)
        seen_md_files: set[str] = set()
        try:
            for child in sorted(target.iterdir()):
                acl_child = self._acl_probe("read_dir", child)
                if acl_child and acl_child.enforced and not acl_child.allowed:
                    continue
                is_dir = child.is_dir()
                if not is_dir and child.suffix.lower() in {".md", ".markdown"}:
                    seen_md_files.add(child.name)
                # An unreadable child (e.g. /root, /lost+found) is listed without
                # tags or batch instead of emptying the whole listing.
                try:
                    if is_dir:
                        entry_tags = self._read_folder_sidecar(child)["tags"]
                    else:
                        entry_tags = self._read_entry_tags(child, md_tag_cache)
                except OSError:
                    entry_tags = []
                entry = self._build_file_entry(
                    name=child.name,
                    is_dir=is_dir,
                    path=str(child),
                    tags=entry_tags,
                )
                if is_dir:
                    try:
                        batch_info = self._get_folder_batch(child)
                    except OSError:
                        batch_info = {"batch": None, "batchText": None}
                    if batch_info["batch"]:
                        entry["batch"] = batch_info["batch"]
                    if batch_info["batchText"]:
                        entry["batchText"] = batch_info["batchText"]
                entries.append(entry)
        except Exception:
            return []

        if self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if not any(item["name"] == name for item in entries):
                    embryo_path = target / name
                    acl_embryo = self._acl_probe("read_dir", embryo_path)
                    if acl_embryo and acl_embryo.enforced and not acl_embryo.allowed:
                        continue
                    embryo_path = target / name
                    entry = self._build_file_entry(
                        name=name,
                        is_dir=True,
                        path=str(embryo_path),
                        tags=[],
                        is_embryo=True,
                    )
                    batch_info = self._get_folder_batch(embryo_path)
                    if (not batch_info["batch"] and not batch_info["batchText"]) and self.blueprint:
                        embryo_rel = f"{rel}/{name}" if rel else name
                        batch_info = self._get_folder_batch_for_embryo(self.blueprint, embryo_rel)
                    if batch_info["batch"]:
                        entry["batch"] = batch_info["batch"]
                    if batch_info["batchText"]:
                        entry["batchText"] = batch_info["batchText"]
                    entries.append(entry)
        # File-browser style order: folders first, then files, both alphabetic.
        entries.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))
        groups = virtual_groups(target)
        if groups:
            entries = self._with_virtual_folders(target, entries, groups)
        self._prune_markdown_tag_cache(md_tag_cache, seen_md_files)
        self._save_markdown_tag_cache(target, md_tag_cache)
        if effective_filter and effective_filter.config.flatten:
            entries = self._list_entries_flattened(target)
        entries = apply_filter_projection(
            entries,
            cwd=target,
            filter_state=effective_filter,
            project_root=project_root,
        )
        return entries

    def _with_virtual_folders(self, target: Path, entries: List[FileEntryWithOptionalEmbryo],
                              groups: Dict[str, List[Path]]) -> List[FileEntryWithOptionalEmbryo]:
        """entries with the loose files of a sorted folder grouped into virtual folders
        (core.filing: too few files for real ones yet; nothing moves)."""
        grouped = {str(f) for files in groups.values() for f in files}
        result = [e for e in entries if e.get("path") not in grouped]
        for name in groups:
            result.append({"name": name, "isDir": True, "path": str(target / name), "tags": [], "isVirtual": True})
        result.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))
        return result

    def _list_virtual(self, path: str) -> List[FileEntryWithOptionalEmbryo]:
        """The content of a virtual folder: its virtual subfolders, or at the last level the
        files that would lie there (they really lie loose in the sorted folder)."""
        try:
            view = virtual_listing(self._resolve_path(path))
        except Exception:
            view = None
        if view is None:
            return []
        base = self._resolve_path(path)
        entries: List[FileEntryWithOptionalEmbryo] = [
            {"name": name, "isDir": True, "path": str(base / name), "tags": [], "isVirtual": True}
            for name in sorted(view.groups)
        ]
        for file in view.files:
            probe = self._acl_probe("read_dir", file)
            if probe and probe.enforced and not probe.allowed:
                continue
            entries.append(self._build_file_entry(name=file.name, is_dir=False, path=str(file),
                                                  tags=self._read_entry_tags(file, None)))
        return entries

    def list_entries_xray(self, path: str, budget: int, folders_shown: bool) -> List[FileEntryWithOptionalEmbryo]:
        """
        list_entries with small folders seen through (core.xray) while the listing fits
        budget entries (what the FilesPanel shows without scrolling). Their files take the
        folder's place and carry xrayVia, the folder they lie in ("Rechnungen/2024").
        folders_shown: whether the panel shows folders (else only files take room).
        """
        entries = self.list_entries(path)
        target = self._resolve_dir(path)
        if target is None or int(budget) <= 0:
            return entries
        embryos = sum(1 for e in entries if e.get("isEmbryo")) if folders_shown else 0

        def may_read(folder: Path) -> bool:
            # Security: x-ray never shows what the user may not read.
            probe = self._acl_probe("read_dir", folder)
            return not (probe and probe.enforced and not probe.allowed)

        virtual = virtual_groups(target)
        try:
            plan = xray_listing(target, int(budget), extra=embryos, may_read=may_read,
                                folders_shown=bool(folders_shown), virtual=virtual)
        except OSError:
            return entries
        seen_through = [e for e in plan if e.via]
        opened = {e.via.split("/")[0] for e in seen_through}
        # Virtual folders seen through: their files simply show where they lie (loose here).
        opened_virtual = set(virtual) - {e.path.name for e in plan if e.virtual}
        if not opened and not opened_virtual:
            return entries
        result = [e for e in entries if not (e.get("isDir") and not e.get("isEmbryo") and e.get("name") in opened)
                  and not (e.get("isVirtual") and e.get("name") in opened_virtual)]
        for name in opened_virtual:
            for file in virtual[name]:
                result.append(self._build_file_entry(name=file.name, is_dir=False, path=str(file),
                                                     tags=self._read_entry_tags(file, None)))
        for item in seen_through:
            entry = self._build_file_entry(
                name=item.path.name,
                is_dir=False,
                path=str(item.path),
                tags=self._read_entry_tags(item.path, None),
            )
            entry["xrayVia"] = item.via
            result.append(entry)
        result.sort(key=lambda e: (not bool(e.get("isDir")), str(e.get("name", "")).lower()))
        return result

    def list_entries_filtered(
        self, path: str, tags: List[str], match_all: bool = False
    ) -> List[FileEntryWithOptionalEmbryo]:
        selected = [str(tag or "").strip() for tag in (tags or [])]
        selected = [tag for tag in selected if tag]
        if not selected:
            return self.list_entries(path)

        selected_set = set(selected)
        filtered: List[FileEntryWithOptionalEmbryo] = []
        for entry in self.list_entries(path):
            entry_tags = set(entry.get("tags") or [])
            if not entry_tags:
                continue
            if match_all:
                if selected_set.issubset(entry_tags):
                    filtered.append(entry)
            else:
                if entry_tags.intersection(selected_set):
                    filtered.append(entry)
        return filtered

    def list_project_tags(self, path: str) -> List[str]:
        # Like other configs, Tags.md inherits upwards: a subproject without one of its
        # own suggests the tags of the nearest parent project that has one.
        target = self._resolve_path(path)
        tags_file = find_config_in_parents(target, "Tags.md", honor_inherit_not=False)
        if tags_file is None:
            return []
        return _read_markdown_tag_list(tags_file)

    def list_folder_tags(self, path: str) -> List[str]:
        target = self._resolve_path(path)
        if not target.exists() or not target.is_dir():
            return []
        return self._read_folder_sidecar(target)["tags"]

    def set_folder_tags(self, path: str, tags: List[str]) -> bool:
        target = self._resolve_path(path)
        if not target.exists() or not target.is_dir():
            return False
        cleaned = sorted(
            set(_normalize_tag_value(tag) for tag in (tags or []) if _normalize_tag_value(tag)),
            key=str.lower,
        )
        self._write_folder_sidecar(target, cleaned)
        self._remove_legacy_folder_tag_colors_file(target)
        return True

    def list_tag_buckets(self, path: str) -> Dict[str, Any]:
        """
        Tags of the tag bar for a listed folder: of the folder itself, of its subfolders
        and of its files. Tags of the folder itself are not repeated in the other two;
        subfolders and files may share a tag (Scope can hide the subfolders).
        """
        target = self._resolve_dir(path)
        if target is None:
            return {
                "folderTags": [],
                "subfolderTags": [],
                "fileTags": [],
                "folderTagColors": {},
                "subfolderTagColors": {},
                "fileTagColors": {},
            }
        sidecar = self._read_folder_sidecar(target)
        folder_tags = sidecar["tags"]
        all_tag_colors = self._read_folder_tag_colors(target)
        subfolder_bag: Dict[str, bool] = {}
        file_bag: Dict[str, bool] = {}
        for entry in self.list_entries(str(target)):
            bag = subfolder_bag if entry.get("isDir") else file_bag
            for raw in entry.get("tags") or []:
                tag = str(raw or "").strip()
                if tag:
                    bag[tag] = True
        own = set(folder_tags)
        subfolder_tags = sorted([tag for tag in subfolder_bag if tag not in own], key=str.lower)
        file_tags = sorted([tag for tag in file_bag if tag not in own], key=str.lower)

        def colors(tags: List[str]) -> Dict[str, str]:
            return {tag: all_tag_colors[tag] for tag in tags if tag in all_tag_colors}

        return {
            "folderTags": folder_tags,
            "subfolderTags": subfolder_tags,
            "fileTags": file_tags,
            "folderTagColors": colors(folder_tags),
            "subfolderTagColors": colors(subfolder_tags),
            "fileTagColors": colors(file_tags),
        }

    def set_folder_tag_color(self, path: str, tag: str, color: str) -> bool:
        target = self._resolve_path(path)
        if not target.exists() or not target.is_dir():
            return False
        normalized_tag = _normalize_tag_value(tag)
        if not normalized_tag:
            return False
        normalized_color = _normalize_hex_color(color)
        if not normalized_color:
            return False
        folder_tags = self._read_folder_sidecar(target)["tags"]
        if normalized_tag not in folder_tags:
            return False
        colors = self._read_folder_tag_colors(target)
        colors[normalized_tag] = normalized_color
        self._write_folder_tag_colors(target, colors)
        self._remove_legacy_folder_tag_colors_file(target)
        return True

    def _read_entry_tags(self, entry_path: Path, md_tag_cache: Optional[Dict[str, Any]] = None) -> List[str]:
        tags: List[str] = []
        if entry_path.is_dir():
            # Directory tags live in a sidecar and do NOT imply "project".
            tags.extend(self._read_folder_sidecar(entry_path)["tags"])
        else:
            if entry_path.suffix.lower() in {".md", ".markdown"}:
                tags.extend(self._read_markdown_tags_with_cache(entry_path, md_tag_cache))
            try:
                tags_map = read_tags(entry_path)
            except Exception:
                tags_map = {}
            tags.extend(str(tag).strip() for tag in tags_map.keys())
        tags = [tag for tag in tags if tag]
        return sorted(set(tags), key=str.lower)

    def _markdown_tag_cache_path(self, directory: Path) -> Path:
        return directory / _MD_TAG_CACHE_FILE

    def _load_markdown_tag_cache(self, directory: Path) -> Dict[str, Any]:
        state: Dict[str, Any] = {"entries": {}, "dirty": False}
        cache_path = self._markdown_tag_cache_path(directory)
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return state
        if not isinstance(raw, dict):
            return state
        if int(raw.get("version", 0)) != _MD_TAG_CACHE_VERSION:
            return state
        entries = raw.get("entries", {})
        if isinstance(entries, dict):
            state["entries"] = entries
        return state

    def _prune_markdown_tag_cache(self, cache_state: Dict[str, Any], keep_names: set[str]) -> None:
        entries = cache_state.get("entries")
        if not isinstance(entries, dict):
            cache_state["entries"] = {}
            cache_state["dirty"] = True
            return
        for key in list(entries.keys()):
            if key not in keep_names:
                entries.pop(key, None)
                cache_state["dirty"] = True

    def _save_markdown_tag_cache(self, directory: Path, cache_state: Dict[str, Any]) -> None:
        if not cache_state.get("dirty"):
            return
        entries = cache_state.get("entries", {})
        if not isinstance(entries, dict):
            return
        payload = {"version": _MD_TAG_CACHE_VERSION, "entries": entries}
        cache_path = self._markdown_tag_cache_path(directory)
        try:
            cache_path.write_text(json.dumps(payload, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
            cache_state["dirty"] = False
        except Exception:
            # Cache write failures must not break directory listing.
            return

    def _read_markdown_tags_with_cache(self, entry_path: Path, cache_state: Optional[Dict[str, Any]]) -> List[str]:
        if not cache_state or not isinstance(cache_state.get("entries"), dict):
            return _read_markdown_content_tags(entry_path)

        try:
            stat = entry_path.stat()
        except OSError:
            return _read_markdown_content_tags(entry_path)

        entry_name = entry_path.name
        entries = cache_state["entries"]
        cached = entries.get(entry_name)
        mtime_ns = int(stat.st_mtime_ns)
        size = int(stat.st_size)

        if isinstance(cached, dict):
            try:
                cached_mtime = int(cached.get("mtime_ns", -1))
                cached_size = int(cached.get("size", -1))
            except (TypeError, ValueError):
                cached_mtime = -1
                cached_size = -1
            cached_tags = cached.get("tags", [])
            if cached_mtime == mtime_ns and cached_size == size and isinstance(cached_tags, list):
                return sorted(set(str(tag).strip() for tag in cached_tags if str(tag).strip()), key=str.lower)

        tags = _read_markdown_content_tags(entry_path)
        entries[entry_name] = {
            "mtime_ns": mtime_ns,
            "size": size,
            "tags": tags,
        }
        cache_state["dirty"] = True
        return tags

    def _read_folder_sidecar(self, folder_path: Path) -> Dict[str, Any]:
        result: Dict[str, Any] = {"tags": []}
        sidecar = folder_path / ".MyOS" / "myTags.md"
        if not sidecar.exists():
            return result
        try:
            text = sidecar.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return result
        frontmatter, body = _split_frontmatter(text)
        tags = _extract_hash_line_tags_from_text(body if frontmatter else text)
        result["tags"] = tags
        return result

    def _write_folder_sidecar(self, folder_path: Path, tags: List[str]) -> None:
        myos_dir = folder_path / ".MyOS"
        sidecar = myos_dir / "myTags.md"
        cleaned = sorted(
            set(_normalize_tag_value(tag) for tag in (tags or []) if _normalize_tag_value(tag)),
            key=str.lower,
        )

        if not cleaned:
            try:
                if sidecar.exists():
                    sidecar.unlink()
            except Exception:
                return
            self._cleanup_empty_folder_myos_dir(folder_path)
            return

        lines = [f"#{tag}" for tag in cleaned]
        content = "\n".join(lines).rstrip() + "\n"

        try:
            myos_dir.mkdir(parents=True, exist_ok=True)
            old_content = sidecar.read_text(encoding="utf-8", errors="replace") if sidecar.exists() else None
            if old_content == content:
                return
            sidecar.write_text(content, encoding="utf-8")
        except Exception:
            return

    def _cleanup_empty_folder_myos_dir(self, folder_path: Path) -> None:
        myos_dir = folder_path / ".MyOS"
        if not myos_dir.exists() or not myos_dir.is_dir():
            return
        try:
            next(myos_dir.iterdir())
            return
        except StopIteration:
            pass
        except Exception:
            return
        try:
            myos_dir.rmdir()
        except Exception:
            return

    def _read_folder_tag_colors(self, folder_path: Path) -> Dict[str, str]:
        registry_path = self._resolve_tag_registry_path(folder_path)
        if not registry_path or not registry_path.exists():
            return {}
        try:
            raw = json.loads(registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        plugin = raw.get("colored-tags-wrangler", {})
        entries = plugin.get("tags", []) if isinstance(plugin, dict) else []
        if not isinstance(entries, list):
            return {}
        result: Dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            color = _normalize_hex_color(str(entry.get("color", "")).strip())
            if not color:
                continue
            names_raw = str(entry.get("name", ""))
            for part in [piece.strip() for piece in names_raw.split(";") if piece.strip()]:
                tag = _normalize_tag_value(part)
                if tag:
                    result[tag] = color
        return result

    def _write_folder_tag_colors(self, folder_path: Path, colors: Dict[str, str]) -> None:
        registry_path = self._resolve_tag_registry_path(folder_path)
        if not registry_path:
            return
        payload: Dict[str, str] = {}
        for key, value in (colors or {}).items():
            tag = _normalize_tag_value(str(key or ""))
            color = _normalize_hex_color(str(value or ""))
            if tag and color:
                payload[tag] = color
        if not payload:
            return
        try:
            existing = {}
            if registry_path.exists():
                loaded = json.loads(registry_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    existing = loaded
            if not isinstance(existing, dict):
                existing = {}
            for tag, color in payload.items():
                self._assign_tag_color_in_registry(existing, tag, color)
            registry_path.parent.mkdir(parents=True, exist_ok=True)
            registry_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            return

    def _assign_tag_color_in_registry(self, registry_data: Dict[str, Any], tag: str, color_hex: str) -> bool:
        safe_tag = _normalize_tag_value(tag)
        normalized_color = _normalize_hex_color(color_hex)
        if not safe_tag or not normalized_color:
            return False
        root = registry_data if isinstance(registry_data, dict) else {}
        plugin = root.setdefault("colored-tags-wrangler", {})
        if not isinstance(plugin, dict):
            plugin = {}
            root["colored-tags-wrangler"] = plugin
        entries = plugin.setdefault("tags", [])
        if not isinstance(entries, list):
            entries = []
            plugin["tags"] = entries
        settings = plugin.setdefault("settings", {})
        if not isinstance(settings, dict):
            settings = {}
            plugin["settings"] = settings
        separate_background = bool(settings.get("separateBackground", True))

        target_idx = None
        target_names: List[str] = []
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            names = [_normalize_tag_value(p.strip()) for p in str(entry.get("name", "")).split(";") if p.strip()]
            names = [n for n in names if n]
            if safe_tag in names:
                target_idx = idx
                target_names = names
                break

        if target_idx is None:
            new_entry: Dict[str, Any] = {"name": safe_tag, "color": normalized_color, "luminanceOffset": 15}
            if separate_background:
                new_entry["background"] = _lighten_hex(normalized_color)
            entries.append(new_entry)
            return True

        entry = entries[target_idx]
        if len(target_names) <= 1:
            entry["color"] = normalized_color
            if separate_background:
                entry["background"] = _lighten_hex(normalized_color)
            elif "background" in entry:
                entry.pop("background", None)
            return True

        remaining = [n for n in target_names if n != safe_tag]
        entry["name"] = ";".join(remaining)
        new_entry = {"name": safe_tag, "color": normalized_color, "luminanceOffset": int(entry.get("luminanceOffset", 15))}
        if separate_background:
            new_entry["background"] = _lighten_hex(normalized_color)
        entries.append(new_entry)
        return True

    def _find_vault_root_for_path(self, file_path: Path) -> Optional[Path]:
        start = file_path if file_path.is_dir() else file_path.parent
        for parent in [start, *start.parents]:
            if (parent / "app.json").exists() or (parent / ".obsidian" / "app.json").exists() or (parent / ".obsidian").exists():
                return parent
        return None

    def _resolve_tag_registry_path(self, folder_path: Path) -> Optional[Path]:
        vault_root = self._find_vault_root_for_path(folder_path)
        if vault_root is None:
            project_root = find_project_root(folder_path)
            vault_root = project_root if project_root else None
        if vault_root is None:
            return None
        root_app = vault_root / "app.json"
        obs_app = vault_root / ".obsidian" / "app.json"
        if root_app.exists():
            return root_app
        if obs_app.exists():
            return obs_app
        if (vault_root / ".obsidian").exists():
            return obs_app
        return root_app

    def _remove_legacy_folder_tag_colors_file(self, folder_path: Path) -> None:
        legacy = folder_path / ".MyOS" / "tagColors.json"
        try:
            if legacy.exists():
                legacy.unlink()
        except OSError:
            pass

    def _get_folder_batch(self, folder_path: Path) -> Dict[str, Optional[str]]:
        """Return batch image URL or batchText from .MyOS/batch.* (batch1.svg etc. ignored)."""
        myos = folder_path / ".MyOS"
        if not myos.is_dir():
            return {"batch": None, "batchText": None}
        for ext in (".svg", ".png", ".webp"):
            batch_file = myos / f"batch{ext}"
            if batch_file.is_file():
                return {"batch": batch_file.as_uri(), "batchText": None}
        batch_md = myos / "batch.md"
        if batch_md.is_file():
            try:
                text = batch_md.read_text(encoding="utf-8", errors="replace")
                _, body = _split_frontmatter(text)
                stem, ext = batch_md.stem, batch_md.suffix
                filename_heading = (stem + ext).lower()
                stem_lower = stem.lower()
                for line in body.splitlines():
                    cleaned = line.strip().lstrip("#").strip()
                    if not cleaned:
                        continue
                    if cleaned.lower() in (stem_lower, filename_heading):
                        continue
                    return {"batch": None, "batchText": cleaned[:3]}
            except Exception:
                pass
        return {"batch": None, "batchText": None}

    def _get_folder_batch_for_embryo(
        self, blueprint: Any, rel_path: str
    ) -> Dict[str, Optional[str]]:
        """Return batch from template source for virtual embryos."""
        birth_clinic = getattr(blueprint, "birth_clinic", None)
        if birth_clinic is None:
            return {"batch": None, "batchText": None}
        find_source = getattr(birth_clinic, "find_template_source", None)
        if not callable(find_source):
            return {"batch": None, "batchText": None}
        try:
            template_source = find_source(rel_path)
            return self._get_folder_batch(template_source)
        except (ValueError, Exception):
            return {"batch": None, "batchText": None}

    def _build_folder_entry(
        self,
        *,
        name: str,
        is_project: bool,
        is_embryo: bool,
        folder_type: int,
        color: Optional[str],
        folder_path: Optional[Path] = None,
        context_blueprint: Optional[Any] = None,
        embryo_rel_path: Optional[str] = None,
    ) -> FolderEntry:
        """Build a folder-like API entry with stable role keys for QML."""
        entry: Dict[str, Any] = {
            "name": str(name),
            "isProject": bool(is_project),
            "isEmbryo": bool(is_embryo),
            "folderType": int(folder_type),
            "color": str(color) if color else None,
        }
        batch_info: Dict[str, Optional[str]] = {"batch": None, "batchText": None}
        if folder_path:
            batch_info = self._get_folder_batch(folder_path)
        if (not batch_info["batch"] and not batch_info["batchText"]) and is_embryo and context_blueprint and embryo_rel_path:
            embryo_batch = self._get_folder_batch_for_embryo(context_blueprint, embryo_rel_path)
            if embryo_batch["batch"] or embryo_batch["batchText"]:
                batch_info = embryo_batch
        if batch_info["batch"]:
            entry["batch"] = batch_info["batch"]
        if batch_info["batchText"]:
            entry["batchText"] = batch_info["batchText"]
        return entry

    def _classify_folder_type(
        self,
        *,
        context_blueprint: Optional[Any],
        rel_path: str,
        is_embryo: bool,
    ) -> int:
        if is_embryo:
            return self.FOLDER_TYPE_EMBRYO
        if self._is_template_path(context_blueprint, rel_path):
            return self.FOLDER_TYPE_BORN
        return self.FOLDER_TYPE_NORMAL

    def _is_template_path(self, context_blueprint: Optional[Any], rel_path: str) -> bool:
        if context_blueprint is None:
            return False
        rel = str(rel_path or "").strip().strip("/")
        if not rel:
            return False
        node = getattr(context_blueprint, "embryo_tree", None)
        if not isinstance(node, dict):
            return False
        for part in rel.split("/"):
            if not isinstance(node, dict) or part not in node:
                return False
            node = node.get(part)
        return True

    def _build_file_entry(
        self,
        *,
        name: str,
        is_dir: bool,
        path: str,
        tags: List[str],
        is_embryo: bool = False,
    ) -> FileEntryWithOptionalEmbryo:
        entry: FileEntryWithOptionalEmbryo = {
            "name": str(name),
            "isDir": bool(is_dir),
            "path": str(path),
            "tags": [str(tag) for tag in (tags or [])],
        }
        if is_embryo:
            entry["isEmbryo"] = True
            return entry
        # One stat for the list view's columns; folder sizes come from live measurement.
        try:
            info = os.stat(path)
        except OSError:
            return entry
        entry["modifiedTs"] = float(info.st_mtime)
        entry["accessedTs"] = float(info.st_atime)
        entry["permissions"] = stat.filemode(info.st_mode)
        entry["owner"] = _user_name(info.st_uid)
        entry["group"] = _group_name(info.st_gid)
        if not is_dir:
            entry["sizeBytes"] = int(info.st_size)
        elif os.path.isfile(os.path.join(path, ".MyOS", "Project.md")):
            entry["isProject"] = True  # the P badge on the folder
            color = self._resolve_effective_project_color(Path(path))
            if color:
                entry["projectColor"] = color  # behind the folder's name
        return entry

    def acl_summary(self, path: str, entry_paths: Iterable[str]) -> Dict[str, Any]:
        """
        Data of the ACL filter panel for a listed folder (see ACLView.listing_summary):
        {hasAcls, path, principals, access}, or {hasAcls: False} when the project has
        no ACLs.md. Read-only and without an audit event per entry (only the check
        below is audited), so it can run for large listings in a background task.
        """
        view = self._visible_acl_view(path)
        if view is None:
            return {"hasAcls": False}
        folder = Path(path).expanduser().resolve()
        summary = view.listing_summary(folder, [str(p) for p in entry_paths])
        me = self._acl_user_at(folder)
        can_edit = acl_can_edit(folder, me)
        # Not one of the people of this project (e.g. on another computer): say so, and
        # whom the user may say they are (core.identity; admins only by hand).
        # In a template the people are those of future projects: no hint there.
        listed = not view.policy.users or me in view.policy.users or is_template_root(view.project_root)
        choices = claimable_people(folder) if not listed and self._acl_user_override is None else []
        return {"hasAcls": True, "path": str(folder), "canEdit": can_edit, "listed": listed,
                "whoChoices": choices, **summary}

    def acl_claim_identity(self, path: str, name: str) -> Dict[str, Any]:
        """Remember on this computer that the user is the person name of path's project
        (core.identity.claim_person). Returns {ok, reason} like acl_set_role_rights."""
        return self._acl_edit(lambda: claim_person(path, name))

    def _visible_acl_view(self, path: str) -> Optional[ACLView]:
        """ACLView for path, or None without ACLs.md or when the user may not see it."""
        view = ACLView.for_path(path)
        if view is None:
            return None
        # Security: the panels show the content of ACLs.md (who may do what); with
        # enforcement on, only a user who may read ACLs.md gets to see it.
        probe = self._acl_probe("read", view.project_root / ".MyOS" / "ACLs.md")
        if probe is not None and probe.enforced and not probe.allowed:
            return None
        return view

    def trash_entries(self, path: str) -> List[Dict[str, Any]]:
        """
        Trash of the project path lies in (nearest project), newest first, as
        {name, original, deletedAt (ISO), deletedBy, isDir}. Only entries the user could
        have deleted at their original place are listed (see Designdocument Trash.md).
        """
        root = find_project_root(self._resolve_path(path))
        if root is None:
            return []
        entries = [e for e in trash.list_trash(root) if self._may_delete(root / e.original)]
        entries.sort(key=lambda e: e.deleted_at, reverse=True)
        return [
            {"name": e.name, "original": e.original, "deletedAt": e.deleted_at.isoformat(),
             "deletedBy": e.deleted_by, "isDir": e.is_dir}
            for e in entries
        ]

    def trash_restore(self, path: str, name: str) -> Dict[str, Any]:
        """Restore name from the trash of path's project; {ok, reason, path}."""
        return self._trash_op(path, name, restore=True)

    def trash_delete_finally(self, path: str, name: str) -> Dict[str, Any]:
        """Remove name from the trash of path's project for good; {ok, reason, path}."""
        return self._trash_op(path, name, restore=False)

    def trash_empty(self, path: str) -> Dict[str, Any]:
        """Delete for good what the user may delete in path's project trash; counts the rest."""
        root = find_project_root(self._resolve_path(path))
        deleted = skipped = 0
        for entry in (trash.list_trash(root) if root else []):
            if self._trash_op(path, entry.name, restore=False)["ok"]:
                deleted += 1
            else:
                skipped += 1
        return {"ok": True, "deleted": deleted, "skipped": skipped}

    def _trash_op(self, path: str, name: str, restore: bool) -> Dict[str, Any]:
        root = find_project_root(self._resolve_path(path))
        entry = next((e for e in trash.list_trash(root) if e.name == name), None) if root else None
        if entry is None:
            return {"ok": False, "reason": "missing", "path": ""}
        # Security: the trash keeps the rights of the original place (delete there).
        if not self._may_delete(root / entry.original):
            return {"ok": False, "reason": "permission", "path": ""}
        try:
            if restore:
                return {"ok": True, "reason": "", "path": str(trash.restore(root, name))}
            trash.delete_finally(root, name)
        except (trash.TrashError, OSError):
            return {"ok": False, "reason": "failed", "path": ""}
        return {"ok": True, "reason": "", "path": ""}

    def _may_delete(self, target: Path) -> bool:
        probe = self._acl_probe("delete", target)
        return not (probe and probe.enforced and not probe.allowed)

    def acl_has_own_rule(self, path: str, role: str) -> bool:
        """Whether role has a rule of its own at exactly path ("back to inherited" possible)."""
        return own_acl_rule(path, role) is not None

    def acl_set_role_rights(self, path: str, role: str, rights: Optional[List[str]]) -> Dict[str, Any]:
        """
        Set role's rights at path in the governing ACLs.md (see acl_edit.set_role_rights):
        rights is the complete list, [] = locked out ("none"), None = back to inherited.
        Returns {ok, reason} (see _acl_edit). The editor is the user ACLs are checked for.
        """
        return self._acl_edit(lambda: set_role_rights(
            path, role, None if rights is None else set(rights), editor=self._acl_user_at(path)))

    def acl_user_groups(self, path: str, user: str) -> Dict[str, Any]:
        """
        The groups dialog for one person: {name, groups: [{key, name, member, rights}]},
        groups sorted by name, rights = what the group may at path (in RIGHTS_ORDER).
        {} without visible ACLs or for a person not listed in # Users.
        """
        view = self._visible_acl_view(path)
        return (view.user_groups(user, path) if view is not None else None) or {}

    def acl_set_user_groups(self, path: str, user: str, groups: List[str]) -> Dict[str, Any]:
        """
        Set the groups of user (whole project) in the ACLs.md governing path (see
        acl_edit.set_user_roles); [] removes the person. Returns {ok, reason} like
        acl_set_role_rights.
        """
        return self._acl_edit(lambda: set_user_roles(path, user, set(groups), editor=self._acl_user_at(path)))

    def acl_group_choices(self, path: str) -> Dict[str, Any]:
        """The groups dialog for a person still to be added: {groups: [{key, name, member,
        rights}]} like acl_user_groups, nobody a member. {} without visible ACLs."""
        view = self._visible_acl_view(path)
        return {"groups": view.group_choices(path)} if view is not None else {}

    def acl_add_user(self, path: str, name: str, groups: List[str]) -> Dict[str, Any]:
        """
        Add a person with their groups to # Users of the ACLs.md governing path (see
        acl_edit.add_user). Returns {ok, reason} like acl_set_role_rights, and "exists"
        when a person of that name is listed already.
        """
        return self._acl_edit(lambda: add_user(path, name, set(groups), editor=self._acl_user_at(path)))

    def _acl_edit(self, edit: Callable[[], Any]) -> Dict[str, Any]:
        """Run an ACLs.md edit; {ok, reason}: "permission" (no change right), "lockout"
        (the editor would lose that right), "exists" (person listed already) or "invalid"
        (with a message)."""
        try:
            edit()
        except PermissionError:
            return {"ok": False, "reason": "permission"}
        except ACLSelfLockoutError:
            return {"ok": False, "reason": "lockout"}
        except ACLPersonExistsError:
            return {"ok": False, "reason": "exists"}
        except (ACLEditError, OSError) as exc:
            return {"ok": False, "reason": "invalid", "message": str(exc)}
        # Security: checks of this session follow the new rules at once. Only rebuilt when
        # configured from the environment (a service set via set_acl_enforcement stays).
        env_mode = str(os.environ.get("MYOS_ACL_MODE") or "off").strip().lower()
        if self._acl_enforcement is not None and env_mode in {"monitor", "enforce"}:
            self._configure_acl_from_env()
        return {"ok": True, "reason": ""}

    # How often (in entries) a running measurement asks whether it should go on.
    _MEASURE_CHECK_EVERY = 256

    def measure_folder_size(
        self,
        path: str,
        max_entries: Optional[int] = None,
        should_continue: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Measure a folder's size live (nothing is persisted). Symlinks are not followed
        and other filesystems below the folder are not entered (like du -x).
        With max_entries the walk stops after that many entries and reports the bytes
        counted so far as a lower bound (complete=False), so one huge folder cannot
        hold up the sizes of all others. should_continue is polled while walking; when
        it returns False the walk stops the same way (navigation away, app quit).
        """
        try:
            target = self._resolve_path(path)
        except Exception:
            return {"bytes": 0, "complete": True}
        # Read-only and works anywhere, not only inside MyOS projects.
        if not target.is_dir():
            return {"bytes": 0, "complete": True}
        root_device = self._device_id(target)
        total = 0
        visited = 0
        stack: List[Path] = [target]
        while stack:
            current = stack.pop()
            if self._device_id(current) != root_device:
                continue
            try:
                with os.scandir(current) as it:
                    for entry in it:
                        if max_entries is not None and visited >= max_entries:
                            return {"bytes": total, "complete": False}
                        if (
                            should_continue is not None
                            and visited % self._MEASURE_CHECK_EVERY == 0
                            and not should_continue()
                        ):
                            return {"bytes": total, "complete": False}
                        visited += 1
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                total += int(entry.stat(follow_symlinks=False).st_size)
                        except OSError:
                            continue
            except OSError:
                continue
        return {"bytes": total, "complete": True}

    @staticmethod
    def _device_id(path: Path) -> int:
        try:
            return os.lstat(path).st_dev
        except OSError:
            return -1

    def has_myos_dir(self, path: str) -> bool:
        target = self._resolve_path(path)
        return (target / ".MyOS").is_dir()

    def is_project(self, path: str) -> bool:
        target = self._resolve_path(path)
        return (target / ".MyOS" / "Project.md").is_file()

    def is_dir(self, path: str) -> bool:
        target = self._resolve_path(path)
        return target.is_dir()

    def get_project_color(self, path: str) -> Optional[str]:
        target = self._resolve_path(path)
        is_dir = target.is_dir()
        is_proj = self.is_project(str(target)) if is_dir else False
        out = None
        if is_dir and is_proj:
            out = self._resolve_effective_project_color(target)
        return out

    def get_default_project_color(self) -> Optional[str]:
        return self._root_default_project_color

    def get_effective_project_color(self, path: str) -> Optional[str]:
        target = self._resolve_path(path)
        out = self._resolve_project_color(
            target,
            require_project=False,
            project_only=True,
            stop_at_project_root=False,
        )
        return out

    def get_project_icon(self, path: str) -> Optional[str]:
        target = self._resolve_path(path)
        if not target.is_dir():
            return None
        config_path = self._desk_service.find_config(target, config_name="Desk.md")
        if config_path is None:
            return None
        try:
            desk = DeskConfig.from_file(config_path)
        except Exception:
            return None
        icon_value = str(desk.project_icon or "").strip()
        return icon_value or None

    def _resolve_direct_project_color(self, path: Path) -> Optional[str]:
        return self._read_first_color(path, [".MyOS/Color.md", ".MyOS/Project.md"])

    def _resolve_effective_project_color(self, path: Path) -> Optional[str]:
        return self._resolve_project_color(
            path,
            require_project=True,
            project_only=True,
            stop_at_project_root=False,
        )

    def _resolve_project_color(
        self,
        path: Path,
        *,
        require_project: bool = False,
        project_only: bool = False,
        stop_at_project_root: bool = True,
    ) -> Optional[str]:
        if not path or not path.is_dir():
            return None
        if require_project and not self.is_project(str(path)):
            return None

        cache_key = f"{path}|{int(bool(require_project))}|{int(bool(project_only))}|{int(bool(stop_at_project_root))}"
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        stop: Optional[Path] = None
        if stop_at_project_root and self.project_root and is_within(path, self.project_root):
            stop = self.project_root

        current = path
        while True:
            if (not project_only) or current == self.project_root or self.is_project(str(current)):
                color = self._resolve_direct_project_color(current)
                if color:
                    self._color_cache[cache_key] = color
                    return color
            if stop is not None and current == stop:
                break
            if current == current.parent:
                break
            if stop is not None and not is_within(current.parent, stop):
                break
            current = current.parent

        self._color_cache[cache_key] = None
        return None

    def _resolve_template_color(self, rel_path: str, name: str) -> Optional[str]:
        if not self.blueprint:
            return None
        parts = [p for p in rel_path.split("/") if p]
        parts.append(name)
        for template_name in self.blueprint.template_names:
            base = self.blueprint.templates_dir / template_name
            candidate = base.joinpath(*parts)
            if not candidate.exists():
                continue
            color = self._find_color_upwards(candidate, base)
            if color:
                return color
        return None

    def _find_color_upwards(self, start: Path, stop: Path) -> Optional[str]:
        return self._find_first_color_upwards(start, stop, [".MyOS/Color.md", "Color.md"])

    def _read_first_color(self, base: Path, relative_paths: List[str]) -> Optional[str]:
        for rel in relative_paths:
            color = self._read_color_file(base / rel)
            if color:
                return color
        return None

    def _find_first_color_upwards(self, start: Path, stop: Path, relative_paths: List[str]) -> Optional[str]:
        current = start
        while True:
            color = self._read_first_color(current, relative_paths)
            if color:
                return color
            if current == stop or current == current.parent:
                return None
            current = current.parent

    def _read_color_file(self, path: Path) -> Optional[str]:
        """Liest eine Farbe aus einer Datei, robust gegenüber Whitespace und Formatierung."""
        try:
            if not path.exists():
                return None

            content = path.read_text(encoding="utf-8")
            color = self._extract_color(content)
            return color

        except Exception:
            return None

    def _extract_color(self, text: str) -> Optional[str]:
        """Extrahiert einen Hex-Farbcode aus einem Text, robust gegenüber Whitespace."""
        if not text:
            return None
        
        # Suche nach # gefolgt von 6 oder 3 Hex-Ziffern
        match = re.search(r"(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b", text)
        if not match:
            return None
        
        raw = match.group(0)
        raw = raw.strip()
        
        # Stelle sicher, dass wir einen sauberen String haben
        if len(raw) == 4:  # 3-stellig
            r, g, b = raw[1], raw[2], raw[3]
            # Expandiere zu 6-stellig für QML-Kompatibilität
            expanded = f"#{r}{r}{g}{g}{b}{b}"
            return expanded.upper()
        
        if len(raw) == 7:  # 6-stellig
            return raw.upper()
        
        return None

    def can_create_project(self, path: str) -> bool:
        """
        Whether path may become a project (P-Button): an existing folder below a .MyOS
        (inside the projects tree), no project yet, no template folder and no .MyOS folder.
        """
        try:
            target = Path(path).expanduser().resolve()
        except (OSError, RuntimeError):
            return False
        if not target.is_dir() or (target / ".MyOS" / "Project.md").exists() or ".MyOS" in target.parts:
            return False
        if ProjectConfig._find_parent_myos(target) is None:
            return False  # creating needs a .MyOS above (ProjectConfig.create)
        templates_dir = _resolve_templates_dir(target)
        if templates_dir is not None:
            templates_dir = templates_dir.resolve()
            if target == templates_dir or templates_dir in target.parents:
                return False  # templates are folder structures, not projects
        probe = self._acl_probe("write_dir", target)
        return not (probe and probe.enforced and not probe.allowed)

    def can_remove_project(self, path: str) -> bool:
        """Whether path is a project that can become an ordinary folder again (crossed-out
        P-Button; core.project_unmake): not the top project, not in a template."""
        try:
            target = Path(path).expanduser().resolve()
        except (OSError, RuntimeError):
            return False
        return can_unmake(target) and self._may_remove_project(target)

    def remove_project(self, path: str, keep_own: bool) -> Dict[str, Any]:
        """
        Make the project at path an ordinary folder again. {ok, reason, own}: reason "own"
        lists its settings of its own (ask, then call again with keep_own: they go into
        the parent project's trash), "permission", or "invalid".
        """
        try:
            target = Path(path).expanduser().resolve()
        except (OSError, RuntimeError):
            return {"ok": False, "reason": "invalid", "own": []}
        if not can_unmake(target):
            return {"ok": False, "reason": "invalid", "own": []}
        if not self._may_remove_project(target):
            return {"ok": False, "reason": "permission", "own": []}
        try:
            unmake_project(target, self._acl_user_at(target), keep_own=bool(keep_own))
        except ProjectHasOwnSettings as exc:
            return {"ok": False, "reason": "own", "own": exc.names}
        except (OSError, ValueError, trash.TrashError):
            return {"ok": False, "reason": "invalid", "own": []}
        return {"ok": True, "reason": "", "own": []}

    def _may_remove_project(self, target: Path) -> bool:
        # Security: a project with its own ACLs.md stops governing its folders when it goes;
        # that is a change of rights, for those who may change them. Otherwise it is a
        # change to the folder, like creating the project.
        if (target / ".MyOS" / "ACLs.md").is_file():
            return acl_can_edit(target, self._acl_user_at(target))
        probe = self._acl_probe("write_dir", target)
        return not (probe and probe.enforced and not probe.allowed)

    def create_project(self, path: str) -> bool:
        # Security: the same checks as for the button, whatever the GUI shows.
        if not self.can_create_project(path):
            return False
        target = Path(path).expanduser().resolve()
        return ProjectConfig.make_project(target)

    def create_folder(self, path: str, name: str) -> Optional[str]:
        base = self._resolve_dir(path)
        if base is None:
            return None
        acl_result = self._acl_probe("create_folder", base)
        if acl_result and acl_result.enforced and not acl_result.allowed:
            return None
        cleaned = _clean_entry_name(name)
        if cleaned is None:
            return None
        target = base / cleaned
        if target.exists():
            return None
        try:
            target.mkdir(parents=False, exist_ok=False)
        except Exception:
            return None
        return str(target)

    def create_note(self, path: str, name: str) -> Optional[str]:
        base = self._resolve_dir(path)
        if base is None:
            return None
        acl_result = self._acl_probe("create_note", base)
        if acl_result and acl_result.enforced and not acl_result.allowed:
            return None

        cleaned = _clean_entry_name(name, allow_empty=True)
        if cleaned is None:
            return None
        if not cleaned:
            cleaned = "New Note"
        if not cleaned.lower().endswith(".md"):
            cleaned = f"{cleaned}.md"

        target = base / cleaned
        if target.exists():
            stem = target.stem
            suffix = target.suffix or ".md"
            for idx in range(2, 200):
                candidate = base / f"{stem} {idx}{suffix}"
                if not candidate.exists():
                    target = candidate
                    break
            else:
                return None
        try:
            title = target.stem.strip() or "New Note"
            target.write_text(f"# {title}\n\n", encoding="utf-8")
        except Exception:
            return None
        return str(target)

    def rename_entry(self, path: str, new_name: str) -> Optional[str]:
        try:
            source = self._resolve_path(path)
        except Exception:
            return None
        acl_result = self._acl_probe("rename", source)
        if acl_result and acl_result.enforced and not acl_result.allowed:
            return None
        if not source.exists():
            return None
        return self._rename_one(source, new_name)

    def _rename_one(self, source: Path, target_name: str) -> Optional[str]:
        cleaned = _clean_entry_name(target_name)
        if cleaned is None:
            return None

        resolved_target_name = cleaned
        if source.is_file() and "." not in cleaned and source.suffix:
            resolved_target_name = f"{cleaned}{source.suffix}"
        target = source.with_name(resolved_target_name)
        if target == source:
            return str(source)
        if target.exists():
            return None
        if self._acl_rules_blocked(source, target):
            return None
        try:
            source.rename(target)
        except Exception:
            return None
        self._acl_rules_follow(source, target)
        return str(target)

    def _acl_rules_blocked(self, old: Path, new: Path) -> bool:
        """
        Security: rules waiting for the new path would add up with the rules that follow
        the entry (acl_edit.check_move_rules); such a rename or move is refused.
        """
        try:
            check_move_rules(old, new)
        except ACLEditError:
            return True
        except OSError:
            return False
        return False

    def _acl_rules_follow(self, old: Path, new: Path) -> None:
        """Rewrite ACL rules of old to new after a rename or move (rights unchanged)."""
        try:
            move_acl_rules(old, new, editor=self._acl_user_at(old))
        except (ACLEditError, OSError):
            pass

    def _iter_unique_sources(self, values: List[str]):
        seen: set[str] = set()
        for raw in (values or []):
            source_text = str(raw or "").strip()
            if not source_text:
                continue
            try:
                source = Path(source_text).expanduser().resolve()
            except Exception:
                # // Security: malformed paths (e.g. embedded NUL) are rejected early.
                yield None, source_text, False, True
                continue
            source_key = str(source)
            duplicate = source_key in seen
            if not duplicate:
                seen.add(source_key)
            yield source, source_key, duplicate, False

    def _prepare_move(self, source: Path, target_dir: Path):
        source_key = str(source)
        if not source.exists():
            return {"status": "error", "reason": "source_missing", "source": source_key}
        if source == target_dir:
            return {"status": "skip", "reason": "same_as_target", "source": source_key}
        if source.parent == target_dir:
            return {"status": "skip", "reason": "already_in_target", "source": source_key}
        if is_within(target_dir, source):
            return {"status": "error", "reason": "target_inside_source", "source": source_key}
        destination = target_dir / source.name
        if destination.exists():
            return {
                "status": "error",
                "reason": "destination_exists",
                "source": source_key,
                "destination": str(destination),
            }
        return {
            "status": "ok",
            "source": source_key,
            "destination": destination,
        }

    def rename_entries_batch(self, paths: List[str], replace_from: str, replace_to: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": True,
            "renamed": [],
            "unchanged": 0,
            "failed": 0,
            "errors": [],
        }
        token_from = str(replace_from or "")
        token_to = str(replace_to or "")
        if token_from == "":
            result["ok"] = False
            result["errors"].append({"source": "", "reason": "missing_replace_from"})
            return result

        for source, source_key, duplicate, invalid in self._iter_unique_sources(paths):
            if invalid:
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "invalid_path"})
                continue
            if duplicate:
                continue

            acl_result = self._acl_probe("rename", source)
            if acl_result and acl_result.enforced and not acl_result.allowed:
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "acl_denied"})
                continue
            if not source.exists():
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "source_missing"})
                continue
            if source.is_dir():
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "unsupported_type"})
                continue

            stem = source.stem
            suffix = source.suffix
            new_stem = stem.replace(token_from, token_to)
            if new_stem == stem:
                result["unchanged"] += 1
                continue

            first_target = f"{new_stem}{suffix}"
            renamed = self._rename_one(source, first_target)
            if not renamed:
                for idx in range(1, 1000):
                    candidate = f"{new_stem}({idx}){suffix}"
                    renamed = self._rename_one(source, candidate)
                    if renamed:
                        break
            if renamed:
                result["renamed"].append(renamed)
            else:
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "rename_failed"})

        result["ok"] = result["failed"] == 0
        return result

    def suggest_batch_rename_token(self, paths: List[str]) -> str:
        stems: List[str] = []
        for source, _, duplicate, invalid in self._iter_unique_sources(paths):
            if invalid:
                continue
            if duplicate:
                continue
            stem, _ = _split_stem_and_ext(source.name)
            stems.append(str(stem or ""))

        prefix = _longest_common_prefix(stems)
        while len(prefix) > 1 and prefix[-1] in "0123456789_- ":
            prefix = prefix[:-1]
        if prefix:
            return prefix
        return stems[0] if stems else ""

    def delete_entries(self, paths: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {"ok": True, "deleted": [], "errors": [], "reabsorbed": []}
        emptied: List[Path] = []
        for source, key, duplicate, invalid in self._iter_unique_sources(paths):
            if invalid:
                result["errors"].append({"source": key, "reason": "invalid_path"})
                continue
            if duplicate:
                continue
            acl_result = self._acl_probe("delete", source)
            if acl_result and acl_result.enforced and not acl_result.allowed:
                result["errors"].append({"source": key, "reason": "acl_denied"})
                continue
            if not source.exists():
                result["errors"].append({"source": key, "reason": "missing"})
                continue
            # Deleting is undoable: into the project's trash (.MyOS/Trash), outside
            # projects into the system trash. Nothing is removed for good here.
            try:
                if trash.project_trash_root(source) is not None:
                    trash.move_to_trash(source, deleted_by=self._acl_user_at(source))
                else:
                    _move_to_system_trash(source)
                result["deleted"].append(key)
                emptied.append(source.parent)
            except Exception:
                result["errors"].append({"source": key, "reason": "delete_failed"})
        result["reabsorbed"] = self._reabsorb_emptied_folders(emptied)
        result["ok"] = len(result["errors"]) == 0
        return result

    def _reabsorb_emptied_folders(self, folders: Iterable[Path]) -> List[str]:
        """
        Turn born template folders that an operation just emptied back into embryos
        (Blueprint.reabsorb_upwards). Returns the removed folders as strings.
        """
        removed: List[str] = []
        for folder in dict.fromkeys(folders):
            if not folder.is_dir():
                continue
            root, blueprint = self._resolve_context_for_target(folder)
            if not root or blueprint is None or folder == root or not is_within(folder, root):
                continue
            try:
                removed.extend(str(path) for path in blueprint.reabsorb_upwards(str(folder.relative_to(root))))
            except Exception:
                continue
        return removed

    def move_entry(self, source: str, target_dir: str) -> bool:
        _dbg = os.environ.get("MYOS_DEBUG_BIRTH")
        if _dbg:
            print(f"[birth] move_entry source={source!r} target_dir={target_dir!r}")
        try:
            src = self._resolve_path(source)
        except Exception:
            return False
        dst_dir, reason = self._resolve_or_materialize_target_dir(target_dir)
        if _dbg:
            print(f"[birth] move_entry after resolve: dst_dir={dst_dir!r} reason={reason!r}")
        if dst_dir is None:
            return False
        acl_target = self._acl_probe("write_dir", dst_dir)
        if acl_target and acl_target.enforced and not acl_target.allowed:
            return False
        acl_source = self._acl_probe("move", src)
        if acl_source and acl_source.enforced and not acl_source.allowed:
            return False
        if not dst_dir.is_dir():
            return False
        move_plan = self._prepare_move(src, dst_dir)
        if move_plan.get("status") != "ok":
            return False
        destination = move_plan["destination"]
        if self._acl_rules_blocked(src, destination):
            return False
        try:
            shutil.move(str(src), str(destination))
            self._acl_rules_follow(src, destination)
            self.catch_up_filing(str(destination.parent))
            self._reabsorb_emptied_folders([src.parent])
            return True
        except Exception:
            return False

    def move_entries(self, sources: List[str], target_dir: str) -> Dict[str, Any]:
        _dbg = os.environ.get("MYOS_DEBUG_BIRTH")
        if _dbg:
            print(f"[birth] move_entries target_dir={target_dir!r} sources#={len(sources)}")
        result: Dict[str, Any] = {
            "ok": True,
            "moved": [],
            "skipped": [],
            "errors": [],
            "reabsorbed": [],
        }
        emptied: List[Path] = []
        dst_dir, target_reason = self._resolve_or_materialize_target_dir(target_dir)
        if _dbg:
            print(f"[birth] move_entries after resolve: dst_dir={dst_dir!r} reason={target_reason!r}")
        if dst_dir is None:
            result["ok"] = False
            reason = target_reason or "target_not_directory"
            result["errors"].append({"source": "", "reason": reason, "target": str(target_dir)})
            return result
        acl_target = self._acl_probe("write_dir", dst_dir)
        if acl_target and acl_target.enforced and not acl_target.allowed:
            result["errors"].append({"source": "", "reason": "acl_denied_target", "target": str(dst_dir)})
            result["ok"] = False
            return result

        for src, src_key, duplicate, invalid in self._iter_unique_sources(sources):
            if invalid:
                result["errors"].append({"source": src_key, "reason": "invalid_path"})
                continue
            if duplicate:
                result["skipped"].append({"source": src_key, "reason": "duplicate_source"})
                continue
            acl_source = self._acl_probe("move", src)
            if acl_source and acl_source.enforced and not acl_source.allowed:
                result["errors"].append({"source": src_key, "reason": "acl_denied_source"})
                continue

            move_plan = self._prepare_move(src, dst_dir)
            status = move_plan.get("status")
            if status == "skip":
                result["skipped"].append({"source": src_key, "reason": move_plan["reason"]})
                continue
            if status != "ok":
                error_item = {"source": src_key, "reason": move_plan["reason"]}
                if "destination" in move_plan:
                    error_item["destination"] = move_plan["destination"]
                result["errors"].append(error_item)
                continue

            destination = move_plan["destination"]
            if self._acl_rules_blocked(src, destination):
                result["errors"].append({"source": src_key, "reason": "acl_rules_conflict"})
                continue
            try:
                shutil.move(str(src), str(destination))
                self._acl_rules_follow(src, destination)
                result["moved"].append({"source": src_key, "destination": str(destination)})
                emptied.append(src.parent)
                filed = self.catch_up_filing(str(destination.parent))
                for item in filed["moved"]:
                    if item["source"] == str(destination):
                        result.setdefault("sorted", []).append(item)
            except Exception:
                result["errors"].append({"source": src_key, "reason": "move_failed"})

        result["reabsorbed"] = self._reabsorb_emptied_folders(emptied)
        result["ok"] = len(result["errors"]) == 0
        return result

    def open_markdown(self, path: str) -> bool:
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return False
        acl_result = self._acl_probe("open_markdown", target)
        if acl_result and acl_result.enforced and not acl_result.allowed:
            return False
        # // Security: only open existing markdown files.
        if not target.is_file():
            return False
        if target.suffix.lower() not in {".md", ".markdown"}:
            return False
        opener = Path(__file__).resolve().parent / "bin" / "open_md.py"
        if not opener.exists():
            return False
        result = subprocess.run(
            [sys.executable, str(opener), str(target)], check=False
        )
        return result.returncode == 0

    def open_with(self, path: str, command: str) -> bool:
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return False
        cmd = str(command or "").strip()
        if not cmd:
            return False
        if not target.is_file():
            return False
        try:
            argv = shlex.split(cmd)
        except Exception:
            return False
        if not argv:
            return False
        try:
            subprocess.Popen(argv + [str(target)])
            return True
        except Exception:
            return False

    def notify_config_changed(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        if notify_project_config_changed is None:
            return False
        try:
            result = notify_project_config_changed(target, dry_run=False)
            return bool(result.get("ok"))
        except Exception:
            return False
