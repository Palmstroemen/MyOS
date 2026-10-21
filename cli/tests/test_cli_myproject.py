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


def test_myproject_create_new_path_with_flag():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "Root"
        root.mkdir()
        myos_dir = root / ".MyOS"
        myos_dir.mkdir(parents=True)
        (myos_dir / "Project.md").write_text("# MyOS Project\n")

        target = root / "NewChild"
        result = _run_myproject(["create", "--new", str(target)], cwd=tmpdir)

        assert result.returncode == 0
        assert (target / ".MyOS" / "Project.md").exists()


def _tidy_project(tmpdir: str) -> Path:
    """Project with born 04_Finanz/Ausgaben (unused) and Einnahmen (holds a user file)."""
    root = Path(tmpdir) / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    template = root / "Templates" / "Standard" / "04_Finanz"
    (template / "Ausgaben").mkdir(parents=True)
    (template / "Einnahmen").mkdir(parents=True)
    (root / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (root / "04_Finanz" / "Einnahmen").mkdir(parents=True)
    (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").write_bytes(b"%PDF")
    (root / "Privat").mkdir()
    return root


def _env_without_templates_override():
    import os
    return {k: v for k, v in os.environ.items() if k not in ("MYOS_TEMPLATES_DIR", "MYOS_ROLES")}


def test_myproject_tidy_turns_unused_born_folders_back_into_embryos():
    with tempfile.TemporaryDirectory() as tmpdir:
        root = _tidy_project(tmpdir)
        script = Path(__file__).parent.parent.parent / "cli" / "myproject.py"

        result = subprocess.run(
            [sys.executable, str(script), "tidy", str(root / "04_Finanz")],
            capture_output=True, text=True, cwd=tmpdir, env=_env_without_templates_override(),
        )

        assert result.returncode == 0, result.stderr
        assert not (root / "04_Finanz" / "Ausgaben").exists()
        assert (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").is_file()
        assert (root / "Privat").is_dir()
        assert str(root / "04_Finanz" / "Ausgaben") in result.stdout


def test_myproject_tidy_outside_project_fails():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = _run_myproject(["tidy", tmpdir], cwd=tmpdir)

        assert result.returncode == 1


def test_myproject_tidy_also_tidies_nested_sub_projects():
    with tempfile.TemporaryDirectory() as tmpdir:
        parent = Path(tmpdir) / "Parent"
        (parent / ".MyOS").mkdir(parents=True)
        (parent / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
        sub = _tidy_project(str(parent))
        script = Path(__file__).parent.parent.parent / "cli" / "myproject.py"

        result = subprocess.run(
            [sys.executable, str(script), "tidy", str(parent)],
            capture_output=True, text=True, cwd=tmpdir, env=_env_without_templates_override(),
        )

        assert result.returncode == 0, result.stderr
        assert not (sub / "04_Finanz" / "Ausgaben").exists()
        assert (sub / "04_Finanz" / "Einnahmen" / "Beleg.pdf").is_file()


def _trash_project(tmpdir):
    import os
    root = Path(tmpdir) / "Root"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    for name in ("Alt", "Neu"):
        (root / name).mkdir()
        (root / name / "a.md").write_text(name)
    return root


def _env():
    import os
    env = {k: v for k, v in os.environ.items() if not k.startswith("MYOS_ACL")}
    env["MYOS_ACL_USER"] = "tester"
    return env


def _run(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "myproject.py"
    return subprocess.run([sys.executable, str(script)] + args, capture_output=True, text=True, cwd=cwd, env=_env())


def test_myproject_trash_list_restore_delete_empty():
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from core import trash

    with tempfile.TemporaryDirectory() as tmpdir:
        root = _trash_project(tmpdir)
        trash.move_to_trash(root / "Alt", deleted_by="tester")
        trash.move_to_trash(root / "Neu", deleted_by="tester")

        listed = _run(["trash", "list", str(root)], cwd=tmpdir)
        assert listed.returncode == 0
        assert "Alt" in listed.stdout and "Neu" in listed.stdout and "tester" in listed.stdout

        assert _run(["trash", "restore", "Alt", "--in", str(root)], cwd=tmpdir).returncode == 0
        assert (root / "Alt" / "a.md").exists()

        refused = _run(["trash", "empty", "--in", str(root)], cwd=tmpdir)
        assert refused.returncode != 0 and "--yes" in refused.stderr
        assert [e.name for e in trash.list_trash(root)] == ["Neu"]

        assert _run(["trash", "empty", "--in", str(root), "--yes"], cwd=tmpdir).returncode == 0
        assert trash.list_trash(root) == []

        trash.move_to_trash(root / "Alt", deleted_by="tester")
        assert _run(["trash", "delete", "Alt", "--in", str(root)], cwd=tmpdir).returncode == 0
        assert trash.list_trash(root) == []
        missing = _run(["trash", "restore", "Nix", "--in", str(root)], cwd=tmpdir)
        assert missing.returncode != 0
