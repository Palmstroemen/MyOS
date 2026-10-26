"""Scope's top bar is being emptied (Scope/Designdocument Setup.md, step 4): light/dark and the
language are on the back already, the two rows are switched there, and what slipped in from
development (files 50 %, give project a theme, enable sorting) is gone; narrow mode is gone, the
filter moved to the back, the edge-dock switch waits for the Headline."""

from pathlib import Path

MAIN = (Path(__file__).resolve().parents[1] / "main.qml").read_text(encoding="utf-8")


def test_gone_from_the_top_bar():
    for gone in ('qsTr("Files 50%")', 'qsTr("Give project a theme")', 'qsTr("Enable sorting")',
                 "// Theme Switch", "// Language toggle", "// Projects browser visibility toggle",
                 "// Templates browser visibility toggle", "filesPanelHalfTransparent",
                 "// Filter toggle", "// Schmal-Modus", "schmalMode", "Rectangle { // Edge-Dock"):
        assert gone not in MAIN, gone


def compile_errors(source: Path) -> str:
    """What Qt says compiling a QML file ("" when it compiles)."""
    import os
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlEngine()
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(source)))
    return component.errorString() if component.isError() else ""


def test_main_qml_compiles():
    # Taking things out of main.qml can leave it broken (an "else" without its "if" did);
    # the smoke test fails for older reasons and so would not tell.
    assert compile_errors(Path(__file__).resolve().parents[1] / "main.qml") == ""


def test_a_broken_main_qml_is_told(tmp_path):
    broken = Path(__file__).resolve().parents[1] / "zz_broken_test.qml"
    text = (Path(__file__).resolve().parents[1] / "main.qml").read_text(encoding="utf-8")
    broken.write_text(text.replace("    onEdgeDockStateChanged: {", "    onEdgeDockStateChanged: {\n        else show_FilesPanel()", 1),
                      encoding="utf-8")
    try:
        assert compile_errors(broken) != ""
    finally:
        broken.unlink()


def test_setup_stands_left_of_m():
    assert MAIN.index("Rectangle { // Setup: the back of Scope") < MAIN.index("Rectangle { // Minimal view (M)")  # far left


def test_the_flip_turns_the_other_way_both_ways():
    # One swing turns the panel through: to the back and back again in the same sense.
    flip = MAIN[MAIN.index("id: setupFlipAnimation"):MAIN.index("function flipSetup(toBack)")]
    assert "from: 0; to: -90" in flip and "from: 90; to: 0" in flip
    assert "toBack ?" not in flip  # no direction of its own for the way back


def test_choosing_a_filter_by_hand_is_gone():
    # A step on the way (E6): the lens comes by a double click on the MyOS folder; filters
    # still work by themselves (auto), without a menu (Designdocument Perspective Resolver MVP.md).
    scope = (Path(__file__).resolve().parents[1] / "Scope.py").read_text(encoding="utf-8")
    page = (Path(__file__).resolve().parents[1] / "SetupPage.qml").read_text(encoding="utf-8")
    for gone in ("id: filterMenu", "FilterSaveDialog", "FilterNameDialog", "activateFilterPath", "refreshFilters"):
        assert gone not in MAIN, gone
    for gone in ("def setManualFilter", "def clearManualFilter", "def saveFilter", "def listFilterSaveTargets", "_filter_lens"):
        assert gone not in scope, gone
    assert "openFilterMenu" not in page and "setupFilter" not in page


def test_scope_follows_the_embryo_setting():
    assert "embryoOpacity: 0.4" not in MAIN  # no fixed value any more
    assert MAIN.count("embryoOpacity: window.embryoOpacity") >= 3  # both rows and the files


def test_the_rows_make_the_badges_of_suggestions_pale():
    browser = (Path(__file__).resolve().parents[1] / "FolderBrowser.qml").read_text(encoding="utf-8")
    assert browser.count("badgeOpacity: root.itemIsEmbryo(modelData) ? root.embryoBadgeOpacity : 1.0") >= 5
    assert MAIN.count("embryoBadgeOpacity: window.embryoBadgeOpacity") == 2


def test_path_bar_and_preview_left_the_menus_for_the_back():
    browser = (Path(__file__).resolve().parents[1] / "FolderBrowser.qml").read_text(encoding="utf-8")
    for gone in ('qsTr("P Path bar")', 'qsTr("Preview background")', 'text: qsTr("Preview")'):
        assert gone not in browser, gone
    assert MAIN.count("previewEnabled: setupPage.previewOn") == 2
    assert MAIN.count("previewShowBackground: setupPage.previewBackgroundOn") == 2
    assert "usePathBar: !window.minimalView && setupPage.pathBarOn" in MAIN
    assert "usePathBar: window.minimalView || setupPage.pathBarOn" in MAIN


def test_the_projects_browser_offers_no_myos_suggestions():
    # MyOS folders are only on the left (Perspective Resolver MVP, A3.9); suggestions are MyOS
    # folders, so the projects browser could never show them.
    projects = MAIN[MAIN.index("id: projectsBrowser"):]
    projects = projects[:projects.index("onNavigationRequested")]
    assert "showEmbryos: false" in projects


def test_no_display_menu_any_more():
    browser = (Path(__file__).resolve().parents[1] / "FolderBrowser.qml").read_text(encoding="utf-8")
    for gone in ('qsTr("T Text")', 'qsTr("Instant reopen")', 'qsTr("Tuning: Soft")', "horizontalDisplayMenu", "verticalDisplayMenu"):
        assert gone not in browser, gone
    assert "visible: projectsBrowserVisible || window.minimalView" in MAIN  # M keeps its CWD button
