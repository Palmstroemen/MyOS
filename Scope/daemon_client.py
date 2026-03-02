"""
Client for the perspective daemon (Unix socket).
When the daemon is running, Scope delegates perspective_* calls to this client.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _default_socket_path() -> str:
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    if runtime:
        return str(Path(runtime) / "myos-perspective.sock")
    return str(Path.home() / ".config" / "myos" / "perspective.sock")


def _send_request(socket_path: str, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    import socket
    req = {"method": method}
    if params is not None:
        req["params"] = params
    line = json.dumps(req, ensure_ascii=False) + "\n"
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(socket_path)
        sock.sendall(line.encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        sock.close()
        resp = json.loads(buf.decode("utf-8", errors="replace").strip())
        if not resp.get("ok"):
            return None
        return resp.get("result")
    except Exception:
        return None


class DaemonClient:
    """Client that talks to the perspective daemon over Unix socket."""

    def __init__(self, socket_path: Optional[str] = None) -> None:
        self._socket_path = socket_path or os.environ.get("MYOS_DAEMON_SOCKET") or _default_socket_path()

    def ping(self) -> bool:
        result = _send_request(self._socket_path, "ping")
        return result is not None and result.get("pong") is True

    def perspective_open(self, path: str, perspective_id: str = "flipped") -> Dict[str, Any]:
        result = _send_request(
            self._socket_path,
            "perspective_open",
            {"path": path, "perspective_id": perspective_id},
        )
        if result is None:
            return {"active": False, "ok": False}
        return result

    def perspective_set_cpd(self, cpd: str) -> Dict[str, Any]:
        result = _send_request(self._socket_path, "perspective_set_cpd", {"cpd": cpd})
        if result is None:
            return {"ok": False}
        return result

    def perspective_state(self) -> Dict[str, Any]:
        result = _send_request(self._socket_path, "perspective_state")
        if result is None:
            return {"active": False}
        return result

    def perspective_list_dir(self, cpd: str = "", show_hidden: bool = False) -> List[Dict[str, Any]]:
        result = _send_request(
            self._socket_path,
            "perspective_list_dir",
            {"cpd": cpd, "show_hidden": show_hidden},
        )
        if result is None:
            return []
        return result if isinstance(result, list) else []

    def perspective_list_templates(self, cpd: str = "", show_hidden: bool = False) -> List[Dict[str, Any]]:
        result = _send_request(
            self._socket_path,
            "perspective_list_templates",
            {"cpd": cpd, "show_hidden": show_hidden},
        )
        if result is None:
            return []
        return result if isinstance(result, list) else []


def connect(socket_path: Optional[str] = None) -> Optional[DaemonClient]:
    """Try to connect to the daemon. Returns a DaemonClient if daemon responds to ping, else None."""
    client = DaemonClient(socket_path)
    if client.ping():
        return client
    return None
