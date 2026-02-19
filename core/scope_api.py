from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import re
import shutil
import json
import shlex
from typing import List, Optional, Dict, Any, TypedDict
from core.tags import read_tags
from core.acl import ACLAuthorizer
from core.acl_enforcement import ACLCheckRequest, ACLCheckResult, ACLEnforcementService
from core.desk_service import DeskService
from core.sort import SortRule, iter_sort_rule_roots, resolve_effective_sort_rules
from core.sort_runtime import SortRuntime

try:
    from core.localBlueprintLayer import Blueprint
    from core.project import ProjectConfig, notify_config_changed as notify_project_config_changed
except Exception:  # pragma: no cover - optional for non-MyOS paths
    Blueprint = None
    notify_project_config_changed = None


def find_project_root(start_path: Path) -> Optional[Path]:
    start_path = start_path.resolve()
    for candidate in [start_path] + list(start_path.parents):
        if (candidate / ".MyOS").exists():
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
    color: Optional[str]


class FileEntry(TypedDict):
    name: str
    isDir: bool
    path: str
    tags: List[str]


class FileEntryWithOptionalEmbryo(FileEntry, total=False):
    isEmbryo: bool
    folderSizeBytes: int


class ScopeApi:
    def __init__(self, start_path: str) -> None:
        self.start_path = Path(start_path).expanduser().resolve()
        self.project_root = None
        self.blueprint = None
        self._blueprint_cache: Dict[str, Optional[Any]] = {}
        self._color_cache: Dict[str, Optional[str]] = {}
        self._root_default_project_color: Optional[str] = None
        self._acl_enforcement: Optional[ACLEnforcementService] = None
        self._acl_user: str = str(os.environ.get("MYOS_ACL_USER") or os.environ.get("USER") or "local").strip().lower()
        self._acl_audit_events: List[Dict[str, Any]] = []
        self._acl_audit_file: Optional[Path] = None
        self._acl_audit_max_bytes: int = 262_144
        self._desk_service = DeskService()
        self._sort_runtime = SortRuntime()
        self.myos_root = find_top_project_root(self.start_path)
        self._set_project_root(find_project_root(self.start_path))
        self._configure_acl_from_env()
        self._refresh_desk_context(self.start_path)

    def _set_project_root(self, root: Optional[Path]) -> None:
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

    def update_context(self, path: str) -> None:
        target = self._resolve_path(path)
        root = find_project_root(target)
        if root != self.project_root:
            self._set_project_root(root)
            self._configure_acl_from_env()
        self._refresh_desk_context(target)

    def _refresh_desk_context(self, target: Path) -> None:
        self._desk_service.refresh_context(target)

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

    def preview_sort_target(self, file_path: str) -> Dict[str, Any]:
        try:
            target = self._resolve_path(file_path)
        except Exception:
            return {"ok": False, "reason": "invalid_path", "target": ""}
        if not target.exists() or not target.is_file():
            return {"ok": False, "reason": "missing_file", "target": ""}
        rules = self._resolve_sort_rules_for_target(target)
        resolved = self._sort_runtime.preview_target(target, rules, event="move")
        return {"ok": resolved.get("ok") == "1", "reason": resolved.get("reason"), "target": resolved.get("target", "")}

    def preview_sort_target_for_move(self, source_path: str, target_dir: str) -> Dict[str, Any]:
        try:
            source = self._resolve_path(source_path)
            target = self._resolve_path(target_dir)
        except Exception:
            return {"ok": False, "reason": "invalid_path", "target": ""}
        if not source.exists() or not source.is_file():
            return {"ok": False, "reason": "missing_file", "target": ""}
        simulated = target / source.name
        rules = self._resolve_sort_rules_for_target(target)
        resolved = self._sort_runtime.preview_target(simulated, rules, event="move")
        return {"ok": resolved.get("ok") == "1", "reason": resolved.get("reason"), "target": resolved.get("target", "")}

    def apply_sort_now(self, root_path: str) -> Dict[str, Any]:
        try:
            root = self._resolve_path(root_path)
        except Exception:
            return {"ok": False, "reason": "invalid_path", "moved": [], "errors": []}
        rules = self._resolve_sort_rules_for_target(root)
        return self._sort_runtime.apply_root(root, rules, event="move")

    def list_sort_watch_roots(self, path: str) -> List[str]:
        try:
            target = self._resolve_path(path)
        except Exception:
            return []
        rules = self._resolve_sort_rules_for_target(target)
        roots = [str(root) for root in iter_sort_rule_roots(rules)]
        return sorted(set(roots))

    def _resolve_sort_rules_for_target(self, target: Path) -> List[SortRule]:
        template_root = self._resolve_template_root_for_target(target)
        return resolve_effective_sort_rules(
            target,
            template_root=template_root,
            global_root=self.myos_root,
            config_name="Sort.md",
        )

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

    def set_acl_enforcement(self, service: Optional[ACLEnforcementService], user: Optional[str] = None) -> None:
        self._acl_enforcement = service
        if user is not None and str(user).strip():
            self._acl_user = str(user).strip().lower()

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

        root = self.project_root or self.start_path
        try:
            authorizer = ACLAuthorizer.from_project(root, backend=backend)
        except Exception:
            self._acl_enforcement = None
            self._acl_audit_file = None
            return

        self._acl_enforcement = ACLEnforcementService(authorizer, mode=mode)

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
        try:
            result = self._acl_enforcement.check(
                ACLCheckRequest(
                    user=self._acl_user,
                    action=acl_action,
                    resource=str(resource),
                )
            )
            self._on_acl_audit_event(
                {
                    "user": self._acl_user,
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

    def list_children(self, path: str, include_embryos: bool = True) -> List[FolderEntry]:
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
        if can_list_dirs:
            try:
                for child in sorted(target.iterdir()):
                    if child.name.startswith("."):
                        continue
                    if child.is_dir():
                        acl_child = self._acl_probe("read_dir", child)
                        if acl_child and acl_child.enforced and not acl_child.allowed:
                            continue
                        is_project = self.is_project(str(child))
                        project_color = self._resolve_effective_project_color(child) if is_project else None
                        entries.append(
                            self._build_folder_entry(
                                name=child.name,
                                is_project=is_project,
                                is_embryo=False,
                                color=project_color,
                            )
                        )
            except Exception:
                return []

        if can_list_virtual_embryos:
            rel = "" if target == context_root else str(target.relative_to(context_root))
            embryos = context_blueprint.get_embryos_at(rel)
            for name in embryos:
                if not any(item["name"] == name for item in entries):
                    embryo_path = target / name
                    acl_embryo = self._acl_probe("read_dir", embryo_path)
                    if acl_embryo and acl_embryo.enforced and not acl_embryo.allowed:
                        continue
                    embryo_color = self._resolve_template_color_for_context(context_blueprint, rel, name)
                    entries.append(
                        self._build_folder_entry(
                            name=name,
                            is_project=False,
                            is_embryo=True,
                            color=(embryo_color or parent_color),
                        )
                    )
            entries.sort(key=lambda item: item["name"])

        return entries

    def list_templates(self, path: str, include_embryos: bool = True) -> List[FolderEntry]:
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
        debug = os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}
        if not include_embryos:
            if debug:
                print(f"[scope_api] list_templates: include_embryos=False -> []")
            return []
        if not context_blueprint or not context_root or not is_within(target, context_root):
            if debug:
                print(
                    f"[scope_api] list_templates: blueprint={bool(context_blueprint)} "
                    f"project_root={context_root} target={target} -> []"
                )
            return []
        rel = "" if target == context_root else str(target.relative_to(context_root))
        try:
            parent_color = self._resolve_project_color_with_root(target, context_root)
            embryos = sorted(context_blueprint.get_embryos_at(rel))
            result = []
            for name in embryos:
                embryo_color = self._resolve_template_color_for_context(context_blueprint, rel, name)
                result.append(
                    self._build_folder_entry(
                        name=name,
                        is_project=False,
                        is_embryo=True,
                        color=(embryo_color or parent_color),
                    )
                )
            if debug:
                print(
                    f"[scope_api] list_templates: rel='{rel}' templates={context_blueprint.template_names} "
                    f"result={[item['name'] for item in result]}"
                )
            return result
        except Exception:
            if debug:
                print(f"[scope_api] list_templates: error for rel='{rel}'")
            return []

    def list_entries(self, path: str) -> List[FileEntryWithOptionalEmbryo]:
        target = self._resolve_dir(path)
        if target is None:
            return []
        self._acl_probe("read_dir", target)
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
                folder_size_bytes: Optional[int] = None
                if is_dir:
                    sidecar = self._read_folder_sidecar(child)
                    entry_tags = sidecar["tags"]
                    folder_size_bytes = self._compute_folder_size_bytes(child)
                    if sidecar["folder_size_bytes"] != folder_size_bytes:
                        self._write_folder_sidecar(child, sidecar["tags"], folder_size_bytes)
                else:
                    entry_tags = self._read_entry_tags(child, md_tag_cache)
                entry = self._build_file_entry(
                    name=child.name,
                    is_dir=is_dir,
                    path=str(child),
                    tags=entry_tags,
                    folder_size_bytes=folder_size_bytes,
                )
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
                    entries.append(
                        self._build_file_entry(
                            name=name,
                            is_dir=True,
                            path=str(target / name),
                            tags=[],
                            is_embryo=True,
                        )
                    )
        # File-browser style order: folders first, then files, both alphabetic.
        entries.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))
        self._prune_markdown_tag_cache(md_tag_cache, seen_md_files)
        self._save_markdown_tag_cache(target, md_tag_cache)

        return entries

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
        target = self._resolve_path(path)
        root = find_project_root(target)
        if not root:
            return []
        tags_file = root / ".MyOS" / "Tags.md"
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
        sidecar = self._read_folder_sidecar(target)
        self._write_folder_sidecar(target, cleaned, sidecar["folder_size_bytes"])
        self._remove_legacy_folder_tag_colors_file(target)
        return True

    def list_tag_buckets(self, path: str) -> Dict[str, Any]:
        target = self._resolve_dir(path)
        if target is None:
            return {
                "folderTags": [],
                "fileTags": [],
                "folderTagColors": {},
                "fileTagColors": {},
                "folderSizeBytes": 0,
            }
        sidecar = self._read_folder_sidecar(target)
        folder_tags = sidecar["tags"]
        folder_set = set(folder_tags)
        all_tag_colors = self._read_folder_tag_colors(target)
        folder_tag_colors = {tag: all_tag_colors[tag] for tag in folder_tags if tag in all_tag_colors}
        file_bag: Dict[str, bool] = {}
        for entry in self.list_entries(str(target)):
            if entry.get("isDir"):
                continue
            for raw in entry.get("tags") or []:
                tag = str(raw or "").strip()
                if tag:
                    file_bag[tag] = True
        file_tags = sorted([tag for tag in file_bag.keys() if tag not in folder_set], key=str.lower)
        file_tag_colors = {tag: all_tag_colors[tag] for tag in file_tags if tag in all_tag_colors}
        folder_size = sidecar["folder_size_bytes"]
        if folder_size is None:
            folder_size = self._compute_folder_size_bytes(target)
            self._write_folder_sidecar(target, folder_tags, folder_size)
        return {
            "folderTags": folder_tags,
            "fileTags": file_tags,
            "folderTagColors": folder_tag_colors,
            "fileTagColors": file_tag_colors,
            "folderSizeBytes": int(folder_size or 0),
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
        result: Dict[str, Any] = {"tags": [], "folder_size_bytes": None}
        sidecar = folder_path / ".MyOS" / "myTags.md"
        if not sidecar.exists():
            return result
        try:
            text = sidecar.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return result
        frontmatter, body = _split_frontmatter(text)
        tags = _extract_hash_line_tags_from_text(body if frontmatter else text)
        folder_size_bytes: Optional[int] = None
        if frontmatter:
            for raw in frontmatter.splitlines():
                line = str(raw or "").strip()
                if not line or ":" not in line:
                    continue
                key, value = line.split(":", 1)
                if key.strip().lower() != "folder_size_bytes":
                    continue
                try:
                    parsed = int(value.strip())
                    if parsed >= 0:
                        folder_size_bytes = parsed
                except ValueError:
                    pass
        result["tags"] = tags
        result["folder_size_bytes"] = folder_size_bytes
        return result

    def _write_folder_sidecar(self, folder_path: Path, tags: List[str], folder_size_bytes: Optional[int]) -> None:
        myos_dir = folder_path / ".MyOS"
        sidecar = myos_dir / "myTags.md"
        cleaned = sorted(
            set(_normalize_tag_value(tag) for tag in (tags or []) if _normalize_tag_value(tag)),
            key=str.lower,
        )
        size_value = 0
        if folder_size_bytes is not None:
            try:
                parsed = int(folder_size_bytes)
                if parsed >= 0:
                    size_value = parsed
            except (TypeError, ValueError):
                size_value = 0

        lines = ["---", f"folder_size_bytes: {size_value}", "---", ""]
        for tag in cleaned:
            lines.append(f"#{tag}")
        content = "\n".join(lines).rstrip() + "\n"

        try:
            myos_dir.mkdir(parents=True, exist_ok=True)
            old_content = sidecar.read_text(encoding="utf-8", errors="replace") if sidecar.exists() else None
            if old_content == content:
                return
            sidecar.write_text(content, encoding="utf-8")
        except Exception:
            return

    def _compute_folder_size_bytes(self, folder_path: Path) -> int:
        total = 0
        stack: List[Path] = [folder_path]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as it:
                    for entry in it:
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
        return max(0, int(total))

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

    def _build_folder_entry(
        self,
        *,
        name: str,
        is_project: bool,
        is_embryo: bool,
        color: Optional[str],
    ) -> FolderEntry:
        """Build a folder-like API entry with stable role keys for QML."""
        return {
            "name": str(name),
            "isProject": bool(is_project),
            "isEmbryo": bool(is_embryo),
            "color": str(color) if color else None,
        }

    def _build_file_entry(
        self,
        *,
        name: str,
        is_dir: bool,
        path: str,
        tags: List[str],
        is_embryo: bool = False,
        folder_size_bytes: Optional[int] = None,
    ) -> FileEntryWithOptionalEmbryo:
        entry: FileEntryWithOptionalEmbryo = {
            "name": str(name),
            "isDir": bool(is_dir),
            "path": str(path),
            "tags": [str(tag) for tag in (tags or [])],
        }
        if is_embryo:
            entry["isEmbryo"] = True
        if is_dir and folder_size_bytes is not None:
            entry["folderSizeBytes"] = int(folder_size_bytes)
        return entry

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
        if not target.is_dir():
            return None
        if not self.is_project(str(target)):
            return None
        return self._resolve_effective_project_color(target)

    def get_default_project_color(self) -> Optional[str]:
        return self._root_default_project_color

    def get_effective_project_color(self, path: str) -> Optional[str]:
        target = self._resolve_path(path)
        return self._resolve_project_color(
            target,
            require_project=False,
            project_only=True,
            stop_at_project_root=False,
        )

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

    def create_project(self, path: str) -> bool:
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
        try:
            source.rename(target)
        except Exception:
            return None
        return str(target)

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
        result: Dict[str, Any] = {"ok": True, "deleted": [], "errors": []}
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
            try:
                if source.is_dir():
                    shutil.rmtree(source)
                else:
                    source.unlink()
                result["deleted"].append(key)
            except Exception:
                result["errors"].append({"source": key, "reason": "delete_failed"})
        result["ok"] = len(result["errors"]) == 0
        return result

    def move_entry(self, source: str, target_dir: str) -> bool:
        try:
            src = self._resolve_path(source)
        except Exception:
            return False
        dst_dir = self._resolve_dir(target_dir)
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
        try:
            shutil.move(str(src), str(destination))
            rules = self._resolve_sort_rules_for_target(destination.parent)
            self._sort_runtime.apply_file(destination, rules, event="move")
            return True
        except Exception:
            return False

    def move_entries(self, sources: List[str], target_dir: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": True,
            "moved": [],
            "skipped": [],
            "errors": [],
        }
        dst_dir = self._resolve_path(target_dir)
        if not dst_dir.is_dir():
            result["ok"] = False
            result["errors"].append({"source": "", "reason": "target_not_directory", "target": str(dst_dir)})
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
            try:
                shutil.move(str(src), str(destination))
                result["moved"].append({"source": src_key, "destination": str(destination)})
                rules = self._resolve_sort_rules_for_target(destination.parent)
                sorted_result = self._sort_runtime.apply_file(destination, rules, event="move")
                if sorted_result.get("ok") == "1" and sorted_result.get("reason") == "moved":
                    result.setdefault("sorted", []).append(
                        {
                            "source": str(sorted_result.get("source") or ""),
                            "destination": str(sorted_result.get("destination") or ""),
                        }
                    )
            except Exception:
                result["errors"].append({"source": src_key, "reason": "move_failed"})

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
        if os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}:
            print(f"[scope_api] open_markdown: {target}")
            print(f"[scope_api] opener: {opener}")
        result = subprocess.run(
            [sys.executable, str(opener), str(target)], check=False
        )
        if os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}:
            print(f"[scope_api] returncode: {result.returncode}")
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
