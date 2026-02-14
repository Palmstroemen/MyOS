import json
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PostFix.tag_registry import (
    assign_tag_color_in_registry,
    find_vault_root,
    flatten_tag_colors,
    load_tag_registry,
    parse_scope_tags,
    save_tag_registry,
    write_scope_tags,
)


@pytest.fixture
def postfix_test_lab(tmp_path: Path) -> dict[str, Path]:
    """Small PostFix-focused test lab with vault + project layout."""
    vault = tmp_path / "vault"
    project = vault / "Projects" / "Demo"
    myos = project / ".MyOS"
    obsidian = vault / ".obsidian"
    obsidian.mkdir(parents=True, exist_ok=True)
    myos.mkdir(parents=True, exist_ok=True)
    return {
        "vault": vault,
        "project": project,
        "myos": myos,
        "obsidian_app_json": obsidian / "app.json",
        "scope_tags_md": myos / "Tags.md",
    }


def test_find_vault_root_from_nested_file(postfix_test_lab: dict[str, Path]):
    note = postfix_test_lab["project"] / "note.md"
    note.write_text("# demo\n", encoding="utf-8")
    postfix_test_lab["obsidian_app_json"].write_text("{}", encoding="utf-8")
    assert find_vault_root(note) == postfix_test_lab["vault"]


def test_write_and_parse_scope_tags_roundtrip(postfix_test_lab: dict[str, Path]):
    tags_md = postfix_test_lab["scope_tags_md"]
    ok = write_scope_tags(tags_md, ["important", "#todo", "important", "  urgent  "])
    assert ok is True
    assert tags_md.exists()
    parsed = parse_scope_tags(tags_md)
    assert parsed == ["important", "todo", "urgent"]


def test_load_tag_registry_invalid_json_returns_empty(postfix_test_lab: dict[str, Path]):
    registry = postfix_test_lab["obsidian_app_json"]
    registry.write_text("{not-valid-json", encoding="utf-8")
    assert load_tag_registry(registry) == {}


def test_save_then_load_tag_registry(postfix_test_lab: dict[str, Path]):
    registry = postfix_test_lab["obsidian_app_json"]
    data = {"colored-tags-wrangler": {"tags": [{"name": "important", "color": "#ff0000"}]}}
    assert save_tag_registry(registry, data) is True
    loaded = load_tag_registry(registry)
    assert loaded["colored-tags-wrangler"]["tags"][0]["name"] == "important"


def test_flatten_tag_colors_handles_grouped_names():
    app_json = {
        "colored-tags-wrangler": {
            "tags": [
                {"name": "important;urgent", "color": "#ff0000"},
                {"name": "team", "color": "#0000ff"},
            ]
        }
    }
    flat = flatten_tag_colors(app_json)
    assert flat["important"] == "#ff0000"
    assert flat["urgent"] == "#ff0000"
    assert flat["team"] == "#0000ff"


def test_assign_tag_color_creates_new_entry_with_background():
    app_json = {"colored-tags-wrangler": {"tags": [], "settings": {"separateBackground": True}}}
    assert assign_tag_color_in_registry(app_json, "important", "#336699") is True
    tags = app_json["colored-tags-wrangler"]["tags"]
    assert len(tags) == 1
    assert tags[0]["name"] == "important"
    assert tags[0]["color"] == "#336699"
    assert "background" in tags[0]


def test_assign_tag_color_splits_group_entry():
    app_json = {
        "colored-tags-wrangler": {
            "tags": [{"name": "important;urgent;todo", "color": "#ff0000", "luminanceOffset": 20}],
            "settings": {"separateBackground": True},
        }
    }
    assert assign_tag_color_in_registry(app_json, "urgent", "#ffaa00") is True
    tags = app_json["colored-tags-wrangler"]["tags"]
    names = {entry["name"] for entry in tags}
    assert "important;todo" in names
    assert "urgent" in names
    urgent_entry = [entry for entry in tags if entry["name"] == "urgent"][0]
    assert urgent_entry["color"] == "#ffaa00"
    assert urgent_entry["luminanceOffset"] == 20
