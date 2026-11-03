"""The one editor of a PostFix (PostFix/editor_host.py): CodeMirror in QtWebEngine, moved into
the note being edited; every note keeps its own text, cursor and undo history in it. Runs a real
browser page without a screen."""

import os
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication, QWidget

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def host(app):
    from PostFix.editor_host import EditorHost

    editor = EditorHost()
    assert _wait(app, lambda: editor.ready, 20), "the editor page did not load"
    yield editor
    editor.shutdown()


def _wait(app, condition, seconds=5):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    return False


def _js(app, host, code):
    result = {}
    host.view.page().runJavaScript(code, 0, lambda value: result.update(value=value))
    _wait(app, lambda: "value" in result)
    return result.get("value")


def _type(app, host, text):
    # As a keystroke would: an input transaction at the cursor.
    _js(app, host, f"(h => h.view.dispatch(h.view.state.replaceSelection({text!r}), {{userEvent: 'input'}}))(window.host)")
    _wait(app, lambda: False, 0.1)


def test_typed_text_reaches_python_with_its_note(app, host, tmp_path):
    changes = []
    host.changed.connect(lambda note, text: changes.append((note, text)))
    a = QWidget()
    host.attach(a, "a.md", "Hallo", tmp_path)
    _wait(app, lambda: False, 0.2)
    _type(app, host, "X")
    assert _wait(app, lambda: changes)
    assert changes[-1] == ("a.md", "XHallo")


def test_each_note_keeps_its_own_undo(app, host, tmp_path):
    a, b = QWidget(), QWidget()
    host.attach(a, "a.md", "Erste", tmp_path)
    _wait(app, lambda: False, 0.2)
    _type(app, host, "A")
    host.attach(b, "b.md", "Zweite", tmp_path)
    _wait(app, lambda: False, 0.2)
    _type(app, host, "B")
    host.attach(a, "a.md", "AErste", tmp_path)
    _wait(app, lambda: False, 0.2)
    _js(app, host, "MyOSEditor.undoOnce(window.host)")
    assert _js(app, host, "window.host.getDoc('a.md')") == "Erste"
    assert _js(app, host, "window.host.getDoc('b.md')") == "BZweite"  # untouched by a's undo


def test_a_change_from_outside_is_not_reported_back_as_typing(app, host, tmp_path):
    changes = []
    host.changed.connect(lambda note, text: changes.append(note))
    host.attach(QWidget(), "a.md", "Alt", tmp_path)
    _wait(app, lambda: False, 0.2)
    host.set_doc("a.md", "Neu von außen")
    _wait(app, lambda: False, 0.3)
    assert _js(app, host, "window.host.getDoc('a.md')") == "Neu von außen" and changes == []


def test_the_editor_moves_between_notes_and_outlives_a_closed_one(app, host, tmp_path):
    a, b = QWidget(), QWidget()
    left = []
    host.attach(a, "a.md", "A", tmp_path, on_leave=lambda: left.append("a"))
    assert host.view.parent() is a
    host.attach(b, "b.md", "B", tmp_path)
    assert host.view.parent() is b and left == ["a"]
    host.release(b)  # the note's window closes
    b.deleteLater()
    _wait(app, lambda: False, 0.3)
    assert host.view.parent() is None and _js(app, host, "1 + 1") == 2  # the editor lives on


def test_a_link_reports_its_note(app, host, tmp_path):
    links = []
    host.linkClicked.connect(lambda note, href: links.append((note, href)))
    host.attach(QWidget(), "a.md", "Text\n\n[weiter](<../Lektion02/Markdown-Dateien.md>)", tmp_path)  # cursor away from it
    _wait(app, lambda: False, 0.3)
    _js(app, host, "window.host.view.contentDOM.querySelector('.cm-md-link')"
                   ".dispatchEvent(new MouseEvent('mousedown', {bubbles: true}))")
    assert _wait(app, lambda: links)
    assert links == [("a.md", "../Lektion02/Markdown-Dateien.md")]


def test_a_note_deleted_with_the_editor_in_it_does_not_take_the_editor_along(app, host, tmp_path):
    note = QWidget()
    host.attach(note, "a.md", "A", tmp_path)
    note.deleteLater()  # gone without closing first
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)  # processEvents() leaves deletions
    assert host.owner() is None and host.view.parent() is None
    assert _js(app, host, "window.host.getDoc('a.md')") == "A"  # the editor and its states live on
