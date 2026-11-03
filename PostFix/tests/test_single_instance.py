"""One PostFix for all notes (PostFix/single_instance.py): a second start hands its note to the
PostFix already running and ends; that one opens it in a window of its own. So all notes share
one program (and later one editor) instead of each starting its own."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from PostFix import single_instance as si

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def app():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QApplication.instance() or QApplication([])


def _spin(app, seconds):
    end = time.time() + seconds
    while time.time() < end:
        app.processEvents()
        time.sleep(0.01)


def test_one_postfix_per_user_display_and_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "a"))
    first = si.server_name()
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "b"))  # e.g. a test, or the test machine's harness
    assert si.server_name() != first
    monkeypatch.setenv("DISPLAY", ":1")
    assert si.server_name() != first
    assert first.startswith("myos-postfix-")


def test_without_a_running_postfix_nothing_is_handed_over(app, tmp_path):
    assert not si.hand_over(f"myos-postfix-test-{os.getpid()}-none", str(tmp_path / "x.md"), timeout_ms=300)


def test_a_second_start_hands_its_note_over(app, tmp_path):
    name = f"myos-postfix-test-{os.getpid()}"
    note = tmp_path / "Zweite Notiz.md"
    note.write_text("# Zweite\n", encoding="utf-8")
    server = si.InstanceServer(name)
    assert server.listen()
    received = []
    server.openRequested.connect(received.append)
    client = subprocess.Popen(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0, sys.argv[1]);"
         "from PySide6.QtCore import QCoreApplication; app = QCoreApplication([]);"
         "from PostFix.single_instance import hand_over;"
         "print('ok' if hand_over(sys.argv[2], sys.argv[3]) else 'no')",
         str(REPO), name, str(note)],
        stdout=subprocess.PIPE, text=True)
    deadline = time.time() + 10
    while client.poll() is None and time.time() < deadline:
        _spin(app, 0.05)
    assert client.stdout.read().strip() == "ok"
    assert received == [str(note.resolve())]
    server.close()


def test_only_existing_markdown_notes_are_taken(app, tmp_path):
    # Security: whatever connects only gets an existing .md opened - no other file, no command.
    note = tmp_path / "Notiz.md"
    note.write_text("x", encoding="utf-8")
    assert si.accepted_path(str(note)) == str(note.resolve())
    assert si.accepted_path(None) is None  # a new, empty note
    for bad in (str(tmp_path / "fehlt.md"), str(tmp_path), "/etc/passwd", "relative.md", 42):
        assert si.accepted_path(bad) is False


def test_the_connection_is_for_this_user_only(app):
    server = si.InstanceServer(f"myos-postfix-test-{os.getpid()}-perm")
    assert server.listen()
    from PySide6.QtNetwork import QLocalServer
    assert server.server.socketOptions() == QLocalServer.UserAccessOption
    server.close()


def test_a_second_start_opens_its_note_in_the_running_postfix(tmp_path, monkeypatch):
    # The whole way, as Scope or a double click start PostFix: two starts, one program.
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", XDG_CONFIG_HOME=str(tmp_path / "config"))
    first, second = tmp_path / "Erste.md", tmp_path / "Zweite.md"
    first.write_text("# Erste\n", encoding="utf-8")
    second.write_text("# Zweite\n", encoding="utf-8")
    running = subprocess.Popen([sys.executable, str(REPO / "PostFix" / "cli.py"), str(first)],
                               env=env, stderr=subprocess.PIPE, text=True)
    try:
        time.sleep(3)  # until it listens
        started = time.time()
        handed = subprocess.run([sys.executable, str(REPO / "PostFix" / "cli.py"), str(second)],
                                env=env, timeout=30)
        assert handed.returncode == 0 and time.time() - started < 10  # ended at once
        time.sleep(1)
    finally:
        running.terminate()  # as "Bin fertig" on the test machine: closes, saves, cleans up
        log = running.communicate(timeout=10)[1]
    assert f"opened {second.resolve()}" in log
    assert running.returncode == 0
    monkeypatch.setenv("XDG_CONFIG_HOME", env["XDG_CONFIG_HOME"])
    assert not Path(si.socket_path(si.server_name())).exists()  # no connection left behind


def test_the_connection_lies_in_the_users_private_runtime_folder(monkeypatch, tmp_path):
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    assert Path(si.socket_path("myos-postfix-x")).parent == runtime


def test_handing_over_needs_no_qt(tmp_path):
    # A later start only hands its note over: plain Python, quick, before loading anything of Qt.
    code = ("import sys; sys.path.insert(0, sys.argv[1]); import PostFix.single_instance as si;"
            "si.hand_over('myos-postfix-none', None, timeout_ms=100);"
            "print(any(m.startswith('PySide6') for m in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code, str(REPO)], capture_output=True, text=True).stdout.strip()
    assert out == "False"
