"""The tools row at the top of M's dropdown below the CWD (Scope/CwdTools.qml): what would hide
behind a menu lies there as buttons - Clipboard, search, light/dark, language, hidden folders
(Designdocument Perspective Resolver MVP.md, E4). The search is no tool here: its magnifier stands
in the line, right of the CWD (a click in the dropdown closed it before the field showed)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

SCOPE_DIR = Path(__file__).resolve().parents[1]
TOOLS = ["toolClipboard", "toolTheme", "toolLanguage", "toolHidden", "toolSetup"]


@pytest.fixture
def tools(tmp_path):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    host = tmp_path / "host.qml"
    host.write_text(
        f'import QtQuick 2.15\nimport "{SCOPE_DIR.as_uri()}"\n'
        'CwdTools { id: t; objectName: "tools"; buttonSize: 28; baseFont: 13\n'
        '  property var heard: []\n'
        '  onOpenClipboard: heard = heard.concat(["clipboard"])\n'
        '  onSwitchTheme: heard = heard.concat(["theme"])\n'
        '  onSwitchLanguage: heard = heard.concat(["language"])\n'
        '  onToggleHidden: heard = heard.concat(["hidden"])\n'
        '  onOpenSetup: heard = heard.concat(["setup"])\n'
        '}\n', encoding="utf-8")
    view = QQuickView()
    view.setSource(QUrl.fromLocalFile(str(host)))
    assert view.status() == QQuickView.Ready, [e.toString() for e in view.errors()]
    view.show()
    QTest.qWait(50)
    yield view
    view.close()


def _button(view, name):
    return view.rootObject().findChild(QQuickItem, name)


def _click(view, name):
    button = _button(view, name)
    centre = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, centre.toPoint())


def test_all_tools_lie_in_one_row(tools):
    buttons = [_button(tools, name) for name in TOOLS]
    assert all(b is not None and b.isVisible() for b in buttons)
    xs = [b.mapToScene(QPointF(0, 0)).x() for b in buttons]
    assert xs == sorted(xs) and len({b.mapToScene(QPointF(0, 0)).y() for b in buttons}) == 1
    assert tools.rootObject().property("implicitWidth") >= len(TOOLS) * 28


def test_each_button_says_what_it_wants(tools):
    for name in TOOLS:
        _click(tools, name)
    heard = tools.rootObject().property("heard")
    assert (heard.toVariant() if hasattr(heard, "toVariant") else heard) == [
        "clipboard", "theme", "language", "hidden", "setup"]


def test_the_buttons_show_the_state(tools):
    root = tools.rootObject()
    root.setProperty("clipboardHasItems", False)
    assert _button(tools, "toolClipboard").opacity() < 1  # empty: pale
    root.setProperty("clipboardHasItems", True)
    assert _button(tools, "toolClipboard").opacity() == 1

    root.setProperty("language", "de")
    assert _button(tools, "toolLanguage").property("label") == "DE"
    root.setProperty("hiddenShown", False)
    assert not _button(tools, "toolHidden").property("checked")


def test_the_search_is_no_tool_of_the_dropdown(tools):
    assert _button(tools, "toolSearch") is None
