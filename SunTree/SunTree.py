#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QCursor
from PySide6.QtQml import QQmlApplicationEngine

from core.scope_api import ScopeApi


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
    clipboardPathChanged = Signal(str)

    def __init__(self, adapter: MyOSBackendAdapter, start_path: str) -> None:
        super().__init__()
        self._adapter = adapter
        self._cwd = str(Path(start_path).expanduser().resolve())
        self._adapter.update_context(self._cwd)
        self._clipboard = self._resolve_clipboard_dir()
        self._ensure_clipboard_dir()

    @Slot(result=str)
    def cwd(self) -> str:
        return self._cwd

    @Slot(result=str)
    def clipboardPath(self) -> str:
        return self._clipboard

    @Slot(result="QVariantMap")
    def cursorGlobalPos(self):
        pos = QCursor.pos()
        return {"x": int(pos.x()), "y": int(pos.y())}

    @Slot(result="QVariantList")
    def listParents(self):
        parts = Path(self._cwd).parts
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
        return self._adapter.list_children(self._cwd)

    @Slot(result="QVariantList")
    def listEmbryos(self):
        return self._adapter.list_templates(self._cwd)

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

    @Slot(result="QVariantList")
    def listFilters(self):
        return self._adapter.list_filters(self._cwd)

    @Slot(str, result="QVariantMap")
    def openPerspective(self, path: str):
        target = str(path or "").strip() or self._cwd
        return self._adapter.perspective_open(target)

    @Slot(result="QVariantMap")
    def getPerspectiveState(self):
        return self._adapter.perspective_state()

    @Slot(str, result="QVariantMap")
    def setPerspectiveCpd(self, cpd: str):
        return self._adapter.perspective_set_cpd(cpd)

    @Slot(str, result="QVariantMap")
    def resolvePerspectiveCpd(self, cpd: str):
        return self._adapter.perspective_resolve_cpd(cpd)

    @Slot(str, result="QVariantMap")
    def resolvePerspectiveReal(self, path: str):
        return self._adapter.perspective_resolve_real(path)

    @Slot(str, result="QVariantList")
    def listPerspectiveDir(self, cpd: str):
        return self._adapter.perspective_list_dir(cpd)

    @Slot(str, result="QVariantList")
    def listPerspectiveTemplates(self, cpd: str):
        return self._adapter.perspective_list_templates(cpd)

    @Slot(result=bool)
    def clearPerspective(self) -> bool:
        return self._adapter.perspective_clear()

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
        self._cwd = str(target)
        self._adapter.update_context(self._cwd)
        self.cwdChanged.emit(self._cwd)
        self.dataChanged.emit()
        return True

    @Slot(str, result=bool)
    def enterFolder(self, path: str) -> bool:
        return self.setCwd(path)

    @Slot(str, str, result=bool)
    def moveTo(self, source_path: str, target_dir: str) -> bool:
        ok = self._adapter.move_entry(source_path, target_dir)
        if ok:
            self.dataChanged.emit()
        return ok

    @Slot(str, result=bool)
    def moveToClipboard(self, source_path: str) -> bool:
        self._ensure_clipboard_dir()
        ok = self._adapter.move_entry(source_path, self._clipboard)
        if ok:
            self.dataChanged.emit()
        return ok

    @Slot(str, result=str)
    def createFolder(self, name: str) -> str:
        created = self._adapter.create_folder(self._cwd, name) or ""
        if created:
            self.dataChanged.emit()
        return created

    @Slot(str, result=str)
    def createNote(self, name: str) -> str:
        created = self._adapter.create_note(self._cwd, name) or ""
        if created:
            self.dataChanged.emit()
        return created

    @Slot(str, result=str)
    def createClipboardNote(self, name: str) -> str:
        self._ensure_clipboard_dir()
        created = self._adapter.create_note(self._clipboard, name) or ""
        if created:
            self.dataChanged.emit()
        return created

    @Slot()
    def refreshAll(self) -> None:
        self._adapter.update_context(self._cwd)
        self.dataChanged.emit()

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

    def update_context(self, path: str) -> None:
        self._api.update_context(path)

    def get_myos_root(self) -> Optional[str]:
        return self._api.get_myos_root()

    def list_children(self, path: str) -> list:
        return self._api.list_children(path, False)

    def list_templates(self, path: str) -> list:
        return self._api.list_templates(path, True)

    def list_entries(self, path: str) -> list:
        return self._api.list_entries(path)

    def list_filters(self, path: str) -> list:
        return self._api.list_filters(path)

    def perspective_open(self, path: str, perspective_id: str = "flipped") -> dict:
        return self._api.perspective_open(path, perspective_id)

    def perspective_state(self) -> dict:
        return self._api.perspective_state()

    def perspective_set_cpd(self, cpd: str) -> dict:
        return self._api.perspective_set_cpd(cpd)

    def perspective_resolve_cpd(self, cpd: str) -> dict:
        return self._api.perspective_resolve_cpd(cpd)

    def perspective_resolve_real(self, path: str) -> dict:
        return self._api.perspective_resolve_real(path)

    def perspective_list_dir(self, cpd: str = "") -> list:
        return self._api.perspective_list_dir(cpd)

    def perspective_list_templates(self, cpd: str = "") -> list:
        return self._api.perspective_list_templates(cpd)

    def perspective_clear(self) -> bool:
        return self._api.perspective_clear()

    def get_effective_project_color(self, path: str) -> Optional[str]:
        return self._api.get_effective_project_color(path)

    def move_entry(self, source_path: str, target_dir: str) -> bool:
        return self._api.move_entry(source_path, target_dir)

    def create_folder(self, path: str, name: str) -> Optional[str]:
        return self._api.create_folder(path, name)

    def create_note(self, path: str, name: str) -> Optional[str]:
        return self._api.create_note(path, name)


def main() -> int:
    os.environ.setdefault("MYOS_MD_USE_POSTFIX", "1")
    start_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())

    app = QGuiApplication(sys.argv)
    app.setApplicationName("SunTree")
    icon_path = REPO_ROOT / "Scope" / "Theme" / "icons" / "folder.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    api = ScopeApi(start_path)
    adapter = MyOSBackendAdapter(api)
    backend = SunTreeBackend(adapter, start_path)
    hotkey = os.environ.get("SUNTREE_HOTKEY", "<ctrl>+<alt>+space")
    hotkey_service = GlobalHotkeyService(hotkey)
    requested_hidden = os.environ.get("SUNTREE_START_HIDDEN", "1") not in {"0", "false", "no"}
    start_hidden = requested_hidden and hotkey_service.status() == "active"

    engine = QQmlApplicationEngine()
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
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
