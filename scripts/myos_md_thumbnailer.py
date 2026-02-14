#!/usr/bin/env python3
"""Generate Markdown thumbnails for Linux file browsers.

Design:
- Short notes are rendered as sticky notes ("post-it" look).
- Longer notes are rendered as notebook pages.

Input:
- Markdown file path
- Output PNG path
- Requested thumbnail size
"""

from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path
from textwrap import wrap


HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

STYLE_ALIASES = {
    "postit": "postit",
    "kurznotiz": "postit",
    "sticky": "postit",
    "a4": "sheet",
    "blatt": "sheet",
    "mitschrift": "sheet",
    "transcript": "sheet",
    "notebook": "notebook",
    "heft": "notebook",
    "konzept": "notebook",
    "concept": "notebook",
    "cloud": "cloud",
    "gedankenskizze": "cloud",
    "idea": "cloud",
    "sketch": "cloud",
    "aichat": "chat",
    "chat": "chat",
    "speech": "chat",
    "sprechblase": "chat",
    "config": "config",
    "konfig": "config",
    "konfiguration": "config",
    "settings": "config",
}

STYLE_BADGES = {
    "postit": "POST",
    "sheet": "A4",
    "notebook": "HEFT",
    "cloud": "IDEA",
    "chat": "AI",
    "config": "CFG",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MyOS markdown thumbnailer")
    parser.add_argument("input", nargs="?", help="Input markdown path")
    parser.add_argument("output", nargs="?", help="Output PNG path")
    parser.add_argument("size", nargs="?", type=int, help="Thumbnail size in px")
    parser.add_argument("--input", dest="input_opt")
    parser.add_argument("--output", dest="output_opt")
    parser.add_argument("--size", dest="size_opt", type=int)
    args = parser.parse_args()

    input_path = args.input_opt or args.input
    output_path = args.output_opt or args.output
    size = args.size_opt or args.size or 256
    if not input_path or not output_path:
        parser.error("input and output are required")
    args.input_path = Path(input_path)
    args.output_path = Path(output_path)
    args.thumb_size = max(64, min(1024, int(size)))
    return args


def _extract_frontmatter_and_body(text: str) -> tuple[dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            raw_meta = lines[1:i]
            body = "\n".join(lines[i + 1 :])
            meta: dict[str, str] = {}
            for raw in raw_meta:
                if ":" not in raw:
                    continue
                key, value = raw.split(":", 1)
                meta[key.strip().lower()] = value.strip().strip("'\"")
            return meta, body
    return {}, text


def _sanitize_plaintext(md_body: str) -> str:
    # Strip fenced code blocks completely.
    text = re.sub(r"```.*?```", " ", md_body, flags=re.DOTALL)
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.DOTALL)
    # Remove inline code delimiters.
    text = re.sub(r"`([^`]*)`", r"\1", text)
    # Markdown links/images -> keep label.
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Strip HTML/script tags and entities.
    text = re.sub(r"<script.*?>.*?</script>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style.*?>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    # Remove markdown markers/noise.
    text = re.sub(r"^[#>\-\*\+\d\.\s]+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_style_key(value: str | None) -> str | None:
    if not value:
        return None
    key = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    if not key:
        return None
    return STYLE_ALIASES.get(key)


def _choose_style(plain_text: str, meta: dict[str, str]) -> str:
    explicit = _normalize_style_key(meta.get("note_style") or meta.get("myos_note_style"))
    if explicit:
        return explicit

    chars = len(plain_text)
    words = len(plain_text.split())
    # Tiny/short notes feel like sticky notes.
    if chars <= 180 and words <= 35:
        return "postit"
    # Medium-length text reads well on a plain "A4 sheet" style.
    if chars <= 1200 and words <= 220:
        return "sheet"
    return "notebook"


def _validate_color(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not HEX_COLOR_RE.fullmatch(value):
        return None
    if len(value) == 4:
        # #abc -> #aabbcc
        return f"#{value[1]*2}{value[2]*2}{value[3]*2}".lower()
    return value.lower()


def _font_paths() -> list[str]:
    return [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]


def _draw_pillow_badge(draw, size: int, style: str) -> None:
    from PIL import ImageFont

    label = STYLE_BADGES.get(style)
    if not label:
        return
    x0 = int(size * 0.08)
    y0 = int(size * 0.05)
    x1 = x0 + int(size * 0.22)
    y1 = y0 + int(size * 0.08)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=6, fill="#212121", outline="#424242", width=1)
    font = ImageFont.load_default()
    draw.text((x0 + 7, y0 + 4), label, fill="#f2f2f2", font=font)


def _try_render_with_pillow(
    output_path: Path,
    size: int,
    style: str,
    text: str,
    bg_color: str | None,
) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return False

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if style == "postit":
        fill = bg_color or "#fff59d"
        x0 = int(size * 0.10)
        y0 = int(size * 0.08)
        x1 = int(size * 0.90)
        y1 = int(size * 0.88)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.05), fill=fill, outline="#b9ae67", width=2)
        fold = int(size * 0.14)
        draw.polygon([(x1 - fold, y0), (x1, y0), (x1, y0 + fold)], fill="#efe39a", outline="#b9ae67")
        text_box = (x0 + int(size * 0.05), y0 + int(size * 0.08), x1 - int(size * 0.05), y1 - int(size * 0.05))
        ink = "#2d2d2d"
        max_lines = 7
    elif style == "sheet":
        fill = bg_color or "#ffffff"
        x0 = int(size * 0.14)
        y0 = int(size * 0.06)
        x1 = int(size * 0.88)
        y1 = int(size * 0.94)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.02), fill=fill, outline="#c8c8c8", width=2)
        fold = int(size * 0.10)
        draw.polygon([(x1 - fold, y0), (x1, y0), (x1, y0 + fold)], fill="#ececec", outline="#c8c8c8")
        for i in range(7):
            ly = y0 + int(size * 0.13) + i * int(size * 0.09)
            draw.line((x0 + int(size * 0.05), ly, x1 - int(size * 0.05), ly), fill="#e6e6e6", width=1)
        text_box = (x0 + int(size * 0.06), y0 + int(size * 0.14), x1 - int(size * 0.06), y1 - int(size * 0.05))
        ink = "#2b2b2b"
        max_lines = 10
    elif style == "chat":
        fill = bg_color or "#d7efff"
        x0 = int(size * 0.10)
        y0 = int(size * 0.12)
        x1 = int(size * 0.90)
        y1 = int(size * 0.78)
        draw.rectangle((x0, y0, x1, y1), fill=fill, outline="#6f9fc2", width=3)
        tail = [(x0 + int(size * 0.20), y1), (x0 + int(size * 0.30), y1), (x0 + int(size * 0.24), y1 + int(size * 0.11))]
        draw.polygon(tail, fill=fill, outline="#6f9fc2")
        # Pixel-ish top strip.
        for i in range(8):
            bx = x0 + 6 + i * int(size * 0.09)
            draw.rectangle((bx, y0 + 6, bx + int(size * 0.05), y0 + int(size * 0.03)), fill="#8ab6d7")
        text_box = (x0 + int(size * 0.05), y0 + int(size * 0.08), x1 - int(size * 0.04), y1 - int(size * 0.06))
        ink = "#17314a"
        max_lines = 7
    elif style == "cloud":
        fill = bg_color or "#eef3ff"
        cx = int(size * 0.50)
        cy = int(size * 0.50)
        r = int(size * 0.16)
        bubbles = [
            (cx - r * 2, cy - r, r * 2, r * 2),
            (cx - r, cy - r * 2, r * 2, r * 2),
            (cx, cy - r * 2, r * 2, r * 2),
            (cx + r, cy - r, r * 2, r * 2),
            (cx - r, cy, r * 3, r * 2),
        ]
        for x, y, w, h in bubbles:
            draw.ellipse((x, y, x + w, y + h), fill=fill, outline="#a5b0d4", width=2)
        text_box = (int(size * 0.24), int(size * 0.30), int(size * 0.76), int(size * 0.72))
        ink = "#2c3554"
        max_lines = 6
    elif style == "config":
        fill = bg_color or "#eceff1"
        x0 = int(size * 0.14)
        y0 = int(size * 0.08)
        x1 = int(size * 0.88)
        y1 = int(size * 0.92)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.02), fill=fill, outline="#b0b7bb", width=2)
        # Gear-ish symbol.
        gx = x1 - int(size * 0.16)
        gy = y0 + int(size * 0.14)
        gr = int(size * 0.05)
        draw.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill="#98a3ab", outline="#6f7980", width=2)
        for i in range(8):
            ang = i * 45
            dx = int((gr + 8) * (1 if ang in (0, 45, 315) else -1 if ang in (135, 180, 225) else 0))
            dy = int((gr + 8) * (1 if ang in (45, 90, 135) else -1 if ang in (225, 270, 315) else 0))
            draw.rectangle((gx + dx - 2, gy + dy - 2, gx + dx + 2, gy + dy + 2), fill="#6f7980")
        text_box = (x0 + int(size * 0.06), y0 + int(size * 0.14), x1 - int(size * 0.06), y1 - int(size * 0.06))
        ink = "#283238"
        max_lines = 9
    else:
        fill = bg_color or "#f4f1e8"
        x0 = int(size * 0.12)
        y0 = int(size * 0.06)
        x1 = int(size * 0.90)
        y1 = int(size * 0.94)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=int(size * 0.03), fill=fill, outline="#b6b2a8", width=2)
        # Notebook binding and ruled lines.
        bind_x = x0 + int(size * 0.07)
        draw.rectangle((x0, y0, bind_x, y1), fill="#ddd8cb")
        for i in range(6):
            cy = y0 + int((i + 1) * (y1 - y0) / 7)
            draw.ellipse((x0 + 6, cy - 4, x0 + 14, cy + 4), fill="#b5b1a8")
        for i in range(7):
            ly = y0 + int(size * 0.09) + i * int(size * 0.10)
            draw.line((bind_x + 8, ly, x1 - 8, ly), fill="#d8d2c6", width=1)
        text_box = (bind_x + int(size * 0.03), y0 + int(size * 0.08), x1 - int(size * 0.04), y1 - int(size * 0.05))
        ink = "#2f2f2f"
        max_lines = 9

    # Font selection.
    font = None
    for fp in _font_paths():
        if Path(fp).exists():
            try:
                font = ImageFont.truetype(fp, max(12, int(size * 0.072)))
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    text = text or "Markdown note"
    line_width_chars = max(14, int((text_box[2] - text_box[0]) / max(7, int(size * 0.035))))
    lines = []
    for paragraph in re.split(r"\s{2,}", text):
        lines.extend(wrap(paragraph, width=line_width_chars))
        if len(lines) >= max_lines:
            break
    lines = lines[:max_lines]
    if lines and len(lines) == max_lines and len(text) > sum(len(line) for line in lines):
        lines[-1] = lines[-1][: max(1, len(lines[-1]) - 1)] + "…"

    y = text_box[1]
    for line in lines:
        draw.text((text_box[0], y), line, fill=ink, font=font)
        y += int(size * 0.085)
    _draw_pillow_badge(draw, size, style)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    return True


def _render_with_qt(output_path: Path, size: int, style: str, text: str, bg_color: str | None) -> bool:
    # Fallback path when Pillow is unavailable.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtCore import Qt, QRectF
        from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPainterPath, QPen
    except Exception:
        return False

    app = QGuiApplication.instance() or QGuiApplication([])
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    p = QPainter(image)
    p.setRenderHint(QPainter.Antialiasing, True)

    if style == "postit":
        fill = QColor(bg_color or "#fff59d")
        x0, y0 = int(size * 0.10), int(size * 0.08)
        w, h = int(size * 0.80), int(size * 0.80)
        rect = QRectF(x0, y0, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, size * 0.05, size * 0.05)
        p.fillPath(path, fill)
        p.setPen(QPen(QColor("#b9ae67"), 2))
        p.drawPath(path)
        fold = int(size * 0.14)
        fold_path = QPainterPath()
        fold_path.moveTo(x0 + w - fold, y0)
        fold_path.lineTo(x0 + w, y0)
        fold_path.lineTo(x0 + w, y0 + fold)
        fold_path.closeSubpath()
        p.fillPath(fold_path, QColor("#efe39a"))
        p.drawPath(fold_path)
        text_rect = QRectF(x0 + size * 0.05, y0 + size * 0.08, w - size * 0.10, h - size * 0.12)
        max_lines = 7
    elif style == "sheet":
        fill = QColor(bg_color or "#ffffff")
        x0, y0 = int(size * 0.14), int(size * 0.06)
        w, h = int(size * 0.74), int(size * 0.88)
        rect = QRectF(x0, y0, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, size * 0.02, size * 0.02)
        p.fillPath(path, fill)
        p.setPen(QPen(QColor("#c8c8c8"), 2))
        p.drawPath(path)
        fold = int(size * 0.10)
        fold_path = QPainterPath()
        fold_path.moveTo(x0 + w - fold, y0)
        fold_path.lineTo(x0 + w, y0)
        fold_path.lineTo(x0 + w, y0 + fold)
        fold_path.closeSubpath()
        p.fillPath(fold_path, QColor("#ececec"))
        p.drawPath(fold_path)
        p.setPen(QPen(QColor("#e6e6e6"), 1))
        for i in range(7):
            ly = y0 + int(size * 0.13) + i * int(size * 0.09)
            p.drawLine(x0 + int(size * 0.05), ly, x0 + w - int(size * 0.05), ly)
        text_rect = QRectF(x0 + size * 0.06, y0 + size * 0.14, w - size * 0.12, h - size * 0.20)
        max_lines = 10
    elif style == "chat":
        fill = QColor(bg_color or "#d7efff")
        x0, y0 = int(size * 0.10), int(size * 0.12)
        w, h = int(size * 0.80), int(size * 0.66)
        p.fillRect(QRectF(x0, y0, w, h), fill)
        p.setPen(QPen(QColor("#6f9fc2"), 3))
        p.drawRect(QRectF(x0, y0, w, h))
        tail = QPainterPath()
        tail.moveTo(x0 + int(size * 0.20), y0 + h)
        tail.lineTo(x0 + int(size * 0.30), y0 + h)
        tail.lineTo(x0 + int(size * 0.24), y0 + h + int(size * 0.11))
        tail.closeSubpath()
        p.fillPath(tail, fill)
        p.drawPath(tail)
        text_rect = QRectF(x0 + size * 0.05, y0 + size * 0.08, w - size * 0.09, h - size * 0.12)
        max_lines = 7
    elif style == "cloud":
        fill = QColor(bg_color or "#eef3ff")
        p.setPen(QPen(QColor("#a5b0d4"), 2))
        p.setBrush(fill)
        r = int(size * 0.16)
        cx, cy = int(size * 0.50), int(size * 0.50)
        ellipses = [
            QRectF(cx - r * 2, cy - r, r * 2, r * 2),
            QRectF(cx - r, cy - r * 2, r * 2, r * 2),
            QRectF(cx, cy - r * 2, r * 2, r * 2),
            QRectF(cx + r, cy - r, r * 2, r * 2),
            QRectF(cx - r, cy, r * 3, r * 2),
        ]
        for e in ellipses:
            p.drawEllipse(e)
        text_rect = QRectF(size * 0.24, size * 0.30, size * 0.52, size * 0.42)
        max_lines = 6
    elif style == "config":
        fill = QColor(bg_color or "#eceff1")
        x0, y0 = int(size * 0.14), int(size * 0.08)
        w, h = int(size * 0.74), int(size * 0.84)
        rect = QRectF(x0, y0, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, size * 0.02, size * 0.02)
        p.fillPath(path, fill)
        p.setPen(QPen(QColor("#b0b7bb"), 2))
        p.drawPath(path)
        gx = x0 + w - int(size * 0.16)
        gy = y0 + int(size * 0.14)
        gr = int(size * 0.05)
        p.setPen(QPen(QColor("#6f7980"), 2))
        p.setBrush(QColor("#98a3ab"))
        p.drawEllipse(QRectF(gx - gr, gy - gr, gr * 2, gr * 2))
        text_rect = QRectF(x0 + size * 0.06, y0 + size * 0.14, w - size * 0.12, h - size * 0.20)
        max_lines = 9
    else:
        fill = QColor(bg_color or "#f4f1e8")
        x0, y0 = int(size * 0.12), int(size * 0.06)
        w, h = int(size * 0.78), int(size * 0.88)
        rect = QRectF(x0, y0, w, h)
        path = QPainterPath()
        path.addRoundedRect(rect, size * 0.03, size * 0.03)
        p.fillPath(path, fill)
        p.setPen(QPen(QColor("#b6b2a8"), 2))
        p.drawPath(path)
        bind_w = int(size * 0.07)
        p.fillRect(QRectF(x0, y0, bind_w, h), QColor("#ddd8cb"))
        p.setPen(QPen(QColor("#d8d2c6"), 1))
        for i in range(7):
            ly = y0 + int(size * 0.09) + i * int(size * 0.10)
            p.drawLine(x0 + bind_w + 8, ly, x0 + w - 8, ly)
        text_rect = QRectF(x0 + bind_w + size * 0.03, y0 + size * 0.08, w - bind_w - size * 0.07, h - size * 0.12)
        max_lines = 9

    font = QFont("Sans Serif", max(9, int(size * 0.040)))
    p.setFont(font)
    p.setPen(QColor("#2f2f2f"))
    short = (text or "Markdown note").strip()
    words = short.split()
    lines = []
    line = ""
    fm = p.fontMetrics()
    max_w = int(text_rect.width())
    for word in words:
        candidate = f"{line} {word}".strip()
        if fm.horizontalAdvance(candidate) <= max_w or not line:
            line = candidate
        else:
            lines.append(line)
            line = word
        if len(lines) >= max_lines:
            break
    if line and len(lines) < max_lines:
        lines.append(line)
    if len(lines) >= max_lines and len(words) > 0:
        lines[-1] = (lines[-1][:-1] + "…") if len(lines[-1]) > 1 else lines[-1]
    draw_text = "\n".join(lines[:max_lines])
    p.drawText(text_rect, int(Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignTop), draw_text)

    badge = STYLE_BADGES.get(style)
    if badge:
        bx = int(size * 0.08)
        by = int(size * 0.05)
        bw = int(size * 0.22)
        bh = int(size * 0.08)
        p.fillRect(QRectF(bx, by, bw, bh), QColor("#212121"))
        p.setPen(QColor("#f2f2f2"))
        badge_font = QFont("Sans Serif", max(7, int(size * 0.030)))
        p.setFont(badge_font)
        p.drawText(QRectF(bx + 4, by + 1, bw - 6, bh - 2), int(Qt.AlignCenter), badge)
    p.end()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok = image.save(str(output_path), "PNG")
    # Prevent "unused var" lint in some environments.
    _ = app
    return bool(ok)


def main() -> int:
    args = _parse_args()
    try:
        raw = args.input_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 1

    meta, body = _extract_frontmatter_and_body(raw)
    bg = _validate_color(meta.get("background_color"))
    plain = _sanitize_plaintext(body)
    style = _choose_style(plain, meta)

    if _try_render_with_pillow(args.output_path, args.thumb_size, style, plain, bg):
        return 0
    if _render_with_qt(args.output_path, args.thumb_size, style, plain, bg):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
