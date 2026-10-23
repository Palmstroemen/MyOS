"""
Client for the perspective daemon (Unix socket; daemon/perspective_daemon.py).

One daemon serves one projects root: it keeps the lens session and the "Perspektiven"
drive. A client talks only to the daemon of its own projects root.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from daemon.api import decode_response
from daemon.perspective_daemon import DaemonState, _handle_request, socket_path_for


def _send_request(socket_path: str, method: str, params: Optional[Dict[str, Any]] = None,
                  timeout: float = 5.0) -> Dict[str, Any]:
    """The daemon's whole reply ({ok, result} or {ok: False, error})."""
    import socket

    req: Dict[str, Any] = {"method": method}
    if params is not None:
        req["params"] = params
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(socket_path)
        sock.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
        sock.close()
        reply = json.loads(buf.decode("utf-8", errors="replace").strip())
        return reply if isinstance(reply, dict) else {"ok": False, "error": "invalid reply"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


class DaemonClient:
    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path

    def ping(self) -> Optional[Dict[str, Any]]:
        """{pong, projects_root, mount_point}, or None when no daemon answers."""
        reply = _send_request(self.socket_path, "ping", timeout=1.0)
        return reply.get("result") if reply.get("ok") else None

    def call(self, method: str, **params: Any) -> Dict[str, Any]:
        """A lens request (state, listing, set_cwd, put_on, ...): {ok, result | error}."""
        return _send_request(self.socket_path, method, params)

    def request_shutdown(self, timeout: float = 1.0) -> bool:
        """Ask the daemon to end (it unmounts its drive)."""
        return bool(_send_request(self.socket_path, "shutdown", timeout=timeout).get("ok"))


class LocalSession:
    """The same answers as a daemon, from a session in this process: for when none runs
    (tests; no drive then). Other programs do not see this lens."""

    def __init__(self, projects_root: Union[str, Path]) -> None:
        self._state = DaemonState(projects_root=str(Path(projects_root).expanduser().resolve()))

    def call(self, method: str, **params: Any) -> Dict[str, Any]:
        return decode_response(_handle_request(self._state, {"method": method, "params": params}))


def connect(projects_root: Union[str, Path]) -> Optional[DaemonClient]:
    """The daemon of projects_root, if one runs (another root's daemon is never used)."""
    root = str(Path(projects_root).expanduser().resolve())
    client = DaemonClient(socket_path_for(root))
    info = client.ping()
    if info and info.get("projects_root") == root:
        return client
    return None
