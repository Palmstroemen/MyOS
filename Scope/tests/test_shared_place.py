"""Scope and SunTree always share the place (Designdocument Perspective Resolver MVP.md, A7,
decided 2026-10-25): the session has one CWD; turned to, a program follows where the other
one went (daemon/lens_link.py, LensLink.follow)."""

import functools
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("MYOS_SCOPE_START_DAEMON", "0")
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    (tmp_path / "Templates" / "Standard" / "04_Finanz").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    return {"root": root.resolve(), "studio": _project(root / "Musikstudio").resolve(),
            "reisen": _project(root / "Reisen").resolve()}


@pytest.fixture
def programs(world, monkeypatch):
    """Scope and SunTree at one session - it stands in for the daemon both connect to."""
    import Scope.Scope as S
    import SunTree.SunTree as T
    from core.scope_api import ScopeApi
    from daemon.client import LocalSession
    from daemon.lens_link import LensLink

    daemon = LocalSession(world["root"])
    shared = functools.partial(LensLink, connect=lambda root: daemon)
    monkeypatch.setattr(S, "LensLink", shared)
    monkeypatch.setattr(T, "LensLink", shared)

    app = QGuiApplication.instance() or QGuiApplication([])
    scope = S.Backend(ScopeApi(str(world["studio"])), app, QQmlApplicationEngine())
    scope.lens("set_cwd", {"path": str(world["studio"])})  # as Scope's QML does on start
    suntree = T.SunTreeBackend(T.MyOSBackendAdapter(ScopeApi(str(world["studio"]))), str(world["studio"]))
    yield scope, suntree
    suntree.close()


def test_scope_follows_where_suntree_went(world, programs):
    scope, suntree = programs
    suntree.setCwd(str(world["reisen"]))

    assert scope.followPlace() == str(world["reisen"])
    assert scope.followPlace() == ""  # already there


def test_suntree_follows_where_scope_went(world, programs):
    scope, suntree = programs
    scope.lens("set_cwd", {"path": str(world["reisen"])})

    assert suntree.followPlace()
    assert suntree.cwd() == str(world["reisen"])
    assert not suntree.followPlace()  # already there


def test_scope_outside_the_projects_is_not_pulled_back(world, programs, tmp_path):
    scope, _ = programs
    scope.lens("set_cwd", {"path": str(tmp_path)})  # refused: no project there

    assert scope.followPlace() == ""


def test_suntree_turned_to_shows_scopes_place(world, programs):
    from PySide6.QtCore import QObject, QUrl, Signal

    class Hotkey(QObject):
        activated = Signal()

    scope, suntree = programs
    engine, hotkey = QQmlApplicationEngine(), Hotkey()
    ctx = engine.rootContext()
    ctx.setContextProperty("sunTreeBackend", suntree)
    ctx.setContextProperty("sunTreeHotkey", hotkey)
    ctx.setContextProperty("sunTreeStartHidden", True)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[2] / "SunTree" / "main.qml")))
    win = engine.rootObjects()[0]

    scope.lens("set_cwd", {"path": str(world["reisen"])})
    scope.lens("look_at", {"path": str(world["reisen"] / "04_Finanz")})
    hotkey.activated.emit()  # SunTree comes up
    QGuiApplication.instance().processEvents()

    assert win.property("cwdPath") == str(world["reisen"])
    lens = win.property("lensState")
    assert (lens.toVariant() if hasattr(lens, "toVariant") else lens)["lens"] == ["04_Finanz"]
    engine.deleteLater()
