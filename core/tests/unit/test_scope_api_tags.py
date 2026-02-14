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
