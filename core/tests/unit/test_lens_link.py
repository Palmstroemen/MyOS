"""One program's line to the lens (daemon/lens_link.py): Scope and SunTree both use it.

They share one lens - the daemon's of their projects root (Designdocument Perspective
Resolver MVP.md, A6) - and the Desk follows every move of it (A5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from daemon.client import LocalSession
from daemon.lens_link import LensLink


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


class FakeApi:
    """The part of ScopeApi the link uses: its projects root and the Desk's context."""

    def __init__(self, root):
        self.root = root
        self.contexts = []

    def projects_root(self):
        return self.root

    def update_context(self, path, lens_desk="", lens_desk_save=None):
        self.contexts.append((path, lens_desk, lens_desk_save))


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def world(tmp_path):
    finance = tmp_path / "Templates" / "Standard" / "04_Finanz" / ".MyOS"
    finance.mkdir(parents=True)
    (finance / "Desk.md").write_text("# Desk\nThemePreset: Finanz-Hell\n")
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    return {"root": root.resolve(), "studio": _project(root / "Musikstudio").resolve(),
            "finance_desk": (finance / "Desk.md").resolve()}


def test_two_programs_see_one_lens(world):
    daemon = LocalSession(world["root"])  # stands in for the daemon both connect to
    scope = LensLink(FakeApi(world["root"]), start_daemon=False, connect=lambda root: daemon)
    suntree = LensLink(FakeApi(world["root"]), start_daemon=False, connect=lambda root: daemon)

    scope.call("set_cwd", {"path": str(world["studio"])})
    scope.call("put_on", {"lens": ["04_Finanz"]})

    seen = suntree.call("state", {})["result"]
    assert seen["active"] and seen["lens"] == ["04_Finanz"]


def test_without_a_daemon_a_session_of_its_own(world):
    link = LensLink(FakeApi(world["root"]), start_daemon=False, connect=lambda root: None)

    link.call("set_cwd", {"path": str(world["studio"])})
    assert link.call("put_on", {"lens": ["04_Finanz"]})["result"]["active"]


def test_a_missing_daemon_is_started_once(world):
    started = []
    daemon = LocalSession(world["root"])
    answers = iter([None, daemon])  # none runs; after the start it answers
    link = LensLink(FakeApi(world["root"]), start_daemon=True, connect=lambda root: next(answers),
                    spawn=lambda root: started.append(root) or object(), wait=0)

    assert started == [world["root"]]
    assert link.started_daemon
    assert link.call("state", {})["ok"]


def test_outside_the_projects_no_lens(tmp_path):
    link = LensLink(FakeApi(None), start_daemon=True, connect=lambda root: pytest.fail("no root"))

    assert link.call("state", {}) == {"ok": False, "error": "no lens here"}


def test_only_lens_requests_pass(world):
    link = LensLink(FakeApi(world["root"]), start_daemon=False, connect=lambda root: None)

    assert link.call("shutdown", {}) == {"ok": False, "error": "no lens request: shutdown"}
    assert link.call("bear", {})["ok"] is False


def test_the_desk_follows_the_lens(world):
    api = FakeApi(world["root"])
    link = LensLink(api, start_daemon=False, connect=lambda root: None)
    link.call("set_cwd", {"path": str(world["studio"])})
    assert api.contexts == []  # set_cwd moves no lens; the program sets its context itself

    link.call("put_on", {"lens": ["04_Finanz"]})
    path, desk, desk_save = api.contexts[-1]
    assert path == str(world["studio"]) and desk == str(world["finance_desk"])
    assert desk_save == str(world["finance_desk"])  # changes are kept in the template

    link.call("take_off", {})
    assert api.contexts[-1] == (str(world["studio"]), "", None)  # the project's Desk again


def test_the_context_of_a_place_with_and_without_the_lens(world):
    api = FakeApi(world["root"])
    link = LensLink(api, start_daemon=False, connect=lambda root: None)

    link.update_context(str(world["studio"]))
    assert api.contexts[-1] == (str(world["studio"]), "", None)

    link.call("set_cwd", {"path": str(world["studio"])})
    link.call("put_on", {"lens": ["04_Finanz"]})
    link.update_context(str(world["studio"]))
    assert api.contexts[-1][1] == str(world["finance_desk"])


def test_closing_ends_only_a_daemon_it_started(world):
    class Daemon(LocalSession):
        ended = False

        def request_shutdown(self, timeout=1.0):
            Daemon.ended = True
            return True

    found = Daemon(world["root"])
    LensLink(FakeApi(world["root"]), start_daemon=True, connect=lambda root: found).close()
    assert not Daemon.ended  # someone else's: it stays

    answers = iter([None, found])
    link = LensLink(FakeApi(world["root"]), start_daemon=True, connect=lambda root: next(answers),
                    spawn=lambda root: object(), wait=0)
    link.close()
    assert Daemon.ended
