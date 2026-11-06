"""Scope's colours come from the scheme files (core/color_schemes.py; Scope/Designdocument
Setup.md, step 2): main.qml names them, the scheme holds them, and light/dark changes the scheme."""

import os
import re
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem

from core.color_schemes import load_scheme

SCOPE_DIR = Path(__file__).resolve().parents[1]
MAIN = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")


def test_scope_names_exactly_the_colours_of_the_scheme():
    named = set()
    for qml in [*SCOPE_DIR.glob("*.qml"), *SCOPE_DIR.glob("Dialogs/*.qml")]:
        named |= set(re.findall(r"schemeColors\.(\w+)", qml.read_text(encoding="utf-8")))
    assert named == set(load_scheme("dark"))


def test_no_colour_of_the_scheme_is_left_in_main():
    colours = MAIN[MAIN.index("property color dialogPanelBg"):MAIN.index("property color currentProjectTint")]
    assert not re.search(r'darkTheme\s*\?\s*"#', colours)


class SchemeHost(QObject):
    """Just what main.qml asks for its colours; the rest of Scope's backend stays away."""

    @Slot(str, result="QVariantMap")
    def colorScheme(self, name):
        return load_scheme(name)


@pytest.fixture
def window():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    host = SchemeHost()
    engine.rootContext().setContextProperty("backend", host)
    engine.rootContext().setContextProperty("scopeStartPath", "")
    engine.rootContext().setContextProperty("scopeProjectRoot", "")
    engine.load(QUrl.fromLocalFile(str(SCOPE_DIR / "main.qml")))
    assert engine.rootObjects()
    root = engine.rootObjects()[0]
    yield root
    root.close()


def _colours(window):
    theme = next(o for o in window.findChildren(QObject) if o.metaObject().indexOfProperty("filesPaneBackground") >= 0)
    return {"dialogPanelBg": window.property("dialogPanelBg"), "bg": theme.property("bg"),
            "accentPrimaryText": theme.property("accentPrimaryText")}


@pytest.mark.parametrize("dark, scheme", [(True, "dark"), (False, "light")])
def test_the_window_wears_the_scheme(window, dark, scheme):
    window.setProperty("darkTheme", dark)
    for name, colour in _colours(window).items():
        assert colour == QColor(load_scheme(scheme)[name]), name


# --- The middle of the FilesPanel: a colour of each scheme, no longer a veil over the frame ------


def _files_panel(window):
    return next(o for o in window.findChildren(QObject) if o.metaObject().indexOfProperty("filesCenterColor") >= 0)


def _lightness(color):
    return (color.redF() + color.greenF() + color.blueF()) / 3


def test_the_middle_is_light_in_light_and_dark_in_dark(window):
    window.setProperty("darkTheme", True)
    dark = QColor(_files_panel(window).property("filesCenterColor"))
    window.setProperty("darkTheme", False)
    light = QColor(_files_panel(window).property("filesCenterColor"))
    assert _lightness(light) > _lightness(dark) + 0.1


def test_the_middle_is_set_for_each_scheme_on_its_own(window, monkeypatch):
    window.setProperty("darkTheme", True)
    dark_before = QColor(_files_panel(window).property("filesCenterColor"))
    window.setProperty("darkTheme", False)
    light_before = QColor(_files_panel(window).property("filesCenterColor"))

    original = load_scheme
    def other_light(name):
        scheme = original(name)
        if name == "light":
            scheme["filesPanelCenter"] = "#102030"
        return scheme
    monkeypatch.setattr(sys.modules[__name__], "load_scheme", other_light)

    window.setProperty("darkTheme", True)  # asks for the schemes anew
    assert QColor(_files_panel(window).property("filesCenterColor")) == dark_before
    window.setProperty("darkTheme", False)
    assert QColor(_files_panel(window).property("filesCenterColor")) != light_before


def test_the_middle_lies_under_the_files(window):
    # Over them (z: 1) it hid the files; as a veil it had been dulling them all along.
    center = window.findChild(QQuickItem, "filesCenter")
    assert center.z() == 0
    grid = window.findChild(QQuickItem, "filesCenter").parentItem().childItems()
    assert grid.index(center) < next(i for i, item in enumerate(grid) if "ColumnLayout" in item.metaObject().className())


def test_a_colour_set_on_the_back_shows_at_once(window, monkeypatch):
    before = QColor(_files_panel(window).property("filesCenterColor"))
    original = load_scheme
    def own(name):
        scheme = original(name)
        scheme["filesPanelCenter"] = "#102030"
        return scheme
    monkeypatch.setattr(sys.modules[__name__], "load_scheme", own)
    window.setProperty("schemeRevision", window.property("schemeRevision") + 1)  # what the back's edit does
    assert QColor(_files_panel(window).property("filesCenterColor")) != before


def test_the_back_tells_main_of_a_colour_set():
    assert "onSchemeColorEdited: window.schemeRevision++" in MAIN


def test_no_veil_over_the_middle_is_left():
    panel = (SCOPE_DIR / "FilesPanel.qml").read_text(encoding="utf-8")
    assert "filesPanelOverlay" not in panel
    assert "filesOverlayColor" not in (SCOPE_DIR / "Theme" / "panel_colors.js").read_text(encoding="utf-8")


# --- The colours scattered over the other files -----------------------------------------------


def test_the_components_keep_no_colours_of_their_own():
    # main.qml hands them the scheme's; a default here would hide a colour forgotten there.
    for name in ("FilesPanel.qml", "FolderBrowser.qml", "CwdTools.qml", "SetupPage.qml"):
        source = (SCOPE_DIR / name).read_text(encoding="utf-8")
        assert not re.search(r'property color \w+: (\w+ \? )?"#', source), name


def test_the_acl_dialogs_take_the_scheme():
    for name in ("AclRoleDialog.qml", "AclPersonDialog.qml"):
        source = (SCOPE_DIR / "Dialogs" / name).read_text(encoding="utf-8")
        assert not re.search(r'color: (\w+\.\w+ \? )?"#', source), name
