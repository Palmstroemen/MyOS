# cli/tests/test_cli_myfilter.py

import subprocess
import sys
import tempfile
from pathlib import Path


def _run_cmd(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "myfilter.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_filter(path: Path, name: str) -> None:
    path.write_text(f"# Filter\nName: {name}\n")


def test_myfilter_list_orders_by_specificity():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        (root / ".MyOS").mkdir(parents=True)
        _write_filter(root / ".MyOS" / "Filter.md", "Root")
        _write_filter(sub / "Filter.md", "Sub")

        result = _run_cmd(["list", str(sub)], cwd=tmpdir)

        assert result.returncode == 0
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        assert lines[0].startswith("Sub ")
        assert lines[1].startswith("Root ")


def test_myfilter_resolve_manual_wins():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        manual = root / ".MyOS"
        manual.mkdir(parents=True)
        _write_filter(manual / "Filter.md", "Manual")
        _write_filter(sub / "Filter.md", "Auto")

        result = _run_cmd(["resolve", str(sub), "--manual", str(manual / "Filter.md")], cwd=tmpdir)

        assert result.returncode == 0
        assert result.stdout.strip() == "Manual"


def test_myfilter_resolve_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)

        myos = root / ".MyOS"
        myos.mkdir(parents=True)
        _write_filter(myos / "Filter.md", "Root")

        result = _run_cmd(["resolve", str(sub)], cwd=tmpdir)

        assert result.returncode == 0
        assert result.stdout.strip() == "Root"


def test_myfilter_activate_and_clear_manual_state():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)
        manual = root / ".MyOS"
        manual.mkdir(parents=True)
        _write_filter(manual / "Filter.md", "Manual")
        _write_filter(sub / "Filter.md", "Auto")

        activated = _run_cmd(["activate", str(manual / "Filter.md")], cwd=tmpdir)
        resolved = _run_cmd(["resolve", str(sub)], cwd=tmpdir)
        cleared = _run_cmd(["clear"], cwd=tmpdir)
        resolved_auto = _run_cmd(["resolve", str(sub)], cwd=tmpdir)

        assert activated.returncode == 0
        assert "Activated manual filter" in activated.stdout
        assert resolved.returncode == 0
        assert resolved.stdout.strip() == "Manual"
        assert cleared.returncode == 0
        assert "Manual filter cleared" in cleared.stdout
        assert resolved_auto.returncode == 0
        assert resolved_auto.stdout.strip() == "Auto"


def test_myfilter_show_verbose_outputs_chain():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Root"
        sub = root / "Sub"
        sub.mkdir(parents=True)
        _write_filter(root / "Filter.md", "Root")
        _write_filter(sub / "Filter.md", "Sub")

        result = _run_cmd(["show", str(sub), "--verbose"], cwd=tmpdir)

        assert result.returncode == 0
        assert "name: Sub" in result.stdout
        assert "chain:" in result.stdout
