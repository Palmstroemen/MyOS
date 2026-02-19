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


def test_markdown_file_tags_are_parsed_from_frontmatter_and_hashtags(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    note = root / "note.md"
    note.write_text(
        "\n".join(
            [
                "---",
                "tags:",
                "  - alpha",
                "  - #beta",
                "---",
                "# Heading should not become a tag",
                "Body has #gamma and #delta tags.",
                "Duplicate #gamma should collapse.",
            ]
        ),
        encoding="utf-8",
    )

    api = ScopeApi(str(root))
    entries = api.list_entries(str(root))
    by_name = {entry["name"]: entry for entry in entries}

    assert by_name["note.md"]["tags"] == ["alpha", "beta", "delta", "gamma"]


def test_directory_tags_ignore_xattr_and_use_only_sidecar(tmp_path, monkeypatch):
    root = tmp_path / "Workspace"
    root.mkdir()
    folder = root / "Folder"
    folder.mkdir()
    sidecar = folder / ".MyOS"
    sidecar.mkdir()
    (sidecar / "myTags.md").write_text("#from-sidecar\n", encoding="utf-8")

    def fake_read_tags(path: Path):
        if str(path) == str(folder):
            return {"from-xattr": None}
        return {}

    monkeypatch.setattr(scope_api_module, "read_tags", fake_read_tags)

    api = ScopeApi(str(root))
    entries = api.list_entries(str(root))
    by_name = {entry["name"]: entry for entry in entries}

    assert by_name["Folder"]["tags"] == ["from-sidecar"]


def test_markdown_tag_cache_file_is_written_and_reused(tmp_path, monkeypatch):
    root = tmp_path / "Workspace"
    root.mkdir()
    note = root / "note.md"
    note.write_text("Body with #alpha\n", encoding="utf-8")

    api = ScopeApi(str(root))
    first_entries = api.list_entries(str(root))
    first_by_name = {entry["name"]: entry for entry in first_entries}
    assert first_by_name["note.md"]["tags"] == ["alpha"]

    cache_file = root / ".TagsHere.json"
    assert cache_file.exists()

    def fake_parse(path: Path):
        return ["from-parser-now"]

    monkeypatch.setattr(scope_api_module, "_read_markdown_content_tags", fake_parse)

    second_entries = api.list_entries(str(root))
    second_by_name = {entry["name"]: entry for entry in second_entries}
    # File unchanged => cached tags should win over parser.
    assert second_by_name["note.md"]["tags"] == ["alpha"]


def test_invalid_cache_values_do_not_break_entries_listing(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    note = root / "note.md"
    note.write_text("Body with #alpha\n", encoding="utf-8")
    # Corrupt cache types for mtime/size to ensure robust fallback.
    (root / ".TagsHere.json").write_text(
        '{"version":1,"entries":{"note.md":{"mtime_ns":"broken","size":"broken","tags":["cached"]}}}',
        encoding="utf-8",
    )

    api = ScopeApi(str(root))
    entries = api.list_entries(str(root))
    by_name = {entry["name"]: entry for entry in entries}

    assert by_name["note.md"]["tags"] == ["alpha"]


def test_folder_sidecar_roundtrip_with_size_metadata(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    folder = root / "Folder"
    folder.mkdir()

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(folder), ["One", "#two"]) is True

    sidecar = folder / ".MyOS" / "myTags.md"
    text = sidecar.read_text(encoding="utf-8")
    assert "folder_size_bytes:" in text
    assert "#One" in text or "#one" in text
    assert "#two" in text

    tags = api.list_folder_tags(str(folder))
    assert sorted(tags, key=str.lower) == ["One", "two"]


def test_list_tag_buckets_splits_folder_and_file_tags(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    note = root / "note.md"
    note.write_text("Body #filetag #shared\n", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root), ["shared", "foldertag"]) is True

    buckets = api.list_tag_buckets(str(root))
    assert buckets["folderTags"] == ["foldertag", "shared"]
    assert buckets["fileTags"] == ["filetag"]
    assert isinstance(buckets["folderSizeBytes"], int)
    assert buckets["folderSizeBytes"] >= 0


def test_folder_tag_colors_roundtrip_and_bucket_exposure(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    (root / "app.json").write_text("{}", encoding="utf-8")
    note = root / "note.md"
    note.write_text("Body #filetag\n", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root), ["foldertag"]) is True
    assert api.set_folder_tag_color(str(root), "foldertag", "#4C72D9") is True

    buckets = api.list_tag_buckets(str(root))
    assert buckets["folderTagColors"]["foldertag"] == "#4c72d9"

    registry_file = root / "app.json"
    content = registry_file.read_text(encoding="utf-8")
    assert "colored-tags-wrangler" in content
    assert "#4c72d9" in content


def test_set_folder_tag_color_rejects_invalid_input(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    (root / "app.json").write_text("{}", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root), ["foldertag"]) is True
    assert api.set_folder_tag_color(str(root), "foldertag", "blue") is False
    assert api.set_folder_tag_color(str(root), "other", "#123456") is False


def test_folder_tag_color_uses_obsidian_app_registry_when_present(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    obsidian_dir = root / ".obsidian"
    obsidian_dir.mkdir()
    (obsidian_dir / "app.json").write_text("{}", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root), ["foldertag"]) is True
    assert api.set_folder_tag_color(str(root), "foldertag", "#33AA77") is True

    app_content = (obsidian_dir / "app.json").read_text(encoding="utf-8")
    assert "colored-tags-wrangler" in app_content
    assert "#33aa77" in app_content


def test_list_tag_buckets_exposes_file_tag_colors_from_registry(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir()
    (root / "app.json").write_text(
        """
{
  "colored-tags-wrangler": {
    "tags": [
      {"name": "filetag", "color": "#ff8800"},
      {"name": "foldertag", "color": "#33aa77"}
    ]
  }
}
""".strip(),
        encoding="utf-8",
    )
    note = root / "note.md"
    note.write_text("Body #filetag\n", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.set_folder_tags(str(root), ["foldertag"]) is True
    buckets = api.list_tag_buckets(str(root))

    assert buckets["fileTags"] == ["filetag"]
    assert buckets["fileTagColors"]["filetag"] == "#ff8800"


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


def test_scope_api_refreshes_desk_context_on_init_and_updates(tmp_path, monkeypatch):
    calls = []

    class FakeDeskService:
        def refresh_context(self, path, *, manual_desk=None):
            calls.append(str(Path(path).resolve()))
            return {"ok": True, "applied": False, "reason": "test"}

        def get_active_profile(self):
            return {"source": "fake", "hash": "fake"}

        def get_last_result(self):
            return {"ok": True, "applied": False, "reason": "test", "source": None, "steps": []}

    monkeypatch.setattr(scope_api_module, "DeskService", FakeDeskService)

    root = tmp_path / "Workspace"
    child = root / "Child"
    child.mkdir(parents=True)

    api = ScopeApi(str(root))
    api.update_context(str(child))

    assert calls[0] == str(root.resolve())
    assert calls[1] == str(child.resolve())
    assert api.get_last_desk_result()["reason"] == "test"
    assert api.get_active_desk_profile()["source"] == "fake"


def test_scope_api_desk_context_runtime_error_is_non_fatal(tmp_path, monkeypatch):
    class FailingDeskService:
        def refresh_context(self, path, *, manual_desk=None):
            return {"ok": False, "applied": False, "reason": "runtime_error", "source": None, "steps": []}

        def get_active_profile(self):
            return {"source": None, "hash": None}

        def get_last_result(self):
            return {"ok": False, "applied": False, "reason": "runtime_error", "source": None, "steps": []}

    monkeypatch.setattr(scope_api_module, "DeskService", FailingDeskService)

    root = tmp_path / "Workspace"
    root.mkdir(parents=True)
    api = ScopeApi(str(root))

    assert api.get_last_desk_result()["ok"] is False
    assert api.get_last_desk_result()["reason"] == "runtime_error"


def test_scope_api_rejects_unsafe_config_name_for_security(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir(parents=True)
    secret = root / "outside.md"
    secret.write_text("do not touch", encoding="utf-8")
    project_root = root / "Project"
    project_root.mkdir(parents=True)
    (project_root / ".MyOS").mkdir(parents=True)
    (project_root / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")

    api = ScopeApi(str(project_root))

    assert api.has_local_config(str(project_root), "../outside.md") is False
    targets = api.list_config_targets(str(project_root), "../outside.md")
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"
    assert api.ensure_project_config(str(project_root), "../outside.md")["ok"] is False
    assert api.capture_config_state("../outside.md")["ok"] is False
    assert api.apply_config_state_to_target(str(project_root), "../outside.md", "discard")["ok"] is False


def test_scope_api_rejects_overlong_config_name_for_security(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir(parents=True)
    project_root = root / "Project"
    project_root.mkdir(parents=True)
    (project_root / ".MyOS").mkdir(parents=True)
    (project_root / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    api = ScopeApi(str(project_root))
    long_name = "A" * 200 + ".md"

    assert api.has_local_config(str(project_root), long_name) is False
    assert api.ensure_project_config(str(project_root), long_name)["ok"] is False
    assert api.capture_config_state(long_name)["ok"] is False
    targets = api.list_config_targets(str(project_root), long_name)
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"


def test_scope_api_rejects_non_ascii_spoofed_config_name_for_security(tmp_path):
    root = tmp_path / "Workspace"
    root.mkdir(parents=True)
    project_root = root / "Project"
    project_root.mkdir(parents=True)
    (project_root / ".MyOS").mkdir(parents=True)
    (project_root / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    api = ScopeApi(str(project_root))
    spoofed = "Dеsk.md"  # Cyrillic e

    assert api.has_local_config(str(project_root), spoofed) is False
    assert api.ensure_project_config(str(project_root), spoofed)["ok"] is False
    assert api.capture_config_state(spoofed)["ok"] is False
    targets = api.list_config_targets(str(project_root), spoofed)
    assert len(targets) == 1
    assert targets[0]["id"] == "discard"
