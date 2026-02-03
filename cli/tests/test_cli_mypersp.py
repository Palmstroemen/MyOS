# cli/tests/test_cli_mypersp.py

import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cmd(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "mypersp.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_perspective(path: Path, name: str) -> None:
    path.write_text(f"# Perspective\nName: {name}\n")


def test_mypersp_list_orders_by_specificity():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        (root / ".MyOS").mkdir(parents=True)
        _write_perspective(root / ".MyOS" / "Perspective.md", "Root")
        _write_perspective(sub / "Perspective.md", "Sub")

        result = _run_cmd(["list", str(sub)], cwd=tmpdir)

        assert result.returncode == 0
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert lines[0].startswith("Sub ")
        assert lines[1].startswith("Root ")


def test_mypersp_resolve_manual_wins():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        manual = root / ".MyOS"
        manual.mkdir(parents=True)
        _write_perspective(manual / "Perspective.md", "Manual")
        _write_perspective(sub / "Perspective.md", "Auto")

        result = _run_cmd(["resolve", str(sub), "--manual", str(manual / "Perspective.md")], cwd=tmpdir)

        assert result.returncode == 0
        assert result.stdout.strip() == "Manual"


def test_mypersp_resolve_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        myos = root / ".MyOS"
        myos.mkdir(parents=True)
        _write_perspective(myos / "Perspective.md", "Root")

        result = _run_cmd(["resolve", str(sub)], cwd=tmpdir)

        assert result.returncode == 0
        assert result.stdout.strip() == "Root"
