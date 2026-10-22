from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from core.desk import DeskConfig


@dataclass(frozen=True)
class BackendStepResult:
    ok: bool
    message: str = ""


@dataclass(frozen=True)
class DesktopState:
    """What a Desk.md describes of the running desktop: themes, wallpaper path, taskbar."""

    theme: str = ""
    wallpaper: str = ""
    panel_theme: str = ""
    taskbar: Optional[Tuple[str, ...]] = None  # pinned programs; None: this desktop cannot tell


class DesktopBackend:
    name = "none"

    def capture(self) -> Optional[DesktopState]:
        """The desktop as it is now, None when this backend cannot read it."""
        return None

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="theme noop")

    def apply_panel_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        return BackendStepResult(ok=True, message="panel theme noop")

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
