from pathlib import Path

from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


def _build_service(mode: str, root: Path) -> ACLEnforcementService:
    finance_rule = f"{(root / 'Finanz').resolve()}/**"
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path=finance_rule, rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode=mode)


def test_scope_api_enforce_blocks_rename_entry_when_source_not_allowed(tmp_path):
    root = tmp_path / "lab"
    hr = root / "HR"
    hr.mkdir(parents=True)
    source = hr / "note.md"
    source.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    renamed = api.rename_entry(str(source), "renamed")

    assert renamed is None
    assert source.exists()


def test_scope_api_enforce_allows_rename_entry_when_source_allowed(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    finanz.mkdir(parents=True)
    source = finanz / "note.md"
    source.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    renamed = api.rename_entry(str(source), "renamed")

    assert renamed is not None
    assert renamed.endswith("renamed.md")
    assert not source.exists()
    assert (finanz / "renamed.md").exists()


def test_scope_api_enforce_blocks_batch_rename_for_denied_source(tmp_path):
    root = tmp_path / "lab"
    hr = root / "HR"
    hr.mkdir(parents=True)
    source = hr / "img001.jpg"
    source.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    report = api.rename_entries_batch([str(source)], "img", "foto")

    assert report["ok"] is False
    assert report["renamed"] == []
    assert report["failed"] == 1
    assert any(err["reason"] == "acl_denied" for err in report["errors"])
    assert source.exists()
