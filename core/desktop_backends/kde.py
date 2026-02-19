from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from core.desk import DeskConfig, env_flag_is_true
from core.desktop_backends.base import BackendStepResult, DesktopBackend


class KdeDesktopBackend(DesktopBackend):
    """
    KDE adapter for Desk runtime operations.

    Commands are capability-gated by environment flags so the backend can be
    enabled safely in incremental rollout.
    """

    name = "kde"

    def __init__(self) -> None:
        self.enable_theme = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_THEME_ENABLE", "1"))
        self.enable_wallpaper = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_WALLPAPER_ENABLE", "1"))
        self.enable_dock = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_DOCK_ENABLE", "0"))
        self.enable_recent_policy = env_flag_is_true(os.environ.get("MYOS_DESK_KDE_RECENT_ENABLE", "0"))
        self.command_timeout_s = self._read_timeout_seconds()

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        preset = str(config.theme_preset or "").strip()
        if not preset:
            return BackendStepResult(ok=True, message="theme skipped (no preset)")
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
        preset = str(config.dock_preset or "").strip()
        if not preset:
            return BackendStepResult(ok=True, message="dock skipped (no preset)")
        if not self.enable_dock:
            return BackendStepResult(ok=True, message="dock skipped (capability disabled)")
        return BackendStepResult(ok=True, message=f"dock hook acknowledged ({preset})")

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

    def _resolve_wallpaper_path(self, config: DeskConfig) -> tuple[str, str]:
        base_dir = config.source_path.parent.resolve()

        def _validate(resolved: Path) -> tuple[str, str]:
            if not resolved.exists() or not resolved.is_file():
                return "", "wallpaper failed (invalid path)"
            return str(resolved), ""

        explicit = str(config.wallpaper_path or "").strip()
        if explicit:
            try:
                resolved_explicit = Path(explicit).expanduser().resolve()
            except Exception:
                return "", "wallpaper failed (invalid path)"
            # Security: explicit wallpaper paths are treated as trusted user
            # intent and may point outside profile directories.
            return _validate(resolved_explicit)

        preset = str(config.wallpaper_preset or "").strip()
        if not preset:
            return "", ""

        # Treat relative presets as paths relative to the desk file directory.
        candidate = Path(preset).expanduser()
        if candidate.is_absolute():
            try:
                resolved_abs = candidate.resolve()
            except Exception:
                return "", "wallpaper failed (invalid path)"
            return _validate(resolved_abs)

        try:
            resolved_rel = (base_dir / candidate).resolve()
        except Exception:
            return "", "wallpaper failed (invalid path)"
        # Security: keep relative wallpaper presets within profile directory.
        try:
            resolved_rel.relative_to(base_dir)
        except ValueError:
            return "", "wallpaper failed (preset escapes profile directory)"
        return _validate(resolved_rel)

    def _read_timeout_seconds(self) -> int:
        raw = str(os.environ.get("MYOS_DESK_KDE_TIMEOUT_S", "15")).strip()
        try:
            timeout = int(raw or "15")
        except Exception:
            timeout = 15
        # Security: clamp timeout to a sane range to prevent hangs/abuse.
        return max(1, min(timeout, 120))

    def _run_command(self, argv: Sequence[str], *, dry_run: bool, label: str) -> BackendStepResult:
        binary = str(argv[0]).strip()
        if not shutil.which(binary):
            return BackendStepResult(ok=False, message=f"{label} failed (missing binary: {binary})")
        if dry_run:
            rendered = " ".join(shlex.quote(str(part)) for part in argv)
            return BackendStepResult(ok=True, message=f"{label} dry-run: {rendered}")
        try:
            proc = subprocess.run(
                [str(part) for part in argv],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.command_timeout_s,
            )
        except subprocess.TimeoutExpired:
            # Security: explicit timeout handling prevents backend command hangs.
            return BackendStepResult(ok=False, message=f"{label} failed (timeout)")
        except OSError as exc:
            return BackendStepResult(ok=False, message=f"{label} failed ({exc})")
        if proc.returncode != 0:
            stderr = (proc.stderr or proc.stdout or "").strip()
            return BackendStepResult(ok=False, message=f"{label} failed ({proc.returncode}): {stderr}")
        return BackendStepResult(ok=True, message=f"{label} applied")
