from PostFix.markdown_render import (
    extract_block_line_anchors,
    extract_block_line_ranges,
    render_markdown,
)
from PostFix.smart_editor import SmartEditor


def test_obsidian_image_width_syntax_renders_img_width():
    html = render_markdown("![Beschreibung|300](myBild.jpg)")
    assert "<img" in html
    assert 'src="myBild.jpg"' in html
    assert 'width="300"' in html


def test_markdown_table_renders_table_html():
    md = "| A | B |\n| - | - |\n| 1 | 2 |\n"
    html = render_markdown(md)
    assert "<table>" in html
    assert "<td>1</td>" in html


def test_markdown_table_with_blank_lines_between_rows_is_normalized():
    md = "| A | B |\n\n| - | - |\n\n| 1 | 2 |\n"
    html = render_markdown(md)
    assert "<table>" in html
    assert "<th>A</th>" in html
    assert "<td>2</td>" in html


def test_heading_without_space_is_treated_as_heading():
    html = render_markdown("#Titel\n\nText\n")
    assert "<h1>Titel</h1>" in html


def test_extract_block_line_anchors_map_back_to_source_lines():
    md = "#Titel\n\n| A | B |\n\n| - | - |\n\n| 1 | 2 |\n"
    anchors = extract_block_line_anchors(md)
    assert anchors[0] == 0
    # Ensure we preserve original source line positions despite table-blank normalization.
    assert any(a >= 2 for a in anchors)


def test_extract_tags_ignores_anchor_link_targets():
    editor = SmartEditor.__new__(SmartEditor)
    body = "[this one](#links)\n\n#realtag and #todo\n"
    tags = SmartEditor.extract_tags(editor, body)
    assert "links" not in tags
    assert "realtag" in tags
    assert "todo" in tags


def test_obsidian_wikilink_renders_markdown_link():
    html = render_markdown("Go to [[My Note]].")
    assert 'href="My%20Note.md"' in html
    assert ">My Note<" in html


def test_obsidian_wikilink_with_alias_renders_alias_text():
    html = render_markdown("Open [[Folder/Page Name|Alias]].")
    assert 'href="Folder/Page%20Name.md"' in html
    assert ">Alias<" in html


def test_obsidian_embed_image_with_size_renders_img_width():
    html = render_markdown("![[lama.webp|300]]")
    assert "<img" in html
    assert 'src="lama.webp"' in html
    assert 'width="300"' in html


def test_tasklist_syntax_renders_checkbox_markup():
    html = render_markdown("- [ ] todo\n- [x] done\n")
    assert 'type="checkbox"' in html


def test_extract_block_line_ranges_returns_non_empty_ranges():
    md = "# Titel\n\nAbsatz\n\n| A | B |\n| - | - |\n| 1 | 2 |\n"
    ranges = extract_block_line_ranges(md)
    assert ranges
    assert ranges[0][0] == 0
    assert all(start < end for start, end in ranges)


def test_obsidian_callout_renders_structured_html_block():
    md = "> [!note] Hinweis\n> Erste Zeile\n> Zweite Zeile\n"
    html = render_markdown(md)
    assert 'class="ofm-callout ofm-callout-note"' in html
    assert 'class="ofm-callout-title"' in html
    assert "Hinweis" in html
    assert "Erste Zeile" in html
