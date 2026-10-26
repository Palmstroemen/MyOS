"""A small SunTree crown on the SunTree tab of Scope's back (Scope/CrownPreview.qml): it shows
what the values do - with SunTree's own arithmetic (SunTree/js/Crown.js) - and plays a dive
through one level whenever a value changes."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture
def preview(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    qml = tmp_path / "host.qml"
    qml.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'CrownPreview { width: 200; height: 400 }\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(50)
    yield view.rootObject()
    view.close()


def _guides(root):
    from PySide6.QtCore import QMetaObject, Q_RETURN_ARG
    result = QMetaObject.invokeMethod(root, "guides", Q_RETURN_ARG("QVariant"))
    return result.toVariant() if hasattr(result, "toVariant") else result


def test_the_lines_are_where_suntree_draws_them(preview):
    g = _guides(preview)
    R = g["R"]
    assert abs(g["inner"] - 0.2 * R) < 1e-6 and abs(g["line"] - 0.7 * R) < 1e-6
    assert abs(g["enter"] - (0.2 * R + 0.5 * R / 0.75)) < 1e-6  # the field's edge (fieldEnd)
    assert abs(g["leave"] - (0.2 * R + 0.25 * 0.8 * R)) < 1e-6  # where the next level starts

    preview.setProperty("enter", 0.9)
    preview.setProperty("lineT", 0.6)
    g = _guides(preview)
    assert abs(g["line"] - 0.6 * R) < 1e-6 and abs(g["enter"] - (0.2 * R + 0.4 * R / 0.9)) < 1e-6


def _call(root, name, *args):
    from PySide6.QtCore import QMetaObject, Q_ARG, Q_RETURN_ARG
    result = QMetaObject.invokeMethod(root, name, Q_RETURN_ARG("QVariant"), *[Q_ARG("QVariant", a) for a in args])
    return result.toVariant() if hasattr(result, "toVariant") else result


def test_moving_the_borders_plays_nothing(preview):
    QTest.qWait(300)
    for name, value in (("inner", 0.25), ("leave", 0.3), ("lineT", 0.6), ("enter", 0.9)):
        preview.setProperty(name, value)
    QTest.qWait(250)
    assert not preview.property("playing")


def test_the_hand_plays_with_the_fan(preview):
    # Outward the folder under the hand grows; the fan follows with the softness.
    g = _guides(preview)
    cx, cy = preview.property("cx"), preview.property("cy")
    _call(preview, "handAt", cx + g["line"], cy)  # at the line T: the field fills the half
    assert preview.property("targetS") > g["inner"]
    QTest.qWait(1500)
    assert abs(preview.property("shownS") - preview.property("targetS")) < 1


def test_a_new_value_plays_nothing(preview):
    preview.setProperty("lens", 4.0)
    preview.setProperty("softness", 3.0)
    QTest.qWait(300)
    assert not preview.property("playing") and preview.property("shownLens") == 4.0


def test_over_the_magnifier_the_fan_breathes_and_rests_when_left(preview):
    preview.setProperty("demo", "lens")
    QTest.qWait(100)
    assert preview.property("playing")
    seen = []
    for _ in range(30):  # one breath: 2.8 s
        QTest.qWait(100)
        seen.append(preview.property("shownLens"))
    assert max(seen) > 2.2 > min(seen)  # around the value set
    preview.setProperty("demo", "")
    QTest.qWait(50)
    assert not preview.property("playing") and preview.property("shownLens") == 2.2


def test_over_a_border_the_pointer_goes_where_it_counts(preview):
    g = _guides(preview)
    preview.setProperty("demo", "lineT")
    QTest.qWait(1500)
    assert preview.property("highlight") == "lineT"
    assert abs(_call(preview, "pointerRadius") - g["line"]) < 3  # on the amber ring
    preview.setProperty("demo", "inner")
    QTest.qWait(1500)
    assert abs(_call(preview, "pointerRadius") - g["inner"]) < 3


def test_over_softness_the_pointer_wiggles_as_softly_as_set(preview):
    def lag(softness):
        preview.setProperty("softness", softness)
        preview.setProperty("demo", "softness")
        QTest.qWait(150)
        assert preview.property("handShown")  # the hand drawn as a ring, the fan following it
        gaps = []
        for _ in range(10):
            QTest.qWait(60)
            gaps.append(abs(preview.property("shownU") - preview.property("targetU")))
        preview.setProperty("demo", "")
        QTest.qWait(200)
        return sum(gaps)
    soft, direct = lag(3.0), lag(25.0)
    assert soft > 3 * direct  # softer follows clearly further behind
    assert preview.property("handShown") is False  # the hand's ring only while it plays


def test_the_exit_at_the_edge_runs_past_the_ends(preview):
    g = _guides(preview)
    assert abs(g["exit"] - 0.08 * g["R"]) < 1e-6  # the arc beyond the first and last folder
    preview.setProperty("edge", 0.15)
    assert abs(_guides(preview)["exit"] - 0.15 * g["R"]) < 1e-6


def test_the_stem_is_hinted_left_of_the_centre(preview):
    from PySide6.QtCore import QMetaObject, Q_RETURN_ARG
    result = QMetaObject.invokeMethod(preview, "stemShape", Q_RETURN_ARG("QVariant"))
    stem = result.toVariant() if hasattr(result, "toVariant") else result
    assert stem["width"] > 0 and stem["ovalRadius"] > 0
    assert stem["width"] == preview.property("cx")  # the stem reaches the centre of the half
    assert stem["ovalRadius"] < _guides(preview)["inner"]  # the oval's end lies in the hollow
