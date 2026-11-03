"""The light rendering of a note: what the editor (PostFix/codemirror, CodeMirror's live preview)
shows while the cursor is elsewhere, drawn by Qt without a browser page. A note that is only read
never loads the editor (about 300 MB); when it gets the editor, nothing jumps.

So this follows the editor's rules, not Markdown's paragraphs: every line of the note is a line
on screen (an empty line is an empty line), Markdown marks are hidden, images, check boxes,
bullets, rules and tables are drawn. The look (fonts, sizes, colours, widths) is the editor's
theme in PostFix/codemirror/src/editor.js; how the two were measured alike: PostFix/Designdokument.md.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Optional

from markdown_it import MarkdownIt

# The editor's theme (editor.js and the page in editor_host.py), for both sides.
FONT_SIZE = 16          # px
LINE_HEIGHT = 1.65      # of the font size
HEADING_SIZE = {1: 1.8, 2: 1.45, 3: 1.2}             # em
HEADING_LINE_HEIGHT = {1: 1.3, 2: 1.3}               # others keep LINE_HEIGHT
HEADING_PAD_TOP = {1: 0.4, 2: 0.35, 3: 0.3}          # em of the heading's size
CONTENT_WIDTH = 720     # px at most, centred
PAD_TOP, PAD_SIDE, PAD_BOTTOM = 28, 24, 120
COLORS = {"fg": "#1f2330", "muted": "#6b7083", "accent": "#5b4fd6", "quote": "#d5d8e2",
          "code_bg": "rgba(0,0,0,0.05)"}
QUARTER_SPACE = "&#8197;"  # 0.25em: the bullet's padding on each side

_FENCE = re.compile(r"^ {0,3}(```|~~~)")
_HEADING = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+|$)")
_RULE = re.compile(r"^ {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")
_SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
_QUOTE = re.compile(r"^ {0,3}> ?")
_BULLET = re.compile(r"^([ \t]*)([-*+])([ \t]+|$)")
_ORDERED = re.compile(r"^([ \t]*)(\d{1,9}[.)])([ \t]+|$)")
_TASK = re.compile(r"^\[([ xX])\]")
_TABLE_DIVIDER = re.compile(r"^[ \t]*\|?[ \t]*:?-+:?[ \t]*(\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
_IMAGE_ALT_WIDTH = re.compile(r"^(.*)\|(\d+)$")


@dataclass
class Block:
    """One line on screen (or a whole table)."""

    kind: str = "line"              # line, rule, table
    html: str = ""                  # the line's content, inline HTML
    heading: int = 0
    quote: bool = False
    code: bool = False
    task: Optional[bool] = None     # a check box: ticked or not
    images: list = field(default_factory=list)  # [(src, width or None)]
    rows: list = field(default_factory=list)    # a table's cells
    lines: int = 1                  # source lines it stands for


_MD: Optional[MarkdownIt] = None


def _inline_parser() -> MarkdownIt:
    global _MD
    if _MD is None:
        # What the editor's Markdown (CodeMirror, GFM) hides; everything else stays as typed:
        # HTML, entities and <autolinks> show as written there.
        md = MarkdownIt("commonmark", {"html": False})
        md.enable("strikethrough")
        md.disable(["entity", "autolink"])
        md.normalizeLink = lambda url: url          # links keep their target as written
        md.normalizeLinkText = lambda text: text
        md.validateLink = lambda url: True
        _MD = md
    return _MD


def _style(**css) -> str:
    return "; ".join(f"{key.replace('_', '-')}: {value}" for key, value in css.items())


def _inline_lines(text: str, images: list, done: bool = False) -> list[str]:
    """Inline Markdown of one or more lines (a paragraph: emphasis may span lines) as HTML,
    one entry per line, open formatting closed at each line's end and opened again after."""
    lines, current, open_ = [], [], []  # open_: [(start tag, end tag)] still open

    def put(fragment):
        current.append(fragment)

    def push(start, end):
        open_.append((start, end))
        put(start)

    def pop():
        if open_:
            put(open_.pop()[1])

    def new_line():
        nonlocal current
        lines.append("".join(current) + "".join(end for _, end in reversed(open_)))
        current = [start for start, _ in open_]

    tokens = _inline_parser().parseInline(text)
    children = tokens[0].children if tokens else []
    for token in children or []:
        kind = token.type
        if kind == "text":
            put(html.escape(token.content, quote=False))
        elif kind in ("softbreak", "hardbreak"):
            new_line()
        elif kind == "strong_open":
            push("<b>", "</b>")
        elif kind == "em_open":
            push("<i>", "</i>")
        elif kind == "s_open":
            push("<s>", "</s>")
        elif kind in ("strong_close", "em_close", "s_close", "link_close"):
            pop()
        elif kind == "code_inline":
            put(f'<span style="{_style(font_family="__MONO__", background_color=COLORS["code_bg"])}">'
                f"{html.escape(token.content, quote=False)}</span>")
        elif kind == "link_open":
            href = html.escape(token.attrGet("href") or "", quote=True)
            push(f'<a href="{href}" style="{_style(color=COLORS["accent"], text_decoration="underline")}">', "</a>")
        elif kind == "image":
            src = token.attrGet("src") or ""
            alt = token.content or ""
            match = _IMAGE_ALT_WIDTH.match(alt)
            width = int(match.group(2)) if match else None
            images.append((src, width))
            size = f' width="{width}"' if width else ""
            put(f'<img src="{html.escape(src, quote=True)}"{size} alt="{html.escape(alt, quote=True)}">')
        else:
            put(html.escape(token.content or "", quote=False))
    lines.append("".join(current) + "".join(end for _, end in reversed(open_)))
    if done:
        style = _style(color=COLORS["muted"], text_decoration="line-through")
        lines = [f'<span style="{style}">{line}</span>' for line in lines]
    return lines


def _leading(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" \t"))]


def _starts_block(line: str) -> bool:
    return bool(not line.strip() or _FENCE.match(line) or _HEADING.match(line) or _RULE.match(line)
                or _QUOTE.match(line) or _BULLET.match(line) or _ORDERED.match(line))


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def render_lines(body: str) -> list[Block]:
    """The note's body as the editor shows it with the cursor elsewhere."""
    source = body.split("\n")
    if source and source[-1] == "" and len(source) > 1:
        source = source[:-1] + [""]  # the empty last line is a line in the editor too
    blocks: list[Block] = []
    i, in_fence = 0, None
    while i < len(source):
        line = source[i]
        fence = _FENCE.match(line)
        if in_fence or fence:
            closing = bool(in_fence and fence and fence.group(1) == in_fence)
            if fence and (closing or not in_fence):  # the fence marks: grey
                text = f'<span style="{_style(color=COLORS["muted"])}">{html.escape(line, quote=False)}</span>'
            else:  # the code: on its own background again, as the editor marks it
                text = (f'<span style="{_style(background_color=COLORS["code_bg"])}">'
                        f'{html.escape(line, quote=False)}</span>') if line else ""
            blocks.append(Block(html=text, code=True))
            if in_fence and fence and fence.group(1) == in_fence:
                in_fence = None
            elif not in_fence:
                in_fence = fence.group(1)
            i += 1
            continue
        if "|" in line and i + 1 < len(source) and _TABLE_DIVIDER.match(source[i + 1]) and "-" in source[i + 1]:
            end = i + 2
            while end < len(source) and source[end].strip() and "|" in source[end]:
                end += 1
            rows = [_cells(source[i])] + [_cells(row) for row in source[i + 2:end]]
            blocks.append(Block(kind="table", rows=rows, lines=end - i))
            i = end
            continue
        if _RULE.match(line) and not (_SETEXT.match(line) and blocks and _paragraph_before(source, i)):
            blocks.append(Block(kind="rule"))
            i += 1
            continue
        if _SETEXT.match(line) and _paragraph_before(source, i):
            blocks.append(Block())  # the underline of a heading: its mark, hidden
            i += 1
            continue
        heading = _HEADING.match(line)
        if heading:
            images: list = []
            content = re.sub(r"[ \t]+#+[ \t]*$", "", line[heading.end():])
            (inner,) = _inline_lines(content, images)[:1] or [""]
            blocks.append(Block(html=inner, heading=len(heading.group(1)), images=images))
            i += 1
            continue
        quote = _QUOTE.match(line)
        if quote:
            rest = line[quote.end():]
            while _QUOTE.match(rest):
                rest = rest[_QUOTE.match(rest).end():]
            images = []
            muted = f'<span style="{_style(color=COLORS["muted"])}">' + "".join(_inline_lines(rest, images)) + "</span>"
            blocks.append(Block(html=muted, quote=True, images=images))
            i += 1
            continue
        bullet = _BULLET.match(line)
        ordered = _ORDERED.match(line)
        if ordered and line.strip():  # the number stays, grey like every list mark
            images = []
            (inner,) = _inline_lines(line[ordered.end():], images)[:1]
            number = f'<span style="{_style(color=COLORS["muted"])}">{html.escape(ordered.group(2), quote=False)}</span>'
            blocks.append(Block(html=html.escape(ordered.group(1), quote=False) + number
                                + html.escape(ordered.group(3), quote=False) + inner, images=images))
            i += 1
            continue
        if bullet and line.strip():
            rest = line[bullet.end():]
            task = _TASK.match(rest)
            images = []
            if task:
                checked = task.group(1) in "xX"
                after = rest[task.end():]
                (inner,) = _inline_lines(after, images, done=checked)[:1]
                lead = html.escape(bullet.group(1), quote=False)
                box = f'<img src="postfix-task:{"on" if checked else "off"}" style="vertical-align: bottom">'
                blocks.append(Block(html=lead + box + inner, task=checked, images=images))
            else:
                dot = (f'<span style="{_style(color=COLORS["muted"])}">'
                       f"{QUARTER_SPACE}•{QUARTER_SPACE}</span>")
                (inner,) = _inline_lines(rest, images)[:1]
                blocks.append(Block(html=html.escape(bullet.group(1), quote=False) + dot
                                    + html.escape(bullet.group(3), quote=False) + inner, images=images))
            i += 1
            continue
        if not line.strip():
            blocks.append(Block())
            i += 1
            continue
        # A paragraph: its lines together (emphasis may span them), each a line on screen.
        end = i + 1
        while end < len(source) and not _starts_block(source[end]) and not _SETEXT.match(source[end]):
            end += 1
        images = []
        rendered = _inline_lines("\n".join(source[i:end]), images)
        for offset, inner in enumerate(rendered):
            lead = html.escape(_leading(source[i + offset]), quote=False) if offset else ""
            mine = [image for image in images if f'src="{html.escape(image[0], quote=True)}"' in inner]
            blocks.append(Block(html=lead + inner, images=mine))
        i = end
    return blocks


def _paragraph_before(source: list[str], i: int) -> bool:
    if i == 0:
        return False
    before = source[i - 1]
    return bool(before.strip()) and not _starts_block(before)
