import core.thumbnailer.markdown_thumbnailer as thumb
from core.thumbnailer.markdown_thumbnailer import (
    SAFE_MAX_INPUT_BYTES,
    SAFE_MAX_INPUT_LINES,
    SAFE_MAX_LINE_LENGTH,
    _read_markdown_safely,
    detect_note_style,
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


def test_detect_note_style_uses_line_thresholds():
    short = "\n".join(f"line {i}" for i in range(9))
    medium = "\n".join(f"line {i}" for i in range(10))
    medium_high = "\n".join(f"line {i}" for i in range(99))
    long_note = "\n".join(f"line {i}" for i in range(100))
    assert detect_note_style(short) == "postit"
    assert detect_note_style(medium) == "sheet"
    assert detect_note_style(medium_high) == "sheet"
    assert detect_note_style(long_note) == "notebook"


def test_detect_note_style_prefers_config_inside_myos_folder(tmp_path):
    path = tmp_path / "Project" / ".MyOS" / "Manifest.md"
    path.parent.mkdir(parents=True)
    text = "\n".join(f"line {i}" for i in range(50))
    assert detect_note_style(text, input_path=path) == "config"


def test_detect_note_style_prefers_config_inside_lowercase_myos_folder(tmp_path):
    path = tmp_path / "Project" / ".myos" / "Manifest.md"
    path.parent.mkdir(parents=True)
    text = "\n".join(f"line {i}" for i in range(50))
    assert detect_note_style(text, input_path=path) == "config"


def test_detect_note_style_detects_long_structured_ai_chat():
    lines = []
    for i in range(10):
        lines.append(f"User: question {i}")
        lines.append(f"Assistant: answer {i}")
    md = "\n".join(lines)
    assert detect_note_style(md) == "chat"


def test_detect_note_style_chat_not_triggered_for_single_speaker():
    lines = [f"User: question {i}" for i in range(20)]
    md = "\n".join(lines)
    assert detect_note_style(md) == "sheet"


def test_detect_note_style_explicit_style_overrides_autodetect_and_path(tmp_path):
    path = tmp_path / "Project" / ".MyOS" / "Templates.md"
    path.parent.mkdir(parents=True)
    md = """---
note_style: postit
---
line a
line b
line c
"""
    assert detect_note_style(md, input_path=path) == "postit"


def test_read_markdown_safely_clips_bytes_lines_and_line_length(tmp_path):
    source = tmp_path / "big.md"
    giant_line = "x" * (SAFE_MAX_LINE_LENGTH + 300)
    many_lines = [f"line {i}" for i in range(SAFE_MAX_INPUT_LINES + 500)]
    data = ("header\n" + giant_line + "\n" + "\n".join(many_lines)).encode("utf-8")
    # Force byte clipping too.
    source.write_bytes(data + (b"z" * SAFE_MAX_INPUT_BYTES))

    text, truncated = _read_markdown_safely(source)
    assert truncated is True
    lines = text.splitlines()
    assert len(lines) <= SAFE_MAX_INPUT_LINES
    assert max(len(line) for line in lines) <= SAFE_MAX_LINE_LENGTH


def test_generate_thumbnail_writes_fallback_png_when_pillow_missing(tmp_path, monkeypatch):
    src = tmp_path / "note.md"
    out = tmp_path / "thumb.png"
    src.write_text("tiny note", encoding="utf-8")

    monkeypatch.setattr(thumb, "Image", None)
    monkeypatch.setattr(thumb, "ImageDraw", None)
    monkeypatch.setattr(thumb, "ImageFont", None)

    code = thumb.generate_thumbnail(src, out, 256)
    assert code == 0
    assert out.exists()
    assert out.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_generate_thumbnail_returns_error_for_missing_input_file(tmp_path):
    missing = tmp_path / "does-not-exist.md"
    out = tmp_path / "thumb.png"
    code = thumb.generate_thumbnail(missing, out, 256)
    assert code == 1
    assert not out.exists()
