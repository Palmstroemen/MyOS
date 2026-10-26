"""The files panel (Scope/FilesPanel.qml): embryos among the folders are pale as everywhere,
the X-ray button looks like an X-ray, and a new folder tag is a pale tag without a name that
one clicks to name."""

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


@pytest.fixture
def panel(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    qml = tmp_path / "host.qml"
    qml.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'Item { width: 1000; height: 640\n'
        '  property var asked: []\n'
        '  ListModel { id: files\n'
        '    ListElement { name: "Real"; isDir: true; isEmbryo: false; isVirtual: false; path: "/x/Real" }\n'
        '    ListElement { name: "Embryo"; isDir: true; isEmbryo: true; isVirtual: false; path: "/x/Embryo" }\n'
        '    ListElement { name: "2025"; isDir: true; isEmbryo: false; isVirtual: true; path: "/x/2025" }\n'
        '  }\n'
        '  FilesPanel { objectName: "panel"; anchors.fill: parent; itemsModel: files; showFolders: true\n'
        '    currentPath: "/x"\n'
        '    onAddFolderTagRequested: function(tag) { parent.asked = parent.asked.concat([tag]) } }\n'
        '}\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(150)
    yield view
    view.close()


def _entry(view, label):
    return next(i for i in _walk(view.rootObject()) if i.property("label") == label and i.property("itemPath") is not None)


def test_embryos_among_the_folders_are_pale(panel):
    assert _entry(panel, "Real").opacity() == 1.0
    assert abs(_entry(panel, "Embryo").opacity() - 0.4) < 1e-6  # as in the folder rows
    assert abs(_entry(panel, "2025").opacity() - 0.55) < 1e-6  # a virtual folder, as before


def test_the_xray_button_is_no_folder():
    main = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")
    assert 'iconFolderXray: Qt.resolvedUrl("Theme/icons/xray.svg")' in main
    assert (SCOPE_DIR / "Theme" / "icons" / "xray.svg").exists()


def test_a_new_folder_tag_is_a_pale_tag_to_name(panel):
    assert _named(panel, "tagEntryButton") is None  # no "#" button any more
    ghost = _named(panel, "ghostFolderTag")
    assert ghost is not None and ghost.isVisible() and ghost.opacity() < 0.5
    centre = ghost.mapToScene(QPointF(ghost.width() / 2, ghost.height() / 2)).toPoint()
    QTest.mouseClick(panel, Qt.LeftButton, Qt.NoModifier, centre)
    QTest.qWait(50)
    field = _named(panel, "newFolderTagInput")
    assert field.isVisible() and field.hasActiveFocus() and ghost.opacity() == 1.0  # named here
    field.setProperty("text", "Rechnungen")
    QTest.keyClick(panel, Qt.Key_Return)
    QTest.qWait(50)
    asked = panel.rootObject().property("asked")
    assert (asked.toVariant() if hasattr(asked, "toVariant") else asked) == ["Rechnungen"]
    assert ghost.opacity() < 0.5  # pale again for the next
