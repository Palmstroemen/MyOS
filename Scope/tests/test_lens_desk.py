"""The Desk with a lens, through Scope's backend (Designdocument Perspective Resolver MVP.md, A5).

Musikstudio is dark, the finance lens light (its Desk in the template). The lens' Desk
overrules the project's wherever the lens is moved; ✕ brings the Desk of the project one
stands in. What the user changes with the lens on is kept in the template."""

import os
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from core.desk_runtime import DeskRuntime, DeskRuntimeSettings
from core.desk_service import DeskService
from core.desktop_backends.base import BackendStepResult, DesktopBackend, DesktopState
from core.scope_api import ScopeApi


class FakeDesktop(DesktopBackend):
    name = "fake"

    def __init__(self):
        self.state = DesktopState(theme="Mint-Y", wallpaper="/bg/default.jpg", panel_theme="Mint", taskbar=())

    def capture(self):
        return self.state

    def apply_theme(self, config, *, dry_run=True):
        if config.theme_preset and not dry_run:
            self.state = replace(self.state, theme=config.theme_preset)
        return BackendStepResult(ok=True)

    def apply_panel_theme(self, config, *, dry_run=True):
        return BackendStepResult(ok=True)

    def apply_wallpaper(self, config, *, dry_run=True):
        return BackendStepResult(ok=True)

    def apply_dock(self, config, *, dry_run=True):
        return BackendStepResult(ok=True)


def _project(path: Path, theme=None) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    if theme:
        (path / ".MyOS" / "Desk.md").write_text(f"# Desk\nThemePreset: {theme}\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("MYOS_SCOPE_START_DAEMON", "0")
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    finance = tmp_path / "Templates" / "Standard" / "04_Finanz" / ".MyOS"
    finance.mkdir(parents=True)
    (finance / "Desk.md").write_text("# Desk\nThemePreset: Finanz-Hell\n")
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio", "Studio-Dunkel")
    (studio / "04_Finanz" / ".MyOS").mkdir(parents=True)  # born: with a copy of the template's Desk
    (studio / "04_Finanz" / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Alte-Kopie\n")
    reisen = _project(root / "Reisen", "Reisen-Blau")
    return {"studio": studio, "reisen": reisen, "finance_desk": finance / "Desk.md"}


@pytest.fixture
def scope(world):
    from Scope.Scope import Backend

    app = QGuiApplication.instance() or QGuiApplication([])
    api = ScopeApi(str(world["studio"]))
    desktop = FakeDesktop()
    settings = DeskRuntimeSettings(enabled=True, dry_run=False, backend_name="fake", include_root_desk=False,
                                   prefer_filter_desk=True, fallback_profile=None)
    api._desk_service = DeskService(runtime=DeskRuntime(settings=settings, backend=desktop))
    backend = Backend(api, app, QQmlApplicationEngine())
    backend.desktop = desktop
    return backend


def test_the_lens_desk_overrules_the_projects(world, scope):
    scope.setContext(str(world["studio"]))
    assert scope.desktop.state.theme == "Studio-Dunkel"

    scope.lens("set_cwd", {"path": str(world["studio"])})
    scope.lens("put_on", {"lens": ["04_Finanz"]})
    assert scope.desktop.state.theme == "Finanz-Hell"  # the template's, not the old copy

    scope.lens("move_to", {"path": str(world["reisen"])})
    scope.setContext(str(world["reisen"]))  # Scope's CWP follows the lens
    assert scope.desktop.state.theme == "Finanz-Hell"

    scope.lens("take_off", {})
    assert scope.desktop.state.theme == "Reisen-Blau"


def test_take_off_in_the_same_project_brings_its_desk(world, scope):
    scope.lens("set_cwd", {"path": str(world["studio"])})
    scope.lens("put_on", {"lens": ["04_Finanz"]})
    assert scope.desktop.state.theme == "Finanz-Hell"

    scope.lens("take_off", {})  # the CWP stays Musikstudio: QML sets no new context
    assert scope.desktop.state.theme == "Studio-Dunkel"


def test_changes_with_the_lens_on_are_kept_in_the_template(world, scope):
    scope.lens("set_cwd", {"path": str(world["studio"])})
    scope.lens("put_on", {"lens": ["04_Finanz"]})
    scope.desktop.state = replace(scope.desktop.state, theme="Finanz-Gold")  # the user changes it

    scope.lens("take_off", {})

    assert "ThemePreset: Finanz-Gold\n" in world["finance_desk"].read_text()
    assert "Finanz-Gold" not in (world["studio"] / ".MyOS" / "Desk.md").read_text()
    assert scope.desktop.state.theme == "Studio-Dunkel"
