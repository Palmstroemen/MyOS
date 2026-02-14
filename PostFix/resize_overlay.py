"""Resize overlay widget for PostFix window edges."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QMainWindow


class PaperResizeOverlay(QFrame):
    """Transparent overlay to resize the window by paper edges."""

    EDGE = 8

    def __init__(self, window: QMainWindow):
        super().__init__()
        self._window = window
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setMouseTracking(True)
        self.setStyleSheet("QFrame { background: transparent; }")

    def _hit_edges(self, pos):
        rect = self.rect()
        edges = Qt.Edges()
        if pos.x() <= self.EDGE:
            edges |= Qt.LeftEdge
        if pos.x() >= rect.width() - self.EDGE:
            edges |= Qt.RightEdge
        if pos.y() <= self.EDGE:
            edges |= Qt.TopEdge
        if pos.y() >= rect.height() - self.EDGE:
            edges |= Qt.BottomEdge
        return edges

    def _update_cursor(self, edges):
        if edges.testFlag(Qt.LeftEdge) and edges.testFlag(Qt.TopEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges.testFlag(Qt.RightEdge) and edges.testFlag(Qt.BottomEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif edges.testFlag(Qt.RightEdge) and edges.testFlag(Qt.TopEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edges.testFlag(Qt.LeftEdge) and edges.testFlag(Qt.BottomEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        elif edges.testFlag(Qt.LeftEdge) or edges.testFlag(Qt.RightEdge):
            self.setCursor(Qt.SizeHorCursor)
        elif edges.testFlag(Qt.TopEdge) or edges.testFlag(Qt.BottomEdge):
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.unsetCursor()

    def mouseMoveEvent(self, event):
        edges = self._hit_edges(event.position().toPoint())
        self._update_cursor(edges)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        edges = self._hit_edges(event.position().toPoint())
        handle = self._window.windowHandle()
        if handle and edges:
            handle.startSystemResize(edges)
            event.accept()
            return
        super().mousePressEvent(event)
