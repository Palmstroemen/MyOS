"""List cell texts of the FilesPanel (Scope/js/FormatUtils.js), run in Qt's JS engine."""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QJSEngine

FORMAT_UTILS_JS = Path(__file__).resolve().parents[1] / "js" / "FormatUtils.js"


@pytest.fixture(scope="module")
def js():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    result = engine.evaluate(FORMAT_UTILS_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    assert not result.isError(), result.toString()

    def call(name, *args):
        value = engine.globalObject().property(name).call([engine.toScriptValue(a) for a in args])
        assert not value.isError(), value.toString()
        return value.toVariant()

    yield call


@pytest.mark.parametrize("mode, shown", [
    ("drwxr-xr-x", "d rwx r-x r-x"),
    ("-rw-r--r--", "- rw- r-- r--"),
    ("lrwxrwxrwx", "l rwx rwx rwx"),
    ("drwxrwsr-t", "d rwx rws r-t"),
    ("", ""),
    ("odd", "odd"),
])
def test_permissions_are_grouped_type_owner_group_others(js, mode, shown):
    assert js("listCellText", "permissions", {"permissions": mode}, False) == shown


def test_a_list_row_carries_every_role_the_panel_reads(js):
    row = js("listRow", {"name": "a.pdf", "isDir": False, "path": "/x/a.pdf", "tags": ["t"]})
    for role in ("isEmbryo", "isProject", "isVirtual", "projectColor", "xrayVia", "thumb", "batch",
                 "batchText", "iconName", "originPath", "filterGroup", "filterActive",
                 "sizeBytes", "folderSizeBytes", "folderSizeComplete", "modifiedTs", "accessedTs",
                 "typeName", "permissions", "owner", "group", "tagsText"):
        assert role in row, role
    assert row["isEmbryo"] is False and row["projectColor"] == "" and row["sizeBytes"] == -1
    assert row["tagsText"] == "#t" and row["name"] == "a.pdf"
    kept = js("listRow", {"name": "B", "isDir": True, "isEmbryo": True, "isProject": True, "projectColor": "#123456"})
    assert kept["isEmbryo"] is True and kept["isProject"] is True and kept["projectColor"] == "#123456"


def test_embryos_stay_pale_when_the_first_listing_held_only_files(tmp_path):
    # A ListModel knows only the roles of its first rows: a folder listed after a listing of
    # files alone (x-ray, folders hidden) lost isEmbryo and isProject - no pale folders, no P.
    from PySide6.QtCore import QUrl
    from PySide6.QtQuick import QQuickView
    from PySide6.QtTest import QTest

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    qml = tmp_path / "rows.qml"
    qml.write_text(
        'import QtQuick 2.15\n'
        f'import "{FORMAT_UTILS_JS.as_uri()}" as FormatUtils\n'
        'Item { property var seen: []\n'
        '  ListModel { id: rows; dynamicRoles: true }\n'
        '  Repeater { model: rows; delegate: Item { Component.onCompleted:\n'
        '    seen = seen.concat([[model.name, !!model.isEmbryo, !!model.isProject]]) } }\n'
        '  Component.onCompleted: {\n'
        '    rows.append(FormatUtils.listRow({ name: "a.pdf", isDir: false }))\n'
        '    rows.clear()\n'
        '    rows.append(FormatUtils.listRow({ name: "04_Finanz", isDir: true, isEmbryo: true }))\n'
        '    rows.append(FormatUtils.listRow({ name: "Job", isDir: true, isProject: true }))\n'
        '  } }\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    QTest.qWait(50)
    seen = view.rootObject().property("seen")
    seen = seen.toVariant() if hasattr(seen, "toVariant") else seen
    assert seen[-2:] == [["04_Finanz", True, False], ["Job", False, True]]
