#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from PySide6.QtCore import QObject, Slot, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core.scope_api import ScopeApi


class Backend(QObject):
    def __init__(self, api: ScopeApi) -> None:
        super().__init__()
        self._api = api

    @Slot(str, result="QStringList")
    def listChildren(self, path: str):
        return self._api.list_children(path)

    @Slot(result=str)
    def getStartPath(self) -> str:
        return self._api.get_start_path()

    @Slot(result=str)
    def getProjectRoot(self) -> str:
        return self._api.get_project_root() or ""


def main() -> int:
    start_path = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())
    api = ScopeApi(start_path)
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    ctx = engine.rootContext()
    ctx.setContextProperty("backend", Backend(api))
    ctx.setContextProperty("scopeStartPath", api.get_start_path())
    ctx.setContextProperty("scopeProjectRoot", api.get_project_root() or "")

    qml_path = Path(__file__).with_name("main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
