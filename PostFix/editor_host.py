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
</style>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>__BUNDLE__</script>
</head><body><div id="editor"></div>
<script>
new QWebChannel(qt.webChannelTransport, (channel) => {
  const bridge = channel.objects.bridge;
  window.host = MyOSEditor.createHost(document.getElementById("editor"), {
    onChange: (note, text) => bridge.changed(note, text),
    onLink: (note, href) => bridge.link(note, href),
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
        self._on_leave: Optional[Callable[[], None]] = None
        self.view = QWebEngineView()
        self.view.hide()
        self._bridge = _Bridge(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self.view.page().setWebChannel(self._channel)
        bundle = BUNDLE.read_text(encoding="utf-8").replace("</script", "<\\/script")
        self.view.setHtml(PAGE.replace("__BUNDLE__", bundle), QUrl.fromLocalFile(str(BUNDLE.parent) + "/"))

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
               background: Optional[str] = None):
        """Show note's body in the editor, laid over widget (the note's rendering)."""
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
        self.view.setGeometry(widget.rect())
        self.view.show()
        self.view.raise_()
        base = QUrl.fromLocalFile(str(Path(base_dir).resolve()) + "/").toString()
        if background:
            self._run(f"document.documentElement.style.setProperty('--bg', {json.dumps(background)})")
        self._run(f"window.host.show({json.dumps(note)}, {json.dumps(body)}, {json.dumps(base)}); window.host.focus()")
        self.view.setFocus()

    def owner(self):
        return self._owner

    def set_doc(self, note: str, body: str):
        """A change from outside (the file, a merge): into the note's state, not reported back."""
        self._run(f"window.host.setDoc({json.dumps(note)}, {json.dumps(body)})")

    def drop(self, note: str):
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
        if watched is self._owner and event.type() == QEvent.Resize:
            self.view.setGeometry(watched.rect())
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
        atexit.register(_shutdown_shared)
    return _shared


def _shutdown_shared():
    global _shared
    if _shared is not None:
        _shared.shutdown()
        _shared = None
