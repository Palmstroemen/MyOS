# cli/tests/test_cli_myproject.py

import subprocess
import sys
import tempfile
from pathlib import Path


def _run_myproject(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "myproject.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_myproject_create_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Root"
        child = root / "Child"
        child.mkdir(parents=True)

        myos_dir = root / ".MyOS"
        myos_dir.mkdir(parents=True)
        (myos_dir / "Project.md").write_text("# MyOS Project\n")

        result = _run_myproject(["create", str(child)], cwd=tmpdir)

        assert result.returncode == 0
        assert (child / ".MyOS" / "Project.md").exists()


def test_myproject_create_without_parent_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "NoParent"
        target.mkdir()

        result = _run_myproject(["create", str(target)], cwd=tmpdir)

        assert result.returncode != 0
        assert "Error:" in result.stderr
