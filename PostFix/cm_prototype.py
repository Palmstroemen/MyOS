#!/usr/bin/env python3
"""
Prototype, not yet PostFix: a note in the new editor (CodeMirror 6 with a live preview like
Obsidian's, PostFix/codemirror) to compare it with Obsidian side by side.

    python3 PostFix/cm_prototype.py ["Learning MyOS/DE/Lektion01/Beginne HIER.md"] [--in-place]

Without --in-place it works on a copy of the note's folder in a temporary folder, so trying
it out changes nothing in the repository. It saves as you type, shows changes from outside at
once, opens .md links in the same window and prints start time and memory to the terminal.
"""

import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QFileSystemWatcher, QObject, QTimer, QUrl, Slot  # noqa: E402
from PySide6.QtGui import QDesktopServices  # noqa: E402
from PySide6.QtWebChannel import QWebChannel  # noqa: E402
from PySide6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from PySide6.QtWidgets import QApplication, QMainWindow  # noqa: E402

from PostFix.metadata import MetadataManager  # noqa: E402

BUNDLE = Path(__file__).resolve().parent / "codemirror" / "dist" / "editor.bundle.js"
STARTED = time.time()

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<style>
:root { --fg: #1f2330; --muted: #6b7083; --accent: #5b4fd6; --quote: #d5d8e2; --code-bg: #f1f2f6;
        --bg: #ffffff; --body: "Inter", "Segoe UI", system-ui, sans-serif; --mono: "JetBrains Mono", monospace; }
@media (prefers-color-scheme: dark) { :root { --fg: #e4e6ee; --muted: #9a9fb3; --accent: #a59cff;
        --quote: #3a3e50; --code-bg: #262936; --bg: #1c1e27; } }
html, body { margin: 0; height: 100%; background: var(--bg); }
#editor { height: 100%; }
</style>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
<script>__BUNDLE__</script>
</head><body><div id="editor"></div>
<script>
new QWebChannel(qt.webChannelTransport, (channel) => {
  const bridge = channel.objects.bridge;
  window.editor = MyOSEditor.create(document.getElementById("editor"), {
    doc: __DOC__,
    onChange: (text) => bridge.changed(text),
    onLink: (href) => bridge.link(href),
  });
  window.editor.focus();
  bridge.ready();
});
</script></body></html>"""


def rss_mb(pid: int) -> float:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    except OSError:
        pass
    return 0.0


def web_engine_mb() -> float:
    """Memory of the Chromium processes QtWebEngine started for this program."""
    import os

    total = 0.0
    for proc in Path("/proc").iterdir():
        if proc.name.isdigit():
            try:
                if (proc / "stat").read_text().split()[3] == str(os.getpid()) or \
                        "QtWebEngineProcess" in (proc / "cmdline").read_text(errors="replace") and \
                        str(os.getpid()) in (proc / "environ").read_text(errors="replace"):
                    total += rss_mb(int(proc.name))
            except OSError:
                continue
    return total


class Bridge(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    @Slot(str)
    def changed(self, body: str):
        self.window.body = body
        self.window.save_timer.start()

    @Slot(str)
    def link(self, href: str):
        self.window.follow(href)

    @Slot()
    def ready(self):
        import os

        print(f"[prototype] ready after {time.time() - STARTED:.2f} s; memory: this process "
              f"{rss_mb(os.getpid()):.0f} MB, browser processes {web_engine_mb():.0f} MB")


class Window(QMainWindow):
    def __init__(self, note: Path):
        super().__init__()
        self.meta_manager = MetadataManager()
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)
        self.resize(900, 760)
        self.bridge = Bridge(self)
        self.channel = QWebChannel(self)
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)
        self.save_timer = QTimer(self, singleShot=True, interval=300, timeout=self.save)
        self.watcher = QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(lambda _p: self.reload_timer.start())
        self.reload_timer = QTimer(self, singleShot=True, interval=150, timeout=self.reload_from_disk)
        self.open(note)

    def open(self, note: Path):
        self.note = note
        self.disk_text = note.read_text(encoding="utf-8")
        self.meta, self.body = self.meta_manager.split_frontmatter(self.disk_text)
        self.setWindowTitle(f"Prototyp – {note.name}")
        html = PAGE.replace("__BUNDLE__", BUNDLE.read_text(encoding="utf-8").replace("</script", "<\\/script")) \
                   .replace("__DOC__", json.dumps(self.body))
        self.view.setHtml(html, QUrl.fromLocalFile(str(note.parent) + "/"))
        if self.watcher.files():
            self.watcher.removePaths(self.watcher.files())
        self.watcher.addPath(str(note))

    def save(self):
        text = self.meta_manager.build_frontmatter(self.meta, self.body) if self.meta else self.body
        if text != self.disk_text:
            self.note.write_text(text, encoding="utf-8")
            self.disk_text = text

    def reload_from_disk(self):
        try:
            text = self.note.read_text(encoding="utf-8")
        except OSError:
            return
        if str(self.note) not in self.watcher.files():
            self.watcher.addPath(str(self.note))  # replaced by another program: watch the new file
        if text == self.disk_text:
            return
        self.disk_text = text
        self.meta, self.body = self.meta_manager.split_frontmatter(text)
        self.view.page().runJavaScript(f"window.editor && window.editor.setDoc({json.dumps(self.body)})")

    def follow(self, href: str):
        if href.startswith(("http://", "https://")):
            QDesktopServices.openUrl(QUrl(href))
            return
        target = (self.note.parent / QUrl.fromPercentEncoding(href.encode()).split("#")[0]).resolve()
        if target.suffix == ".md" and target.exists():
            self.save()
            self.open(target)
        else:
            print(f"[prototype] link not followed here: {href}")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    note = Path(args[0] if args else REPO_ROOT / "Learning MyOS" / "DE" / "Lektion01" / "Beginne HIER.md").resolve()
    if "--in-place" not in sys.argv:
        # A copy of the whole tutorial (links between lessons keep working), not the repository.
        root = note.parent
        while root.parent != root and root.name != "Learning MyOS":
            root = root.parent
        source = root if root.name == "Learning MyOS" else note.parent
        copy = Path(tempfile.mkdtemp(prefix="postfix-prototype-")) / source.name
        shutil.copytree(source, copy)
        note = copy / note.relative_to(source)
        print(f"[prototype] working on a copy: {note}")
    app = QApplication(sys.argv)
    window = Window(note)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
