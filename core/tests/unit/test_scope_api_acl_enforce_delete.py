from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


def _build_service(mode: str) -> ACLEnforcementService:
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode=mode)


def test_scope_api_enforce_blocks_delete_without_permission(tmp_path):
    root = tmp_path / "lab"
    target = root / "secret.txt"
    root.mkdir()
    target.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce"), user="bertha")

    report = api.delete_entries([str(target)])

    assert report["ok"] is False
    assert report["deleted"] == []
    assert any(err["reason"] == "acl_denied" for err in report["errors"])
    assert target.exists()
    events = api.get_acl_audit_events()
    deny_event = next(e for e in events if e["action"] == "delete")
    assert deny_event["mode"] == "enforce"
    assert deny_event["allowed"] is False
    assert deny_event["reason"] == "policy_denied"


def test_scope_api_enforce_allows_delete_for_admin(tmp_path):
    root = tmp_path / "lab"
    target = root / "note.txt"
    root.mkdir()
    target.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce"), user="alfred")

    report = api.delete_entries([str(target)])

    assert report["ok"] is True
    assert report["deleted"] == [str(target)]
    assert report["errors"] == []
    assert not target.exists()
