from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.desk import DeskConfig


@dataclass(frozen=True)
class BackendStepResult:
    ok: bool
    message: str = ""


class DesktopBackend:
    name = "none"

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="theme noop")

    def apply_wallpaper(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="wallpaper noop")

    def apply_dock(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="dock noop")

    def apply_recent_policy(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="recent-policy noop")

    def rollback(
        self,
        config: DeskConfig,
        *,
        applied_steps: list[str],
        dry_run: bool = True,
    ) -> BackendStepResult:
        return BackendStepResult(ok=True, message="rollback noop")


class NoopDesktopBackend(DesktopBackend):
    name = "none"

    def _msg(self, feature: str, config: DeskConfig) -> str:
        return f"{feature} ignored (backend=none source={config.source_path})"

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message=self._msg("theme", config))

    def apply_wallpaper(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message=self._msg("wallpaper", config))

    def apply_dock(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message=self._msg("dock", config))

    def apply_recent_policy(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message=self._msg("recent-policy", config))

    def rollback(
        self,
        config: DeskConfig,
        *,
        applied_steps: list[str],
        dry_run: bool = True,
    ) -> BackendStepResult:
        return BackendStepResult(ok=True, message=self._msg("rollback", config))


def ensure_non_empty(value: Optional[str], fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback
