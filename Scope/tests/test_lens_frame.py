"""The lens' frame in the path line (Scope/js/FolderBrowserUtils.js), run in Qt's JS engine.

Designdocument Perspective Resolver MVP.md, A3: Projekte › Job › [✕ 04_Finanz › Ausgaben].
The frame holds the segments below the project the lens looks into."""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QJSEngine

FB_UTILS_JS = Path(__file__).resolve().parents[1] / "js" / "FolderBrowserUtils.js"

JOB = "/home/u/Projekte/Job"
LINE = ["/home/u/Projekte", JOB, JOB + "/04_Finanz", JOB + "/04_Finanz/Ausgaben"]


@pytest.fixture(scope="module")
def js():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    result = engine.evaluate(FB_UTILS_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    assert not result.isError(), result.toString()

    def call(name, *args):
        value = engine.globalObject().property(name).call([engine.toScriptValue(a) for a in args])
        assert not value.isError(), value.toString()
        return value.toVariant()

    yield call


def test_the_frame_starts_below_the_project(js):
    assert js("lensFrameStart", LINE, JOB) == 2
    assert js("lensFrameStart", LINE, JOB + "/") == 2


def test_no_frame_without_a_lens_or_outside_it(js):
    assert js("lensFrameStart", LINE, "") == 4
    assert js("lensFrameStart", LINE, "/home/u/Projekte/Reisen") == 4
    assert js("lensFrameStart", LINE, JOB + "/04_Finanz/Ausgaben") == 4  # nothing below it


def test_a_name_starting_like_the_project_is_not_below_it(js):
    assert js("lensFrameStart", ["/home/u/Projekte", JOB + "2/04_Finanz"], JOB) == 2


def test_index_ranges_for_the_two_parts_of_the_line(js):
    assert js("indexRange", 0, 2) == [0, 1]
    assert js("indexRange", 2, 4) == [2, 3]
    assert js("indexRange", 3, 3) == []


def test_the_minimal_view_starts_the_path_line_below_the_project(js):
    # Minimal view (M): the CWD button stands left; the path line goes on below it.
    assert js("firstBelow", LINE, JOB) == 2
    assert js("firstBelow", LINE, "") == 0  # nothing hidden
    assert js("firstBelow", [JOB], JOB) == 1  # only the project: nothing left to show
    assert js("firstBelow", ["/home/u/Projekte", JOB + "2/04_Finanz"], JOB) == 2


def test_the_cascade_ends_at_the_projects_root(js):
    chain = ["/home", "/home/u", "/home/u/Projekte", "/home/u/Projekte/Wohnen"]
    assert js("pathsFrom", chain, "/home/u/Projekte") == ["/home/u/Projekte", "/home/u/Projekte/Wohnen"]
    assert js("pathsFrom", chain, "") == chain
