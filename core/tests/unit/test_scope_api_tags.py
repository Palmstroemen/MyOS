from pathlib import Path

import core.scope_api as scope_api_module
from core.scope_api import ScopeApi


def test_list_project_tags_reads_hash_lines(tmp_path):
    project = tmp_path / "DemoProject"
    tags_md = project / ".MyOS" / "Tags.md"
    tags_md.parent.mkdir(parents=True)
    tags_md.write_text(
        "\n".join(
            [
                "#alpha",
                "ignored line",
                "#beta",
                "#alpha",
                "##not-a-tag",
            ]
        ),
        encoding="utf-8",
    )

    api = ScopeApi(str(project))
    tags = api.list_project_tags(str(project))

    assert tags == ["alpha", "beta", "not-a-tag"]


def test_list_entries_filtered_supports_or_and_modes(tmp_path, monkeypatch):
    root = tmp_path / "Data"
    root.mkdir()
    a = root / "a.md"
    b = root / "b.md"
    c = root / "c.md"
    a.write_text("a", encoding="utf-8")
    b.write_text("b", encoding="utf-8")
    c.write_text("c", encoding="utf-8")

    tag_map = {
        str(a): {"red": None, "blue": None},
        str(b): {"red": None},
        str(c): {"green": None},
    }

    def fake_read_tags(path: Path):
        return tag_map.get(str(path), {})

    monkeypatch.setattr(scope_api_module, "read_tags", fake_read_tags)

    api = ScopeApi(str(root))
    names_or = sorted(item["name"] for item in api.list_entries_filtered(str(root), ["red", "green"], match_all=False))
    names_and = sorted(item["name"] for item in api.list_entries_filtered(str(root), ["red", "blue"], match_all=True))

    assert names_or == ["a.md", "b.md", "c.md"]
    assert names_and == ["a.md"]


def test_directory_sidecar_mytags_is_used_without_project_flag(tmp_path, monkeypatch):
    root = tmp_path / "Workspace"
    root.mkdir()
    folder = root / "Invoices"
    folder.mkdir()
    sidecar = folder / ".MyOS"
    sidecar.mkdir()
    (sidecar / "myTags.md").write_text("#finance\n#urgent\n", encoding="utf-8")

    file_path = root / "note.md"
    file_path.write_text("note", encoding="utf-8")

    def fake_read_tags(path: Path):
        # Keep file tags working while directory tags come from sidecar.
        if str(path) == str(file_path):
            return {"doc": None}
        return {}

    monkeypatch.setattr(scope_api_module, "read_tags", fake_read_tags)

    api = ScopeApi(str(root))
    entries = api.list_entries(str(root))
    by_name = {entry["name"]: entry for entry in entries}

    assert by_name["Invoices"]["isDir"] is True
    assert by_name["Invoices"]["tags"] == ["finance", "urgent"]
    assert by_name["note.md"]["tags"] == ["doc"]

    filtered = api.list_entries_filtered(str(root), ["finance"], match_all=False)
    assert sorted(item["name"] for item in filtered) == ["Invoices"]


def test_move_entries_moves_multiple_sources(tmp_path):
    root = tmp_path / "Lab"
    root.mkdir()
    src_a = root / "a.txt"
    src_b = root / "b.txt"
    dst = root / "Target"
    dst.mkdir()
    src_a.write_text("A", encoding="utf-8")
    src_b.write_text("B", encoding="utf-8")

    api = ScopeApi(str(root))
    result = api.move_entries([str(src_a), str(src_b)], str(dst))

    assert result["ok"] is True
    assert len(result["moved"]) == 2
    assert not src_a.exists()
    assert not src_b.exists()
    assert (dst / "a.txt").exists()
    assert (dst / "b.txt").exists()


def test_move_entries_skips_invalid_target_inside_source(tmp_path):
    root = tmp_path / "Lab"
    root.mkdir()
    parent = root / "Parent"
    nested = parent / "Nested"
    parent.mkdir()
    nested.mkdir()

    api = ScopeApi(str(root))
    result = api.move_entries([str(parent)], str(nested))

    assert result["ok"] is False
    assert result["moved"] == []
    assert any(item["reason"] == "target_inside_source" for item in result["errors"])
