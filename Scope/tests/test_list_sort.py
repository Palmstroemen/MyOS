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
