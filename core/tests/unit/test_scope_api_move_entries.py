from pathlib import Path

from core.scope_api import ScopeApi


def _write_project_marker(root: Path) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")


def _write_templates_config(root: Path, template_name: str) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Templates.md").write_text(f"# Templates\n{template_name}\n", encoding="utf-8")


def _setup_embryo_project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    _write_project_marker(root)
    _write_templates_config(root, "Standard")
    (root / "Templates" / "Standard" / "admin").mkdir(parents=True, exist_ok=True)
    return root


def _setup_nested_embryo_project(tmp_path: Path) -> Path:
    """Project with nested embryos: parent_embryo/child_embryo (e.g. 04_Finanz/Ausgaben)."""
    root = tmp_path / "Project"
    _write_project_marker(root)
    _write_templates_config(root, "Standard")
    (root / "Templates" / "Standard" / "admin").mkdir(parents=True, exist_ok=True)
    # Nested embryo: 04_Finanz and 04_Finanz/Ausgaben
    (root / "Templates" / "Standard" / "04_Finanz").mkdir(parents=True, exist_ok=True)
    (root / "Templates" / "Standard" / "04_Finanz" / "Ausgaben").mkdir(parents=True, exist_ok=True)
    return root


def test_move_entries_reports_moved_and_errors(tmp_path):
    src_root = tmp_path / "src"
    dst_root = tmp_path / "dst"
    src_root.mkdir()
    dst_root.mkdir()

    file_ok = src_root / "one.txt"
    file_ok.write_text("x", encoding="utf-8")
    file_missing = src_root / "missing.txt"
    # pre-create conflicting destination for second file name
    file_conflict = src_root / "two.txt"
    file_conflict.write_text("y", encoding="utf-8")
    (dst_root / "two.txt").write_text("existing", encoding="utf-8")

    api = ScopeApi(str(src_root))
    report = api.move_entries(
        [str(file_ok), str(file_missing), str(file_conflict), str(file_ok)],
        str(dst_root),
    )

    assert any(item["source"].endswith("one.txt") for item in report["moved"])
    assert any(err["reason"] == "source_missing" for err in report["errors"])
    assert any(err["reason"] == "destination_exists" for err in report["errors"])
    assert any(skip["reason"] == "duplicate_source" for skip in report["skipped"])


def test_move_entries_into_own_parent_is_skipped_not_an_error(tmp_path):
    """Dropping a file back into the folder it already lives in is a no-op."""
    folder = tmp_path / "Folder"
    folder.mkdir()
    file_path = folder / "note.txt"
    file_path.write_text("x", encoding="utf-8")

    api = ScopeApi(str(tmp_path))
    report = api.move_entries([str(file_path)], str(folder))

    assert report["errors"] == []
    assert report["moved"] == []
    assert any(skip["reason"] == "already_in_target" for skip in report["skipped"])
    assert file_path.read_text(encoding="utf-8") == "x"


def test_move_entries_rejects_target_inside_source(tmp_path):
    source_dir = tmp_path / "FolderA"
    source_dir.mkdir()
    nested_target = source_dir / "Inner"
    nested_target.mkdir()

    api = ScopeApi(str(tmp_path))
    report = api.move_entries([str(source_dir)], str(nested_target))
    assert report["ok"] is False
    assert any(err["reason"] == "target_inside_source" for err in report["errors"])


def test_move_entry_rejects_target_inside_source(tmp_path):
    source_dir = tmp_path / "FolderA"
    source_dir.mkdir()
    nested_target = source_dir / "Inner"
    nested_target.mkdir()

    api = ScopeApi(str(tmp_path))
    assert api.move_entry(str(source_dir), str(nested_target)) is False


def test_move_entry_materializes_embryo_target_dir(tmp_path):
    root = _setup_embryo_project(tmp_path)
    source = root / "inbox" / "doc.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("x", encoding="utf-8")
    embryo_target = root / "admin"

    api = ScopeApi(str(root))
    ok = api.move_entry(str(source), str(embryo_target))

    assert ok is True
    assert not source.exists()
    assert embryo_target.is_dir()
    assert (embryo_target / "doc.txt").exists()


def test_move_entry_materializes_nested_embryo_target_dir(tmp_path, monkeypatch):
    """Move into unborn subfolder of embryo (e.g. 04_Finanz/Ausgaben) materializes parent and child, file ends up there."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)  # use project's Templates, not test_lab
    root = _setup_nested_embryo_project(tmp_path)
    source = root / "inbox" / "doc.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("content", encoding="utf-8")
    # Target is nested embryo: 04_Finanz (parent embryo) / Ausgaben (child embryo)
    embryo_parent = root / "04_Finanz"
    embryo_child = root / "04_Finanz" / "Ausgaben"

    assert not embryo_parent.exists(), "parent embryo must not exist before move"
    assert not embryo_child.exists(), "child embryo must not exist before move"

    api = ScopeApi(str(root))
    ok = api.move_entry(str(source), str(embryo_child))

    assert ok is True, "move_entry into nested embryo should succeed"
    assert not source.exists(), "source file should be gone"
    assert embryo_parent.is_dir(), "parent embryo 04_Finanz should be materialized"
    assert embryo_child.is_dir(), "child embryo 04_Finanz/Ausgaben should be materialized"
    assert (embryo_child / "doc.txt").exists(), "file should be in 04_Finanz/Ausgaben"
    assert (embryo_child / "doc.txt").read_text(encoding="utf-8") == "content"


def test_resolve_or_materialize_target_dir_nested_embryo(tmp_path, monkeypatch):
    """_resolve_or_materialize_target_dir for nested embryo path returns resolved dir and materializes both levels."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    target_dir = root / "04_Finanz" / "Ausgaben"

    assert not target_dir.exists()

    api = ScopeApi(str(root))
    resolved, reason = api._resolve_or_materialize_target_dir(str(target_dir))

    assert resolved is not None, f"expected resolved path, got reason={reason!r}"
    assert resolved.is_dir()
    assert resolved == target_dir.resolve() or resolved.samefile(target_dir)
    assert (root / "04_Finanz").is_dir()
    assert (root / "04_Finanz" / "Ausgaben").is_dir()


def test_move_entries_materializes_nested_embryo_target_dir(tmp_path, monkeypatch):
    """Move multiple files into nested embryo 04_Finanz/Ausgaben materializes parent and child."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    (root / "inbox").mkdir(parents=True, exist_ok=True)
    (root / "inbox" / "a.txt").write_text("a", encoding="utf-8")
    (root / "inbox" / "b.txt").write_text("b", encoding="utf-8")
    embryo_child = root / "04_Finanz" / "Ausgaben"

    assert not embryo_child.exists()

    api = ScopeApi(str(root))
    report = api.move_entries(
        [str(root / "inbox" / "a.txt"), str(root / "inbox" / "b.txt")],
        str(embryo_child),
    )

    assert report["ok"] is True
    assert len(report["moved"]) == 2
    assert (embryo_child / "a.txt").read_text(encoding="utf-8") == "a"
    assert (embryo_child / "b.txt").read_text(encoding="utf-8") == "b"


def test_move_entries_materializes_embryo_target_dir_for_directory_source(tmp_path):
    root = _setup_embryo_project(tmp_path)
    source_dir = root / "inbox"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "nested.txt").write_text("x", encoding="utf-8")
    embryo_target = root / "admin"

    api = ScopeApi(str(root))
    report = api.move_entries([str(source_dir)], str(embryo_target))

    assert report["ok"] is True
    assert source_dir.exists() is False
    assert embryo_target.is_dir()
    assert (embryo_target / "inbox" / "nested.txt").exists()


def test_move_entry_rejects_non_embryo_missing_target(tmp_path):
    root = _setup_embryo_project(tmp_path)
    source = root / "inbox" / "doc.txt"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("x", encoding="utf-8")
    missing_target = root / "not_an_embryo"

    api = ScopeApi(str(root))
    ok = api.move_entry(str(source), str(missing_target))

    assert ok is False
    assert source.exists()
    assert not missing_target.exists()


def test_delete_entries_reports_missing_and_ignores_duplicate(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    doomed = root / "gone.txt"
    doomed.write_text("x", encoding="utf-8")
    missing = root / "missing.txt"

    api = ScopeApi(str(root))
    report = api.delete_entries([str(doomed), str(missing), str(doomed)])

    assert report["ok"] is False
    assert report["deleted"] == [str(doomed)]
    assert len(report["errors"]) == 1
    assert report["errors"][0]["reason"] == "missing"


def test_move_entries_into_sub_embryo_of_born_folder(tmp_path, monkeypatch):
    """Parent already born, child still an embryo: the drop births just the child."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    (root / "Templates" / "Standard" / "04_Finanz" / "Einnahmen").mkdir(parents=True, exist_ok=True)
    (root / "inbox").mkdir()
    (root / "inbox" / "a.txt").write_text("a", encoding="utf-8")
    (root / "inbox" / "b.txt").write_text("b", encoding="utf-8")
    api = ScopeApi(str(root))
    first = api.move_entries([str(root / "inbox" / "a.txt")], str(root / "04_Finanz"))
    assert first["ok"] is True

    report = api.move_entries([str(root / "inbox" / "b.txt")], str(root / "04_Finanz" / "Einnahmen"))

    assert report["ok"] is True, report
    assert (root / "04_Finanz" / "Einnahmen" / "b.txt").read_text(encoding="utf-8") == "b"
    assert not (root / "04_Finanz" / "Ausgaben").exists()


def _born_chain_with_file(tmp_path, monkeypatch):
    """04_Finanz/Ausgaben born by dropping a.txt into it; returns (api, root, file)."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    (root / "inbox").mkdir()
    (root / "inbox" / "a.txt").write_text("a", encoding="utf-8")
    api = ScopeApi(str(root))
    child = root / "04_Finanz" / "Ausgaben"
    assert api.move_entries([str(root / "inbox" / "a.txt")], str(child))["ok"] is True
    return api, root, child / "a.txt"


def test_moving_last_file_out_turns_born_chain_back_into_embryos(tmp_path, monkeypatch):
    api, root, moved_file = _born_chain_with_file(tmp_path, monkeypatch)

    report = api.move_entries([str(moved_file)], str(root / "inbox"))

    assert report["ok"] is True
    assert (root / "inbox" / "a.txt").is_file()
    assert not (root / "04_Finanz").exists()
    assert report["reabsorbed"] == [str(root / "04_Finanz" / "Ausgaben"), str(root / "04_Finanz")]
    assert api.blueprint.is_embryo("04_Finanz/Ausgaben") is True


def test_deleting_last_file_turns_born_chain_back_into_embryos(tmp_path, monkeypatch):
    api, root, born_file = _born_chain_with_file(tmp_path, monkeypatch)

    report = api.delete_entries([str(born_file)])

    assert report["ok"] is True
    assert not (root / "04_Finanz").exists()
    assert report["reabsorbed"] == [str(root / "04_Finanz" / "Ausgaben"), str(root / "04_Finanz")]


def test_move_entry_single_also_reabsorbs(tmp_path, monkeypatch):
    api, root, born_file = _born_chain_with_file(tmp_path, monkeypatch)

    assert api.move_entry(str(born_file), str(root / "inbox")) is True

    assert not (root / "04_Finanz").exists()


def test_emptied_user_folder_is_kept(tmp_path, monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    (root / "Privat").mkdir()
    (root / "Privat" / "a.txt").write_text("a", encoding="utf-8")
    api = ScopeApi(str(root))

    report = api.delete_entries([str(root / "Privat" / "a.txt")])

    assert report["ok"] is True
    assert (root / "Privat").is_dir()
    assert report["reabsorbed"] == []


def test_navigating_into_nested_embryo_does_not_birth_but_drop_does(tmp_path, monkeypatch):
    """Browsing into an embryo and its sub-embryo is read-only; dropping files there births the chain only."""
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    root = _setup_nested_embryo_project(tmp_path)
    (root / "Templates" / "Standard" / "04_Finanz" / "Einnahmen").mkdir(parents=True, exist_ok=True)
    parent = root / "04_Finanz"
    child = parent / "Ausgaben"
    api = ScopeApi(str(root))

    for path in (parent, child):
        api.list_children(str(path), True)
        api.list_entries(str(path))
        api.list_entries_filtered(str(path), [], False)
        api.list_tag_buckets(str(path))
    assert not parent.exists(), "navigation must not birth the embryo"

    (root / "inbox").mkdir()
    (root / "inbox" / "a.txt").write_text("a", encoding="utf-8")
    report = api.move_entries([str(root / "inbox" / "a.txt")], str(child))

    assert report["ok"] is True
    assert (child / "a.txt").read_text(encoding="utf-8") == "a"
    assert not (parent / "Einnahmen").exists(), "siblings stay embryos"
