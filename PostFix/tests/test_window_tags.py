from pathlib import Path

import pytest

from PostFix import window_tags as wt


class _DummyTimer:
    def __init__(self):
        self.started_with = None

    def start(self, ms: int):
        self.started_with = ms


class _DummySidebar:
    def __init__(self):
        self.tag_colors = None
        self.tags = None
        self.color_entries = None

    def set_tag_colors(self, colors):
        self.tag_colors = dict(colors)

    def set_tags(self, tags):
        self.tags = list(tags)

    def set_color_entries(self, entries):
        self.color_entries = list(entries)


class _DummyEditor:
    def __init__(self):
        self.current_path = None
        self.render_map = None
        self.replace_calls = []
        self.jump_calls = []

    def set_render_tag_colors(self, tag_map):
        self.render_map = dict(tag_map)

    def replace_color_definition(self, key, old_hex, new_hex):
        self.replace_calls.append((key, old_hex, new_hex))
        return True

    def jump_to_color_definition(self, key, hex_value):
        self.jump_calls.append((key, hex_value))


class _DummyWindow(wt.WindowTagsMixin):
    def __init__(self):
        self._doc_tags = []
        self._doc_color_defs = []
        self._scope_tags = []
        self._scope_tags_path = None
        self._tag_color_map = {}
        self._vault_root = None
        self._app_json_path = None
        self._app_json_data = {}
        self._scope_sync_timer = _DummyTimer()
        self.right_sidebar = _DummySidebar()
        self.editor = _DummyEditor()
        self.refreshed = 0
        self.saved = 0
        self.reloaded = 0

    def _refresh_tag_ui(self):
        self.refreshed += 1
        super()._refresh_tag_ui()

    def _save_tag_registry(self):
        self.saved += 1
        return True

    def _reload_tag_context(self):
        self.reloaded += 1

    def _save_current_document(self):
        self.saved += 1
        return True


def test_on_editor_tags_changed_normalizes_and_debounces():
    w = _DummyWindow()
    w._on_editor_tags_changed([" urgent ", "todo", "todo", "", "important"])
    assert w._doc_tags == ["important", "todo", "urgent"]
    assert w._scope_sync_timer.started_with == 1200
    assert w.refreshed == 1


def test_sync_scope_tags_from_document_writes_and_propagates(tmp_path: Path):
    w = _DummyWindow()
    w._scope_tags_path = tmp_path / ".MyOS" / "Tags.md"
    w._scope_tags = ["important"]
    w._doc_tags = ["important", "todo"]
    called = {"write": None, "propagate": 0}

    def _write(path, tags):
        called["write"] = (path, list(tags))
        return True

    def _propagate():
        called["propagate"] += 1

    w._write_scope_tags = _write
    w._propagate_scope_tags_update = _propagate
    w._sync_scope_tags_from_document()

    assert called["write"] is not None
    assert called["write"][0] == w._scope_tags_path
    assert called["write"][1] == ["important", "todo"]
    assert w._scope_tags == ["important", "todo"]
    assert called["propagate"] == 1


def test_refresh_tag_ui_updates_sidebar_and_editor_map():
    w = _DummyWindow()
    w._doc_tags = ["important", "todo"]
    w._doc_color_defs = [{"key": "color", "hex": "#123456"}]
    w._tag_color_map = {"important": "#ff0000", "other": "#00ff00"}

    wt.WindowTagsMixin._refresh_tag_ui(w)

    assert w.right_sidebar.tag_colors == {"important": "#ff0000"}
    assert w.right_sidebar.tags == ["important", "todo"]
    assert w.right_sidebar.color_entries == [{"key": "color", "hex": "#123456"}]
    assert w.editor.render_map == {"important": "#ff0000", "other": "#00ff00"}


def test_on_tag_color_change_reloads_when_vault_missing_and_saves():
    w = _DummyWindow()
    w._vault_root = None
    w._tag_color_map = {"important": "#ff0000"}
    w._app_json_data = {"colored-tags-wrangler": {"tags": []}}

    def _assign(tag, color):
        return True

    def _flatten():
        return {"important": "#ffaa00"}

    w._assign_tag_color_in_registry = _assign
    w._flatten_tag_colors = _flatten

    w._on_tag_color_change("important", "#ffaa00")

    assert w.reloaded == 1
    assert w.saved == 1
    assert w._tag_color_map == {"important": "#ffaa00"}
    assert w.refreshed >= 1


def test_propagate_scope_tags_update_calls_notify(monkeypatch, tmp_path: Path):
    calls = []

    def fake_notify(path, dry_run=False):
        calls.append((path, dry_run))

    monkeypatch.setattr(wt, "notify_config_changed", fake_notify)
    w = _DummyWindow()
    w._scope_tags_path = tmp_path / ".MyOS" / "Tags.md"

    wt.WindowTagsMixin._propagate_scope_tags_update(w)
    assert calls == [(w._scope_tags_path, False)]


def test_reload_tag_context_discovers_scope_and_sets_registry_path(tmp_path: Path):
    vault = tmp_path / "vault"
    project = vault / "Projects" / "Demo"
    myos = project / ".MyOS"
    obsidian = vault / ".obsidian"
    myos.mkdir(parents=True, exist_ok=True)
    obsidian.mkdir(parents=True, exist_ok=True)
    (myos / "Tags.md").write_text("# Tags\n#important\n", encoding="utf-8")
    (obsidian / "app.json").write_text("{}", encoding="utf-8")
    note = project / "note.md"
    note.write_text("# demo\n", encoding="utf-8")

    class _RealReloadWindow(_DummyWindow):
        def _load_tag_registry(self):
            self._app_json_data = {}
            return self._app_json_data

        def _sync_scope_tags_from_document(self):
            return

        def _flatten_tag_colors(self):
            return {}

    w = _RealReloadWindow()
    w.editor.current_path = note

    wt.WindowTagsMixin._reload_tag_context(w)

    assert w._vault_root == vault
    assert w._app_json_path == obsidian / "app.json"
    assert w._scope_tags_path == myos / "Tags.md"
    assert w._scope_tags == ["important"]
