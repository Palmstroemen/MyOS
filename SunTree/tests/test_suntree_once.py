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
