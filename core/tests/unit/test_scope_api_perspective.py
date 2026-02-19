from pathlib import Path

from core.scope_api import ScopeApi


def _write_project_marker(root: Path) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")


def _write_perspective(path: Path, name: str, extra: str = "") -> None:
    body = "# Perspective\n" + f"Name: {name}\n"
    if extra:
        body += "\n" + extra.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_scope_api_lists_and_resolves_perspectives(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_project_marker(root)
    _write_perspective(root / ".MyOS" / "Perspectives" / "Finance.md", "Finance")
    _write_perspective(sub / "Perspective.md", "Sub")

    api = ScopeApi(str(sub))
    listed = api.list_perspectives(str(sub))
    names = [str(item.get("name") or "") for item in listed]
    assert names[0] == "Sub"
    assert "Finance" in names

    resolved_auto = api.resolve_active_perspective(str(sub))
    assert resolved_auto.get("active") is True
    assert resolved_auto.get("name") == "Sub"
    assert resolved_auto.get("mode") == "auto"
    assert len(resolved_auto.get("chain") or []) >= 1

    manual_path = str(root / ".MyOS" / "Perspectives" / "Finance.md")
    assert api.set_manual_perspective(manual_path) is True
    resolved_manual = api.resolve_active_perspective(str(sub))
    assert resolved_manual.get("active") is True
    assert resolved_manual.get("name") == "Finance"
    assert resolved_manual.get("mode") == "manual"

    assert api.clear_manual_perspective() is True
    resolved_cleared = api.resolve_active_perspective(str(sub))
    assert resolved_cleared.get("name") == "Sub"


def test_scope_api_applies_perspective_projection_to_entries(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_project_marker(root)
    _write_perspective(
        sub / "Perspective.md",
        "OnlyText",
        extra="## Filter\n*.txt\n",
    )
    (sub / "keep.txt").write_text("ok", encoding="utf-8")
    (sub / "drop.jpg").write_text("x", encoding="utf-8")

    api = ScopeApi(str(sub))
    entries = api.list_entries(str(sub))
    names = [str(item.get("name") or "") for item in entries]
    assert "keep.txt" in names
    assert "drop.jpg" not in names


def test_scope_api_perspective_save_targets_and_copy(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_project_marker(root)
    source = sub / "Perspective.md"
    _write_perspective(source, "Source")

    api = ScopeApi(str(sub))
    targets = api.list_perspective_save_targets(str(sub), str(source))
    ids = [str(item.get("id") or "") for item in targets]
    assert "project_local" in ids
    assert "source_scope" in ids
    assert "new_named" in ids

    result = api.save_perspective(str(sub), str(source), "new_named", "InvoiceFocus")
    assert result.get("ok") is True
    saved = Path(str(result.get("path") or ""))
    assert saved.exists()
    assert saved.name == "InvoiceFocus.md"
