import json

from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


def _build_monitor_service() -> ACLEnforcementService:
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode="monitor")


def test_scope_api_writes_acl_audit_events_to_file(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    audit_path = root / ".MyOS" / "audit.log"

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_monitor_service(), user="bertha")
    api.set_acl_audit_file(str(audit_path), max_bytes=64_000)

    created = api.create_folder(str(root), "HR")
    assert created is not None
    assert audit_path.exists()

    lines = audit_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 1
    payload = json.loads(lines[-1])
    assert payload["action"] == "create_folder"
    assert payload["mode"] == "monitor"
    assert payload["resource"] == str(root)


def test_scope_api_rotates_acl_audit_file_when_limit_exceeded(tmp_path):
    root = tmp_path / "lab"
    root.mkdir()
    audit_path = root / ".MyOS" / "audit.log"
    rotated_path = root / ".MyOS" / "audit.log.1"

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_monitor_service(), user="bertha")
    api.set_acl_audit_file(str(audit_path), max_bytes=4_096)

    for idx in range(64):
        api.create_folder(str(root), f"f{idx}")

    assert audit_path.exists()
    assert rotated_path.exists()
    assert audit_path.stat().st_size <= 4_096
    assert rotated_path.stat().st_size > 0
