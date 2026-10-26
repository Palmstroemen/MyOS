"""The back of Scope (Scope/SetupPage.qml; Scope/Designdocument Setup.md): tabs General, Scope,
Headline, SunTree; what is set there goes to the one settings file (core/settings.py)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]


class SettingsHost(QObject):
    """What Scope's backend offers the back (Scope.py: setting, setSetting, ...)."""

    def __init__(self):
        super().__init__()
        from core.settings import Settings
        self.settings = Settings()

    @Slot(str, result="QVariant")
    def setting(self, key):
        return self.settings.get(key)

    @Slot(str, "QVariant", result=bool)
    def setSetting(self, key, value):
        return self.settings.set(key, value)

    @Slot(str, result="QVariant")
    def settingDefault(self, key):
        return self.settings.default(key)

    @Slot(str, result="QVariantList")
    def settingLimits(self, key):
        return list(self.settings.limits(key) or [])

    @Slot(str)
    def resetSetting(self, key):
        self.settings.reset(key)


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _named(view, name):
    return next((i for i in _walk(view.rootObject()) if i.objectName() == name), None)


@pytest.fixture
def page(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = SettingsHost()
    qml = tmp_path / "host.qml"
    qml.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'SetupPage { width: 800; height: 600; settings: host\n'
        '  property var heard: []\n'
        '  onSwitchTheme: heard = heard.concat(["theme"])\n'
        '  onSwitchLanguage: heard = heard.concat(["language"])\n'
        '  onFlipBack: heard = heard.concat(["back"])\n'
        '  onToggleProjectsRow: heard = heard.concat(["projectsRow"])\n'
        '  onToggleTemplatesRow: heard = heard.concat(["templatesRow"])\n'
        '}\n', encoding="utf-8")
    view = QQuickView()
    view.rootContext().setContextProperty("host", host)
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(50)
    yield view, host
    view.close()


def _click(view, item):
    centre = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, centre.toPoint())
    QTest.qWait(30)


def _heard(view):
    heard = view.rootObject().property("heard")
    return heard.toVariant() if hasattr(heard, "toVariant") else heard


def test_four_tabs(page):
    view, _ = page
    assert [_named(view, f"tab{name}") is not None for name in ("General", "Scope", "Headline", "SunTree")] == [True] * 4


def test_general_switches_and_flipping_back(page):
    view, _ = page
    _click(view, _named(view, "setupTheme"))
    _click(view, _named(view, "setupLanguage"))
    _click(view, _named(view, "setupFlipBack"))
    assert _heard(view) == ["theme", "language", "back"]


def test_suntree_values_go_to_the_settings_file(page):
    from core.settings import Settings

    view, host = page
    _click(view, _named(view, "tabSunTree"))
    slider = _named(view, "setting_SunTree/enter")
    assert slider is not None and slider.property("value") == 0.75
    slider.setProperty("value", 0.85)
    QTest.qWait(30)
    assert Settings().get("SunTree/enter") == 0.85  # in the file, for SunTree to read

    _click(view, _named(view, "reset_SunTree/enter"))
    assert Settings().get("SunTree/enter") == 0.75 and slider.property("value") == 0.75


def test_the_small_crown_follows_the_sliders(page):
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    preview = _named(view, "crownPreview")
    assert preview is not None and preview.property("enter") == 0.75
    _named(view, "setting_SunTree/enter").setProperty("value", 0.9)
    QTest.qWait(30)
    assert abs(preview.property("enter") - 0.9) < 1e-9


ORDER = ["SunTree/inner", "SunTree/leave", "SunTree/lineT", "SunTree/enter",
         "SunTree/lens", "SunTree/softness", "SunTree/edge"]


def test_the_sliders_go_from_the_inside_out_each_explained(page):
    # In the order their lines lie in the small crown, then the three that are no line; a
    # line under each says what it does (the user does not know "crown" or "drawing in").
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    sliders = [_named(view, "setting_" + key) for key in ORDER]
    ys = [s.mapToScene(QPointF(0, 0)).y() for s in sliders]
    assert ys == sorted(ys)
    for key in ORDER:
        help_line = _named(view, "help_" + key)
        assert help_line is not None and help_line.isVisible() and len(help_line.property("text")) > 20


def test_over_a_slider_its_demo_plays_and_a_click_stops_it(page):
    from PySide6.QtCore import QPoint
    view, _ = page
    _click(view, _named(view, "tabSunTree"))
    preview = _named(view, "crownPreview")
    label = _named(view, "row_SunTree/lens")
    at = label.mapToScene(QPointF(label.width() / 2, label.height() / 2)).toPoint()
    QTest.mouseMove(view, at)
    QTest.qWait(100)
    assert preview.property("demo") == "lens"
    slider = _named(view, "setting_SunTree/lens")
    press = slider.mapToScene(QPointF(slider.width() / 2, slider.height() / 2)).toPoint()
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, press)
    QTest.qWait(50)
    assert preview.property("demo") == ""  # following the slider now
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, press)
    QTest.qWait(50)
    assert preview.property("demo") == ""  # and stays quiet while the mouse is on the row
    QTest.mouseMove(view, QPoint(5, 5))  # away ...
    QTest.qWait(50)
    QTest.mouseMove(view, at)  # ... and back: it shows again
    QTest.qWait(100)
    assert preview.property("demo") == "lens"


def test_the_scope_tab_switches_the_two_rows(page):
    view, _ = page
    root = view.rootObject()
    _click(view, _named(view, "tabScope"))
    _click(view, _named(view, "setupProjectsRow"))
    _click(view, _named(view, "setupTemplatesRow"))
    assert _heard(view)[-2:] == ["projectsRow", "templatesRow"]
    root.setProperty("projectsRowShown", False)
    assert "OFF" in _named(view, "setupProjectsRow").property("label")


def test_done_stands_top_left(page):
    view, _ = page
    done = _named(view, "setupFlipBack").mapToScene(QPointF(0, 0))
    title = _named(view, "setupTitle").mapToScene(QPointF(0, 0))
    assert done.x() < title.x() and abs(done.y() - title.y()) < 20
