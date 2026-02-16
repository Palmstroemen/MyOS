from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


def _build_monitor_service(finance_path_rule: str = "/Finanz/**") -> ACLEnforcementService:
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path=finance_path_rule, rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode="monitor")


def test_scope_api_monitor_mode_logs_denied_but_does_not_block_create(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_monitor_service(), user="bertha")

    created = api.create_folder(str(root), "HR")

    assert created is not None
    assert (root / "HR").exists()
    events = api.get_acl_audit_events()
    assert len(events) >= 1
    assert any(e["action"] == "create_folder" for e in events)
    denied_event = next(e for e in events if e["action"] == "create_folder")
    assert denied_event["mode"] == "monitor"
    assert denied_event["allowed"] is True
    assert denied_event["reason"] == "monitor_override"


def test_scope_api_monitor_mode_logs_allowed_read(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    finanz.mkdir(parents=True)
    (finanz / "report.md").write_text("# q1\n", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_monitor_service(f"{finanz}/**"), user="bertha")

    entries = api.list_entries(str(finanz))
    assert any(item["name"] == "report.md" for item in entries)

    events = api.get_acl_audit_events()
    read_event = next(e for e in events if e["action"] == "read_dir")
    assert read_event["mode"] == "monitor"
    assert read_event["reason"] == "policy_allowed"
    assert read_event["allowed"] is True

