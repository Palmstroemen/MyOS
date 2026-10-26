"""The CWD's mark in Scope (Scope/FolderItem.qml), as in SunTree (SunTree/Designdocument
Krone.md): light around it in its project's colour lit up, a bright frame, bold. On a light
theme a light glow does not show; there the frame is stronger instead."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem  # noqa: F401 (created items come typed as such)

SCOPE_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def make_item():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlEngine()
    made = []

    def make(props):
        component = QQmlComponent(engine)
        component.setData(
            f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
            f'FolderItem {{ width: 160; label: "Job"; style: "text"; compactHeight: 24; {props} }}'
            .encode(), QUrl.fromLocalFile(str(SCOPE_DIR / "test.qml")))
        item = component.create()
        assert item is not None, component.errorString()
        QQmlEngine.setObjectOwnership(item, QQmlEngine.CppOwnership)
        made.append((component, item))
        app.processEvents()
        return item

    yield make


def _glow(item):
    # Repeater-made: in the item tree, not among the QObject children.
    return [child for child in item.childItems() if child.objectName() == "cwdGlow"]


def test_an_ordinary_button_is_not_marked(make_item):
    item = make_item('strokeColor: "#58648a"')
    assert item.property("shownBorderWidth") == 1
    assert not item.property("shownBold")
    assert not any(g.isVisible() for g in _glow(item))


def test_the_cwd_glows_with_a_bright_frame_and_bold(make_item):
    item = make_item('cwdMark: true; cwdMarkColor: "#ffd9a0"; strokeColor: "#58648a"')
    assert item.property("shownBorderWidth") == 2 and QColor(item.property("shownBorderColor")) == QColor("#ffd9a0")
    assert item.property("shownBold")
    glow = _glow(item)
    assert glow and all(g.isVisible() for g in glow)


def test_on_a_light_theme_the_frame_is_stronger_instead(make_item):
    item = make_item('cwdMark: true; cwdGlow: false; cwdMarkColor: "#5a3d00"')
    assert item.property("shownBorderWidth") == 3
    assert not any(g.isVisible() for g in _glow(item))
