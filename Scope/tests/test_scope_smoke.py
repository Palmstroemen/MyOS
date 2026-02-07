from __future__ import annotations

import os
from pathlib import Path

import pytest

try:
    from PySide6.QtCore import QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
except Exception:  # pragma: no cover
    pytest.skip("PySide6 not installed", allow_module_level=True)


def test_scope_qml_loads_without_errors():
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        pytest.skip("No display available for QML")

    messages = []

    def handler(_mode, _context, message):
        if "Error" in message or "Type" in message:
            messages.append(message)

    qInstallMessageHandler(handler)

    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QQmlApplicationEngine()
    qml_path = Path(__file__).resolve().parents[1] / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    assert engine.rootObjects(), "QML failed to load"
    assert not messages, "\n".join(messages)
