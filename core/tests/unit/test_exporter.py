# test_exporter.py

import re
import tempfile
from pathlib import Path

import pytest

from core.exporter import export_subtree


def _create_project(project_root: Path, template_name: str = "Standard") -> None:
    myos_dir = project_root / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)
    (myos_dir / "Project.md").write_text("# MyOS Project\n")
    (myos_dir / "Templates.md").write_text(f"# Templates\n{template_name}\n")


def _create_templates(project_root: Path, template_name: str = "Standard") -> None:
    templates_root = project_root / "Templates" / template_name
    templates_root.mkdir(parents=True, exist_ok=True)
    (templates_root / "admin").mkdir(parents=True, exist_ok=True)


def test_export_subtree_includes_myos_and_templates():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()

        _create_project(project_root)
        _create_templates(project_root)

        subtree = project_root / "finanz" / "ausgaben"
        subtree.mkdir(parents=True)
        (subtree / "rechnung.txt").write_text("R1")

        output_dir = tmp / "exports"

        result = export_subtree(subtree, output_dir)

        package_root = result.package_path
        assert (package_root / "finanz" / "ausgaben" / "rechnung.txt").exists()
        assert (package_root / ".MyOS" / "Project.md").exists()
        project_md = package_root / ".MyOS" / "Project.md"
        assert project_md.exists()
        assert "# Export" in project_md.read_text()
        assert (package_root / "Templates" / "Standard" / "admin").exists()


def test_export_metadata_contains_reference_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()

        _create_project(project_root)
        _create_templates(project_root)

        subtree = project_root / "info"
        subtree.mkdir(parents=True)
        (subtree / "note.txt").write_text("N1")

        output_dir = tmp / "exports"

        result = export_subtree(subtree, output_dir)
        project_md = result.package_path / ".MyOS" / "Project.md"
        content = project_md.read_text()

        assert "ReferencePath:" in content
        assert "Subtree: /info" in content


def test_export_zip_removes_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()

        _create_project(project_root)
        _create_templates(project_root)

        subtree = project_root / "info"
        subtree.mkdir(parents=True)
        (subtree / "note.txt").write_text("N1")

        output_dir = tmp / "exports"

        result = export_subtree(subtree, output_dir, zip_output=True)

        assert result.zip_path is not None
        assert result.package_path.suffix == ".zip"
        assert result.package_path.exists()
        assert not result.package_path.with_suffix("").exists()


def test_export_rejects_non_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "plain"
        source.mkdir()
        output_dir = tmp / "exports"

        with pytest.raises(ValueError):
            export_subtree(source, output_dir)


def test_export_skips_symlinks():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        project_root.mkdir()

        _create_project(project_root)
        _create_templates(project_root)

        subtree = project_root / "info"
        subtree.mkdir(parents=True)
        (subtree / "note.txt").write_text("N1")

        target = project_root / "target.txt"
        target.write_text("secret")
        (subtree / "link.txt").symlink_to(target)

        output_dir = tmp / "exports"
        result = export_subtree(subtree, output_dir)

        package_root = result.package_path
        assert (package_root / "info" / "note.txt").exists()
        assert not (package_root / "info" / "link.txt").exists()


def test_default_export_name_format():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "MyProject"
        project_root.mkdir()

        _create_project(project_root)
        _create_templates(project_root)

        subtree = project_root / "info"
        subtree.mkdir(parents=True)
        (subtree / "note.txt").write_text("N1")

        output_dir = tmp / "exports"
        result = export_subtree(subtree, output_dir)

        name = result.package_path.name
        assert re.match(r"^MyProject_export_\d{8}$", name)
