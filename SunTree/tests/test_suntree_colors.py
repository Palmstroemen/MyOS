"""SunTree wears the scheme of Scope (core/color_schemes.py; Scope/Designdocument Setup.md, step 2):
it reads it each time it appears, and what stands on a project's colour stays readable."""

import re
from pathlib import Path

from PySide6.QtGui import QColor

from core.color_schemes import load_scheme, set_scheme_color
from core.settings import Settings
from SunTree.tests.test_suntree_crown import _call, suntree, window, world  # noqa: F401

MAIN = Path(__file__).resolve().parents[1] / "main.qml"


def test_no_colour_is_left_in_the_code():
    assert not re.findall(r'"#[0-9a-fA-F]{3,8}"|Qt\.rgba|"rgba', MAIN.read_text(encoding="utf-8"))


def test_the_backend_gives_the_scheme_worn(world, suntree):
    assert suntree.colorScheme() == load_scheme("dark")
    Settings().set("General/darkTheme", False)
    assert suntree.colorScheme() == load_scheme("light")
    assert suntree.darkThemeSetting() is False


def test_a_change_counts_when_suntree_appears_next(world, suntree, window):
    set_scheme_color("dark", "crownText", "#123456")
    assert window.property("schemeColors")["crownText"] != "#123456"
    _call(window, "applyCrownSettings")
    assert window.property("schemeColors")["crownText"] == "#123456"

    Settings().set("General/darkTheme", False)
    _call(window, "applyCrownSettings")
    assert window.property("schemeColors") == load_scheme("light")


def test_the_cwd_glows_light_on_dark_and_dark_on_light(world, suntree, window):
    assert window.property("cwdGlow") == "#ffffff"
    Settings().set("General/darkTheme", False)
    _call(window, "applyCrownSettings")
    assert QColor(window.property("cwdGlow")).lightness() < 60


def test_the_schemes_text_stays_where_it_can_be_read(world, suntree, window):
    assert _call(window, "readableOn", "#eaf3ff", "#3f5475") == "#eaf3ff"
    assert _call(window, "readableOn", "#1a2233", "#a3b9dc") == "#1a2233"


def test_text_turns_over_where_it_could_not_be_read(world, suntree, window):
    assert QColor(_call(window, "readableOn", "#eaf3ff", "#eedd22")).lightness() < 60  # light on yellow
    assert QColor(_call(window, "readableOn", "#1a2233", "#3118ab")).lightness() > 200  # dark on violet


def test_a_pale_folder_counts_with_what_shines_through(world, suntree, window):
    pale = _call(window, "mixedOver", "#3118ab", "#d5e4e8", 0.4)
    assert QColor(pale).lightness() > QColor("#3118ab").lightness()
    assert _call(window, "mixedOver", "#3118ab", "#d5e4e8", 1) == "#3118ab"
