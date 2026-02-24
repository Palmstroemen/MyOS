from __future__ import annotations

from pathlib import Path


def _main_qml_text() -> str:
    path = Path(__file__).resolve().parents[1] / "main.qml"
    return path.read_text(encoding="utf-8")


def test_main_qml_uses_folder_type_helper_in_both_browser_double_click_handlers():
    text = _main_qml_text()

    assert "function shouldApplyPerspectiveForFolderType(folderMeta)" in text
    assert "onFolderDoubleActivated: function(path, folderMeta)" in text
    assert "onFolderDoubleActivated: function(name, folderMeta)" in text
    assert text.count("shouldApplyPerspectiveForFolderType(folderMeta)") >= 2


def test_main_qml_routes_project_browser_double_click_to_real_path_perspective_apply():
    text = _main_qml_text()

    assert "function applyPerspectiveForRealPath(realPath)" in text
    assert "applyPerspectiveForRealPath(targetPath)" in text
