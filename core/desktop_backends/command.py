"""
command.py - shared base of desktop backends that run commands (KDE tools, gsettings).

Commands are argv lists (never a shell); values from a project's Desk.md are checked
before they reach a command.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Sequence
from urllib.parse import unquote, urlparse

from core.desk import DeskConfig
from core.desktop_backends.base import BackendStepResult, DesktopBackend

# Theme names as desktops use them ("Mint-Y-Dark-Aqua", "Breeze Dark", "org.kde.breeze").
# Security: no leading "-" (would be read as an option), no quotes or control characters.
_THEME_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+()-]{0,99}$")


def is_safe_theme_name(name: str) -> bool:
    return bool(_THEME_NAME_RE.match(str(name or "")))


def plain_path(value: str) -> str:
    """A wallpaper as a plain path: KDE and GNOME store file:// URIs."""
    text = str(value or "").strip()
    if text.startswith("file://"):
        return unquote(urlparse(text).path)
    return text


class CommandDesktopBackend(DesktopBackend):
    timeout_env = "MYOS_DESK_TIMEOUT_S"

    def __init__(self) -> None:
        self.command_timeout_s = self._read_timeout_seconds()

    def _read_timeout_seconds(self) -> int:
        raw = str(os.environ.get(self.timeout_env, "15")).strip()
        try:
            timeout = int(raw or "15")
        except Exception:
            timeout = 15
        # Security: clamp timeout to a sane range to prevent hangs/abuse.
        return max(1, min(timeout, 120))

    def _checked_theme(self, config: DeskConfig, value: Optional[str] = None,
                       label: str = "theme") -> tuple[str, Optional[BackendStepResult]]:
        """(name, None) for a usable theme name, ("", result) to return instead."""
        preset = str(config.theme_preset if value is None else value or "").strip()
        if not preset:
            return "", BackendStepResult(ok=True, message=f"{label} skipped (no preset)")
        if not is_safe_theme_name(preset):
            return "", BackendStepResult(ok=False, message=f"{label} failed (invalid name)")
        return preset, None

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

    def _read_output(self, argv: Sequence[str]) -> Optional[str]:
        """stdout of a reading command, None when it is missing or fails."""
        if not shutil.which(str(argv[0])):
            return None
        try:
            proc = subprocess.run(
                [str(part) for part in argv],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.command_timeout_s,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
        return proc.stdout if proc.returncode == 0 else None
