"""
Perspective daemon: holds state (project_root, CPD), serves Unix-socket API,
runs FUSE with live-updated context.
"""

from __future__ import annotations

import atexit
import os
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

_DAEMON_LOG_LOCK = threading.Lock()
_DAEMON_LOG_FILE: Optional[Any] = None
_DAEMON_LOG_PID: Optional[int] = None


def _daemon_log_path(socket_path: str) -> Path:
    """Log file next to socket: XDG_RUNTIME_DIR/perspective-daemon.log or ~/.config/myos/perspective-daemon.log."""
    return Path(socket_path).resolve().parent / "perspective-daemon.log"


def _daemon_log(msg: str, log_path: Optional[Path] = None) -> None:
    """Append one line to the daemon log (timestamp, pid, msg). Thread-safe."""
    global _DAEMON_LOG_FILE
    with _DAEMON_LOG_LOCK:
        try:
            if log_path is not None and _DAEMON_LOG_FILE is None:
                _DAEMON_LOG_FILE = open(log_path, "a", encoding="utf-8")
            if _DAEMON_LOG_FILE is not None:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                pid = os.getpid()
                _DAEMON_LOG_FILE.write(f"{ts} pid={pid} {msg}\n")
                _DAEMON_LOG_FILE.flush()
        except Exception:
            pass


def _daemon_log_close() -> None:
    """Write 'ended' and close log file. Safe to call multiple times."""
    global _DAEMON_LOG_FILE
    with _DAEMON_LOG_LOCK:
        if _DAEMON_LOG_FILE is not None:
            try:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                pid = os.getpid()
                _DAEMON_LOG_FILE.write(f"{ts} pid={pid} ended\n")
                _DAEMON_LOG_FILE.flush()
            except Exception:
                pass
            try:
                _DAEMON_LOG_FILE.close()
            except Exception:
                pass
            _DAEMON_LOG_FILE = None

# Run from repo root so core and daemon are importable
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.perspective_fuse import FUSE, PerspectiveFuseAdapter
from core.perspective_resolver import PerspectiveContext, perspective_open, perspective_open_from_cpd
from core.scope_api import ScopeApi, find_project_root

from daemon.api import decode_request, encode_response, encode_request


def _default_socket_path() -> str:
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    if runtime:
        return str(Path(runtime) / "myos-perspective.sock")
    return str(Path.home() / ".config" / "myos" / "perspective.sock")


class DaemonState:
    def __init__(
        self,
        project_root: str,
        cpd: str = "/Projekte",
        mount_point: str = "",
    ) -> None:
        self._lock = threading.Lock()
        self._project_root = project_root
        self._cpd = cpd
        self._mount_point = mount_point
        self._cached_ctx: Optional[PerspectiveContext] = None
        self._api: Optional[ScopeApi] = None
        self._shutdown_requested = False

    @property
    def project_root(self) -> str:
        with self._lock:
            return self._project_root

    @property
    def cpd(self) -> str:
        with self._lock:
            return self._cpd

    @property
    def mount_point(self) -> str:
        with self._lock:
            return self._mount_point

    @property
    def shutdown_requested(self) -> bool:
        with self._lock:
            return self._shutdown_requested

    def set_cpd(self, project_root: Optional[str], cpd: str) -> None:
        with self._lock:
            if project_root is not None:
                self._project_root = project_root
            self._cpd = (cpd or "").strip() or "/Projekte"

    def set_mount_point(self, mount_point: str) -> None:
        with self._lock:
            self._mount_point = mount_point

    def request_shutdown(self) -> None:
        with self._lock:
            self._shutdown_requested = True

    def get_context(self) -> PerspectiveContext:
        with self._lock:
            root = self._project_root
            cpd = self._cpd or "/Projekte"
        try:
            ctx = perspective_open_from_cpd(project_root=root, cpd=cpd)
            with self._lock:
                self._cached_ctx = ctx
            return ctx
        except Exception:
            with self._lock:
                if self._cached_ctx is not None:
                    return self._cached_ctx
            raise

    def _ensure_api(self) -> ScopeApi:
        with self._lock:
            root = self._project_root
        if self._api is None:
            self._api = ScopeApi(start_path=root)
        return self._api

    def _sync_ctx(self) -> bool:
        api = self._ensure_api()
        try:
            ctx = self.get_context()
            api._perspective_ctx = ctx
            return True
        except Exception:
            return False

    def perspective_state(self) -> Dict[str, Any]:
        if not self._sync_ctx():
            return {
                "active": False,
                "perspectiveId": "",
                "projectRoot": self.project_root,
                "cpd": self.cpd,
                "cwdReal": "",
                "role": "",
                "templateHead": [],
                "templateRoot": "",
                "templateRoots": [],
            }
        return self._api.perspective_state()

    def perspective_list_dir(self, cpd: str = "", show_hidden: bool = False) -> list:
        if not self._sync_ctx():
            return []
        return self._api.perspective_list_dir(cpd or self.cpd, show_hidden)

    def perspective_list_templates(self, cpd: str = "", show_hidden: bool = False) -> list:
        if not self._sync_ctx():
            return []
        return self._api.perspective_list_templates(cpd or self.cpd, show_hidden)


def _handle_request(state: DaemonState, req: Dict[str, Any]) -> str:
    method = (req.get("method") or "").strip()
    params = req.get("params") or {}

    if method == "ping":
        return encode_response(True, {"pong": True})

    if method == "shutdown":
        state.request_shutdown()
        return encode_response(True, {"shutdown": True})

    if method == "set_cpd":
        project_root = params.get("project_root")
        if project_root is not None:
            project_root = str(project_root).strip()
        cpd = str(params.get("cpd", "")).strip() or "/Projekte"
        try:
            state.set_cpd(project_root, cpd)
            ctx = state.get_context()
            return encode_response(True, {"cpd": ctx.cpd, "ok": True})
        except Exception as e:
            return encode_response(False, error=str(e))

    if method == "get_state":
        try:
            ctx = state.get_context()
            active = True
            cpd = ctx.cpd
        except Exception:
            active = False
            cpd = state.cpd
        return encode_response(True, {
            "project_root": state.project_root,
            "cpd": cpd,
            "mount_point": state.mount_point,
            "active": active,
        })

    if method == "perspective_open":
        path = str(params.get("path", "")).strip()
        perspective_id = str(params.get("perspective_id") or params.get("perspectiveId") or "flipped")
        root = find_project_root(Path(path).expanduser().resolve())
        if root is None:
            return encode_response(False, result={"active": False, "ok": False}, error="missing project_root")
        try:
            ctx = perspective_open(
                perspective_id=perspective_id,
                project_root=str(root),
                start_real_path=path,
            )
            state.set_cpd(str(root), ctx.cpd)
            out = state.perspective_state()
            out["ok"] = True
            return encode_response(True, result=out)
        except Exception as e:
            return encode_response(False, error=str(e))

    if method == "perspective_set_cpd":
        cpd = str(params.get("cpd", "")).strip()
        try:
            state.set_cpd(None, cpd)
            ctx = state.get_context()
            return encode_response(True, result={"ok": True, "cpd": ctx.cpd})
        except Exception as e:
            return encode_response(True, result={"ok": False, "errorCode": "invalid_path", "message": str(e)})

    if method == "perspective_state":
        try:
            result = state.perspective_state()
            return encode_response(True, result=result)
        except Exception as e:
            return encode_response(False, error=str(e))

    if method == "perspective_list_dir":
        cpd = str(params.get("cpd", "")).strip()
        show_hidden = bool(params.get("show_hidden", False))
        try:
            result = state.perspective_list_dir(cpd, show_hidden)
            return encode_response(True, result=result)
        except Exception as e:
            return encode_response(False, error=str(e))

    if method == "perspective_list_templates":
        cpd = str(params.get("cpd", "")).strip()
        show_hidden = bool(params.get("show_hidden", False))
        try:
            result = state.perspective_list_templates(cpd, show_hidden)
            return encode_response(True, result=result)
        except Exception as e:
            return encode_response(False, error=str(e))

    return encode_response(False, error=f"unknown method: {method}")


def _run_socket_server(socket_path: str, state: DaemonState) -> None:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        Path(socket_path).parent.mkdir(parents=True, exist_ok=True)
        if Path(socket_path).exists():
            Path(socket_path).unlink()
        sock.bind(socket_path)
        sock.listen(4)
    except Exception as e:
        print(f"daemon: socket bind failed: {e}", file=sys.stderr)
        return
    while not state.shutdown_requested:
        try:
            sock.settimeout(1.0)
            conn, _ = sock.accept()
        except socket.timeout:
            continue
        except OSError:
            break
        try:
            buf = b""
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                if b"\n" in buf:
                    break
            line = buf.decode("utf-8", errors="replace").split("\n", 1)[0]
            req = decode_request(line)
            if req is None:
                resp = encode_response(False, error="invalid request")
            else:
                resp = _handle_request(state, req)
            conn.sendall(resp.encode("utf-8"))
            if req and (req.get("method") or "").strip() == "shutdown":
                break
        except Exception as e:
            try:
                conn.sendall(encode_response(False, error=str(e)).encode("utf-8"))
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    try:
        sock.close()
    except Exception:
        pass
    if state.shutdown_requested:
        os.kill(os.getpid(), signal.SIGTERM)


def _pulse_loop(log_path: Path) -> None:
    """Background thread: write a 'pulse' line every 60 seconds."""
    while True:
        time.sleep(60)
        _daemon_log("pulse", log_path=log_path)


def run_daemon(
    project_root: str,
    mount_point: str,
    socket_path: Optional[str] = None,
    foreground: bool = True,
) -> None:
    socket_path = socket_path or os.environ.get("MYOS_DAEMON_SOCKET") or _default_socket_path()
    project_root = str(Path(project_root).expanduser().resolve())
    mount_point = str(Path(mount_point).expanduser().resolve())

    log_path = _daemon_log_path(socket_path)
    _daemon_log(f"started mount_point={mount_point!r} socket_path={socket_path!r}", log_path=log_path)

    pulse_thread = threading.Thread(target=_pulse_loop, args=(log_path,), daemon=True)
    pulse_thread.start()

    atexit.register(_daemon_log_close)

    state = DaemonState(project_root=project_root, cpd="/Projekte", mount_point=mount_point)

    def context_provider() -> PerspectiveContext:
        return state.get_context()

    if FUSE is None:
        raise RuntimeError("fusepy is not installed")
    adapter = PerspectiveFuseAdapter(
        context_provider=context_provider,
    )
    state.set_mount_point(mount_point)

    server_thread = threading.Thread(target=_run_socket_server, args=(socket_path, state), daemon=False)
    server_thread.start()

    def on_sigterm(_signum: int, _frame: Any) -> None:
        _daemon_log_close()
        sys.exit(0)
    signal.signal(signal.SIGTERM, on_sigterm)

    try:
        FUSE(adapter, mount_point, foreground=foreground, allow_other=False)
    finally:
        _daemon_log_close()
