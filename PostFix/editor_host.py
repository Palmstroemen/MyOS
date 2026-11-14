"""The one editor of a PostFix: CodeMirror with a live preview like Obsidian's (PostFix/codemirror)
in a QtWebEngine page, moved into the note being edited. A page costs about 300 MB; one page for
all notes of a PostFix keeps that once. Every note keeps its own text, cursor, selection and undo
history in it; the other notes show their light rendering meanwhile.

The note's window gives the editor its body (front matter stays with PostFix) and gets each
change back through `changed`; links come back through `linkClicked`.
"""

import atexit
import json
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QEvent, QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView
import shiboken6

BUNDLE = Path(__file__).resolve().parent / "codemirror" / "dist" / "editor.bundle.js"

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
:root { --fg: #1f2330; --muted: #6b7083; --accent: #5b4fd6; --quote: #d5d8e2; --code-bg: rgba(0,0,0,0.05);
        --bg: #ffffff; --body: "Inter", "Segoe UI", system-ui, sans-serif; --mono: "JetBrains Mono", monospace; }
html, body { margin: 0; height: 100%; background: var(--bg); }
#editor { height: 100%; }
/* The scroll bar of PostFix's rendering (smart_editor.py), as wide: both lay out alike. */
::-webkit-scrollbar { width: 11px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.047); border-radius: 5px; margin: 2px 0;
  border-right: 2px solid transparent; background-clip: padding-box; }
::-webkit-scrollbar-thumb { background: rgba(40,40,40,0.43); border-radius: 5px; min-height: 22px;
  border-right: 2px solid transparent; background-clip: padding-box; }
::-webkit-scrollbar-thumb:hover { background-color: rgba(40,40,40,0.57); }
</style>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>__BUNDLE__</script>
</head><body><div id="editor"></div>
<script>
new QWebChannel(qt.webChannelTransport, (channel) => {
  const bridge = channel.objects.bridge;
  window.host = PostFixEditor.createHost(document.getElementById("editor"), {
    onChange: (note, text) => bridge.changed(note, text),
    onLink: (note, href) => bridge.link(note, href),
    onScroll: (note, line, offset) => bridge.scrolled(note, line, offset),
  });
  bridge.ready();
});
</script></body></html>"""


class _Bridge(QObject):
    def __init__(self, host):
        super().__init__()
        self._host = host

    @Slot(str, str)
    def changed(self, note: str, text: str):
        self._host.changed.emit(note, text)

    @Slot(str, str)
    def link(self, note: str, href: str):
        self._host.linkClicked.emit(note, href)

    @Slot(str, int, float)
    def scrolled(self, note: str, line: int, offset: float):
        self._host._tops[note] = (line, offset)

    @Slot()
    def ready(self):
        self._host._on_ready()


class EditorHost(QObject):
    """One editor page for all notes; attach() moves it into the note being edited."""

    changed = Signal(str, str)      # note, its body as typed
    linkClicked = Signal(str, str)  # note, the link's target as written

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ready = False
        self._pending = []
        self._owner = None
        self._watched = set()
        self._tops: dict = {}  # note -> (first line in view, its offset), as the page reports
        self._on_leave: Optional[Callable[[], None]] = None
        self.view = QWebEngineView()
        self.view.hide()
        self._bridge = _Bridge(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self.view.page().setWebChannel(self._channel)
        bundle = BUNDLE.read_text(encoding="utf-8").replace("</script", "<\\/script")
        self.view.setHtml(PAGE.replace("__BUNDLE__", bundle), QUrl.fromLocalFile(str(BUNDLE.parent) + "/"))
        # The fonts the light rendering uses too (light_view.fonts), so both look the same.
        from . import light_view
        body, mono = light_view.fonts()
        self._run(f"document.documentElement.style.setProperty('--body', {json.dumps(json.dumps(body))});"
                  f"document.documentElement.style.setProperty('--mono', {json.dumps(json.dumps(mono))})")

    # --- talking to the page ------------------------------------------------------------------

    def _on_ready(self):
        self.ready = True
        for code in self._pending:
            self.view.page().runJavaScript(code)
        self._pending = []

    def _run(self, code: str):
        if self.ready:
            self.view.page().runJavaScript(code)
        else:
            self._pending.append(code)

    # --- notes ----------------------------------------------------------------------------------

    def attach(self, widget, note: str, body: str, base_dir, on_leave: Optional[Callable[[], None]] = None,
               background: Optional[str] = None, place: Optional[dict] = None):
        """Show note's body in the editor, laid over widget (the note's rendering). place: where
        the rendering was - {line, offset} of its first line in view, {x, y} of a click (in
        widget's coordinates) for the cursor, text typed meanwhile."""
        if self._owner is not None and self._owner is not widget:
            self._let_go(self._owner)
            if self._on_leave is not None:
                self._on_leave()  # the note it leaves shows its rendering again
        if self._owner is not widget:
            # A note (or its window) deleted with the editor still in it would take the editor
            # along: it leaves when the deletion is due (a QWidget deletes its children before it
            # says destroyed - too late).
            self._watched = {widget, widget.window()}
            for watched in self._watched:
                watched.installEventFilter(self)
        self._owner = widget
        self._on_leave = on_leave
        self.view.setParent(widget)
        self.view.setGeometry(self._area(widget))
        self.view.show()
        self.view.raise_()
        base = QUrl.fromLocalFile(str(Path(base_dir).resolve()) + "/").toString()
        if background:
            self._run(f"document.documentElement.style.setProperty('--bg', {json.dumps(background)})")
        self._run(f"window.host.show({json.dumps(note)}, {json.dumps(body)}, {json.dumps(base)}, "
                  f"{json.dumps(place)}); window.host.focus()")
        self.view.setFocus()

    def owner(self):
        return self._owner

    @staticmethod
    def _area(widget):
        # The part of the note the editor covers: its rendering when the note says so.
        area = getattr(widget, "editor_area", None)
        return area() if callable(area) else widget.rect()

    def top_of(self, note: str):
        """(first line in view, its offset) of note in the editor, as last reported, or None."""
        return self._tops.get(note)

    def set_doc(self, note: str, body: str):
        """A change from outside (the file, a merge): into the note's state, not reported back."""
        self._run(f"window.host.setDoc({json.dumps(note)}, {json.dumps(body)})")

    def drop(self, note: str):
        self._tops.pop(note, None)
        self._run(f"window.host.drop({json.dumps(note)})")

    def release(self, widget):
        """widget goes away (its window closes): the editor leaves it first, so it lives on."""
        if self._owner is not widget:
            return
        self._let_go(widget)
        self.view.hide()
        self.view.setParent(None)
        self._owner = None
        self._on_leave = None

    def _let_go(self, widget):
        for watched in self._watched:
            watched.removeEventFilter(self)
        self._watched = set()

    def eventFilter(self, watched, event):
        if watched is self._owner and event.type() in (QEvent.Resize, QEvent.LayoutRequest):
            self.view.setGeometry(self._area(watched))
        elif event.type() == QEvent.DeferredDelete and watched in self._watched:
            self.release(self._owner)
        return False

    def shutdown(self):
        """Delete the page now: one still alive when Qt ends crashes the program on exit."""
        if self.view is None:
            return
        if self._owner is not None:
            self.release(self._owner)
        shiboken6.delete(self.view)
        self.view = None


_shared: Optional[EditorHost] = None


def shared() -> EditorHost:
    """The editor of this PostFix, made when the first note wants it."""
    global _shared
    if _shared is None:
        _shared = EditorHost()
        if not _retired:
            atexit.register(_shutdown_shared)
    return _shared


_retired: list = []


def _shutdown_shared():
    global _shared
    for host in [_shared] + _retired:
        if host is not None:
            host.shutdown()
    _shared = None
    _retired.clear()


def forget_shared():
    """Tests: start over as a PostFix that has not edited yet. The page is put aside, deleted
    on exit: pages deleted one after another while Qt runs crash QtWebEngine (measured)."""
    global _shared
    if _shared is not None:
        if _shared.owner() is not None:
            _shared.release(_shared.owner())
        _retired.append(_shared)
        _shared = None
        if len(_retired) == 1:
            atexit.register(_shutdown_shared)
