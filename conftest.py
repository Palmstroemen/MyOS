"""Shared safety fixtures for every test suite (core, cli, Scope, PostFix)."""

import os

import pytest
from core.brand import env_name

# Browser pages (PostFix's editor) without a screen: Chromium's GPU emulation crashes when pages
# are made and deleted one after another (measured); drawn without a GPU it does not. Set before
# QtWebEngine starts.
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-gpu")


@pytest.fixture(autouse=True)
def no_real_desktop_changes(monkeypatch, tmp_path_factory):
    """
    Desk profiles are always on: opening a folder may change the wallpaper and theme,
    and MyOS keeps the user's own desktop in ~/.config/MyOS. Tests must never touch the
    real desktop or that file: no backend (tests that need one pass a fake) and a
    config home of their own.
    """
    monkeypatch.setenv(env_name("DESK_BACKEND"), "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    # Nor start a perspective daemon that mounts a drive (Scope starts one by default).
    monkeypatch.setenv(env_name("SCOPE_START_DAEMON"), "0")
