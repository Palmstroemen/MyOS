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
import shutil
import shlex
import urllib.parse
import re
import hashlib
import difflib
from pathlib import Path

import markdown2
import yaml
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLabel,
                               QSpacerItem, QSizePolicy, QFrame, QColorDialog,
                               QPlainTextEdit, QTextBrowser, QStackedWidget,
                               QSplitter, QGraphicsOpacityEffect, QStackedLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QVariantAnimation, QEvent, QRect, QTimer, Signal, QSize
from PySide6.QtGui import QColor, QPalette, QTextCursor, QIcon, QFont, QGuiApplication, QTextDocument, QCursor, QWindow
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
        self._tag_colors = {}
        self.setup_ui()
        
    def setup_ui(self):
        self._rebuild()

    def set_tags(self, tags):
        cleaned = sorted({str(t).strip() for t in (tags or []) if str(t).strip()})
        self.tags = cleaned
        self._rebuild()

    def _rebuild(self):
        layout = self.layout()
        layout.setContentsMargins(0, 8, 0, 8)
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for tag in self.tags:
            color = self._color_for_tag(tag)
            text_color = self._text_color_for_bg(color)
            btn = QPushButton(f"#{tag}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _=False, t=tag: self._pick_tag_color(t))
            btn.setToolTip("Click to change tag color")
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    color: {text_color};
                    border: none;
                    border-top-left-radius: 2px;
                    border-bottom-left-radius: 2px;
                    border-top-right-radius: 10px;
                    border-bottom-right-radius: 10px;
                    padding: 5px 10px;
                    margin: 2px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    border: 1px solid white;
                }}
                """
            )
            layout.addWidget(btn)
        layout.addStretch()

    def _color_for_tag(self, tag: str) -> str:
        color_from_tag = self._hex_color_from_tag(tag)
        if color_from_tag:
            self._tag_colors[tag] = color_from_tag
            return color_from_tag
        if tag in self._tag_colors:
            return self._tag_colors[tag]
        palette = ["#ff6b6b", "#ffa726", "#ffd93d", "#6bcf7f", "#4d96ff", "#9c6bff", "#26c6da"]
        idx = int(hashlib.md5(tag.encode("utf-8")).hexdigest(), 16) % len(palette)
        self._tag_colors[tag] = palette[idx]
        return palette[idx]

    def _hex_color_from_tag(self, tag: str):
        value = (tag or "").strip()
        if len(value) == 3 and all(ch in "0123456789abcdefABCDEF" for ch in value):
            return f"#{value[0]}{value[0]}{value[1]}{value[1]}{value[2]}{value[2]}".upper()
        if len(value) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in value):
            return f"#{value}".upper()
        return None

    def _text_color_for_bg(self, color_hex: str) -> str:
        color = QColor(color_hex)
        if not color.isValid():
            return "#ffffff"
        # Perceived luminance for contrast decision
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        return "#1f2433" if luminance > 165 else "#ffffff"

    def _pick_tag_color(self, tag: str):
        chosen = QColorDialog.getColor(QColor(self._color_for_tag(tag)), self, f"Color for #{tag}")
        if not chosen.isValid():
            return
        self._tag_colors[tag] = chosen.name()
        self._rebuild()


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
        self.flyout.setAttribute(Qt.WA_TranslucentBackground, True)
        self.flyout.setMouseTracking(True)
        self.flyout.setAttribute(Qt.WA_Hover, True)
        self.flyout.setStyleSheet(
            "QFrame { background-color: transparent; border: none; }"
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
        btn.setStyleSheet("""
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
        text.setStyleSheet("QLabel { font-size: 10px; color: #333333; background: transparent; }")
        text.setFixedWidth(90)

        layout.addWidget(btn, alignment=Qt.AlignHCenter)
        layout.addWidget(text, alignment=Qt.AlignHCenter)
        return wrapper

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_layer.setGeometry(0, 0, self.width(), self.height())


class SmartEditor(QWidget):
    """Central editor with source, preview, and split modes."""
    tagsChanged = Signal(list)

    MODE_FOCUS = "Focus Mode"
    MODE_PREVIEW = MODE_FOCUS
    MODE_SOURCE = MODE_FOCUS
    MODE_SPLIT = MODE_FOCUS

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
        self._focus_spans = []
        self._active_focus_idx = -1
        self._syncing_focus = False
        self._editing_focus = False
        self._index_debug_visible = False
        self._overlay_top_hint = None
        self.setup_ui()
        self.apply_background(self.current_bg, update_frontmatter=False, animate=False)
        self.render_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.source_edit = QPlainTextEdit()
        self.source_edit.setPlaceholderText("Write your markdown here...")
        self.source_edit.setViewportMargins(12, 12, 12, 12)
        self.source_edit.setFrameStyle(QFrame.NoFrame)
        self.source_edit.textChanged.connect(self._on_source_changed)
        self.source_edit.hide()

        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(True)
        self.preview.setFrameStyle(QFrame.NoFrame)
        self.preview.viewport().installEventFilter(self)
        self.preview.verticalScrollBar().valueChanged.connect(self._sync_index_scroll)
        self.preview.verticalScrollBar().valueChanged.connect(self._on_preview_scrolled)

        self.index_gutter = QPlainTextEdit()
        self.index_gutter.setReadOnly(True)
        self.index_gutter.setFrameStyle(QFrame.NoFrame)
        self.index_gutter.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.index_gutter.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.index_gutter.setFixedWidth(54)
        self.index_gutter.viewport().installEventFilter(self)
        self.index_gutter.setVisible(self._index_debug_visible)

        preview_row = QWidget()
        preview_layout = QHBoxLayout(preview_row)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(6)
        preview_layout.addWidget(self.index_gutter)
        preview_layout.addWidget(self.preview, 1)

        self.focus_edit = QPlainTextEdit()
        self.focus_edit.setPlaceholderText("")
        self.focus_edit.setMaximumHeight(260)
        self.focus_edit.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.focus_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.focus_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.focus_edit.setViewportMargins(0, 0, 0, 0)
        self.focus_edit.textChanged.connect(self._on_focus_text_changed)
        self.focus_edit.installEventFilter(self)
        self.focus_edit.setParent(self.preview.viewport())
        self.focus_edit.hide()

        layout.addWidget(preview_row)

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
        self._rebuild_focus_spans()

    def load_markdown(self, text: str):
        meta, body = self.metadata.split_frontmatter(text)
        self._frontmatter = meta
        self.source_edit.setPlainText(text if self.show_frontmatter else body)
        self._rebuild_focus_spans()
        bg = self._frontmatter.get("background_color")
        if isinstance(bg, str) and bg.startswith("#"):
            self.apply_background(bg, update_frontmatter=False, animate=False)
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
        self.source_edit.hide()
        self.preview.show()
        if self._active_focus_idx >= 0:
            self.focus_edit.show()
        else:
            self.focus_edit.hide()

    def render_preview(self, sync_focus: bool = True):
        text = self.source_edit.toPlainText()
        _, body = self.metadata.split_frontmatter(text)
        scroll_value = self.preview.verticalScrollBar().value()
        html = markdown2.markdown(body, extras=["fenced-code-blocks"])
        self.preview.setHtml(html)
        self.preview.verticalScrollBar().setValue(scroll_value)
        self._refresh_index_gutter()
        self._rebuild_focus_spans()
        tags = self.extract_tags(body)
        self.tagsChanged.emit(tags)
        if sync_focus and self._active_focus_idx >= 0:
            self._apply_focus_text_from_source()
        self.apply_background(self.current_bg, update_frontmatter=False)

    def _on_source_changed(self):
        if self._syncing_focus:
            return
        self.render_preview(sync_focus=not self._editing_focus)

    def extract_tags(self, body: str):
        found = re.findall(r"(?<!\w)#([a-zA-Z0-9_/\-äöüÄÖÜß]+)", body or "")
        return sorted(set(found), key=lambda t: t.lower())

    def _rebuild_focus_spans(self):
        body = self._source_body()
        lines = body.splitlines()
        spans = [(idx, idx + 1) for idx in range(len(lines))]
        if not spans:
            spans = [(0, max(1, len(lines)))]
        self._focus_spans = spans
        if self._active_focus_idx >= len(spans):
            self._active_focus_idx = len(spans) - 1

    def _source_body(self) -> str:
        text = self.source_edit.toPlainText()
        if self.show_frontmatter:
            _, body = self.metadata.split_frontmatter(text)
            return body
        return text

    def _source_lines(self):
        return self._source_body().splitlines()

    def _refresh_index_gutter(self):
        lines = self._source_lines()
        if not lines:
            self.index_gutter.setPlainText("0001")
            return
        markers = []
        for idx in range(len(lines)):
            markers.append(f"{idx + 1:04d} ·")
        self.index_gutter.blockSignals(True)
        self.index_gutter.setPlainText("\n".join(markers))
        self.index_gutter.blockSignals(False)
        self._sync_index_scroll()

    def _sync_index_scroll(self):
        if not self.index_gutter.isVisible():
            return
        pbar = self.preview.verticalScrollBar()
        gbar = self.index_gutter.verticalScrollBar()
        if pbar.maximum() <= 0 or gbar.maximum() <= 0:
            gbar.setValue(0)
            return
        ratio = pbar.value() / max(1, pbar.maximum())
        gbar.setValue(int(ratio * gbar.maximum()))

    def _on_preview_scrolled(self):
        if self.focus_edit.isVisible() and self._active_focus_idx >= 0:
            self._position_focus_overlay()

    def _normalize_for_match(self, text: str) -> str:
        cleaned = (text or "").strip().lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^a-z0-9äöüß _/\-:.]", "", cleaned)
        return cleaned

    def _set_source_body(self, body: str):
        if self.show_frontmatter:
            updated = self.metadata.build_frontmatter(self._frontmatter, body)
            self._replace_source_text(updated)
            return
        self._replace_source_text(body)

    def _apply_focus_text_from_source(self, preserve_cursor: bool = False):
        if self._active_focus_idx < 0 or self._active_focus_idx >= len(self._focus_spans):
            return
        body_lines = self._source_body().splitlines()
        start, end = self._focus_spans[self._active_focus_idx]
        segment = "\n".join(body_lines[start:end]) if start < len(body_lines) else ""
        cursor_pos = self.focus_edit.textCursor().position()
        self._syncing_focus = True
        self.focus_edit.blockSignals(True)
        self.focus_edit.setPlainText(segment)
        self.focus_edit.blockSignals(False)
        if preserve_cursor:
            cursor = self.focus_edit.textCursor()
            cursor.setPosition(min(cursor_pos, len(segment)))
            self.focus_edit.setTextCursor(cursor)
        self._syncing_focus = False
        self._position_focus_overlay()

    def _position_focus_overlay(self):
        viewport = self.preview.viewport()
        if viewport is None:
            return
        count = max(1, len(self._focus_spans))
        idx = max(0, min(self._active_focus_idx, count - 1))

        doc = self.preview.document()
        layout = doc.documentLayout() if doc else None
        doc_height = layout.documentSize().height() if layout else 0.0
        scroll = float(self.preview.verticalScrollBar().value())

        if doc_height > 1.0 and count > 0:
            # Anchor editor to the NEXT index (below selected line/segment).
            next_idx = min(idx + 1, count - 1)
            y_top = ((next_idx / float(count)) * doc_height) - scroll
            y_bottom = (((next_idx + 1) / float(count)) * doc_height) - scroll
            top = int(round(y_top))
            bottom = int(round(y_bottom))
        else:
            line_h = max(18, self.preview.fontMetrics().lineSpacing() + 4)
            top = min(idx + 1, count - 1) * line_h
            bottom = top + line_h

        if self._overlay_top_hint is not None:
            top = int(self._overlay_top_hint)
        top = max(0, min(top, viewport.height() - 1))

        # True auto-height based on current text and current overlay width.
        content_h = self._estimate_focus_height(self.focus_edit.toPlainText(), max(120, viewport.width()))
        min_h = max(20, self.preview.fontMetrics().lineSpacing() + 4)
        height = max(min_h, content_h + 2)
        height = max(height, bottom - top)
        if top + height > viewport.height():
            top = max(0, viewport.height() - height)

        self.focus_edit.setGeometry(0, top, max(120, viewport.width()), height)
        self.focus_edit.setVisible(True)
        self.focus_edit.raise_()

    def _hide_focus_overlay(self):
        self.focus_edit.hide()
        self._overlay_top_hint = None
        self.preview.setFocus()

    def _estimate_focus_height(self, text: str, width: int) -> int:
        fm = self.focus_edit.fontMetrics()
        usable_w = max(40, width - 2)
        lines = text.splitlines()
        if not lines:
            lines = [""]
        total = 0
        for line in lines:
            probe = line if line else " "
            rect = fm.boundingRect(QRect(0, 0, usable_w, 100000), Qt.TextWordWrap | Qt.TextExpandTabs, probe)
            total += max(fm.lineSpacing(), rect.height())
        return total + 4

    def _on_focus_text_changed(self):
        if self._syncing_focus:
            return
        if self._active_focus_idx < 0 or self._active_focus_idx >= len(self._focus_spans):
            return
        body_lines = self._source_body().splitlines()
        start, end = self._focus_spans[self._active_focus_idx]
        replacement = self.focus_edit.toPlainText().splitlines()
        new_lines = body_lines[:start] + replacement + body_lines[end:]
        self._syncing_focus = True
        self._editing_focus = True
        self._set_source_body("\n".join(new_lines) + ("\n" if self._source_body().endswith("\n") else ""))
        self._editing_focus = False
        self._syncing_focus = False
        self.render_preview(sync_focus=False)
        self._position_focus_overlay()

    def _move_focus_line(self, delta: int):
        if not self._focus_spans:
            return
        col = self.focus_edit.textCursor().positionInBlock()
        step = max(18, self.preview.fontMetrics().lineSpacing() + 2)
        if self._overlay_top_hint is not None:
            self._overlay_top_hint += delta * step
        if self._active_focus_idx < 0:
            self._active_focus_idx = 0
        else:
            self._active_focus_idx = max(0, min(self._active_focus_idx + delta, len(self._focus_spans) - 1))
        self._apply_focus_text_from_source()
        cursor = self.focus_edit.textCursor()
        cursor.setPosition(min(col, len(self.focus_edit.document().firstBlock().text())))
        self.focus_edit.setTextCursor(cursor)
        self.focus_edit.setFocus()

    def eventFilter(self, watched, event):
        focus_widget = getattr(self, "focus_edit", None)
        preview_widget = getattr(self, "preview", None)
        index_widget = getattr(self, "index_gutter", None)

        if focus_widget is None or preview_widget is None or index_widget is None:
            return super().eventFilter(watched, event)

        if watched is preview_widget.viewport() and event.type() == QEvent.Resize:
            if focus_widget.isVisible() and self._active_focus_idx >= 0:
                self._position_focus_overlay()
            return False

        if watched is focus_widget and event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Up:
                self._move_focus_line(-1)
                return True
            if key == Qt.Key_Down:
                self._move_focus_line(1)
                return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                self._hide_focus_overlay()
                return True
        if watched is preview_widget.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if focus_widget.isVisible() and not focus_widget.geometry().contains(pos):
                self._hide_focus_overlay()
            return False
        if watched is preview_widget.viewport() and event.type() == QEvent.MouseButtonDblClick:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if self._focus_spans:
                idx = self._line_index_from_preview_pos(pos)
                self._active_focus_idx = idx
                click_cursor = preview_widget.cursorForPosition(pos)
                click_rect = preview_widget.cursorRect(click_cursor)
                self._overlay_top_hint = click_rect.bottom() + 1
                self._apply_focus_text_from_source()
                focus_widget.setFocus()
            return False
        if watched is index_widget.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            cursor = index_widget.cursorForPosition(pos)
            idx = max(0, min(cursor.blockNumber(), len(self._focus_spans) - 1))
            self._active_focus_idx = idx
            self._overlay_top_hint = pos.y() + 1
            self._apply_focus_text_from_source()
            focus_widget.setFocus()
            return True
        return super().eventFilter(watched, event)

    def _line_index_from_preview_pos(self, pos: QPoint) -> int:
        count = len(self._focus_spans)
        if count <= 0:
            return 0

        scroll = self.preview.verticalScrollBar().value()
        abs_y = float(scroll + pos.y())
        doc = self.preview.document()
        layout = doc.documentLayout() if doc else None
        height = layout.documentSize().height() if layout else 0.0

        if height > 1.0:
            ratio = max(0.0, min(1.0, abs_y / height))
            idx = int(round(ratio * (count - 1)))
            idx = max(0, min(idx, count - 1))
            return self._refine_index_with_preview_text(pos, idx)

        cursor = self.preview.cursorForPosition(pos)
        idx = max(0, min(cursor.blockNumber(), count - 1))
        return self._refine_index_with_preview_text(pos, idx)

    def _refine_index_with_preview_text(self, pos: QPoint, estimated_idx: int) -> int:
        cursor = self.preview.cursorForPosition(pos)
        cursor.select(QTextCursor.LineUnderCursor)
        clicked = self._normalize_for_match(cursor.selectedText())
        if not clicked:
            return estimated_idx

        lines = self._source_lines()
        if not lines:
            return estimated_idx

        window = 220
        start = max(0, estimated_idx - window)
        end = min(len(lines), estimated_idx + window + 1)
        best_idx = estimated_idx
        best_rank = -999.0
        for i in range(start, end):
            candidate = self._normalize_for_match(lines[i])
            if not candidate:
                continue
            if clicked in candidate or candidate in clicked:
                score = 1.0
            else:
                score = difflib.SequenceMatcher(None, clicked, candidate).ratio()
            # Prefer close-by lines when text is similarly plausible.
            distance = abs(i - estimated_idx)
            rank = score - min(0.25, distance * 0.0025)
            if rank > best_rank:
                best_rank = rank
                best_idx = i
        if best_rank >= 0.50:
            return best_idx
        return estimated_idx

    def apply_background(self, color_hex: str, update_frontmatter: bool = True, animate: bool = True):
        if color_hex == self.current_bg and self._bg_initialized:
            return
        start = QColor(self.current_bg)
        end = QColor(color_hex)
        if self._bg_anim and self._bg_anim.state() == QVariantAnimation.Running:
            self._bg_anim.stop()
        if animate:
            self._bg_anim = QVariantAnimation(self)
            self._bg_anim.setDuration(700)
            self._bg_anim.setStartValue(start)
            self._bg_anim.setEndValue(end)
            self._bg_anim.valueChanged.connect(self.apply_editor_background)
            self._bg_anim.finished.connect(lambda: self.apply_editor_background(end))
            self._bg_anim.start()
        else:
            self.apply_editor_background(end)
        self.current_bg = color_hex
        self._current_border = QColor(color_hex).darker(120).name()
        self._bg_initialized = True
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
        self.focus_edit.setFont(self.preview.font())

        h, s, v, _ = color.getHsv()
        if h < 0:
            h = 0
        if s < 0:
            s = 0
        if s < 12 and v > 235:
            overlay = QColor("#f3d9ea")
        else:
            overlay = QColor(
                int((color.red() + (255 * 3)) / 4),
                int((color.green() + (255 * 3)) / 4),
                int((color.blue() + (255 * 3)) / 4),
            )
        overlay_bg = f"rgba({overlay.red()}, {overlay.green()}, {overlay.blue()}, 228)"
        overlay_border = overlay_bg

        self.source_edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {color_hex}; padding: 12px; }}"
        )
        self.preview.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {color_hex};
                padding: 12px;
                border: none;
            }}
            QScrollBar:vertical {{
                background: rgba(0, 0, 0, 12);
                width: 11px;
                margin: 2px 2px 2px 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(40, 40, 40, 110);
                min-height: 22px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(40, 40, 40, 145);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: rgba(255, 255, 255, 120);
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{
                width: 0px;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent;
            }}
            """
        )
        self.focus_edit.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: {overlay_bg};
                color: #1f2433;
                border: 1px solid {overlay_border};
                border-radius: 2px;
                padding-top: 0px;
                padding-bottom: 0px;
                padding-left: 0px;
                padding-right: 0px;
                selection-background-color: #b7c7ea;
                selection-color: #111111;
            }}
            """
        )
        if hasattr(self, "on_theme_color_changed"):
            self.on_theme_color_changed(color_hex)

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


class ObsidianEmbed(QWidget):
    """Embed an external Obsidian window inside the editor area."""

    def __init__(
        self,
        open_path: Path | None = None,
        obsidian_path: str | None = None,
        obsidian_command: str | None = None,
        obsidian_view: str | None = None,
        zen_hotkey: str | None = None,
        zen_delay_ms: int = 2500,
        hotkeys: list[str] | None = None,
        hotkey_gap_ms: int = 300,
        close_hotkey: str | None = "ctrl+shift+w",
        obsidian_vault: str | None = None,
        obsidian_file: str | None = None,
        open_delay_ms: int = 1500,
        no_open: bool = False,
        debug_window_search: bool = False,
        open_mode: str | None = None,
        window_title: str | None = None,
        close_other_windows: bool = False,
        obsidian_vault_path: str | None = None,
    ):
        super().__init__()
        self.current_bg = "#ffffff"
        self.current_path = open_path
        self._obsidian_cmd = self._resolve_obsidian_command(obsidian_path)
        self._obsidian_command = obsidian_command
        self._obsidian_view = obsidian_view
        self._zen_hotkey = zen_hotkey
        self._zen_delay_ms = zen_delay_ms
        self._hotkeys = hotkeys or []
        self._hotkey_gap_ms = hotkey_gap_ms
        self._close_hotkey = close_hotkey
        self._obsidian_vault = obsidian_vault
        self._obsidian_file = obsidian_file
        self._obsidian_vault_path = obsidian_vault_path
        self._open_delay_ms = open_delay_ms
        self._no_open = no_open
        self._debug_window_search = debug_window_search
        self._open_mode = open_mode
        self._window_title = window_title
        self._close_other_windows = close_other_windows
        self._last_win_id = None
        self._debug_printed = False
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(1000)
        self._watch_timer.timeout.connect(self._watch_embedded_window)
        self._can_find_window = bool(
            shutil.which("xdotool") or shutil.which("wmctrl") or shutil.which("xwininfo")
        )
        self._container = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(500)
        self._poll_timer.timeout.connect(self._try_embed)
        self._poll_attempts = 0
        self._max_attempts = 60

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._status = QLabel("Starting Obsidian...")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet(
            "QWidget { background-color: #ffffff; } QLabel { color: #333333; }"
        )

        if not self._obsidian_cmd:
            self._status.setText("Obsidian not found in PATH. Install or provide --obsidian-path.")
            return

        self._launch_obsidian()
        if not self._can_find_window:
            self._status.setText(
                "Install xdotool, wmctrl, or use xwininfo to embed Obsidian."
            )
            return
        self._poll_timer.start()

    def _launch_obsidian(self):
        try:
            subprocess.Popen(self._obsidian_cmd)
        except OSError:
            self._status.setText("Failed to start Obsidian.")
            return

        if not self._no_open:
            uri = self._build_open_uri()
            if uri:
                QTimer.singleShot(self._open_delay_ms, lambda: subprocess.Popen(["xdg-open", uri]))
        if self._obsidian_command or self._obsidian_view:
            QTimer.singleShot(2500, self._send_advanced_uri)

    def _try_embed(self):
        self._poll_attempts += 1
        require_title = bool(self._window_title)
        win_id = self._find_obsidian_window_id(require_title=require_title)
        if win_id:
            self._poll_timer.stop()
            self._last_win_id = win_id
            self._embed_window(win_id)
            self._watch_timer.start()
            if self._close_other_windows:
                QTimer.singleShot(self._zen_delay_ms, self._close_other_obsidian_windows)
            if self._zen_hotkey:
                QTimer.singleShot(self._zen_delay_ms, self._send_zen_hotkey)
            if self._hotkeys and self.current_path:
                QTimer.singleShot(self._zen_delay_ms, self._send_hotkeys)
            return
        if self._poll_attempts >= self._max_attempts:
            self._poll_timer.stop()
            self._status.setText(
                "Unable to find Obsidian window. Install xdotool or wmctrl."
            )

    def _find_obsidian_window_id(self, require_title: bool = False) -> int | None:
        if shutil.which("xdotool"):
            for args in (["--classname", "obsidian"], ["--name", "Obsidian"]):
                result = subprocess.run(
                    ["xdotool", "search", "--onlyvisible", *args],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if self._debug_window_search and not self._debug_printed:
                    print(f"[ObsidianEmbed] xdotool search {args}: {result.stdout.strip()}")
                if result.stdout.strip():
                    line = result.stdout.strip().splitlines()[0]
                    try:
                        return int(line, 0)
                    except ValueError:
                        return None
        if shutil.which("wmctrl"):
            result = subprocess.run(
                ["wmctrl", "-lx"],
                capture_output=True,
                text=True,
                check=False,
            )
            if self._debug_window_search and not self._debug_printed:
                print("[ObsidianEmbed] wmctrl -lx output:")
                print(result.stdout)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) < 3:
                    continue
                win_id, wm_class = parts[0], parts[2]
                if "obsidian" in wm_class.lower():
                    try:
                        return int(win_id, 16)
                    except ValueError:
                        return None
        if shutil.which("xwininfo"):
            candidates: list[tuple[int, int, str]] = []
            if self._debug_window_search and not self._debug_printed:
                tree = subprocess.run(
                    ["xwininfo", "-root", "-tree"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                print("[ObsidianEmbed] xwininfo -root -tree matches:")
                for line in tree.stdout.splitlines():
                    if "Obsidian" in line or "obsidian" in line:
                        print(line.strip())
            tree = subprocess.run(
                ["xwininfo", "-root", "-tree"],
                capture_output=True,
                text=True,
                check=False,
            )
            for line in tree.stdout.splitlines():
                line = line.strip()
                if not line.startswith("0x"):
                    continue
                if "Obsidian" not in line and "obsidian" not in line:
                    continue
                parts = line.split()
                if not parts:
                    continue
                try:
                    win_id = int(parts[0], 16)
                except ValueError:
                    continue
                if "InputOnly" in line:
                    continue
                if "20x20" in line:
                    continue
                size = self._parse_window_size(line)
                title = self._parse_window_title(line)
                candidates.append((size, win_id, title))
            if self._window_title:
                title_lower = self._window_title.lower()
                for _, win_id, title in sorted(candidates, reverse=True):
                    if title_lower in title.lower():
                        return win_id
                if require_title:
                    return None
            for _, win_id, _ in sorted(candidates, reverse=True):
                if self._is_window_mapped(win_id):
                    return win_id
            # Fallback: pick the largest candidate even if unmapped
            if candidates:
                return sorted(candidates, reverse=True)[0][1]
            for name in ("Obsidian", "obsidian"):
                result = subprocess.run(
                    ["xwininfo", "-name", name],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if self._debug_window_search and not self._debug_printed:
                    print(f"[ObsidianEmbed] xwininfo -name {name}: {result.stdout.strip()}")
                for line in result.stdout.splitlines():
                    if "Window id:" in line:
                        parts = line.strip().split()
                        try:
                            win_id = parts[2]
                        except IndexError:
                            continue
                        try:
                            parsed_id = int(win_id, 16)
                        except ValueError:
                            continue
                        if self._window_title and require_title:
                            continue
                        if self._is_window_mapped(parsed_id):
                            return parsed_id
                        return parsed_id
            if self._debug_window_search and not self._debug_printed:
                self._debug_printed = True
        return None

    def _is_window_mapped(self, win_id: int) -> bool:
        if not shutil.which("xwininfo"):
            return True
        result = subprocess.run(
            ["xwininfo", "-id", hex(win_id)],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in result.stdout.splitlines():
            if "Map State:" in line:
                return "IsViewable" in line
        return False

    def _parse_window_size(self, line: str) -> int:
        # Try to extract width x height from xwininfo tree line for ranking
        for token in line.split():
            if "x" in token and "+" in token:
                size = token.split("+", 1)[0]
                try:
                    width, height = size.split("x", 1)
                    return int(width) * int(height)
                except ValueError:
                    continue
        return 0

    def _parse_window_title(self, line: str) -> str:
        if "\"" not in line:
            return ""
        parts = line.split("\"", 2)
        if len(parts) < 2:
            return ""
        return parts[1]

    def _close_other_obsidian_windows(self):
        if not shutil.which("xdotool"):
            return
        if not shutil.which("xwininfo"):
            return
        target_fragment = (self._window_title or "").lower()
        tree = subprocess.run(
            ["xwininfo", "-root", "-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in tree.stdout.splitlines():
            line = line.strip()
            if not line.startswith("0x"):
                continue
            if "Obsidian" not in line and "obsidian" not in line:
                continue
            win_id = line.split()[0]
            title = self._parse_window_title(line).lower()
            if target_fragment and target_fragment in title:
                continue
            if self._last_win_id and win_id == hex(self._last_win_id):
                continue
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", win_id, "key", "ctrl+shift+w"],
                check=False,
            )

    def _send_advanced_uri(self):
        params = {}
        if self.current_path:
            params["filepath"] = str(self.current_path)
        if self._obsidian_view:
            params["view"] = self._obsidian_view
        if self._obsidian_command:
            params["commandid"] = self._obsidian_command
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        uri = f"obsidian://advanced-uri?{query}"
        subprocess.Popen(["xdg-open", uri])

    def _build_open_uri(self) -> str | None:
        vault_info = self._resolve_vault_info()
        vault_name = vault_info.get("vault")
        vault_file = vault_info.get("file")
        if self._obsidian_command or self._obsidian_view or self._open_mode:
            params = {}
            if vault_name and vault_file:
                params["vault"] = vault_name
                params["file"] = vault_file
            elif self.current_path:
                params["filepath"] = str(self.current_path)
            if self._obsidian_view:
                params["view"] = self._obsidian_view
            if self._obsidian_command:
                params["commandid"] = self._obsidian_command
            if self._open_mode:
                params["openmode"] = self._open_mode
            if params:
                query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                return f"obsidian://advanced-uri?{query}"
        if vault_name and vault_file:
            vault = urllib.parse.quote(vault_name)
            file_path = urllib.parse.quote(vault_file)
            return f"obsidian://open?vault={vault}&file={file_path}"
        if self.current_path:
            path = urllib.parse.quote(str(self.current_path))
            return f"obsidian://open?path={path}"
        return None

    def _resolve_vault_info(self) -> dict:
        if self._obsidian_vault and self._obsidian_file:
            return {"vault": self._obsidian_vault, "file": self._obsidian_file}
        if self._obsidian_vault_path and self.current_path:
            vault_path = Path(self._obsidian_vault_path).expanduser().resolve()
            try:
                rel_path = self.current_path.resolve().relative_to(vault_path)
            except ValueError:
                return {}
            return {"vault": vault_path.name, "file": rel_path.as_posix()}
        return {}

    def _watch_embedded_window(self):
        if not self._last_win_id:
            return
        if self._is_window_mapped(self._last_win_id):
            return
        self._watch_timer.stop()
        if self._container:
            self._container.setVisible(False)
        self._status.setText("Obsidian window lost. Waiting to re-attach...")
        self._status.show()
        self._last_win_id = None
        if not self._poll_timer.isActive():
            self._poll_timer.start()

    def _send_zen_hotkey(self):
        if not self._last_win_id:
            return
        if shutil.which("xdotool"):
            subprocess.run(
                [
                    "xdotool",
                    "windowactivate",
                    "--sync",
                    str(self._last_win_id),
                    "key",
                    self._zen_hotkey,
                ],
                check=False,
            )

    def _send_hotkeys(self):
        if not self._last_win_id or not shutil.which("xdotool"):
            return
        for idx, hotkey in enumerate(self._hotkeys):
            delay = idx * self._hotkey_gap_ms
            QTimer.singleShot(
                delay,
                lambda hk=hotkey: subprocess.run(
                    [
                        "xdotool",
                        "windowactivate",
                        "--sync",
                        str(self._last_win_id),
                        "key",
                        hk,
                    ],
                    check=False,
                ),
            )

    def send_close_hotkey(self):
        if not self._last_win_id or not self._close_hotkey:
            return
        if shutil.which("xdotool"):
            subprocess.run(
                [
                    "xdotool",
                    "windowactivate",
                    "--sync",
                    str(self._last_win_id),
                    "key",
                    self._close_hotkey,
                ],
                check=False,
            )

    def _resolve_obsidian_command(self, obsidian_path: str | None) -> list[str] | None:
        if obsidian_path:
            return shlex.split(obsidian_path)
        found = shutil.which("obsidian")
        if not found:
            return None
        return [found]

    def _embed_window(self, win_id: int):
        window = QWindow.fromWinId(win_id)
        if not window:
            self._status.setText("Failed to attach to Obsidian window.")
            return
        self._container = QWidget.createWindowContainer(window, self)
        self.layout().addWidget(self._container)
        self._status.hide()

    def set_view_mode(self, mode: str):
        return

    def apply_background(self, color_hex: str):
        return

    def wrap_selection(self, *args, **kwargs):
        return

    def update_window_metadata(self, *args, **kwargs):
        return

    def get_markdown(self) -> str:
        if self.current_path and self.current_path.exists():
            return self.current_path.read_text(encoding="utf-8")
        return ""

    def set_path(self, path: Path):
        self.current_path = path


class PostFixWindow(QMainWindow):
    """Main application window."""
    
    def __init__(
        self,
        open_path: Path | None = None,
        debug: bool = False,
        embed_obsidian: bool = False,
        obsidian_path: str | None = None,
        obsidian_command: str | None = None,
        obsidian_view: str | None = None,
        zen_hotkey: str | None = None,
        zen_delay_ms: int = 2500,
        obsidian_hotkeys: list[str] | None = None,
        obsidian_hotkey_gap_ms: int = 300,
        obsidian_close_hotkey: str | None = "ctrl+shift+w",
        obsidian_vault: str | None = None,
        obsidian_file: str | None = None,
        obsidian_open_delay_ms: int = 1500,
        obsidian_no_open: bool = False,
        obsidian_debug_window_search: bool = False,
        obsidian_open_mode: str | None = None,
        obsidian_window_title: str | None = None,
        obsidian_close_other_windows: bool = False,
        obsidian_vault_path: str | None = None,
    ):
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
        # Obsidian embed is paused for now. Keep the code here for later.
        # self.editor = ObsidianEmbed(
        #     open_path=open_path,
        #     obsidian_path=obsidian_path,
        #     obsidian_command=obsidian_command,
        #     obsidian_view=obsidian_view,
        #     zen_hotkey=zen_hotkey,
        #     zen_delay_ms=zen_delay_ms,
        #     hotkeys=obsidian_hotkeys,
        #     hotkey_gap_ms=obsidian_hotkey_gap_ms,
        #     close_hotkey=obsidian_close_hotkey,
        #     obsidian_vault=obsidian_vault,
        #     obsidian_file=obsidian_file,
        #     open_delay_ms=obsidian_open_delay_ms,
        #     no_open=obsidian_no_open,
        #     debug_window_search=obsidian_debug_window_search,
        #     open_mode=obsidian_open_mode,
        #     window_title=obsidian_window_title,
        #     close_other_windows=obsidian_close_other_windows,
        #     obsidian_vault_path=obsidian_vault_path,
        # )
        self.editor = SmartEditor(show_frontmatter=debug)
        self.right_sidebar = TagSidebar()
        # Always wire editor->window theme callback; dynamic attribute on SmartEditor.
        self.editor.on_theme_color_changed = self.apply_theme_color_hex
        if hasattr(self.editor, "MODE_FOCUS"):
            self.editor.set_view_mode(self.editor.MODE_FOCUS)
            self.btn_view_mode.setText(self.editor.MODE_FOCUS)
            self.btn_view_mode.setEnabled(False)
        if hasattr(self.editor, "tagsChanged"):
            self.editor.tagsChanged.connect(self.right_sidebar.set_tags)
        elif embed_obsidian:
            self.btn_view_mode.setText("Obsidian")
            self.btn_view_mode.setEnabled(False)
            for btn in [self.btn_bg_color, self.btn_text_color, self.btn_highlight]:
                btn.setEnabled(False)
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
        main_layout.addWidget(self.btn_close, 0, 2, Qt.AlignLeft | Qt.AlignTop)

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
        self.apply_theme_color_hex(self.editor.current_bg)
        if open_path and open_path.exists() and hasattr(self.editor, "load_markdown"):
            self.editor.load_markdown(open_path.read_text(encoding="utf-8"))
            if hasattr(self.editor, "set_path"):
                self.editor.set_path(open_path)
        elif hasattr(self.editor, "tagsChanged"):
            self.right_sidebar.set_tags([])
        
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
        layout.setContentsMargins(8, 0, 2, 0)
        
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
        self.btn_view_mode = QPushButton("Focus Mode")
        self.btn_view_mode.setCursor(Qt.PointingHandCursor)
        self.apply_oval_button_style(self.btn_view_mode, "#FFF740", "#d4c600")
        self.btn_view_mode.hide()
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
        """Single-mode editor: keep focus mode active."""
        self.btn_view_mode.setText(SmartEditor.MODE_FOCUS)
        self.editor.set_view_mode(SmartEditor.MODE_FOCUS)
        
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
                background-color: rgba(0, 0, 0, 0);
                border: 1px solid rgba(0, 0, 0, 60);
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 25);
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
        self.strip_left_top.setStyleSheet(
            f"QFrame {{ background-color: {color_hex}; }}"
        )
        self.topbar_bg.setStyleSheet(
            f"QFrame {{ background-color: {color_hex}; }}"
        )
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

    def closeEvent(self, event):
        if hasattr(self.editor, "send_close_hotkey"):
            self.editor.send_close_hotkey()
        super().closeEvent(event)


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
    parser.add_argument(
        "--embed-obsidian",
        action="store_true",
        help="Embed an existing Obsidian window into the editor area (X11 only)",
    )
    parser.add_argument(
        "--obsidian-path",
        help="Path to Obsidian executable (if not in PATH)",
    )
    parser.add_argument(
        "--obsidian-command",
        help="Advanced URI command name or id (requires Advanced URI plugin)",
    )
    parser.add_argument(
        "--obsidian-view",
        choices=["live", "source", "preview"],
        help="Open Obsidian in a specific view (requires Advanced URI plugin)",
    )
    parser.add_argument(
        "--obsidian-zen-hotkey",
        help="Send a zen-mode hotkey via xdotool (e.g. ctrl+shift+z)",
    )
    parser.add_argument(
        "--obsidian-zen-delay-ms",
        type=int,
        default=2500,
        help="Delay before sending zen hotkey (ms)",
    )
    parser.add_argument(
        "--obsidian-hotkey",
        action="append",
        help="Send additional hotkeys via xdotool (repeatable)",
    )
    parser.add_argument(
        "--obsidian-hotkey-gap-ms",
        type=int,
        default=300,
        help="Gap between additional hotkeys (ms)",
    )
    parser.add_argument(
        "--obsidian-close-hotkey",
        default="ctrl+shift+w",
        help="Hotkey to close Obsidian window on exit",
    )
    parser.add_argument(
        "--obsidian-vault",
        help="Vault name to open (uses obsidian://open?vault=...&file=...)",
    )
    parser.add_argument(
        "--obsidian-file",
        help="File path inside vault (relative, without extension if desired)",
    )
    parser.add_argument(
        "--obsidian-open-delay-ms",
        type=int,
        default=1500,
        help="Delay before opening file via URI (ms)",
    )
    parser.add_argument(
        "--obsidian-no-open",
        action="store_true",
        help="Do not open a file/vault via URI at startup",
    )
    parser.add_argument(
        "--obsidian-debug-window-search",
        action="store_true",
        help="Print window search output for embedding Obsidian",
    )
    parser.add_argument(
        "--obsidian-open-mode",
        choices=["window", "split", "tab"],
        help="Open mode for Advanced URI (requires plugin)",
    )
    parser.add_argument(
        "--obsidian-window-title",
        help="Prefer embedding window with this title fragment",
    )
    parser.add_argument(
        "--obsidian-close-other-windows",
        action="store_true",
        help="Close other Obsidian windows after embed (requires xdotool)",
    )
    parser.add_argument(
        "--obsidian-vault-path",
        help="Vault base path (used to compute vault name + file path)",
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
    window = PostFixWindow(
        open_path=open_path,
        debug=args.debug,
        embed_obsidian=args.embed_obsidian,
        obsidian_path=args.obsidian_path,
        obsidian_command=args.obsidian_command,
        obsidian_view=args.obsidian_view,
        zen_hotkey=args.obsidian_zen_hotkey,
        zen_delay_ms=args.obsidian_zen_delay_ms,
        obsidian_hotkeys=args.obsidian_hotkey,
        obsidian_hotkey_gap_ms=args.obsidian_hotkey_gap_ms,
        obsidian_close_hotkey=args.obsidian_close_hotkey,
        obsidian_vault=args.obsidian_vault,
        obsidian_file=args.obsidian_file,
        obsidian_open_delay_ms=args.obsidian_open_delay_ms,
        obsidian_no_open=args.obsidian_no_open,
        obsidian_debug_window_search=args.obsidian_debug_window_search,
        obsidian_open_mode=args.obsidian_open_mode,
        obsidian_window_title=args.obsidian_window_title,
        obsidian_close_other_windows=args.obsidian_close_other_windows,
        obsidian_vault_path=args.obsidian_vault_path,
    )
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
