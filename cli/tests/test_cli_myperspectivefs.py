from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module():
    script = Path(__file__).parent.parent.parent / "cli" / "myperspectivefs.py"
    spec = importlib.util.spec_from_file_location("myperspectivefs", script)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_args_requires_core_flags():
    myperspectivefs = _load_module()
    args = myperspectivefs.parse_args(
        [
            "--project-root",
            "/tmp/projects",
            "--mount-point",
            "/tmp/mnt",
            "--foreground",
        ]
    )
    assert args.project_root == "/tmp/projects"
    assert args.mount_point == "/tmp/mnt"
    assert args.perspective == "flipped"
    assert args.foreground is True


def test_choose_default_start_picks_first_project(tmp_path):
    myperspectivefs = _load_module()
    project_root = tmp_path / "Projekte"
    project_root.mkdir()
    (project_root / "B").mkdir()
    (project_root / "A").mkdir()
    start = myperspectivefs._choose_default_start(project_root)
    assert start == project_root / "A"


def test_main_calls_mount_with_expected_arguments(tmp_path, monkeypatch):
    myperspectivefs = _load_module()
    project_root = tmp_path / "Projekte"
    project_root.mkdir()
    (project_root / "ProjektA").mkdir()
    mount_point = tmp_path / "mnt"
    mount_point.mkdir()

    captured = {}

    def _fake_mount(**kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(myperspectivefs, "mount_perspective_fuse", _fake_mount)
    myperspectivefs.main(
        [
            "--project-root",
            str(project_root),
            "--mount-point",
            str(mount_point),
            "--perspective",
            "flipped",
        ]
    )

    assert captured["project_root"] == str(project_root.resolve())
    assert captured["mount_point"] == str(mount_point.resolve())
    assert captured["perspective_id"] == "flipped"
