from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.desk_runtime import DeskRuntime
from core.desktop_backends.base import DesktopState
from core.project import find_config_in_parents, find_next_parent_config

_SAFE_CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_MAX_CONFIG_NAME_LEN = 120


def desk_home() -> Path:
    """Where MyOS keeps the user's own desktop (Desk.md) and what it set last."""
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "MyOS"


_DESK_KEYS = (("ThemePreset", "theme"), ("PanelTheme", "panel_theme"), ("WallpaperPath", "wallpaper"))


def write_desk_values(desk_file: Path, state: DesktopState) -> None:
    """
    Put themes and wallpaper of state into desk_file ("# Desk"), keeping every other
    line (ProjectIcon, comments, ...); creates the file. Written atomically.
    """
    # Security: never write through a symlink (the reader ignores symlinked desks).
    if desk_file.is_symlink():
        raise OSError(f"refusing to write symlinked {desk_file}")
    lines = desk_file.read_text(encoding="utf-8").splitlines() if desk_file.exists() else []
    values = {key: getattr(state, field) for key, field in _DESK_KEYS if getattr(state, field)}
    start = next((i for i, line in enumerate(lines) if line.strip().lstrip("#").strip().lower() == "desk"
                  and line.strip().startswith("#")), None)
    if start is None:
        lines = (lines + [""] if lines and lines[-1].strip() else lines) + ["# Desk"]
        start = len(lines) - 1
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith("#")), len(lines))
    for key, value in values.items():
        hit = next((i for i in range(start + 1, end) if lines[i].split(":", 1)[0].strip().lower() == key.lower()), None)
        if hit is not None:
            lines[hit] = f"{key}: {value}"
        else:
            lines.insert(start + 1, f"{key}: {value}")
            end += 1
    desk_file.parent.mkdir(parents=True, exist_ok=True)
    draft = desk_file.with_name("." + desk_file.name + ".draft")
    draft.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(draft, desk_file)


def _project_roots(path: Path) -> tuple[Optional[Path], Optional[Path]]:
    """(nearest, top) project containing path; (None, None) outside the projects tree."""
    nearest = top = None
    for candidate in [path, *path.parents]:
        if (candidate / ".MyOS" / "Project.md").exists():
            nearest = nearest or candidate
            top = candidate
    return nearest, top


class DeskService:
    """
    Core-facing Desk API boundary used by app integrations.

    This service keeps runtime handling and error normalization in one place so
    callers (Scope/PostFix/CLI) use the same behavior.

    The desktop follows the projects ("Designdocument Desk.md", 12): inside the
    projects tree the nearest Desk.md applies, elsewhere the user's own desktop (the
    system default in desk_home()). What the user changes is saved, without asking,
    where it was changed. Scope and PostFix share what MyOS set last (desk-state.json),
    so neither takes the other's switch for a change by the user.
    """

    def __init__(self, runtime: Optional[DeskRuntime] = None) -> None:
        self._runtime = runtime or DeskRuntime()
        self._providers: Dict[str, Dict[str, Any]] = {
            "Desk.md": {
                "capture": self._capture_desk_payload,
                "render": self._render_desk_markdown,
                "seed": "# Desk\nInherit: dynamic\n",
            },
            "Sort.md": {
                "capture": self._capture_sort_payload,
                "render": self._render_sort_markdown,
                "seed": "# Sort\nRoot: /Pictures\nPattern: {{YYYY}}/{{MM}}/{{DD}}\nDateSource: exif_created,frontmatter_date,fs_mtime\nApplyOn: both\nMaterialization: on_use\nConflict: rename\nEnabled: true\n",
            }
        }
        self._last_result: Dict[str, Any] = {
            "ok": True,
            "applied": False,
            "reason": "not_started",
            "source": None,
            "steps": [],
        }

    def refresh_context(
        self,
        path: Union[str, Path],
        *,
        manual_desk: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        target = Path(path).expanduser().resolve()
        try:
            self._last_result = self._follow(target, manual_desk)
        except Exception:
            self._last_result = {
                "ok": False,
                "applied": False,
                "reason": "runtime_error",
                "source": None,
                "steps": [],
            }
        return dict(self._last_result)

    def _follow(self, target: Path, manual_desk: Optional[Union[str, Path]]) -> Dict[str, Any]:
        runtime = self._runtime
        context = target.parent if target.is_file() else target
        nearest, top = _project_roots(context)
        system_desk = desk_home() / "Desk.md"
        current = runtime.backend.capture() if runtime.settings.enabled and not runtime.settings.dry_run else None
        if current is None:  # no desktop to follow (no backend, disabled, dry run)
            return runtime.handle_context(target, manual_desk=manual_desk, boundary=top)

        shared = self._read_shared()
        changed = shared.get("applied") is not None and current != shared["applied"]
        if changed and shared.get("owner"):
            # The user changed the desktop since MyOS set it: keep it where it was changed.
            write_desk_values(Path(shared["owner"]), current)
        if not system_desk.exists():
            # Before MyOS changes anything: the user's own desktop, restored outside projects.
            write_desk_values(system_desk, current)

        # "Same profile as last time" only means "nothing to do" while the desktop is
        # still as MyOS set it; after a change the profile is applied again.
        last_applied = (None, None) if changed else (shared.get("source"), shared.get("hash"))
        runtime.active_source, runtime.active_hash = last_applied
        if top is None:  # outside the projects tree: the user's own desktop, no search
            manual_desk = manual_desk or system_desk
        result = runtime.handle_context(target, manual_desk=manual_desk, boundary=top, fallback=system_desk)
        owner = nearest / ".MyOS" / "Desk.md" if nearest is not None else system_desk
        self._write_shared(runtime.backend.capture() or current, owner, runtime.active_source, runtime.active_hash)
        return result

    def _read_shared(self) -> Dict[str, Any]:
        try:
            data = json.loads((desk_home() / "desk-state.json").read_text(encoding="utf-8"))
            applied = data.get("applied")
            data["applied"] = DesktopState(**applied) if isinstance(applied, dict) else None
            return data
        except (OSError, ValueError, TypeError):
            return {}

    def _write_shared(self, applied: DesktopState, owner: Path, source: Optional[str], profile_hash: Optional[str]) -> None:
        state_file = desk_home() / "desk-state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "applied": {"theme": applied.theme, "wallpaper": applied.wallpaper, "panel_theme": applied.panel_theme},
            "owner": str(owner),
            "source": source,
            "hash": profile_hash,
        }
        draft = state_file.with_name(".desk-state.json.draft")
        draft.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(draft, state_file)

    def get_active_profile(self) -> Dict[str, Optional[str]]:
        return self._runtime.get_active_profile()

    def get_last_result(self) -> Dict[str, Any]:
        return dict(self._last_result)

    def find_config(
        self,
        start_path: Union[str, Path],
        *,
        config_name: str = "Desk.md",
    ) -> Optional[Path]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._is_safe_config_name(config_name):
            return None
        if not self._has_provider(config_name):
            return None
        return find_config_in_parents(
            start_path,
            config_name,
            require_project_marker=True,
            honor_inherit_not=True,
        )

    def list_config_targets(
        self,
        start_path: Union[str, Path],
        *,
        config_name: str = "Desk.md",
        global_root: Optional[Union[str, Path]] = None,
        include_template_target: bool = False,
        template_root: Optional[Union[str, Path]] = None,
    ) -> List[Dict[str, str]]:
        # Security: reject traversal/path-injection in config filenames.
        if not self._is_safe_config_name(config_name):
            return [
                {
                    "id": "discard",
                    "label": "Nicht speichern",
                    "targetPath": "",
                    "configPath": "",
                    "exists": "0",
                }
            ]
        if not self._has_provider(config_name):
            return [
                {
                    "id": "discard",
                    "label": "Nicht speichern",
                    "targetPath": "",
                    "configPath": "",
                    "exists": "0",
                }
            ]
        target = Path(start_path).expanduser().resolve()
        if target.is_file():
            target = target.parent
        candidates: List[Dict[str, str]] = []
        current_project = self._resolve_project_dir(target)
        if current_project is not None:
            local_path = current_project / ".MyOS" / config_name
            candidates.append(
                {
                    "id": "current_project",
                    "label": "Aktuelles Projekt",
                    "targetPath": str(current_project),
                    "configPath": str(local_path),
                    "exists": "1" if local_path.exists() else "0",
                }
            )
            effective_from_current = find_config_in_parents(
                current_project,
                config_name,
                require_project_marker=True,
                honor_inherit_not=True,
            )
            parent_config = None
            # If effective resolution is blocked locally (inherit:not), do not suggest parent.
            if not (effective_from_current is None and local_path.exists()):
                parent_config = find_next_parent_config(
                    current_project,
                    config_name,
                    require_project_marker=True,
                    honor_inherit_not=True,
                )
            if parent_config is not None:
                parent_root = parent_config.parent.parent
                candidates.append(
                    {
                        "id": "nearest_parent_with_config",
                        "label": "Naechstes Parent-Projekt",
                        "targetPath": str(parent_root),
                        "configPath": str(parent_config),
                        "exists": "1",
                    }
                )
        if global_root:
            root = Path(global_root).expanduser().resolve()
            config_path = root / ".MyOS" / config_name
            candidates.append(
                {
                    "id": "global_root",
                    "label": "MyOS-Root",
                    "targetPath": str(root),
                    "configPath": str(config_path),
                    "exists": "1" if config_path.exists() else "0",
                }
            )
        if include_template_target and template_root:
            root = Path(template_root).expanduser().resolve()
            config_path = root / ".MyOS" / config_name
            candidates.append(
                {
                    "id": "template",
                    "label": "Template",
                    "targetPath": str(root),
                    "configPath": str(config_path),
                    "exists": "1" if config_path.exists() else "0",
                }
            )
        candidates.append(
            {
                "id": "discard",
                "label": "Nicht speichern",
                "targetPath": "",
                "configPath": "",
                "exists": "0",
            }
        )
        return candidates

    def capture_config_state(self, *, config_name: str = "Desk.md") -> Dict[str, Any]:
        if not self._has_provider(config_name):
            return {"ok": False, "reason": "unsupported_config"}
        payload = self._provider_capture(config_name)
        encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        return {
            "ok": True,
            "configName": config_name,
            "stateHash": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
            "state": payload,
        }

    def write_config_from_state(
        self,
        target_root: Union[str, Path],
        *,
        config_name: str = "Desk.md",
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        root = Path(target_root).expanduser().resolve()
        if not self._has_provider(config_name):
            return {"ok": False, "reason": "unsupported_config", "path": ""}
        if not root.exists() or not root.is_dir():
            return {"ok": False, "reason": "target_missing", "path": ""}
        if state is None:
            capture = self.capture_config_state(config_name=config_name)
            if not capture.get("ok"):
                return {"ok": False, "reason": "capture_failed", "path": ""}
            state = dict(capture.get("state") or {})
        config_path = root / ".MyOS" / config_name
        config_path.parent.mkdir(parents=True, exist_ok=True)
        content = self._provider_render(config_name, state)
        config_path.write_text(content, encoding="utf-8")
        return {"ok": True, "reason": "written", "path": str(config_path)}

    def ensure_config_file(
        self,
        target_root: Union[str, Path],
        *,
        config_name: str = "Desk.md",
    ) -> Dict[str, Any]:
        root = Path(target_root).expanduser().resolve()
        if not self._has_provider(config_name):
            return {"ok": False, "reason": "unsupported_config", "path": ""}
        if not root.exists() or not root.is_dir():
            return {"ok": False, "reason": "target_missing", "path": ""}
        config_path = root / ".MyOS" / config_name
        if config_path.exists():
            return {"ok": True, "reason": "exists", "path": str(config_path)}
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(self._provider_seed(config_name), encoding="utf-8")
        return {"ok": True, "reason": "created", "path": str(config_path)}

    def is_safe_config_name(self, value: str) -> bool:
        return self._is_safe_config_name(value)

    def supports_config(self, config_name: str) -> bool:
        return self._has_provider(config_name)

    def _capture_desk_payload(self) -> Dict[str, str]:
        state = self._runtime.backend.capture()
        return {"theme": state.theme, "panel_theme": state.panel_theme, "wallpaper": state.wallpaper} if state is not None else {}

    def _render_desk_markdown(self, state: Dict[str, Any]) -> str:
        theme = str(state.get("theme") or "").strip()
        panel_theme = str(state.get("panel_theme") or "").strip()
        wallpaper = str(state.get("wallpaper") or "").strip()
        lines = ["# Desk"]
        if theme:
            lines.append(f"ThemePreset: {theme}")
        if panel_theme:
            lines.append(f"PanelTheme: {panel_theme}")
        if wallpaper:
            lines.append(f"WallpaperPath: {wallpaper}")
        lines.append("Inherit: dynamic")
        return "\n".join(lines) + "\n"

    def _capture_sort_payload(self) -> Dict[str, Any]:
        return {"rules": []}

    def _render_sort_markdown(self, state: Dict[str, Any]) -> str:
        rules = state.get("rules")
        if not isinstance(rules, list) or not rules:
            return str(self._provider_seed("Sort.md"))
        lines: List[str] = []
        for item in rules:
            if not isinstance(item, dict):
                continue
            root = str(item.get("root") or "/Pictures").strip()
            pattern = str(item.get("pattern") or "{{YYYY}}/{{MM}}/{{DD}}").strip()
            date_source = str(item.get("dateSource") or "exif_created,frontmatter_date,fs_mtime").strip()
            apply_on = str(item.get("applyOn") or "both").strip()
            materialization = str(item.get("materialization") or "on_use").strip()
            conflict = str(item.get("conflict") or "rename").strip()
            enabled = str(item.get("enabled") or "true").strip().lower()
            lines.extend(
                [
                    "# Sort",
                    f"Root: {root}",
                    f"Pattern: {pattern}",
                    f"DateSource: {date_source}",
                    f"ApplyOn: {apply_on}",
                    f"Materialization: {materialization}",
                    f"Conflict: {conflict}",
                    f"Enabled: {enabled}",
                    "",
                ]
            )
        if not lines:
            return str(self._provider_seed("Sort.md"))
        return "\n".join(lines).strip() + "\n"

    def _is_safe_config_name(self, value: str) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        # Security: bound config filename length to avoid pathological paths.
        if len(text) > _MAX_CONFIG_NAME_LEN:
            return False
        if "/" in text or "\\" in text:
            return False
        if text in {".", ".."} or ".." in text:
            return False
        return bool(_SAFE_CONFIG_NAME_RE.match(text))

    def _resolve_project_dir(self, start_path: Path) -> Optional[Path]:
        for candidate in [start_path, *start_path.parents]:
            if (candidate / ".MyOS" / "Project.md").exists():
                return candidate
        return None

    def _has_provider(self, config_name: str) -> bool:
        return str(config_name or "").strip() in self._providers

    def _provider_capture(self, config_name: str) -> Dict[str, Any]:
        provider = self._providers[str(config_name)]
        return dict(provider["capture"]())

    def _provider_render(self, config_name: str, state: Dict[str, Any]) -> str:
        provider = self._providers[str(config_name)]
        return str(provider["render"](state))

    def _provider_seed(self, config_name: str) -> str:
        provider = self._providers[str(config_name)]
        return str(provider.get("seed") or "")
