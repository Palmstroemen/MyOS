"""ACL rules follow entries that are renamed or moved inside the project."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: *\n\n"
    "## Team\n- /Arbeit/: read, write\n- /Arbeit/Geheim/: none\n- /Wartet/: none\n\n"
    "# Users\nAnna: Admin\nKarl: Team\n"
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_BACKEND"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("MYOS_ACL_USER", "karl")


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    (root / "Arbeit" / "Geheim").mkdir(parents=True)
    (root / "Ablage").mkdir()
    return root


def _acls(root: Path) -> str:
    return (root / ".MyOS" / "ACLs.md").read_text()


def test_rename_takes_the_rules_along(tmp_path):
    root = _project(tmp_path)

    renamed = ScopeApi(str(root)).rename_entry(str(root / "Arbeit"), "Projekte2026")

    assert renamed == str(root / "Projekte2026")
    text = _acls(root)
    assert "- /Projekte2026/: read, write\n" in text and "- /Projekte2026/Geheim/: none\n" in text
    assert "/Arbeit/" not in text


def test_move_takes_the_rules_along(tmp_path):
    root = _project(tmp_path)

    report = ScopeApi(str(root)).move_entries([str(root / "Arbeit" / "Geheim")], str(root / "Ablage"))

    assert report["ok"] is True
    assert "- /Ablage/Geheim/: none\n" in _acls(root)


def test_rename_onto_a_path_with_waiting_rules_is_refused(tmp_path):
    root = _project(tmp_path)

    assert ScopeApi(str(root)).rename_entry(str(root / "Arbeit"), "Wartet") is None
    assert (root / "Arbeit").is_dir() and not (root / "Wartet").exists()
    assert _acls(root) == ACLS


def test_move_onto_a_path_with_waiting_rules_is_refused(tmp_path):
    root = _project(tmp_path)
    (root / "Ablage" / "Wartet").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS.replace("- /Wartet/: none\n", "- /Neu/Geheim/: none\n"))
    (root / "Neu").mkdir()

    report = ScopeApi(str(root)).move_entries([str(root / "Arbeit" / "Geheim")], str(root / "Neu"))

    assert report["ok"] is False
    assert report["errors"][0]["reason"] == "acl_rules_conflict"
    assert (root / "Arbeit" / "Geheim").is_dir()
