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

from PySide6.QtCore import QObject, Slot, QUrl, Signal, QThreadPool, QRunnable, QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QImageReader, QImage
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
        return False

    def _cache_key(self, file_path: Path, mime: str) -> str:
        payload = f"{file_path.resolve()}|{mime}"
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def _cache_path_for_key(self, key: str) -> Path:
        return self._cache_root / f"{key}.png"

    def _cached_thumbnail(self, file_path: Path, mime: str) -> str:
        key = self._cache_key(file_path, mime)
        cached = self._cache_path_for_key(key)
        if cached.exists():
            return cached.as_uri()

        # Check freedesktop cache (often used by file managers)
        uri = file_path.as_uri()
        digest = hashlib.md5(uri.encode("utf-8")).hexdigest()
        for size in ["large", "normal"]:
            candidate = self._freedesktop_cache / size / f"{digest}.png"
            if candidate.exists():
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
        except Exception:
            return ""
        return ""


class Backend(QObject):
    thumbnailReady = Signal(str, str)
    entriesReady = Signal(str, "QVariantList")

    def __init__(self, api: ScopeApi) -> None:
        super().__init__()
        self._api = api
        self._thumbnailer = Thumbnailer()
        self._thumbnailer.thumbnailReady.connect(self.thumbnailReady)
        self._entries_lock = Lock()
        self._entries_cache: dict[str, list] = {}
        self._entries_pending: set[str] = set()

    @Slot(str, bool, result="QVariantList")
    def listChildren(self, path: str, includeEmbryos: bool):
        return self._api.list_children(path, includeEmbryos)

    @Slot(str, bool, result="QVariantList")
    def listTemplates(self, path: str, includeEmbryos: bool):
        return self._api.list_templates(path, includeEmbryos)

    @Slot(str, result="QString")
    def projectColor(self, path: str) -> str:
        return self._api.get_project_color(path) or ""

    @Slot(str, str, result=bool)
    def moveEntry(self, source: str, targetDir: str) -> bool:
        return self._api.move_entry(source, targetDir)

    @Slot(str, result="QVariantList")
    def listEntries(self, path: str):
        resolved = str(Path(path).expanduser().resolve())
        with self._entries_lock:
            cached = self._entries_cache.get(resolved)
            if cached is not None:
                return cached
            if resolved in self._entries_pending:
                return []
            self._entries_pending.add(resolved)
        self._start_entries_task(resolved)
        return []

    @Slot(str)
    def setContext(self, path: str) -> None:
        self._api.update_context(path)

    @Slot(str)
    def invalidateEntries(self, path: str) -> None:
        resolved = str(Path(path).expanduser().resolve())
        with self._entries_lock:
            self._entries_cache.pop(resolved, None)
            self._entries_pending.discard(resolved)

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

    @Slot(str, result=bool)
    def hasMyosDir(self, path: str) -> bool:
        return self._api.has_myos_dir(path)

    @Slot(str, result=bool)
    def isProject(self, path: str) -> bool:
        return self._api.is_project(path)

    @Slot(str, result=bool)
    def createProject(self, path: str) -> bool:
        return self._api.create_project(path)

    @Slot(str, result=bool)
    def openMarkdown(self, path: str) -> bool:
        return self._api.open_markdown(path)

    @Slot(result=str)
    def getStartPath(self) -> str:
        return self._api.get_start_path()

    @Slot(result=str)
    def getProjectRoot(self) -> str:
        return self._api.get_project_root() or ""


class EntriesTask(QRunnable):
    def __init__(self, owner: Backend, path: str) -> None:
        super().__init__()
        self._owner = owner
        self._path = path

    def run(self) -> None:
        try:
            mime_db = QMimeDatabase()
            entries = self._owner._api.list_entries(self._path)
            for entry in entries:
                if entry.get("isDir"):
                    entry["mime"] = "inode/directory"
                    entry["iconName"] = "folder"
                    continue
                raw_path = entry.get("path")
                if not raw_path:
                    raw_path = os.path.join(self._path, entry.get("name", ""))
                    entry["path"] = raw_path
                mime = mime_db.mimeTypeForFile(raw_path, QMimeDatabase.MatchExtension)
                entry["mime"] = mime.name()
                entry["iconName"] = mime.iconName() or mime.genericIconName() or "text-x-generic"
            self._owner._prime_thumbnails(entries)
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
    start_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())
    api = ScopeApi(start_path)
    app = QGuiApplication(sys.argv)
    icon_path = Path(__file__).with_name("Theme").joinpath("icons", "folder.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    engine = QQmlApplicationEngine()
    engine.addImageProvider("theme", ThemeIconProvider())

    ctx = engine.rootContext()
    backend = Backend(api)
    ctx.setContextProperty("backend", backend)
    ctx.setContextProperty("scopeDebugOpen", os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"})
    ctx.setContextProperty("scopeStartPath", api.get_start_path())
    ctx.setContextProperty("scopeProjectRoot", api.get_project_root() or "")
    engine._backend = backend

    qml_path = Path(__file__).with_name("main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
