"""Where a folder button takes a click (Scope/FolderItem.qml, hitAcceptsPoint).

A folder with a badge (a department's icon such as "€") shows the badge instead of the
folder icon; the badge takes clicks like the icon does."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Q_ARG, Q_RETURN_ARG, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

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
            f'FolderItem {{ width: 160; label: "04_Finanz"; style: "smallIcon"; compactHeight: 24; iconSmall: 16; {props} }}'
            .encode(), QUrl.fromLocalFile(str(SCOPE_DIR / "test.qml")))
        item = component.create()
        assert item is not None, component.errorString()
        QQmlEngine.setObjectOwnership(item, QQmlEngine.CppOwnership)
        made.append((component, item))
        app.processEvents()
        return item

    yield make


def _hits(item, x, y):
    return QMetaObject.invokeMethod(item, "hitAcceptsPoint", Q_RETURN_ARG("QVariant"), Q_ARG("QVariant", x), Q_ARG("QVariant", y))


@pytest.mark.parametrize("edge_icon", [False, True])
def test_the_badge_takes_a_click_like_the_icon(make_item, edge_icon):
    item = make_item(f'batchText: "€"; edgeIcon: {str(edge_icon).lower()}')
    box = item.property("smallIconBox")
    left = 0 if edge_icon else 6
    assert _hits(item, left + box / 2, 12)


def test_the_icon_takes_a_click(make_item):
    item = make_item(f'iconSource: "{(SCOPE_DIR / "Theme" / "icons" / "folder.svg").as_uri()}"')
    assert _hits(item, 6 + 8, 12)


def test_room_after_the_name_takes_no_click(make_item):
    item = make_item('batchText: "€"')
    assert not _hits(item, 158, 12)
