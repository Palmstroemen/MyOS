"""
Targeted tests for navigation above/outside MyOS root.
Reproduces issues with /MyOS/ and /Dateien/ folders when navigating from /Projekte/.
"""
from pathlib import Path

import pytest

from core.scope_api import ScopeApi, find_project_root, find_top_project_root
from core.brand import META_DIR, NAME


def _setup_test_tree_structure(tmp_path: Path) -> dict:
    """Create Seiton_Test/Projekte/MyOS/Dateien structure."""
    test_tree = tmp_path / f"{NAME}_Test"
    test_tree.mkdir()
    (test_tree / META_DIR).mkdir()
    (test_tree / META_DIR / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")

    projekte = test_tree / "Projekte"
    projekte.mkdir()
    haus = projekte / "Haus"
    haus.mkdir()

    repo_folder = test_tree / "MyOS"  # folder named MyOS (sibling of Projekte)
    repo_folder.mkdir()

    dateien = test_tree / "Dateien"
    dateien.mkdir()

    return {
        "test_tree": test_tree,
        "projekte": projekte,
        "haus": haus,
        "repo_folder": repo_folder,
        "dateien": dateien,
    }


def test_list_children_at_test_tree_root_includes_myos_and_dateien(tmp_path):
    """list_children(Seiton_Test) must include MyOS and Dateien folders."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))  # start from Projekte/Haus

    children = api.list_children(str(paths["test_tree"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "MyOS" in names, f"Expected MyOS in list_children result, got: {names}"
    assert "Dateien" in names, f"Expected Dateien in list_children result, got: {names}"
    assert "Projekte" in names, f"Expected Projekte in list_children result, got: {names}"


def test_list_children_at_projekte_includes_subfolders(tmp_path):
    """list_children(Projekte) must include Haus and siblings."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["projekte"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "Haus" in names, f"Expected Haus in list_children result, got: {names}"


def test_list_children_settings_folder_as_target(tmp_path):
    """list_children(Seiton_Test/MyOS) must work - folder named MyOS."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["repo_folder"]), include_embryos=True)
    # Should return list (possibly empty if no children), not raise
    assert isinstance(children, list)


def test_list_children_dateien_folder_as_target(tmp_path):
    """list_children(Seiton_Test/Dateien) must work."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["dateien"]), include_embryos=True)
    assert isinstance(children, list)


def test_find_project_root_for_settings_folder(tmp_path):
    """find_project_root(Seiton_Test/MyOS) must find Seiton_Test."""
    paths = _setup_test_tree_structure(tmp_path)

    root = find_project_root(paths["repo_folder"])
    assert root is not None, "find_project_root must find Seiton_Test for MyOS folder"
    assert root == paths["test_tree"]


def test_find_project_root_for_dateien_folder(tmp_path):
    """find_project_root(Seiton_Test/Dateien) must find Seiton_Test."""
    paths = _setup_test_tree_structure(tmp_path)

    root = find_project_root(paths["dateien"])
    assert root is not None
    assert root == paths["test_tree"]


def test_update_context_to_settings_folder(tmp_path):
    """update_context(Seiton_Test/MyOS) must not raise and must update project_root."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    api.update_context(str(paths["repo_folder"]))
    root = api.get_project_root()
    assert root is not None, "project_root must be set after update_context to MyOS folder"


def test_update_context_to_test_tree_root(tmp_path):
    """update_context(Seiton_Test) must work when navigating above Projekte."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    api.update_context(str(paths["test_tree"]))
    root = api.get_project_root()
    assert root is not None


def test_list_children_above_project_root(tmp_path):
    """When start_path is in Projekte, list_children(Seiton_Test) must work."""
    paths = _setup_test_tree_structure(tmp_path)
    api = ScopeApi(str(paths["projekte"]))  # start from Projekte

    children = api.list_children(str(paths["test_tree"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "MyOS" in names
    assert "Dateien" in names


def test_list_children_path_above_top_root_still_lists_real_dirs(tmp_path):
    """Paths above MyOS root - list_children should still list real dirs (no filter)."""
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()

    test_tree = tmp_path / f"{NAME}_Test"
    test_tree.mkdir()
    (test_tree / META_DIR).mkdir()
    (test_tree / META_DIR / "Project.md").write_text("# Project\n", encoding="utf-8")

    api = ScopeApi(str(test_tree))

    # parent is above MyOS root - no .MyOS in ancestors; context_root will be None
    # list_children must still return real directory contents
    children = api.list_children(str(parent), include_embryos=True)
    names = [c["name"] for c in children]

    assert "child" in names, f"Expected child when listing parent above MyOS root, got: {names}"
