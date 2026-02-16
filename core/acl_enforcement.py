from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from core.acl import ACLAuthorizer

AuditSink = Callable[[Dict[str, object]], None]


@dataclass(frozen=True)
class ACLCheckRequest:
    user: str
    action: str
    resource: str


@dataclass(frozen=True)
class ACLCheckResult:
    allowed: bool
    enforced: bool
    reason: str
    mode: str


class ACLEnforcementService:
    """Feature-flagged ACL enforcement wrapper with audit events."""

    def __init__(
        self,
        authorizer: ACLAuthorizer,
        mode: str = "off",
        audit_sink: Optional[AuditSink] = None,
    ) -> None:
        self.authorizer = authorizer
        self.mode = self._normalize_mode(mode)
        self._audit_sink = audit_sink

    @staticmethod
    def _normalize_mode(raw_mode: str) -> str:
        mode = str(raw_mode or "").strip().lower()
        if mode in {"off", "monitor", "enforce"}:
            return mode
        # // Security: unknown modes fail closed to strict enforcement.
        return "enforce"

    def check(self, request: ACLCheckRequest) -> ACLCheckResult:
        user = str(request.user or "").strip().lower()
        action = str(request.action or "").strip().lower() or "read"
        resource = str(request.resource or "").strip() or "/"

        policy_allowed = self.authorizer.can_user_access(user, resource, action)
        if self.mode == "off":
            result = ACLCheckResult(allowed=True, enforced=False, reason="acl_off", mode=self.mode)
        elif self.mode == "monitor":
            reason = "policy_allowed" if policy_allowed else "monitor_override"
            result = ACLCheckResult(allowed=True, enforced=False, reason=reason, mode=self.mode)
        else:
            reason = "policy_allowed" if policy_allowed else "policy_denied"
            result = ACLCheckResult(allowed=policy_allowed, enforced=True, reason=reason, mode=self.mode)

        self._emit_audit_event(
            user=user,
            action=action,
            resource=resource,
            policy_allowed=policy_allowed,
            result=result,
        )
        return result

    def _emit_audit_event(
        self,
        *,
        user: str,
        action: str,
        resource: str,
        policy_allowed: bool,
        result: ACLCheckResult,
    ) -> None:
        if self._audit_sink is None:
            return
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "mode": result.mode,
            "policy_allowed": bool(policy_allowed),
            "allowed": bool(result.allowed),
            "enforced": bool(result.enforced),
            "reason": result.reason,
            "backend": self.authorizer.backend,
        }
        self._audit_sink(event)

