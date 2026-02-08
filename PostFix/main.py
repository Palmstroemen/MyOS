#!/usr/bin/env python3
"""
PostFix - Main Application Entry Point
Builds UI directly in Python without .ui files for full control.
"""
import sys
from pathlib import Path

import markdown2
import yaml
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLabel,
                               QSpacerItem, QSizePolicy, QFrame, QColorDialog,
                               QPlainTextEdit, QTextBrowser, QStackedWidget,
                               QSplitter, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QVariantAnimation, QEvent
from PySide6.QtGui import QColor, QPalette, QTextCursor, QIcon, QFont

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
        self.base_opacity = 0.6  # Half transparent when idle
        self.hover_opacity = 0.9  # More visible on hover
        
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
        
        # Clear placeholder widgets
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add ACL checkboxes (fake implementation)
        acl_items = ["Alfred", "Bertha", "Christian", "Doris", 
                    "Buchhaltung", "Entwicklung", "Dokumentation"]
        
        for item in acl_items:
            # Using buttons for now, could be checkboxes
            btn = QPushButton(f"○ {item}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #333333;
                    border: none;
                    text-align: left;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 50);
                    border-radius: 3px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)
        
        layout.addStretch()


class BottomToolbar(QWidget):
    """Two-level bottom toolbar with hover effect."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(30)
        self.setMaximumHeight(30)  # Only primary level visible initially
        self.theme_color = "#FFF740"
        self.theme_border = "#d4c600"
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Secondary toolbar (hidden initially)
        self.secondary_toolbar = QWidget()
        self.secondary_toolbar.setStyleSheet(
            f"QWidget {{ background-color: {self.theme_color}; border-bottom: 1px solid transparent; }}"
        )
        self.secondary_layout = QHBoxLayout(self.secondary_toolbar)
        self.secondary_layout.setSpacing(15)
        
        # Primary toolbar (always visible)
        self.primary_toolbar = QWidget()
        self.primary_toolbar.setStyleSheet(
            f"QWidget {{ background-color: {self.theme_color}; border-top: 1px solid transparent; }}"
        )
        self.primary_layout = QHBoxLayout(self.primary_toolbar)
        self.primary_layout.setSpacing(15)
        
        # Add toolbars to main layout
        self.main_layout.addWidget(self.secondary_toolbar)
        self.main_layout.addWidget(self.primary_toolbar)
        
        # Initially hide secondary toolbar
        self.secondary_toolbar.hide()
        
        # Setup content
        self.setup_primary_toolbar()
        self.setup_secondary_toolbar()
        
    def setup_primary_toolbar(self):
        """Setup the always-visible primary toolbar."""
        # Primary action buttons
        actions = ["Send To", "Open In", "Print"]
        
        for action in actions:
            btn = QPushButton(action)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #333333;
                    border: none;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    background-color: rgba(200, 200, 200, 100);
                    border-radius: 3px;
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            
            # Connect hover to show secondary toolbar
            btn.enterEvent = lambda e, a=action: self.show_secondary(a)
            btn.leaveEvent = lambda e: self.start_hide_timer()
            
            self.primary_layout.addWidget(btn)
        
        # Add stretch
        self.primary_layout.addStretch()
        
    def setup_secondary_toolbar(self):
        """Setup the secondary toolbar that appears on hover."""
        # Clear any existing widgets
        while self.secondary_layout.count():
            item = self.secondary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add some example secondary actions
        # In real implementation, this would change based on primary selection
        example_actions = ["Email", "WhatsApp", "Telegram", "Obsidian", 
                          "LibreOffice", "PDF Printer", "Network Printer"]
        
        for action in example_actions:
            btn = QPushButton(action)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 100, 100, 100);
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: rgba(150, 150, 150, 150);
                }
            """)
            btn.setCursor(Qt.PointingHandCursor)
            self.secondary_layout.addWidget(btn)
        
        self.secondary_layout.addStretch()
        
    def show_secondary(self, primary_action):
        """Show secondary toolbar for the given primary action."""
        # Update secondary toolbar based on primary action
        self.setup_secondary_toolbar()  # Recreate with appropriate actions
        
        # Animate show
        if not self.secondary_toolbar.isVisible():
            self.secondary_toolbar.show()
            self.setMaximumHeight(60)  # Expand to show both levels
            
    def start_hide_timer(self):
        """Start timer to hide secondary toolbar (simplified)."""
        # For simplicity, we hide immediately when mouse leaves
        # In production, you'd use a QTimer with short delay
        self.hide_secondary()
        
    def hide_secondary(self):
        """Hide secondary toolbar."""
        if self.secondary_toolbar.isVisible():
            self.secondary_toolbar.hide()
            self.setMaximumHeight(30)  # Back to primary only

    def set_theme_color(self, color_hex: str):
        self.theme_color = color_hex
        self.theme_border = QColor(color_hex).darker(120).name()
        self.secondary_toolbar.setStyleSheet(
            f"QWidget {{ background-color: {self.theme_color}; border-bottom: 1px solid transparent; }}"
        )
        self.primary_toolbar.setStyleSheet(
            f"QWidget {{ background-color: {self.theme_color}; border-top: 1px solid transparent; }}"
        )


class SmartEditor(QWidget):
    """Central editor with source, preview, and split modes."""

    MODE_PREVIEW = "Live Preview"
    MODE_SOURCE = "Edit Source"
    MODE_SPLIT = "Split View"

    def __init__(self):
        super().__init__()
        self.metadata = MetadataManager()
        self.current_bg = "#ffffff"
        self._current_border = QColor(self.current_bg).darker(120).name()
        self._bg_anim = None
        self._bg_initialized = False
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

        initial_text = (
            "---\n"
            "title: PostFix Note\n"
            "background_color: #ffffff\n"
            "---\n"
            "Start writing your note here.\n"
        )
        self.source_edit.setPlainText(initial_text)

    def load_markdown(self, text: str):
        self.source_edit.setPlainText(text)
        bg = self.metadata.get_field(text, "background_color")
        if isinstance(bg, str) and bg.startswith("#"):
            self.apply_background(bg)
        else:
            self.render_preview()

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
            updated = self.metadata.update_field(
                self.source_edit.toPlainText(), "background_color", color_hex
            )
            cursor = self.source_edit.textCursor()
            pos = cursor.position()
            self.source_edit.blockSignals(True)
            self.source_edit.setPlainText(updated)
            self.source_edit.blockSignals(False)
            cursor.setPosition(min(pos, len(updated)))
            self.source_edit.setTextCursor(cursor)
            self.render_preview()

    def apply_editor_background(self, color: QColor):
        color_hex = color.name()
        self.source_edit.setStyleSheet(
            f"QPlainTextEdit {{ background-color: {color_hex}; padding: 12px; }}"
        )
        self.preview.setStyleSheet(
            f"QTextBrowser {{ background-color: {color_hex}; padding: 12px; }}"
        )

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
    
    def __init__(self, open_path: Path | None = None):
        super().__init__()
        self.setWindowTitle("PostFix")
        self.setGeometry(100, 100, 900, 650)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setWindowOpacity(1.0)
        
        # Set application styles
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                font-size: 12px;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setStyleSheet("QWidget { background: transparent; }")
        self.setCentralWidget(central_widget)
        
        # Main layout (5x3 grid)
        main_layout = QGridLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create and add top toolbar
        self.create_top_toolbar()
        self.top_toolbar.setFixedHeight(40)
        self.init_topbar_fade()

        # Center area (editor + sidebars)
        self.left_sidebar = ACLSidebar()
        self.editor = SmartEditor()
        self.right_sidebar = TagSidebar()
        self.editor.on_theme_color_changed = self.update_theme_color
        self._theme_anim = None
        self._current_theme_color = self.editor.current_bg

        # Bottom toolbar
        self.bottom_toolbar = BottomToolbar()

        # Corner widgets (more transparent)
        self.corner_tl = self.make_corner_widget()
        self.corner_tr = self.make_corner_widget()
        self.corner_bl = self.make_corner_widget()
        self.corner_br = self.make_corner_widget()

        # Inner side strips (theme-colored)
        self.strip_left_top = self.make_strip_widget()
        self.strip_left_mid = self.make_strip_widget()
        self.strip_left_bot = self.make_strip_widget()
        self.strip_right_top = self.make_strip_widget()
        self.strip_right_mid = self.make_strip_widget()
        self.strip_right_bot = self.make_strip_widget()

        self.topbar_bg = QFrame()
        self.topbar_bg.setStyleSheet("QFrame { background-color: #ffffff; }")

        # Layout: 5x3 grid
        main_layout.addWidget(self.corner_tl, 0, 0)
        main_layout.addWidget(self.strip_left_top, 0, 1)
        main_layout.addWidget(self.topbar_bg, 0, 2)
        main_layout.addWidget(self.top_toolbar, 0, 2)
        main_layout.addWidget(self.strip_right_top, 0, 3)
        main_layout.addWidget(self.corner_tr, 0, 4)

        main_layout.addWidget(self.left_sidebar, 1, 0)
        main_layout.addWidget(self.strip_left_mid, 1, 1)
        main_layout.addWidget(self.editor, 1, 2)
        main_layout.addWidget(self.right_sidebar, 1, 3, 1, 2)

        main_layout.addWidget(self.corner_bl, 2, 0)
        main_layout.addWidget(self.strip_left_bot, 2, 1)
        main_layout.addWidget(self.bottom_toolbar, 2, 2)
        main_layout.addWidget(self.strip_right_bot, 2, 3)
        main_layout.addWidget(self.corner_br, 2, 4)

        main_layout.setRowStretch(1, 1)
        main_layout.setColumnStretch(2, 1)
        main_layout.setColumnMinimumWidth(1, 40)
        main_layout.setColumnMinimumWidth(3, 40)
        
        # Connect signals
        self.connect_signals()
        self.update_theme_color(self.editor.current_bg)
        if open_path and open_path.exists():
            self.editor.load_markdown(open_path.read_text(encoding="utf-8"))
        
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
        
        # Expanding spacer
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
        self.apply_round_button_style(self.btn_close, "#FFF740", "#d4c600")
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
            "#fff8b0", "#ffe082", "#ffd54f", "#ffb74d", "#ff8a65",
            "#f48fb1", "#ce93d8", "#90caf9", "#80cbc4", "#a5d6a7",
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
            grid.addWidget(btn, idx // 5, idx % 5)

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
        strip.setStyleSheet("QFrame { background-color: #FFF740; }")
        return strip

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
        self.left_sidebar.update_background_style(f"rgba({color.red()}, {color.green()}, {color.blue()}, 128)")
        self.right_sidebar.update_background_style(f"rgba({color.red()}, {color.green()}, {color.blue()}, 128)")
        for strip in [
            self.strip_left_top, self.strip_left_mid, self.strip_left_bot,
            self.strip_right_top, self.strip_right_mid, self.strip_right_bot,
        ]:
            strip.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
        self.topbar_bg.setStyleSheet(f"QFrame {{ background-color: {color_hex}; }}")
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
        if obj is self.top_toolbar:
            if event.type() == QEvent.Enter:
                self.fade_topbar(1.0)
            elif event.type() == QEvent.Leave:
                self.fade_topbar(0.0)
        return super().eventFilter(obj, event)

    def fade_topbar(self, target_opacity: float):
        if self._topbar_anim.state() == QPropertyAnimation.Running:
            self._topbar_anim.stop()
        self._topbar_anim.setStartValue(self._topbar_effect.opacity())
        self._topbar_anim.setEndValue(target_opacity)
        self._topbar_anim.start()


def main():
    """Application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("PostFix")
    app.setOrganizationName("PostFixDev")
    
    open_path = None
    if len(sys.argv) > 1:
        candidate = Path(sys.argv[1]).expanduser()
        if candidate.suffix.lower() == ".md":
            open_path = candidate
    window = PostFixWindow(open_path=open_path)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
