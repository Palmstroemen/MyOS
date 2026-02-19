from __future__ import annotations

import configparser
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from core.desk_runtime import DeskRuntime
from core.project import find_config_in_parents, find_next_parent_config

_SAFE_CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\.md$")
_MAX_CONFIG_NAME_LEN = 120


class DeskService:
    """
    Core-facing Desk API boundary used by app integrations.

    This service keeps runtime handling and error normalization in one place so
    callers (Scope/PostFix/CLI) use the same behavior.
    """

    def __init__(self, runtime: Optional[DeskRuntime] = None) -> None:
        self._runtime = runtime or DeskRuntime()
        self._providers: Dict[str, Dict[str, Any]] = {
            "Desk.md": {
                "capture": self._capture_kde_payload,
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
            self._last_result = self._runtime.handle_context(target, manual_desk=manual_desk)
        except Exception:
            self._last_result = {
                "ok": False,
                "applied": False,
                "reason": "runtime_error",
                "source": None,
                "steps": [],
            }
        return dict(self._last_result)

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

    def _capture_kde_payload(self) -> Dict[str, str]:
        home = Path.home()
        kdeglobals = home / ".config" / "kdeglobals"
        plasmarc = home / ".config" / "plasmarc"
        appletsrc = home / ".config" / "plasma-org.kde.plasma.desktop-appletsrc"
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str
        loaded = parser.read([str(kdeglobals), str(plasmarc), str(appletsrc)], encoding="utf-8")
        payload: Dict[str, str] = {}
        payload["kde_sources"] = ",".join(loaded)
        payload["look_and_feel"] = parser.get("KDE", "LookAndFeelPackage", fallback="")
        payload["color_scheme"] = parser.get("General", "ColorScheme", fallback="")
        payload["font"] = parser.get("General", "font", fallback="")
        payload["wallpaper_plugin"] = parser.get(
            "Containments][1][Wallpaper][org.kde.image][General",
            "Image",
            fallback="",
        )
        return payload

    def _render_desk_markdown(self, state: Dict[str, Any]) -> str:
        look_and_feel = str(state.get("look_and_feel") or "").strip()
        color_scheme = str(state.get("color_scheme") or "").strip()
        wallpaper = str(state.get("wallpaper_plugin") or "").strip()
        lines = ["# Desk"]
        if look_and_feel:
            lines.append(f"ThemePreset: {look_and_feel}")
        elif color_scheme:
            lines.append(f"ThemePreset: {color_scheme}")
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
