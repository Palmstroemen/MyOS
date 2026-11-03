"""The light rendering on screen: a QTextBrowser that lays out light_render's lines the way the
editor's page does (same fonts, sizes, line heights, widths and colours), so a note looks the
same whether it is only read or being edited.

Two differences between Qt and the browser are evened out here: Qt sets the text at the top of
a line while the browser centres it in the line (each line is moved down by the difference; Qt
merges margins like CSS, so the first line's goes into the frame), and Qt draws backgrounds and
borders of a line only as high as its text (code backgrounds, quote bars and rules are painted
over the full line).
"""

from __future__ import annotations

import html as html_module
import math
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import (QBrush, QFontInfo, QGuiApplication, QColor, QFont, QFontDatabase, QFontMetricsF, QImage, QImageReader,
                           QPainter, QPen, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument, QTextImageFormat, QTextLayout,
                           QTextFrameFormat, QTextLength, QTextTableFormat)
from PySide6.QtWidgets import QTextBrowser

try:
    from . import light_render as lr
except ImportError:  # run as a script from PostFix/
    import light_render as lr

QUOTE_STATE, RULE_STATE, CODE_STATE = 1, 2, 3
_IMG = re.compile(r'<img src="(?P<src>[^"]*)"(?: width="(?P<width>\d+)")?[^>]*>')
TABLE_TOP, TABLE_BOTTOM = 1, 3
CELL_TEXT_DOWN = 2.5
BROWSER_SCROLLBAR = 11  # px, the editor page's scroll bar (editor_host.PAGE)
LINE_HEIGHT_PROPERTY = 0x100000 + 1
WANTED_TOP_PROPERTY = 0x100000 + 2  # the top margin the browser's layout asks for, maybe < 0
BROWSER_TOP_PROPERTY = 0x100000 + 3  # where the editor's line starts, from Qt's paragraph top  # QTextFormat.UserProperty + 1: the line height in px
QUOTE_BAR, QUOTE_PAD = 3, 12


def fonts() -> tuple[str, str]:
    """The text and code fonts both sides use: the editor's wish if installed, else the system's
    (the browser and Qt may resolve "system-ui" differently - so PostFix decides for both)."""
    families = set(QFontDatabase.families())
    body = next((f for f in ("Inter", "Segoe UI") if f in families),
                QFontDatabase.systemFont(QFontDatabase.GeneralFont).family())
    mono = next((f for f in ("JetBrains Mono",) if f in families),
                QFontDatabase.systemFont(QFontDatabase.FixedFont).family())
    # The installed family, not an alias like "Sans" each side may resolve on its own.
    return QFontInfo(QFont(body)).family(), QFontInfo(QFont(mono)).family()


def _font(family: str, px: float, bold: bool = False) -> QFont:
    font = QFont(family)
    # The browser sizes fonts in fractions of a pixel (0.92em = 14.72 px); Qt's pixel sizes are
    # whole, its point sizes are not.
    font.setPointSizeF(px * 72 / _dpi())
    font.setBold(bold)
    return font


def _dpi() -> float:
    screen = QGuiApplication.primaryScreen()
    return screen.logicalDotsPerInchY() if screen is not None else 96.0


def _px(font: QFont) -> float:
    return font.pointSizeF() * _dpi() / 72


import math
import math
import math
_NATURAL: dict = {}


def _natural(font: QFont) -> tuple[float, float]:
    """Height and ascent of a line of this font as Qt lays it out."""
    key = (font.family(), font.pointSizeF(), font.bold())
    if key not in _NATURAL:
        layout = QTextLayout("Hg", font)
        layout.beginLayout()
        line = layout.createLine()
        layout.endLayout()
        _NATURAL[key] = (line.height(), line.ascent())
    return _NATURAL[key]


def _shift(font: QFont, line_height: float) -> float:
    """How much higher Qt sets the baseline in a line of this height than the browser does
    (negative: Qt sets the text at the top of the line, the browser centres ascent and descent,
    in whole pixels)."""
    metrics = QFontMetricsF(font)
    browser = (line_height + round(metrics.ascent()) - round(metrics.descent())) / 2
    return _natural(font)[1] - browser


def _line_format(font: QFont, line_height: float) -> QTextBlockFormat:
    fmt = QTextBlockFormat()
    # Lines exactly line_height apart: Qt's own line height plus the rest as distance.
    fmt.setLineHeight(line_height - _natural(font)[0], QTextBlockFormat.LineDistanceHeight.value)
    fmt.setProperty(LINE_HEIGHT_PROPERTY, line_height)
    return fmt


def _unit(px: float) -> float:
    """px as the browser lays out: in 64ths of a pixel, rounded down (26.4 -> 26.390625)."""
    return math.floor(px * 64) / 64


def _block_font(block: lr.Block, body: str, mono: str) -> tuple[QFont, float]:
    size = lr.FONT_SIZE
    if block.heading in lr.HEADING_SIZE:
        size = lr.FONT_SIZE * lr.HEADING_SIZE[block.heading]
    if block.code:
        return _font(mono, lr.FONT_SIZE * 0.92), _unit(lr.FONT_SIZE * 0.92 * lr.LINE_HEIGHT)
    factor = lr.HEADING_LINE_HEIGHT.get(block.heading, lr.LINE_HEIGHT)
    return _font(body, size, bold=block.heading > 0), _unit(size * factor)


def _checkbox(checked: bool, font: QFont) -> QImage:
    """The browser's check box (light theme): 13 px, grey frame, blue when ticked, 0.45em after
    it, its middle half an x-height above the baseline. As high as a line of text and set at its
    bottom, so the line stays as high as the others."""
    height, ascent = _natural(font)
    descent = height - ascent
    box_top = height - descent - QFontMetricsF(font).xHeight() / 2 - 6.5
    image = QImage(QSize(13 + round(0.45 * lr.FONT_SIZE), int(height) - 1), QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(0, round(box_top) - 1)
    if checked:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#0075ff"))
        painter.drawRoundedRect(QRectF(0, 0, 13, 13), 2, 2)
        painter.setPen(QPen(QColor("white"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPolyline([QPointF(3.2, 6.8), QPointF(5.6, 9.2), QPointF(10, 4.2)])
    else:
        painter.setPen(QPen(QColor("#767676"), 1))
        painter.setBrush(QColor("white"))
        painter.drawRoundedRect(QRectF(0.5, 0.5, 12, 12), 2, 2)
    painter.end()
    return image


def fill(document: QTextDocument, body: str, width: int, base_dir: Optional[Path] = None,
         view_width: Optional[int] = None) -> list[int]:
    """Lay the note out in document as the editor would in a page width pixels wide (without
    its scroll bar), in a view view_width wide (default: width). Returns for each line of body
    the number of the paragraph that shows it."""
    body_family, mono_family = fonts()
    blocks = lr.render_lines(body)
    document.clear()
    document.setDocumentMargin(0)
    document.setDefaultFont(_font(body_family, lr.FONT_SIZE))
    document.setDefaultStyleSheet("")
    if base_dir is not None:
        document.setBaseUrl(QUrl.fromLocalFile(str(Path(base_dir).resolve()) + "/"))
    text_font = _font(body_family, lr.FONT_SIZE)
    document.addResource(QTextDocument.ImageResource, QUrl("postfix-task:on"), _checkbox(True, text_font))
    document.addResource(QTextDocument.ImageResource, QUrl("postfix-task:off"), _checkbox(False, text_font))

    content = min(lr.CONTENT_WIDTH, width)
    side = (width - content) / 2 + lr.PAD_SIDE
    text_width = content - 2 * lr.PAD_SIDE

    root = document.rootFrame().frameFormat()
    root.setLeftMargin(side)
    root.setRightMargin((view_width or width) - side - text_width)
    root.setBottomMargin(lr.PAD_BOTTOM)
    cursor = QTextCursor(document)
    previous_shift = 0.0
    first = True
    line_blocks: list[int] = []
    for block in blocks:
        font, line_height = _block_font(block, body_family, mono_family)
        picture = bool(block.images) and block.kind == "line"
        if picture:
            # A line with a picture is as high as the picture (set at the line's bottom), the
            # picture at its top - in the browser as in Qt.
            shift = 0.0
            fmt = QTextBlockFormat()
            fmt.setLineHeight(0, QTextBlockFormat.LineDistanceHeight.value)
            fmt.setProperty(LINE_HEIGHT_PROPERTY, line_height)
        else:
            shift = _shift(font, line_height)
            fmt = _line_format(font, line_height)
        top = 0.0
        if block.heading in lr.HEADING_PAD_TOP:
            top += _unit(lr.HEADING_PAD_TOP[block.heading] * _px(font))
        # Where the editor's line starts compared with Qt's paragraph (its padding included).
        fmt.setProperty(BROWSER_TOP_PROPERTY, shift - top)
        top += previous_shift - shift  # every line moved down by its shift
        if first:
            root.setTopMargin(lr.PAD_TOP + top)
        else:
            fmt.setTopMargin(max(0.0, top))
            fmt.setProperty(WANTED_TOP_PROPERTY, top)
        if block.quote:
            fmt.setLeftMargin(QUOTE_BAR + QUOTE_PAD)
        char = QTextCharFormat()
        char.setFont(font)
        char.setForeground(QColor(lr.COLORS["fg"]))
        if block.kind == "table":
            # Qt keeps the paragraph a table is inserted in in front of it: one of no height.
            holder = QTextBlockFormat()
            holder.setLineHeight(0, QTextBlockFormat.FixedHeight.value)
            tiny = QTextCharFormat()
            tiny.setFontPointSize(0.1)
            holder.setProperty(BROWSER_TOP_PROPERTY, -TABLE_TOP)
            if first:
                cursor.setBlockFormat(holder)
                cursor.setBlockCharFormat(tiny)
            else:
                cursor.insertBlock(holder, tiny)
            line_blocks += [cursor.block().blockNumber()] * block.lines
            if first:
                root.setTopMargin(lr.PAD_TOP)
            _table(cursor, block, font, line_height)
            cursor.setBlockFormat(holder)  # Qt's paragraph after the table: of no height too
            cursor.setBlockCharFormat(tiny)
            first, previous_shift = False, 0.0
            continue
        if first:
            cursor.setBlockFormat(fmt)
            cursor.setBlockCharFormat(char)
            cursor.setCharFormat(char)
        else:
            cursor.insertBlock(fmt, char)
        first = False
        line_blocks += [cursor.block().blockNumber()] * block.lines
        if block.kind == "rule":
            cursor.block().setUserState(RULE_STATE)
        elif block.quote:
            cursor.block().setUserState(QUOTE_STATE)
        elif block.code:
            cursor.block().setUserState(CODE_STATE)
        html = _fit_images(block.html.replace("__MONO__", mono_family), block.images, text_width, base_dir)
        # Text as HTML, pictures (and check boxes) on their own: a picture inserted as HTML makes
        # Qt put a stray frame in front of the next table.
        parts, at = [], 0
        for image in _IMG.finditer(html):
            parts += [html[at:image.start()], image]
            at = image.end()
        parts.append(html[at:])
        for part in parts:
            image = part if isinstance(part, re.Match) else None
            if image:
                picture = QTextImageFormat()
                picture.setName(html_module.unescape(image.group("src")))
                if image.group("width"):
                    picture.setWidth(float(image.group("width")))
                picture.setVerticalAlignment(QTextCharFormat.AlignBottom)
                cursor.insertImage(picture)
            elif part:
                part = _spaces_that_count(part)
                cursor.insertHtml(f'<span style="white-space: pre-wrap; font-family: \'{font.family()}\';'
                                  f' font-size: {font.pointSizeF():.3f}pt;{" font-weight: 700;" if block.heading else ""}'
                                  f' color: {lr.COLORS["fg"]}">{part}</span>')
        cursor.setBlockFormat(fmt)
        previous_shift = shift
    document.rootFrame().setFrameFormat(root)
    _take_back_negative_margins(document, view_width or width)
    return line_blocks


def _take_back_negative_margins(document: QTextDocument, width: float):
    """Qt knows no negative margins: where a line should start a little higher (after a heading
    that the browser centres differently), the line before gets that much shorter instead."""
    document.setTextWidth(width)
    document.documentLayout()  # laid out: the lines are counted
    previous = None
    block = document.begin()
    while block.isValid():
        wanted = block.blockFormat().property(WANTED_TOP_PROPERTY)
        if isinstance(wanted, float) and wanted < 0 and previous is not None:
            lines = max(1, previous.layout().lineCount())
            fmt = previous.blockFormat()
            if fmt.lineHeightType() == QTextBlockFormat.LineDistanceHeight.value:
                fmt.setLineHeight(fmt.lineHeight() + wanted / lines, QTextBlockFormat.LineDistanceHeight.value)
                QTextCursor(previous).setBlockFormat(fmt)
        previous = block
        block = block.next()
    # Qt lays out again only from the first change on - and loses lines after a picture in long
    # notes doing so (measured): all of it once more.
    document.markContentsDirty(0, document.characterCount())


def _spaces_that_count(html: str) -> str:
    """The editor wraps with white-space: break-spaces - a space at a line's end must fit too;
    Qt lets it hang past the line. A zero-width break after every space: the line breaks after
    it, so the space is no longer at the line's end and counts."""
    return "".join(piece if piece.startswith("<") else piece.replace(" ", " \u200b")
                   for piece in re.split(r"(<[^>]*>)", html))


def _fit_images(html: str, images: list, text_width: float, base_dir: Optional[Path]) -> str:
    # max-width: 100% - Qt knows no max-width, so the width is given where a picture is wider.
    for src, width in images:
        if width:
            continue
        path = Path(src) if Path(src).is_absolute() or base_dir is None else Path(base_dir) / src
        size = QImageReader(str(path)).size()
        if size.isValid() and size.width() > text_width:
            html = html.replace(f'src="{src}"', f'src="{src}" width="{int(text_width)}"', 1)
    return html


def _table(cursor: QTextCursor, block: lr.Block, font: QFont, line_height: float):
    columns = max(len(row) for row in block.rows)
    fmt = QTextTableFormat()
    fmt.setBorderCollapse(True)
    fmt.setBorder(1)
    fmt.setBorderBrush(QBrush(QColor(lr.COLORS["quote"])))
    fmt.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)
    fmt.setCellSpacing(0)
    fmt.setCellPadding(0)
    # The browser's 6 px around the table; Qt adds 5 px above and 3 px below of its own (measured).
    fmt.setTopMargin(TABLE_TOP)
    fmt.setBottomMargin(TABLE_BOTTOM)
    fmt.setAlignment(Qt.AlignLeft)
    fmt.setWidth(QTextLength(QTextLength.VariableLength, 0))
    table = cursor.insertTable(len(block.rows), columns, fmt)
    for r, row in enumerate(block.rows):
        for c in range(columns):
            cell = table.cellAt(r, c)
            cell_fmt = cell.format().toTableCellFormat()
            cell_fmt.setLeftPadding(10)
            cell_fmt.setRightPadding(10)
            # 4 px around the text; the text lower by what the browser centres it more (measured).
            cell_fmt.setTopPadding(4 + CELL_TEXT_DOWN)
            cell_fmt.setBottomPadding(4 - CELL_TEXT_DOWN)
            if r == 0:
                cell_fmt.setBackground(QColor(0, 0, 0, 13))
            cell.setFormat(cell_fmt)
            cell_cursor = cell.firstCursorPosition()
            text = row[c] if c < len(row) else ""
            if not text:  # an empty cell has no line in the browser: only its padding
                empty = QTextBlockFormat()
                empty.setLineHeight(0, QTextBlockFormat.FixedHeight.value)
                tiny = QTextCharFormat()
                tiny.setFontPointSize(0.1)
                cell_cursor.setBlockFormat(empty)
                cell_cursor.setBlockCharFormat(tiny)
                continue
            cell_font = _font(font.family(), _px(font), bold=r == 0)
            cell_cursor.setBlockFormat(_line_format(cell_font, line_height))
            char = QTextCharFormat()
            char.setFont(cell_font)
            char.setForeground(QColor(lr.COLORS["fg"]))
            cell_cursor.insertText(text, char)
    cursor.movePosition(QTextCursor.End)


class LightBrowser(QTextBrowser):
    """A QTextBrowser that also paints the quote bars and rules of the light rendering."""

    def paintEvent(self, event):
        super().paintEvent(event)
        document = self.document()
        layout = document.documentLayout()
        root = document.rootFrame().frameFormat()
        painter = None
        dy = -self.verticalScrollBar().value()
        block = document.begin()
        while block.isValid():
            state = block.userState()
            if state in (QUOTE_STATE, RULE_STATE, CODE_STATE) and block.layout().lineCount():
                rect = layout.blockBoundingRect(block)
                lines = block.layout()
                line_height = block.blockFormat().property(LINE_HEIGHT_PROPERTY)
                # The full lines, as the browser draws them around the text.
                top = rect.top() + lines.lineAt(0).y() + self._shift_of(block) + dy
                height = lines.lineCount() * line_height
                if top + height >= 0 and top <= self.viewport().height():
                    if painter is None:
                        painter = QPainter(self.viewport())
                    left = root.leftMargin()
                    right = self.viewport().width() - root.rightMargin()
                    if state == QUOTE_STATE:
                        painter.fillRect(QRectF(left, top, QUOTE_BAR, height), QColor(lr.COLORS["quote"]))
                    elif state == CODE_STATE:
                        painter.fillRect(QRectF(left, top, right - left, height), QColor(0, 0, 0, 13))
                    else:
                        middle = round(top + height / 2) + 0.5
                        painter.setPen(QPen(QColor(lr.COLORS["quote"]), 1))
                        painter.drawLine(QPointF(left, middle), QPointF(right, middle))
            block = block.next()
        if painter is not None:
            painter.end()

    @staticmethod
    def _shift_of(block) -> float:
        # Where the browser's line starts compared with Qt's: Qt's text sits lower by the shift.
        fmt = block.charFormat()
        return _shift(fmt.font(), block.blockFormat().property(LINE_HEIGHT_PROPERTY))

    def show_note(self, body: str, base_dir: Optional[Path] = None):
        """Show body; laid out again whenever the view's width changes (a scroll bar, a resize)."""
        self._note = (body, base_dir)
        if getattr(self, "_laying_out", False):
            return  # a scroll bar came or went while laying out: again once this is done
        self._laying_out = True
        try:
            self._laid_out_width = self.viewport().width()
            scroll = self.verticalScrollBar().value()
            # The page is as wide as the view less the browser's scroll bar (when there is one).
            page = self._laid_out_width
            if self.verticalScrollBar().isVisible():
                page = self._laid_out_width + self.verticalScrollBar().width() - BROWSER_SCROLLBAR
            self._line_blocks = fill(self.document(), body, page, base_dir, view_width=self._laid_out_width)
            self.document().size()  # laid out now, so the scroll range is right again
            self.verticalScrollBar().setValue(scroll)
            # The browser's own cursor went along to the end while the note was put in; Qt keeps
            # it in view (on focus and the like): it goes where the view is.
            self._cursor_into_view()
        finally:
            self._laying_out = False
        if self.viewport().width() != self._laid_out_width:
            QTimer.singleShot(0, lambda: self.show_note(*self._note))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        note = getattr(self, "_note", None)
        if note is not None and self.viewport().width() != self._laid_out_width:
            self.show_note(*note)

    # --- lines and scrolling, in the editor's terms ---------------------------------------------

    def line_top(self, line: int) -> float:
        """Where line (0 = the first line of the body) starts, as the editor lays it out."""
        blocks = getattr(self, "_line_blocks", [])
        if not blocks:
            return 0.0
        number = blocks[max(0, min(line, len(blocks) - 1))]
        block = self.document().findBlockByNumber(number)
        rect = self.document().documentLayout().blockBoundingRect(block)
        delta = block.blockFormat().property(BROWSER_TOP_PROPERTY)
        return rect.top() + (delta if isinstance(delta, float) else 0.0)

    def top_line(self) -> tuple[int, float]:
        """The first line starting in view and how far below the view's top it starts."""
        scroll = self.verticalScrollBar().value()
        blocks = getattr(self, "_line_blocks", [])
        for line in range(len(blocks)):
            top = self.line_top(line)
            if top >= scroll - 0.5:
                return line, top - scroll
        return max(0, len(blocks) - 1), 0.0

    def scroll_to_line(self, line: int, offset: float):
        """Scroll so that line starts offset pixels below the view's top."""
        self.document().size()  # laid out, so the scroll range is right
        self.verticalScrollBar().setValue(round(self.line_top(line) - offset))
        self._cursor_into_view()

    def _cursor_into_view(self):
        # A line in the middle of the view: one surely in it, so setting it scrolls nothing.
        self.setTextCursor(self.cursorForPosition(QPoint(0, self.viewport().height() // 2)))
