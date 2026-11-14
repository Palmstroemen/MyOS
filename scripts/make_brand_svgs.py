#!/usr/bin/env python3
"""The brand's pictures (assets/brand): the square icon - a bento box, "sei" in three
compartments on top, "t" and "on" below - its small form without letters (16 and 32 px),
and the wordmark. The letters are outlines (paths) of a font, so the pictures look the same
everywhere, with or without that font installed.

    python3 scripts/make_brand_svgs.py [--font PATH] [--out assets/brand]
"""

import argparse
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:  # started as a script: make core importable
    sys.path.insert(0, str(REPO_ROOT))

from core.brand import NAME, file_name  # noqa: E402

WORD = NAME.lower()  # the name as the pictures show it
FONT = Path("/usr/share/fonts/truetype/open-sans/OpenSans-Semibold.ttf")  # SIL Open Font License
BOX = "#4a3478"  # the box and the letters
PAPER = "#f3ecdf"  # the compartments

SIZE = 160
WALL = 10  # outer wall and walls between the compartments: 1 px at 16 px
ROW = (SIZE - 3 * WALL) / 2
COL = (SIZE - 4 * WALL) / 3
LETTER_SIZE = 46


class Letters:
    def __init__(self, font_path: Path):
        self.font = TTFont(str(font_path))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.x_height = self.font["OS/2"].sxHeight

    def _names(self, text):
        return [self.cmap[ord(c)] for c in text]

    def bounds(self, text, size):
        """Ink box (x0, x1) of text at size, starting at 0 (font units scaled)."""
        scale, x, lo, hi = size / self.upm, 0, None, None
        for name in self._names(text):
            pen = BoundsPen(self.glyphs)
            self.glyphs[name].draw(pen)
            if pen.bounds:
                lo = x + pen.bounds[0] if lo is None else min(lo, x + pen.bounds[0])
                hi = x + pen.bounds[2] if hi is None else max(hi, x + pen.bounds[2])
            x += self.glyphs[name].width
        return lo * scale, hi * scale

    def path(self, text, size, x, baseline):
        """SVG path data of text, its left edge of ink at x, on baseline."""
        scale = size / self.upm
        ink_left = self.bounds(text, size)[0]
        pen = SVGPathPen(self.glyphs)
        advance = 0
        for name in self._names(text):
            # Font units grow upwards, SVG downwards: flip y.
            transform = (scale, 0, 0, -scale, x - ink_left + advance * scale, baseline)
            self.glyphs[name].draw(TransformPen(pen, transform))
            advance += self.glyphs[name].width
        return pen.getCommands()

    def centered(self, text, size, left, top, width, height):
        """Path of text centred in a compartment: by its ink across, by the x-height down
        (so the letters of a row share one baseline)."""
        x0, x1 = self.bounds(text, size)
        x = left + (width - (x1 - x0)) / 2
        baseline = top + height / 2 + self.x_height * size / self.upm / 2
        return self.path(text, size, x, baseline)


def _compartments():
    """(text, x, y, width, height): s e i on top, t and on below (for seiton)."""
    top, bottom = WALL, 2 * WALL + ROW
    cols = [WALL + i * (COL + WALL) for i in range(3)]
    w = WORD
    return [(w[0], cols[0], top, COL, ROW), (w[1], cols[1], top, COL, ROW), (w[2], cols[2], top, COL, ROW),
            (w[3], cols[0], bottom, COL, ROW), (w[4:], cols[1], bottom, 2 * COL + WALL, ROW)]


def _n(v: float) -> str:
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _icon_body(letters: Letters) -> str:
    parts = [f'<rect width="{SIZE}" height="{SIZE}" fill="{BOX}"/>']
    for _text, x, y, w, h in _compartments():
        parts.append(f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}" fill="{PAPER}"/>')
    paths = " ".join(letters.centered(t, LETTER_SIZE, x, y, w, h) for t, x, y, w, h in _compartments())
    parts.append(f'<path fill="{BOX}" d="{paths}"/>')
    return "\n  ".join(parts)


def icon(letters: Letters) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}">\n'
            f'  <title>{WORD}</title>\n  {_icon_body(letters)}\n</svg>\n')


def icon_small() -> str:
    """16 px on the pixel grid: walls of 1 px across, 2 px between the rows; no letters."""
    cells = [(1, 1, 4, 6), (6, 1, 4, 6), (11, 1, 4, 6), (1, 9, 4, 6), (6, 9, 9, 6)]
    rects = "\n  ".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{PAPER}"/>' for x, y, w, h in cells)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16" '
            'shape-rendering="crispEdges">\n'
            f'  <title>{WORD}</title>\n  <rect width="16" height="16" fill="{BOX}"/>\n  {rects}\n</svg>\n')


def wordmark(letters: Letters) -> str:
    """The icon, and beside it the name, its x-height as high as a row of the box."""
    size = ROW / (letters.x_height / letters.upm)
    gap = SIZE * 0.18
    baseline = 2 * WALL + 2 * ROW  # the name sits on the floor of the lower row
    x0, x1 = letters.bounds(WORD, size)
    width = SIZE + gap + (x1 - x0)
    name = letters.path(WORD, size, SIZE + gap, baseline)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_n(width)} {SIZE}" '
            f'width="{_n(width)}" height="{SIZE}">\n  <title>{WORD}</title>\n  {_icon_body(letters)}\n'
            f'  <path fill="{BOX}" d="{name}"/>\n</svg>\n')


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--font", type=Path, default=FONT)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "assets" / "brand")
    args = parser.parse_args(argv)
    if not args.font.is_file():
        print(f"font not found: {args.font}", file=sys.stderr)
        return 1
    letters = Letters(args.font)
    args.out.mkdir(parents=True, exist_ok=True)
    files = {file_name("icon.svg"): icon(letters), file_name("icon-small.svg"): icon_small(),
             file_name("wordmark.svg"): wordmark(letters)}
    for name, text in files.items():
        (args.out / name).write_text(text, encoding="utf-8")
        print(args.out / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
