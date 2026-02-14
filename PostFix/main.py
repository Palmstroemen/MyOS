#!/usr/bin/env python3
"""
PostFix - Main Application Entry Point
Builds UI directly in Python without .ui files for full control.
"""
import subprocess
import tempfile
import re
from pathlib import Path

import markdown2
try:
    from .ui_panels import TagSidebar, ACLSidebar, BottomToolbar
    from .smart_editor import SmartEditor
    from .window_layout import WindowLayoutMixin
    from .window_tags import WindowTagsMixin
    from .window_theme import WindowThemeMixin
except ImportError:
    from ui_panels import TagSidebar, ACLSidebar, BottomToolbar
    from smart_editor import SmartEditor
    from window_layout import WindowLayoutMixin
    from window_tags import WindowTagsMixin
    from window_theme import WindowThemeMixin
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QPushButton, QLabel,
                               QSpacerItem, QSizePolicy, QFrame,
                               QGraphicsOpacityEffect, QStackedLayout)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint, QEvent, QRect, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QTextDocument
from PySide6.QtPrintSupport import QPrinter

class PostFixWindow(WindowLayoutMixin, WindowTagsMixin, WindowThemeMixin, QMainWindow):
    """Main application window."""
    NOTE_STYLE_ALIASES = {
        "postit": "postit",
        "kurznotiz": "postit",
        "sticky": "postit",
        "sheet": "sheet",
        "a4": "sheet",
        "blatt": "sheet",
        "mitschrift": "sheet",
        "notebook": "notebook",
        "heft": "notebook",
        "konzept": "notebook",
        "cloud": "cloud",
        "gedankenskizze": "cloud",
        "chat": "chat",
        "aichat": "chat",
        "aichatbubble": "chat",
        "sprechblase": "chat",
        "config": "config",
        "konfig": "config",
        "konfiguration": "config",
        "settings": "config",
    }
    
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
        self._doc_tags = []
        self._doc_color_defs = []
        self._scope_tags = []
        self._scope_tags_path = None
        self._tag_color_map = {}
        self._vault_root = None
        self._app_json_path = None
        self._app_json_data = {}
        # Always wire editor->window theme callback; dynamic attribute on SmartEditor.
        self.editor.on_theme_color_changed = self.apply_theme_color_hex
        if hasattr(self.editor, "MODE_FOCUS"):
            self.editor.set_view_mode(self.editor.MODE_FOCUS)
            self.btn_view_mode.setText(self.editor.MODE_FOCUS)
            self.btn_view_mode.setEnabled(False)
        if hasattr(self.editor, "tagsChanged"):
            self.editor.tagsChanged.connect(self._on_editor_tags_changed)
        if hasattr(self.editor, "colorDefinitionsChanged"):
            self.editor.colorDefinitionsChanged.connect(self._on_editor_color_definitions_changed)
        elif embed_obsidian:
            self.btn_view_mode.setText("Obsidian")
            self.btn_view_mode.setEnabled(False)
            for btn in [self.btn_bg_color, self.btn_text_color, self.btn_highlight]:
                btn.setEnabled(False)
        if hasattr(self.right_sidebar, "tagColorChangeRequested"):
            self.right_sidebar.tagColorChangeRequested.connect(self._on_tag_color_change)
        if hasattr(self.right_sidebar, "colorDefinitionChangeRequested"):
            self.right_sidebar.colorDefinitionChangeRequested.connect(self._on_color_definition_change)
        if hasattr(self.right_sidebar, "colorDefinitionSearchRequested"):
            self.right_sidebar.colorDefinitionSearchRequested.connect(self._on_color_definition_search)
        self._theme_anim = None
        self._syncing_note_style_combo = False
        self._current_theme_color = self.editor.current_bg
        self._meta_timer = QTimer(self)
        self._meta_timer.setSingleShot(True)
        self._meta_timer.timeout.connect(self._flush_window_metadata)
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_current_document)
        self._scope_sync_timer = QTimer(self)
        self._scope_sync_timer.setSingleShot(True)
        self._scope_sync_timer.timeout.connect(self._sync_scope_tags_from_document)
        if hasattr(self.editor, "source_edit"):
            self.editor.source_edit.textChanged.connect(self._schedule_save)

        self.acl_host = QFrame()
        self._show_acl_dummy = False
        self.acl_host.setFixedWidth(120 if self._show_acl_dummy else 0)
        acl_layout = QVBoxLayout(self.acl_host)
        acl_layout.setContentsMargins(0, 0, 0, 0)
        acl_layout.addWidget(self.left_sidebar)
        self.acl_host.setVisible(self._show_acl_dummy)

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
        if self._show_acl_dummy:
            left_mid_stack.addWidget(self.acl_host)
        left_mid_stack.addWidget(self.strip_left_mid_host)
        if self._show_acl_dummy:
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
        self.close_corner_host = QWidget()
        close_corner_layout = QHBoxLayout(self.close_corner_host)
        close_corner_layout.setContentsMargins(5, 5, 0, 0)
        close_corner_layout.setSpacing(0)
        close_corner_layout.addWidget(self.btn_close, 0, Qt.AlignLeft | Qt.AlignTop)
        close_corner_layout.addStretch(1)
        main_layout.addWidget(self.close_corner_host, 0, 2)
        self._init_close_corner_fade()

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
        if open_path and open_path.exists() and hasattr(self.editor, "load_markdown"):
            self.editor.load_markdown(open_path.read_text(encoding="utf-8"))
            if hasattr(self.editor, "set_path"):
                self.editor.set_path(open_path)
        self._sync_note_style_selector_from_document()
        self._defer_noncritical_startup()

    def _defer_noncritical_startup(self):
        # First paint: show markdown quickly, then warm up non-critical UI.
        QTimer.singleShot(0, self._finish_noncritical_startup)

    def _finish_noncritical_startup(self):
        self.apply_theme_color_hex(self.editor.current_bg)
        if getattr(self.editor, "current_path", None):
            self._reload_tag_context()
        elif hasattr(self.editor, "tagsChanged"):
            self.right_sidebar.set_tags([])
        
    def _schedule_save(self):
        self._save_timer.start(250)

    def _save_current_document(self) -> bool:
        if not hasattr(self, "editor"):
            return False
        path = getattr(self.editor, "current_path", None)
        if not path:
            return False
        # Finalize scoped tag list using stable editor state at save time.
        self._sync_scope_tags_from_document()
        try:
            content = self.editor.get_markdown()
            path.write_text(content, encoding="utf-8")
            return True
        except OSError:
            return False
        
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

    def _normalize_note_style(self, raw) -> str:
        text = str(raw or "").strip().lower()
        if not text:
            return ""
        key = re.sub(r"[^a-z0-9]+", "", text)
        return self.NOTE_STYLE_ALIASES.get(key, "")

    def _sync_note_style_selector_from_document(self):
        combo = getattr(self, "note_style_combo", None)
        editor = getattr(self, "editor", None)
        if combo is None or editor is None:
            return
        raw = editor.get_frontmatter_field("note_style")
        if raw in (None, ""):
            raw = editor.get_frontmatter_field("myos_note_style")
        normalized = self._normalize_note_style(raw)
        idx = combo.findData(normalized)
        if idx < 0:
            idx = combo.findData("")
        self._syncing_note_style_combo = True
        combo.setCurrentIndex(max(0, idx))
        self._syncing_note_style_combo = False

    def on_note_style_selected(self, _index: int):
        if self._syncing_note_style_combo:
            return
        combo = getattr(self, "note_style_combo", None)
        if combo is None:
            return
        normalized = self._normalize_note_style(combo.currentData())
        if normalized:
            self.editor.set_frontmatter_field("note_style", normalized)
            # Keep a single canonical key in frontmatter.
            self.editor.set_frontmatter_field("myos_note_style", None)
        else:
            self.editor.set_frontmatter_field("note_style", None)
            self.editor.set_frontmatter_field("myos_note_style", None)
        self._schedule_save()

    def eventFilter(self, obj, event):
        if obj in (getattr(self, "top_toolbar", None), getattr(self, "close_corner_host", None)):
            if event.type() == QEvent.Enter:
                self.fade_topbar(1.0)
            elif event.type() == QEvent.Leave:
                self.fade_topbar(0.0)
            elif event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                if self._try_start_window_move(obj, event):
                    return True
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

    def _try_start_window_move(self, obj, event) -> bool:
        """Allow dragging the frameless window from free top-panel space."""
        handle = self.windowHandle()
        if handle is None:
            return False
        local_pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        child = obj.childAt(local_pos) if hasattr(obj, "childAt") else None
        if isinstance(child, QPushButton):
            return False
        return bool(handle.startSystemMove())

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
        self._save_current_document()

    def closeEvent(self, event):
        self._save_current_document()
        super().closeEvent(event)

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


def main():
    try:
        from .cli import main as cli_main
    except ImportError:
        from cli import main as cli_main
    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())
