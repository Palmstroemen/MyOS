"""ACL rules in ACLs.md are relative to the project root; ScopeApi checks absolute paths.

The enforcement must translate between the two, otherwise only "/*" rules ever match.
"""

from pathlib import Path

import pytest

from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_USER", "MYOS_ACL_BACKEND", "MYOS_ACL_AUDIT"):
        monkeypatch.delenv(key, raising=False)


def _lab(tmp_path: Path) -> Path:
    root = tmp_path / "lab"
    (root / "Finanz").mkdir(parents=True)
    (root / "HR").mkdir()
    (root / "Finanz" / "budget.md").write_text("# b\n", encoding="utf-8")
    return root


def test_relative_rule_filters_listing(tmp_path):
    root = _lab(tmp_path)
    policy = ACLPolicy(
        roles={"finance"},
        permissions={"finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})]},
        users={"bertha": {"finance"}},
    )
    api = ScopeApi(str(root))
    api.set_acl_enforcement(ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode="enforce"), user="bertha")

    assert [e["name"] for e in api.list_entries(str(root))] == ["Finanz"]
    assert [e["name"] for e in api.list_entries(str(root / "Finanz"))] == ["budget.md"]


def test_real_acls_file_from_env_is_enforced(tmp_path, monkeypatch):
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (root / "Templates" / "Standard" / "finanz").mkdir(parents=True)
    (root / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhalter\n- /finanz/: read, write\n\n# Users\nBertha: Buchhalter\n"
    )
    (root / "finanz").mkdir()
    (root / "privat").mkdir()
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")
    monkeypatch.setenv("MYOS_ACL_BACKEND", "legacy")
    monkeypatch.setenv("MYOS_ACL_USER", "bertha")

    api = ScopeApi(str(root))
    names = [e["name"] for e in api.list_entries(str(root))]

    assert "finanz" in names
    assert "privat" not in names


def test_subproject_is_enforced_with_the_parent_acls(tmp_path, monkeypatch):
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhalter\n- /finanz/: read, write\n\n# Users\nBertha: Buchhalter\n"
    )
    sub = root / "finanz" / "Kunde"
    (sub / ".MyOS").mkdir(parents=True)
    (sub / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (sub / "rechnungen").mkdir()
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")
    monkeypatch.setenv("MYOS_ACL_BACKEND", "legacy")
    monkeypatch.setenv("MYOS_ACL_USER", "bertha")

    api = ScopeApi(str(sub))

    assert [e["name"] for e in api.list_entries(str(sub)) if not e["name"].startswith(".")] == ["rechnungen"]


def test_folder_rules_are_enforced_in_subproject_template_folders(tmp_path, monkeypatch):
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (root / "Templates" / "Standard" / "finanz").mkdir(parents=True)
    (root / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Folder\n- /{Folder}/: read, write\n\n## Familie\n- /Familie/: read\n\n"
        "# Users\nBertha: finanz, Familie\n"
    )
    sub = root / "Familie"
    (sub / ".MyOS").mkdir(parents=True)
    (sub / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (sub / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (sub / "finanz").mkdir()
    (sub / "finanz" / "beleg.md").write_text("x")
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")
    monkeypatch.setenv("MYOS_ACL_BACKEND", "legacy")
    monkeypatch.setenv("MYOS_ACL_USER", "bertha")

    api = ScopeApi(str(sub))

    assert api._acl_probe("write", sub / "finanz" / "beleg.md").allowed is True
    assert api._acl_probe("write", sub / "x.md").allowed is False  # Familie may only read
