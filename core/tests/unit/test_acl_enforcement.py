from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLCheckRequest, ACLEnforcementService


def _build_authorizer() -> ACLAuthorizer:
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLAuthorizer(policy, backend="legacy")


def test_acl_enforcement_off_mode_allows_and_marks_bypass():
    service = ACLEnforcementService(_build_authorizer(), mode="off")
    result = service.check(ACLCheckRequest(user="bertha", action="read", resource="/HR"))

    assert result.allowed is True
    assert result.enforced is False
    assert result.reason == "acl_off"
    assert result.mode == "off"


def test_acl_enforcement_monitor_mode_logs_denied_but_allows():
    events = []
    service = ACLEnforcementService(_build_authorizer(), mode="monitor", audit_sink=events.append)
    result = service.check(ACLCheckRequest(user="bertha", action="read", resource="/HR"))

    assert result.allowed is True
    assert result.enforced is False
    assert result.reason == "monitor_override"
    assert result.mode == "monitor"
    assert len(events) == 1
    assert events[0]["policy_allowed"] is False
    assert events[0]["allowed"] is True


def test_acl_enforcement_enforce_mode_blocks_denied_access():
    events = []
    service = ACLEnforcementService(_build_authorizer(), mode="enforce", audit_sink=events.append)
    denied = service.check(ACLCheckRequest(user="bertha", action="read", resource="/HR"))
    allowed = service.check(ACLCheckRequest(user="bertha", action="read", resource="/Finanz/Q1"))

    assert denied.allowed is False
    assert denied.enforced is True
    assert denied.reason == "policy_denied"
    assert allowed.allowed is True
    assert allowed.reason == "policy_allowed"
    assert len(events) == 2
    assert events[0]["mode"] == "enforce"
    assert events[0]["resource"] == "/HR"
    assert events[1]["resource"] == "/Finanz/Q1"


def test_acl_enforcement_invalid_mode_fails_closed_to_enforce():
    service = ACLEnforcementService(_build_authorizer(), mode="weird")
    result = service.check(ACLCheckRequest(user="bertha", action="read", resource="/HR"))

    assert result.mode == "enforce"
    assert result.allowed is False
