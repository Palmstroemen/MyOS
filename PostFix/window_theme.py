"""Theme and fade behavior mixin for PostFixWindow."""

from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QTimer, QVariantAnimation
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QPushButton,
    QHBoxLayout,
    QWidget,
)


class WindowThemeMixin:
    """Styling, palette, and top/bottom bar fade helpers."""

    def apply_round_button_style(self, button: QPushButton, bg_color: str, border_color: str):
        button.setFixedSize(30, 30)
        button.setStyleSheet(
            """
            QPushButton {
                border-radius: 15px;
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid rgba(0, 0, 0, 60);
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 25);
            }
            """
        )

    def apply_oval_button_style(self, button: QPushButton, bg_color: str, border_color: str):
        button.setFixedHeight(30)
        button.setStyleSheet(
            """
            QPushButton {
                padding: 0 10px;
                border-radius: 14px;
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid rgba(0, 0, 0, 60);
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 25);
            }
            """
        )

    def open_palette(self, initial_hex: str, on_color, anchor: QWidget):
        colors = [
            "#ffffff", "#fff8b0", "#ffe082", "#ffd54f", "#ffb74d", "#ff8a65",
            "#e6f5a7", "#a5d6a7", "#80cbc4", "#90caf9", "#ce93d8", "#f48fb1",
        ]
        popup = QFrame(self)
        popup.setWindowFlags(Qt.Popup)
        popup.setWindowFlags(popup.windowFlags())
        popup.setStyleSheet("QFrame { background: #f7f7f7; border: 1px solid #cfcfcf; border-radius: 8px; }")
        grid = QGridLayout(popup)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)

        for idx, color in enumerate(colors):
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {color}; border: 1px solid #bdbdbd; border-radius: 11px; }}"
                f"QPushButton:hover {{ border: 2px solid #8c8c8c; }}"
            )
            btn.clicked.connect(lambda _, c=color: (on_color(QColor(c)), popup.close()))
            grid.addWidget(btn, idx // 6, idx % 6)

        pos = anchor.mapToGlobal(anchor.rect().bottomLeft()) + QPoint(0, 6)
        popup.move(pos)
        popup.show()

    def make_corner_widget(self) -> QWidget:
        corner = QFrame()
        corner.setFixedSize(20, 20)
        corner.setStyleSheet("QFrame { background-color: rgba(30, 30, 30, 128); }")
        return corner

    def make_strip_widget(self) -> QWidget:
        strip = QFrame()
        strip.setFixedWidth(40)
        strip.setStyleSheet("QFrame { background-color: #ffffff; }")
        return strip

    def make_strip_host(self, align_right: bool) -> tuple[QFrame, QFrame]:
        host = QFrame()
        layout = QHBoxLayout(host)
        layout.setContentsMargins(0, 0, 0, 0)
        if align_right:
            layout.addStretch()
        strip = self.make_strip_widget()
        layout.addWidget(strip)
        if not align_right:
            layout.addStretch()
        return host, strip

    def update_theme_color(self, color_hex: str):
        if color_hex == self._current_theme_color:
            return
        start = QColor(self._current_theme_color)
        end = QColor(color_hex)
        if self._theme_anim and self._theme_anim.state() == QVariantAnimation.Running:
            self._theme_anim.stop()
        self._theme_anim = QVariantAnimation(self)
        self._theme_anim.setDuration(1000)
        self._theme_anim.setStartValue(start)
        self._theme_anim.setEndValue(end)
        self._theme_anim.valueChanged.connect(self.apply_theme_color)
        self._theme_anim.finished.connect(lambda: self.apply_theme_color(end))
        self._theme_anim.start()
        self._current_theme_color = color_hex

    def apply_theme_color_hex(self, color_hex: str):
        self._current_theme_color = color_hex
        self.apply_theme_color(QColor(color_hex))

    def apply_theme_color(self, color: QColor):
        color_hex = color.name()
        dark_a = color.darker(185)
        dark_b = color.darker(150)
        rgba_strong = f"rgba({dark_a.red()}, {dark_a.green()}, {dark_a.blue()}, 110)"
        rgba_mid = f"rgba({dark_b.red()}, {dark_b.green()}, {dark_b.blue()}, 80)"
        rgba_soft = f"rgba({dark_b.red()}, {dark_b.green()}, {dark_b.blue()}, 0)"
        corner_rgba = f"rgba({dark_b.red()}, {dark_b.green()}, {dark_b.blue()}, 128)"

        self.top_toolbar.setStyleSheet(
            f"QWidget {{ background-color: {color_hex}; border-bottom: 1px solid transparent; }}"
        )
        self.bottom_toolbar.set_theme_color(color_hex)
        self.left_sidebar.update_background_style(f"rgba({color.red()}, {color.green()}, {color.blue()}, 128)")
        self.left_sidebar.update_background_style(color_hex)
        self.right_sidebar.update_background_style(color_hex)
        for strip in [
            self.strip_left_top, self.strip_left_mid, self.strip_left_bot,
            self.strip_right_top, self.strip_right_mid, self.strip_right_bot,
        ]:
            strip.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.strip_left_top.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.topbar_bg.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.bottombar_bg.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.corner_tl.setStyleSheet(f"QFrame {{ background-color: {corner_rgba}; }}")
        self.corner_tr.setStyleSheet(f"QFrame {{ background-color: {corner_rgba}; }}")
        self.corner_bl.setStyleSheet(f"QFrame {{ background-color: {corner_rgba}; }}")
        self.corner_br.setStyleSheet(f"QFrame {{ background-color: {corner_rgba}; }}")
        self.bottom_shadow.setStyleSheet(
            "QFrame { "
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {rgba_strong}, stop:1 {rgba_soft}); "
            "}"
        )
        self.right_shadow.setStyleSheet(
            "QFrame { "
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {rgba_strong}, stop:1 {rgba_soft}); "
            "}"
        )
        self.right_shadow_bot.setStyleSheet(
            "QFrame { "
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {rgba_strong}, stop:1 {rgba_soft}); "
            "}"
        )
        self.right_shadow_down.setStyleSheet(
            "QFrame { "
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {rgba_mid}, stop:1 {rgba_soft}); "
            "}"
        )
        self.corner_shadow.setStyleSheet(
            "QFrame { "
            f"background: qradialgradient(cx:0,cy:0, radius:1, fx:0, fy:0, stop:0 {rgba_strong}, stop:1 {rgba_soft}); "
            "}"
        )
        self.editor.setStyleSheet(
            f"QWidget {{ background-color: {color_hex}; }} QSplitter::handle {{ background-color: {color_hex}; }}"
        )

    def init_topbar_fade(self):
        effect = QGraphicsOpacityEffect(self.top_toolbar)
        effect.setOpacity(0.0)
        self.top_toolbar.setGraphicsEffect(effect)
        self._topbar_effect = effect
        self._topbar_anim = QPropertyAnimation(effect, b"opacity", self)
        self._topbar_anim.setDuration(500)
        self._topbar_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.top_toolbar.installEventFilter(self)

    def _init_close_corner_fade(self):
        if not hasattr(self, "close_corner_host"):
            return
        close_effect = QGraphicsOpacityEffect(self.close_corner_host)
        close_effect.setOpacity(getattr(self, "_topbar_effect", None).opacity() if hasattr(self, "_topbar_effect") else 0.0)
        self.close_corner_host.setGraphicsEffect(close_effect)
        self._close_corner_effect = close_effect
        self._close_corner_anim = QPropertyAnimation(close_effect, b"opacity", self)
        self._close_corner_anim.setDuration(500)
        self._close_corner_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.close_corner_host.installEventFilter(self)

    def fade_topbar(self, target_opacity: float):
        if self._topbar_anim.state() == QPropertyAnimation.Running:
            self._topbar_anim.stop()
        self._topbar_anim.setStartValue(self._topbar_effect.opacity())
        self._topbar_anim.setEndValue(target_opacity)
        self._topbar_anim.start()
        close_anim = getattr(self, "_close_corner_anim", None)
        close_effect = getattr(self, "_close_corner_effect", None)
        if close_anim and close_effect:
            if close_anim.state() == QPropertyAnimation.Running:
                close_anim.stop()
            close_anim.setStartValue(close_effect.opacity())
            close_anim.setEndValue(target_opacity)
            close_anim.start()

    def init_bottombar_fade(self):
        effect = QGraphicsOpacityEffect(self.bottom_toolbar)
        effect.setOpacity(0.0)
        self.bottom_toolbar.setGraphicsEffect(effect)
        self._bottombar_effect = effect
        self._bottombar_anim = QPropertyAnimation(effect, b"opacity", self)
        self._bottombar_anim.setDuration(500)
        self._bottombar_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.bottom_toolbar.installEventFilter(self)
        self.bottom_toolbar.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def fade_bottombar(self, target_opacity: float):
        if self._bottombar_anim.state() == QPropertyAnimation.Running:
            self._bottombar_anim.stop()
        self._bottombar_anim.setStartValue(self._bottombar_effect.opacity())
        self._bottombar_anim.setEndValue(target_opacity)
        self._bottombar_anim.start()

    def _schedule_bottombar_hide(self):
        QTimer.singleShot(1000, self._hide_bottombar_if_idle)

    def _hide_bottombar_if_idle(self):
        if self.bottom_toolbar.underMouse():
            return
        flyout = getattr(self.bottom_toolbar, "flyout", None)
        if flyout and flyout.underMouse():
            return
        self.fade_bottombar(0.0)
