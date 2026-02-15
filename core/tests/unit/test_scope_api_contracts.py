from core.scope_api import ScopeApi


def test_move_entries_contract_has_stable_keys(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    src = root / "a.txt"
    src.write_text("a", encoding="utf-8")
    dst = root / "dst"
    dst.mkdir()

    api = ScopeApi(str(root))
    report = api.move_entries([str(src)], str(dst))

    assert set(report.keys()) == {"ok", "moved", "skipped", "errors"}
    assert isinstance(report["ok"], bool)
    assert isinstance(report["moved"], list)
    assert isinstance(report["skipped"], list)
    assert isinstance(report["errors"], list)
    assert report["ok"] is True


def test_delete_entries_contract_has_stable_keys(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    src = root / "a.txt"
    src.write_text("a", encoding="utf-8")

    api = ScopeApi(str(root))
    report = api.delete_entries([str(src)])

    assert set(report.keys()) == {"ok", "deleted", "errors"}
    assert isinstance(report["ok"], bool)
    assert isinstance(report["deleted"], list)
    assert isinstance(report["errors"], list)
    assert report["ok"] is True


def test_rename_entries_batch_contract_has_stable_keys(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    src = root / "img1.png"
    src.write_text("a", encoding="utf-8")

    api = ScopeApi(str(root))
    report = api.rename_entries_batch([str(src)], "img", "foto")

    assert set(report.keys()) == {"ok", "renamed", "unchanged", "failed", "errors"}
    assert isinstance(report["ok"], bool)
    assert isinstance(report["renamed"], list)
    assert isinstance(report["unchanged"], int)
    assert isinstance(report["failed"], int)
    assert isinstance(report["errors"], list)
    assert report["ok"] is True

