"""ScopeApi deletes into the project trash (outside projects: the system trash)."""

from pathlib import Path

import pytest

from core import trash
from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_BACKEND"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MYOS_ACL_USER", "anna")


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / "Ordner").mkdir()
    (root / "Ordner" / "a.md").write_text("a")
    return root


def test_delete_in_a_project_goes_to_its_trash(tmp_path, fake_system_trash):
    root = _project(tmp_path)

    report = ScopeApi(str(root)).delete_entries([str(root / "Ordner")])

    assert report["ok"] is True and report["deleted"] == [str(root / "Ordner")]
    assert not (root / "Ordner").exists()
    [entry] = trash.list_trash(root)
    assert entry.original == "Ordner" and entry.deleted_by == "anna"
    assert fake_system_trash == []


def test_delete_outside_projects_uses_the_system_trash(tmp_path, fake_system_trash):
    loose = tmp_path / "loose.md"
    loose.write_text("x")

    report = ScopeApi(str(tmp_path)).delete_entries([str(loose)])

    assert report["ok"] is True
    assert fake_system_trash == [loose]


def test_without_a_system_trash_nothing_is_deleted(tmp_path, monkeypatch):
    loose = tmp_path / "loose.md"
    loose.write_text("x")

    def no_trash(path):
        raise OSError("no system trash")

    monkeypatch.setattr("core.scope_api._move_to_system_trash", no_trash)
    report = ScopeApi(str(tmp_path)).delete_entries([str(loose)])

    assert report["ok"] is False
    assert report["errors"] == [{"source": str(loose), "reason": "delete_failed"}]
    assert loose.exists()


ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: *\n\n"
    "## Team\n- /Ordner/: read, write\n- /Offen/: read, write, delete\n\n"
    "# Users\nAnna: Admin\nKarl: Team\n"
)


def test_list_restore_and_delete_finally(tmp_path):
    root = _project(tmp_path)
    api = ScopeApi(str(root))
    api.delete_entries([str(root / "Ordner")])

    [entry] = api.trash_entries(str(root))
    assert entry["name"] == "Ordner" and entry["original"] == "Ordner" and entry["isDir"] is True
    assert entry["deletedBy"] == "anna" and entry["deletedAt"]

    assert api.trash_restore(str(root), "Ordner") == {"ok": True, "reason": "", "path": str(root / "Ordner")}
    assert (root / "Ordner" / "a.md").exists()
    assert api.trash_entries(str(root)) == []

    api.delete_entries([str(root / "Ordner")])
    assert api.trash_delete_finally(str(root), "Ordner")["ok"] is True
    assert api.trash_entries(str(root)) == []


def test_trash_shows_only_what_the_user_could_delete(tmp_path, monkeypatch):
    root = _project(tmp_path)
    (root / "Offen").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")
    monkeypatch.setenv("MYOS_ACL_BACKEND", "legacy")
    ScopeApi(str(root)).delete_entries([str(root / "Ordner"), str(root / "Offen")])  # by anna

    monkeypatch.setenv("MYOS_ACL_USER", "karl")
    karl = ScopeApi(str(root))

    assert [e["name"] for e in karl.trash_entries(str(root))] == ["Offen"]
    assert karl.trash_restore(str(root), "Ordner") == {"ok": False, "reason": "permission", "path": ""}
    assert karl.trash_delete_finally(str(root), "Ordner")["reason"] == "permission"
    assert karl.trash_restore(str(root), "Offen")["ok"] is True


def test_expired_entries_are_cleaned_up_when_the_project_is_opened(tmp_path):
    root = _project(tmp_path)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\ntrash_days: 0\n")
    api = ScopeApi(str(root))
    api.delete_entries([str(root / "Ordner")])
    info = next((root / ".MyOS" / "Trash" / "info").glob("*.trashinfo"))
    info.write_text(info.read_text().replace("DeletionDate=20", "DeletionDate=19"))  # a century ago

    ScopeApi(str(root))  # opening the project

    assert trash.list_trash(root) == []
