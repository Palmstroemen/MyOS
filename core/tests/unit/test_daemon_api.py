"""The perspective daemon: one lens session per projects root, served over a socket.

Requests are handled directly here (no socket, no FUSE). See "Designdocument Perspective
Resolver MVP.md", A6: Scope, SunTree and the CLI only ask the daemon."""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from daemon.api import decode_request, decode_response, encode_request, encode_response
from daemon.perspective_daemon import DaemonState, _end_when_free, _handle_request, socket_path_for


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def state(tmp_path):
    (tmp_path / "Templates" / "Standard" / "04_Finanz").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    _project(root / "Musikstudio")
    _project(root / "Reisen")
    (root / "Reisen" / "lose.pdf").write_text("x")
    return DaemonState(projects_root=str(root), mount_point=str(tmp_path / "Perspektiven"))


def _ask(state, method, **params):
    return decode_response(_handle_request(state, {"method": method, "params": params}))


def test_ping_names_the_projects_root_and_the_drive(state, tmp_path):
    reply = _ask(state, "ping")

    assert reply["ok"] and reply["result"] == {
        "pong": True, "projects_root": str((tmp_path / "Projekte").resolve()),
        "mount_point": str(tmp_path / "Perspektiven")}


def test_the_lens_through_the_daemon(state, tmp_path):
    root = tmp_path / "Projekte"
    assert _ask(state, "set_cwd", path=str(root / "Musikstudio"))["result"]["active"] is False

    on = _ask(state, "put_on", lens=["04_Finanz"])["result"]
    assert on["active"] and on["cpd"] == "/04_Finanz/Projekte/Musikstudio"
    assert on["cwd"] == str((root / "Musikstudio").resolve())

    moved = _ask(state, "move_to_project", project=["Reisen"])["result"]
    assert moved["target"] == str((root / "Reisen" / "04_Finanz").resolve())
    listing = _ask(state, "listing")["result"]
    assert listing["fallback"] and [e["name"] for e in listing["entries"]] == ["lose.pdf"]

    off = _ask(state, "take_off")["result"]
    assert off["active"] is False and off["cwd"] == str((root / "Musikstudio").resolve())


def test_mistakes_are_reported(state):
    assert _ask(state, "put_on", lens=["04_Finanz"]) == {"ok": False, "error": "no CWD"}
    assert _ask(state, "nonsense")["ok"] is False
    assert _ask(state, "set_cwd", path="/etc")["ok"] is False


def test_one_socket_per_projects_root(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    a, b = socket_path_for(tmp_path / "A" / "Projekte"), socket_path_for(tmp_path / "B" / "Projekte")

    assert a != b and Path(a).parent == tmp_path and socket_path_for(tmp_path / "A" / "Projekte") == a


def test_protocol_roundtrip():
    assert decode_request(encode_request("put_on", {"lens": ["04_Finanz"]})) == {"method": "put_on", "params": {"lens": ["04_Finanz"]}}
    assert json.loads(encode_response(True, {"x": 1})) == {"ok": True, "result": {"x": 1}}
    assert decode_request("not json") is None


def _ending(state, answers):
    """_end_when_free in a thread, with an unmount answering from answers (True: done)."""
    calls = []

    def unmount():
        calls.append(state.shutdown_requested)
        return answers(len(calls))

    thread = threading.Thread(target=_end_when_free, args=(state, unmount, 0.01), daemon=True)
    thread.start()
    return thread, calls


def test_shutdown_waits_while_the_drive_is_busy(state):
    # A program (LibreOffice) still has a file open: unmounting is refused, the drive stays
    # and it is tried again until it is free - never killed, never lazily unmounted.
    thread, calls = _ending(state, lambda n: n >= 3)
    thread.join(0.2)
    assert calls == [] and thread.is_alive()  # nothing happens before Scope asks

    assert _ask(state, "shutdown")["ok"]
    thread.join(2)
    assert not thread.is_alive() and len(calls) == 3


def test_a_client_coming_back_cancels_the_shutdown(state):
    # Scope closed while the drive was busy, and a new Scope connected: the drive stays.
    cancelled = threading.Event()

    def answers(n):
        if n == 2:
            _ask(state, "ping")
            cancelled.set()
        return False

    thread, calls = _ending(state, answers)
    _ask(state, "shutdown")
    assert cancelled.wait(2)
    thread.join(0.2)
    assert thread.is_alive() and len(calls) == 2 and not state.shutdown_requested
