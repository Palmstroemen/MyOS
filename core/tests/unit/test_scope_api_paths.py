from core.scope_api import ScopeApi


def test_create_folder_and_note_require_directory_base(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    file_base = root / "base.txt"
    file_base.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.create_folder(str(file_base), "Child") is None
    assert api.create_note(str(file_base), "Note") is None


def test_list_methods_return_empty_for_non_directory_targets(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    file_target = root / "entry.md"
    file_target.write_text("# x\n", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.list_entries(str(file_target)) == []
    assert api.list_children(str(file_target)) == []


def test_is_helpers_on_missing_path_are_false(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    missing = root / "does-not-exist"

    api = ScopeApi(str(root))
    assert api.is_dir(str(missing)) is False
    assert api.is_project(str(missing)) is False
    assert api.has_myos_dir(str(missing)) is False

