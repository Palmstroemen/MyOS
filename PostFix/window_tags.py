"""Tag/context-related behavior for PostFixWindow."""

from pathlib import Path

try:
    from core.project import notify_config_changed
except Exception:
    notify_config_changed = None

try:
    from .tag_registry import (
        find_vault_root,
        parse_scope_tags,
        write_scope_tags,
        load_tag_registry,
        save_tag_registry,
        flatten_tag_colors,
        assign_tag_color_in_registry,
    )
except ImportError:
    from tag_registry import (
        find_vault_root,
        parse_scope_tags,
        write_scope_tags,
        load_tag_registry,
        save_tag_registry,
        flatten_tag_colors,
        assign_tag_color_in_registry,
    )


class WindowTagsMixin:
    def _on_editor_tags_changed(self, tags: list[str]):
        ordered: list[str] = []
        seen: set[str] = set()
        for raw in tags or []:
            tag = str(raw).strip()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            ordered.append(tag)
        self._doc_tags = ordered
        # Debounce scope-tag updates to avoid transient tags while typing/deleting.
        self._scope_sync_timer.start(1200)
        self._refresh_tag_ui()

    def _on_editor_color_definitions_changed(self, items: list):
        normalized = []
        for item in items or []:
            if isinstance(item, dict):
                key = str(item.get("key", "")).strip()
                value = str(item.get("hex", "")).strip()
                if key and value:
                    normalized.append({"key": key, "hex": value})
        self._doc_color_defs = normalized
        self._refresh_tag_ui()

    def _find_vault_root(self, file_path: Path | None) -> Path | None:
        return find_vault_root(file_path)

    def _parse_scope_tags(self, tags_md_path: Path) -> list[str]:
        return parse_scope_tags(tags_md_path)

    def _write_scope_tags(self, tags_md_path: Path, tags: list[str]) -> bool:
        return write_scope_tags(tags_md_path, tags)

    def _load_tag_registry(self) -> dict:
        self._app_json_data = load_tag_registry(self._app_json_path)
        return self._app_json_data

    def _save_tag_registry(self) -> bool:
        return save_tag_registry(self._app_json_path, self._app_json_data)

    def _flatten_tag_colors(self) -> dict[str, str]:
        return flatten_tag_colors(self._app_json_data)

    def _assign_tag_color_in_registry(self, tag: str, color_hex: str) -> bool:
        return assign_tag_color_in_registry(self._app_json_data, tag, color_hex)

    def _reload_tag_context(self):
        file_path = getattr(self.editor, "current_path", None)
        self._vault_root = self._find_vault_root(file_path)
        if self._vault_root:
            root_app = self._vault_root / "app.json"
            obs_app = self._vault_root / ".obsidian" / "app.json"
            if root_app.exists():
                self._app_json_path = root_app
            elif obs_app.exists():
                self._app_json_path = obs_app
            else:
                self._app_json_path = root_app
        else:
            self._app_json_path = None
        self._load_tag_registry()

        self._scope_tags = []
        self._scope_tags_path = None
        if file_path:
            current_dir = file_path.parent
            nearest_myos_dir = None
            for parent in [current_dir, *current_dir.parents]:
                myos_dir = parent / ".MyOS"
                if nearest_myos_dir is None and myos_dir.exists():
                    nearest_myos_dir = myos_dir
                tags_md = myos_dir / "Tags.md"
                if tags_md.exists():
                    self._scope_tags_path = tags_md
                    self._scope_tags = self._parse_scope_tags(tags_md)
                    break
            if self._scope_tags_path is None and nearest_myos_dir is not None:
                # No explicit project tag config yet; keep a writable target.
                self._scope_tags_path = nearest_myos_dir / "Tags.md"

        self._sync_scope_tags_from_document()

        self._tag_color_map = self._flatten_tag_colors()
        self._refresh_tag_ui()

    def _sync_scope_tags_from_document(self):
        if not self._scope_tags_path:
            return
        scope_set = {t for t in self._scope_tags}
        missing = [t for t in self._doc_tags if t not in scope_set]
        if not missing:
            return
        merged = self._scope_tags + missing
        if self._write_scope_tags(self._scope_tags_path, merged):
            self._scope_tags = merged
            self._propagate_scope_tags_update()

    def _propagate_scope_tags_update(self):
        if notify_config_changed is None or not self._scope_tags_path:
            return
        try:
            notify_config_changed(self._scope_tags_path, dry_run=False)
        except Exception:
            pass

    def _refresh_tag_ui(self):
        visible_tags = list(self._doc_tags)

        sidebar_colors = {t: self._tag_color_map[t] for t in visible_tags if t in self._tag_color_map}
        self.right_sidebar.set_tag_colors(sidebar_colors)
        self.right_sidebar.set_tags(visible_tags)
        self.right_sidebar.set_color_entries(self._doc_color_defs)
        if hasattr(self.editor, "set_render_tag_colors"):
            self.editor.set_render_tag_colors(self._tag_color_map)

    def _on_tag_color_change(self, tag: str, color_hex: str):
        if not tag or not color_hex:
            return
        if not self._vault_root:
            self._reload_tag_context()
        changed = self._assign_tag_color_in_registry(tag, color_hex)
        if not changed:
            return
        self._save_tag_registry()
        self._tag_color_map = self._flatten_tag_colors()
        self._refresh_tag_ui()

    def _on_color_definition_change(self, key: str, old_hex: str, new_hex: str):
        if not hasattr(self, "editor"):
            return
        changed = self.editor.replace_color_definition(key, old_hex, new_hex)
        if changed:
            self._save_current_document()

    def _on_color_definition_search(self, key: str, hex_value: str):
        if not hasattr(self, "editor"):
            return
        self.editor.jump_to_color_definition(key, hex_value)

    def _on_tag_search(self, tag: str):
        if not hasattr(self, "editor") or not tag:
            return
        self.editor.jump_to_tag(tag)
