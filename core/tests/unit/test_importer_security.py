# test_importer_security.py

import tempfile
import zipfile
from pathlib import Path

import pytest

from core.importer import import_package


def _write_export_project(project_root: Path, subtree: str) -> None:
    myos_dir = project_root / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)
    project_md = myos_dir / "Project.md"
    project_md.write_text(
        "# MyOS Project\n"
        "# Export\n"
        f"ReferencePath: {project_root}\n"
        f"Subtree: {subtree}\n"
        "ExportedAt: 2026-02-02T00:00:00Z\n"
        "Source: test@host\n"
    )


def test_import_rejects_missing_project_md():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()
        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_subtree_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/../evil")
        (package / "evil").mkdir()

        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_symlinks():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/data")
        data_dir = package / "data"
        data_dir.mkdir(parents=True)

        secret = package / "secret.txt"
        secret.write_text("secret")
        (data_dir / "link.txt").symlink_to(secret)

        with pytest.raises(ValueError):
            import_package(package, target_root=tmp / "target", mode="adopt")


def test_import_rejects_zip_traversal():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        zip_path = tmp / "attack.zip"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("../evil.txt", "boom")

        with pytest.raises(ValueError):
            import_package(zip_path, target_root=tmp / "target", mode="adopt")


def test_import_basic_merge():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        package = tmp / "package"
        package.mkdir()

        _write_export_project(package, "/data")
        data_dir = package / "data"
        data_dir.mkdir(parents=True)
        (data_dir / "note.txt").write_text("hello")

        target = tmp / "target"
        target.mkdir()

        result = import_package(package, target_root=target, mode="adopt", conflict="merge")

        assert (target / "data" / "note.txt").exists()
        assert result.import_root == target
