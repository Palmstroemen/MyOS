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


def test_parse_args():
    myperspectivefs = _load_module()
    args = myperspectivefs.parse_args(["--projects-root", "/tmp/Projekte", "--mount-point", "/tmp/Perspektiven", "--foreground"])
    assert (args.projects_root, args.mount_point, args.foreground) == ("/tmp/Projekte", "/tmp/Perspektiven", True)
    # the former name still works
    assert myperspectivefs.parse_args(["--project-root", "/x", "--mount-point", "/y"]).projects_root == "/x"


def test_main_mounts_the_drive(tmp_path, monkeypatch):
    myperspectivefs = _load_module()
    captured = {}
    monkeypatch.setattr(myperspectivefs, "mount_perspective_drive", lambda **kwargs: captured.update(kwargs))

    myperspectivefs.main(["--projects-root", str(tmp_path / "Projekte"), "--mount-point", str(tmp_path / "Perspektiven")])

    assert captured == {"projects_root": str((tmp_path / "Projekte").resolve()),
                        "mount_point": str((tmp_path / "Perspektiven").resolve()), "foreground": False}
