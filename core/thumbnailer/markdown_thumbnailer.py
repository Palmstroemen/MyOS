"""Generate safe, styled thumbnails for Markdown files."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from textwrap import wrap

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:  # pragma: no cover - runtime optional dependency
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
STYLE_ALIASES = {
    "postit": "postit",
    "kurznotiz": "postit",
    "sticky": "postit",
    "a4": "sheet",
    "sheet": "sheet",
    "blatt": "sheet",
    "mitschrift": "sheet",
    "notebook": "notebook",
    "heft": "notebook",
    "konzept": "notebook",
    "chat": "chat",
    "aichat": "chat",
    "sprechblase": "chat",
    "config": "config",
    "konfig": "config",
    "konfiguration": "config",
    "settings": "config",
}
SPEAKER_LINE_RE = re.compile(
    r"^\s*(user|assistant|system|human|ai|prompt|frage|antwort|ich|du|you)\s*[:\-]\s+",
    re.IGNORECASE,
)


def split_frontmatter(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), "\n".join(lines[idx + 1 :])
    return "", text


def _parse_frontmatter(text: str) -> dict[str, str]:
    frontmatter, _ = split_frontmatter(text)
    meta: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip().strip("'\"")
    return meta


def normalize_hex_color(color: str, default: str = "#ffffff") -> str:
    value = (color or "").strip()
    if not HEX_RE.fullmatch(value):
        return default
    if len(value) == 4:
        return "#" + "".join(ch * 2 for ch in value[1:]).lower()
    return value.lower()


def extract_background_color(markdown_text: str, default: str = "#ffffff") -> str:
    frontmatter, body = split_frontmatter(markdown_text)
    for block in (frontmatter, body):
        for line in block.splitlines():
            match = BG_COLOR_LINE_RE.match(line)
            if match:
                return normalize_hex_color(match.group(1), default=default)
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
    text = html.unescape(text)
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
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "", line)
        line = re.sub(r"^\s*\d+\.\s+", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines) if lines else "Markdown note"


def _normalize_style_key(value: str | None) -> str | None:
    if not value:
        return None
    key = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    if not key:
        return None
    return STYLE_ALIASES.get(key)


def _line_count_for_autodetect(markdown_text: str) -> int:
    _, body = split_frontmatter(markdown_text)
    count = 0
    in_fence = False
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence or not line:
            continue
        count += 1
    return count


def _looks_like_ai_chat(markdown_text: str) -> bool:
    _, body = split_frontmatter(markdown_text)
    nonempty = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if len(nonempty) < 18:
        return False
    speaker_lines = 0
    speakers: set[str] = set()
    for line in nonempty:
        match = SPEAKER_LINE_RE.match(line)
        if not match:
            continue
        speaker_lines += 1
        speakers.add(match.group(1).lower())
    return speaker_lines >= 8 and len(speakers) >= 2


def detect_note_style(markdown_text: str, input_path: Path | None = None) -> str:
    """Resolve note style from explicit metadata or conservative autodetect rules."""
    meta = _parse_frontmatter(markdown_text)
    explicit = _normalize_style_key(meta.get("note_style") or meta.get("myos_note_style"))
    if explicit:
        return explicit

    if input_path and ".MyOS" in input_path.parts:
        return "config"
    if _looks_like_ai_chat(markdown_text):
        return "chat"

    line_count = _line_count_for_autodetect(markdown_text)
    if line_count < 10:
        return "postit"
    if line_count < 100:
        return "sheet"
    return "notebook"


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


def _draw_paper(draw, size: int, style: str, bg: str) -> tuple[tuple[int, int, int, int], int]:
    if style == "postit":
        x0, y0 = int(size * 0.10), int(size * 0.08)
        x1, y1 = int(size * 0.90), int(size * 0.88)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.05), fill=bg, outline="#b9ae67", width=2)
        fold = int(size * 0.14)
        draw.polygon([(x1 - fold, y0), (x1, y0), (x1, y0 + fold)], fill="#efe39a", outline="#b9ae67")
        return (x0 + 12, y0 + 18, x1 - 12, y1 - 12), 7
    if style == "sheet":
        x0, y0 = int(size * 0.14), int(size * 0.06)
        x1, y1 = int(size * 0.88), int(size * 0.94)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.02), fill=bg, outline="#c8c8c8", width=2)
        for i in range(8):
            ly = y0 + int(size * 0.13) + i * int(size * 0.08)
            draw.line((x0 + 12, ly, x1 - 12, ly), fill="#e6e6e6", width=1)
        return (x0 + 14, y0 + 26, x1 - 14, y1 - 12), 10
    if style == "config":
        x0, y0 = int(size * 0.14), int(size * 0.08)
        x1, y1 = int(size * 0.88), int(size * 0.92)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.02), fill=bg, outline="#b0b7bb", width=2)
        draw.ellipse((x1 - 38, y0 + 16, x1 - 14, y0 + 40), fill="#98a3ab", outline="#6f7980", width=2)
        return (x0 + 14, y0 + 26, x1 - 14, y1 - 12), 9
    if style == "chat":
        x0, y0 = int(size * 0.10), int(size * 0.12)
        x1, y1 = int(size * 0.90), int(size * 0.78)
        draw.rectangle((x0, y0, x1, y1), fill=bg, outline="#6f9fc2", width=3)
        tail = [(x0 + int(size * 0.20), y1), (x0 + int(size * 0.30), y1), (x0 + int(size * 0.24), y1 + int(size * 0.11))]
        draw.polygon(tail, fill=bg, outline="#6f9fc2")
        return (x0 + 12, y0 + 16, x1 - 12, y1 - 10), 7

    x0, y0 = int(size * 0.12), int(size * 0.06)
    x1, y1 = int(size * 0.90), int(size * 0.94)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.03), fill=bg, outline="#b6b2a8", width=2)
    bind_x = x0 + int(size * 0.07)
    draw.rectangle((x0, y0, bind_x, y1), fill="#ddd8cb")
    for i in range(7):
        ly = y0 + int(size * 0.09) + i * int(size * 0.10)
        draw.line((bind_x + 8, ly, x1 - 8, ly), fill="#d8d2c6", width=1)
    return (bind_x + 12, y0 + 16, x1 - 12, y1 - 12), 9


def render_note_thumbnail(markdown_text: str, output_path: Path, size: int = 256, input_path: Path | None = None) -> None:
    if Image is None:
        raise RuntimeError("Pillow is not available. Install `Pillow` or `python3-pil`.")

    style = detect_note_style(markdown_text, input_path=input_path)
    default_bg = {
        "postit": "#fff59d",
        "sheet": "#ffffff",
        "notebook": "#f4f1e8",
        "chat": "#d7efff",
        "config": "#eceff1",
    }.get(style, "#f4f1e8")
    bg = extract_background_color(markdown_text, default=default_bg)
    snippet = markdown_to_snippet(markdown_text, max_lines=12)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    text_box, max_lines = _draw_paper(draw, size, style, bg)
    font = _load_font(max(12, int(size * 0.070)))
    chars_per_line = max(12, int((text_box[2] - text_box[0]) / max(7, int(size * 0.035))))
    lines: list[str] = []
    for paragraph in snippet.splitlines():
        lines.extend(wrap(paragraph, width=chars_per_line))
        if len(lines) >= max_lines:
            break
    lines = lines[:max_lines]
    if lines and len(lines) == max_lines:
        lines[-1] = (lines[-1][:-1] + "…") if len(lines[-1]) > 1 else lines[-1]

    y = text_box[1]
    line_height = max(14, int(size * 0.085))
    for line in lines:
        draw.text((text_box[0], y), line, fill="#2f2f2f", font=font)
        y += line_height
        if y > text_box[3]:
            break
    img.save(output_path, format="PNG")


def generate_thumbnail(input_file: Path, output_file: Path, size: int) -> int:
    try:
        text = input_file.read_text(encoding="utf-8", errors="replace")
        render_note_thumbnail(text, output_file, size=max(64, min(1024, int(size))), input_path=input_file)
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

