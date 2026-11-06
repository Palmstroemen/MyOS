"""The colour schemes of MyOS's programs (Scope/Designdocument Setup.md, step 2).

A scheme is a file in core/schemes, one colour per name; the programs say where each name is used.
Colours one sets oneself are kept beside the settings, per scheme (~/.config/MyOS/schemes), and lie
over the shipped ones, which stay as they are. That file can be edited by hand: what is no colour
of the scheme in it is ignored.
"""

import json
import re
from pathlib import Path
from typing import Dict

from core.settings import settings_path

SCHEMES_DIR = Path(__file__).with_name("schemes")
SCHEME_NAMES = ("dark", "light")
_COLOR = re.compile(r"#([0-9a-fA-F]{2})?[0-9a-fA-F]{6}")


def shipped_scheme(name: str) -> Dict[str, str]:
    return json.loads((SCHEMES_DIR / f"{name}.json").read_text(encoding="utf-8"))


def own_colors_path(name: str) -> Path:
    return settings_path().parent / "schemes" / f"{name}.json"


def _own_colors(name: str) -> Dict[str, str]:
    try:
        own = json.loads(own_colors_path(name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(own, dict):
        return {}
    shipped = shipped_scheme(name)
    return {color: value for color, value in own.items()
            if color in shipped and isinstance(value, str) and _COLOR.fullmatch(value)}


def load_scheme(name: str) -> Dict[str, str]:
    return {**shipped_scheme(name), **_own_colors(name)}


def set_scheme_color(name: str, color: str, value: str) -> bool:
    if name not in SCHEME_NAMES or color not in shipped_scheme(name) or not _COLOR.fullmatch(value):
        return False
    _write_own_colors(name, {**_own_colors(name), color: value})
    return True


def reset_scheme_color(name: str, color: str) -> None:
    own = _own_colors(name)
    if color in own:
        del own[color]
        _write_own_colors(name, own)


def reset_scheme(name: str) -> None:
    own_colors_path(name).unlink(missing_ok=True)


def has_own_colors(name: str) -> bool:
    return bool(_own_colors(name))


def _write_own_colors(name: str, own: Dict[str, str]) -> None:
    path = own_colors_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(own, indent=4) + "\n", encoding="utf-8")
    tmp.replace(path)  # whole or not at all, as with the settings file
