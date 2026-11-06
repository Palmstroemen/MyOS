"""While the back of Scope is shown, the front takes nothing (Scope/Designdocument Setup.md, 1):
a drag on the back woke the drag handlers of the front behind it, and one caught a folder."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow  # noqa: F401  (QQuickWindow: root objects come as what they are)
from PySide6.QtTest import QTest

from core.color_schemes import load_scheme

SCOPE_DIR = Path(__file__).resolve().parents[1]


class SchemeHost(QObject):
    @Slot(str, result="QVariantMap")
    def colorScheme(self, name):
        return load_scheme(name)


@pytest.fixture
def window():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    host = SchemeHost()
    engine.rootContext().setContextProperty("backend", host)
    engine.rootContext().setContextProperty("scopeStartPath", "")
    engine.rootContext().setContextProperty("scopeProjectRoot", "")
    engine.load(QUrl.fromLocalFile(str(SCOPE_DIR / "main.qml")))
    assert engine.rootObjects()
    root = engine.rootObjects()[0]
    root.setProperty("width", 1300)
    root.setProperty("height", 850)
    QTest.qWait(100)
    yield root
    root.close()


def _front_handlers_enabled(window):
    """For each drag handler of the front: is its item enabled? Qt delivers nothing to one that is not."""
    setup = window.findChild(QQuickItem, "setupPage")
    def on_the_back(item):
        while item is not None:
            if item == setup:
                return True
            item = item.parentItem()
        return False
    items = [o.parent() for o in window.findChildren(QObject)
             if "DragHandler" in o.metaObject().className() and isinstance(o.parent(), QQuickItem)]
    return [item.isEnabled() for item in items if not on_the_back(item)]


def test_the_front_takes_nothing_while_the_back_is_shown(window):
    assert _front_handlers_enabled(window) and all(_front_handlers_enabled(window))
    window.setProperty("setupShown", True)
    QTest.qWait(20)
    assert not any(_front_handlers_enabled(window))


def test_the_front_answers_again_after_the_back(window):
    window.setProperty("setupShown", True)
    QTest.qWait(20)
    window.setProperty("setupShown", False)
    QTest.qWait(20)
    assert all(_front_handlers_enabled(window))
