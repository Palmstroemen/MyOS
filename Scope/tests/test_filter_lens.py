"""A filter chosen by hand puts on its lens (Designdocument Perspective Resolver MVP.md, A6, E6).

`## Perspective` names the lens (04_Finanz/Ausgaben); it is put on where one stands. Lifting
the filter takes the lens off - only while it is still the filter's. An auto filter never
puts on a lens."""

from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


def _filter(path: Path, name: str, lens: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    perspective = f"\n## Perspective\n{lens}\n" if lens else ""
    path.write_text(f"# Filter\nName: {name}\n{perspective}")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("MYOS_SCOPE_START_DAEMON", "0")
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    (tmp_path / "Templates" / "Standard" / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (tmp_path / "Templates" / "Standard" / "05_Rechtliches").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio").resolve()
    filters = studio / ".MyOS" / "Filters"
    return {
        "studio": studio,
        "expenses": _filter(filters / "Ausgaben.md", "Ausgaben", "04_Finanz/Ausgaben"),
        "legal": _filter(filters / "Recht.md", "Recht", "05_Rechtliches"),
        "plain": _filter(filters / "Schlicht.md", "Schlicht"),
    }


@pytest.fixture
def scope(world):
    from Scope.Scope import Backend
    from core.scope_api import ScopeApi

    app = QGuiApplication.instance() or QGuiApplication([])
    backend = Backend(ScopeApi(str(world["studio"])), app, QQmlApplicationEngine())
    backend.lens("set_cwd", {"path": str(world["studio"])})
    return backend


def _lens(scope):
    return scope.lens("state", {})["result"]


def test_choosing_the_filter_puts_on_its_lens(world, scope):
    assert scope.setManualFilter(str(world["expenses"]))

    lens = _lens(scope)
    assert lens["active"] and lens["lens"] == ["04_Finanz", "Ausgaben"]
    assert lens["project_dir"] == str(world["studio"])  # where one stands
    assert scope.resolveActiveFilter(str(world["studio"]))["lens"] == ["04_Finanz", "Ausgaben"]


def test_lifting_the_filter_takes_its_lens_off(world, scope):
    scope.setManualFilter(str(world["expenses"]))

    assert scope.clearManualFilter()
    assert not _lens(scope)["active"]


def test_a_lens_changed_since_stays(world, scope):
    scope.setManualFilter(str(world["expenses"]))
    scope.lens("look_at", {"path": str(world["studio"] / "04_Finanz")})  # the user goes on

    scope.clearManualFilter()
    assert _lens(scope)["lens"] == ["04_Finanz"]  # no longer the filter's: it stays


def test_another_filter_brings_its_own_lens(world, scope):
    scope.setManualFilter(str(world["expenses"]))
    scope.setManualFilter(str(world["legal"]))
    assert _lens(scope)["lens"] == ["05_Rechtliches"]

    scope.setManualFilter(str(world["plain"]))  # without a lens: the previous filter's goes
    assert not _lens(scope)["active"]


def test_a_filter_without_perspective_leaves_the_lens(world, scope):
    scope.lens("look_at", {"path": str(world["studio"] / "04_Finanz")})

    scope.setManualFilter(str(world["plain"]))
    scope.clearManualFilter()
    assert _lens(scope)["lens"] == ["04_Finanz"]  # not the filter's lens


def test_an_auto_filter_puts_on_no_lens(world, scope):
    _filter(world["studio"] / ".MyOS" / "Filter.md", "Auto", "04_Finanz")

    assert scope.resolveActiveFilter(str(world["studio"]))["active"]
    scope.setContext(str(world["studio"]))
    assert not _lens(scope)["active"]
