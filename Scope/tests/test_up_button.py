"""Without the path bar (Setup, Scope tab) a row shows only its current folder; an ↑ button
left of it goes one folder up - as clicking the parent segment of the path bar would."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _named(view, name):
    return next((i for i in _walk(view.rootObject()) if i.objectName() == name), None)


def _browser(tmp_path, path, path_bar=False):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = tmp_path / "host.qml"
    host.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'Item { width: 700; height: 120\n'
        '  property var went: []\n'
        '  property var segments: []\n'
        '  FolderBrowser { objectName: "browser"; anchors.left: parent.left; anchors.right: parent.right\n'
        f'    path: "{path}"; pathDisplayPrefix: "/p/Projekte"; usePathBar: {str(path_bar).lower()}\n'
        '    foldersShown: true; showModeToggle: false; showSearchToggle: false; showClipboardButton: false\n'
        '    folders: ["Aufträge", "Belege"]\n'
        '    onNavigateToPathRequested: function(p) { parent.went = parent.went.concat([p]) }\n'
        '    onPathSegmentActivated: function(i) { parent.segments = parent.segments.concat([i]) }\n'
        '  }\n}\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(host)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(300)
    return view


def _list(view, name):
    value = view.rootObject().property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click(view, item):
    centre = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, centre)
    QTest.qWait(30)


def test_without_the_path_bar_up_stands_left_of_the_current_folder(tmp_path):
    view = _browser(tmp_path, "/p/Projekte/Job/04_Finanz")
    up = _named(view, "upButton")
    current = next(i for i in _walk(view.rootObject()) if i.property("label") == "04_Finanz" and i.isVisible())
    assert up is not None and up.isVisible()
    assert up.mapToScene(QPointF(up.width(), 0)).x() <= current.mapToScene(QPointF(0, 0)).x()
    _click(view, up)
    assert _list(view, "went") == ["/p/Projekte/Job"]
    assert _list(view, "segments") == [1]  # as the parent segment in the path bar
    view.close()


def test_at_the_top_of_the_row_up_goes_nowhere(tmp_path):
    view = _browser(tmp_path, "/p/Projekte")
    up = _named(view, "upButton")
    assert up.isVisible() and up.opacity() < 1.0
    _click(view, up)
    assert _list(view, "went") == []
    view.close()


def test_with_the_path_bar_there_is_no_up(tmp_path):
    view = _browser(tmp_path, "/p/Projekte/Job/04_Finanz", path_bar=True)
    up = _named(view, "upButton")
    assert up is None or not up.isVisible()
    view.close()


def test_main_keeps_m_without_up():
    # M climbs through its CWD dropdown; the ↑ is for the rows with the path bar switched off.
    main = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")
    projects = main[main.index("id: projectsBrowser"):]
    assert "showUpButton: !window.minimalView" in projects[:projects.index("onNavigationRequested")]
