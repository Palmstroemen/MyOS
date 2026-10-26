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
