"""Shared safety fixtures for every test suite (core, cli, Scope, PostFix)."""

import pytest


@pytest.fixture(autouse=True)
def no_real_desktop_changes(monkeypatch, tmp_path_factory):
    """
    Desk profiles are always on: opening a folder may change the wallpaper and theme,
    and MyOS keeps the user's own desktop in ~/.config/MyOS. Tests must never touch the
    real desktop or that file: no backend (tests that need one pass a fake) and a
    config home of their own.
    """
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    # Nor start a perspective daemon that mounts a drive (Scope starts one by default).
    monkeypatch.setenv("MYOS_SCOPE_START_DAEMON", "0")
