"""The light rendering of a note (PostFix/light_render.py): what the editor (CodeMirror, live
preview) shows while the cursor is elsewhere - line for line, Markdown marks hidden - drawn by Qt
without a browser page."""

import html as html_module
import re

from PostFix.light_render import render_lines


def _blocks(body):
    return render_lines(body)


def _text(html):
    return html_module.unescape(re.sub(r"<[^>]+>", "", html)).replace("\u2005", " ")


def test_every_line_is_a_block_of_its_own_blank_lines_included():
    blocks = _blocks("Erste Zeile\nzweite Zeile\n\nDritte")
    assert [b.kind for b in blocks] == ["line", "line", "line", "line"]
    assert [_text(b.html) for b in blocks] == ["Erste Zeile", "zweite Zeile", "", "Dritte"]


def test_a_heading_hides_its_marks_and_keeps_its_level():
    (block,) = _blocks("## Zweite Ebene")
    assert block.heading == 2 and _text(block.html) == "Zweite Ebene"


def test_emphasis_hides_its_marks_even_across_lines():
    first, second = _blocks("Ein **fetter\nText** und *schräg*")
    assert "<b>fetter</b>" in first.html and _text(first.html) == "Ein fetter"
    assert "<b>Text</b>" in second.html and "<i>schräg</i>" in second.html


def test_a_link_shows_its_text_and_keeps_its_target():
    (block,) = _blocks("Weiter zu [Lektion 2](<../Lektion 2/Text.md>).")
    assert _text(block.html) == "Weiter zu Lektion 2."
    assert 'href="../Lektion 2/Text.md"' in block.html


def test_bullets_become_dots_numbers_stay():
    dot, number = _blocks("- Punkt\n1. Erstens")
    assert _text(dot.html) == " •  Punkt"  # the dot with a quarter space on each side, then the space
    assert _text(number.html) == "1. Erstens"


def test_tasks_become_boxes():
    done, todo = _blocks("- [x] erledigt\n- [ ] offen")
    assert done.task is True and _text(done.html).strip() == "erledigt" and "line-through" in done.html
    assert todo.task is False and _text(todo.html).strip() == "offen"


def test_a_quote_hides_its_mark():
    (block,) = _blocks("> Zitat")
    assert block.quote and _text(block.html) == "Zitat"


def test_a_rule_and_code():
    rule, fence, code, end = _blocks("---\n```\nx = 1 * 2\n```")
    assert rule.kind == "rule"
    assert [fence.code, code.code, end.code] == [True, True, True]
    assert _text(fence.html) == "```" and _text(code.html) == "x = 1 * 2"  # no emphasis in code


def test_inline_code_and_escapes():
    (block,) = _blocks("Ein \\*Stern\\* und `**roh**`")
    assert _text(block.html) == "Ein *Stern* und **roh**"


def test_a_table_is_one_block_without_its_divider():
    table, after = _blocks("| A | B |\n|---|---|\n| 1 | 2 |\nDanach")
    assert table.kind == "table" and table.rows == [["A", "B"], ["1", "2"]] and table.lines == 3
    assert _text(after.html) == "Danach"


def test_an_image_with_its_obsidian_width():
    (block,) = _blocks("![Lama|300](<lama.jpg>)")
    assert block.images == [("lama.jpg", 300)]
    assert 'src="lama.jpg"' in block.html


def test_markup_in_the_text_is_shown_not_run():
    (block,) = _blocks("<b>nicht fett</b> & mehr")
    assert "<b>nicht" not in block.html and _text(block.html) == "<b>nicht fett</b> & mehr"
