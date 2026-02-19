import importlib
from pathlib import Path
import subprocess
import pytest

from core.desk import env_flag_is_true, resolve_active_desk
from core.desk_runtime import DeskRuntime, DeskRuntimeSettings
from core.desktop_backends.kde import KdeDesktopBackend
from core.desktop_backends import build_backend
from core.desktop_backends.base import NoopDesktopBackend
from core.desk import DeskConfig


def _write_desk(path: Path, theme: str = "DemoTheme") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Desk\nThemePreset: {theme}\n", encoding="utf-8")


def test_env_flag_is_true_parses_expected_truthy_values():
    assert env_flag_is_true("1") is True
    assert env_flag_is_true("true") is True
    assert env_flag_is_true("yes") is True
    assert env_flag_is_true("on") is True
    assert env_flag_is_true("0") is False
    assert env_flag_is_true("no") is False
    assert env_flag_is_true(None) is False


def test_runtime_settings_from_env(monkeypatch):
    monkeypatch.setenv("MYOS_DESK_ENABLE", "1")
    monkeypatch.setenv("MYOS_DESK_DRY_RUN", "0")
    monkeypatch.setenv("MYOS_DESK_BACKEND", "kde")
    monkeypatch.setenv("MYOS_DESK_INCLUDE_ROOT", "1")
    monkeypatch.setenv("MYOS_DESK_DISABLE_PERSPECTIVE", "1")
    monkeypatch.setenv("MYOS_DESK_FALLBACK", "/tmp/fallback/Desk.md")

    settings = DeskRuntimeSettings.from_env()

    assert settings.enabled is True
    assert settings.dry_run is False
    assert settings.backend_name == "kde"
    assert settings.include_root_desk is True
    assert settings.prefer_perspective_desk is False
    assert settings.fallback_profile == "/tmp/fallback/Desk.md"


def test_runtime_returns_no_profile_for_empty_context(tmp_path):
    workspace = tmp_path / "Workspace"
    workspace.mkdir()
    runtime = DeskRuntime(
        settings=DeskRuntimeSettings(
            enabled=True,
            dry_run=True,
            backend_name="none",
            include_root_desk=False,
            prefer_perspective_desk=True,
            fallback_profile=None,
        )
    )

    result = runtime.handle_context(workspace)

    assert result["ok"] is True
    assert result["reason"] == "no_profile"
    assert result["source"] is None


def test_runtime_disabled_tracks_profile_without_applying(tmp_path):
    project = tmp_path / "Project"
    project.mkdir()
    _write_desk(project / ".MyOS" / "Desk.md", "RootTheme")
    runtime = DeskRuntime(
        settings=DeskRuntimeSettings(
            enabled=False,
            dry_run=True,
            backend_name="none",
            include_root_desk=False,
            prefer_perspective_desk=True,
            fallback_profile=None,
        )
    )

    result = runtime.handle_context(project)
    active = runtime.get_active_profile()

    assert result["ok"] is True
    assert result["reason"] == "runtime_disabled"
    assert active["source"] == str(project / ".MyOS" / "Desk.md")
    assert active["hash"]


def test_runtime_rejects_invalid_context_path():
    runtime = DeskRuntime(
        settings=DeskRuntimeSettings(
            enabled=True,
            dry_run=True,
            backend_name="none",
            include_root_desk=False,
            prefer_perspective_desk=True,
            fallback_profile=None,
        )
    )

    result = runtime.handle_context("bad\0path")

    assert result["ok"] is False
    assert result["reason"] == "invalid_path"


def test_build_backend_returns_expected_types():
    assert isinstance(build_backend("none"), NoopDesktopBackend)
    backend = build_backend("kde")
    assert backend.name in {"kde", "none"}


def test_perspective_desk_path_traversal_is_ignored(tmp_path):
    root = tmp_path / "Project"
    work = root / "Work"
    work.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    outside = tmp_path / "OutsideDesk.md"
    _write_desk(outside, "OutsideTheme")
    (work / "Perspective.md").write_text(
        "# Perspective\nName: Unsafe\n\n## Desk\n../../OutsideDesk.md\n",
        encoding="utf-8",
    )

    resolved = resolve_active_desk(work)

    assert resolved is not None
    assert resolved.source_path == (root / ".MyOS" / "Desk.md")


def test_kde_backend_timeout_is_clamped(monkeypatch):
    monkeypatch.setenv("MYOS_DESK_KDE_TIMEOUT_S", "9000")
    kde_module = importlib.import_module("core.desktop_backends.kde")
    backend = kde_module.KdeDesktopBackend()
    assert backend.command_timeout_s == 120

    monkeypatch.setenv("MYOS_DESK_KDE_TIMEOUT_S", "oops")
    backend_invalid = kde_module.KdeDesktopBackend()
    assert backend_invalid.command_timeout_s == 15


def test_kde_backend_rejects_nonexistent_wallpaper_path_for_security(tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    backend = KdeDesktopBackend()
    config = DeskConfig(
        source_path=source,
        theme_preset=None,
        wallpaper_preset=None,
        wallpaper_path=str(tmp_path / "missing.png"),
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )

    result = backend.apply_wallpaper(config, dry_run=True)

    assert result.ok is False
    assert "invalid path" in result.message


def test_kde_backend_rejects_relative_wallpaper_escape_for_security(tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    outside = tmp_path / "Project" / "outside.png"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_bytes(b"png")
    backend = KdeDesktopBackend()
    config = DeskConfig(
        source_path=source,
        theme_preset=None,
        wallpaper_preset="../outside.png",
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )

    result = backend.apply_wallpaper(config, dry_run=True)

    assert result.ok is False
    assert "escapes profile directory" in result.message


def test_kde_backend_rejects_relative_wallpaper_symlink_escape_for_security(tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"png")
    link = source.parent / "wallpaper-link.png"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation not supported in this environment")
    backend = KdeDesktopBackend()
    config = DeskConfig(
        source_path=source,
        theme_preset=None,
        wallpaper_preset="wallpaper-link.png",
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )

    result = backend.apply_wallpaper(config, dry_run=True)

    assert result.ok is False
    assert "escapes profile directory" in result.message


def test_kde_backend_accepts_relative_wallpaper_symlink_inside_profile(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    local_target = source.parent / "local.png"
    local_target.write_bytes(b"png")
    link = source.parent / "local-link.png"
    try:
        link.symlink_to(local_target)
    except OSError:
        pytest.skip("Symlink creation not supported in this environment")
    backend = KdeDesktopBackend()
    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/plasma-apply-wallpaperimage")
    config = DeskConfig(
        source_path=source,
        theme_preset=None,
        wallpaper_preset="local-link.png",
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )

    result = backend.apply_wallpaper(config, dry_run=True)

    assert result.ok is True
    assert "dry-run" in result.message


def test_kde_backend_allows_explicit_wallpaper_symlink_outside_profile(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    outside_dir = tmp_path / "shared"
    outside_dir.mkdir(parents=True, exist_ok=True)
    outside_target = outside_dir / "outside.png"
    outside_target.write_bytes(b"png")
    explicit_link = source.parent / "explicit-link.png"
    try:
        explicit_link.symlink_to(outside_target)
    except OSError:
        pytest.skip("Symlink creation not supported in this environment")
    backend = KdeDesktopBackend()
    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/plasma-apply-wallpaperimage")
    config = DeskConfig(
        source_path=source,
        theme_preset=None,
        wallpaper_preset=None,
        wallpaper_path=str(explicit_link),
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )

    result = backend.apply_wallpaper(config, dry_run=True)

    assert result.ok is True
    assert "dry-run" in result.message


def test_kde_backend_dry_run_does_not_execute_subprocess(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    config = DeskConfig(
        source_path=source,
        theme_preset="BreezeDark",
        wallpaper_preset=None,
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )
    backend = KdeDesktopBackend()

    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/lookandfeeltool")

    def _boom(*_args, **_kwargs):
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr("core.desktop_backends.kde.subprocess.run", _boom)

    result = backend.apply_theme(config, dry_run=True)

    assert result.ok is True
    assert "dry-run" in result.message


def test_kde_backend_preserves_argument_boundaries_against_injection(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    payload = "BreezeDark; touch /tmp/pwned"
    config = DeskConfig(
        source_path=source,
        theme_preset=payload,
        wallpaper_preset=None,
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )
    backend = KdeDesktopBackend()
    called = {}

    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/lookandfeeltool")

    class _Proc:
        returncode = 0
        stderr = ""
        stdout = ""

    def _fake_run(argv, **_kwargs):
        called["argv"] = list(argv)
        return _Proc()

    monkeypatch.setattr("core.desktop_backends.kde.subprocess.run", _fake_run)

    result = backend.apply_theme(config, dry_run=False)

    assert result.ok is True
    assert called["argv"][0] == "lookandfeeltool"
    assert called["argv"][1] == "-a"
    assert called["argv"][2] == payload


def test_kde_backend_reports_timeout_without_throwing(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    config = DeskConfig(
        source_path=source,
        theme_preset="BreezeDark",
        wallpaper_preset=None,
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )
    backend = KdeDesktopBackend()
    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/lookandfeeltool")

    def _timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["lookandfeeltool"], timeout=1)

    monkeypatch.setattr("core.desktop_backends.kde.subprocess.run", _timeout)

    result = backend.apply_theme(config, dry_run=False)

    assert result.ok is False
    assert "timeout" in result.message


def test_kde_backend_handles_oserror_race_between_which_and_run(monkeypatch, tmp_path):
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")
    config = DeskConfig(
        source_path=source,
        theme_preset="BreezeDark",
        wallpaper_preset=None,
        wallpaper_path=None,
        dock_preset=None,
        recent_policy=None,
        inherit="dynamic",
        raw={},
    )
    backend = KdeDesktopBackend()
    monkeypatch.setattr("core.desktop_backends.kde.shutil.which", lambda _name: "/usr/bin/lookandfeeltool")

    def _race(*_args, **_kwargs):
        raise OSError("binary disappeared")

    monkeypatch.setattr("core.desktop_backends.kde.subprocess.run", _race)

    result = backend.apply_theme(config, dry_run=False)

    assert result.ok is False
    assert "binary disappeared" in result.message
