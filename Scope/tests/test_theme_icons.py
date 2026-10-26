"""Scope's folder icons follow the system theme (image://theme/...): projects too, unless a
project chooses an icon of its own (Desk.md "projectIcon"); a project shows itself by its
colour and the P badge, not by an icon of Scope's own."""

from pathlib import Path

SCOPE_DIR = Path(__file__).resolve().parents[1]
MAIN = (SCOPE_DIR / "main.qml").read_text(encoding="utf-8")
SETUP = (SCOPE_DIR / "SetupPage.qml").read_text(encoding="utf-8")
SCOPE_PY = (SCOPE_DIR / "Scope.py").read_text(encoding="utf-8")


def test_projects_without_an_own_icon_get_the_themes_folder():
    body = MAIN[MAIN.index("function projectIconForPath(path)"):]
    body = body[:body.index("\n    }\n")]
    # No icon of Scope's own: "" lets FolderBrowser fall back to image://theme/folder.
    assert "Theme/icons" not in body and "Fallback" not in body
    assert "Theme/icons/project.svg" not in MAIN
    assert not (SCOPE_DIR / "Theme" / "icons" / "project.svg").exists()


def test_the_setup_examples_show_the_themes_folder():
    assert "Theme/icons/folder.svg" not in SETUP
    assert SETUP.count('iconSource: "image://theme/folder"') == 3


def test_the_window_icon_comes_from_the_theme():
    assert "with_project_badge(QIcon.fromTheme(\"folder\"" in SCOPE_PY


def test_the_window_icon_is_the_themes_folder_with_the_project_p():
    # In the taskbar Scope is told apart from the file browser by the P its projects carry.
    import os

    from PySide6.QtGui import QGuiApplication, QIcon

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    import sys
    sys.path.insert(0, str(SCOPE_DIR))
    from window_icon import with_project_badge

    folder = QIcon(str(SCOPE_DIR / "Theme" / "icons" / "folder.svg"))
    icon = with_project_badge(folder)
    plain = folder.pixmap(64, 64).toImage()
    marked = icon.pixmap(64, 64).toImage()
    assert marked.width() == 64 and plain.width() == 64

    def dark(image, x0, x1, y0, y1):
        return sum(1 for x in range(x0, x1) for y in range(y0, y1) if image.pixelColor(x, y).value() < 60
                   and image.pixelColor(x, y).alpha() > 200)

    # The P: dark pixels in the lower half, right of centre - none there before.
    assert dark(plain, 32, 56, 30, plain.height()) == 0 and dark(marked, 32, 56, 30, 60) > 20
    assert dark(marked, 0, 20, 0, 20) == 0  # the folder elsewhere as it was
    assert not icon.availableSizes() or 16 in [s.width() for s in icon.availableSizes()]


def test_on_a_hidpi_screen_the_small_sizes_stay_whole():
    # On a screen at factor 2 an icon asked for 24 px without a factor answers 48 px pixels
    # (ratio 2): the P icon asks at factor 1, else it crops the folder.
    import os

    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QGuiApplication, QPixmap

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    import sys
    sys.path.insert(0, str(SCOPE_DIR))
    from window_icon import with_project_badge

    class HiDpiIcon:
        def isNull(self):
            return False

        def pixmap(self, *args):
            explicit = len(args) >= 2 and isinstance(args[0], QSize) and float(args[1]) == 1.0
            side = args[0].width() if isinstance(args[0], QSize) else args[0]
            pixmap = QPixmap(side if explicit else side * 2, side if explicit else side * 2)
            pixmap.fill(Qt.yellow)
            if not explicit:
                pixmap.setDevicePixelRatio(2.0)
            return pixmap

    small = with_project_badge(HiDpiIcon()).pixmap(24, 24).toImage()
    corner = small.pixelColor(22, 2)  # top right: away from the P, lost when cropped
    assert small.width() == 24 and corner.alpha() > 200 and corner.red() > 200 and corner.blue() < 60
