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
