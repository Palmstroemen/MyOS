from core.scope_api import ScopeApi


def test_rename_entry_keeps_extension_for_files(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    source = root / "note.md"
    source.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    renamed = api.rename_entry(str(source), "renamed")

    assert renamed is not None
    assert renamed.endswith("renamed.md")
    assert not source.exists()
    assert (root / "renamed.md").exists()


def test_rename_entry_rejects_existing_target(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    source = root / "a.txt"
    source.write_text("a", encoding="utf-8")
    (root / "b.txt").write_text("b", encoding="utf-8")

    api = ScopeApi(str(root))
    renamed = api.rename_entry(str(source), "b.txt")

    assert renamed is None
    assert source.exists()


def test_rename_entries_batch_reports_unchanged_renamed_and_failed(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    src_1 = root / "img004.jpg"
    src_2 = root / "img005.jpg"
    src_3 = root / "note.txt"
    src_1.write_text("1", encoding="utf-8")
    src_2.write_text("2", encoding="utf-8")
    src_3.write_text("3", encoding="utf-8")
    (root / "foto005.jpg").write_text("conflict", encoding="utf-8")

    api = ScopeApi(str(root))
    report = api.rename_entries_batch(
        [str(src_1), str(src_2), str(src_3), str(root / "missing.jpg")],
        "img",
        "foto",
    )

    assert any(path.endswith("foto004.jpg") for path in report["renamed"])
    # second file must use fallback suffix because foto005.jpg already exists
    assert any(path.endswith("foto005(1).jpg") for path in report["renamed"])
    assert report["unchanged"] == 1  # note.txt does not contain "img"
    assert report["failed"] == 1  # missing.jpg
    assert any(err["reason"] == "source_missing" for err in report["errors"])


def test_rename_entries_batch_requires_nonempty_replace_from(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    source = root / "a.txt"
    source.write_text("a", encoding="utf-8")

    api = ScopeApi(str(root))
    report = api.rename_entries_batch([str(source)], "", "x")

    assert report["ok"] is False
    assert report["renamed"] == []
    assert report["failed"] == 0
    assert any(err["reason"] == "missing_replace_from" for err in report["errors"])


def test_rename_entries_batch_ignores_duplicate_sources(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    source = root / "img100.jpg"
    source.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    report = api.rename_entries_batch([str(source), str(source)], "img", "foto")

    assert report["ok"] is True
    assert report["failed"] == 0
    assert report["unchanged"] == 0
    assert len(report["renamed"]) == 1
    assert report["renamed"][0].endswith("foto100.jpg")


def test_suggest_batch_rename_token_trims_numeric_tail(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    p1 = root / "img004.jpg"
    p2 = root / "img005.jpg"
    p1.write_text("1", encoding="utf-8")
    p2.write_text("2", encoding="utf-8")

    api = ScopeApi(str(root))
    token = api.suggest_batch_rename_token([str(p1), str(p2)])

    assert token == "img"


def test_create_folder_rejects_invalid_names(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    api = ScopeApi(str(root))

    assert api.create_folder(str(root), "") is None
    assert api.create_folder(str(root), " ") is None
    assert api.create_folder(str(root), ".") is None
    assert api.create_folder(str(root), "..") is None
    assert api.create_folder(str(root), "a/b") is None
    assert api.create_folder(str(root), "a\\b") is None


def test_create_note_rejects_invalid_names_but_accepts_default(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    api = ScopeApi(str(root))

    assert api.create_note(str(root), ".") is None
    assert api.create_note(str(root), "..") is None
    assert api.create_note(str(root), "a/b") is None
    assert api.create_note(str(root), "a\\b") is None

    created = api.create_note(str(root), "")
    assert created is not None
    assert created.endswith("New Note.md")
    assert (root / "New Note.md").exists()

