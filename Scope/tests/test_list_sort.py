"""Sorting of the FilesPanel list (Scope/js/ListSort.js), run in Qt's JS engine."""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QJSEngine

LIST_SORT_JS = Path(__file__).resolve().parents[1] / "js" / "ListSort.js"


@pytest.fixture(scope="module")
def sort_names():
    # QJSEngine needs an application; the same kind as the other Scope tests so they coexist.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    source = LIST_SORT_JS.read_text(encoding="utf-8").replace(".pragma library", "")
    result = engine.evaluate(source)
    assert not result.isError(), result.toString()
    fn = engine.globalObject().property("sortEntries")

    def run(entries, key, ascending):
        sorted_value = fn.call([engine.toScriptValue(entries), key, ascending])
        assert not sorted_value.isError(), sorted_value.toString()
        return [row["name"] for row in sorted_value.toVariant()]

    yield run


ENTRIES = [
    {"name": "b.txt", "isDir": False, "sizeBytes": 10, "modifiedTs": 300},
    {"name": "Zeta", "isDir": True, "folderSizeBytes": 5000, "modifiedTs": 100},
    {"name": "a.txt", "isDir": False, "sizeBytes": 900, "modifiedTs": 200},
    {"name": "alpha", "isDir": True, "folderSizeBytes": -1, "modifiedTs": 400},
    {"name": "Mitte", "isDir": True, "folderSizeBytes": 20, "modifiedTs": -1},
]


def test_name_sort_keeps_folders_first_and_ignores_case(sort_names):
    assert sort_names(ENTRIES, "name", True) == ["alpha", "Mitte", "Zeta", "a.txt", "b.txt"]
    assert sort_names(ENTRIES, "name", False) == ["Zeta", "Mitte", "alpha", "b.txt", "a.txt"]


def test_size_sort_puts_unknown_sizes_last_in_both_directions(sort_names):
    assert sort_names(ENTRIES, "size", True) == ["Mitte", "Zeta", "alpha", "b.txt", "a.txt"]
    assert sort_names(ENTRIES, "size", False) == ["Zeta", "Mitte", "alpha", "a.txt", "b.txt"]


def test_modified_sort_puts_unknown_dates_last(sort_names):
    assert sort_names(ENTRIES, "modified", True) == ["Zeta", "alpha", "Mitte", "a.txt", "b.txt"]
    assert sort_names(ENTRIES, "modified", False) == ["alpha", "Zeta", "Mitte", "b.txt", "a.txt"]


def test_unknown_key_falls_back_to_name(sort_names):
    assert sort_names(ENTRIES, "bogus", True) == sort_names(ENTRIES, "name", True)


TEXT_ENTRIES = [
    {"name": "c.md", "isDir": False, "typeName": "Markdown", "owner": "oliver", "tags": ["b"], "accessedTs": 5},
    {"name": "a.pdf", "isDir": False, "typeName": "PDF-Dokument", "owner": "root", "tags": [], "accessedTs": 9},
    {"name": "b.txt", "isDir": False, "typeName": "Einfacher Text", "owner": "Anna", "tags": ["a"], "accessedTs": -1},
]


def test_text_columns_sort_case_insensitive_with_empty_last(sort_names):
    assert sort_names(TEXT_ENTRIES, "type", True) == ["b.txt", "c.md", "a.pdf"]
    assert sort_names(TEXT_ENTRIES, "owner", True) == ["b.txt", "c.md", "a.pdf"]
    assert sort_names(TEXT_ENTRIES, "tags", True) == ["b.txt", "c.md", "a.pdf"]
    assert sort_names(TEXT_ENTRIES, "tags", False) == ["c.md", "b.txt", "a.pdf"]


def test_access_time_sorts_like_a_date(sort_names):
    assert sort_names(TEXT_ENTRIES, "accessed", False) == ["a.pdf", "c.md", "b.txt"]


def test_default_direction_is_descending_only_for_dates_and_size():
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    engine.evaluate(LIST_SORT_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    first = engine.globalObject().property("defaultAscending")
    results = {key: first.call([key]).toBool() for key in
               ("name", "type", "tags", "permissions", "owner", "group", "modified", "accessed", "size")}
    assert results == {"name": True, "type": True, "tags": True, "permissions": True, "owner": True,
                       "group": True, "modified": False, "accessed": False, "size": False}


GRID_ENTRIES = [
    {"name": "b.txt", "isDir": False, "modifiedTs": 300},
    {"name": "Aufträge", "isDir": True, "isProject": True, "modifiedTs": 100},
    {"name": "08_Dokumentation", "isDir": True, "isEmbryo": True},
    {"name": "Zeta", "isDir": True, "isStandard": True, "modifiedTs": 400},
    {"name": "01_Ablage", "isDir": True, "modifiedTs": 500},
    {"name": "04_Finanz", "isDir": True, "isStandard": True, "modifiedTs": 200},
    {"name": "a.txt", "isDir": False, "modifiedTs": 200},
]


@pytest.fixture(scope="module")
def grid_names():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    result = engine.evaluate(LIST_SORT_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    assert not result.isError(), result.toString()
    fn = engine.globalObject().property("sortForGrid")

    def run(entries):
        value = fn.call([engine.toScriptValue(entries)])
        assert not value.isError(), value.toString()
        return [row["name"] for row in value.toVariant()]

    yield run


def test_the_grid_shows_myos_folders_first_then_other_folders_then_files(grid_names):
    assert grid_names(GRID_ENTRIES) == [
        "04_Finanz", "08_Dokumentation", "Zeta",  # MyOS folders, born or pale
        "01_Ablage", "Aufträge",  # subprojects and other folders
        "a.txt", "b.txt",
    ]


def test_the_grid_order_does_not_depend_on_the_list_columns():
    main = (Path(__file__).resolve().parents[1] / "main.qml").read_text(encoding="utf-8")
    assert 'filesItemStyle === "largeIcon"' in main.split("fileItemsRaw = ", 1)[1].split("\n", 1)[0]
    toggle = main.split("onItemStyleToggleRequested:", 1)[1].split("compactButtonHeight:", 1)[0]
    assert "filterEntries()" in toggle  # the other view has its own order
