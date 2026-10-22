"""
gnome.py - desktop backend for the GNOME family (GNOME, Cinnamon) via gsettings.

Both keep wallpaper and theme in gsettings, under their own schemas. "Theme" is the
application (GTK) theme; the panel theme (taskbar, menus) is Cinnamon's "Desktop" theme,
plain GNOME has none without extensions. Values are passed as quoted GVariant strings in
an argv list.

Taskbar programs: GNOME keeps them in gsettings (favorite-apps). Cinnamon keeps them in
the settings file of its grouped window list applet (pinned-apps in
~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/<instance>.json). The applet
does not react to the file by itself, so after writing it MyOS asks Cinnamon over D-Bus
to reload the file (updateSetting) and the applet to reload its pinned programs
(activateCallback "updateFavorites", Cinnamon 6.0).
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Optional, Tuple

from core.desk import DeskConfig
from core.desktop_backends.base import BackendStepResult, DesktopState
from core.desktop_backends.command import CommandDesktopBackend, is_safe_app_id, plain_path

# flavor -> (wallpaper schema, wallpaper keys, theme schema, theme key)
_SCHEMAS = {
    "cinnamon": ("org.cinnamon.desktop.background", ("picture-uri",), "org.cinnamon.desktop.interface", "gtk-theme"),
    # GNOME 42+ keeps a second wallpaper for the dark style; set it when it exists.
    "gnome": ("org.gnome.desktop.background", ("picture-uri", "picture-uri-dark"), "org.gnome.desktop.interface", "gtk-theme"),
}
# flavor -> (schema, key) of the panel theme
_PANEL_SCHEMAS = {"cinnamon": ("org.cinnamon.theme", "name")}
# flavor -> (schema, key) of the taskbar programs kept in gsettings
_FAVORITE_SCHEMAS = {"gnome": ("org.gnome.shell", "favorite-apps")}
_WINDOW_LIST = "grouped-window-list@cinnamon.org"
_INSTANCE_RE = re.compile(r"^[0-9]{1,9}$")


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


def _parse_gvariant_strings(output: Optional[str]) -> Optional[Tuple[str, ...]]:
    """The strings of a gsettings list answer ("['a', 'b']", "@as []"), None for anything else."""
    text = str(output or "").strip()
    if text.startswith("@as "):
        text = text[4:].strip()
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return None
    return tuple(value)


def _gvariant_strings(values: Tuple[str, ...]) -> str:
    return "[" + ", ".join(_gvariant_string(value) for value in values) + "]" if values else "@as []"


def _safe_apps(values) -> Optional[Tuple[str, ...]]:
    if not isinstance(values, list):
        return None
    return tuple(app for app in values if isinstance(app, str) and is_safe_app_id(app))


class GnomeFamilyDesktopBackend(CommandDesktopBackend):
    def __init__(self, flavor: str) -> None:
        super().__init__()
        self.name = flavor
        self._wallpaper_schema, self._wallpaper_keys, self._theme_schema, self._theme_key = _SCHEMAS[flavor]
        self._panel = _PANEL_SCHEMAS.get(flavor)
        self._favorites = _FAVORITE_SCHEMAS.get(flavor)

    def _get(self, schema: str, key: str) -> Optional[str]:
        output = self._read_output(["gsettings", "get", schema, key])
        return None if output is None else _parse_gvariant_string(output)

    def capture(self) -> Optional[DesktopState]:
        theme = self._get(self._theme_schema, self._theme_key)
        wallpaper = self._get(self._wallpaper_schema, self._wallpaper_keys[0])
        panel = self._get(*self._panel) if self._panel else None
        taskbar = self._read_taskbar()
        if theme is None and wallpaper is None and panel is None and taskbar is None:
            return None
        return DesktopState(theme=theme or "", wallpaper=plain_path(wallpaper or ""), panel_theme=panel or "",
                            taskbar=taskbar)

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

    def apply_dock(self, config: DeskConfig, *, dry_run: bool = True) -> BackendStepResult:
        apps = config.taskbar
        if apps is None:
            return BackendStepResult(ok=True, message="taskbar skipped (none set)")
        if not all(is_safe_app_id(app) for app in apps):
            return BackendStepResult(ok=False, message="taskbar failed (invalid program name)")
        if self._favorites is not None:
            argv = ["gsettings", "set", *self._favorites, _gvariant_strings(tuple(apps))]
            return self._run_command(argv, dry_run=dry_run, label="taskbar")
        found = self._window_list_settings()
        if found is None:
            return BackendStepResult(ok=True, message=f"taskbar skipped (no grouped window list on {self.name})")
        return self._write_pinned_apps(*found, tuple(apps), dry_run=dry_run)

    def _read_taskbar(self) -> Optional[Tuple[str, ...]]:
        if self._favorites is not None:
            output = self._read_output(["gsettings", "get", *self._favorites])
            return None if output is None else _safe_apps(list(_parse_gvariant_strings(output) or []))
        found = self._window_list_settings()
        if found is None:
            return None
        try:
            entry = json.loads(found[0].read_text(encoding="utf-8")).get("pinned-apps")
        except (OSError, ValueError, AttributeError):
            return None
        return _safe_apps(entry.get("value")) if isinstance(entry, dict) else None

    def _window_list_settings(self) -> Optional[Tuple[Path, str]]:
        """(settings file, instance id) of Cinnamon's first grouped window list."""
        if self.name != "cinnamon":
            return None
        applets = _parse_gvariant_strings(self._read_output(["gsettings", "get", "org.cinnamon", "enabled-applets"]))
        for entry in applets or ():
            parts = entry.split(":")  # panel1:left:2:grouped-window-list@cinnamon.org:79
            # Security: the instance id becomes a file name; digits only.
            if len(parts) == 5 and parts[3] == _WINDOW_LIST and _INSTANCE_RE.match(parts[4]):
                config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
                return Path(config_home) / "cinnamon" / "spices" / _WINDOW_LIST / f"{parts[4]}.json", parts[4]
        return None

    def _write_pinned_apps(self, settings: Path, instance: str, apps: Tuple[str, ...], *, dry_run: bool) -> BackendStepResult:
        # Security: the file belongs to Cinnamon; never write through a symlink.
        if settings.is_symlink():
            return BackendStepResult(ok=False, message="taskbar failed (settings file is a symlink)")
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return BackendStepResult(ok=False, message=f"taskbar failed ({exc})")
        entry = data.get("pinned-apps") if isinstance(data, dict) else None
        if not isinstance(entry, dict):
            return BackendStepResult(ok=False, message="taskbar failed (no pinned-apps in the window list settings)")
        if dry_run:
            return BackendStepResult(ok=True, message=f"taskbar dry-run: {settings} pinned-apps = {list(apps)}")
        entry["value"] = list(apps)  # every other setting of the applet stays as it is
        draft = settings.with_name("." + settings.name + ".myos-draft")
        try:
            draft.write_text(json.dumps(data, indent=4), encoding="utf-8")
            os.replace(draft, settings)
        except OSError as exc:
            return BackendStepResult(ok=False, message=f"taskbar failed ({exc})")
        dbus = ["gdbus", "call", "--session", "--dest", "org.Cinnamon", "--object-path", "/org/Cinnamon", "--method"]
        reload_file = self._run_command(
            [*dbus, "org.Cinnamon.updateSetting", _gvariant_string(_WINDOW_LIST), _gvariant_string(instance),
             _gvariant_string("pinned-apps"), _gvariant_string(json.dumps(list(apps)))],
            dry_run=False, label="taskbar reload",
        )
        reload_list = self._run_command(
            [*dbus, "org.Cinnamon.activateCallback", _gvariant_string("updateFavorites"),
             _gvariant_string(_WINDOW_LIST), _gvariant_string(instance)],
            dry_run=False, label="taskbar reload",
        ) if reload_file.ok else reload_file
        if not reload_list.ok:
            # The file is written; Cinnamon shows it at its next start at the latest.
            return BackendStepResult(ok=True, message=f"taskbar saved, not shown yet ({reload_list.message})")
        return BackendStepResult(ok=True, message="taskbar applied")
