# acl_view.py - side-effect-free ACL answers for display (Scope, PostFix)

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Tuple

from core.acl import ACLPolicy, _normalize_path, _rule_base, find_acl_project_root

# Rights a "*" grant stands for (ACL design document, MVP rights set), in display order.
RIGHTS_ORDER = ("read", "write", "execute", "change", "delete")
ALL_RIGHTS = frozenset(RIGHTS_ORDER)


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

    def may_view(self, viewer: Optional[str]) -> bool:
        """
        Whether viewer may see these ACLs (who may do what) in a GUI panel.
        Security: with enforcement on, the panels show the content of ACLs.md, so only a
        user who may read ACLs.md sees them. viewer None means no enforcement.
        """
        if viewer is None:
            return True
        return "read" in self.rights_for_user(viewer, self.project_root / ".MyOS" / "ACLs.md")

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
        return self._principals_at(rel)

    def _principals_at(self, rel: str) -> List[Principal]:
        role_rights = {role: self._rights_for_role(role, rel) for role in self.policy.roles}
        name = self.policy.display_name
        roles = [Principal(name(role), "role", r, role) for role, r in sorted(role_rights.items()) if r]
        users = []
        for user, user_roles in sorted(self.policy.users.items()):
            rights = frozenset().union(*(role_rights.get(role, frozenset()) for role in user_roles))
            if rights:
                users.append(Principal(name(user), "user", rights, user))
        return roles + users

    def listing_summary(self, folder, entry_paths) -> dict:
        """
        Who may do what in a listed folder, for the ACL filter panel.

        principals: roles, then users, each {id, name, kind, rights, section, partial, count}.
          section "folder": has rights on the folder itself (rights = those rights);
            partial: some listed entry is closed to it, so filtering by it hides entries.
          section "exception": no rights on the folder, but on count of its entries.
        access: entry path (as given) -> ids of the principals with any right on it.
        """
        folder_principals = self.principals(folder)
        folder_rel = self.relative_path(folder)
        folder_text = str(Path(folder).expanduser().resolve()) if folder_rel is not None else ""
        access: Dict[str, List[str]] = {}
        entry_count: Dict[str, int] = {}
        found: Dict[str, Principal] = {}
        for entry in entry_paths:
            # Entries directly in the (resolved) folder need no resolve() of their own:
            # with thousands of entries that syscall would dominate the time.
            parent, _, name = str(entry).rpartition("/")
            if folder_rel is not None and parent == folder_text and name not in ("", ".", ".."):
                rel = (folder_rel.rstrip("/") + "/" + name)
            else:
                rel = self.relative_path(entry)
            ids = []
            for principal in (self._principals_at(rel) if rel is not None else []):
                pid = f"{principal.kind}:{principal.key}"
                ids.append(pid)
                entry_count[pid] = entry_count.get(pid, 0) + 1
                found.setdefault(pid, principal)
            access[str(entry)] = ids

        total = len(access)
        result = []
        folder_ids = set()
        for principal in folder_principals:
            pid = f"{principal.kind}:{principal.key}"
            folder_ids.add(pid)
            result.append(self._summary_item(
                principal, pid, "folder", entry_count.get(pid, 0) < total, entry_count.get(pid, 0)))
        exceptions = [(pid, p) for pid, p in found.items() if pid not in folder_ids]
        exceptions.sort(key=lambda item: (item[1].kind != "role", item[0]))
        for pid, principal in exceptions:
            result.append(self._summary_item(principal, pid, "exception", True, entry_count[pid]))
        return {"principals": result, "access": access}

    @staticmethod
    def _summary_item(principal: Principal, pid: str, section: str, partial: bool, count: int) -> dict:
        return {
            "id": pid,
            "name": principal.name,
            "kind": principal.kind,
            "rights": [r for r in RIGHTS_ORDER if r in principal.rights] if section == "folder" else [],
            "section": section,
            "partial": bool(partial),
            "count": int(count),
        }

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

