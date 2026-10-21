"""Shared fixtures for the core unit tests."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def fake_system_trash(monkeypatch):
    """
    Deleting outside a MyOS project uses the system trash (gio trash). Tests must never
    fill the real user's trash: record the paths and remove them instead.
    """
    trashed = []

    def fake(path):
        path = Path(path)
        trashed.append(path)
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()

    monkeypatch.setattr("core.scope_api._move_to_system_trash", fake)
    return trashed
