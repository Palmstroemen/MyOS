"""Scope's icon in the taskbar: the theme's folder with the "P" its projects carry, so Scope is
told apart from the desktop's file browser (FolderItem.qml draws the same P on large icons)."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap

SIZES = (16, 22, 24, 32, 48, 64, 128, 256)
# As FolderItem's large icon: the badge band is 4/11 of the height, 2/11 above the bottom;
# the P is 0.85 of the band, a little right of centre (0.18 of the width).
BAND = 4 / 11
BOTTOM = 2 / 11
SHIFT = 0.18


def with_project_badge(folder: QIcon) -> QIcon:
    """folder with a black, bold, italic P on it, in every size the taskbar may ask for."""
    icon = QIcon()
    for size in SIZES:
        # At factor 1: on a HiDPI screen pixmap(size) answers twice the pixels, which the
        # centring below would crop.
        pixmap = folder.pixmap(QSize(size, size), 1.0)
        if pixmap.isNull():
            continue
        if pixmap.width() != size or pixmap.height() != size:
            canvas = QPixmap(size, size)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap((size - pixmap.width()) // 2, (size - pixmap.height()) // 2, pixmap)
            painter.end()
            pixmap = canvas
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        band = size * BAND
        font = QFont()
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(max(6, round(band * 0.85)))
        painter.setFont(font)
        painter.setPen(QColor("#000000"))
        area = QRectF(size * SHIFT, size - size * BOTTOM - band, size, band)
        painter.drawText(area, Qt.AlignCenter, "P")
        painter.end()
        icon.addPixmap(pixmap)
    return icon if not icon.isNull() else folder
