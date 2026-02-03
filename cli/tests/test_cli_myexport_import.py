# cli/tests/test_cli_myexport_import.py

import subprocess
import sys
import tempfile
from pathlib import Path

from core.exporter import export_subtree


def _run_cmd(script_name, args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / script_name
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _create_project(project_root: Path) -> None:
    myos_dir = project_root / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)
    (myos_dir / "Project.md").write_text("# MyOS Project\n")
    (myos_dir / "Templates.md").write_text("# Templates\nStandard\n")

    templates_dir = project_root / "Templates" / "Standard"
    templates_dir.mkdir(parents=True, exist_ok=True)


def test_myexport_creates_package():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()
        _create_project(project_root)

        subtree = project_root / "finanz"
        subtree.mkdir()
        (subtree / "note.txt").write_text("x")

        out_dir = tmp / "out"
        result = _run_cmd("myexport.py", [str(subtree), "--out", str(out_dir)], cwd=tmpdir)

        assert result.returncode == 0
        assert "Exported to" in result.stdout
        assert any(out_dir.iterdir())


def test_myimport_imports_package():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()
        _create_project(project_root)

        subtree = project_root / "docs"
        subtree.mkdir()
        (subtree / "note.txt").write_text("x")

        out_dir = tmp / "out"
        out_dir.mkdir()
        exported = export_subtree(subtree, out_dir)

        target = tmp / "Target"
        target.mkdir()

        result = _run_cmd(
            "myimport.py",
            [str(exported.package_path), "--target", str(target), "--mode", "adopt"],
            cwd=tmpdir,
        )

        assert result.returncode == 0
        assert "Imported into" in result.stdout
        assert (target / "docs" / "note.txt").exists()
