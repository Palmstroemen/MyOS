from pathlib import Path

from PostFix.main import PostFixWindow


class _DummyEditor:
    def __init__(self, path: Path, content: str):
        self.current_path = path
        self._content = content

    def get_markdown(self) -> str:
        return self._content


class _DummyWindow:
    _save_current_document = PostFixWindow._save_current_document
    _on_editor_text_changed = PostFixWindow._on_editor_text_changed
    _set_clean_document_state = PostFixWindow._set_clean_document_state

    def __init__(self, path: Path, content: str):
        self.editor = _DummyEditor(path, content)
        self._track_local_changes = True
        self._has_local_changes = False
        self._scope_sync_calls = 0
        self._schedule_calls = 0

    def _sync_scope_tags_from_document(self):
        self._scope_sync_calls += 1

    def _schedule_save(self):
        self._schedule_calls += 1


def test_save_skips_when_no_local_changes(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("original", encoding="utf-8")
    w = _DummyWindow(note, "updated")

    ok = w._save_current_document()

    assert ok is False
    assert note.read_text(encoding="utf-8") == "original"
    assert w._scope_sync_calls == 0


def test_save_writes_when_local_changes_present_and_cleans_state(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("original", encoding="utf-8")
    w = _DummyWindow(note, "updated")
    w._has_local_changes = True

    ok = w._save_current_document()

    assert ok is True
    assert note.read_text(encoding="utf-8") == "updated"
    assert w._scope_sync_calls == 1
    assert w._has_local_changes is False


def test_on_editor_text_changed_sets_dirty_and_schedules():
    w = _DummyWindow(Path("/tmp/note.md"), "x")

    w._on_editor_text_changed()

    assert w._has_local_changes is True
    assert w._schedule_calls == 1
