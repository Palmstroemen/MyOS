"""
Targeted tests for navigation above/outside MyOS root.
Reproduces issues with /MyOS/ and /Dateien/ folders when navigating from /Projekte/.
"""
from pathlib import Path

import pytest

from core.scope_api import ScopeApi, find_project_root, find_top_project_root


def _setup_myos_test_structure(tmp_path: Path) -> dict:
    """Create MyOS_Test/Projekte/MyOS/Dateien structure."""
    myos_test = tmp_path / "MyOS_Test"
    myos_test.mkdir()
    (myos_test / ".MyOS").mkdir()
    (myos_test / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")

    projekte = myos_test / "Projekte"
    projekte.mkdir()
    haus = projekte / "Haus"
    haus.mkdir()

    myos_folder = myos_test / "MyOS"  # folder named MyOS (sibling of Projekte)
    myos_folder.mkdir()

    dateien = myos_test / "Dateien"
    dateien.mkdir()

    return {
        "myos_test": myos_test,
        "projekte": projekte,
        "haus": haus,
        "myos_folder": myos_folder,
        "dateien": dateien,
    }


def test_list_children_at_myos_test_root_includes_myos_and_dateien(tmp_path):
    """list_children(MyOS_Test) must include MyOS and Dateien folders."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))  # start from Projekte/Haus

    children = api.list_children(str(paths["myos_test"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "MyOS" in names, f"Expected MyOS in list_children result, got: {names}"
    assert "Dateien" in names, f"Expected Dateien in list_children result, got: {names}"
    assert "Projekte" in names, f"Expected Projekte in list_children result, got: {names}"


def test_list_children_at_projekte_includes_subfolders(tmp_path):
    """list_children(Projekte) must include Haus and siblings."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["projekte"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "Haus" in names, f"Expected Haus in list_children result, got: {names}"


def test_list_children_myos_folder_as_target(tmp_path):
    """list_children(MyOS_Test/MyOS) must work - folder named MyOS."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["myos_folder"]), include_embryos=True)
    # Should return list (possibly empty if no children), not raise
    assert isinstance(children, list)


def test_list_children_dateien_folder_as_target(tmp_path):
    """list_children(MyOS_Test/Dateien) must work."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    children = api.list_children(str(paths["dateien"]), include_embryos=True)
    assert isinstance(children, list)


def test_find_project_root_for_myos_folder(tmp_path):
    """find_project_root(MyOS_Test/MyOS) must find MyOS_Test."""
    paths = _setup_myos_test_structure(tmp_path)

    root = find_project_root(paths["myos_folder"])
    assert root is not None, "find_project_root must find MyOS_Test for MyOS folder"
    assert root == paths["myos_test"]


def test_find_project_root_for_dateien_folder(tmp_path):
    """find_project_root(MyOS_Test/Dateien) must find MyOS_Test."""
    paths = _setup_myos_test_structure(tmp_path)

    root = find_project_root(paths["dateien"])
    assert root is not None
    assert root == paths["myos_test"]


def test_update_context_to_myos_folder(tmp_path):
    """update_context(MyOS_Test/MyOS) must not raise and must update project_root."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    api.update_context(str(paths["myos_folder"]))
    root = api.get_project_root()
    assert root is not None, "project_root must be set after update_context to MyOS folder"


def test_update_context_to_myos_test_root(tmp_path):
    """update_context(MyOS_Test) must work when navigating above Projekte."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["haus"]))

    api.update_context(str(paths["myos_test"]))
    root = api.get_project_root()
    assert root is not None


def test_list_children_above_project_root(tmp_path):
    """When start_path is in Projekte, list_children(MyOS_Test) must work."""
    paths = _setup_myos_test_structure(tmp_path)
    api = ScopeApi(str(paths["projekte"]))  # start from Projekte

    children = api.list_children(str(paths["myos_test"]), include_embryos=True)
    names = [c["name"] for c in children]

    assert "MyOS" in names
    assert "Dateien" in names


def test_list_children_path_above_myos_root_still_lists_real_dirs(tmp_path):
    """Paths above MyOS root - list_children should still list real dirs (no filter)."""
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()

    myos_test = tmp_path / "MyOS_Test"
    myos_test.mkdir()
    (myos_test / ".MyOS").mkdir()
    (myos_test / ".MyOS" / "Project.md").write_text("# Project\n", encoding="utf-8")

    api = ScopeApi(str(myos_test))

    # parent is above MyOS root - no .MyOS in ancestors; context_root will be None
    # list_children must still return real directory contents
    children = api.list_children(str(parent), include_embryos=True)
    names = [c["name"] for c in children]

    assert "child" in names, f"Expected child when listing parent above MyOS root, got: {names}"
