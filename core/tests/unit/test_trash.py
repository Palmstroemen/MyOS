"""Trash per project (see "Designdocument Trash.md")."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from core import trash


def _project(base: Path, name: str = "Project", project_md: str = "# MyOS Project\n") -> Path:
    root = base / name
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text(project_md)
    return root


def test_delete_moves_into_the_project_trash_with_info(tmp_path):
    root = _project(tmp_path)
    folder = root / "Ich" / "Steuer"
    folder.mkdir(parents=True)
    (folder / "beleg.pdf").write_text("x")

    entry = trash.move_to_trash(folder, deleted_by="oliver")

    assert not folder.exists()
    assert (root / ".MyOS" / "Trash" / "files" / "Steuer" / "beleg.pdf").read_text() == "x"
    info = (root / ".MyOS" / "Trash" / "info" / "Steuer.trashinfo").read_text()
    assert info.startswith("[Trash Info]\n")
    assert "Path=Ich/Steuer\n" in info  # project-relative, freedesktop style (no leading /)
    assert "DeletedBy=oliver\n" in info
    assert entry.name == "Steuer" and entry.original == "Ich/Steuer" and entry.is_dir


def test_subproject_has_its_own_trash(tmp_path):
    root = _project(tmp_path)
    sub = _project(root, "Familie")
    note = sub / "Kinder" / "Ferien.md"
    note.parent.mkdir()
    note.write_text("x")

    trash.move_to_trash(note, deleted_by="oliver")

    assert (sub / ".MyOS" / "Trash" / "files" / "Ferien.md").exists()
    assert not (root / ".MyOS" / "Trash").exists()


def test_same_names_get_unique_trash_names(tmp_path):
    root = _project(tmp_path)
    for folder in ("a", "b"):
        (root / folder).mkdir()
        (root / folder / "notiz.md").write_text(folder)

    first = trash.move_to_trash(root / "a" / "notiz.md", deleted_by="oliver")
    second = trash.move_to_trash(root / "b" / "notiz.md", deleted_by="oliver")

    assert first.name == "notiz.md" and second.name == "notiz.md.2"
    assert {e.original for e in trash.list_trash(root)} == {"a/notiz.md", "b/notiz.md"}


def test_list_shows_date_and_who(tmp_path):
    root = _project(tmp_path)
    (root / "x.md").write_text("x")

    trash.move_to_trash(root / "x.md", deleted_by="anna")
    [entry] = trash.list_trash(root)

    assert entry.deleted_by == "anna"
    assert abs((datetime.now() - entry.deleted_at).total_seconds()) < 60
    assert entry.is_dir is False


def test_restore_puts_it_back_and_recreates_parents(tmp_path):
    root = _project(tmp_path)
    folder = root / "Ich" / "Steuer"
    folder.mkdir(parents=True)
    (folder / "beleg.pdf").write_text("x")
    trash.move_to_trash(folder, deleted_by="oliver")
    (root / "Ich").rmdir()  # its parent vanished meanwhile

    restored = trash.restore(root, "Steuer")

    assert restored == folder
    assert (folder / "beleg.pdf").read_text() == "x"
    assert trash.list_trash(root) == []


def test_restore_does_not_overwrite(tmp_path):
    root = _project(tmp_path)
    (root / "notiz.md").write_text("old")
    trash.move_to_trash(root / "notiz.md", deleted_by="oliver")
    (root / "notiz.md").write_text("new")

    restored = trash.restore(root, "notiz.md")

    assert restored == root / "notiz (restored).md"
    assert restored.read_text() == "old"
    assert (root / "notiz.md").read_text() == "new"


def test_delete_finally(tmp_path):
    root = _project(tmp_path)
    (root / "x").mkdir()
    trash.move_to_trash(root / "x", deleted_by="oliver")

    trash.delete_finally(root, "x")

    assert trash.list_trash(root) == []
    assert not (root / ".MyOS" / "Trash" / "files" / "x").exists()


def test_cleanup_removes_entries_older_than_the_retention(tmp_path):
    root = _project(tmp_path, project_md="# MyOS Project\ntrash_days: 7\n")
    for name in ("alt.md", "neu.md"):
        (root / name).write_text("x")
        trash.move_to_trash(root / name, deleted_by="oliver")

    removed = trash.cleanup(root, now=datetime.now() + timedelta(days=8))

    assert sorted(removed) == ["alt.md", "neu.md"]
    assert trash.list_trash(root) == []
    assert trash.cleanup(root) == []


def test_retention_days_inherits_from_the_parent_project(tmp_path):
    root = _project(tmp_path, project_md="---\nx: 1\n---\ncolor: #123456\ntrash_days: 14\n")
    sub = _project(root, "Familie")
    own = _project(root, "Job", project_md="# MyOS Project\ntrash_days: 60\n")
    plain = _project(tmp_path, "Plain")

    assert trash.retention_days(root) == 14
    assert trash.retention_days(sub) == 14
    assert trash.retention_days(own) == 60
    assert trash.retention_days(plain) == trash.DEFAULT_RETENTION_DAYS == 30


def test_outside_projects_there_is_no_project_trash(tmp_path):
    loose = tmp_path / "loose.md"
    loose.write_text("x")

    assert trash.project_trash_root(loose) is None
    with pytest.raises(trash.TrashError):
        trash.move_to_trash(loose, deleted_by="oliver")
    assert loose.exists()


def test_the_trash_itself_and_project_folders_cannot_be_trashed(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(trash.TrashError):
        trash.move_to_trash(root, deleted_by="oliver")
    with pytest.raises(trash.TrashError):
        trash.move_to_trash(root / ".MyOS", deleted_by="oliver")


def test_restored_folder_names_keep_dots(tmp_path):
    root = _project(tmp_path)
    (root / "v1.2").mkdir()
    trash.move_to_trash(root / "v1.2", deleted_by="oliver")
    (root / "v1.2").mkdir()

    assert trash.restore(root, "v1.2") == root / "v1.2 (restored)"


def test_restore_refuses_paths_leading_out_of_the_project(tmp_path):
    root = _project(tmp_path)
    (root / "x.md").write_text("x")
    trash.move_to_trash(root / "x.md", deleted_by="oliver")
    info = root / ".MyOS" / "Trash" / "info" / "x.md.trashinfo"
    info.write_text(info.read_text().replace("Path=x.md", "Path=../../outside.md"))

    with pytest.raises(trash.TrashError):
        trash.restore(root, "x.md")
    assert not (tmp_path.parent / "outside.md").exists()
    assert (root / ".MyOS" / "Trash" / "files" / "x.md").exists()
