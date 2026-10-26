#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import hashlib
import mimetypes
import shutil
import subprocess
import time
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
    QEvent,
    QSettings,
)
from PySide6.QtGui import (
    QGuiApplication,
    QIcon,
    QImageReader,
    QImage,
    QCursor,
    QDropEvent,
)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtCore import QMimeDatabase

from core.scope_api import ScopeApi
from core.settings import Settings
from daemon.lens_link import LensLink

try:  # imported as Scope.Scope (tests) or run as a script (python3 Scope/Scope.py)
    from .window_icon import with_project_badge
except ImportError:
    from window_icon import with_project_badge


class DropDebugFilter(QObject):
    """Log drop events at window level to see if the drop reaches the window at all."""

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Drop and isinstance(event, QDropEvent):
            pos = event.position() if hasattr(event, "position") else event.pos()
            md = event.mimeData()
            text = (md.text() or "").strip() if md else ""
            urls = list(md.urls()) if md else []
            print(
                "[drop.window] Drop am Fenster empfangen",
                "pos=",
                (round(pos.x()), round(pos.y())),
                "text=",
                "ok" if text else "-",
                "urls=",
                len(urls),
            )
        return False


class ThumbnailTask(QRunnable):
    def __init__(self, owner: "Thumbnailer", file_path: Path, cache_path: Path, mime: str) -> None:
        super().__init__()
        self._owner = owner
        self._file_path = file_path
        self._cache_path = cache_path
        self._mime = mime

    def run(self) -> None:
        try:
            if self._owner._shutting_down:
                return
            result = self._owner._generate_thumbnail(self._file_path, self._cache_path, self._mime)
            if result and not self._owner._shutting_down:
                self._owner.thumbnailReady.emit(str(self._file_path), result)
        finally:
            self._owner._mark_done(self._file_path, self._mime)


class Thumbnailer(QObject):
    thumbnailReady = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        self._pool = QThreadPool()
        self._shutting_down = False
        self._lock = Lock()
        self._pending: set[str] = set()
        self._cache_root = Path("~/.cache/myos-scope/thumbnails").expanduser()
        self._freedesktop_cache = Path("~/.cache/thumbnails").expanduser()
        self._pdftoppm = shutil.which("pdftoppm")
        self._md_thumbnailer = Path(__file__).resolve().parents[1] / "core" / "bin" / "myos-md-thumbnailer"
        self._size_px = 256

    def request_thumbnail(self, file_path: Path) -> str:
        if self._shutting_down:
            return ""
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

    def shutdown(self) -> None:
        """Stop accepting new requests and wait briefly for running tasks."""
        self._shutting_down = True
        self._pool.clear()
        self._pool.waitForDone(2000)


class Backend(QObject):
    thumbnailReady = Signal(str, str)
    entriesReady = Signal(str, "QVariantList")
    languageChanged = Signal(str)
    # (listingPath, [{path, bytes, complete}]) in batches; bytes is a lower bound while
    # complete is False. The listing's own path carries the total of the listed folder.
    folderSizesReady = Signal(str, "QVariantList")
    # (listingPath, summary) for the ACL filter panel, see ScopeApi.acl_summary.
    aclSummaryReady = Signal(str, "QVariantMap")
    # Filing by date moved files (catch-up at start and once a day): listings may be stale.
    filingDone = Signal()
    # FilesPanel views: tiles and list.
    FILES_VIEW_STYLES = ("largeIcon", "smallIcon")
    # List view columns right of the name (ids as in Scope/js/FormatUtils.js).
    FILES_LIST_COLUMNS = ("modified", "size", "type", "tags", "accessed", "permissions", "owner", "group")
    # Persisted sort keys of the list (Scope/js/ListSort.js). Sorting by size is not
    # persisted: it belongs to the on-demand size measurement of one folder.
    FILES_SORT_KEYS = ("name", "modified", "type", "tags", "accessed", "permissions", "owner", "group")
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
        self._shutting_down = False
        app.aboutToQuit.connect(self._on_about_to_quit)
        self._entries_lock = Lock()
        self._entries_cache: dict[str, list] = {}
        # X-ray view (core.xray): how many entries the FilesPanel shows without scrolling
        # (0: off) and whether it shows folders. Set by the window, used for every listing.
        self._xray_budget = 0
        self._xray_folders_shown = True
        self._entries_pending: set[str] = set()
        # Folder sizes: measured on demand (hover/click on the size column), one task at a
        # time; a new request or cancel bumps the generation so older measurements stop.
        self._settings = QSettings("MyOS", "Scope")
        # The settings of all MyOS programs (core/settings.py), set on Scope's back.
        self._shared_settings = Settings()
        self._sizes_pool = QThreadPool(self)
        self._sizes_pool.setMaxThreadCount(1)
        self._sizes_generation = 0
        # ACL panel: computed in the background, newest request wins (like folder sizes).
        self._acl_pool = QThreadPool(self)
        self._acl_pool.setMaxThreadCount(1)
        self._acl_generation = 0
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_watched_file_changed)
        self._watched_markdown_by_dir: dict[str, set[str]] = {}
        self._watch_refcount: dict[str, int] = {}
        self._thumb_refresh_timers: dict[str, QTimer] = {}
        self._thumb_refresh_retries: dict[str, int] = {}
        self._translator: QTranslator | None = None
        self._language = "de"
        self._i18n_dir = Path(__file__).with_name("i18n")
        self.entriesReady.connect(self._on_entries_ready_for_watcher)
        # Filing by date (core/filing.py) catches up instead of watching: a sorted folder
        # is filed when looked at (ScopeApi.list_entries), the whole project at the start
        # (a moment later, the window first) and once a day.
        self._filing_pool = QThreadPool(self)
        self._filing_pool.setMaxThreadCount(1)
        self._filing_timer = QTimer(self)
        self._filing_timer.timeout.connect(self._catch_up_filing)
        QTimer.singleShot(3000, self._catch_up_filing)
        self._filing_timer.start(24 * 60 * 60 * 1000)
        # The lens: the daemon of this projects root, shared with SunTree (daemon/lens_link.py).
        # Scope starts it when none runs (switched off with MYOS_SCOPE_START_DAEMON=0, e.g.
        # for tests).
        self._lens_link = LensLink(self._api, start_daemon=os.environ.get("MYOS_SCOPE_START_DAEMON", "1") != "0")
        self._projects_root = self._lens_link.projects_root

    @Slot(str, bool, bool, result="QVariantList")
    def listChildren(self, path: str, includeEmbryos: bool, showHidden: bool = False):
        return self._api.list_children(path, includeEmbryos, showHidden)

    @Slot(str, bool, bool, result="QVariantList")
    def listTemplates(self, path: str, includeEmbryos: bool, showHidden: bool = False):
        return self._api.list_templates(path, includeEmbryos, showHidden)

    @Slot(str, result="QString")
    def projectColor(self, path: str) -> str:
        return self._api.get_project_color(path) or ""

    @Slot(str, result="QString")
    def projectIcon(self, path: str) -> str:
        return self._api.get_project_icon(path) or ""

    @Slot(result="QString")
    def defaultProjectColor(self) -> str:
        return self._api.get_default_project_color() or ""

    @Slot(result="QString")
    def projectsRoot(self) -> str:
        """The projects root ("Projekte") of this Scope; "" outside the projects."""
        return str(self._projects_root or "")

    @Slot(result="QString")
    def platformName(self) -> str:
        """Returns QPA platform name, e.g. 'xcb' (X11) or 'wayland'. Used for edge-dock trigger (X11 vs Wayland fallback)."""
        if hasattr(self._app, "platformName"):
            return self._app.platformName() or "unknown"
        return "unknown"

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
        result = self._api.move_entries(cleaned, targetDir)
        self._invalidate_reabsorbed(result)
        return result

    @Slot(str, bool, result="QVariantList")
    def listEntries(self, path: str, showHidden: bool = False):
        resolved = str(Path(path).expanduser().resolve())
        cached_entries = None
        with self._entries_lock:
            cached = self._entries_cache.get(resolved)
            if cached is not None:
                cached_entries = cached
            elif resolved not in self._entries_pending:
                self._entries_pending.add(resolved)
        if cached_entries is not None:
            self._prime_thumbnails(cached_entries)
            if not showHidden:
                cached_entries = [
                    e for e in cached_entries
                    if not (e.get("name") or "").startswith(".")
                ]
            return cached_entries
        self._start_entries_task(resolved)
        quick = self._api.list_entries_quick(resolved, showHidden)
        self._enrich_entries(quick, resolved)
        return quick

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
        # The desktop follows (Desk.md, with a lens on its Desk) and changes are saved in
        # the core (DeskService).
        self._lens_link.update_context(path)

    @Slot(str, str, result="QVariantMap")
    def ensureProjectConfig(self, path: str, configName: str):
        return self._api.ensure_project_config(path, configName)

    @Slot(str, str, result="QString")
    def findConfig(self, path: str, configName: str) -> str:
        return self._api.find_config(path, configName) or ""

    # The lens (Designdocument Perspective Resolver MVP.md, Part A): Scope only asks the
    # session (daemon/lens_link.py); it builds no lens paths itself.

    @Slot(str, "QVariantMap", result="QVariantMap")
    def lens(self, method: str, params) -> dict:
        """A lens request: {ok, result | error}; result describes the lens afterwards.
        The Desk follows the lens."""
        return self._lens_link.call(method, dict(params or {}))

    @Slot(result=str)
    def followPlace(self) -> str:
        """Where SunTree went since Scope last set or saw the place: the new CWD, or "".
        Scope and SunTree always share the place; Scope asks when turned to."""
        return self._lens_link.follow() or ""

    @Slot(result="QVariantMap")
    def lensBear(self) -> dict:
        """Bear the lens' folder (where the department folder is missing) to drop or create
        something in it."""
        state = self.lens("state", {}).get("result") or {}
        target = str(state.get("target") or "")
        if not target:
            return {"ok": False, "error": "no lens target"}
        # Security: only born where the user may write - as for any folder created.
        if not self._api.acl_allows("write", Path(target)):
            return {"ok": False, "error": f"no write access: {target}"}
        return self._lens_link.bear()

    @Slot(str, str, result="QVariantMap")
    def previewSortTargetForMove(self, sourcePath: str, targetDir: str):
        return self._api.preview_sort_target_for_move(sourcePath, targetDir)

    @Slot(str, result="QVariantMap")
    def enableSorting(self, path: str):
        """Give the folder a sort rule (years and months by date; see ScopeApi)."""
        return self._api.enable_sorting(path)

    def _catch_up_filing(self) -> None:
        if not self._shutting_down:
            self._filing_pool.start(FilingTask(self, self._api.get_start_path()))

    def _invalidate_reabsorbed(self, result) -> None:
        # Reabsorbed folders vanished from disk: drop cached listings of them and their parents.
        for raw in (result or {}).get("reabsorbed") or []:
            self.invalidateEntries(raw)
            self.invalidateEntries(str(Path(raw).parent))

    @Slot(result=bool)
    def filesXray(self) -> bool:
        """X-ray view on or off; on by default."""
        return str(self._settings.value("filesXray", "true")).lower() not in ("false", "0")

    @Slot(bool)
    def setFilesXray(self, enabled: bool) -> None:
        self._settings.setValue("filesXray", bool(enabled))

    @Slot(int, bool)
    def setXrayView(self, budget: int, folders_shown: bool) -> None:
        """Entries the FilesPanel shows without scrolling (0: x-ray off) and whether it shows
        folders; cached listings no longer match then."""
        budget = max(0, int(budget))
        if (budget, bool(folders_shown)) == (self._xray_budget, self._xray_folders_shown):
            return
        self._xray_budget, self._xray_folders_shown = budget, bool(folders_shown)
        with self._entries_lock:
            self._entries_cache.clear()
            self._entries_pending.clear()

    def _list_for_view(self, path: str) -> list:
        if self._xray_budget > 0:
            return self._api.list_entries_xray(path, self._xray_budget, self._xray_folders_shown)
        return self._api.list_entries(path)

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
        if self._shutting_down:
            return
        task = EntriesTask(self, path)
        self._thumbnailer._pool.start(task)

    @Slot(str)
    def requestFolderSizes(self, path: str) -> None:
        """Measure the subfolders of this listing (on demand; replaces any running measurement)."""
        self._sizes_generation += 1
        if self._shutting_down:
            return
        resolved = str(Path(path).expanduser().resolve())
        self._sizes_pool.start(FolderSizesTask(self, resolved, self._sizes_generation))

    @Slot()
    def cancelFolderSizes(self) -> None:
        """Stop measurements of a listing that is no longer shown (energy saving)."""
        self._sizes_generation += 1

    def _sizes_task_current(self, generation: int) -> bool:
        return not self._shutting_down and generation == self._sizes_generation

    @Slot(str, "QVariantList")
    def requestAclSummary(self, path: str, entryPaths) -> None:
        """Compute the ACL panel for this listing in the background (aclSummaryReady)."""
        self._acl_generation += 1
        if self._shutting_down:
            return
        paths = [str(p or "") for p in (entryPaths or []) if str(p or "")]
        self._acl_pool.start(AclSummaryTask(self, str(path or ""), paths, self._acl_generation))

    @Slot(str, result="QVariantList")
    def trashEntries(self, path: str) -> list:
        """Trash of the project path lies in (see ScopeApi.trash_entries)."""
        return self._api.trash_entries(path)

    @Slot(str, str, result="QVariantMap")
    def trashRestore(self, path: str, name: str) -> dict:
        return self._api.trash_restore(path, name)

    @Slot(str, str, result="QVariantMap")
    def trashDeleteFinally(self, path: str, name: str) -> dict:
        return self._api.trash_delete_finally(path, name)

    @Slot(str, result="QVariantMap")
    def trashEmpty(self, path: str) -> dict:
        return self._api.trash_empty(path)

    @Slot(str, str, result=bool)
    def aclHasOwnRule(self, path: str, role: str) -> bool:
        return self._api.acl_has_own_rule(path, role)

    @Slot(str, str, "QVariant", result="QVariantMap")
    def aclSetRoleRights(self, path: str, role: str, rights) -> dict:
        """rights: list of rights, [] = none, null = back to inherited (see ScopeApi)."""
        if hasattr(rights, "toVariant"):  # a JS array or null arrives as QJSValue
            rights = None if rights.isNull() or rights.isUndefined() else rights.toVariant()
        values = None if rights is None else [str(r) for r in rights]
        return self._api.acl_set_role_rights(path, role, values)

    @Slot(str, str, result="QVariantMap")
    def aclUserGroups(self, path: str, user: str) -> dict:
        return self._api.acl_user_groups(path, user)

    @Slot(str, str, "QVariant", result="QVariantMap")
    def aclSetUserGroups(self, path: str, user: str, groups) -> dict:
        """groups: list of group keys, [] removes the person (see ScopeApi)."""
        if hasattr(groups, "toVariant"):  # a JS array arrives as QJSValue
            groups = groups.toVariant()
        return self._api.acl_set_user_groups(path, user, [str(g) for g in (groups or [])])

    @Slot(str, str, result="QVariantMap")
    def aclClaimIdentity(self, path: str, name: str) -> dict:
        """Remember on this computer that the user is the person name (see core.identity)."""
        return self._api.acl_claim_identity(path, name)

    @Slot(str, result="QVariantMap")
    def aclGroupChoices(self, path: str) -> dict:
        return self._api.acl_group_choices(path)

    @Slot(str, str, "QVariant", result="QVariantMap")
    def aclAddUser(self, path: str, name: str, groups) -> dict:
        """groups: list of group keys, at least one (see ScopeApi.acl_add_user)."""
        if hasattr(groups, "toVariant"):  # a JS array arrives as QJSValue
            groups = groups.toVariant()
        return self._api.acl_add_user(path, name, [str(g) for g in (groups or [])])

    def _acl_task_current(self, generation: int) -> bool:
        return not self._shutting_down and generation == self._acl_generation

    @Slot(result=str)
    def filesViewStyle(self) -> str:
        style = str(self._settings.value("filesViewStyle", "largeIcon") or "")
        return style if style in self.FILES_VIEW_STYLES else "largeIcon"

    @Slot(str)
    def setFilesViewStyle(self, style: str) -> None:
        if style in self.FILES_VIEW_STYLES:
            self._settings.setValue("filesViewStyle", style)

    @Slot(result="QStringList")
    def filesListColumns(self) -> list:
        raw = self._settings.value("filesListColumns", None)
        if raw is None:
            return ["modified", "size"]
        # Written as one comma string; an unquoted value in a hand-edited file comes back
        # as a list instead, so accept both.
        parts = raw if isinstance(raw, (list, tuple)) else str(raw).split(",")
        return [str(part).strip() for part in parts if str(part).strip() in self.FILES_LIST_COLUMNS]

    @Slot("QStringList")
    def setFilesListColumns(self, columns) -> None:
        ids = [str(c) for c in (columns or []) if str(c) in self.FILES_LIST_COLUMNS]
        self._settings.setValue("filesListColumns", ",".join(ids))

    @Slot(result="QVariantMap")
    def filesSort(self) -> dict:
        key = str(self._settings.value("filesSortKey", "name") or "")
        if key not in self.FILES_SORT_KEYS:
            # Unknown or no longer persisted key (e.g. "size" from older versions).
            return {"key": "name", "ascending": True}
        ascending = self._settings.value("filesSortAscending", True, type=bool)
        return {"key": key, "ascending": bool(ascending)}

    @Slot(str, bool)
    def setFilesSort(self, key: str, ascending: bool) -> None:
        if key in self.FILES_SORT_KEYS:
            self._settings.setValue("filesSortKey", key)
            self._settings.setValue("filesSortAscending", bool(ascending))


    def _store_entries(self, path: str, entries: list) -> None:
        with self._entries_lock:
            self._entries_cache[path] = entries
            self._entries_pending.discard(path)

    def _on_thumbnail_ready(self, full_path: str, thumb_url: str) -> None:
        if self._shutting_down or not full_path or not thumb_url:
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
        # List column "Typ": the MIME description in the system language (e.g. "PDF-Dokument").
        folder_type = mime_db.mimeTypeForName("inode/directory").comment()
        for entry in entries:
            if entry.get("isDir"):
                entry["mime"] = "inode/directory"
                entry["typeName"] = folder_type
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
            entry["typeName"] = mime.comment()
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
    def canCreateProject(self, path: str) -> bool:
        return self._api.can_create_project(path)

    @Slot(str, result=bool)
    def canRemoveProject(self, path: str) -> bool:
        return self._api.can_remove_project(path)

    @Slot(str, bool, result="QVariantMap")
    def removeProject(self, path: str, keep_own: bool) -> dict:
        """{ok, reason, own}; reason "own": ask, then call again with keep_own (ScopeApi)."""
        return self._api.remove_project(path, keep_own)

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
        result = self._api.delete_entries(cleaned)
        self._invalidate_reabsorbed(result)
        return result

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

    # The back of Scope (Scope/Designdocument Setup.md): the one settings file.
    @Slot(str, result="QVariant")
    def setting(self, key: str):
        return self._shared_settings.get(key)

    @Slot(str, "QVariant", result=bool)
    def setSetting(self, key: str, value) -> bool:
        return self._shared_settings.set(key, value)

    @Slot(str, result="QVariant")
    def settingDefault(self, key: str):
        return self._shared_settings.default(key)

    @Slot(str, result="QVariantList")
    def settingLimits(self, key: str) -> list:
        return list(self._shared_settings.limits(key) or [])

    @Slot(str)
    def resetSetting(self, key: str) -> None:
        self._shared_settings.reset(key)

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

        # Source strings are English; other languages load i18n/scope_<code>.qm.
        if code != "en":
            translator = QTranslator(self)
            qm_path = self._i18n_dir / f"scope_{code}.qm"
            if not translator.load(str(qm_path)):
                code = "en"
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

    def _on_about_to_quit(self) -> None:
        """Stop thumbnail tasks and timers so the app can exit promptly."""
        self._shutting_down = True
        # Running size measurements poll _shutting_down and stop within a few entries.
        self._sizes_generation += 1
        self._sizes_pool.clear()
        self._sizes_pool.waitForDone(1000)
        self._acl_generation += 1
        self._acl_pool.clear()
        self._acl_pool.waitForDone(1000)
        self._filing_timer.stop()
        self._filing_pool.waitForDone(3000)  # a move in progress finishes
        self._lens_link.close()  # the drive ends with the Scope that started it
        for timer in self._thumb_refresh_timers.values():
            timer.stop()
        self._thumb_refresh_timers.clear()
        self._thumbnailer.shutdown()


class FilingTask(QRunnable):
    """Catch up filing by date in the project tree of path (core/filing.py)."""

    def __init__(self, owner: Backend, path: str) -> None:
        super().__init__()
        self._owner = owner
        self._path = path

    def run(self) -> None:
        try:
            report = self._owner._api.catch_up_filing_all(self._path)
        except Exception:
            return
        if report.get("moved") and not self._owner._shutting_down:
            with self._owner._entries_lock:
                self._owner._entries_cache.clear()
            self._owner.filingDone.emit()


class EntriesTask(QRunnable):
    def __init__(self, owner: Backend, path: str) -> None:
        super().__init__()
        self._owner = owner
        self._path = path

    def run(self) -> None:
        try:
            entries = self._owner._list_for_view(self._path)
            self._owner._enrich_entries(entries, self._path)
            self._owner._store_entries(self._path, entries)
            self._owner.entriesReady.emit(self._path, entries)
        except Exception:
            self._owner._store_entries(self._path, [])
            self._owner.entriesReady.emit(self._path, [])


class AclSummaryTask(QRunnable):
    """ACL panel data of one listing; dropped when a newer request came in meanwhile."""

    def __init__(self, owner: Backend, listing_path: str, entry_paths: list, generation: int) -> None:
        super().__init__()
        self._owner = owner
        self._listing_path = listing_path
        self._entry_paths = entry_paths
        self._generation = generation

    def run(self) -> None:
        if not self._owner._acl_task_current(self._generation):
            return
        try:
            summary = self._owner._api.acl_summary(self._listing_path, self._entry_paths)
        except Exception:
            summary = {"hasAcls": False}
        if self._owner._acl_task_current(self._generation):
            self._owner.aclSummaryReady.emit(self._listing_path, summary)


class FolderSizesTask(QRunnable):
    """
    Measure the subfolders of a listing in two passes and report results in batches.
    Pass 1 gives every folder a small budget so one huge folder cannot hold up the
    others; folders over budget report a lower bound and are finished in pass 2.
    The listing's total is the sum of its files and subfolders (no second walk).
    Every measurement stops as soon as the listing is left or the app quits.
    """

    PASS1_MAX_ENTRIES = 2000
    BATCH_INTERVAL_S = 0.15

    def __init__(self, owner: Backend, listing_path: str, generation: int) -> None:
        super().__init__()
        self._owner = owner
        self._listing_path = listing_path
        self._generation = generation
        self._batch: list = []
        self._last_flush = time.monotonic()

    def _current(self) -> bool:
        return self._owner._sizes_task_current(self._generation)

    def _add(self, path: str, size: int, complete: bool) -> None:
        self._batch.append({"path": path, "bytes": float(size), "complete": bool(complete)})
        if time.monotonic() - self._last_flush >= self.BATCH_INTERVAL_S:
            self._flush()

    def _flush(self) -> None:
        if self._batch and self._current():
            self._owner.folderSizesReady.emit(self._listing_path, self._batch)
        self._batch = []
        self._last_flush = time.monotonic()

    def _scan_listing(self):
        """Direct file bytes and subfolders (visible first) of the listing."""
        files_bytes = 0
        visible, hidden = [], []
        try:
            device = os.lstat(self._listing_path).st_dev
            with os.scandir(self._listing_path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if entry.stat(follow_symlinks=False).st_dev == device:
                                (hidden if entry.name.startswith(".") else visible).append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            files_bytes += int(entry.stat(follow_symlinks=False).st_size)
                    except OSError:
                        continue
        except OSError:
            pass
        visible.sort(key=str.lower)
        hidden.sort(key=str.lower)
        return files_bytes, visible + hidden

    def _measure(self, path: str, max_entries) -> dict:
        return self._owner._api.measure_folder_size(path, max_entries=max_entries, should_continue=self._current)

    def run(self) -> None:
        try:
            files_bytes, folders = self._scan_listing()
            results = {}
            for path in folders:
                if not self._current():
                    return
                results[path] = self._measure(path, self.PASS1_MAX_ENTRIES)
                self._add(path, results[path]["bytes"], results[path]["complete"])
            partial = any(not r["complete"] for r in results.values())
            if partial:
                total = files_bytes + sum(r["bytes"] for r in results.values())
                self._add(self._listing_path, total, False)
            self._flush()
            for path in [p for p, r in results.items() if not r["complete"]]:
                if not self._current():
                    return
                results[path] = self._measure(path, None)
                self._add(path, results[path]["bytes"], results[path]["complete"])
            total = files_bytes + sum(r["bytes"] for r in results.values())
            self._add(self._listing_path, total, all(r["complete"] for r in results.values()))
            self._flush()
        except Exception:
            return


class ThemeIconProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, icon_id: str, size: QSize, requested_size: QSize):
        target_size = requested_size if requested_size.isValid() else QSize(64, 64)
        use_active = icon_id.endswith("#active")
        base_id = icon_id[:-7] if use_active else icon_id  # strip "#active"
        # Für Ordner: Hover = folder-open (freedesktop-Standard), sonst QIcon.Mode.Active
        if use_active and base_id == "folder":
            base_id = "folder-open"
            use_active = False
        icon = QIcon.fromTheme(base_id)
        if icon.isNull():
            fallback = "folder" if base_id == "folder" else "text-x-generic"
            icon = QIcon.fromTheme(fallback)
        mode = QIcon.Mode.Active if use_active else QIcon.Mode.Normal
        pixmap = icon.pixmap(target_size, mode, QIcon.State.Off) if not icon.isNull() else None
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
    # The window's icon is the theme's folder (Scope's own only where the theme has none) with
    # the projects' P on it: in the taskbar Scope is not the file browser.
    icon_path = Path(__file__).with_name("Theme").joinpath("icons", "folder.svg")
    app.setWindowIcon(with_project_badge(QIcon.fromTheme("folder", QIcon(str(icon_path)))))
    engine = QQmlApplicationEngine()
    engine.addImageProvider("theme", ThemeIconProvider())

    ctx = engine.rootContext()
    backend = Backend(api, app, engine)
    ctx.setContextProperty("backend", backend)
    ctx.setContextProperty("scopeStartPath", api.get_start_path())
    ctx.setContextProperty("scopeProjectRoot", api.get_project_root() or "")
    engine._backend = backend

    ui_lang = os.environ.get("MYOS_UI_LANG", "de")
    backend.setLanguage(ui_lang)

    qml_path = Path(__file__).with_name("main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    root = engine.rootObjects()[0]
    drop_filter = DropDebugFilter()
    root.installEventFilter(drop_filter)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
