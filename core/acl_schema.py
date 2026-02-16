from __future__ import annotations

from typing import Dict, List, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from core.acl import ACLPolicy, PermissionRule

ALLOWED_RIGHTS = {"read", "write", "execute", "change", "delete", "*"}


def _normalize_name(value: str) -> str:
    return str(value or "").strip().lower()


def _normalize_path(path: str) -> str:
    text = str(path or "").strip()
    if not text:
        raise ValueError("path must not be empty")
    if not text.startswith("/"):
        text = f"/{text}"
    if text != "/*":
        text = text.rstrip("/")
    return text


class ACLRuleModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    rights: Set[str] = Field(default_factory=set)

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        path = _normalize_path(value)
        # // Security: reject path traversal-like fragments in ACL definitions.
        if "/../" in f"{path}/" or path.endswith("/.."):
            raise ValueError("path traversal fragments are not allowed")
        return path

    @field_validator("rights")
    @classmethod
    def _validate_rights(cls, values: Set[str]) -> Set[str]:
        normalized = {_normalize_name(item) for item in (values or set()) if str(item).strip()}
        if not normalized:
            raise ValueError("rights must not be empty")
        unknown = sorted(right for right in normalized if right not in ALLOWED_RIGHTS)
        if unknown:
            raise ValueError(f"unsupported rights: {', '.join(unknown)}")
        return normalized


class ACLDocumentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    roles: Dict[str, List[ACLRuleModel]] = Field(default_factory=dict)
    users: Dict[str, Set[str]] = Field(default_factory=dict)

    @field_validator("roles")
    @classmethod
    def _validate_roles(cls, value: Dict[str, List[ACLRuleModel]]) -> Dict[str, List[ACLRuleModel]]:
        normalized: Dict[str, List[ACLRuleModel]] = {}
        for raw_role, rules in (value or {}).items():
            role = _normalize_name(raw_role)
            if not role:
                raise ValueError("role names must not be empty")
            normalized[role] = list(rules or [])
        return normalized

    @field_validator("users")
    @classmethod
    def _validate_users(cls, value: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        normalized: Dict[str, Set[str]] = {}
        for raw_user, role_values in (value or {}).items():
            user = _normalize_name(raw_user)
            if not user:
                raise ValueError("user names must not be empty")
            normalized[user] = {_normalize_name(role) for role in (role_values or set()) if str(role).strip()}
        return normalized

    @model_validator(mode="after")
    def _validate_user_roles_exist(self) -> "ACLDocumentModel":
        known_roles = set(self.roles.keys())
        for user, roles in self.users.items():
            unknown = sorted(role for role in roles if role not in known_roles)
            if unknown:
                raise ValueError(f"user '{user}' references unknown roles: {', '.join(unknown)}")
        return self

    def to_acl_policy(self) -> ACLPolicy:
        permissions: Dict[str, List[PermissionRule]] = {}
        for role, rules in self.roles.items():
            permissions[role] = [
                PermissionRule(path=rule.path, rights=set(rule.rights))
                for rule in rules
            ]
        return ACLPolicy(
            roles=set(self.roles.keys()),
            permissions=permissions,
            users={user: set(roles) for user, roles in self.users.items()},
        )


def acl_policy_from_document(data: dict) -> ACLPolicy:
    doc = ACLDocumentModel.model_validate(data)
    return doc.to_acl_policy()

