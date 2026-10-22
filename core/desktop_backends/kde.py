from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Optional

from core.desk import DeskConfig, env_flag_is_true
from core.desktop_backends.base import BackendStepResult, DesktopState
from core.desktop_backends.command import CommandDesktopBackend, plain_path


class KdeDesktopBackend(CommandDesktopBackend):
    """
    KDE adapter for Desk runtime operations.

    Commands are capability-gated by environment flags so the backend can be
    enabled safely in incremental rollout.
    """

    name = "kde"
    timeout_env = "MYOS_DESK_KDE_TIMEOUT_S"

    def __init__(self) -> None:
        super().__init__()
        self.enable_theme = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_THEME_ENABLE", "1"))
        self.enable_wallpaper = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_WALLPAPER_ENABLE", "1"))
        self.enable_recent_policy = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_RECENT_ENABLE", "0"))

    def capture(self) -> Optional[DesktopState]:
        """Look-and-feel (else color scheme) and wallpaper from the KDE config files."""
        config_dir = Path.home() / ".config"
        parser = configparser.ConfigParser(interpolation=None, strict=False)
        parser.optionxform = str
        try:
            loaded = parser.read(
                [str(config_dir / name) for name in ("kdeglobals", "plasmarc", "plasma-org.kde.plasma.desktop-appletsrc")],
                encoding="utf-8",
            )
        except (configparser.Error, OSError, UnicodeDecodeError):
            return None
        if not loaded:
            return None
        theme = parser.get("KDE", "LookAndFeelPackage", fallback="") or parser.get("General", "ColorScheme", fallback="")
        image = parser.get("Containments][1][Wallpaper][org.kde.image][General", "Image", fallback="")
        return DesktopState(theme=theme.strip(), wallpaper=plain_path(image))

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        preset, skipped = self._checked_theme(config)
        if skipped is not None:
            return skipped
        if not self.enable_theme:
            return BackendStepResult(ok=True, message="theme skipped (capability disabled)")
        return self._run_command(["lookandfeeltool", "-a", preset], dry_run=dry_run, label="theme")

    def apply_wallpaper(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        wallpaper, error = self._resolve_wallpaper_path(config)
        if error:
            return BackendStepResult(ok=False, message=error)
        if not wallpaper:
            return BackendStepResult(ok=True, message="wallpaper skipped (no path/preset)")
        if not self.enable_wallpaper:
            return BackendStepResult(ok=True, message="wallpaper skipped (capability disabled)")
        return self._run_command(["plasma-apply-wallpaperimage", wallpaper], dry_run=dry_run, label="wallpaper")

    def apply_dock(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        if config.taskbar is None:
            return BackendStepResult(ok=True, message="taskbar skipped (none set)")
        # Plasma keeps its launchers in plasma-org.kde.plasma.desktop-appletsrc and takes
        # changes only through its scripting API; not built yet (no KDE to try it on).
        return BackendStepResult(ok=True, message="taskbar skipped (not supported on kde yet)")

    def apply_recent_policy(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        policy = str(config.recent_policy or "").strip()
        if not policy:
            return BackendStepResult(ok=True, message="recent policy skipped (none)")
        if not self.enable_recent_policy:
            return BackendStepResult(ok=True, message="recent policy skipped (capability disabled)")
        return BackendStepResult(ok=True, message=f"recent policy hook acknowledged ({policy})")

    def rollback(
        self,
        config: DeskConfig,
        *,
        applied_steps: list[str],
        dry_run: bool = True,
    ) -> BackendStepResult:
        if not applied_steps:
            return BackendStepResult(ok=True, message="rollback skipped (no applied steps)")
        return BackendStepResult(ok=True, message=f"rollback noop ({','.join(applied_steps)})")

