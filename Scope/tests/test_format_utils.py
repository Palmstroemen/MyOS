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
