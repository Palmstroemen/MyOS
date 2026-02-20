#!/usr/bin/env python3
"""
desk_runtime.py - Runtime desk profile activation pipeline.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from core.desk import DeskConfig, env_flag_is_true, resolve_active_desk
from core.desktop_backends import build_backend
from core.desktop_backends.base import DesktopBackend

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeskRuntimeSettings:
    enabled: bool
    dry_run: bool
    backend_name: str
    include_root_desk: bool
    prefer_filter_desk: bool
    fallback_profile: Optional[str]

    @classmethod
    def from_env(cls) -> "DeskRuntimeSettings":
        return cls(
            enabled=env_flag_is_true(os.environ.get("MYOS_DESK_ENABLE", "0")),
            dry_run=env_flag_is_true(os.environ.get("MYOS_DESK_DRY_RUN", "1")),
            backend_name=str(os.environ.get("MYOS_DESK_BACKEND", "none")).strip().lower() or "none",
            include_root_desk=env_flag_is_true(os.environ.get("MYOS_DESK_INCLUDE_ROOT", "0")),
            prefer_filter_desk=not env_flag_is_true(os.environ.get("MYOS_DESK_DISABLE_FILTER", "0")),
            fallback_profile=(str(os.environ.get("MYOS_DESK_FALLBACK", "")).strip() or None),
        )


class DeskRuntime:
    """
    Resolve and apply desk profiles for path-context transitions.
    """

    def __init__(
        self,
        settings: Optional[DeskRuntimeSettings] = None,
        backend: Optional[DesktopBackend] = None,
    ) -> None:
        self.settings = settings or DeskRuntimeSettings.from_env()
        self.backend = backend or build_backend(self.settings.backend_name)
        self.active_source: Optional[str] = None
        self.active_hash: Optional[str] = None
        self.last_result: Dict[str, Any] = {
            "ok": True,
            "applied": False,
            "reason": "not_started",
            "source": None,
            "steps": [],
        }

    def handle_context(
        self,
        path: Union[str, Path],
        *,
        manual_desk: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        # Security: reject malformed paths early so untrusted input cannot
        # crash context resolution.
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            self.last_result = {
                "ok": False,
                "applied": False,
                "reason": "invalid_path",
                "source": None,
                "steps": [],
            }
            return dict(self.last_result)
        if target.is_file():
            target = target.parent

        desk = resolve_active_desk(
            target,
            manual=manual_desk,
            fallback=self.settings.fallback_profile,
            include_root_desk=self.settings.include_root_desk,
            prefer_filter_desk=self.settings.prefer_filter_desk,
        )
        if desk is None:
            logger.debug("desk.handle_context no profile target=%s", target)
            self.last_result = {
                "ok": True,
                "applied": False,
                "reason": "no_profile",
                "source": None,
                "steps": [],
            }
            return dict(self.last_result)

        profile_hash = self._profile_hash(desk)
        profile_source = str(desk.source_path)
        if self.active_source == profile_source and self.active_hash == profile_hash:
            logger.debug("desk.handle_context unchanged source=%s", profile_source)
            self.last_result = {
                "ok": True,
                "applied": False,
                "reason": "unchanged",
                "source": profile_source,
                "steps": [],
            }
            return dict(self.last_result)

        if not self.settings.enabled:
            self.active_source = profile_source
            self.active_hash = profile_hash
            logger.info("desk.handle_context runtime disabled source=%s", profile_source)
            self.last_result = {
                "ok": True,
                "applied": False,
                "reason": "runtime_disabled",
                "source": profile_source,
                "steps": [],
            }
            return dict(self.last_result)

        steps = self._apply_profile(desk)
        ok = all(bool(step.get("ok")) for step in steps)
        if ok:
            self.active_source = profile_source
            self.active_hash = profile_hash
            reason = "applied" if not self.settings.dry_run else "dry_run"
            logger.info("desk.handle_context applied source=%s reason=%s", profile_source, reason)
        else:
            reason = "apply_failed"
            logger.warning("desk.handle_context apply failed source=%s", profile_source)
        self.last_result = {
            "ok": ok,
            "applied": ok,
            "reason": reason,
            "source": profile_source,
            "steps": steps,
        }
        return dict(self.last_result)

    def get_active_profile(self) -> Dict[str, Optional[str]]:
        return {
            "source": self.active_source,
            "hash": self.active_hash,
        }

    def _apply_profile(self, config: DeskConfig) -> list[Dict[str, Any]]:
        ordered_steps = [
            ("theme", self.backend.apply_theme),
            ("wallpaper", self.backend.apply_wallpaper),
            ("dock", self.backend.apply_dock),
            ("recent_policy", self.backend.apply_recent_policy),
        ]
        results: list[Dict[str, Any]] = []
        applied_steps: list[str] = []
        for step_name, step_fn in ordered_steps:
            try:
                step_result = step_fn(config, dry_run=self.settings.dry_run)
                step_ok = bool(step_result.ok)
                results.append({"name": step_name, "ok": step_ok, "message": str(step_result.message or "")})
                if step_ok:
                    applied_steps.append(step_name)
                    continue
                rollback_result = self._rollback_profile(config, applied_steps=applied_steps)
                results.append(rollback_result)
                break
            except Exception as exc:  # pragma: no cover - defensive boundary
                results.append({"name": step_name, "ok": False, "message": str(exc)})
                rollback_result = self._rollback_profile(config, applied_steps=applied_steps)
                results.append(rollback_result)
                break
        return results

    def _rollback_profile(self, config: DeskConfig, *, applied_steps: list[str]) -> Dict[str, Any]:
        try:
            rollback = self.backend.rollback(config, applied_steps=applied_steps, dry_run=self.settings.dry_run)
            return {"name": "rollback", "ok": bool(rollback.ok), "message": str(rollback.message or "")}
        except Exception as exc:  # pragma: no cover - defensive boundary
            return {"name": "rollback", "ok": False, "message": str(exc)}

    def _profile_hash(self, config: DeskConfig) -> str:
        payload = {
            "source": str(config.source_path),
            "theme_preset": config.theme_preset,
            "wallpaper_preset": config.wallpaper_preset,
            "wallpaper_path": config.wallpaper_path,
            "dock_preset": config.dock_preset,
            "recent_policy": config.recent_policy,
            "inherit": config.inherit,
            "raw": config.raw,
        }
        encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
