"""
Perspective daemon: one lens session per projects root (core/perspective_session.py),
served over a Unix socket, and the "Perspektiven" FUSE drive (core/perspective_fuse.py).

See "Designdocument Perspective Resolver MVP.md", A6: the lens' state lives only here;
Scope, SunTree and the CLI ask. The drive shows the whole turned tree, independent of
the lens. Each projects root has its own socket, so a client finds the daemon of its root.
"""

from __future__ import annotations

import atexit
import hashlib
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

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

from core.perspective_fuse import FUSE, mount_perspective_drive
from core.perspective_session import PerspectiveSession

from daemon.api import decode_request, encode_response, encode_request


def socket_path_for(projects_root: Union[str, Path]) -> str:
    """The socket of the daemon serving projects_root (one per root)."""
    key = hashlib.sha1(str(Path(projects_root).expanduser().resolve()).encode("utf-8")).hexdigest()[:12]
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    base = Path(runtime) if runtime else Path.home() / ".config" / "myos"
    return str(base / f"myos-perspective-{key}.sock")


class DaemonState:
    """The lens session of one projects root, and whether the daemon is asked to end."""

    def __init__(self, projects_root: str, mount_point: str = "") -> None:
        self._lock = threading.Lock()
        self.session = PerspectiveSession(projects_root)
        self.projects_root = str(self.session.projects_root)
        self.mount_point = mount_point
        self._shutdown = threading.Event()

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown.is_set()

    def request_shutdown(self) -> None:
        with self._lock:
            self._shutdown.set()

    def cancel_shutdown(self) -> None:
        """A client came back while the drive was still busy: the daemon stays."""
        with self._lock:
            self._shutdown.clear()

    def wait_for_shutdown(self) -> None:
        self._shutdown.wait()

    # --- the lens (Part A, A3) ---------------------------------------------------------

    def act(self, action: Callable[[PerspectiveSession], Any]) -> Dict[str, Any]:
        """Run a lens action and describe the lens afterwards (ValueError: a mistake)."""
        with self._lock:
            action(self.session)
            return self._describe()

    def describe(self) -> Dict[str, Any]:
        with self._lock:
            return self._describe()

    def listing(self) -> Dict[str, Any]:
        with self._lock:
            view = self.session.listing()
        return {
            "shown": str(view.shown),
            "fallback": view.fallback,
            "entries": [{"name": p.name, "path": str(p), "isDir": p.is_dir()} for p in view.entries],
        }

    def _describe(self) -> Dict[str, Any]:
        session = self.session
        target, desk = session.target, session.desk_file()
        return {
            "active": session.active,
            "cwd": str(session.cwd) if session.cwd else "",
            "cpd": session.cpd,
            "lens": list(session.lens),
            "project": list(session.project) if session.project is not None else None,
            "target": str(target) if target else "",
            "desk": str(desk) if desk else "",
        }


# method -> lens action taking the request's params
_ACTIONS: Dict[str, Callable[[PerspectiveSession, Dict[str, Any]], Any]] = {
    "set_cwd": lambda s, p: s.set_cwd(str(p.get("path", ""))),
    "put_on": lambda s, p: s.put_on(list(p.get("lens") or [])),
    "move_to_project": lambda s, p: s.move_to_project(list(p.get("project") or [])),
    "go_into": lambda s, p: s.go_into(str(p.get("name", ""))),
    "to_shelf": lambda s, p: s.to_shelf(),
    "into_shelf": lambda s, p: s.into_shelf(str(p.get("name", ""))),
    "take_off": lambda s, p: s.take_off(),
}


def _handle_request(state: DaemonState, req: Dict[str, Any]) -> str:
    method = (req.get("method") or "").strip()
    params = req.get("params") or {}
    if method != "shutdown" and state.shutdown_requested:
        state.cancel_shutdown()
        _daemon_log("shutdown cancelled: a client came back")
    try:
        if method == "ping":
            return encode_response(True, {"pong": True, "projects_root": state.projects_root,
                                          "mount_point": state.mount_point})
        if method == "shutdown":
            state.request_shutdown()
            return encode_response(True, {"shutdown": True})
        if method == "state":
            return encode_response(True, state.describe())
        if method == "listing":
            return encode_response(True, state.listing())
        if method in _ACTIONS:
            return encode_response(True, state.act(lambda session: _ACTIONS[method](session, params)))
    except (ValueError, OSError) as exc:
        return encode_response(False, error=str(exc))
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
    # Serves until the process ends (the drive unmounted): while the drive is still busy,
    # a new Scope can come back and cancel the shutdown.
    while True:
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


def _end_when_free(state: DaemonState, unmount: Callable[[], bool], retry_s: float = 2.0) -> None:
    """Once asked to end, unmount the drive (FUSE then returns in the main thread and the
    daemon ends). While a program still has a file open on it (LibreOffice), unmounting is
    refused: the drive stays and it is tried again - unless a client came back meanwhile.
    Never killed (that leaves a dead mount point) and never unmounted lazily: a program
    still open would then save into the empty mount point, outside the projects."""
    while True:
        state.wait_for_shutdown()
        logged = False
        while state.shutdown_requested:
            if unmount():
                return
            if not logged:
                _daemon_log("drive busy; unmounting when it is free")
                logged = True
            time.sleep(retry_s)


def _fusermount(mount_point: str) -> bool:
    """Unmount mount_point; False while it is busy."""
    try:
        return subprocess.run(["fusermount", "-u", mount_point], capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _shutdown_on_sigterm(state: DaemonState) -> None:
    """SIGTERM (e.g. logging out) ends the daemon the same way as Scope does. Python runs
    signal handlers only in the main thread, which stays inside FUSE: the signal is
    blocked there and received here instead."""
    while True:
        signal.sigwait({signal.SIGTERM})
        _daemon_log("SIGTERM; ending")
        state.request_shutdown()


def _pulse_loop(log_path: Path) -> None:
    """Background thread: write a 'pulse' line every 60 seconds."""
    while True:
        time.sleep(60)
        _daemon_log("pulse", log_path=log_path)


def run_daemon(
    projects_root: str,
    mount_point: str,
    socket_path: Optional[str] = None,
    foreground: bool = True,  # kept for callers; the drive always runs in this process
) -> None:
    projects_root = str(Path(projects_root).expanduser().resolve())
    socket_path = socket_path or os.environ.get("MYOS_DAEMON_SOCKET") or socket_path_for(projects_root)
    mount_point = str(Path(mount_point).expanduser().resolve())

    log_path = _daemon_log_path(socket_path)
    _daemon_log(f"started projects_root={projects_root!r} mount_point={mount_point!r} socket_path={socket_path!r}",
                log_path=log_path)

    atexit.register(_daemon_log_close)
    state = DaemonState(projects_root=projects_root, mount_point=mount_point)
    # Blocked before any thread starts, so every thread inherits it (see _shutdown_on_sigterm).
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    pulse_thread = threading.Thread(target=_pulse_loop, args=(log_path,), daemon=True)
    pulse_thread.start()

    if FUSE is None:
        raise RuntimeError("fusepy is not installed")
    from core.scope_api import ScopeApi  # late: heavy

    acl_api = ScopeApi(start_path=projects_root)

    def may(path: Path, action: str) -> bool:
        # Security: the drive follows the same ACL checks as Scope.
        return acl_api.acl_allows(action, path)

    # The daemon lives as long as its drive: these threads end with it.
    for target, args in ((_run_socket_server, (socket_path, state)),
                         (_end_when_free, (state, lambda: _fusermount(mount_point))),
                         (_shutdown_on_sigterm, (state,))):
        threading.Thread(target=target, args=args, daemon=True).start()

    Path(mount_point).mkdir(parents=True, exist_ok=True)
    try:
        # Always in the foreground: the daemon already is the background process, and a
        # FUSE fork would keep only this thread - the socket server would be gone.
        mount_perspective_drive(projects_root=projects_root, mount_point=mount_point, may=may, foreground=True)
    finally:
        Path(socket_path).unlink(missing_ok=True)
        _daemon_log_close()
