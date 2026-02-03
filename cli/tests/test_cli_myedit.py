# cli/tests/test_cli_myedit.py

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cmd(args, cwd, env):
    script = Path(__file__).parent.parent.parent / "cli" / "myedit.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def _create_project(path: Path) -> None:
    myos_dir = path / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)
    (myos_dir / "Project.md").write_text("# MyOS Project\n")


def test_myedit_creates_target_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Project"
        root.mkdir()
        _create_project(root)

        env = os.environ.copy()
        env["EDITOR"] = "true"

        result = _run_cmd(["tags", str(root)], cwd=tmpdir, env=env)

        assert result.returncode == 0
        assert (root / ".MyOS" / "Tags.md").exists()


def test_myedit_errors_when_no_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["EDITOR"] = "true"

        result = _run_cmd(["tags", tmpdir], cwd=tmpdir, env=env)

        assert result.returncode != 0
        assert "No project found" in result.stderr
