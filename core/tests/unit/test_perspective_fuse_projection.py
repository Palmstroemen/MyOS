"""The FUSE drive over the turned tree (core/perspective_drive.py), called directly.

What LibreOffice does when saving into /04_Finanz/Projekte/Reisen: a lock file, a
temporary file written and renamed over the target - all landing in Reisen/04_Finanz."""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

import pytest

from core.perspective_drive import PerspectiveDrive
from core.perspective_fuse import FuseOSError, PerspectiveDriveFuse


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def world(tmp_path):
    (tmp_path / "Templates" / "Standard" / "04_Finanz").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    (studio / "04_Finanz").mkdir()
    (studio / "04_Finanz" / "r1.pdf").write_text("eins")
    reisen = _project(root / "Reisen")
    return {"root": root, "studio": studio, "reisen": reisen, "fs": PerspectiveDriveFuse(PerspectiveDrive(root))}


def _errno(call) -> int:
    with pytest.raises(FuseOSError) as caught:
        call()
    return caught.value.errno


def test_virtual_levels_are_folders_and_real_files_are_files(world):
    fs = world["fs"]

    assert stat.S_ISDIR(fs.getattr("/")["st_mode"]) and stat.S_ISDIR(fs.getattr("/04_Finanz/Projekte")["st_mode"])
    assert stat.S_ISREG(fs.getattr("/04_Finanz/Projekte/Musikstudio/r1.pdf")["st_mode"])
    assert set(fs.readdir("/04_Finanz/Projekte", None)) == {".", "..", "Musikstudio", "Reisen"}
    assert _errno(lambda: fs.getattr("/04_Finanz/Projekte/Musikstudio/fehlt.pdf")) == errno.ENOENT
    assert _errno(lambda: fs.getattr("/04_Finanz/Projekte/Musikstudio/.MyOS")) == errno.ENOENT


def test_reading_a_file(world):
    fs = world["fs"]
    handle = fs.open("/04_Finanz/Projekte/Musikstudio/r1.pdf", os.O_RDONLY)
    try:
        assert fs.read("/04_Finanz/Projekte/Musikstudio/r1.pdf", 100, 0, handle) == b"eins"
    finally:
        fs.release("/04_Finanz/Projekte/Musikstudio/r1.pdf", handle)


def test_saving_like_libreoffice_lands_in_the_department_folder(world):
    fs = world["fs"]
    base = "/04_Finanz/Projekte/Reisen"

    lock = fs.create(f"{base}/.~lock.Rechnung.odt#", 0o644)
    fs.release(f"{base}/.~lock.Rechnung.odt#", lock)
    temp = fs.create(f"{base}/lu12345.tmp", 0o644)
    fs.write(f"{base}/lu12345.tmp", b"Rechnung", 0, temp)
    fs.release(f"{base}/lu12345.tmp", temp)
    fs.rename(f"{base}/lu12345.tmp", f"{base}/Rechnung.odt")
    fs.unlink(f"{base}/.~lock.Rechnung.odt#")

    folder = world["reisen"] / "04_Finanz"
    assert (folder / "Rechnung.odt").read_bytes() == b"Rechnung"
    assert sorted(p.name for p in folder.iterdir() if p.name != ".MyOS") == ["Rechnung.odt"]
    assert "Rechnung.odt" in fs.readdir(base, None)


def test_a_created_file_can_be_read_through_its_handle(world):
    # LibreOffice creates its lock file (O_RDWR | O_CREAT) and reads it at once; fusepy
    # does not pass the open flags to create, so a write-only handle failed with EBADF.
    fs = world["fs"]
    lock = "/04_Finanz/Projekte/Reisen/.~lock.Rechnung.odt#"

    handle = fs.create(lock, 0o644)
    try:
        assert fs.read(lock, 4096, 0, handle) == b""
        fs.write(lock, b"Oliver,host", 0, handle)
        assert fs.read(lock, 4096, 0, handle) == b"Oliver,host"
    finally:
        fs.release(lock, handle)


def test_folders_and_deleting(world):
    fs = world["fs"]

    fs.mkdir("/04_Finanz/Projekte/Musikstudio/2026", 0o755)
    assert (world["studio"] / "04_Finanz" / "2026").is_dir()
    fs.rmdir("/04_Finanz/Projekte/Musikstudio/2026")
    fs.unlink("/04_Finanz/Projekte/Musikstudio/r1.pdf")
    assert list(p.name for p in (world["studio"] / "04_Finanz").iterdir()) == []


def test_the_virtual_levels_cannot_be_written(world):
    fs = world["fs"]

    assert _errno(lambda: fs.create("/04_Finanz/Projekte/neu.pdf", 0o644)) == errno.EACCES
    assert _errno(lambda: fs.mkdir("/04_Finanz/Neu", 0o755)) == errno.EACCES
    assert _errno(lambda: fs.rmdir("/04_Finanz/Projekte/Reisen")) == errno.EACCES
    assert _errno(lambda: fs.rename("/04_Finanz/Projekte/Reisen", "/04_Finanz/Projekte/Ferien")) == errno.EACCES


def test_denied_by_acls(world):
    studio_finance = world["studio"] / "04_Finanz"
    fs = PerspectiveDriveFuse(PerspectiveDrive(
        world["root"], may=lambda path, action: not (action == "write" and studio_finance in [path, *path.parents])))

    assert stat.S_ISREG(fs.getattr("/04_Finanz/Projekte/Musikstudio/r1.pdf")["st_mode"])
    assert _errno(lambda: fs.create("/04_Finanz/Projekte/Musikstudio/neu.pdf", 0o644)) == errno.EACCES
    assert _errno(lambda: fs.unlink("/04_Finanz/Projekte/Musikstudio/r1.pdf")) == errno.EACCES
    assert _errno(lambda: fs.open("/04_Finanz/Projekte/Musikstudio/r1.pdf", os.O_WRONLY)) == errno.EACCES


def test_where_the_lens_enters_a_project_stays(world):
    fs = world["fs"]

    for path in ("/04_Finanz/Projekte/Reisen", "/04_Finanz/Projekte/Musikstudio"):  # stand-in / real
        assert _errno(lambda: fs.rmdir(path)) == errno.EACCES
        assert _errno(lambda: fs.rename(path, path + "2")) == errno.EACCES
    assert world["reisen"].is_dir() and (world["studio"] / "04_Finanz").is_dir()
