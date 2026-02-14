from core.thumbnailer.markdown_thumbnailer import (
    extract_background_color,
    markdown_to_snippet,
    normalize_hex_color,
    sanitize_markdown_for_preview,
)


def test_normalize_hex_color():
    assert normalize_hex_color("#abc") == "#aabbcc"
    assert normalize_hex_color("#A1B2C3") == "#a1b2c3"
    assert normalize_hex_color("evil", default="#ffffff") == "#ffffff"


def test_extract_background_color_frontmatter():
    md = """---
background_color: "#FFEEAA"
---
# Note
text
"""
    assert extract_background_color(md) == "#ffeeaa"


def test_extract_background_color_body_fallback():
    md = """
title: test
background_color: #ccdd11
text
"""
    assert extract_background_color(md) == "#ccdd11"


def test_sanitize_markdown_for_preview_removes_script_and_controls():
    raw = "<script>alert(1)</script>\x00Hello [x](javascript:alert(1))"
    clean = sanitize_markdown_for_preview(raw)
    assert "<script>" not in clean.lower()
    assert "\x00" not in clean
    assert "Hello" in clean
    assert "javascript:" not in clean.lower()


def test_markdown_to_snippet_strips_markup():
    md = """---
background_color: #ffeecc
---
# Heading
- item 1
1. item 2
Paragraph line.
"""
    snippet = markdown_to_snippet(md)
    assert "Heading" in snippet
    assert "item 1" in snippet
    assert "Paragraph line." in snippet
