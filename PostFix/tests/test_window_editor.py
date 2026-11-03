"""PostFix windows with the one editor (MYOS_POSTFIX_EDITOR=codemirror): the note being edited
gets the CodeMirror editor, the others keep their rendering; what is typed is saved as before
(front matter kept, changes from outside merged), links open notes in the same window."""

import os
import time
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

NOTE = "---\nbackground_color: '#fff8b0'\n---\n# Lektion\n\nErster Absatz.\n\n[weiter](<Zweite.md>)\n"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv("MYOS_POSTFIX_EDITOR", "codemirror")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    app = QApplication.instance() or QApplication([])
    from PostFix import editor_host
    from PostFix.main import PostFixWindow

    first = tmp_path / "Erste.md"
    first.write_text(NOTE, encoding="utf-8")
    (tmp_path / "Zweite.md").write_text("# Zweite\n\nDer zweite Text.\n", encoding="utf-8")
    windows = []

    def window(path):
        w = PostFixWindow(open_path=path, ui_language="en")
        w.show()
        windows.append(w)
        return w

    yield app, window, tmp_path, editor_host
    for w in windows:
        w.close()
    _wait(app, lambda: False, 0.2)


def _wait(app, condition, seconds=8):
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


def _ready(app, host):
    assert _wait(app, lambda: host.ready, 20)
    _wait(app, lambda: False, 0.3)


def test_typing_in_the_editor_is_saved_with_the_front_matter(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    assert host.owner() is w.editor
    _js(app, host, "(h => h.view.dispatch({changes: {from: h.view.state.doc.length, insert: 'Neu getippt.\\n'},"
                   " userEvent: 'input'}))(window.host)")
    assert _wait(app, lambda: "Neu getippt." in (folder / "Erste.md").read_text(encoding="utf-8"))
    saved = (folder / "Erste.md").read_text(encoding="utf-8")
    assert saved.startswith("---\n") and "background_color" in saved and "Erster Absatz." in saved


def test_a_change_from_outside_shows_in_the_editor(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    (folder / "Erste.md").write_text(NOTE.replace("Erster Absatz.", "Von außen."), encoding="utf-8")
    assert _wait(app, lambda: "Von außen." in (_js(app, host, f"window.host.getDoc({str((folder / 'Erste.md').resolve())!r})") or ""))


def test_the_editor_moves_to_the_note_being_edited(setup):
    app, window, folder, editor_host = setup
    first, second = window(folder / "Erste.md"), window(folder / "Zweite.md")
    host = editor_host.shared()
    first._take_editor()
    _ready(app, host)
    first._take_editor()  # checked right away: activation events must not move it in between
    assert host.owner() is first.editor and first.editor.preview_suspended()
    second._take_editor()
    assert host.owner() is second.editor
    assert not first.editor.preview_suspended()  # the first shows its rendering again
    assert second.editor.preview_suspended()


def test_a_link_opens_the_note_in_the_same_window(setup):
    app, window, folder, editor_host = setup
    w = window(folder / "Erste.md")
    w._take_editor()
    host = editor_host.shared()
    _ready(app, host)
    w.follow_link("Zweite.md")
    _wait(app, lambda: False, 0.3)
    assert Path(w.editor.current_path) == (folder / "Zweite.md")
    assert "Der zweite Text." in w.editor.get_markdown()
    assert _wait(app, lambda: "Der zweite Text." in (_js(app, host, f"window.host.getDoc({str((folder / 'Zweite.md').resolve())!r})") or ""))


def test_without_the_switch_postfix_stays_as_it_was(setup, monkeypatch):
    app, window, folder, editor_host = setup
    monkeypatch.delenv("MYOS_POSTFIX_EDITOR")
    w = window(folder / "Erste.md")
    w._take_editor()
    assert not w.editor.preview_suspended()
