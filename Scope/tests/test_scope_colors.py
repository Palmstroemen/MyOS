"""Scope's colours come from the scheme files (core/color_schemes.py; Scope/Designdocument
Setup.md, step 2): main.qml names them, the scheme holds them, and light/dark changes the scheme."""

import os
import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core.color_schemes import load_scheme

SCOPE_DIR = Path(__file__).resolve().parents[1]
MAIN = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")


def test_main_names_exactly_the_colours_of_the_scheme():
    assert set(re.findall(r"schemeColors\.(\w+)", MAIN)) == set(load_scheme("dark"))


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
