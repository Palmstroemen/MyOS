"""Sidebar and bottom toolbar widgets for PostFix."""

import glob
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QRect, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QColorDialog,
    QGraphicsOpacityEffect,
)

try:
    from Theme.tag_chips import build_tag_chip_stylesheet
except Exception:  # pragma: no cover - runtime fallback
    def build_tag_chip_stylesheet(background: str, foreground: str) -> str:
        return f"""
            QPushButton {{
                background-color: {background};
                color: {foreground};
                border: 1px solid rgba(0, 0, 0, 60);
                border-top-left-radius: 2px;
                border-bottom-left-radius: 2px;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                text-align: right;
                padding: 4px 8px;
                margin: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid rgba(0, 0, 0, 95);
            }}
        """


class SidebarWidget(QWidget):
    """Base class for sidebars with fade-in/fade-out on hover."""

    def __init__(self, title="Sidebar", bg_color="rgba(200, 220, 240, 60)"):
        super().__init__()
        self._title_text = title
        self.bg_color = bg_color
        self.base_opacity = 1.0
        self.hover_opacity = 1.0
        self.update_background_style(bg_color)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        layout.addStretch()
        self.set_opacity(self.base_opacity)

    def set_title_text(self, text: str):
        self._title_text = str(text or "")
        if hasattr(self, "title_label"):
            self.title_label.setText(self._title_text)

    def set_opacity(self, opacity):
        self.setWindowOpacity(opacity)

    def update_background_style(self, bg_color: str):
        self.bg_color = bg_color
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                border: 1px dashed #aaa;
            }}
            QLabel {{
                color: #333333;
                font-weight: bold;
            }}
        """
        )

    def enterEvent(self, event):
        self.animate_opacity(self.base_opacity, self.hover_opacity)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animate_opacity(self.hover_opacity, self.base_opacity)
        super().leaveEvent(event)

    def animate_opacity(self, start, end):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


class ChipButton(QPushButton):
    """Button with distinct single- and double-click signals."""

    singleClicked = Signal()
    doubleClicked = Signal()

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._single_timer = QTimer(self)
        self._single_timer.setSingleShot(True)
        self._single_timer.setInterval(220)
        self._single_timer.timeout.connect(self.singleClicked.emit)
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self._single_timer.start()

    def mouseDoubleClickEvent(self, event):
        if self._single_timer.isActive():
            self._single_timer.stop()
        self.doubleClicked.emit()
        event.accept()


class TagSidebar(SidebarWidget):
    """Right sidebar for tags with interactive tag buttons."""

    tagSearchRequested = Signal(str)
    tagColorChangeRequested = Signal(str, str)
    colorDefinitionChangeRequested = Signal(str, str, str)
    colorDefinitionSearchRequested = Signal(str, str)

    def __init__(self):
        super().__init__("Tags", "rgba(220, 240, 200, 60)")
        self.tags = []
        self.color_entries = []
        self._tag_colors = {}
        self.setup_ui()
        self.retranslate_ui()

    def setup_ui(self):
        self._rebuild()

    def set_tags(self, tags):
        cleaned = []
        seen = set()
        for raw in tags or []:
            tag = str(raw).strip()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            cleaned.append(tag)
        self.tags = cleaned
        self._rebuild()

    def set_color_entries(self, entries):
        normalized = []
        for item in entries or []:
            if isinstance(item, dict):
                key = str(item.get("key", "")).strip()
                value = str(item.get("hex", "")).strip()
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                key = str(item[0]).strip()
                value = str(item[1]).strip()
            else:
                continue
            if key and value:
                normalized.append({"key": key, "hex": value})
        self.color_entries = normalized
        self._rebuild()

    def set_tag_colors(self, tag_colors: dict[str, str] | None):
        self._tag_colors = dict(tag_colors or {})
        self._rebuild()

    def _rebuild(self):
        layout = self.layout()
        layout.setContentsMargins(0, 8, 0, 8)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in self.color_entries:
            key = item["key"]
            value = item["hex"]
            chip_bg = value if QColor(value).isValid() else "#777777"
            chip_fg = self._text_color_for_bg(chip_bg)
            btn = ChipButton(f"{key}: {value}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.singleClicked.connect(lambda k=key, v=value: self.colorDefinitionSearchRequested.emit(k, v))
            btn.doubleClicked.connect(lambda k=key, v=value: self._pick_color_definition(k, v))
            btn.setToolTip(self.tr("Klick: naechster Treffer | Doppelklick: Farbe aendern"))
            btn.setStyleSheet(build_tag_chip_stylesheet(chip_bg, chip_fg))
            layout.addWidget(btn)

        for tag in self.tags:
            chip_bg = self._tag_colors.get(tag, "#ffd54f")
            chip_fg = self._text_color_for_bg(chip_bg)
            btn = ChipButton(f"#{tag}")
            btn.setStyleSheet(build_tag_chip_stylesheet(chip_bg, chip_fg))
            btn.singleClicked.connect(lambda t=tag: self.tagSearchRequested.emit(t))
            btn.doubleClicked.connect(lambda t=tag: self._pick_tag_color(t))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(self.tr("Klick: naechster Treffer | Doppelklick: Farbe aendern"))
            layout.addWidget(btn)

        layout.addStretch()

    def _text_color_for_bg(self, color_hex: str) -> str:
        color = QColor(color_hex)
        if not color.isValid():
            return "#1f1f1f"
        luminance = (0.2126 * color.redF()) + (0.7152 * color.greenF()) + (0.0722 * color.blueF())
        return "#ffffff" if luminance < 0.45 else "#1f1f1f"

    def _pick_tag_color(self, tag: str):
        initial = QColor(self._tag_colors.get(tag, "#ffd54f"))
        chosen = QColorDialog.getColor(initial, self, self.tr("Farbe fuer #%1").replace("%1", tag))
        if not chosen.isValid():
            return
        self.tagColorChangeRequested.emit(tag, chosen.name())

    def _pick_color_definition(self, key: str, old_hex: str):
        chosen = QColorDialog.getColor(QColor(old_hex), self, self.tr("Farbe fuer %1").replace("%1", key))
        if not chosen.isValid():
            return
        self.colorDefinitionChangeRequested.emit(key, old_hex, chosen.name())

    def retranslate_ui(self):
        self.set_title_text(self.tr("Tags"))
        self._rebuild()


class ACLSidebar(SidebarWidget):
    """Left sidebar for ACLs (fake implementation)."""

    def __init__(self):
        super().__init__("ACLs", "rgba(200, 220, 240, 60)")
        self.setup_ui()
        self.retranslate_ui()

    def setup_ui(self):
        layout = self.layout()
        layout.setContentsMargins(0, 8, 0, 8)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        people = ["Alfred", "Bertha", "Christian", "Doris"]
        groups = ["Buchhaltung", "Entwicklung", "Dokumentation"]
        acl_items = [(name, "#d6d6d6") for name in people] + [(name, "#b5b5b5") for name in groups]
        for item, bg in acl_items:
            btn = QPushButton(f"{item}  ▸")
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {bg};
                    color: #333333;
                    border: none;
                    border-top-left-radius: 2px;
                    border-bottom-left-radius: 2px;
                    border-top-right-radius: 12px;
                    border-bottom-right-radius: 12px;
                    text-align: right;
                    padding: 4px 8px;
                    margin: 3px;
                }}
                QPushButton:hover {{
                    background-color: {bg};
                    border: 1px solid #9a9a9a;
                }}
            """
            )
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
        layout.addStretch()

    def retranslate_ui(self):
        self.set_title_text(self.tr("ACLs"))


class BottomToolbar(QWidget):
    """Two-level bottom toolbar with hover effect."""

    printRequested = Signal(str)
    openInRequested = Signal(str)
    sendToRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)
        self.theme_color = "#ffffff"
        self.theme_border = "#cfcfcf"
        self.bg_layer = QFrame(self)
        self.bg_layer.lower()
        self.bg_layer.setStyleSheet("QFrame { background-color: #ffffff; }")
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_flyout)
        self._desktop_index = None
        self._printers = None
        self._runtime_resources_loaded = False
        self._active_flyout = None
        self._primary_buttons = []
        self._flyout_anim = None
        self._primary_button_map = {}
        self._flyout_height = 40
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.primary_toolbar = QWidget()
        self.primary_toolbar.setStyleSheet(
            "QWidget { background-color: transparent; border-top: 1px solid transparent; }"
        )
        self.primary_layout = QHBoxLayout(self.primary_toolbar)
        self.primary_layout.setSpacing(15)
        self.primary_layout.setContentsMargins(6, 3, 6, 3)
        self.primary_layout.addStretch()
        self.main_layout.addWidget(self.primary_toolbar)
        self.setup_primary_toolbar()
        self.setup_flyout()

    def _ensure_runtime_resources(self):
        if self._runtime_resources_loaded:
            return
        self._desktop_index = self._load_desktop_index()
        self._printers = self._load_printers()
        self._runtime_resources_loaded = True

    def setup_primary_toolbar(self):
        while self.primary_layout.count():
            item = self.primary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._primary_buttons = []
        self._primary_button_map = {}
        self.primary_layout.addStretch()
        actions = [
            ("↗", "send_to", self.tr("Senden an")),
            ("⇱", "open_in", self.tr("Oeffnen in")),
            ("⎙", "print", self.tr("Drucken")),
        ]
        for icon, action_key, label in actions:
            btn = QPushButton(icon)
            btn.setToolTip(label)
            btn.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(0, 0, 0, 0);
                    color: #333333;
                    border: 1px solid rgba(0, 0, 0, 60);
                    border-radius: 15px;
                    padding: 0;
                    font-size: 14px;
                    min-width: 30px;
                    min-height: 30px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 25);
                }
            """
            )
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(30, 30)
            btn.setMouseTracking(True)
            btn._flyout_label = action_key
            self.primary_layout.addWidget(btn)
            self._primary_buttons.append(btn)
            self._primary_button_map[btn] = action_key
        self.primary_layout.addStretch()

    def setup_flyout(self):
        parent = self.window()
        self.flyout = QFrame(parent)
        self.flyout.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.flyout.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.flyout.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.flyout.setAttribute(Qt.WA_TranslucentBackground, True)
        self.flyout.setMouseTracking(True)
        self.flyout.setAttribute(Qt.WA_Hover, True)
        self.flyout.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        self.flyout_layout = QHBoxLayout(self.flyout)
        self.flyout_layout.setContentsMargins(12, 8, 12, 8)
        self.flyout_layout.setSpacing(12)
        self.flyout_layout.setAlignment(Qt.AlignHCenter)
        self.flyout.hide()
        self._flyout_effect = QGraphicsOpacityEffect(self.flyout)
        self._flyout_effect.setOpacity(1.0)
        self.flyout.setGraphicsEffect(self._flyout_effect)
        self._flyout_anim = QPropertyAnimation(self._flyout_effect, b"opacity", self)
        self._flyout_anim.setDuration(250)
        self._flyout_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._flyout_anim.finished.connect(self._on_flyout_fade_finished)

    def show_flyout(self, primary_action, anchor_btn: QPushButton):
        if not hasattr(self, "flyout"):
            return
        if self._active_flyout == primary_action and self.flyout.isVisible():
            return
        self._ensure_runtime_resources()
        printer_items = [(p["label"], ["printer"], p["name"]) for p in (self._printers or [])] or [(self.tr("Drucker"), ["printer"], self.tr("Drucker"))]
        print_items = [("PDF", ["application-pdf", "pdf", "evince", "okular"], "PDF")] + printer_items
        items = {
            "send_to": [
                (self.tr("Mail"), ["mail", "thunderbird", "evolution", "kmail", "geary"]),
                ("WhatsApp", ["whatsapp"]),
                ("Signal", ["signal"]),
                ("Telegram", ["telegram"]),
                ("Chat", ["slack", "discord", "threema"]),
            ],
            "open_in": [
                ("Obsidian", ["obsidian"]),
                (self.tr("LibreOffice Writer"), ["libreoffice-writer", "writer"]),
                (self.tr("LibreOffice Impress"), ["libreoffice-impress", "impress"]),
            ],
            "print": print_items,
        }
        for i in reversed(range(self.flyout_layout.count())):
            item = self.flyout_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for item in items.get(primary_action, []):
            if primary_action == "print":
                label, names, printer_name = item
                widget = self._make_flyout_item(label, names, lambda _, value=printer_name: self.printRequested.emit(value))
            else:
                label, names = item
                if primary_action == "open_in":
                    widget = self._make_flyout_item(label, names, lambda _, value=label: self.openInRequested.emit(value))
                else:
                    widget = self._make_flyout_item(label, names, lambda _, value=label: self.sendToRequested.emit(value))
            self.flyout_layout.addWidget(widget)

        self.flyout_layout.invalidate()
        self.flyout_layout.activate()
        self.flyout.adjustSize()
        width = self.primary_toolbar.width()
        height = max(self._flyout_height, self.flyout.sizeHint().height())
        self._flyout_height = height
        bar_pos = self.primary_toolbar.mapToGlobal(QPoint(0, 0))
        x = bar_pos.x()
        y = bar_pos.y() - height - 6
        if y < 0:
            y = 0
        self.flyout.setGeometry(x, y, width, height)
        if self._flyout_anim.state() == QPropertyAnimation.Running:
            self._flyout_anim.stop()
        self._flyout_effect.setOpacity(1.0)
        self.flyout.show()
        self.flyout.raise_()
        self._active_flyout = primary_action

    def schedule_hide(self):
        QTimer.singleShot(1000, self._hide_if_not_over_area)

    def cancel_hide(self):
        if self._hide_timer.isActive():
            self._hide_timer.stop()

    def hide_flyout(self):
        if not hasattr(self, "flyout"):
            return
        if self._flyout_anim.state() == QPropertyAnimation.Running:
            self._flyout_anim.stop()
        self._flyout_anim.setStartValue(self._flyout_effect.opacity())
        self._flyout_anim.setEndValue(0.0)
        self._flyout_anim.start()
        self._active_flyout = None

    def _on_flyout_fade_finished(self):
        if hasattr(self, "flyout"):
            self.flyout.hide()

    def _hide_if_not_over_area(self):
        cursor_pos = QCursor.pos()
        toolbar_rect = QRect(self.mapToGlobal(QPoint(0, 0)), self.size())
        if toolbar_rect.contains(cursor_pos):
            QTimer.singleShot(200, self._hide_if_not_over_area)
            return
        if hasattr(self, "flyout") and self.flyout.isVisible():
            flyout_rect = QRect(self.flyout.mapToGlobal(QPoint(0, 0)), self.flyout.size())
            if flyout_rect.contains(cursor_pos):
                QTimer.singleShot(200, self._hide_if_not_over_area)
                return
        self.hide_flyout()

    def _button_from_widget(self, widget):
        while widget and widget is not self:
            if widget in self._primary_button_map:
                return widget
            widget = widget.parentWidget()
        return None

    def event(self, event):
        if event.type() in (QEvent.MouseMove, QEvent.HoverMove):
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            child = self.childAt(pos)
            if child is self.flyout or (hasattr(self, "flyout") and self.flyout.isAncestorOf(child)):
                return super().event(event)
            btn = self._button_from_widget(child)
            if btn:
                label = self._primary_button_map.get(btn)
                if label:
                    self.show_flyout(label, btn)
        elif event.type() == QEvent.Leave:
            self.schedule_hide()
        return super().event(event)

    def set_theme_color(self, color_hex: str):
        self.theme_color = color_hex
        self.theme_border = QColor(color_hex).darker(120).name()
        self.bg_layer.setStyleSheet(f"QFrame {{ background-color: {self.theme_color}; }}")
        self.primary_toolbar.setStyleSheet(
            "QWidget { background-color: transparent; border-top: 1px solid transparent; }"
        )
        self.update()

    def _load_desktop_index(self):
        index = {}
        paths = ["/usr/share/applications", str(Path.home() / ".local/share/applications")]
        for folder in paths:
            for file_path in glob.glob(str(Path(folder) / "*.desktop")):
                name = ""
                icon = ""
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            if line.startswith("Name=") and not name:
                                name = line.strip().split("=", 1)[1]
                            elif line.startswith("Icon=") and not icon:
                                icon = line.strip().split("=", 1)[1]
                            if name and icon:
                                break
                except OSError:
                    continue
                if name and icon:
                    index[name.lower()] = icon
        return index

    def _find_icon(self, names):
        for name in names:
            icon = QIcon.fromTheme(name)
            if not icon.isNull():
                return icon
            for key, value in (self._desktop_index or {}).items():
                if name in key:
                    themed = QIcon.fromTheme(value)
                    if not themed.isNull():
                        return themed
        return None

    def _load_printers(self):
        try:
            result = subprocess.run(
                ["lpstat", "-p"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
        except OSError:
            return []
        printers = []
        current = None
        for line in result.stdout.splitlines():
            parts = line.split()
            if parts and parts[0].lower() in ("printer", "drucker") and len(parts) > 1:
                if current:
                    printers.append(current)
                current = {"name": parts[1], "label": parts[1]}
            if current and line.strip().startswith(("Location:", "Ort:")):
                current["label"] = line.split(":", 1)[1].strip()
        if current:
            printers.append(current)
        return printers

    def _make_flyout_item(self, label: str, names: list, on_click):
        display_label = label.replace("_", " ")
        wrapper = QFrame()
        wrapper.setObjectName("flyoutItemCard")
        wrapper.setStyleSheet(
            """
            QFrame#flyoutItemCard {
                background-color: rgba(255, 255, 255, 212);
                border: 1px solid rgba(0, 0, 0, 30);
                border-radius: 20px;
            }
            QFrame#flyoutItemCard:hover {
                background-color: rgba(255, 255, 255, 235);
            }
            """
        )
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        btn = QPushButton()
        btn.setToolTip(display_label)
        btn.setFixedSize(44, 44)
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                color: #333333;
                border: none;
                border-radius: 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 18);
            }
            """
        )
        icon = self._find_icon(names)
        if icon:
            btn.setIcon(icon)
            btn.setIconSize(QSize(28, 28))
        else:
            btn.setText(display_label[:2].upper())

        def _handle_click():
            on_click(None)
            self.hide_flyout()

        btn.clicked.connect(_handle_click)

        text = QLabel(display_label)
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignHCenter)
        text.setStyleSheet("QLabel { font-size: 10px; color: #333333; background: transparent; }")
        text.setFixedWidth(90)

        layout.addWidget(btn, alignment=Qt.AlignHCenter)
        layout.addWidget(text, alignment=Qt.AlignHCenter)
        return wrapper

    def retranslate_ui(self):
        self.setup_primary_toolbar()
        self.hide_flyout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_layer.setGeometry(0, 0, self.width(), self.height())
