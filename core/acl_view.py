# acl_view.py - side-effect-free ACL answers for display (Scope, PostFix)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

from core.acl import ACLPolicy, _normalize_path, _rule_base, find_acl_project_root

# Rights a "*" grant stands for (ACL design document, MVP rights set).
ALL_RIGHTS = frozenset({"read", "write", "execute", "change"})


@dataclass(frozen=True)
class Principal:
    """A role or user that has at least one right on a path."""

    name: str  # as written in ACLs.md / on disk, for display
    kind: str  # "role" | "user"
    rights: FrozenSet[str]
    key: str = ""  # lower-case key used by the policy


class ACLView:
    """
    Read-only view on a project's ACLs.md for the GUI: what may a user do here,
    who may do what here, and does a folder have rules of its own.

    Unlike ACLEnforcementService.check it emits no audit events, so it can be asked
    for every row of a listing. It takes absolute filesystem paths, as the GUI has
    them, and maps them to the project-relative paths ACLs.md is written in.
    """

    # project root -> (ACLs.md mtime, view); reloaded when the file changes.
    _cache: Dict[Path, Tuple[float, "ACLView"]] = {}

    def __init__(self, policy: ACLPolicy, project_root: Path) -> None:
        self.policy = policy
        self.project_root = Path(project_root).resolve()

    @classmethod
    def for_path(cls, path) -> Optional["ACLView"]:
        """View for the ACLs.md governing path (inherited into subprojects), or None."""
        root = find_acl_project_root(path)
        if root is None:
            return None
        acl_file = root / ".MyOS" / "ACLs.md"
        try:
            mtime = acl_file.stat().st_mtime
        except OSError:
            return None
        cached = cls._cache.get(root)
        if cached is not None and cached[0] == mtime:
            return cached[1]
        try:
            view = cls(ACLPolicy.from_project(root), root)
        except Exception:
            return None
        cls._cache[root] = (mtime, view)
        return view

    def relative_path(self, path) -> Optional[str]:
        """Project-relative path as written in ACLs.md ("/" for the root), or None outside."""
        try:
            rel = Path(path).expanduser().resolve().relative_to(self.project_root)
        except (OSError, ValueError):
            return None
        text = str(rel).replace("\\", "/")
        return "/" if text in ("", ".") else "/" + text

    def _rights_for_role(self, role: str, rel: str) -> FrozenSet[str]:
        rights = self.policy.rights_for(role, rel)
        if "*" in rights:
            return ALL_RIGHTS
        return frozenset(rights - {"none"})

    def rights_for_role(self, role: str, path) -> FrozenSet[str]:
        rel = self.relative_path(path)
        if rel is None:
            return frozenset()
        return self._rights_for_role(str(role).strip().lower(), rel)

    def rights_for_user(self, user: str, path) -> FrozenSet[str]:
        rel = self.relative_path(path)
        if rel is None:
            return frozenset()
        rights = set()
        for role in self.policy.roles_for_user(str(user)):
            rights |= self._rights_for_role(role, rel)
        return frozenset(rights)

    def principals(self, path) -> List[Principal]:
        """Roles, then users, that have any right on path (sorted by name)."""
        rel = self.relative_path(path)
        if rel is None:
            return []
        role_rights = {role: self._rights_for_role(role, rel) for role in self.policy.roles}
        name = self.policy.display_name
        roles = [Principal(name(role), "role", r, role) for role, r in sorted(role_rights.items()) if r]
        users = []
        for user, user_roles in sorted(self.policy.users.items()):
            rights = frozenset().union(*(role_rights.get(role, frozenset()) for role in user_roles))
            if rights:
                users.append(Principal(name(user), "user", rights, user))
        return roles + users

    def has_own_rules(self, path) -> bool:
        """
        True if some rule addresses exactly this path (it has rules of its own);
        False if all rights here are inherited from rules on parent folders.
        """
        rel = self.relative_path(path)
        if rel is None:
            return False
        key = _normalize_path(rel)
        for rules in self.policy.permissions.values():
            for rule in rules:
                if _rule_base(rule.path) == key:
                    return True
        return False

