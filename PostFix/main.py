#!/usr/bin/env python3
"""
PostFix - Main Application Entry Point
Builds UI directly in Python without .ui files for full control.
"""
import sys
import argparse
import glob
import subprocess
import tempfile
from pathlib import Path

import markdown2
import yaml
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLabel,
                               QSpacerItem, QSizePolicy, QFrame, QColorDialog,
                               QPlainTextEdit, QTextBrowser, QStackedWidget,
                               QSplitter, QGraphicsOpacityEffect, QStackedLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QVariantAnimation, QEvent, QRect, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QPalette, QTextCursor, QIcon, QFont, QGuiApplication, QTextDocument, QCursor
from PySide6.QtPrintSupport import QPrinter

FRONTMATTER_BOUNDARY = "---"


class MetadataManager:
    """Handle YAML frontmatter parsing and updates for markdown text."""

    def split_frontmatter(self, text: str):
        lines = text.splitlines()
        if not lines or lines[0].strip() != FRONTMATTER_BOUNDARY:
            return {}, text
        for idx in range(1, len(lines)):
            if lines[idx].strip() == FRONTMATTER_BOUNDARY:
                yaml_text = "\n".join(lines[1:idx]).strip()
                body = "\n".join(lines[idx + 1 :]).lstrip("\n")
                data = yaml.safe_load(yaml_text) if yaml_text else {}
                return data or {}, body
        return {}, text

    def build_frontmatter(self, meta: dict, body: str) -> str:
        yaml_text = yaml.safe_dump(meta, sort_keys=False).strip()
        if yaml_text:
            return f"{FRONTMATTER_BOUNDARY}\n{yaml_text}\n{FRONTMATTER_BOUNDARY}\n{body.lstrip()}"
        return body

    def update_field(self, text: str, key: str, value) -> str:
        meta, body = self.split_frontmatter(text)
        meta[key] = value
        return self.build_frontmatter(meta, body)

    def get_field(self, text: str, key: str):
        meta, _ = self.split_frontmatter(text)
        return meta.get(key)


class SidebarWidget(QWidget):
    """Base class for sidebars with fade-in/fade-out on hover."""
    
    def __init__(self, title="Sidebar", bg_color="rgba(200, 220, 240, 60)"):
        super().__init__()
        self.bg_color = bg_color
        self.base_opacity = 1.0  # Fully opaque
        self.hover_opacity = 1.0
        
        # Set initial style
        self.update_background_style(bg_color)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Add stretch to push content to top
        layout.addStretch()
        
        # Set opacity
        self.set_opacity(self.base_opacity)
        
    def set_opacity(self, opacity):
        """Set widget opacity."""
        self.setWindowOpacity(opacity)

    def update_background_style(self, bg_color: str):
        self.bg_color = bg_color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 5px;
                border: 1px dashed #aaa;
            }}
            QLabel {{
                color: #333333;
                font-weight: bold;
            }}
        """)
        
    def enterEvent(self, event):
        """Fade in when mouse enters."""
        self.animate_opacity(self.base_opacity, self.hover_opacity)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Fade out when mouse leaves."""
        self.animate_opacity(self.hover_opacity, self.base_opacity)
        super().leaveEvent(event)
        
    def animate_opacity(self, start, end):
        """Animate opacity change."""
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)  # ms
        self.animation.setStartValue(start)
        self.animation.setEndValue(end)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


class TagSidebar(SidebarWidget):
    """Right sidebar for tags with interactive tag buttons."""
    
    def __init__(self):
        super().__init__("Tags", "rgba(220, 240, 200, 60)")
        self.tags = []
        self.setup_ui()
        
    def setup_ui(self):
        # Get the layout from parent
        layout = self.layout()
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Clear placeholder widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add tag buttons (example tags)
        self.tag_buttons = []
        example_tags = [
            ("important", "#ff6b6b"),
            ("urgent", "#ffa726"),
            ("in process", "#ffd93d"),
            ("done", "#6bcf7f"),
            ("waiting", "#4d96ff")
        ]
        
        for tag_text, color in example_tags:
            btn = QPushButton(tag_text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-top-left-radius: 2px;
                    border-bottom-left-radius: 2px;
                    border-top-right-radius: 10px;
                    border-bottom-right-radius: 10px;
                    padding: 5px 10px;
                    margin: 2px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    border: 1px solid white;
                }}
            """)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
            self.tag_buttons.append(btn)
        
        # Add Tag button (always visible)
        self.add_tag_btn = QPushButton("+ Add Tag")
        self.add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 100);
                color: white;
                border: 1px dashed white;
                border-top-left-radius: 2px;
                border-bottom-left-radius: 2px;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                padding: 5px 10px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 150);
            }
        """)
        self.add_tag_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.add_tag_btn)
        
        # Add stretch at the bottom
        layout.addStretch()


class ACLSidebar(SidebarWidget):
    """Left sidebar for ACLs (fake implementation)."""
    
    def __init__(self):
        super().__init__("ACLs", "rgba(200, 220, 240, 60)")
        self.setup_ui()
        
    def setup_ui(self):
        layout = self.layout()
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Clear placeholder widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add ACL buttons (people light gray, groups darker gray)
        people = ["Alfred", "Bertha", "Christian", "Doris"]
        groups = ["Buchhaltung", "Entwicklung", "Dokumentation"]
        acl_items = [(name, "#d6d6d6") for name in people] + [(name, "#b5b5b5") for name in groups]
        
        for item, bg in acl_items:
            btn = QPushButton(f"{item}  ▸")
            btn.setStyleSheet(f"""
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
            """)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
        
        layout.addStretch()


class BottomToolbar(QWidget):
    """Two-level bottom toolbar with hover effect."""

    printRequested = Signal(str)
    openInRequested = Signal(str)
    sendToRequested = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)  # Only primary level visible initially
        self.theme_color = "#ffffff"
        self.theme_border = "#cfcfcf"
        self.bg_layer = QFrame(self)
        self.bg_layer.lower()
        self.bg_layer.setStyleSheet("QFrame { background-color: #ffffff; }")
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide_flyout)
        self._desktop_index = self._load_desktop_index()
        self._printers = self._load_printers()
        self._active_flyout = None
        self._primary_buttons = []
        self._flyout_anim = None
        self._primary_button_map = {}
        self._flyout_height = 40
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Primary toolbar (always visible)
        self.primary_toolbar = QWidget()
        self.primary_toolbar.setStyleSheet(
            "QWidget { background-color: transparent; border-top: 1px solid transparent; }"
        )
        self.primary_layout = QHBoxLayout(self.primary_toolbar)
        self.primary_layout.setSpacing(15)
        self.primary_layout.setContentsMargins(6, 3, 6, 3)
        self.primary_layout.addStretch()
        
        # Add toolbar to main layout
        self.main_layout.addWidget(self.primary_toolbar)
        
        # Setup content
        self.setup_primary_toolbar()
        self.setup_flyout()
        
    def setup_primary_toolbar(self):
        """Setup the always-visible primary toolbar."""
        # Primary action buttons (icons)
        actions = [("↗", "Send To"), ("⇱", "Open In"), ("⎙", "Print")]
        
        for icon, label in actions:
            btn = QPushButton(icon)
            btn.setToolTip(label)
            btn.setStyleSheet("""
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
            """)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(30, 30)
            btn.setMouseTracking(True)
            btn._flyout_label = label
            
            self.primary_layout.addWidget(btn)
            self._primary_buttons.append(btn)
            self._primary_button_map[btn] = label
        
        # Add stretch
        self.primary_layout.addStretch()
        
    def setup_flyout(self):
        """Setup the hover flyout with larger icons."""
        parent = self.window()
        self.flyout = QFrame(parent)
        self.flyout.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.flyout.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.flyout.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.flyout.setMouseTracking(True)
        self.flyout.setAttribute(Qt.WA_Hover, True)
        self.flyout.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,235); border: none; }"
        )
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
        printer_items = [(p["label"], ["printer"], p["name"]) for p in self._printers] or [("Printer", ["printer"], "Printer")]
        print_items = [("PDF", ["application-pdf", "pdf", "evince", "okular"], "PDF")] + printer_items
        items = {
            "Send To": [("Mail", ["mail", "thunderbird", "evolution", "kmail", "geary"]),
                        ("WhatsApp", ["whatsapp"]),
                        ("Signal", ["signal"]),
                        ("Telegram", ["telegram"]),
                        ("Chat", ["slack", "discord", "threema"])],
            "Open In": [("Obsidian", ["obsidian"]),
                        ("LibreOffice Writer", ["libreoffice-writer", "writer"]),
                        ("LibreOffice Impress", ["libreoffice-impress", "impress"])],
            "Print": print_items,
        }
        for i in reversed(range(self.flyout_layout.count())):
            item = self.flyout_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for item in items.get(primary_action, []):
            if primary_action == "Print":
                label, names, printer_name = item
                widget = self._make_flyout_item(label, names, lambda _, value=printer_name: self.printRequested.emit(value))
            else:
                label, names = item
                if primary_action == "Open In":
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
        if self.flyout.isVisible():
            pass
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
            for key, value in self._desktop_index.items():
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
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        btn = QPushButton()
        btn.setToolTip(display_label)
        btn.setFixedSize(44, 44)
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 0);
                color: #333333;
                border: 1px solid rgba(0, 0, 0, 60);
                border-radius: 22px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 25);
            }
        """)
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
        text.setStyleSheet("QLabel { font-size: 10px; color: #333333; }")
        text.setFixedWidth(90)

        layout.addWidget(btn, alignment=Qt.AlignHCenter)
        layout.addWidget(text, alignment=Qt.AlignHCenter)
        return wrapper

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_layer.setGeometry(0, 0, self.width(), self.height())


class SmartEditor(QWidget):
    """Central editor with source, preview, and split modes."""

    MODE_PREVIEW = "Live Preview"
    MODE_SOURCE = "Edit Source"
    MODE_SPLIT = "Split View"

    def __init__(self, show_frontmatter: bool = False):
        super().__init__()
        self.metadata = MetadataManager()
        self._frontmatter = {}
        self.show_frontmatter = show_frontmatter
        self.current_bg = "#ffffff"
        self._current_border = QColor(self.current_bg).darker(120).name()
        self._bg_anim = None
        self._bg_initialized = False
        self.current_path = None
        self.setup_ui()
        self.apply_background(self.current_bg)
        self.render_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("Write your markdown here...")
        self.source_edit.setViewportMargins(12, 12, 12, 12)
        self.source_edit.setFrameStyle(QFrame.NoFrame)
        self.source_edit.textChanged.connect(self.render_preview)

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setFrameStyle(QFrame.NoFrame)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.source_edit)
        self.splitter.addWidget(self.preview)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.preview)
        self.stack.addWidget(self.source_edit)
        self.stack.addWidget(self.splitter)

        layout.addWidget(self.stack)

        self._frontmatter = {
            "title": "PostFix Note",
            "background_color": "#ffffff",
        }
        body_text = "Start writing your note here.\n"
        if self.show_frontmatter:
            initial_text = self.metadata.build_frontmatter(self._frontmatter, body_text)
            self.source_edit.setPlainText(initial_text)
        else:
            self.source_edit.setPlainText(body_text)

    def load_markdown(self, text: str):
        meta, body = self.metadata.split_frontmatter(text)
        self._frontmatter = meta
        self.source_edit.setPlainText(text if self.show_frontmatter else body)
        bg = self._frontmatter.get("background_color")
        if isinstance(bg, str) and bg.startswith("#"):
            self.apply_background(bg)
        else:
            self.render_preview()

    def set_path(self, path: Path):
        self.current_path = path

    def get_markdown(self) -> str:
        if self.show_frontmatter:
            return self.source_edit.toPlainText()
        body = self.source_edit.toPlainText()
        return self.metadata.build_frontmatter(self._frontmatter, body)

    def set_view_mode(self, mode: str):
        if mode == self.MODE_PREVIEW:
            self.stack.setCurrentWidget(self.preview)
        elif mode == self.MODE_SOURCE:
            self.stack.setCurrentWidget(self.source_edit)
        else:
            self.stack.setCurrentWidget(self.splitter)

    def render_preview(self):
        text = self.source_edit.toPlainText()
        _, body = self.metadata.split_frontmatter(text)
        html = markdown2.markdown(body, extras=["fenced-code-blocks"])
        self.preview.setHtml(html)
        self.apply_background(self.current_bg, update_frontmatter=False)

    def apply_background(self, color_hex: str, update_frontmatter: bool = True):
        if color_hex == self.current_bg and self._bg_initialized:
            return
        start = QColor(self.current_bg)
        end = QColor(color_hex)
        if self._bg_anim and self._bg_anim.state() == QVariantAnimation.Running:
            self._bg_anim.stop()
        self._bg_anim = QVariantAnimation(self)
        self._bg_anim.setDuration(1000)
        self._bg_anim.setStartValue(start)
        self._bg_anim.setEndValue(end)
        self._bg_anim.valueChanged.connect(self.apply_editor_background)
        self._bg_anim.finished.connect(lambda: self.apply_editor_background(end))
        self._bg_anim.start()
        self.current_bg = color_hex
        self._current_border = QColor(color_hex).darker(120).name()
        self._bg_initialized = True
        if hasattr(self, "on_theme_color_changed"):
            self.on_theme_color_changed(color_hex)
        if update_frontmatter:
            if self.show_frontmatter:
                updated = self.metadata.update_field(
                    self.source_edit.toPlainText(), "background_color", color_hex
                )
                self._replace_source_text(updated)
            else:
                self._frontmatter["background_color"] = color_hex
            self.render_preview()

    def apply_editor_background(self, color: QColor):
        color_hex = color.name()
        self.source_edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {color_hex}; padding: 12px; }}"
        )
        self.preview.setStyleSheet(
            f"QTextBrowser {{ background-color: {color_hex}; padding: 12px; }}"
        )

    def update_window_metadata(self, width_px: int, height_px: int, x_permille: int, y_permille: int):
        if self.show_frontmatter:
            text = self.source_edit.toPlainText()
            updated = self.metadata.update_field(text, "window_width_px", int(width_px))
            updated = self.metadata.update_field(updated, "window_height_px", int(height_px))
            updated = self.metadata.update_field(updated, "window_x_permille", int(x_permille))
            updated = self.metadata.update_field(updated, "window_y_permille", int(y_permille))
            self._replace_source_text(updated)
        else:
            self._frontmatter["window_width_px"] = int(width_px)
            self._frontmatter["window_height_px"] = int(height_px)
            self._frontmatter["window_x_permille"] = int(x_permille)
            self._frontmatter["window_y_permille"] = int(y_permille)

    def _replace_source_text(self, updated: str):
        cursor = self.source_edit.textCursor()
        pos = cursor.position()
        self.source_edit.blockSignals(True)
        self.source_edit.setPlainText(updated)
        self.source_edit.blockSignals(False)
        cursor.setPosition(min(pos, len(updated)))
        self.source_edit.setTextCursor(cursor)

    def wrap_selection(self, css_style: str):
        cursor = self.source_edit.textCursor()
        if not cursor.hasSelection():
            return
        selected = cursor.selectedText().replace("\u2029", "\n")
        wrapped = f"<span style=\"{css_style}\">{selected}</span>"
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(wrapped)
        cursor.endEditBlock()
        self.render_preview()


class PostFixWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, open_path: Path | None = None, debug: bool = False):
        super().__init__()
        self.setWindowTitle("PostFix")
        self.setGeometry(100, 100, 900, 650)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowOpacity(1.0)
        
        # Set application styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: transparent;
            }
            QPushButton {
                font-size: 12px;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background: transparent; }")
        central_widget.setMouseTracking(True)
        central_widget.setAttribute(Qt.WA_Hover, True)
        central_widget.installEventFilter(self)
        self.setCentralWidget(central_widget)
        
        # Main layout (3x3 grid)
        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create and add top toolbar
        self.create_top_toolbar()
        self.top_toolbar.setFixedHeight(40)
        self.init_topbar_fade()

        # Center area (editor + sidebars)
        self.left_sidebar = ACLSidebar()
        self.editor = SmartEditor(show_frontmatter=debug)
        self.right_sidebar = TagSidebar()
        self.editor.on_theme_color_changed = self.update_theme_color
        self._theme_anim = None
        self._current_theme_color = self.editor.current_bg
        self._meta_timer = QTimer(self)
        self._meta_timer.setSingleShot(True)
        self._meta_timer.timeout.connect(self._flush_window_metadata)

        self.acl_host = QFrame()
        self.acl_host.setFixedWidth(120)
        acl_layout = QVBoxLayout(self.acl_host)
        acl_layout.setContentsMargins(0, 0, 0, 0)
        acl_layout.addWidget(self.left_sidebar)

        # Bottom toolbar
        self.bottom_toolbar = BottomToolbar()
        self.init_bottombar_fade()
        self.bottom_toolbar.printRequested.connect(self.print_to_printer)
        self.bottom_toolbar.openInRequested.connect(self.open_in_app)
        self.bottom_toolbar.sendToRequested.connect(self.send_to_app)

        # Corner widgets (more transparent)
        self.corner_tl = self.make_corner_widget()
        self.corner_tr = self.make_corner_widget()
        self.corner_bl = self.make_corner_widget()
        self.corner_br = self.make_corner_widget()

        # Inner side strips (theme-colored)
        self.strip_left_top_host, self.strip_left_top = self.make_strip_host(align_right=True)
        self.strip_left_mid_host, self.strip_left_mid = self.make_strip_host(align_right=True)
        self.strip_left_bot_host, self.strip_left_bot = self.make_strip_host(align_right=True)
        self.strip_right_top_host, self.strip_right_top = self.make_strip_host(align_right=False)
        self.strip_right_mid_host, self.strip_right_mid = self.make_strip_host(align_right=False)
        self.strip_right_bot_host, self.strip_right_bot = self.make_strip_host(align_right=False)

        self.topbar_bg = QFrame()
        self.topbar_bg.setStyleSheet("QFrame { background-color: #ffffff; }")
        self.bottombar_bg = QFrame()
        self.bottombar_bg.setStyleSheet("QFrame { background-color: #ffffff; }")
        self.bottom_shadow = QFrame()
        self.bottom_shadow.setFixedHeight(60)
        self.bottom_shadow.setStyleSheet(
            "QFrame { "
            "background: qlineargradient(x1:0,y1:0,x2:0,y2:1, "
            "stop:0 rgba(0,0,0,80), stop:1 rgba(0,0,0,0)); "
            "}"
        )
        self.right_shadow = QFrame()
        self.right_shadow.setFixedWidth(60)
        self.right_shadow.setStyleSheet(
            "QFrame { "
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
            "stop:0 rgba(0,0,0,80), stop:1 rgba(0,0,0,0)); "
            "}"
        )
        self.corner_shadow = QFrame()
        self.corner_shadow.setFixedSize(60, 60)
        self.corner_shadow.setStyleSheet(
            "QFrame { "
            "background: qradialgradient(cx:0,cy:0, radius:1, "
            "fx:0, fy:0, stop:0 rgba(0,0,0,80), stop:1 rgba(0,0,0,0)); "
            "}"
        )
        self.right_shadow_bot = QFrame()
        self.right_shadow_bot.setFixedWidth(60)
        self.right_shadow_bot.setStyleSheet(
            "QFrame { "
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
            "stop:0 rgba(0,0,0,80), stop:1 rgba(0,0,0,0)); "
            "}"
        )
        self.right_shadow_down = QFrame()
        self.right_shadow_down.setFixedWidth(60)
        self.right_shadow_down.setStyleSheet(
            "QFrame { "
            "background: qlineargradient(x1:0,y1:0,x2:1,y2:0, "
            "stop:0 rgba(0,0,0,60), stop:1 rgba(0,0,0,0)); "
            "}"
        )

        # Debug overlay disabled for production look.
        self._resize_targets = [
            self.centralWidget(),
            self.top_toolbar,
            self.topbar_bg,
            self.bottom_toolbar,
            self.bottombar_bg,
            self.editor,
        ]
        for target in self._resize_targets:
            target.setMouseTracking(True)
            target.setAttribute(Qt.WA_Hover, True)
            target.installEventFilter(self)

        self.left_mid_host = QFrame()
        left_mid_stack = QStackedLayout(self.left_mid_host)
        left_mid_stack.setStackingMode(QStackedLayout.StackAll)
        left_mid_stack.addWidget(self.acl_host)
        left_mid_stack.addWidget(self.strip_left_mid_host)
        left_mid_stack.setAlignment(self.acl_host, Qt.AlignRight | Qt.AlignVCenter)
        left_mid_stack.setAlignment(self.strip_left_mid_host, Qt.AlignRight | Qt.AlignVCenter)

        self.right_mid_host = QFrame()
        right_mid_stack = QStackedLayout(self.right_mid_host)
        right_mid_stack.setStackingMode(QStackedLayout.StackAll)
        right_mid_stack.addWidget(self.strip_right_mid_host)
        right_mid_stack.addWidget(self.right_shadow)
        right_mid_stack.addWidget(self.right_sidebar)
        right_mid_stack.setAlignment(self.right_shadow, Qt.AlignRight | Qt.AlignVCenter)
        self.strip_right_mid_host.lower()
        self.right_shadow.lower()
        self.right_sidebar.raise_()

        self.right_bot_host = QFrame()
        right_bot_stack = QStackedLayout(self.right_bot_host)
        right_bot_stack.setStackingMode(QStackedLayout.StackAll)
        right_bot_stack.addWidget(self.strip_right_bot_host)
        right_bot_stack.addWidget(self.right_shadow_bot)
        right_bot_stack.setAlignment(self.right_shadow_bot, Qt.AlignRight | Qt.AlignVCenter)
        self.strip_right_bot_host.lower()
        self.right_shadow_bot.lower()

        self.corner_tl.setStyleSheet("QFrame { background-color: rgba(30, 30, 30, 128); }")
        self.strip_left_top.setStyleSheet("QFrame { background-color: #ffffff; }")
        self.topbar_bg.setStyleSheet("QFrame { background-color: #ffffff; }")

        # Layout: 3x3 grid (no outer columns)
        main_layout.addWidget(self.strip_left_top_host, 0, 0)
        main_layout.addWidget(self.topbar_bg, 0, 1)
        main_layout.addWidget(self.top_toolbar, 0, 1)
        main_layout.addWidget(self.strip_right_top_host, 0, 2)

        main_layout.addWidget(self.left_mid_host, 1, 0)
        main_layout.addWidget(self.editor, 1, 1)
        main_layout.addWidget(self.right_mid_host, 1, 2)

        main_layout.addWidget(self.strip_left_bot_host, 2, 0)
        main_layout.addWidget(self.bottombar_bg, 2, 1)
        main_layout.addWidget(self.bottom_toolbar, 2, 1)
        main_layout.addWidget(self.right_bot_host, 2, 2)
        main_layout.addWidget(self.bottom_shadow, 3, 1)
        main_layout.addWidget(self.right_shadow_down, 3, 2, Qt.AlignLeft | Qt.AlignVCenter)
        main_layout.addWidget(self.corner_shadow, 3, 2, Qt.AlignLeft | Qt.AlignVCenter)

        main_layout.setRowStretch(1, 1)
        main_layout.setRowStretch(3, 0)
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnMinimumWidth(0, 40)
        main_layout.setColumnMinimumWidth(2, 40)
        main_layout.setRowMinimumHeight(3, 60)
        
        # Connect signals
        self.connect_signals()
        self.update_theme_color(self.editor.current_bg)
        if open_path and open_path.exists():
            self.editor.load_markdown(open_path.read_text(encoding="utf-8"))
            self.editor.set_path(open_path)
        
    def create_top_toolbar(self):
        """Create the top toolbar with all controls."""
        self.top_toolbar = QWidget()
        self.top_toolbar.setMinimumHeight(40)
        self.top_toolbar.setMaximumHeight(40)
        self.top_toolbar.setStyleSheet(
            "QWidget { background-color: #ffffff; border-bottom: 1px solid transparent; }"
        )
        
        layout = QHBoxLayout(self.top_toolbar)
        layout.setSpacing(10)
        
        # Burger menu button
        self.btn_menu = QPushButton("☰")
        self.btn_menu.setCursor(Qt.PointingHandCursor)
        
        # Background color button
        self.btn_bg_color = QPushButton()
        self.btn_bg_color.setCursor(Qt.PointingHandCursor)

        self.btn_text_color = QPushButton("T")
        self.btn_text_color.setCursor(Qt.PointingHandCursor)

        self.btn_highlight = QPushButton()
        self.btn_highlight.setCursor(Qt.PointingHandCursor)

        self.apply_round_button_style(self.btn_menu, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_bg_color, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_text_color, "#FFF740", "#d4c600")
        self.apply_round_button_style(self.btn_highlight, "#FFF740", "#d4c600")
        self.btn_text_color.setStyleSheet(
            self.btn_text_color.styleSheet()
            + "QPushButton { font-weight: bold; font-size: 14px; }"
        )
        self.btn_menu.setStyleSheet(
            self.btn_menu.styleSheet()
            + "QPushButton { font-size: 14px; }"
        )
        icon_path = Path(__file__).with_name("icons").joinpath("highlighter.svg")
        if icon_path.exists():
            self.btn_highlight.setIcon(QIcon(str(icon_path)))
            self.btn_highlight.setIconSize(self.btn_highlight.size())
        
        # Spacer
        layout.addWidget(self.btn_menu)
        layout.addWidget(self.btn_bg_color)
        layout.addWidget(self.btn_text_color)
        layout.addWidget(self.btn_highlight)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Fixed, QSizePolicy.Minimum))
        
        # View mode button
        self.btn_view_mode = QPushButton("Live Preview")
        self.btn_view_mode.setCursor(Qt.PointingHandCursor)
        self.apply_oval_button_style(self.btn_view_mode, "#FFF740", "#d4c600")
        
        # Center view mode button
        layout.addStretch()
        layout.addWidget(self.btn_view_mode)
        layout.addStretch()
        
        # Window control buttons
        self.btn_minimize = QPushButton("−")
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.apply_round_button_style(self.btn_minimize, "#FFF740", "#d4c600")
        self.btn_minimize.setStyleSheet(
            self.btn_minimize.styleSheet()
            + "QPushButton { font-size: 14px; }"
        )
        
        self.btn_maximize = QPushButton("□")
        self.btn_maximize.setCursor(Qt.PointingHandCursor)
        self.apply_round_button_style(self.btn_maximize, "#FFF740", "#d4c600")
        self.btn_maximize.setStyleSheet(
            self.btn_maximize.styleSheet()
            + "QPushButton { font-size: 14px; }"
        )
        
        self.btn_close = QPushButton("✕")
        self.apply_round_button_style(self.btn_close, "#ff5b5b", "#d64a4a")
        self.btn_close.setStyleSheet(
            self.btn_close.styleSheet()
            + "QPushButton { font-size: 14px; }"
        )
        self.btn_close.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(self.btn_minimize)
        layout.addWidget(self.btn_maximize)
        layout.addWidget(self.btn_close)
        
    def connect_signals(self):
        """Connect all button signals."""
        # Window controls
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_maximize.clicked.connect(self.toggle_maximize)
        self.btn_close.clicked.connect(self.close)
        
        # Background color picker
        self.btn_bg_color.clicked.connect(self.pick_background_color)

        # Text formatting
        self.btn_text_color.clicked.connect(self.pick_text_color)
        self.btn_highlight.clicked.connect(self.pick_highlight_color)
        
        # View mode toggle
        self.btn_view_mode.clicked.connect(self.toggle_view_mode)
        
        # Menu button (placeholder)
        self.btn_menu.clicked.connect(self.show_menu)
        
    def toggle_maximize(self):
        """Toggle between normal and maximized window state."""
        if self.isMaximized():
            self.showNormal()
            self.btn_maximize.setText("□")
        else:
            self.showMaximized()
            self.btn_maximize.setText("❐")
            
    def pick_background_color(self):
        """Open color dialog to pick background color."""
        self.open_palette(self.editor.current_bg, self.on_background_color_selected, self.btn_bg_color)

    def on_background_color_selected(self, color: QColor):
        self.apply_round_button_style(
            self.btn_bg_color, color.name(), color.darker(120).name()
        )
        self.editor.apply_background(color.name())

    def pick_text_color(self):
        self.open_palette(QColor("#1f2433").name(), self.on_text_color_selected, self.btn_text_color)

    def on_text_color_selected(self, color: QColor):
        self.editor.wrap_selection(f"color: {color.name()};")

    def pick_highlight_color(self):
        self.open_palette(QColor("#fff59d").name(), self.on_highlight_color_selected, self.btn_highlight)

    def on_highlight_color_selected(self, color: QColor):
        self.editor.wrap_selection(f"background-color: {color.name()};")
            
    def toggle_view_mode(self):
        """Toggle between view modes."""
        current_text = self.btn_view_mode.text()
        modes = [SmartEditor.MODE_PREVIEW, SmartEditor.MODE_SOURCE, SmartEditor.MODE_SPLIT]
        
        try:
            current_index = modes.index(current_text)
            next_index = (current_index + 1) % len(modes)
        except ValueError:
            next_index = 0
            
        next_mode = modes[next_index]
        self.btn_view_mode.setText(next_mode)
        self.editor.set_view_mode(next_mode)
        
    def show_menu(self):
        """Show menu (placeholder)."""
        print("Menu clicked - will show settings/options")
        # TODO: Implement menu functionality

    def apply_round_button_style(self, button: QPushButton, bg_color: str, border_color: str):
        button.setFixedSize(30, 30)
        button.setStyleSheet(
            f"""
            QPushButton {{
                border-radius: 15px;
                background-color: {bg_color};
                border: 1px solid {border_color};
            }}
            QPushButton:hover {{
                background-color: {border_color};
            }}
            """
        )

    def apply_oval_button_style(self, button: QPushButton, bg_color: str, border_color: str):
        button.setFixedHeight(30)
        button.setStyleSheet(
            f"""
            QPushButton {{
                padding: 0 10px;
                border-radius: 14px;
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid rgba(0, 0, 0, 60);
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 25);
            }}
            """
        )

    def open_palette(self, initial_hex: str, on_color, anchor: QWidget):
        colors = [
            "#ffffff", "#fff8b0", "#ffe082", "#ffd54f", "#ffb74d", "#ff8a65",
            "#e6f5a7", "#a5d6a7", "#80cbc4", "#90caf9", "#ce93d8", "#f48fb1",
        ]
        popup = QFrame(self)
        popup.setWindowFlags(Qt.Popup)
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

    def apply_theme_color(self, color: QColor):
        color_hex = color.name()
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
        self.strip_left_top.setStyleSheet(
            f"QFrame {{ background-color: {color_hex}; }}"
        )
        self.topbar_bg.setStyleSheet(
            f"QFrame {{ background-color: {color_hex}; }}"
        )
        self.topbar_bg.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.bottombar_bg.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
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

    def eventFilter(self, obj, event):
        if obj is getattr(self, "top_toolbar", None):
            if event.type() == QEvent.Enter:
                self.fade_topbar(1.0)
            elif event.type() == QEvent.Leave:
                self.fade_topbar(0.0)
        if obj is getattr(self, "bottom_toolbar", None):
            if event.type() == QEvent.Enter:
                self.fade_bottombar(1.0)
            elif event.type() == QEvent.Leave:
                self._schedule_bottombar_hide()
        if obj in getattr(self, "_resize_targets", []):
            if event.type() in (QEvent.MouseMove, QEvent.HoverMove, QEvent.HoverEnter):
                pos = obj.mapTo(self.centralWidget(), event.position().toPoint())
                edges = self._paper_edges_at(pos)
                self._update_paper_cursor(edges)
                self._update_paper_debug(self._paper_rect())
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                pos = obj.mapTo(self.centralWidget(), event.position().toPoint())
                edges = self._paper_edges_at(pos)
                handle = self.windowHandle()
                if handle and edges:
                    handle.startSystemResize(edges)
                    return True
        return super().eventFilter(obj, event)

    def fade_topbar(self, target_opacity: float):
        if self._topbar_anim.state() == QPropertyAnimation.Running:
            self._topbar_anim.stop()
        self._topbar_anim.setStartValue(self._topbar_effect.opacity())
        self._topbar_anim.setEndValue(target_opacity)
        self._topbar_anim.start()

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._meta_timer.start(200)
        self._update_paper_debug(self._paper_rect())

    def moveEvent(self, event):
        super().moveEvent(event)
        self._meta_timer.start(200)

    def _paper_rect(self) -> QRect:
        top_left = self.topbar_bg.mapTo(self.centralWidget(), QPoint(0, 0))
        bottom_right = self.bottombar_bg.mapTo(
            self.centralWidget(), QPoint(self.bottombar_bg.width(), self.bottombar_bg.height())
        )
        rect = QRect(top_left, bottom_right)
        rect.adjust(-40, 0, 40, 0)
        return rect

    def _paper_edges_at(self, pos: QPoint) -> Qt.Edges:
        rect = self._paper_rect()
        edges = Qt.Edges()
        if not rect.contains(pos):
            return edges
        if abs(pos.x() - rect.left()) <= 8:
            edges |= Qt.LeftEdge
        if abs(pos.x() - rect.right()) <= 8:
            edges |= Qt.RightEdge
        if abs(pos.y() - rect.top()) <= 8:
            edges |= Qt.TopEdge
        if abs(pos.y() - rect.bottom()) <= 8:
            edges |= Qt.BottomEdge
        return edges

    def _update_paper_cursor(self, edges: Qt.Edges):
        if (edges & Qt.LeftEdge) and (edges & Qt.TopEdge):
            self.centralWidget().setCursor(Qt.SizeFDiagCursor)
        elif (edges & Qt.RightEdge) and (edges & Qt.BottomEdge):
            self.centralWidget().setCursor(Qt.SizeFDiagCursor)
        elif (edges & Qt.RightEdge) and (edges & Qt.TopEdge):
            self.centralWidget().setCursor(Qt.SizeBDiagCursor)
        elif (edges & Qt.LeftEdge) and (edges & Qt.BottomEdge):
            self.centralWidget().setCursor(Qt.SizeBDiagCursor)
        elif (edges & Qt.LeftEdge) or (edges & Qt.RightEdge):
            self.centralWidget().setCursor(Qt.SizeHorCursor)
        elif (edges & Qt.TopEdge) or (edges & Qt.BottomEdge):
            self.centralWidget().setCursor(Qt.SizeVerCursor)
        else:
            self.centralWidget().unsetCursor()

    def _flush_window_metadata(self):
        geom = self.frameGeometry()
        screen = QGuiApplication.screenAt(geom.center()) or QGuiApplication.primaryScreen()
        if not screen:
            return
        available = screen.availableGeometry()
        x_permille = int(((geom.x() - available.x()) / max(1, available.width())) * 1000)
        y_permille = int(((geom.y() - available.y()) / max(1, available.height())) * 1000)
        self.editor.update_window_metadata(geom.width(), geom.height(), x_permille, y_permille)

    def print_to_printer(self, printer_name: str):
        md_text = self.editor.get_markdown()
        html = markdown2.markdown(md_text, extras=["fenced-code-blocks"])
        doc = QTextDocument()
        doc.setHtml(html)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.close()
        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(tmp.name)
        doc.print_(printer)
        try:
            if printer_name == "PDF":
                subprocess.Popen(["xdg-open", tmp.name])
                return
            subprocess.run(["lp", "-d", printer_name, tmp.name], check=False)
        finally:
            if printer_name != "PDF":
                try:
                    Path(tmp.name).unlink()
                except OSError:
                    pass

    def open_in_app(self, app_label: str):
        if app_label.lower().startswith("obsidian") and self.editor.current_path:
            uri = f"obsidian://open?path={self.editor.current_path}"
            subprocess.Popen(["xdg-open", uri])
            return
        if self.editor.current_path:
            subprocess.Popen(["xdg-open", str(self.editor.current_path)])

    def send_to_app(self, app_label: str):
        if self.editor.current_path:
            subprocess.Popen(["xdg-open", str(self.editor.current_path)])

    def _init_paper_debug(self):
        return

    def _update_paper_debug(self, rect: QRect):
        return


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


def main():
    """Application entry point."""
    parser = argparse.ArgumentParser(description="PostFix Markdown editor")
    parser.add_argument("path", nargs="?", help="Markdown file to open")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show YAML frontmatter in the editor",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("PostFix")
    app.setOrganizationName("PostFixDev")
    icon_path = Path(__file__).with_name("icons").joinpath("postit.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    open_path = None
    if args.path:
        candidate = Path(args.path).expanduser()
        if candidate.suffix.lower() == ".md":
            open_path = candidate
    window = PostFixWindow(open_path=open_path, debug=args.debug)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
