from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PostFix.smart_editor import SmartEditor
from PostFix.tag_registry import (
    assign_tag_color_in_registry,
    normalize_tag_name,
    parse_scope_tags,
    write_scope_tags,
)


def test_normalize_tag_name_rejects_control_and_scriptish_payloads():
    assert normalize_tag_name("important") == "important"
    assert normalize_tag_name(" urgent/tag-1 ") == "urgent/tag-1"
    assert normalize_tag_name("bad\nname") is None
    assert normalize_tag_name("bad\tname") is None
    assert normalize_tag_name("bad<svg>") is None
    assert normalize_tag_name("javascript:alert(1)") is None


def test_assign_tag_color_rejects_malicious_tag_names():
    app_json = {"colored-tags-wrangler": {"tags": [], "settings": {"separateBackground": True}}}
    assert assign_tag_color_in_registry(app_json, "ok-tag", "#112233") is True
    assert assign_tag_color_in_registry(app_json, "evil\nname", "#112233") is False
    assert assign_tag_color_in_registry(app_json, 'x" onclick="alert(1)', "#112233") is False
    names = [entry.get("name") for entry in app_json["colored-tags-wrangler"]["tags"]]
    assert names == ["ok-tag"]


def test_scope_tags_reader_writer_drop_malicious_entries(tmp_path: Path):
    tags_md = tmp_path / ".MyOS" / "Tags.md"
    ok = write_scope_tags(
        tags_md,
        [
            "important",
            "#todo",
            "good/path",
            "bad\nname",
            "weird<script>",
            'x" onclick="alert(1)',
        ],
    )
    assert ok is True
    parsed = parse_scope_tags(tags_md)
    assert parsed == ["important", "todo", "good/path"]


def test_html_sanitizer_strips_script_handlers_and_js_urls():
    raw = (
        '<p onclick="evil()">safe</p>'
        '<script>alert(1)</script>'
        '<a href="javascript:alert(1)">x</a>'
        "<img src='data:text/html;base64,AAAA' onerror='evil()'>"
        "<iframe srcdoc='<script>evil()</script>'></iframe>"
    )
    editor = SmartEditor.__new__(SmartEditor)
    cleaned = SmartEditor._sanitize_rendered_html(editor, raw)
    lower = cleaned.lower()
    assert "<script" not in lower
    assert "onclick=" not in lower
    assert "onerror=" not in lower
    assert "javascript:" not in lower
    assert "data:text/html" not in lower
    assert "srcdoc=" not in lower
