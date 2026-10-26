from pathlib import Path

from core.scope_api import ScopeApi


def _write_project_marker(root: Path) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")


def _write_filter(path: Path, name: str, extra: str = "") -> None:
    body = "# Filter\n" + f"Name: {name}\n"
    if extra:
        body += "\n" + extra.strip() + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_scope_api_lists_and_resolves_filters(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_project_marker(root)
    _write_filter(root / ".MyOS" / "Filters" / "Finance.md", "Finance")
    _write_filter(sub / "Filter.md", "Sub")

    api = ScopeApi(str(sub))
    listed = api.list_filters(str(sub))
    names = [str(item.get("name") or "") for item in listed]
    assert names[0] == "Sub"
    assert "Finance" in names

    resolved_auto = api.resolve_active_filter(str(sub))
    assert resolved_auto.get("active") is True
    assert resolved_auto.get("name") == "Sub"
    assert resolved_auto.get("mode") == "auto"
    assert len(resolved_auto.get("chain") or []) >= 1


def test_scope_api_applies_filter_projection_to_entries(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_project_marker(root)
    _write_filter(
        sub / "Filter.md",
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


def test_no_filter_chosen_by_hand_nor_saved_from_scope():
    # Choosing a filter by hand (it put on its lens) and saving one were steps on the way;
    # auto filters stay (above).
    for gone in ("set_manual_filter", "clear_manual_filter", "manual_filter_lens", "save_filter", "list_filter_save_targets"):
        assert not hasattr(ScopeApi, gone), gone
