"""Generate safe, styled thumbnails for Markdown files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - handled at runtime by CLI
    Image = None
    ImageDraw = None
    ImageFont = None


HEX_RE = re.compile(r"^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")
BG_COLOR_LINE_RE = re.compile(r"^\s*background_color\s*:\s*['\"]?(#[0-9a-fA-F]{3,6})['\"]?\s*$")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
SCRIPT_TAG_RE = re.compile(r"<\s*script\b[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
HTML_TAG_RE = re.compile(r"<[^>]+>")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
AUTO_LINK_RE = re.compile(r"<([^>]+)>")


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1 :])
    return "", text


def normalize_hex_color(color: str, default: str = "#ffffff") -> str:
    value = (color or "").strip()
    if not HEX_RE.fullmatch(value):
        return default
    if len(value) == 4:
        return "#" + "".join(ch * 2 for ch in value[1:])
    return value.lower()


def extract_background_color(markdown_text: str, default: str = "#ffffff") -> str:
    frontmatter, body = split_frontmatter(markdown_text)
    for block in (frontmatter, body):
        for line in block.splitlines():
            m = BG_COLOR_LINE_RE.match(line)
            if m:
                return normalize_hex_color(m.group(1), default=default)
    return default


def sanitize_markdown_for_preview(markdown_text: str) -> str:
    text = SCRIPT_TAG_RE.sub("", markdown_text or "")

    def _replace_md_link(match: re.Match) -> str:
        label = match.group(1)
        url = (match.group(2) or "").strip().lower()
        if url.startswith("javascript:") or url.startswith("data:text/html"):
            return label
        return label

    text = MD_LINK_RE.sub(_replace_md_link, text)
    text = AUTO_LINK_RE.sub(lambda m: m.group(1), text)
    text = HTML_TAG_RE.sub("", text)
    text = CONTROL_CHARS_RE.sub("", text)
    return text


def markdown_to_snippet(markdown_text: str, max_lines: int = 8) -> str:
    _, body = split_frontmatter(markdown_text)
    safe = sanitize_markdown_for_preview(body)
    lines: list[str] = []
    in_fence = False
    for raw in safe.splitlines():
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)  # headings
        line = re.sub(r"^\s*[-*+]\s+", "", line)  # unordered list
        line = re.sub(r"^\s*\d+\.\s+", "", line)  # ordered list
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines) if lines else "Markdown note"


def choose_text_color(bg_hex: str) -> str:
    bg = normalize_hex_color(bg_hex)
    r = int(bg[1:3], 16)
    g = int(bg[3:5], 16)
    b = int(bg[5:7], 16)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#1f2433" if luminance > 165 else "#ffffff"


def _load_font(size: int):
    if ImageFont is None:
        return None
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_postit_thumbnail(markdown_text: str, output_path: Path, size: int = 256) -> None:
    if Image is None:
        raise RuntimeError("Pillow is not available. Install `Pillow` or `python3-pil`.")
    bg = extract_background_color(markdown_text, default="#fff8b0")
    fg = choose_text_color(bg)
    snippet = markdown_to_snippet(markdown_text, max_lines=8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), bg)
    draw = ImageDraw.Draw(img)

    # soft border
    border = max(1, size // 128)
    draw.rectangle([(0, 0), (size - 1, size - 1)], outline=(0, 0, 0, 70), width=border)

    # title stripe
    stripe_h = max(18, size // 10)
    draw.rectangle([(0, 0), (size, stripe_h)], fill=(255, 255, 255, 40))

    font = _load_font(max(12, size // 14))
    line_height = max(14, int(size * 0.09))
    max_chars = max(14, int((size - 20) / max(7, size // 42)))
    y = stripe_h + 8
    for line in snippet.splitlines():
        wrapped = []
        while len(line) > max_chars:
            wrapped.append(line[:max_chars])
            line = line[max_chars:]
        wrapped.append(line)
        for part in wrapped:
            if y + line_height > size - 8:
                break
            draw.text((10, y), part, fill=fg, font=font)
            y += line_height
        if y + line_height > size - 8:
            break

    img.save(output_path, format="PNG")


def generate_thumbnail(input_file: Path, output_file: Path, size: int) -> int:
    try:
        text = input_file.read_text(encoding="utf-8", errors="replace")
        render_postit_thumbnail(text, output_file, size=max(64, min(1024, int(size))))
        return 0
    except Exception:
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate MyOS markdown thumbnail")
    parser.add_argument("input_file", type=Path, help="Input markdown file path")
    parser.add_argument("output_file", type=Path, help="Output PNG path")
    parser.add_argument("size", nargs="?", default="256", help="Thumbnail size (px)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        size = int(args.size)
    except ValueError:
        size = 256
    return generate_thumbnail(args.input_file, args.output_file, size)

