"""SunTree without a background (SunTree/Designdocument Krone.md, one action then gone): only
the crown and the stem are drawn; a click beside them puts SunTree away (cancelling)."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from SunTree.tests.test_suntree_crown import _call, suntree, window, world  # noqa: F401


def _shown(window):
    window.show()
    QGuiApplication.instance().processEvents()
    assert window.isVisible()


def _main_area_origin(window):
    canvas = window.findChild(QQuickItem, "crownCanvas")
    at = canvas.mapToScene(QPointF(0, 0))
    return at.x(), at.y()


def test_the_background_is_transparent(world, window):
    _shown(window)
    image = window.grabWindow()
    assert image.pixelColor(3, 3).alpha() == 0  # the corner: nothing drawn
    geo = _call(window, "crownGeo", 1)
    ox, oy = _main_area_origin(window)
    folder = image.pixelColor(int(ox + geo["cx"] + geo["R"] * 0.5), int(oy + geo["cy"]))
    assert folder.alpha() == 255  # the crown is


def test_a_click_beside_the_crown_puts_suntree_away(world, window):
    _shown(window)
    geo = _call(window, "crownGeo", 1)
    _call(window, "crownClicked", geo["cx"] + geo["R"] + 15, geo["cy"] - geo["R"] + 10, False)
    assert not window.isVisible()


def test_a_click_in_the_margin_puts_suntree_away(world, window):
    _shown(window)
    QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, QPoint(4, 4))
    QGuiApplication.instance().processEvents()
    assert not window.isVisible()


def test_a_click_on_the_crown_or_the_stem_keeps_it(world, window):
    _shown(window)
    geo = _call(window, "crownGeo", 1)
    _call(window, "crownClicked", geo["cx"] + geo["ri"] * 0.5, geo["cy"], False)  # the hollow
    left = _call(window, "crownGeo", -1)
    _call(window, "crownClicked", (left["cx"] + geo["cx"]) / 2, geo["cy"] - geo["R"] * 0.6, False)  # the stem, empty
    assert window.isVisible()
