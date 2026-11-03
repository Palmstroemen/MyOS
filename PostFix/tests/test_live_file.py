"""A note open in PostFix and changed from outside (another program, Scope, a sync, a tester's
reset): PostFix shows the change at once and never writes its older copy over it
(PostFix/live_file.py, PostFixWindow._reconcile_with_disk)."""

from pathlib import Path

from PostFix.live_file import conflict_copy_path, merge3
from PostFix.main import PostFixWindow

BASE = "---\nwindow_x_permille: 78\n---\n# Lektion\n\nErster Absatz.\n\nZweiter Absatz.\n"


def test_changes_at_different_places_are_both_kept():
    mine = BASE.replace("window_x_permille: 78", "window_x_permille: 300")  # the window moved
    theirs = BASE.replace("Zweiter Absatz.", "Zweiter Absatz, von außen ergänzt.")
    merged, conflict = merge3(BASE, mine, theirs)
    assert not conflict
    assert "window_x_permille: 300" in merged and "von außen ergänzt" in merged


def test_the_same_change_on_both_sides_is_no_conflict():
    both = BASE.replace("Erster Absatz.", "Erster Absatz!")
    assert merge3(BASE, both, both) == (both, False)


def test_one_side_unchanged_takes_the_other():
    theirs = BASE + "\nNeu von außen.\n"
    assert merge3(BASE, BASE, theirs) == (theirs, False)
    assert merge3(BASE, theirs, BASE) == (theirs, False)


def test_the_same_place_changed_differently_is_a_conflict():
    mine = BASE.replace("Erster Absatz.", "Mein erster Absatz.")
    theirs = BASE.replace("Erster Absatz.", "Ihr erster Absatz.")
    _merged, conflict = merge3(BASE, mine, theirs)
    assert conflict


def test_insertions_at_the_same_place_conflict_unless_equal():
    mine = BASE.replace("# Lektion\n", "# Lektion\nMeine Zeile\n")
    theirs = BASE.replace("# Lektion\n", "# Lektion\nIhre Zeile\n")
    assert merge3(BASE, mine, theirs)[1]
    assert merge3(BASE, mine, mine) == (mine, False)


def test_the_conflict_copy_does_not_overwrite_another(tmp_path):
    note = tmp_path / "Virtuelle Ordner.md"
    first = conflict_copy_path(note)
    assert first == tmp_path / "Virtuelle Ordner (Konflikt).md"
    first.write_text("x", encoding="utf-8")
    assert conflict_copy_path(note) == tmp_path / "Virtuelle Ordner (Konflikt 2).md"


class _Editor:
    def __init__(self, path: Path, text: str):
        self.current_path = path
        self.text = text
        self.loads = 0

    def get_markdown(self) -> str:
        return self.text

    def load_markdown(self, text: str):
        self.text = text
        self.loads += 1


class _Window:
    _save_current_document = PostFixWindow._save_current_document
    _reconcile_with_disk = PostFixWindow._reconcile_with_disk
    _load_from_disk = PostFixWindow._load_from_disk
    _set_clean_document_state = PostFixWindow._set_clean_document_state

    def __init__(self, path: Path):
        text = path.read_text(encoding="utf-8")
        self.editor = _Editor(path, text)
        self._disk_text = text
        self._track_local_changes = True
        self._has_local_changes = False
        self.notices = []

    def _sync_scope_tags_from_document(self):
        pass

    def _after_reload(self):
        pass

    def _notify(self, text):
        self.notices.append(text)

    def tr(self, text):
        return text


def _note(tmp_path, text=BASE):
    note = tmp_path / "Virtuelle Ordner.md"
    note.write_text(text, encoding="utf-8")
    return note


def test_a_change_from_outside_shows_at_once(tmp_path):
    note = _note(tmp_path)
    w = _Window(note)
    outside = BASE.replace("Erster Absatz.", "Erster Absatz, neu von außen.")
    note.write_text(outside, encoding="utf-8")
    assert w._reconcile_with_disk()
    assert w.editor.text == outside and not w._has_local_changes
    assert note.read_text(encoding="utf-8") == outside


def test_closing_after_moving_the_window_keeps_the_change_from_outside(tmp_path):
    # Lesson 7, 2026-10-26: PostFix wrote its older copy back on closing.
    note = _note(tmp_path)
    w = _Window(note)
    w.editor.text = BASE.replace("window_x_permille: 78", "window_x_permille: 300")
    w._has_local_changes = True
    note.write_text(BASE + "\n[💬 Kommentar](<myos:comment>)\n", encoding="utf-8")
    assert w._save_current_document()
    saved = note.read_text(encoding="utf-8")
    assert "myos:comment" in saved and "window_x_permille: 300" in saved


def test_a_real_conflict_loses_nothing(tmp_path):
    note = _note(tmp_path)
    w = _Window(note)
    w.editor.text = BASE.replace("Erster Absatz.", "Mein erster Absatz.")
    w._has_local_changes = True
    note.write_text(BASE.replace("Erster Absatz.", "Ihr erster Absatz."), encoding="utf-8")
    w._save_current_document()
    assert "Ihr erster Absatz." in note.read_text(encoding="utf-8")  # the file keeps theirs
    copy = tmp_path / "Virtuelle Ordner (Konflikt).md"
    assert "Mein erster Absatz." in copy.read_text(encoding="utf-8")  # mine lies beside it
    assert w.editor.text == note.read_text(encoding="utf-8") and w.notices


def test_our_own_save_is_no_change_from_outside(tmp_path):
    note = _note(tmp_path)
    w = _Window(note)
    w.editor.text = BASE + "\nNeu.\n"
    w._has_local_changes = True
    assert w._save_current_document()
    loads = w.editor.loads
    assert not w._reconcile_with_disk() and w.editor.loads == loads


def test_a_deleted_note_is_not_written_back(tmp_path):
    note = _note(tmp_path)
    w = _Window(note)
    note.unlink()
    assert not w._reconcile_with_disk()
    w.editor.text = BASE + "x"
    w._has_local_changes = True
    w._save_current_document()
    assert not note.exists()  # deleted elsewhere (e.g. a tester's reset): stays gone


def test_a_real_window_follows_changes_from_outside_live(tmp_path, monkeypatch):
    # The watch itself: written, replaced (as many editors save), and written again.
    import os
    import time

    from PySide6.QtWidgets import QApplication

    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("QT_QPA_PLATFORM", os.environ.get("QT_QPA_PLATFORM", "offscreen"))
    app = QApplication.instance() or QApplication([])
    note = tmp_path / "Probe.md"
    note.write_text("# Probe\n\nErster Absatz.\n", encoding="utf-8")
    window = PostFixWindow(open_path=note, ui_language="en")  # no translator left for other tests

    def settle(seconds=0.6):
        end = time.time() + seconds
        while time.time() < end:
            app.processEvents()
            time.sleep(0.02)

    try:
        settle(0.3)
        note.write_text("# Probe\n\nVon außen geändert.\n", encoding="utf-8")
        settle()
        assert "Von außen geändert." in window.editor.get_markdown()
        replacement = note.with_suffix(".tmp")
        replacement.write_text("# Probe\n\nErsetzt.\n", encoding="utf-8")
        os.replace(replacement, note)
        settle()
        assert "Ersetzt." in window.editor.get_markdown()
        note.write_text("# Probe\n\nNoch einmal.\n", encoding="utf-8")
        settle()
        assert "Noch einmal." in window.editor.get_markdown()
    finally:
        window.set_language("en")
        window.close()
        settle(0.2)
    assert note.read_text(encoding="utf-8").endswith("Noch einmal.\n")
