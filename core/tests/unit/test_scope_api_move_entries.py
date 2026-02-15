from core.scope_api import ScopeApi


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
