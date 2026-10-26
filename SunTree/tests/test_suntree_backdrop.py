"""SunTree without a background (SunTree/Designdocument Krone.md, one action then gone): only
the crown and the stem are drawn; a click beside them puts SunTree away (cancelling)."""

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QImage
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


# --- the panel between the halves: what lies behind, blurred and darkened ------------------

def _fake_grab(calls):
    from PySide6.QtGui import QColor

    def grab(x, y, w, h):
        calls.append((x, y, w, h))
        image = QImage(max(1, w), max(1, h), QImage.Format_ARGB32)
        image.fill(QColor("#ffcc00"))
        return image
    return grab


def test_the_backdrop_is_a_snapshot_kept_in_memory(suntree):
    calls = []
    suntree._grab = _fake_grab(calls)

    url = suntree.takeBackdrop(10, 20, 120, 300)

    assert url.startswith("image://backdrop/") and calls == [(10, 20, 120, 300)]
    assert suntree.backdrop.image.width() == 120
    assert suntree.takeBackdrop(10, 20, 120, 300) != url  # a new one each time it shows

    suntree._grab = lambda x, y, w, h: QImage()
    assert suntree.takeBackdrop(0, 0, 10, 10) == ""  # no snapshot (Wayland): only the tint


def test_showing_takes_the_snapshot_behind_the_panel(world, suntree, window):
    from PySide6.QtCore import QPointF

    calls = []
    suntree._grab = _fake_grab(calls)
    QCursor.setPos(-200, -200)
    # the pointer free in the middle of a big screen: SunTree shows at once, under it
    suntree._where = lambda: {"x": 1500, "y": 1000, "sx": 0, "sy": 0, "sw": 3000, "sh": 2000}
    _call(window, "toggleFromHotkey")  # hidden -> shown: the snapshot is taken before
    QGuiApplication.instance().processEvents()

    panel = window.findChild(QQuickItem, "stemPanel")
    left, right = _call(window, "crownGeo", -1), _call(window, "crownGeo", 1)
    assert panel.width() == right["cx"] - left["cx"] and panel.height() > 0  # between the halves
    at = panel.mapToGlobal(QPointF(0, 0))
    assert calls == [(round(at.x()), round(at.y()), round(panel.width()), round(panel.height()))]
    assert panel.property("backdrop").startswith("image://backdrop/")
    tint = window.findChild(QQuickItem, "stemPanelTint")
    assert tint.property("color").alpha() > 0 and tint.property("color").black() == 255
