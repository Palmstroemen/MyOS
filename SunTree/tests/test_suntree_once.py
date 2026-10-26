"""One action, then gone (SunTree/Designdocument Krone.md): after a drop, a double click or
the lens SunTree puts itself away; a drop leaves a notice that can undo it."""

from pathlib import Path

from PySide6.QtGui import QCursor, QGuiApplication, QWindow
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from SunTree.tests.test_suntree_crown import _call, _dive, _prop, suntree, window, world  # noqa: F401

RULE = "# Sort\nPattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 2\n"


def _incoming(tmp_path, name="Rechnung.pdf"):
    downloads = tmp_path / "Downloads"
    downloads.mkdir(exist_ok=True)
    source = downloads / name
    source.write_text("x")
    return source


def _shown(window):
    # The crown tests put the real pointer (QCursor.setPos); away with it, or a half takes it
    # as soon as the window shows.
    QCursor.setPos(-200, -200)
    window.show()
    QGuiApplication.instance().processEvents()


def _notice(window):
    return window.findChild(QWindow, "dropNotice")


# --- the backend: a drop and its undo ----------------------------------------------------

def test_a_drop_is_reported_and_can_be_undone(world, suntree, tmp_path):
    source = _incoming(tmp_path)
    target = world["noten"] / "2025"

    done = suntree.dropFiles([str(source)], str(target))

    assert done["count"] == 1 and done["place"] == str(target)
    assert (target / "Rechnung.pdf").exists() and not source.exists()
    assert suntree.undoDrop()
    assert source.exists() and not (target / "Rechnung.pdf").exists()
    assert not suntree.undoDrop()  # once


def test_undo_finds_a_file_that_was_filed_on(world, suntree, tmp_path):
    belege = world["studio"] / "Belege"
    (belege / ".MyOS").mkdir(parents=True)
    (belege / ".MyOS" / "Sort.md").write_text(RULE)
    for name in ("a 2024-01-01.pdf", "b 2024-02-01.pdf"):  # enough for levels (core/filing.py)
        (belege / name).write_text(name)
    source = _incoming(tmp_path, "c 2025-01-01.pdf")

    done = suntree.dropFiles([str(source)], str(belege))

    assert done["place"] == str(belege / "2025")  # where it lies now
    assert suntree.undoDrop() and source.exists()


def test_undo_brings_back_a_folder_the_drop_emptied(world, suntree, tmp_path):
    ausgaben = world["studio"] / "04_Finanz" / "Ausgaben"
    ausgaben.mkdir(parents=True)
    (ausgaben / "Quittung.pdf").write_text("x")

    suntree.dropFiles([str(ausgaben / "Quittung.pdf")], str(world["noten"]))
    assert not ausgaben.exists()  # emptied, an embryo again

    assert suntree.undoDrop()
    assert (ausgaben / "Quittung.pdf").exists()  # born again by it


# --- the window ----------------------------------------------------------------------------

def test_a_drop_puts_suntree_away_and_leaves_a_notice(world, window, tmp_path):
    _shown(window)
    source = _incoming(tmp_path)
    geo = _call(window, "crownGeo", 1)
    _dive(window, 2 * (geo["T"] - geo["ri"]) + 20)
    target = Path(_call(window, "crownHit")["row"]["path"])

    assert _call(window, "crownDropUrls", ["file://" + str(source)])

    assert not window.isVisible()
    notice = _notice(window)
    assert notice.isVisible() and target.name in notice.property("text")
    QTest.qWait(100)
    drawn = notice.findChildren(QQuickItem)[0]  # its own window: laid out though SunTree's went
    assert drawn.width() == notice.width() > 100
    _call(window, "noticeUndo")
    assert source.exists() and not notice.isVisible()


def test_a_single_click_goes_in_a_double_click_also_away(world, suntree, window):
    _shown(window)
    _dive(window, 5)  # Noten under the pointer
    at = _prop(window, "crownPointer")
    _call(window, "crownClicked", at["x"], at["y"], False)
    assert suntree.cwd() == str(world["noten"]) and window.isVisible()  # to look further

    _call(window, "crownClicked", at["x"], at["y"], True)
    assert suntree.cwd() == str(world["noten"]) and not window.isVisible()


def test_putting_on_a_lens_and_taking_it_off_put_suntree_away(world, suntree, window):
    _shown(window)
    geo = _call(window, "crownGeo", -1)
    _call(window, "handMoved", geo["cx"] - geo["ri"] - 5, geo["cy"])  # the left half: 04_Finanz
    at = _prop(window, "crownPointer")
    _call(window, "crownClicked", at["x"], at["y"], True)
    assert _prop(window, "lensOn") and not window.isVisible()

    _shown(window)
    _call(window, "takeOffLens")
    assert not _prop(window, "lensOn") and not window.isVisible()


# --- appearing under the pointer -------------------------------------------------------------

def _pointer_at(suntree, x, y, screen=(0, 0, 3000, 2000)):
    suntree._where = lambda: {"x": x, "y": y, "sx": screen[0], "sy": screen[1], "sw": screen[2], "sh": screen[3]}


def test_the_backend_knows_where_the_pointer_is(suntree):
    QCursor.setPos(40, 30)
    where = suntree.pointerAt()
    assert (where["x"], where["y"]) == (40, 30) and where["sw"] > 0 and where["sh"] > 0


def test_suntree_appears_with_the_stem_under_the_pointer(world, suntree, window):
    _pointer_at(suntree, 1500, 1000)
    _call(window, "toggleFromHotkey")
    QGuiApplication.instance().processEvents()

    stem = _call(window, "stemCentre")  # in the window
    assert (window.x() + stem["x"], window.y() + stem["y"]) == (1500, 1000)


def test_the_pointer_glides_to_its_new_place(suntree):
    _pointer_at(suntree, 0, 0)
    put = []
    suntree.pointerTo = lambda x, y: put.append((x, y))
    done = []
    suntree.pointerGlideDone.connect(lambda: done.append(True))

    suntree.glidePointerTo(300, 200, 350)
    QTest.qWait(500)

    assert put[-1] == (300, 200) and done
    assert len(put) >= 10  # a ride the eye can follow, not a jump
    distances = [abs(300 - x) + abs(200 - y) for x, y in put]
    assert distances == sorted(distances, reverse=True)  # straight towards it


def test_at_the_screen_edge_it_stays_whole_and_pulls_the_pointer_to_the_stem(world, suntree, window):
    # A screen just as big as SunTree: it stays at (0, 0), and the pointer, near the edge,
    # rides into the middle of the stem - as the crown pulls it anyway. SunTree shows only
    # when it is there: nothing else holds the ride up, so the eye can follow it.
    _pointer_at(suntree, 30, 40, screen=(0, 0, window.width(), window.height()))
    _call(window, "toggleFromHotkey")
    assert _prop(window, "pointerGliding") and not window.isVisible()

    QTest.qWait(600)
    stem = _call(window, "stemCentre")
    assert suntree.lastPointer() == {"x": round(stem["x"]), "y": round(stem["y"])}
    assert window.isVisible() and (window.x(), window.y()) == (0, 0)
    assert not _prop(window, "pointerGliding")


def test_under_the_pointer_it_is_not_pulled(world, suntree, window):
    _pointer_at(suntree, 1500, 1000)
    _call(window, "toggleFromHotkey")
    assert window.isVisible()  # at once
    QTest.qWait(300)
    assert suntree.lastPointer() == {"x": 0, "y": 0}  # never put


def test_going_away_brings_the_pointer_back_where_it_was_picked_up(world, suntree, window):
    _pointer_at(suntree, 30, 40, screen=(0, 0, window.width(), window.height()))
    _call(window, "toggleFromHotkey")
    QTest.qWait(600)  # rode into the stem, SunTree shows
    assert window.isVisible() and suntree.lastPointer() != {"x": 30, "y": 40}

    _pointer_at(suntree, 700, 300, screen=(0, 0, window.width(), window.height()))  # the crown moved it
    _call(window, "putAway")
    QTest.qWait(600)
    assert not window.isVisible() and suntree.lastPointer() == {"x": 30, "y": 40}


def test_the_red_x_brings_the_pointer_back_too_then_quits(world, suntree, window):
    from PySide6.QtQml import qmlEngine

    quits = []
    qmlEngine(window).quit.connect(lambda: quits.append(True))
    _pointer_at(suntree, 30, 40, screen=(0, 0, window.width(), window.height()))
    _call(window, "toggleFromHotkey")
    QTest.qWait(600)

    _call(window, "quitForGood")
    assert not window.isVisible() and not quits  # first the ride back
    QTest.qWait(600)
    assert suntree.lastPointer() == {"x": 30, "y": 40} and quits
