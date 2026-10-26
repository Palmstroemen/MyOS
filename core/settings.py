"""The settings of MyOS's programs in one file (Scope/Designdocument Setup.md).

Scope writes them on its back; SunTree reads them each time it appears. Every setting has a
kind, a default and its allowed values in one place; anything else - a value out of range, of
the wrong kind, a key unknown - falls back to the default, as the file can be edited by hand.
"""

import configparser
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# "Group/name": (kind, default, allowed: (low, high) for numbers, a set for text, None)
SETTINGS: Dict[str, Tuple[type, Any, Any]] = {
    "General/darkTheme": (bool, True, None),
    "General/language": (str, "de", {"de", "en"}),
    # Scope's two rows (the projects, the MyOS folders); views of their own are to come.
    "Scope/projectsRow": (bool, True, None),
    "Scope/templatesRow": (bool, True, None),
    # SunTree's crown (SunTree/Designdocument Krone.md, 5); line and radius as shares of R.
    "SunTree/lineT": (float, 0.7, (0.5, 0.85)),
    "SunTree/inner": (float, 0.2, (0.1, 0.35)),
    "SunTree/enter": (float, 0.75, (0.6, 0.95)),
    "SunTree/leave": (float, 0.25, (0.05, 0.45)),
    "SunTree/lens": (float, 2.2, (0.0, 5.0)),
    "SunTree/softness": (float, 10.0, (2.0, 30.0)),
    "SunTree/edge": (float, 0.08, (0.02, 0.2)),
}


def settings_path() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "MyOS" / "MyOS.conf"


def _checked(key: str, value: Any) -> Optional[Any]:
    """value as the setting's kind, or None when it is not one of its allowed values."""
    if key not in SETTINGS:
        return None
    kind, _default, allowed = SETTINGS[key]
    try:
        if kind is bool:
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered not in {"true", "false"}:
                    return None
                value = lowered == "true"
            elif not isinstance(value, bool):
                return None
        elif kind is float:
            if isinstance(value, bool):
                return None
            value = float(value)
            if not (allowed[0] <= value <= allowed[1]):
                return None
        else:
            value = str(value)
            if allowed is not None and value not in allowed:
                return None
    except (TypeError, ValueError):
        return None
    return value


class Settings:
    """Read on creation; set() writes the file at once (another program may read it next)."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else settings_path()
        self._parser = configparser.ConfigParser(interpolation=None)
        self._parser.optionxform = str  # keep "lineT", not "linet"
        try:
            self._parser.read(self.path, encoding="utf-8")
        except (configparser.Error, OSError):
            self._parser = configparser.ConfigParser(interpolation=None)
            self._parser.optionxform = str

    def default(self, key: str) -> Any:
        return SETTINGS[key][1]

    def limits(self, key: str) -> Any:
        return SETTINGS[key][2]

    def get(self, key: str) -> Any:
        group, _, name = key.partition("/")
        raw = self._parser.get(group, name, fallback=None)
        value = _checked(key, raw) if raw is not None else None
        return self.default(key) if value is None else value

    def group(self, group: str) -> Dict[str, Any]:
        return {key.partition("/")[2]: self.get(key) for key in SETTINGS if key.startswith(group + "/")}

    def set(self, key: str, value: Any) -> bool:
        value = _checked(key, value)
        if value is None:
            return False
        group, _, name = key.partition("/")
        if not self._parser.has_section(group):
            self._parser.add_section(group)
        self._parser.set(group, name, str(value).lower() if isinstance(value, bool) else str(value))
        self._write()
        return True

    def reset(self, key: str) -> None:
        group, _, name = key.partition("/")
        if self._parser.has_option(group, name):
            self._parser.remove_option(group, name)
            self._write()

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".conf.tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            self._parser.write(handle)
        tmp.replace(self.path)  # whole or not at all: SunTree may read it any moment
