#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QEasingCurve, QObject, QPointF, QTranslator, QVariantAnimation, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QCursor, QImage
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

from core.scope_api import ScopeApi
from daemon.lens_link import LensLink

# pynput's syntax: named keys in angle brackets ("<space>", not "space").
DEFAULT_HOTKEY = "<ctrl>+<alt>+<space>"


class BackdropProvider(QQuickImageProvider):
    """The snapshot of what lies behind the stem's panel, as image://backdrop/<n>."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self.image = QImage()

    def requestImage(self, image_id, size, requested_size):  # noqa: N802 (Qt's name)
        return self.image


def grab_screen(x: int, y: int, w: int, h: int) -> QImage:
    """What the screen shows at (x, y, w, h); a null image where it cannot be read (Wayland)."""
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return QImage()
    return screen.grabWindow(0, x, y, w, h).toImage()


def install_translator(app: QGuiApplication, code: str = "de") -> Optional[QTranslator]:
    """SunTree in the language code: the strings in the code are English, other languages
    load i18n/suntree_<code>.qm (as Scope). The installed translator, or None (English, or
    no translation)."""
    if code == "en":
        return None
    translator = QTranslator(app)
    if not translator.load(str(Path(__file__).with_name("i18n") / f"suntree_{code}.qm")):
        return None
    app.installTranslator(translator)
    return translator


def pointer_and_screen() -> dict:
    """The pointer and the free area of its screen, in global pixels."""
    at = QCursor.pos()
    screen = QGuiApplication.screenAt(at) or QGuiApplication.primaryScreen()
    area = screen.availableGeometry() if screen is not None else None
    return {"x": at.x(), "y": at.y(),
            "sx": area.x() if area else 0, "sy": area.y() if area else 0,
            "sw": area.width() if area else 0, "sh": area.height() if area else 0}


class GlobalHotkeyService(QObject):
    activated = Signal()
    statusChanged = Signal(str)

    def __init__(self, hotkey: str, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._hotkey = hotkey
        self._listener = None
        self._status = "disabled"
        self._start_listener()

    @Slot(result=str)
    def status(self) -> str:
        return self._status

    @Slot(result=str)
    def hotkey(self) -> str:
        return self._hotkey

    def _set_status(self, value: str) -> None:
        if self._status == value:
            return
        self._status = value
        self.statusChanged.emit(value)

    def _start_listener(self) -> None:
        # Wayland often blocks global key hooks for normal apps.
        if os.environ.get("WAYLAND_DISPLAY"):
            self._set_status("wayland-no-global-hotkey")
            return
        try:
            from pynput import keyboard  # type: ignore
        except Exception:
            self._set_status("missing-pynput")
            return

        keymap = {
            self._hotkey: self._on_hotkey,
        }
        try:
            self._listener = keyboard.GlobalHotKeys(keymap)
            self._listener.start()
            self._set_status("active")
        except Exception:
            self._listener = None
            self._set_status("failed")

    def _on_hotkey(self) -> None:
        self.activated.emit()

    def stop(self) -> None:
        if self._listener is None:
            return
        try:
            self._listener.stop()
        except Exception:
            pass
        self._listener = None
        self._set_status("stopped")


class SunTreeBackend(QObject):
    cwdChanged = Signal(str)
    dataChanged = Signal()
    pointerGlideDone = Signal()
    clipboardPathChanged = Signal(str)

    def __init__(self, adapter: MyOSBackendAdapter, start_path: str) -> None:
        super().__init__()
        self._adapter = adapter
        self._cwd = str(Path(start_path).expanduser().resolve())
        # What SunTree shows in its middle (the CTD): looking around moves it, the CWD - the
        # place shared with Scope - moves only by an action (a double click).
        self._ctd = self._cwd
        self._last_pointer = {"x": 0, "y": 0}
        # The lens: the daemon of the projects root, shared with Scope (daemon/lens_link.py).
        # Started when none runs, with the same switch as Scope (MYOS_SCOPE_START_DAEMON=0).
        self._lens = LensLink(adapter, start_daemon=os.environ.get("MYOS_SCOPE_START_DAEMON", "1") != "0")
        self._lens.call("set_cwd", {"path": self._cwd})
        self._lens.update_context(self._cwd)
        self._clipboard = self._resolve_clipboard_dir()
        self._last_drop: list = []  # [{from, now}] of the last drop, for undoDrop
        self.backdrop = BackdropProvider()
        self._grab = grab_screen
        self._where = pointer_and_screen
        self._glide = QVariantAnimation(self)
        self._glide.setEasingCurve(QEasingCurve.InOutCubic)  # the eye picks it up and follows
        self._glide.valueChanged.connect(lambda at: self.pointerTo(round(at.x()), round(at.y())))
        self._glide.finished.connect(self.pointerGlideDone)
        self._backdrops = 0
        self._ensure_clipboard_dir()

    @Slot(result=str)
    def cwd(self) -> str:
        return self._cwd

    @Slot(result=str)
    def ctd(self) -> str:
        return self._ctd

    @Slot(str, result=bool)
    def showFolder(self, path: str) -> bool:
        """Look at path: SunTree shows it in its middle; the CWD, the session and the desktop
        stay as they are."""
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return False
        if not target.is_dir():
            return False
        self._ctd = str(target)
        self.dataChanged.emit()
        return True

    @Slot()
    def showCwd(self) -> None:
        """Back where one stands (SunTree appearing)."""
        if self._ctd != self._cwd:
            self._ctd = self._cwd
            self.dataChanged.emit()

    @Slot(result=str)
    def clipboardPath(self) -> str:
        return self._clipboard

    @Slot(result="QVariantMap")
    def cursorGlobalPos(self):
        pos = QCursor.pos()
        return {"x": int(pos.x()), "y": int(pos.y())}

    @Slot(result="QVariantList")
    def listParents(self):
        parts = Path(self._ctd).parts
        if not parts:
            return []
        current = Path(parts[0])
        rows = [
            {
                "label": str(current),
                "path": str(current),
                "color": str(self._adapter.get_effective_project_color(str(current)) or ""),
            }
        ]
        for part in parts[1:]:
            current = current / part
            path_str = str(current)
            rows.append(
                {
                    "label": part,
                    "path": path_str,
                    "color": str(self._adapter.get_effective_project_color(path_str) or ""),
                }
            )
        return rows

    @Slot(result="QVariantList")
    def listFolders(self):
        return self.listFoldersAt(self._ctd)

    @Slot(str, result="QVariantList")
    def listFoldersAt(self, path: str):
        """The right half at path (the CWD, or a level of the crown): folders that are no
        MyOS folder - those, born or not, are shown on the left only."""
        return [entry for entry in self._adapter.list_children(path) if not entry.get("folderType")]

    @Slot(int, int)
    def pointerTo(self, x: int, y: int) -> None:
        """Put the pointer where the crown draws it (global coordinates): diving, the tree
        pulls it inward (SunTree/Designdocument Krone.md). Works on X11, also during a drag;
        Wayland does not let programs move the pointer."""
        self._last_pointer = {"x": int(x), "y": int(y)}
        QCursor.setPos(int(x), int(y))

    @Slot(result="QVariantMap")
    def lastPointer(self):
        return dict(self._last_pointer)

    @Slot(str, result="QVariantList")
    def listEmbryosAt(self, path: str):
        try:
            target = str(Path(path).expanduser().resolve())
        except Exception:
            return []
        return self._adapter.list_templates(target)

    @Slot(result="QVariantList")
    def listClipboardEntries(self):
        return self._adapter.list_entries(self._clipboard)

    # The lens (Designdocument Perspective Resolver MVP.md, Part A): SunTree only asks the
    # session, as Scope does; it builds no lens paths itself.
    @Slot(str, "QVariantMap", result="QVariantMap")
    def lens(self, method: str, params) -> dict:
        """A lens request: {ok, result | error}; result describes the lens afterwards.
        The Desk follows the lens."""
        return self._lens.call(method, dict(params or {}))

    @Slot(result="QString")
    def projectsRoot(self) -> str:
        """The projects root ("Projekte"); "" outside the projects."""
        return str(self._lens.projects_root or "")

    @Slot(result=bool)
    def homeIfOutside(self) -> bool:
        """SunTree appearing with the CWD outside the project tree goes to the projects root."""
        root = self.projectsRoot()
        if not root:
            return False
        cwd = Path(self._cwd)
        if cwd == Path(root) or Path(root) in cwd.parents:
            return False
        return self.setCwd(root)

    @Slot(str, result="QString")
    def effectiveProjectColor(self, path: str) -> str:
        return self._adapter.get_effective_project_color(path) or ""

    @Slot(str, result=bool)
    def setCwd(self, path: str) -> bool:
        try:
            target = Path(path).expanduser().resolve()
        except Exception:
            return False
        if not target.exists() or not target.is_dir():
            return False
        self._cwd = self._ctd = str(target)
        self._lens.call("set_cwd", {"path": self._cwd})  # a lens on stays where it is (A3)
        self._lens.update_context(self._cwd)
        self.cwdChanged.emit(self._cwd)
        self.dataChanged.emit()
        return True

    @Slot(result=bool)
    def followPlace(self) -> bool:
        """Go where Scope went since SunTree last set or saw the place. Scope and SunTree
        always share the place; SunTree asks when turned to."""
        place = self._lens.follow()
        return bool(place) and self.setCwd(place)

    @Slot(str, result=bool)
    def enterFolder(self, path: str) -> bool:
        return self.setCwd(path)

    @Slot(str, str, result=bool)
    def moveTo(self, source_path: str, target_dir: str) -> bool:
        ok = self._adapter.move_entry(source_path, target_dir)
        if ok:
            self.dataChanged.emit()
        return ok

    @Slot("QVariantList", str, result="QVariantMap")
    def dropFiles(self, sources, target_dir: str) -> dict:
        """Files dropped onto a folder (one action, then gone): {count, place} - place is where
        they lie now (a sorted folder files them on). Remembered for undoDrop."""
        if target_dir == self._clipboard:
            self._ensure_clipboard_dir()
        result = self._adapter.move_entries([str(s) for s in (sources or [])], target_dir)
        filed = {item["source"]: item["destination"] for item in result.get("sorted", [])}
        self._last_drop = []
        for item in result.get("moved", []):
            now = filed.get(item["destination"], item["destination"])
            self._last_drop.append({"from": item["source"], "now": now})
        if self._last_drop:
            self.dataChanged.emit()
        place = str(Path(self._last_drop[-1]["now"]).parent) if self._last_drop else target_dir
        return {"count": len(self._last_drop), "place": place}

    @Slot(int, int, int)
    def glidePointerTo(self, x: int, y: int, ms: int) -> None:
        """The pointer rides from where it is to (x, y) instead of jumping (SunTree appearing at
        a screen edge); pointerGlideDone when it is there. Nothing else should run meanwhile:
        the ride's steps come from the event loop."""
        self._glide.stop()
        here = self._where()
        self._glide.setStartValue(QPointF(here["x"], here["y"]))
        self._glide.setEndValue(QPointF(x, y))
        self._glide.setDuration(max(1, int(ms)))
        self._glide.start()

    @Slot(result="QVariantMap")
    def pointerAt(self) -> dict:
        """Where the pointer is ({x, y}) and the free area of its screen ({sx, sy, sw, sh}):
        SunTree appears with its stem under the pointer."""
        return self._where()

    @Slot(int, int, int, int, result=str)
    def takeBackdrop(self, x: int, y: int, w: int, h: int) -> str:
        """A snapshot of what lies behind (x, y, w, h), taken before SunTree shows: the stem's
        panel draws it blurred, as the compositor offers no blur behind windows (Muffin).
        "" when the screen cannot be read: then the panel is only tinted."""
        # Security: the screen's content stays in memory (the provider), never on disk.
        image = self._grab(x, y, w, h)
        if image is None or image.isNull():
            return ""
        self.backdrop.image = image
        self._backdrops += 1
        return f"image://backdrop/{self._backdrops}"

    @Slot(result=bool)
    def undoDrop(self) -> bool:
        """The last drop back where its files came from; a folder it emptied (an embryo again)
        is born again by it. Once."""
        drop, self._last_drop = self._last_drop, []
        undone = False
        for item in drop:
            result = self._adapter.move_entries([item["now"]], str(Path(item["from"]).parent))
            undone = bool(result.get("moved")) or undone
        if undone:
            self.dataChanged.emit()
        return undone

    @Slot(str, result=bool)
    def moveToClipboard(self, source_path: str) -> bool:
        self._ensure_clipboard_dir()
        ok = self._adapter.move_entry(source_path, self._clipboard)
        if ok:
            self.dataChanged.emit()
        return ok

    @Slot(str, result=str)
    def createFolder(self, name: str) -> str:
        created = self._adapter.create_folder(self._ctd, name) or ""
        if created:
            self.dataChanged.emit()
        return created

    @Slot(str, result=str)
    def createNote(self, name: str) -> str:
        created = self._adapter.create_note(self._ctd, name) or ""
        if created:
            self.dataChanged.emit()
        return created

    @Slot()
    def refreshAll(self) -> None:
        self._lens.update_context(self._cwd)
        self.dataChanged.emit()

    def close(self) -> None:
        self._lens.close()  # the drive ends with the program that started it

    def _resolve_clipboard_dir(self) -> str:
        myos_root = self._adapter.get_myos_root()
        base = Path(myos_root).expanduser().resolve() if myos_root else Path(self._cwd).expanduser().resolve()
        return str(base / "Clipboard")

    def _ensure_clipboard_dir(self) -> None:
        clipboard_path = Path(self._clipboard)
        try:
            clipboard_path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return
        self.clipboardPathChanged.emit(self._clipboard)


class MyOSBackendAdapter:
    def __init__(self, api: ScopeApi) -> None:
        self._api = api

    def projects_root(self):
        return self._api.projects_root()

    def update_context(self, path: str, lens_desk: str = "", lens_desk_save: Optional[str] = None) -> None:
        self._api.update_context(path, lens_desk, lens_desk_save)

    def get_myos_root(self) -> Optional[str]:
        return self._api.get_myos_root()

    def list_children(self, path: str) -> list:
        return self._api.list_children(path, False)

    def list_templates(self, path: str) -> list:
        return self._api.list_templates(path, True)

    def list_entries(self, path: str) -> list:
        return self._api.list_entries(path)

    def get_effective_project_color(self, path: str) -> Optional[str]:
        return self._api.get_effective_project_color(path)

    def move_entry(self, source_path: str, target_dir: str) -> bool:
        return self._api.move_entry(source_path, target_dir)

    def move_entries(self, sources: list, target_dir: str) -> dict:
        return self._api.move_entries(sources, target_dir)

    def create_folder(self, path: str, name: str) -> Optional[str]:
        return self._api.create_folder(path, name)

    def create_note(self, path: str, name: str) -> Optional[str]:
        return self._api.create_note(path, name)


def main() -> int:
    os.environ.setdefault("MYOS_MD_USE_POSTFIX", "1")
    start_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())

    app = QGuiApplication(sys.argv)
    app.setApplicationName("SunTree")
    install_translator(app, "de")  # German, as Scope starts
    icon_path = REPO_ROOT / "Scope" / "Theme" / "icons" / "folder.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    api = ScopeApi(start_path)
    adapter = MyOSBackendAdapter(api)
    backend = SunTreeBackend(adapter, start_path)
    hotkey = os.environ.get("SUNTREE_HOTKEY", DEFAULT_HOTKEY)
    hotkey_service = GlobalHotkeyService(hotkey)
    requested_hidden = os.environ.get("SUNTREE_START_HIDDEN", "1") not in {"0", "false", "no"}
    start_hidden = requested_hidden and hotkey_service.status() == "active"

    engine = QQmlApplicationEngine()
    engine.addImageProvider("backdrop", backend.backdrop)
    ctx = engine.rootContext()
    ctx.setContextProperty("sunTreeBackend", backend)
    ctx.setContextProperty("sunTreeHotkey", hotkey_service)
    ctx.setContextProperty("sunTreeStartHidden", start_hidden)

    qml_path = Path(__file__).with_name("main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        hotkey_service.stop()
        return 1

    # Ensure early backend refresh once QML is alive.
    QTimer.singleShot(0, backend.refreshAll)
    exit_code = app.exec()
    hotkey_service.stop()
    backend.close()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
