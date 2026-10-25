"""
One program's line to the lens: Scope and SunTree both use it.

The lens lives in the perspective daemon of the projects root (daemon/perspective_daemon.py);
programs only ask it and build no lens paths themselves. A program connects to the daemon
of its own root and starts it when none runs. Without a daemon it asks a session of its own
(then no other program sees that lens). The Desk follows every move of the lens
(Designdocument Perspective Resolver MVP.md, A5 and A6). The programs share the place too:
turned to, a program follows where the other one went (follow).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from daemon.client import LocalSession, connect as connect_daemon

REPO_ROOT = Path(__file__).resolve().parents[1]


def spawn_daemon(projects_root: Path) -> Optional[subprocess.Popen]:
    """Start the daemon of projects_root; its drive appears as "Perspektiven" next to
    "Projekte"."""
    mount_point = projects_root.parent / "Perspektiven"
    try:
        mount_point.mkdir(exist_ok=True)
        return subprocess.Popen(
            [sys.executable, "-m", "daemon", "--projects-root", str(projects_root), "--mount-point", str(mount_point)],
            cwd=str(REPO_ROOT),
            env=os.environ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return None


def _find_project_root(path: Path) -> Optional[Path]:
    from core.scope_api import find_project_root

    return find_project_root(path)


class LensLink:
    # What a program may ask (the daemon also knows ping and shutdown).
    REQUESTS = frozenset({"state", "set_cwd", "put_on", "look_at", "go_into", "take_off",
                          "move_to", "move_to_project", "to_shelf", "into_shelf", "listing"})
    # Requests that may change the Desk (set_cwd does not: the program sets its context after it).
    MOVES = frozenset({"put_on", "look_at", "go_into", "take_off", "move_to", "move_to_project",
                       "to_shelf", "into_shelf"})

    def __init__(self, api, *, start_daemon: bool,
                 connect: Callable[[Path], Any] = connect_daemon,
                 spawn: Callable[[Path], Any] = spawn_daemon,
                 wait: float = 3.0) -> None:
        """api: the program's ScopeApi (its projects root and the Desk's context)."""
        self._api = api
        self._client = None
        self._process = None
        self._session = None
        self._place = ""  # the session's CWD as this program last set or saw it
        root = api.projects_root()
        self.projects_root: Optional[Path] = Path(root) if root is not None else None
        if self.projects_root is None:
            return
        self._client = connect(self.projects_root)
        if self._client is None and start_daemon:
            self._process = spawn(self.projects_root)
            if self._process is not None:
                for _ in range(max(1, int(wait / 0.1))):  # until it answers
                    if wait:
                        time.sleep(0.1)
                    self._client = connect(self.projects_root)
                    if self._client is not None:
                        break
        self._session = self._client or LocalSession(self.projects_root)

    @property
    def started_daemon(self) -> bool:
        return self._process is not None

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A lens request: {ok, result | error}; result describes the lens afterwards."""
        if self._session is None:
            return {"ok": False, "error": "no lens here"}
        if method not in self.REQUESTS:
            return {"ok": False, "error": f"no lens request: {method}"}
        answer = self._session.call(method, **dict(params or {}))
        if answer.get("ok"):
            self._place = str((answer.get("result") or {}).get("cwd") or self._place)
        if method in self.MOVES and answer.get("ok"):
            # The Desk follows the lens; ✕ in the same project changes no place (A5). Without
            # the lens the project's Desk applies, as for the place, never a department's.
            lens_state = answer.get("result") or {}
            cwd = str(lens_state.get("cwd") or "")
            path = lens_state.get("project_dir") or (_find_project_root(Path(cwd)) if cwd else None)
            if path:
                self._update_context(str(path), lens_state)
        return answer

    def follow(self) -> Optional[str]:
        """Where the other program went since this one last set or saw the place: the new
        CWD, or None. A place of this program the session refused (outside the projects)
        is not left for the session's old one."""
        before = self._place
        cwd = str((self.call("state").get("result") or {}).get("cwd") or "")  # sees it now
        return cwd if cwd and cwd != before else None

    def bear(self) -> Dict[str, Any]:
        """Bear the lens' folder where the department folder is missing. The program checks
        first that the user may write there."""
        if self._session is None:
            return {"ok": False, "error": "no lens here"}
        return self._session.call("bear")

    def update_context(self, path: str) -> None:
        """The program stands at path: the desktop follows (Desk.md)."""
        self._update_context(path, self.call("state").get("result") or {})

    def _update_context(self, path: str, lens_state: Dict[str, Any]) -> None:
        # With a lens on, its Desk overrules the project's and changes of the desktop are
        # kept in the template (A5).
        # Security: the template is written only where the file system lets the user
        # write it (its ACLs.md governs the projects made from it, not the template).
        if lens_state.get("active") and lens_state.get("project_dir"):
            self._api.update_context(path, str(lens_state.get("desk") or ""), str(lens_state.get("desk_save") or ""))
        else:
            self._api.update_context(path)

    def close(self) -> None:
        """The drive ends with the program that started it. Only asked, never killed: a
        killed daemon leaves a dead drive behind. While a program still has a file open on
        the drive, the daemon waits and unmounts once it is free."""
        if self._process is not None and self._client is not None:
            try:
                self._client.request_shutdown(timeout=1.0)
            except Exception:
                pass
        self._process = None
        self._client = None
