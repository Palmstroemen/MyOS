"""M is one line (Designdocument Perspective Resolver MVP.md, E4): the MyOS folders stand right
of the CWD and never flow onto a second line; when they do not fit, the wheel moves them
sideways (FolderBrowser.wrapFolders false)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]
FOLDERS = ["00_Admin", "01_Info", "02_Team", "03_Kommunikation", "04_Finanz", "05_Rechtliches",
           "06_Ressourcen", "07_Arbeit", "08_Dokumentation"]


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _browser(tmp_path, wrap, path_bar=False, search=False):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = tmp_path / f"host_{wrap}_{path_bar}_{search}.qml"
    host.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'Item { width: 500; height: 120\n'
        '  FolderBrowser { objectName: "browser"; anchors.left: parent.left; anchors.right: parent.right\n'
        f'    path: "/p/Projekte/Job/04_Finanz/Ausgaben/2026"; usePathBar: {str(path_bar).lower()}\n'
        '    foldersShown: true; showModeToggle: false\n'
        f'    showSearchToggle: {str(search).lower()}; showClipboardButton: false; wrapFolders: {str(wrap).lower()}\n'
        f'    searchActive: {str(search).lower()}\n'
        f'    folders: {FOLDERS!r}\n'
        '  }\n}\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(host)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(400)  # the flow is placed after layout (100 ms throttle)
    return view


def test_without_wrapping_the_folders_stay_on_the_line(tmp_path):
    view = _browser(tmp_path, wrap=False)
    browser = view.rootObject().findChild(QQuickItem, "browser")
    assert browser.property("flowOnSecondLine") is False
    view.close()


def test_elsewhere_they_still_flow_onto_a_second_line(tmp_path):
    view = _browser(tmp_path, wrap=True)
    browser = view.rootObject().findChild(QQuickItem, "browser")
    assert browser.property("flowOnSecondLine") is True
    view.close()


def test_beside_a_path_the_folders_keep_room(tmp_path):
    # A path in the line too (deeper, or a lens on): the folders must not shrink to nothing.
    view = _browser(tmp_path, wrap=False, path_bar=True)
    browser = view.rootObject().findChild(QQuickItem, "browser")
    first = next(i for i in _walk(browser) if i.property("label") == "00_Admin" and i.isVisible())
    host = first.parentItem().parentItem()
    assert host.width() >= first.width()
    view.close()


def test_the_magnifier_and_its_field_stand_before_the_folders(tmp_path):
    # M: the search's magnifier is in the line, right of the CWD; its field opens there and
    # pushes the folders aside instead of lying over them.
    from PySide6.QtCore import QPointF

    view = _browser(tmp_path, wrap=False, path_bar=True, search=True)
    browser = view.rootObject().findChild(QQuickItem, "browser")
    field = next(i for i in _walk(browser) if i.inherits("QQuickTextInput")
                 and i.property("placeholderText") is not None and i.isVisible())
    first = next(i for i in _walk(browser) if i.property("label") == "00_Admin" and i.isVisible())
    assert field.mapToScene(QPointF(field.width(), 0)).x() <= first.mapToScene(QPointF(0, 0)).x()
    view.close()
