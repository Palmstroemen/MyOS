from __future__ import annotations

from dataclasses import dataclass
import fnmatch
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from core.config.parser import MarkdownConfigParser
from core.project import ProjectConfig

try:
    import casbin as _casbin
except Exception:  # pragma: no cover - optional dependency
    _casbin = None


def _normalize_role(name: str) -> str:
    return name.strip().lower()


def _normalize_path(path: str) -> str:
    normalized = path.strip()
    if normalized == "/*":
        return normalized
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    return normalized.rstrip("/")


@dataclass(frozen=True)
class PermissionRule:
    path: str
    rights: Set[str]


@dataclass(frozen=True)
class ACLPolicy:
    roles: Set[str]
    permissions: Dict[str, List[PermissionRule]]
    users: Dict[str, Set[str]]

    @classmethod
    def from_project(cls, project_root: Path) -> "ACLPolicy":
        project_root = Path(project_root)
        config = ProjectConfig(project_root)
        if not config.is_valid():
            raise ValueError(f"Not a valid MyOS project: {project_root}")

        template_roles = _roles_from_templates(project_root, config.templates)
        acl_roles, role_permissions, folder_defaults, users = _roles_from_acls(project_root)

        roles = {*_normalize_roles(template_roles), *_normalize_roles(acl_roles)}
        permissions = _build_permissions(
            roles=roles,
            template_roles=_normalize_roles(template_roles),
            role_permissions=_normalize_permissions(role_permissions),
            folder_defaults=_normalize_permissions({"folder": folder_defaults}).get("folder", []),
        )

        return cls(roles=roles, permissions=permissions, users=_normalize_users(users))

    def roles_for_user(self, username: str) -> Set[str]:
        user_key = username.strip().lower()
        return self.users.get(user_key, set())

    def can_access(self, role: str, path: str, right: str = "read") -> bool:
        role_key = _normalize_role(role)
        path_key = _normalize_path(path)
        right_key = right.strip().lower()

        if role_key not in self.roles:
            return False

        rules = self.permissions.get(role_key, [])
        for rule in rules:
            if _path_matches(rule.path, path_key):
                if "*" in rule.rights or right_key in rule.rights:
                    return True
        return False


class ACLAuthorizer:
    """Optional authorizer wrapper with pluggable backend."""

    def __init__(self, policy: ACLPolicy, backend: str = "auto") -> None:
        self.policy = policy
        requested = str(backend or "auto").strip().lower()
        if requested not in {"auto", "legacy", "casbin"}:
            requested = "auto"
        self.backend = requested
        self._enforcer = None

        if self.backend == "auto":
            self.backend = "casbin" if _casbin is not None else "legacy"
        elif self.backend == "casbin" and _casbin is None:
            self.backend = "legacy"

        if self.backend == "casbin":
            self._enforcer = _build_casbin_enforcer(self.policy)

    @classmethod
    def from_project(cls, project_root: Path, backend: str = "auto") -> "ACLAuthorizer":
        return cls(ACLPolicy.from_project(project_root), backend=backend)

    def can_access(self, role: str, path: str, right: str = "read") -> bool:
        role_key = _normalize_role(role)
        path_key = _normalize_path(path)
        right_key = str(right or "read").strip().lower()
        if self.backend == "casbin" and self._enforcer is not None:
            return bool(self._enforcer.enforce(role_key, path_key, right_key))
        return self.policy.can_access(role_key, path_key, right_key)

    def can_user_access(self, username: str, path: str, right: str = "read") -> bool:
        user_key = str(username or "").strip().lower()
        path_key = _normalize_path(path)
        right_key = str(right or "read").strip().lower()
        if self.backend == "casbin" and self._enforcer is not None:
            return bool(self._enforcer.enforce(user_key, path_key, right_key))
        for role in self.policy.roles_for_user(user_key):
            if self.policy.can_access(role, path_key, right_key):
                return True
        return False


def _path_matches(rule_path: str, target_path: str) -> bool:
    # Support both legacy prefix-based rules and lightweight glob patterns
    # like /Finanz/** while keeping existing ACL behavior stable.
    if rule_path == "/*":
        return True
    if rule_path == target_path or target_path.startswith(f"{rule_path}/"):
        return True
    if "**" in rule_path:
        # /Finanz/** should match /Finanz and all descendants.
        if rule_path.endswith("/**"):
            prefix = rule_path[:-3]
            if target_path == prefix or target_path.startswith(f"{prefix}/"):
                return True
    if "*" in rule_path or "?" in rule_path:
        return fnmatch.fnmatchcase(target_path, rule_path)
    return False


def _build_casbin_enforcer(policy: ACLPolicy):
    if _casbin is None:  # pragma: no cover - guarded by caller
        return None

    model_conf = """
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && pathMatch(r.obj, p.obj) && (p.act == "*" || p.act == r.act)
"""
    model = _casbin.model.Model()
    model.load_model_from_text(model_conf)
    enforcer = _casbin.Enforcer(model)
    enforcer.add_function("pathMatch", _casbin_path_match)

    for role, rules in policy.permissions.items():
        for rule in rules:
            rights = set(rule.rights or set())
            if "*" in rights:
                enforcer.add_policy(role, rule.path, "*")
                continue
            for right in rights:
                enforcer.add_policy(role, rule.path, right)

    for user, roles in policy.users.items():
        for role in roles:
            enforcer.add_grouping_policy(user, role)
    return enforcer


def _casbin_path_match(request_path: str, policy_path: str) -> bool:
    return _path_matches(str(policy_path or ""), str(request_path or ""))


def _roles_from_templates(project_root: Path, template_names: Iterable[str]) -> Set[str]:
    roles: Set[str] = set()
    templates_root = project_root / "Templates"
    for template in template_names:
        template_dir = templates_root / template
        if not template_dir.exists():
            continue
        for child in template_dir.iterdir():
            if child.is_dir():
                roles.add(child.name)
    return roles


def _roles_from_acls(
    project_root: Path,
) -> Tuple[Set[str], Dict[str, Dict[str, Set[str]]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    myos_dir = project_root / ".MyOS"
    acl_file = myos_dir / "ACLs.md"
    if not acl_file.exists():
        return set(), {}, {}, {}

    data = MarkdownConfigParser.parse_file(acl_file)

    roles: Set[str] = set()
    role_permissions: Dict[str, Dict[str, Set[str]]] = {}
    folder_defaults: Dict[str, Set[str]] = {}
    users: Dict[str, Set[str]] = {}

    for section_name, section_data in data.items():
        section_key = section_name.strip()
        if section_key.lower() in {"permissions", "inherit", "roles"}:
            continue
        if section_key.lower() == "users":
            if isinstance(section_data, dict):
                for user, roles_list in section_data.items():
                    if isinstance(roles_list, list):
                        users[str(user)] = {str(r) for r in roles_list}
                    else:
                        users[str(user)] = {str(roles_list)}
            continue
        if not isinstance(section_data, dict):
            continue

        if section_key.lower() == "folder":
            folder_defaults = _normalize_rule_dict(section_data)
            continue

        roles.add(section_key)
        role_permissions[section_key] = _normalize_rule_dict(section_data)

    return roles, role_permissions, folder_defaults, users


def _normalize_roles(roles: Iterable[str]) -> Set[str]:
    return {_normalize_role(role) for role in roles if str(role).strip()}


def _normalize_permissions(permissions: Dict[str, Dict[str, Set[str]]]) -> Dict[str, Dict[str, Set[str]]]:
    normalized: Dict[str, Dict[str, Set[str]]] = {}
    for role, rules in permissions.items():
        role_key = _normalize_role(role)
        normalized[role_key] = _normalize_rule_dict(rules)
    return normalized


def _normalize_users(users: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    normalized: Dict[str, Set[str]] = {}
    for user, roles in users.items():
        user_key = user.strip().lower()
        normalized[user_key] = {_normalize_role(r) for r in roles if str(r).strip()}
    return normalized


def _normalize_rule_dict(rule_dict: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    normalized: Dict[str, Set[str]] = {}
    for raw_path, rights in rule_dict.items():
        raw_key = str(raw_path).lstrip()
        if raw_key.startswith("- "):
            raw_key = raw_key[2:]
        if raw_key.startswith("* "):
            raw_key = raw_key[2:]
        path_key = _normalize_path(raw_key)
        if not isinstance(rights, (list, set, tuple)):
            rights_set = {str(rights).strip().lower()}
        else:
            rights_set = {str(r).strip().lower() for r in rights}
        normalized[path_key] = rights_set
    return normalized


def _build_permissions(
    roles: Set[str],
    template_roles: Set[str],
    role_permissions: Dict[str, Dict[str, Set[str]]],
    folder_defaults: Dict[str, Set[str]],
) -> Dict[str, List[PermissionRule]]:
    permissions: Dict[str, List[PermissionRule]] = {}

    for role in roles:
        role_key = _normalize_role(role)

        if role_key in role_permissions:
            rules = _expand_rules(role_key, role_permissions[role_key])
        elif role_key in template_roles:
            rules = _expand_rules(role_key, folder_defaults)
        else:
            rules = []

        permissions[role_key] = [PermissionRule(path, rights) for path, rights in rules.items()]

    return permissions


def _expand_rules(role: str, rules: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    expanded: Dict[str, Set[str]] = {}
    for path, rights in rules.items():
        if "{folder}" in path.lower():
            path = path.replace("{Folder}", role).replace("{folder}", role)
        normalized_path = _normalize_path(path)
        if normalized_path in expanded:
            expanded[normalized_path] = expanded[normalized_path].union(rights)
        else:
            expanded[normalized_path] = rights
    return expanded
