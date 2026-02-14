"""SmartEditor widget for PostFix."""

import difflib
import re
from pathlib import Path

import markdown2
from PySide6.QtCore import Qt, QEvent, QRect, Signal, QVariantAnimation, QPoint
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QPlainTextEdit, QFrame, QTextBrowser

try:
    from .metadata import MetadataManager
except ImportError:
    from metadata import MetadataManager


class SmartEditor(QWidget):
    """Central editor with source, preview, and split modes."""

    tagsChanged = Signal(list)
    colorDefinitionsChanged = Signal(list)

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
        self._focus_dynamic_end = None
        self._render_tag_colors = {}
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
        render_body = self._prepare_markdown_for_render(body)
        html = markdown2.markdown(render_body, extras=["fenced-code-blocks", "break-on-newline"])
        html = self._sanitize_rendered_html(html)
        self.preview.setHtml(html)
        self.preview.verticalScrollBar().setValue(scroll_value)
        self._refresh_index_gutter()
        self._rebuild_focus_spans()
        tags = self.extract_tags(body)
        color_defs = self.extract_color_definitions(body)
        self.tagsChanged.emit(tags)
        self.colorDefinitionsChanged.emit(color_defs)
        if sync_focus and self._active_focus_idx >= 0:
            self._apply_focus_text_from_source()
        self.apply_background(self.current_bg, update_frontmatter=False)

    def _on_source_changed(self):
        if self._syncing_focus:
            return
        self.render_preview(sync_focus=not self._editing_focus)

    def extract_tags(self, body: str):
        filtered_lines = []
        for line in (body or "").splitlines():
            if self._parse_color_definition_line(line):
                continue
            filtered_lines.append(line)
        found = re.findall(r"(?<!\w)#([a-zA-Z0-9_/\-äöüÄÖÜß]+)", "\n".join(filtered_lines))
        return sorted(set(found), key=lambda t: t.lower())

    def extract_color_definitions(self, body: str):
        entries = []
        seen = set()
        for line in (body or "").splitlines():
            parsed = self._parse_color_definition_line(line)
            if not parsed:
                continue
            key, value = parsed
            marker = (key.lower(), value.lower())
            if marker in seen:
                continue
            seen.add(marker)
            entries.append({"key": key, "hex": value})
        return entries

    def _parse_color_definition_line(self, line: str):
        match = re.match(r"^\s*([A-Za-z][\w-]*)\s*:\s*(#[0-9a-fA-F]{3}|#[0-9a-fA-F]{6})\s*$", line or "")
        if not match:
            return None
        return match.group(1), match.group(2).lower()

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

    def set_render_tag_colors(self, tag_colors: dict[str, str] | None):
        new_map = dict(tag_colors or {})
        if self._render_tag_colors == new_map:
            return
        self._render_tag_colors = new_map
        self.render_preview(sync_focus=False)

    def _text_color_for_bg(self, color_hex: str) -> str:
        color = QColor(color_hex)
        if not color.isValid():
            return "#ffffff"
        luminance = 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()
        return "#1f2433" if luminance > 165 else "#ffffff"

    def _prepare_markdown_for_render(self, body: str) -> str:
        prepared = []
        in_fence = False
        tag_heading_re = re.compile(r"^(\s{0,3})#([A-Za-z0-9_/\-äöüÄÖÜß]+)\b")
        any_tag_re = re.compile(r"(?<!\w)#([A-Za-z0-9_/\-äöüÄÖÜß]+)\b")
        render_colors = {str(k).lower(): v for k, v in (self._render_tag_colors or {}).items()}
        for line in (body or "").splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                prepared.append(line)
                continue
            if in_fence:
                prepared.append(line)
                continue
            if self._parse_color_definition_line(line):
                prepared.append(line)
                continue
            safe_line = tag_heading_re.sub(r"\1\\#\2", line)
            segments = safe_line.split("`")
            for idx in range(0, len(segments), 2):
                chunks = re.split(r"(<[^>]+>)", segments[idx])
                for cidx, chunk in enumerate(chunks):
                    if chunk.startswith("<") and chunk.endswith(">"):
                        continue

                    def _replace_tag(match):
                        tag_name = match.group(1)
                        color_hex = render_colors.get(tag_name.lower())
                        if not color_hex:
                            return match.group(0)
                        text_color = self._text_color_for_bg(color_hex)
                        return (
                            f"<span style=\"background-color: {color_hex}; color: {text_color}; "
                            f"border: 1px solid #222222; border-radius: 999px; padding: 1px 8px;\">"
                            f"#{tag_name}</span>"
                        )

                    chunks[cidx] = any_tag_re.sub(_replace_tag, chunk)
                segments[idx] = "".join(chunks)
            prepared.append("`".join(segments))
        return "".join(prepared)

    def _sanitize_rendered_html(self, html: str) -> str:
        """Best-effort sanitization against active/scripted content in preview."""
        out = html or ""
        # // Security: Remove high-risk active content blocks entirely.
        out = re.sub(r"<\s*(script|style|iframe|object|embed)\b[^>]*>.*?<\s*/\s*\1\s*>", "", out, flags=re.IGNORECASE | re.DOTALL)
        out = re.sub(r"<\s*(script|style|iframe|object|embed)\b[^>]*/\s*>", "", out, flags=re.IGNORECASE)
        # // Security: Remove inline event handlers (onclick/onerror/...) to prevent script execution.
        out = re.sub(r"(?i)\s+on[a-z0-9_-]+\s*=\s*\"[^\"]*\"", "", out)
        out = re.sub(r"(?i)\s+on[a-z0-9_-]+\s*=\s*'[^']*'", "", out)
        out = re.sub(r"(?i)\s+on[a-z0-9_-]+\s*=\s*[^\s>]+", "", out)

        def _sanitize_attr(match):
            attr = match.group(1)
            value = (match.group(2) or "").strip()
            lower = value.lower()
            if lower.startswith(("javascript:", "vbscript:", "data:")):
                return f'{attr}="#"'
            return match.group(0)

        def _sanitize_unquoted_attr(match):
            attr = match.group(1)
            value = (match.group(2) or "").strip()
            lower = value.lower()
            if lower.startswith(("javascript:", "vbscript:", "data:")):
                return f'{attr}="#"'
            return match.group(0)

        # // Security: Neutralize unsafe URI payloads across link-like attributes.
        out = re.sub(r'(?i)\b(href|src|formaction|xlink:href|poster)\s*=\s*"([^"]*)"', _sanitize_attr, out)
        out = re.sub(r"(?i)\b(href|src|formaction|xlink:href|poster)\s*=\s*'([^']*)'", _sanitize_attr, out)
        out = re.sub(r"(?i)\b(href|src|formaction|xlink:href|poster)\s*=\s*([^\s\"'>]+)", _sanitize_unquoted_attr, out)
        # // Security: Strip srcdoc to avoid injecting executable HTML payloads in embedded contexts.
        out = re.sub(r"(?i)\s+srcdoc\s*=\s*\"[^\"]*\"", "", out)
        out = re.sub(r"(?i)\s+srcdoc\s*=\s*'[^']*'", "", out)
        out = re.sub(r"(?i)\s+srcdoc\s*=\s*[^\s>]+", "", out)
        return out

    def replace_color_definition(self, key: str, old_hex: str, new_hex: str) -> bool:
        key_s = (key or "").strip()
        old_s = (old_hex or "").strip().lower()
        new_s = (new_hex or "").strip().lower()
        if not key_s or not QColor(new_s).isValid():
            return False

        body = self._source_body()
        exact_re = re.compile(
            rf"^(\s*{re.escape(key_s)}\s*:\s*){re.escape(old_s)}(\s*)$",
            re.IGNORECASE,
        )
        generic_re = re.compile(
            rf"^(\s*{re.escape(key_s)}\s*:\s*)(#[0-9a-fA-F]{{3}}|#[0-9a-fA-F]{{6}})(\s*)$",
            re.IGNORECASE,
        )
        changed = False
        out_lines = []
        for line in body.splitlines(keepends=True):
            base = line[:-1] if line.endswith("\n") else line
            m = exact_re.match(base)
            if m:
                suffix_nl = "\n" if line.endswith("\n") else ""
                out_lines.append(f"{m.group(1)}{new_s}{m.group(2)}{suffix_nl}")
                changed = True
                continue
            if not changed:
                m2 = generic_re.match(base)
                if m2:
                    suffix_nl = "\n" if line.endswith("\n") else ""
                    out_lines.append(f"{m2.group(1)}{new_s}{m2.group(3)}{suffix_nl}")
                    changed = True
                    continue
            out_lines.append(line)
        if not changed:
            return False
        self._set_source_body("".join(out_lines))
        self.render_preview(sync_focus=False)
        return True

    def jump_to_color_definition(self, key: str, hex_value: str) -> bool:
        key_s = (key or "").strip()
        hex_s = (hex_value or "").strip().lower()
        if not key_s:
            return False
        body_lines = self._source_body().splitlines()
        if not body_lines:
            return False

        exact_re = re.compile(
            rf"^\s*{re.escape(key_s)}\s*:\s*{re.escape(hex_s)}\s*$",
            re.IGNORECASE,
        )
        key_re = re.compile(
            rf"^\s*{re.escape(key_s)}\s*:\s*(#[0-9a-fA-F]{{3}}|#[0-9a-fA-F]{{6}})\s*$",
            re.IGNORECASE,
        )
        indices = [i for i, line in enumerate(body_lines) if exact_re.match(line)]
        if not indices:
            indices = [i for i, line in enumerate(body_lines) if key_re.match(line)]
        if not indices:
            return False

        current = self._active_focus_idx if self._active_focus_idx >= 0 else -1
        next_idx = None
        for i in indices:
            if i > current:
                next_idx = i
                break
        if next_idx is None:
            next_idx = indices[0]

        self._active_focus_idx = max(0, min(next_idx, len(self._focus_spans) - 1))
        self._overlay_top_hint = None
        self._apply_focus_text_from_source()
        self.focus_edit.setFocus()
        return True

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
        self._focus_dynamic_end = end
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
        self._focus_dynamic_end = None
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
        start, span_end = self._focus_spans[self._active_focus_idx]
        end = self._focus_dynamic_end if self._focus_dynamic_end is not None else span_end
        replacement = self.focus_edit.toPlainText().split("\n")
        new_lines = body_lines[:start] + replacement + body_lines[end:]
        self._focus_dynamic_end = start + len(replacement)
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

    def _select_word_in_focus(self, word: str):
        token = (word or "").strip()
        if not token:
            return
        text = self.focus_edit.toPlainText()
        if not text:
            return
        start = text.find(token)
        if start < 0:
            start = text.lower().find(token.lower())
        if start < 0:
            return
        cursor = self.focus_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(start + len(token), QTextCursor.KeepAnchor)
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
            if key == Qt.Key_Backspace:
                cursor = self.focus_edit.textCursor()
                at_start = cursor.position() == 0 and not cursor.hasSelection()
                if at_start and self._active_focus_idx > 0:
                    self._move_focus_line(-1)
                    jump_cursor = self.focus_edit.textCursor()
                    jump_cursor.movePosition(QTextCursor.End)
                    self.focus_edit.setTextCursor(jump_cursor)
                    self.focus_edit.setFocus()
                    return True
            if key in (Qt.Key_Return, Qt.Key_Enter):
                return False
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
                click_cursor.select(QTextCursor.WordUnderCursor)
                selected_word = click_cursor.selectedText().strip()
                click_rect = preview_widget.cursorRect(click_cursor)
                self._overlay_top_hint = click_rect.bottom() + 1
                self._apply_focus_text_from_source()
                focus_widget.setFocus()
                self._select_word_in_focus(selected_word)
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
                updated = self.metadata.update_field(self.source_edit.toPlainText(), "background_color", color_hex)
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
        self.source_edit.setStyleSheet(f"QPlainTextEdit {{ background-color: {color_hex}; padding: 12px; }}")
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
        if self.focus_edit.isVisible() and (self.focus_edit.hasFocus() or self.focus_edit.textCursor().hasSelection()):
            cursor = self.focus_edit.textCursor()
            if not cursor.hasSelection():
                return
            selected = cursor.selectedText().replace("\u2029", "\n")
            wrapped = f"<span style=\"{css_style}\">{selected}</span>"
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(wrapped)
            cursor.endEditBlock()
            self.focus_edit.setTextCursor(cursor)
            return
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
