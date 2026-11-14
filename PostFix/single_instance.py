"""One PostFix for all notes: a second start (Scope, a double click, an exercise link) hands its
note to the PostFix already running and ends; that one opens the note in a window of its own.
All notes then share one program - and later one editor (CodeMirror in QtWebEngine), which a
program per note would make too heavy.

One PostFix per user, display and settings folder (XDG_CONFIG_HOME): tests and test harnesses
with settings of their own get a PostFix of their own, never the user's.
"""

import hashlib
import json
import os
import socket
import tempfile
from pathlib import Path
from typing import Optional, Union

from core.brand import file_name


def server_name() -> str:
    """The name the running PostFix listens under."""
    config = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    key = "|".join([str(os.getuid()), os.environ.get("DISPLAY", ""), os.environ.get("WAYLAND_DISPLAY", ""),
                    str(Path(config).expanduser().resolve())])
    return file_name("postfix-") + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def socket_path(name: str) -> str:
    """Where the running PostFix listens: the user's private runtime folder (only the user can
    enter it), else the temporary folder."""
    folder = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
    return os.path.join(folder, name + ".sock")


def accepted_path(value) -> Union[str, None, bool]:
    """The note to open as an absolute path, None for a new empty note, False if refused."""
    if value is None:
        return None
    # Security: whatever connects gets nothing but an existing Markdown note opened - no other
    # file, no folder, no relative path resolved against PostFix's own folder.
    if not isinstance(value, str) or not os.path.isabs(value):
        return False
    path = Path(value).resolve()
    if path.suffix.lower() != ".md" or not path.is_file():
        return False
    return str(path)


def hand_over(name: str, path: Optional[str], timeout_ms: int = 1500) -> bool:
    """Give path to the PostFix running under name; False when none runs (or it refused).
    Plain Python, no Qt: a later start hands over quickly and ends."""
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout_ms / 1000)
            connection.connect(socket_path(name))
            connection.sendall((json.dumps({"open": path}) + "\n").encode("utf-8"))
            answer = b""
            while not answer.endswith(b"\n"):
                chunk = connection.recv(64)
                if not chunk:
                    break
                answer += chunk
    except OSError:
        return False
    return answer.strip() == b"ok"


_SERVER_CLASS = None


def __getattr__(attribute):
    # The server needs Qt; only the running PostFix makes one, so Qt loads only there.
    global _SERVER_CLASS
    if attribute == "InstanceServer":
        if _SERVER_CLASS is None:
            _SERVER_CLASS = _server_class()
        return _SERVER_CLASS
    raise AttributeError(attribute)


def _server_class():
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtNetwork import QLocalServer

    class InstanceServer(QObject):
        """Listens for later starts; openRequested(path or None) for each accepted note."""

        openRequested = Signal(object)

        def __init__(self, name: str, parent=None):
            super().__init__(parent)
            self.name = name
            self.path = socket_path(name)
            self.server = QLocalServer(self)
            # Security: only this user may hand notes over (the socket file is owner-only).
            self.server.setSocketOptions(QLocalServer.UserAccessOption)
            self.server.newConnection.connect(self._accept)

        def listen(self) -> bool:
            if self.server.listen(self.path):
                return True
            # Left over from a PostFix that ended without cleaning up (hand_over found nobody).
            QLocalServer.removeServer(self.path)
            return self.server.listen(self.path)

        def close(self):
            self.server.close()

        def _accept(self):
            while self.server.hasPendingConnections():
                socket = self.server.nextPendingConnection()
                socket.readyRead.connect(lambda s=socket: self._read(s))

        def _read(self, socket):
            if not socket.canReadLine():
                return
            line = bytes(socket.readLine().data()).decode("utf-8", errors="replace")
            try:
                path = accepted_path(json.loads(line).get("open"))
            except (ValueError, AttributeError):
                path = False
            socket.write(b"ok\n" if path is not False else b"refused\n")
            socket.flush()
            socket.disconnectFromServer()
            if path is not False:
                self.openRequested.emit(path)

    return InstanceServer
