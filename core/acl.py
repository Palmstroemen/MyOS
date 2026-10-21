from __future__ import annotations

from dataclasses import dataclass, field, replace
import fnmatch
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from core.config.parser import MarkdownConfigParser
from core.project import ProjectConfig, find_config_in_parents

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
    # Normalized (lower-case) role/user key -> name as written (for display).
    display_names: Dict[str, str] = field(default_factory=dict)
    # "## Folder" rules, the roles with a section of their own and, per such role, the
    # folders its section writes explicit entries for: needed to apply the folder rules
    # again inside subprojects (for_context), where an explicit entry for the same folder
    # replaces the inherited one.
    folder_defaults: Dict[str, Set[str]] = field(default_factory=dict)
    own_sections: Set[str] = field(default_factory=set)
    explicit_bases: Dict[str, Set[str]] = field(default_factory=dict)

    def display_name(self, key: str) -> str:
        return self.display_names.get(key, key)

    @classmethod
    def from_project(cls, project_root: Path, acl_file: Optional[Path] = None) -> "ACLPolicy":
        """Policy of project_root; acl_file replaces its .MyOS/ACLs.md (to check a draft)."""
        project_root = Path(project_root)
        config = ProjectConfig(project_root)
        if not config.is_valid():
            raise ValueError(f"Not a valid MyOS project: {project_root}")

        template_roles = _roles_from_templates(project_root, config.get_effective_templates())
        acl_roles, role_permissions, folder_defaults, users = _roles_from_acls(project_root, acl_file)
        normalized_defaults = _normalize_permissions({"folder": folder_defaults}).get("folder", {})
        normalized_sections = _normalize_permissions(role_permissions)

        roles = {*_normalize_roles(template_roles), *_normalize_roles(acl_roles)}
        # Template roles keep their folder's real name: {Folder} must expand to it
        # (paths are case-sensitive, role keys are lower-case).
        folder_names = {_normalize_role(name): name for name in template_roles}
        permissions = _build_permissions(
            roles=roles,
            template_roles=_normalize_roles(template_roles),
            role_permissions=normalized_sections,
            folder_defaults=normalized_defaults,
            folder_names=folder_names,
        )
        explicit_bases = {
            role: {_rule_base(path) for path in _expand_rules(folder_names.get(role, role), rules)}
            for role, rules in normalized_sections.items()
        }
        display_names = {
            **folder_names,
            **{_normalize_role(name): name for name in acl_roles},
            **{str(user).strip().lower(): str(user).strip() for user in users},
        }

        return cls(
            roles=roles,
            permissions=permissions,
            users=_normalize_users(users),
            display_names=display_names,
            folder_defaults=normalized_defaults,
            own_sections=set(normalized_sections),
            explicit_bases=explicit_bases,
        )

    def for_context(self, project_root: Path, context: Optional[Path]) -> "ACLPolicy":
        """
        This policy as seen from context, a (sub)project governed by project_root's
        ACLs.md: the "## Folder" rules apply again to the template folders of every
        subproject between them, with the subproject's path in front
        (/{Folder}/ -> /Familie/04_Finanz/ for the role 04_Finanz), also for roles with a
        section of their own, unless that section has an explicit entry for that folder.
        """
        if context is None or not self.folder_defaults:
            return self
        root = Path(project_root).resolve()
        try:
            rel_parts = Path(context).resolve().relative_to(root).parts
        except ValueError:
            return self
        permissions = {role: list(rules) for role, rules in self.permissions.items()}
        roles = set(self.roles)
        display_names = dict(self.display_names)
        for depth in range(1, len(rel_parts) + 1):
            sub = root.joinpath(*rel_parts[:depth])
            if not (sub / ".MyOS" / "Project.md").exists():
                continue
            try:
                folders = _roles_from_templates(sub, ProjectConfig(sub).get_effective_templates())
            except Exception:
                continue
            prefix = "/" + "/".join(rel_parts[:depth])
            for folder in folders:
                role_key = _normalize_role(folder)
                explicit = self.explicit_bases.get(role_key, set())
                for path, rights in _expand_rules(folder, self.folder_defaults).items():
                    sub_path = _normalize_path(prefix + ("" if path == "/" else path))
                    if _rule_base(sub_path) in explicit:
                        continue  # the role's own entry for this folder wins
                    permissions.setdefault(role_key, []).append(PermissionRule(sub_path, set(rights)))
                roles.add(role_key)
                display_names.setdefault(role_key, folder)
        return replace(self, roles=roles, permissions=permissions, display_names=display_names)

    def roles_for_user(self, username: str) -> Set[str]:
        user_key = username.strip().lower()
        return self.users.get(user_key, set())

    def rights_for(self, role: str, path: str) -> Set[str]:
        """
        Rights of a role at path as written in ACLs.md ("*" = all, "none" = locked out).
        Per role the nearest rule wins: a rule on a deeper folder replaces what the role
        would inherit from rules on its parents, also when it grants less.
        """
        role_key = _normalize_role(role)
        if role_key not in self.roles:
            return set()
        rights: Set[str] = set()
        for rule in _nearest_rules(self.permissions.get(role_key, []), _normalize_path(path)):
            rights |= set(rule.rights)
        return rights

    def can_access(self, role: str, path: str, right: str = "read") -> bool:
        rights = self.rights_for(role, path)
        return "*" in rights or right.strip().lower() in rights


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
    def from_project(cls, project_root: Path, backend: str = "auto", context: Optional[Path] = None) -> "ACLAuthorizer":
        """Authorizer for project_root's ACLs.md as seen from context (see ACLPolicy.for_context)."""
        return cls(ACLPolicy.from_project(project_root).for_context(project_root, context), backend=backend)

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


def find_acl_project_root(path) -> Optional[Path]:
    """
    Project whose ACLs.md governs path: the nearest project with an ACLs.md, walking up.
    A subproject without ACLs.md inherits its parent's rules directly; their paths stay
    relative to the project that holds the ACLs.md.
    """
    try:
        acl_file = find_config_in_parents(Path(path).expanduser(), "ACLs.md", honor_inherit_not=False)
    except OSError:
        return None
    return acl_file.parent.parent.resolve() if acl_file is not None else None


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


def _rule_base(rule_path: str) -> str:
    """Folder a rule is written for: /finanz/** and /finanz/* -> /finanz, /* -> root."""
    parts = []
    for part in rule_path.split("/"):
        if any(ch in part for ch in "*?["):
            break
        parts.append(part)
    return _normalize_path("/".join(parts) or "/")


def _rule_depth(rule_path: str) -> int:
    """How deep in the tree a rule's folder is (root = 0)."""
    return len([part for part in _rule_base(rule_path).split("/") if part])


def _nearest_rules(rules: Iterable[PermissionRule], target_path: str) -> List[PermissionRule]:
    """Rules of one role that match target_path and are written for the deepest folder."""
    matching = [rule for rule in rules if _path_matches(rule.path, target_path)]
    if not matching:
        return []
    depth = max(_rule_depth(rule.path) for rule in matching)
    return [rule for rule in matching if _rule_depth(rule.path) == depth]


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
m = g(r.sub, p.sub) && pathMatch(r.obj, p.obj) && nearestRule(r.obj, p.obj, p.sub) && (p.act == "*" || p.act == r.act)
"""
    model = _casbin.model.Model()
    model.load_model_from_text(model_conf)
    enforcer = _casbin.Enforcer(model)
    enforcer.add_function("pathMatch", _casbin_path_match)

    def _casbin_nearest_rule(request_path: str, policy_path: str, role: str) -> bool:
        # Same "nearest rule per role wins" as ACLPolicy.rights_for, so both backends agree.
        nearest = _nearest_rules(policy.permissions.get(str(role), []), str(request_path or ""))
        return any(rule.path == str(policy_path) for rule in nearest)

    enforcer.add_function("nearestRule", _casbin_nearest_rule)

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
    templates_root = _resolve_templates_dir(project_root)
    if not templates_root or not templates_root.exists():
        return roles
    for template in template_names:
        template_dir = templates_root / template
        if not template_dir.exists():
            continue
        for child in template_dir.iterdir():
            if child.is_dir():
                roles.add(child.name)
    return roles


def _resolve_templates_dir(project_root: Path) -> Optional[Path]:
    env_dir = os.environ.get("MYOS_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    current = Path(project_root).expanduser().resolve()
    while True:
        candidate = current / "Templates"
        if candidate.exists():
            return candidate
        if current == current.parent:
            break
        current = current.parent
    return None


def _roles_from_acls(
    project_root: Path,
    acl_file: Optional[Path] = None,
) -> Tuple[Set[str], Dict[str, Dict[str, Set[str]]], Dict[str, Set[str]], Dict[str, Set[str]]]:
    acl_file = Path(acl_file) if acl_file is not None else project_root / ".MyOS" / "ACLs.md"
    if not acl_file.exists():
        return set(), {}, {}, {}

    try:
        text = acl_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:  # same as MarkdownConfigParser.parse_file
        text = acl_file.read_text(encoding="latin-1")
    data = MarkdownConfigParser.parse(_acl_rule_text(text))

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


def _acl_rule_text(text: str) -> str:
    """ACLs.md reduced to headings and rule lines, for the general config parser."""
    # Security: the general parser ends a section at a blank line or free text, which in
    # ACLs.md would silently drop the rules below (a dropped `none` opens a locked folder).
    # So a rule belongs to the heading above it, whatever stands in between: blank lines,
    # notes and <!-- comments --> are removed here. Commented-out rules do not apply.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    kept: List[str] = []
    section: Optional[str] = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower()
            kept.append(stripped)
            continue
        if section is None or ":" not in stripped.partition("#")[0]:
            continue  # front matter, blank lines and notes
        is_rule = stripped.startswith(("- ", "* "))
        if is_rule or section == "users":
            kept.append(stripped)
    return "\n".join(kept) + "\n"


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
    folder_names: Optional[Dict[str, str]] = None,
) -> Dict[str, List[PermissionRule]]:
    permissions: Dict[str, List[PermissionRule]] = {}
    folder_names = folder_names or {}

    for role in roles:
        role_key = _normalize_role(role)
        folder_name = folder_names.get(role_key, role_key)

        # Like Windows: template folder roles inherit the "## Folder" rules; their own
        # section adds explicit entries, and an explicit entry for the same folder
        # replaces the inherited one there.
        rules = _expand_rules(folder_name, role_permissions.get(role_key, {}))
        if role_key in template_roles:
            explicit = {_rule_base(path) for path in rules}
            for path, rights in _expand_rules(folder_name, folder_defaults).items():
                if _rule_base(path) not in explicit:
                    rules[path] = rights

        permissions[role_key] = [PermissionRule(path, rights) for path, rights in rules.items()]

    return permissions


def _expand_rules(folder_name: str, rules: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    """Rules with {Folder} replaced by the role's folder name (as written on disk)."""
    expanded: Dict[str, Set[str]] = {}
    for path, rights in rules.items():
        if "{folder}" in path.lower():
            path = path.replace("{Folder}", folder_name).replace("{folder}", folder_name)
        normalized_path = _normalize_path(path)
        if normalized_path in expanded:
            expanded[normalized_path] = expanded[normalized_path].union(rights)
        else:
            expanded[normalized_path] = rights
    return expanded
