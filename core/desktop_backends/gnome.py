"""
gnome.py - desktop backend for the GNOME family (GNOME, Cinnamon) via gsettings.

Both keep wallpaper and theme in gsettings, under their own schemas. "Theme" is the
application (GTK) theme; the panel theme (taskbar, menus) is Cinnamon's "Desktop" theme,
plain GNOME has none without extensions. Values are passed as quoted GVariant strings in
an argv list.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Optional

from core.desk import DeskConfig
from core.desktop_backends.base import BackendStepResult, DesktopState
from core.desktop_backends.command import CommandDesktopBackend, plain_path

# flavor -> (wallpaper schema, wallpaper keys, theme schema, theme key)
_SCHEMAS = {
    "cinnamon": ("org.cinnamon.desktop.background", ("picture-uri",), "org.cinnamon.desktop.interface", "gtk-theme"),
    # GNOME 42+ keeps a second wallpaper for the dark style; set it when it exists.
    "gnome": ("org.gnome.desktop.background", ("picture-uri", "picture-uri-dark"), "org.gnome.desktop.interface", "gtk-theme"),
}
# flavor -> (schema, key) of the panel theme
_PANEL_SCHEMAS = {"cinnamon": ("org.cinnamon.theme", "name")}


def _gvariant_string(value: str) -> str:
    """value as a GVariant string literal ('...'), as gsettings set expects it."""
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _parse_gvariant_string(output: Optional[str]) -> str:
    """The string of a gsettings get answer ("'Mint-Y'\\n"), "" for anything else."""
    text = str(output or "").strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        try:
            value = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return ""
        return value if isinstance(value, str) else ""
    return ""


class GnomeFamilyDesktopBackend(CommandDesktopBackend):
    def __init__(self, flavor: str) -> None:
        super().__init__()
        self.name = flavor
        self._wallpaper_schema, self._wallpaper_keys, self._theme_schema, self._theme_key = _SCHEMAS[flavor]
        self._panel = _PANEL_SCHEMAS.get(flavor)

    def _get(self, schema: str, key: str) -> Optional[str]:
        output = self._read_output(["gsettings", "get", schema, key])
        return None if output is None else _parse_gvariant_string(output)

    def capture(self) -> Optional[DesktopState]:
        theme = self._get(self._theme_schema, self._theme_key)
        wallpaper = self._get(self._wallpaper_schema, self._wallpaper_keys[0])
        panel = self._get(*self._panel) if self._panel else None
        if theme is None and wallpaper is None and panel is None:
            return None
        return DesktopState(theme=theme or "", wallpaper=plain_path(wallpaper or ""), panel_theme=panel or "")

    def apply_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        preset, skipped = self._checked_theme(config)
        if skipped is not None:
            return skipped
        argv = ["gsettings", "set", self._theme_schema, self._theme_key, _gvariant_string(preset)]
        return self._run_command(argv, dry_run=dry_run, label="theme")

    def apply_panel_theme(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        name, skipped = self._checked_theme(config, config.panel_theme or "", label="panel theme")
        if skipped is not None:
            return skipped
        if self._panel is None:
            return BackendStepResult(ok=True, message=f"panel theme skipped (not supported on {self.name})")
        argv = ["gsettings", "set", self._panel[0], self._panel[1], _gvariant_string(name)]
        return self._run_command(argv, dry_run=dry_run, label="panel theme")

    def apply_wallpaper(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        wallpaper, error = self._resolve_wallpaper_path(config)
        if error:
            return BackendStepResult(ok=False, message=error)
        if not wallpaper:
            return BackendStepResult(ok=True, message="wallpaper skipped (no path/preset)")
        uri = _gvariant_string(Path(wallpaper).as_uri())
        result = BackendStepResult(ok=True, message="wallpaper skipped")
        for index, key in enumerate(self._wallpaper_keys):
            if index > 0 and dry_run is False and self._get(self._wallpaper_schema, key) is None:
                continue  # optional key this desktop does not have
            result = self._run_command(["gsettings", "set", self._wallpaper_schema, key, uri], dry_run=dry_run, label="wallpaper")
            if not result.ok:
                return result
        return result
