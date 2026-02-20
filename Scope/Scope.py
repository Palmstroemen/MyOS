#!/usr/bin/env python3
from __future__ import annotations

import sys
import os
import hashlib
import mimetypes
import shutil
import subprocess
from pathlib import Path
from threading import Lock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import (
    QObject,
    Slot,
    QUrl,
    Signal,
    QThreadPool,
    QRunnable,
    QSize,
    Qt,
    QTranslator,
    QFileSystemWatcher,
    QTimer,
)
from PySide6.QtGui import QGuiApplication, QIcon, QImageReader, QImage, QCursor
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QMimeDatabase

from core.scope_api import ScopeApi


class ThumbnailTask(QRunnable):
    def __init__(self, owner: "Thumbnailer", file_path: Path, cache_path: Path, mime: str) -> None:
        super().__init__()
        self._owner = owner
        self._file_path = file_path
        self._cache_path = cache_path
        self._mime = mime

    def run(self) -> None:
        try:
            result = self._owner._generate_thumbnail(self._file_path, self._cache_path, self._mime)
            if result:
                self._owner.thumbnailReady.emit(str(self._file_path), result)
        finally:
            self._owner._mark_done(self._file_path, self._mime)


class Thumbnailer(QObject):
    thumbnailReady = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._pool = QThreadPool.globalInstance()
        self._lock = Lock()
        self._pending: set[str] = set()
        self._cache_root = Path("~/.cache/myos-scope/thumbnails").expanduser()
        self._freedesktop_cache = Path("~/.cache/thumbnails").expanduser()
        self._pdftoppm = shutil.which("pdftoppm")
        self._md_thumbnailer = Path(__file__).resolve().parents[1] / "core" / "bin" / "myos-md-thumbnailer"
        self._size_px = 256

    def request_thumbnail(self, file_path: Path) -> str:
        if not file_path.exists() or not file_path.is_file():
            return ""
        mime = self._guess_mime(file_path)
        if not self._is_thumbnail_candidate(file_path, mime):
            return ""

        cached = self._cached_thumbnail(file_path, mime)
        if cached:
            return cached

        key = self._cache_key(file_path, mime)
        with self._lock:
            if key in self._pending:
                return ""
            self._pending.add(key)

        cache_path = self._cache_path_for_key(key)
        task = ThumbnailTask(self, file_path, cache_path, mime)
        self._pool.start(task)
        return ""

    def _mark_done(self, file_path: Path, mime: str) -> None:
        key = self._cache_key(file_path, mime)
        with self._lock:
            self._pending.discard(key)

    def _guess_mime(self, file_path: Path) -> str:
        mime, _ = mimetypes.guess_type(file_path.name)
        return mime or ""

    def _is_thumbnail_candidate(self, file_path: Path, mime: str) -> bool:
        if mime.startswith("image/"):
            return True
        if mime == "application/pdf" or file_path.suffix.lower() == ".pdf":
            return True
        if mime in {"text/markdown", "text/x-markdown"}:
            return True
        if file_path.suffix.lower() in {".md", ".markdown"}:
            return True
        return False

    def _cache_key(self, file_path: Path, mime: str) -> str:
        try:
            stat = file_path.stat()
            stamp = f"{int(stat.st_mtime_ns)}|{stat.st_size}"
        except OSError:
            stamp = "0|0"
        payload = f"{file_path.resolve()}|{mime}|{self._size_px}|{stamp}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def _cache_path_for_key(self, key: str) -> Path:
        return self._cache_root / f"{key}.png"

    def _cached_thumbnail(self, file_path: Path, mime: str) -> str:
        key = self._cache_key(file_path, mime)
        cached = self._cache_path_for_key(key)
        if cached.exists():
            return cached.as_uri()

        # Markdown thumbnails are style-aware (MyOS specific), so using
        # generic desktop cache can return stale/incorrect visuals.
        if mime in {"text/markdown", "text/x-markdown"} or file_path.suffix.lower() in {".md", ".markdown"}:
            return ""

        # Check freedesktop cache (often used by file managers)
        uri = file_path.as_uri()
        digest = hashlib.md5(uri.encode("utf-8")).hexdigest()
        try:
            src_mtime_ns = file_path.stat().st_mtime_ns
        except OSError:
            src_mtime_ns = 0
        for size in ["large", "normal"]:
            candidate = self._freedesktop_cache / size / f"{digest}.png"
            if candidate.exists():
                try:
                    thumb_mtime_ns = candidate.stat().st_mtime_ns
                except OSError:
                    continue
                if thumb_mtime_ns >= src_mtime_ns:
                    return candidate.as_uri()
        return ""

    def _generate_thumbnail(self, file_path: Path, cache_path: Path, mime: str) -> str:
        try:
            if mime.startswith("image/"):
                reader = QImageReader(str(file_path))
                reader.setAutoTransform(True)
                image = reader.read()
                if image.isNull():
                    return ""
                thumb = image.scaled(
                    QSize(self._size_px, self._size_px),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                if thumb.save(str(cache_path), "PNG"):
                    return cache_path.as_uri()
                return ""

            if mime == "application/pdf" or file_path.suffix.lower() == ".pdf":
                if not self._pdftoppm:
                    return ""
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                base = cache_path.with_suffix("")
                result = subprocess.run(
                    [
                        self._pdftoppm,
                        "-f",
                        "1",
                        "-l",
                        "1",
                        "-singlefile",
                        "-png",
                        str(file_path),
                        str(base),
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode == 0 and cache_path.exists():
                    return cache_path.as_uri()
                return ""

            if mime in {"text/markdown", "text/x-markdown"} or file_path.suffix.lower() in {".md", ".markdown"}:
                if not self._md_thumbnailer.exists():
                    return ""
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    [
                        sys.executable,
                        str(self._md_thumbnailer),
                        str(file_path),
                        str(cache_path),
                        str(self._size_px),
                    ],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if result.returncode == 0 and cache_path.exists():
                    return cache_path.as_uri()
                return ""
        except Exception:
            return ""
        return ""


class Backend(QObject):
    thumbnailReady = Signal(str, str)
    entriesReady = Signal(str, "QVariantList")
    languageChanged = Signal(str)
    THUMBNAIL_REFRESH_DEBOUNCE_MS = 220
    THUMBNAIL_REFRESH_RETRY_MS = 180
    THUMBNAIL_REFRESH_MAX_RETRIES = 8

    def __init__(self, api: ScopeApi, app: QGuiApplication, engine: QQmlApplicationEngine) -> None:
        super().__init__()
        self._api = api
        self._app = app
        self._engine = engine
        self._thumbnailer = Thumbnailer()
        self._thumbnailer.thumbnailReady.connect(self._on_thumbnail_ready)
        self._entries_lock = Lock()
        self._entries_cache: dict[str, list] = {}
        self._entries_pending: set[str] = set()
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_watched_file_changed)
        self._sort_watcher = QFileSystemWatcher(self)
        self._sort_watcher.directoryChanged.connect(self._on_sort_root_changed)
        self._sort_watch_roots: set[str] = set()
        self._sort_apply_timers: dict[str, QTimer] = {}
        self._watched_markdown_by_dir: dict[str, set[str]] = {}
        self._watch_refcount: dict[str, int] = {}
        self._thumb_refresh_timers: dict[str, QTimer] = {}
        self._thumb_refresh_retries: dict[str, int] = {}
        self._desktop_watcher = QFileSystemWatcher(self)
        self._desktop_watcher.fileChanged.connect(self._on_desktop_config_changed)
        self._desktop_state_hash: str = ""
        self._project_desktop_hash: dict[str, str] = {}
        self._pending_config_prompt: dict = {}
        self._translator: QTranslator | None = None
        self._language = "de"
        self._i18n_dir = Path(__file__).with_name("i18n")
        self.entriesReady.connect(self._on_entries_ready_for_watcher)
        self._register_desktop_config_watchers()
        self._desktop_state_hash = self._capture_config_state_hash("Desk.md")
        initial_root = self._api.get_project_root() or ""
        if initial_root and self._desktop_state_hash:
            self._project_desktop_hash[initial_root] = self._desktop_state_hash
        self._refresh_sort_watchers(self._api.get_start_path())

    @Slot(str, bool, result="QVariantList")
    def listChildren(self, path: str, includeEmbryos: bool):
        return self._api.list_children(path, includeEmbryos)

    @Slot(str, bool, result="QVariantList")
    def listTemplates(self, path: str, includeEmbryos: bool):
        return self._api.list_templates(path, includeEmbryos)

    @Slot(str, result="QString")
    def projectColor(self, path: str) -> str:
        return self._api.get_project_color(path) or ""

    @Slot(result="QString")
    def defaultProjectColor(self) -> str:
        return self._api.get_default_project_color() or ""

    @Slot(str, result="QString")
    def effectiveProjectColor(self, path: str) -> str:
        return self._api.get_effective_project_color(path) or ""

    @Slot(str, str, result=bool)
    def moveEntry(self, source: str, targetDir: str) -> bool:
        return self._api.move_entry(source, targetDir)

    @Slot("QVariantList", str, result="QVariantMap")
    def moveEntries(self, sources, targetDir: str):
        cleaned = [str(item or "").strip() for item in (sources or [])]
        cleaned = [item for item in cleaned if item]
        return self._api.move_entries(cleaned, targetDir)

    @Slot(str, result="QVariantList")
    def listEntries(self, path: str):
        resolved = str(Path(path).expanduser().resolve())
        cached_entries = None
        with self._entries_lock:
            cached = self._entries_cache.get(resolved)
            if cached is not None:
                cached_entries = cached
            elif resolved in self._entries_pending:
                return []
            else:
                self._entries_pending.add(resolved)
        if cached_entries is not None:
            # Re-prime thumbnails even for cached directory lists so icon updates
            # are picked up after external file changes or delayed writes.
            self._prime_thumbnails(cached_entries)
            return cached_entries
        self._start_entries_task(resolved)
        return []

    @Slot(str, "QVariantList", bool, result="QVariantList")
    def listEntriesFiltered(self, path: str, tags, matchAll: bool):
        resolved = str(Path(path).expanduser().resolve())
        selected = [str(tag or "").strip() for tag in (tags or [])]
        selected = [tag for tag in selected if tag]
        entries = self._api.list_entries_filtered(resolved, selected, bool(matchAll))
        self._enrich_entries(entries, resolved)
        return entries

    @Slot(str, result="QVariantList")
    def listProjectTags(self, path: str):
        return self._api.list_project_tags(path)

    @Slot(str, result="QVariantList")
    def listFolderTags(self, path: str):
        return self._api.list_folder_tags(path)

    @Slot(str, "QVariantList", result=bool)
    def setFolderTags(self, path: str, tags) -> bool:
        cleaned = [str(tag or "").strip() for tag in (tags or [])]
        cleaned = [tag for tag in cleaned if tag]
        return self._api.set_folder_tags(path, cleaned)

    @Slot(str, result="QVariantMap")
    def listTagBuckets(self, path: str):
        return self._api.list_tag_buckets(path)

    @Slot(str, str, str, result=bool)
    def setFolderTagColor(self, path: str, tag: str, color: str) -> bool:
        return self._api.set_folder_tag_color(path, tag, color)

    @Slot(str)
    def setContext(self, path: str) -> None:
        previous_root = self._api.get_project_root() or ""
        current_hash = self._capture_config_state_hash("Desk.md")
        if current_hash:
            self._desktop_state_hash = current_hash
        if previous_root and current_hash:
            previous_hash = self._project_desktop_hash.get(previous_root, "")
            changed = previous_hash != current_hash
            if changed:
                if self._api.has_local_config(previous_root, "Desk.md"):
                    apply_result = self._api.apply_config_state_to_target(previous_root, "Desk.md", "current_project")
                    if bool(apply_result.get("ok")):
                        self._project_desktop_hash[previous_root] = current_hash
                else:
                    options = self._api.list_config_targets(previous_root, "Desk.md")
                    self._pending_config_prompt = {
                        "pending": True,
                        "configName": "Desk.md",
                        "contextPath": previous_root,
                        "options": options,
                    }
        self._api.update_context(path)
        self._refresh_sort_watchers(path)
        next_root = self._api.get_project_root() or ""
        if next_root and self._desktop_state_hash and next_root not in self._project_desktop_hash:
            self._project_desktop_hash[next_root] = self._desktop_state_hash

    @Slot(str, str, result="QVariantMap")
    def ensureProjectConfig(self, path: str, configName: str):
        return self._api.ensure_project_config(path, configName)

    @Slot(str, str, result="QString")
    def findConfig(self, path: str, configName: str) -> str:
        return self._api.find_config(path, configName) or ""

    @Slot(str, result="QVariantList")
    def listFilters(self, path: str):
        return self._api.list_filters(path)

    @Slot(str, result="QVariantMap")
    def resolveActiveFilter(self, path: str):
        return self._api.resolve_active_filter(path)

    @Slot(str, result=bool)
    def setManualFilter(self, filterPath: str) -> bool:
        return self._api.set_manual_filter(filterPath)

    @Slot(result=bool)
    def clearManualFilter(self) -> bool:
        return self._api.clear_manual_filter()

    @Slot(str, str, result="QVariantList")
    def listFilterSaveTargets(self, path: str, sourcePath: str):
        return self._api.list_filter_save_targets(path, sourcePath)

    @Slot(str, str, str, str, result="QVariantMap")
    def saveFilter(self, path: str, sourcePath: str, targetId: str, newName: str):
        return self._api.save_filter(path, sourcePath, targetId, newName)

    @Slot(str, str, result="QVariantMap")
    def perspectiveOpen(self, path: str, perspectiveId: str):
        return self._api.perspective_open(path, perspectiveId)

    @Slot(result="QVariantMap")
    def perspectiveState(self):
        return self._api.perspective_state()

    @Slot(str, result="QVariantMap")
    def perspectiveSetCpd(self, cpd: str):
        return self._api.perspective_set_cpd(cpd)

    @Slot(str, result="QVariantMap")
    def perspectiveResolveCpd(self, cpd: str):
        return self._api.perspective_resolve_cpd(cpd)

    @Slot(str, result="QVariantMap")
    def perspectiveResolveReal(self, path: str):
        return self._api.perspective_resolve_real(path)

    @Slot(str, result="QVariantList")
    def perspectiveListDir(self, cpd: str):
        return self._api.perspective_list_dir(cpd)

    @Slot(result=bool)
    def perspectiveClear(self) -> bool:
        return self._api.perspective_clear()

    @Slot(str, result="QVariantMap")
    def previewSortTarget(self, filePath: str):
        return self._api.preview_sort_target(filePath)

    @Slot(str, str, result="QVariantMap")
    def previewSortTargetForMove(self, sourcePath: str, targetDir: str):
        return self._api.preview_sort_target_for_move(sourcePath, targetDir)

    @Slot(str, result="QVariantMap")
    def applySortNow(self, rootPath: str):
        return self._api.apply_sort_now(rootPath)

    @Slot(result="QVariantMap")
    def configPromptState(self):
        if not self._pending_config_prompt:
            return {"pending": False}
        return dict(self._pending_config_prompt)

    @Slot(str, result="QVariantMap")
    def resolveConfigPrompt(self, targetId: str):
        pending = dict(self._pending_config_prompt or {})
        if not pending:
            return {"ok": False, "reason": "no_pending_prompt"}
        self._pending_config_prompt = {}
        context_path = str(pending.get("contextPath") or "").strip()
        config_name = str(pending.get("configName") or "Desk.md").strip() or "Desk.md"
        if not context_path:
            return {"ok": False, "reason": "missing_context_path"}
        result = self._api.apply_config_state_to_target(context_path, config_name, targetId)
        if bool(result.get("ok")) and targetId != "discard":
            latest_hash = self._capture_config_state_hash(config_name)
            if latest_hash:
                self._project_desktop_hash[context_path] = latest_hash
                self._desktop_state_hash = latest_hash
        return result

    @Slot(str)
    def invalidateEntries(self, path: str) -> None:
        resolved = str(Path(path).expanduser().resolve())
        with self._entries_lock:
            self._entries_cache.pop(resolved, None)
            self._entries_pending.discard(resolved)
        self._drop_watchers_for_dir(resolved)

    @Slot(str, result=str)
    def requestThumbnail(self, path: str) -> str:
        return self._thumbnailer.request_thumbnail(Path(path))

    def _start_entries_task(self, path: str) -> None:
        task = EntriesTask(self, path)
        self._thumbnailer._pool.start(task)

    def _store_entries(self, path: str, entries: list) -> None:
        with self._entries_lock:
            self._entries_cache[path] = entries
            self._entries_pending.discard(path)

    def _on_thumbnail_ready(self, full_path: str, thumb_url: str) -> None:
        if not full_path or not thumb_url:
            return
        normalized = str(Path(full_path).expanduser().resolve())
        with self._entries_lock:
            for _, entries in self._entries_cache.items():
                for entry in entries:
                    item_path = str(entry.get("path") or "")
                    try:
                        item_path_norm = str(Path(item_path).expanduser().resolve()) if item_path else ""
                    except OSError:
                        item_path_norm = item_path
                    if item_path_norm == normalized:
                        entry["thumb"] = thumb_url
        self.thumbnailReady.emit(normalized, thumb_url)

    @Slot(str, "QVariantList")
    def _on_entries_ready_for_watcher(self, path: str, entries) -> None:
        resolved = str(Path(path).expanduser().resolve())
        markdown_files: set[str] = set()
        for entry in (entries or []):
            if entry.get("isDir"):
                continue
            raw_path = str(entry.get("path") or "").strip()
            if not raw_path:
                continue
            suffix = Path(raw_path).suffix.lower()
            if suffix in {".md", ".markdown"}:
                markdown_files.add(str(Path(raw_path).expanduser().resolve()))
        self._sync_watchers_for_dir(resolved, markdown_files)

    def _sync_watchers_for_dir(self, resolved_dir: str, new_files: set[str]) -> None:
        previous = self._watched_markdown_by_dir.get(resolved_dir, set())
        to_remove = previous - new_files
        to_add = new_files - previous

        for file_path in to_remove:
            count = self._watch_refcount.get(file_path, 0) - 1
            if count <= 0:
                self._watch_refcount.pop(file_path, None)
                if file_path in self._watcher.files():
                    self._watcher.removePath(file_path)
            else:
                self._watch_refcount[file_path] = count

        for file_path in to_add:
            self._watch_refcount[file_path] = self._watch_refcount.get(file_path, 0) + 1
            if file_path not in self._watcher.files():
                self._watcher.addPath(file_path)

        if new_files:
            self._watched_markdown_by_dir[resolved_dir] = set(new_files)
        else:
            self._watched_markdown_by_dir.pop(resolved_dir, None)

    def _drop_watchers_for_dir(self, resolved_dir: str) -> None:
        existing = self._watched_markdown_by_dir.pop(resolved_dir, set())
        if not existing:
            return
        for file_path in existing:
            count = self._watch_refcount.get(file_path, 0) - 1
            if count <= 0:
                self._watch_refcount.pop(file_path, None)
                if file_path in self._watcher.files():
                    self._watcher.removePath(file_path)
            else:
                self._watch_refcount[file_path] = count
            timer = self._thumb_refresh_timers.pop(file_path, None)
            if timer is not None:
                timer.stop()

    @Slot(str)
    def _on_watched_file_changed(self, changed_path: str) -> None:
        file_path = Path(changed_path)
        target = str(file_path.resolve()) if file_path.exists() else str(file_path)
        self._schedule_thumbnail_refresh(target)
        # QFileSystemWatcher may auto-drop paths after a change; re-register.
        if changed_path not in self._watcher.files():
            self._watcher.addPath(changed_path)

    @Slot(str)
    def _on_desktop_config_changed(self, changed_path: str) -> None:
        self._desktop_state_hash = self._capture_config_state_hash("Desk.md")
        if changed_path not in self._desktop_watcher.files() and Path(changed_path).exists():
            self._desktop_watcher.addPath(changed_path)

    def _register_desktop_config_watchers(self) -> None:
        home = Path.home()
        candidates = [
            home / ".config" / "kdeglobals",
            home / ".config" / "kwinrc",
            home / ".config" / "plasmarc",
            home / ".config" / "plasma-org.kde.plasma.desktop-appletsrc",
        ]
        paths = [str(p) for p in candidates if p.exists()]
        if paths:
            self._desktop_watcher.addPaths(paths)

    @Slot(str)
    def _on_sort_root_changed(self, root_path: str) -> None:
        resolved = str(Path(root_path).expanduser().resolve())
        timer = self._sort_apply_timers.get(resolved)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda p=resolved: self._api.apply_sort_now(p))
            self._sort_apply_timers[resolved] = timer
        timer.start(250)
        if resolved not in self._sort_watcher.directories() and Path(resolved).exists():
            self._sort_watcher.addPath(resolved)

    def _refresh_sort_watchers(self, path: str) -> None:
        roots = set(self._api.list_sort_watch_roots(path))
        current = set(self._sort_watcher.directories())
        remove_paths = sorted(current - roots)
        add_paths = sorted(roots - current)
        if remove_paths:
            self._sort_watcher.removePaths(remove_paths)
        if add_paths:
            existing = [p for p in add_paths if Path(p).exists()]
            if existing:
                self._sort_watcher.addPaths(existing)
        self._sort_watch_roots = set(roots)

    def _capture_config_state_hash(self, config_name: str) -> str:
        result = self._api.capture_config_state(config_name)
        if not bool(result.get("ok")):
            return ""
        return str(result.get("stateHash") or "")

    def _schedule_thumbnail_refresh(self, full_path: str) -> None:
        timer = self._thumb_refresh_timers.get(full_path)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda p=full_path: self._trigger_thumbnail_refresh(p))
            self._thumb_refresh_timers[full_path] = timer
            self._thumb_refresh_retries[full_path] = 0
        timer.start(self.THUMBNAIL_REFRESH_DEBOUNCE_MS)

    def _trigger_thumbnail_refresh(self, full_path: str) -> None:
        file_path = Path(full_path)
        if not file_path.exists():
            retries = self._thumb_refresh_retries.get(full_path, 0)
            if retries < self.THUMBNAIL_REFRESH_MAX_RETRIES:
                self._thumb_refresh_retries[full_path] = retries + 1
                timer = self._thumb_refresh_timers.get(full_path)
                if timer is not None:
                    timer.start(self.THUMBNAIL_REFRESH_RETRY_MS)
            else:
                self._thumb_refresh_retries.pop(full_path, None)
            return
        self._thumb_refresh_retries.pop(full_path, None)
        thumb = self._thumbnailer.request_thumbnail(file_path)
        if thumb:
            self._on_thumbnail_ready(str(file_path), thumb)

    def _prime_thumbnails(self, entries: list) -> None:
        for entry in entries:
            if entry.get("isDir"):
                continue
            raw_path = entry.get("path")
            if not raw_path:
                continue
            file_path = Path(raw_path)
            thumb = self._thumbnailer.request_thumbnail(file_path)
            if thumb:
                entry["thumb"] = thumb

    def _enrich_entries(self, entries: list, base_path: str) -> None:
        mime_db = QMimeDatabase()
        for entry in entries:
            if entry.get("isDir"):
                entry["mime"] = "inode/directory"
                entry["iconName"] = "folder"
                entry["thumb"] = ""
                continue
            raw_path = entry.get("path")
            if not raw_path:
                raw_path = os.path.join(base_path, entry.get("name", ""))
            try:
                entry["path"] = str(Path(raw_path).expanduser().resolve())
            except OSError:
                entry["path"] = str(raw_path)
            raw_path = entry["path"]
            mime = mime_db.mimeTypeForFile(raw_path, QMimeDatabase.MatchExtension)
            entry["mime"] = mime.name()
            entry["iconName"] = mime.iconName() or mime.genericIconName() or "text-x-generic"
            entry["thumb"] = str(entry.get("thumb") or "")
        self._prime_thumbnails(entries)

    @Slot(str, result=bool)
    def hasMyosDir(self, path: str) -> bool:
        return self._api.has_myos_dir(path)

    @Slot(str, result=bool)
    def isProject(self, path: str) -> bool:
        return self._api.is_project(path)

    @Slot(str, result=bool)
    def isDir(self, path: str) -> bool:
        return self._api.is_dir(path)

    @Slot(str, result=bool)
    def createProject(self, path: str) -> bool:
        return self._api.create_project(path)

    @Slot(str, str, result=str)
    def createFolder(self, path: str, name: str) -> str:
        return self._api.create_folder(path, name) or ""

    @Slot(str, str, result=str)
    def createNote(self, path: str, name: str) -> str:
        return self._api.create_note(path, name) or ""

    @Slot(str, str, result=str)
    def renameEntry(self, path: str, newName: str) -> str:
        return self._api.rename_entry(path, newName) or ""

    @Slot("QVariantList", str, str, result="QVariantMap")
    def renameEntriesBatch(self, paths, replaceFrom: str, replaceTo: str):
        cleaned = [str(item or "").strip() for item in (paths or [])]
        cleaned = [item for item in cleaned if item]
        return self._api.rename_entries_batch(cleaned, str(replaceFrom or ""), str(replaceTo or ""))

    @Slot("QVariantList", result=str)
    def suggestBatchRenameToken(self, paths) -> str:
        cleaned = [str(item or "").strip() for item in (paths or [])]
        cleaned = [item for item in cleaned if item]
        return self._api.suggest_batch_rename_token(cleaned) or ""

    @Slot("QVariantList", result="QVariantMap")
    def deleteEntries(self, paths):
        cleaned = [str(item or "").strip() for item in (paths or [])]
        cleaned = [item for item in cleaned if item]
        return self._api.delete_entries(cleaned)

    @Slot(str, result=bool)
    def openMarkdown(self, path: str) -> bool:
        return self._api.open_markdown(path)

    @Slot(str, str, result=bool)
    def openWith(self, path: str, command: str) -> bool:
        return self._api.open_with(path, command)

    @Slot(str, result=bool)
    def notifyConfigChanged(self, path: str) -> bool:
        return self._api.notify_config_changed(path)

    @Slot(result=str)
    def getStartPath(self) -> str:
        return self._api.get_start_path()

    @Slot(result=str)
    def getProjectRoot(self) -> str:
        return self._api.get_project_root() or ""

    @Slot(result=str)
    def currentLanguage(self) -> str:
        return self._language

    @Slot(str, result=bool)
    def setLanguage(self, languageCode: str) -> bool:
        code = str(languageCode or "de").strip().lower()
        if "-" in code:
            code = code.split("-", 1)[0]
        if code not in {"de", "en"}:
            code = "de"

        if self._translator is not None:
            self._app.removeTranslator(self._translator)
            self._translator = None

        if code != "de":
            translator = QTranslator(self)
            qm_path = self._i18n_dir / f"scope_{code}.qm"
            if not translator.load(str(qm_path)):
                code = "de"
            else:
                self._app.installTranslator(translator)
                self._translator = translator

        self._language = code
        self.languageChanged.emit(self._language)
        try:
            self._engine.retranslate()
        except Exception:
            pass
        return True

    @Slot(float, result=bool)
    def moveCursorByX(self, delta_x: float) -> bool:
        try:
            dx = float(delta_x)
        except (TypeError, ValueError):
            return False
        if abs(dx) < 0.2:
            return False
        pos = QCursor.pos()
        QCursor.setPos(int(round(pos.x() + dx)), int(pos.y()))
        return True


class EntriesTask(QRunnable):
    def __init__(self, owner: Backend, path: str) -> None:
        super().__init__()
        self._owner = owner
        self._path = path

    def run(self) -> None:
        try:
            entries = self._owner._api.list_entries(self._path)
            self._owner._enrich_entries(entries, self._path)
            self._owner._store_entries(self._path, entries)
            self._owner.entriesReady.emit(self._path, entries)
        except Exception:
            self._owner._store_entries(self._path, [])
            self._owner.entriesReady.emit(self._path, [])


class ThemeIconProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, icon_id: str, size: QSize, requested_size: QSize):
        target_size = requested_size if requested_size.isValid() else QSize(64, 64)
        icon = QIcon.fromTheme(icon_id)
        if icon.isNull():
            fallback = "folder" if icon_id == "folder" else "text-x-generic"
            icon = QIcon.fromTheme(fallback)
        pixmap = icon.pixmap(target_size) if not icon.isNull() else None
        if pixmap is None or pixmap.isNull():
            image = QImage(1, 1, QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
        else:
            image = pixmap.toImage()
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def main() -> int:
    os.environ.setdefault("MYOS_MD_USE_POSTFIX", "1")
    start_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())
    api = ScopeApi(start_path)
    app = QGuiApplication(sys.argv)
    icon_path = Path(__file__).with_name("Theme").joinpath("icons", "folder.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    engine = QQmlApplicationEngine()
    engine.addImageProvider("theme", ThemeIconProvider())

    ctx = engine.rootContext()
    backend = Backend(api, app, engine)
    ctx.setContextProperty("backend", backend)
    ctx.setContextProperty("scopeDebugOpen", os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"})
    ctx.setContextProperty("scopeStartPath", api.get_start_path())
    ctx.setContextProperty("scopeProjectRoot", api.get_project_root() or "")
    engine._backend = backend

    ui_lang = os.environ.get("MYOS_UI_LANG", "de")
    backend.setLanguage(ui_lang)

    qml_path = Path(__file__).with_name("main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
