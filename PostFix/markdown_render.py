"""Central Markdown rendering helpers for PostFix."""

from __future__ import annotations

import html
import re
from urllib.parse import quote

from markdown_it import MarkdownIt
from mdit_py_plugins.tasklists import tasklists_plugin

_OBSIDIAN_IMAGE_RE = re.compile(r"!\[(?P<inner>[^\]]*)\]\((?P<src>[^)]+)\)")
_SIZE_RE = re.compile(r"^\s*(?P<w>\d+)(?:x(?P<h>\d+))?\s*$")
_HEADING_NO_SPACE_RE = re.compile(r"^(?P<hashes>#{1,6})(?P<title>[^#\s].*)$")
_OBSIDIAN_WIKILINK_RE = re.compile(r"(?P<embed>!?)\[\[(?P<inner>[^\]]+)\]\]")
_OBSIDIAN_CALLOUT_RE = re.compile(
    r"^\s*>\s*\[\!(?P<kind>[A-Za-z0-9_-]+)\](?P<fold>[+-])?\s*(?P<title>.*)$"
)
_RENDERER: MarkdownIt | None = None
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}


def _get_renderer() -> MarkdownIt:
    global _RENDERER
    if _RENDERER is None:
        md = MarkdownIt("commonmark", {"html": True, "breaks": True})
        md.enable("table")
        md.use(tasklists_plugin, enabled=False, label=True, label_after=True)
        _RENDERER = md
    return _RENDERER


def _replace_obsidian_image_sizes(md_text: str) -> str:
    def _repl(match: re.Match) -> str:
        inner = match.group("inner") or ""
        src = (match.group("src") or "").strip()
        alt = inner
        width = None
        height = None
        if "|" in inner:
            left, right = inner.rsplit("|", 1)
            size_match = _SIZE_RE.match(right)
            if size_match:
                alt = left.strip()
                width = size_match.group("w")
                height = size_match.group("h")
        if not width:
            return match.group(0)
        safe_src = html.escape(src, quote=True)
        safe_alt = html.escape(alt, quote=True)
        attrs = [f'src="{safe_src}"', f'alt="{safe_alt}"', f'width="{width}"']
        if height:
            attrs.append(f'height="{height}"')
        return f"<img {' '.join(attrs)} />"

    return _OBSIDIAN_IMAGE_RE.sub(_repl, md_text or "")


def _split_target_alias(raw: str) -> tuple[str, str]:
    inner = (raw or "").strip()
    if "|" not in inner:
        return inner, ""
    left, right = inner.rsplit("|", 1)
    return left.strip(), right.strip()


def _ensure_markdown_suffix(path_part: str) -> str:
    text = (path_part or "").strip()
    if not text:
        return text
    if text.startswith("#"):
        return text
    if "/" in text:
        tail = text.rsplit("/", 1)[-1]
    else:
        tail = text
    if "." in tail:
        return text
    return f"{text}.md"


def _normalize_href(target: str) -> str:
    normalized = _ensure_markdown_suffix(target)
    return quote(normalized, safe="/#")


def _replace_obsidian_wikilinks(md_text: str) -> str:
    def _repl(match: re.Match) -> str:
        embed = (match.group("embed") or "") == "!"
        raw_inner = match.group("inner") or ""
        target, alias_or_size = _split_target_alias(raw_inner)
        href = _normalize_href(target)
        link_text = alias_or_size or target
        lower_target = target.lower()
        is_image = any(lower_target.endswith(ext) for ext in _IMAGE_EXTENSIONS)

        if embed:
            if is_image:
                attrs = [f'src="{html.escape(href, quote=True)}"', f'alt="{html.escape(target, quote=True)}"']
                if alias_or_size.isdigit():
                    attrs.append(f'width="{alias_or_size}"')
                return f"<img {' '.join(attrs)} />"
            return f"[{html.escape(link_text)}]({href})"

        display = alias_or_size or target
        return f"[{display}]({href})"

    lines = (md_text or "").splitlines(keepends=True)
    out = []
    in_fence = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence:
            out.append(line)
            continue
        out.append(_OBSIDIAN_WIKILINK_RE.sub(_repl, line))
    return "".join(out)


def _replace_obsidian_callouts(md_text: str) -> str:
    lines = (md_text or "").splitlines()
    out: list[str] = []
    in_fence = False
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append(line)
            idx += 1
            continue
        if in_fence:
            out.append(line)
            idx += 1
            continue
        match = _OBSIDIAN_CALLOUT_RE.match(line)
        if not match:
            out.append(line)
            idx += 1
            continue

        kind = (match.group("kind") or "note").strip().lower()
        fold = (match.group("fold") or "").strip()
        title = (match.group("title") or "").strip() or kind.capitalize()
        body_lines: list[str] = []
        idx += 1
        while idx < len(lines):
            nxt = lines[idx]
            if re.match(r"^\s*>", nxt):
                body_lines.append(re.sub(r"^\s*>\s?", "", nxt))
                idx += 1
                continue
            break

        safe_title = html.escape(title, quote=True)
        safe_body = "<br />".join(html.escape(part, quote=False) for part in body_lines).strip()
        attrs = [
            f'class="ofm-callout ofm-callout-{kind}"',
            f'data-callout="{html.escape(kind, quote=True)}"',
        ]
        if fold in {"+", "-"}:
            attrs.append(f'data-fold="{fold}"')
        out.append(f"<div {' '.join(attrs)}>")
        out.append(f"<p class=\"ofm-callout-title\"><strong>{safe_title}</strong></p>")
        if safe_body:
            out.append(f"<p class=\"ofm-callout-body\">{safe_body}</p>")
        out.append("</div>")
    return "\n".join(out)


def _looks_like_table_row(line: str) -> bool:
    text = (line or "").strip()
    if "|" not in text:
        return False
    if len(text.replace("|", "").strip()) == 0:
        return False
    return True


def _normalize_obsidian_compat(md_text: str) -> tuple[str, list[int]]:
    lines = (md_text or "").splitlines()
    if not lines:
        return "", []
    normalized: list[str] = []
    line_map: list[int] = []
    in_fence = False
    for idx, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            normalized.append(line)
            line_map.append(idx)
            continue
        if in_fence:
            normalized.append(line)
            line_map.append(idx)
            continue
        match = _HEADING_NO_SPACE_RE.match(line.strip())
        if match:
            indent = line[: len(line) - len(line.lstrip())]
            hashes = match.group("hashes")
            title = match.group("title").strip()
            normalized.append(f"{indent}{hashes} {title}")
            line_map.append(idx)
            continue
        if not line.strip():
            prev_line = lines[idx - 1] if idx > 0 else ""
            next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
            if _looks_like_table_row(prev_line) and _looks_like_table_row(next_line):
                # Obsidian-tolerant: blank lines inside table source should not break table blocks.
                continue
        normalized.append(line)
        line_map.append(idx)
    return "\n".join(normalized), line_map


def render_markdown(md_text: str) -> str:
    processed, _ = _normalize_obsidian_compat(md_text or "")
    processed = _replace_obsidian_callouts(processed)
    processed = _replace_obsidian_wikilinks(processed)
    processed = _replace_obsidian_image_sizes(processed)
    return _get_renderer().render(processed)


def extract_block_line_anchors(md_text: str) -> list[int]:
    processed, line_map = _normalize_obsidian_compat(md_text or "")
    processed = _replace_obsidian_callouts(processed)
    processed = _replace_obsidian_wikilinks(processed)
    processed = _replace_obsidian_image_sizes(processed)
    tokens = _get_renderer().parse(processed)
    anchors: list[int] = []

    def _to_source_line(normalized_line: int) -> int:
        if not line_map:
            return max(0, normalized_line)
        idx = max(0, min(int(normalized_line), len(line_map) - 1))
        return max(0, int(line_map[idx]))

    for token in tokens:
        if not token.map:
            continue
        start, end = token.map
        if start >= 0:
            anchors.append(_to_source_line(start))
        if end > start:
            anchors.append(_to_source_line(end - 1))
    if not anchors:
        return [0]
    ordered = sorted({a for a in anchors if a >= 0})
    if 0 not in ordered:
        ordered.insert(0, 0)
    return ordered


def extract_block_line_ranges(md_text: str) -> list[tuple[int, int]]:
    processed, line_map = _normalize_obsidian_compat(md_text or "")
    processed = _replace_obsidian_callouts(processed)
    processed = _replace_obsidian_wikilinks(processed)
    processed = _replace_obsidian_image_sizes(processed)
    tokens = _get_renderer().parse(processed)

    def _to_source_line(normalized_line: int) -> int:
        if not line_map:
            return max(0, normalized_line)
        idx = max(0, min(int(normalized_line), len(line_map) - 1))
        return max(0, int(line_map[idx]))

    ranges: list[tuple[int, int]] = []
    for token in tokens:
        if not token.map:
            continue
        start, end = token.map
        if end <= start:
            continue
        src_start = _to_source_line(start)
        src_end = _to_source_line(end - 1) + 1
        if src_end <= src_start:
            src_end = src_start + 1
        ranges.append((src_start, src_end))

    if not ranges:
        return [(0, 1)]

    ranges.sort(key=lambda item: (item[0], item[1]))
    merged: list[tuple[int, int]] = []
    for start, end in ranges:
        if not merged:
            merged.append((start, end))
            continue
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
            continue
        merged.append((start, end))
    return merged
