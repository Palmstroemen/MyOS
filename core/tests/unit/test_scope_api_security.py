from core.scope_api import ScopeApi


def test_name_validation_rejects_control_reserved_and_overlong(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    api = ScopeApi(str(root))
    source = root / "note.md"
    source.write_text("x", encoding="utf-8")

    assert api.create_folder(str(root), "bad\nname") is None
    assert api.create_folder(str(root), "bad|name") is None
    assert api.create_note(str(root), "bad\tname") is None
    assert api.rename_entry(str(source), "bad:name") is None
    assert api.rename_entry(str(source), "a" * 300) is None


def test_batch_operations_report_invalid_path_for_malformed_inputs(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    file_ok = root / "img001.png"
    file_ok.write_text("x", encoding="utf-8")
    invalid = "\x00evil"

    api = ScopeApi(str(root))

    rename_report = api.rename_entries_batch([invalid, str(file_ok)], "img", "foto")
    assert rename_report["failed"] == 1
    assert any(err["reason"] == "invalid_path" for err in rename_report["errors"])
    assert any(path.endswith("foto001.png") for path in rename_report["renamed"])

    delete_report = api.delete_entries([invalid])
    assert delete_report["ok"] is False
    assert any(err["reason"] == "invalid_path" for err in delete_report["errors"])

    dst = root / "dst"
    dst.mkdir()
    move_report = api.move_entries([invalid], str(dst))
    assert move_report["ok"] is False
    assert any(err["reason"] == "invalid_path" for err in move_report["errors"])


def test_open_markdown_rejects_non_markdown_and_missing(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    root.mkdir()
    txt_file = root / "note.txt"
    txt_file.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))

    called = {"n": 0}

    def _fake_run(*args, **kwargs):
        called["n"] += 1
        return None

    monkeypatch.setattr("core.scope_api.subprocess.run", _fake_run)

    assert api.open_markdown(str(txt_file)) is False
    assert api.open_markdown(str(root / "missing.md")) is False
    assert api.open_markdown("\x00evil.md") is False
    assert called["n"] == 0

