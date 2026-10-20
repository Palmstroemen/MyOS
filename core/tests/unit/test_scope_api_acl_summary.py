"""ScopeApi.acl_summary: the ACL filter panel's data for a listed folder."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_USER", "MYOS_ACL_BACKEND", "MYOS_ACL_AUDIT"):
        monkeypatch.delenv(key, raising=False)


def _project(tmp_path: Path, acls: str = None) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (root / "Templates" / "Standard" / "finanz").mkdir(parents=True)
    (root / "finanz").mkdir()
    (root / "privat").mkdir()
    if acls is not None:
        (root / ".MyOS" / "ACLs.md").write_text(acls)
    return root


def test_no_acls_file_means_no_panel(tmp_path):
    root = _project(tmp_path)
    api = ScopeApi(str(root))

    assert api.acl_summary(str(root), [str(root / "finanz")]) == {"hasAcls": False}


def test_summary_for_listing(tmp_path):
    root = _project(tmp_path, "# Permissions\n\n## Buchhalter\n- /finanz/: read, write\n\n# Users\nBertha: Buchhalter\n")
    api = ScopeApi(str(root))
    entries = [str(root / "finanz"), str(root / "privat")]

    summary = api.acl_summary(str(root), entries)

    assert summary["hasAcls"] is True
    assert summary["path"] == str(root.resolve())
    assert {p["id"] for p in summary["principals"] if p["section"] == "exception"} >= {"role:buchhalter", "user:bertha"}
    assert "user:bertha" in summary["access"][str(root / "finanz")]
    assert summary["access"][str(root / "privat")] == []


def test_enforced_user_who_may_not_read_acls_sees_no_panel(tmp_path, monkeypatch):
    root = _project(tmp_path, (
        "# Permissions\n\n"
        "## Admin\n- /*: read, write\n\n"
        "## Buchhalter\n- /finanz/: read, write\n\n"
        "# Users\nAnna: Admin\nBertha: Buchhalter\n"
    ))
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")
    monkeypatch.setenv("MYOS_ACL_BACKEND", "legacy")

    monkeypatch.setenv("MYOS_ACL_USER", "bertha")
    assert ScopeApi(str(root)).acl_summary(str(root / "finanz"), []) == {"hasAcls": False}

    monkeypatch.setenv("MYOS_ACL_USER", "anna")
    assert ScopeApi(str(root)).acl_summary(str(root / "finanz"), [])["hasAcls"] is True
