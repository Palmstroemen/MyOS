# acl_nextcloud.py - a project's ACLs as Nextcloud Team folder rules ("advanced permissions")
#
# ACLs.md stays the source; this only computes what Nextcloud should hold (plan) and has no
# network. Findings behind it (ProjectLogbook, test of 2026-11-07):
# - Nextcloud's rules are per path and per user or group, inherited, and every permission
#   bit inherits on its own (mask). A rule here fixes every bit, so the nearest rule wins as
#   in MyOS.
# - Rules are per person (account), not per group: creating groups needs a Nextcloud admin.
#   A person's rights are the union of their roles, computed by ACLPolicy as everywhere.
# - Nextcloud needs read on every parent folder. Who has rights only deep down gets read on
#   the way there, and every other entry on the way is locked (else it would inherit read).
#   Security: entries created later on that way inherit that read until the next sync.
# - Without a rule the Team folder's own permissions apply: everyone gets a rule at the root.

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from core.acl import ACLPolicy, _nearest_rules, _normalize_path, _rule_base

# MyOS right -> Nextcloud permissions. execute and change have none; share is never given
# (it would pass files on beyond ACLs.md).
NEXTCLOUD_PERMISSIONS = ("read", "write", "create", "delete", "share")
_MAP = {"read": {"read"}, "write": {"write", "create"}, "delete": {"delete"}}
_ALL_MYOS = {"read", "write", "execute", "change", "delete"}


@dataclass(frozen=True)
class PlannedRule:
    path: str  # project-relative, "/" for the root
    kind: str  # "user" | "group"
    account: str  # Nextcloud user or group id
    allowed: FrozenSet[str]  # Nextcloud permissions; all others are denied


@dataclass
class Plan:
    rules: List[PlannedRule] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def local_tree(root: Path) -> Tuple[Callable[[str], bool], Callable[[str], List[str]]]:
    """exists(path) and children(path) for project-relative paths, from the local folder."""
    root = Path(root)

    def _disk(path: str) -> Path:
        return root.joinpath(*[part for part in path.split("/") if part])

    def exists(path: str) -> bool:
        return os.path.lexists(_disk(path))

    def children(path: str) -> List[str]:
        try:
            return sorted(entry.name for entry in os.scandir(_disk(path)) if entry.is_dir() or entry.is_file())
        except OSError:
            return []

    return exists, children


def read_nextcloud_md(path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    A project's .MyOS/Nextcloud.md: (settings of "# Nextcloud", lower-case keys, e.g. url,
    folder, group; people of "# Accounts", lower-case person -> account, "Anna Huber: anna.h").
    """
    sections: Dict[str, Dict[str, str]] = {"nextcloud": {}, "accounts": {}}
    section = None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {}, {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip().lower()
        elif section in sections and ":" in stripped:
            key, _, value = stripped.lstrip("-* ").partition(":")
            if key.strip() and value.strip():
                sections[section][key.strip().lower()] = value.strip()
    return sections["nextcloud"], sections["accounts"]


def plan(
    policy: ACLPolicy,
    accounts: Dict[str, str],
    exists: Callable[[str], bool],
    children: Callable[[str], List[str]],
    base_group: Optional[str] = None,
) -> Plan:
    """
    The Nextcloud rules for policy (ACLPolicy.for_tree of the project, whose root is the
    Team folder's root): per person with an account, rules only where their rights change.
    base_group, the group the Team folder is given to, gets a rule without rights at the
    root, so only the people's own rules let anyone in.
    """
    result = Plan()
    rules = _mappable_rules(policy, result.notes)
    if any("change" in r.rights or "*" in r.rights for role_rules in rules.values() for r in role_rules):
        result.notes.append("change is not copied: who may manage the rules is set for the whole Team folder")
    missing: Set[str] = set()
    if base_group:
        result.rules.append(PlannedRule("/", "group", base_group, frozenset()))
    for person, roles in sorted(policy.users.items()):
        account = accounts.get(person)
        if not account:
            result.notes.append(f"{policy.display_name(person)} has no Nextcloud account in # Accounts: no rules")
            continue
        for path, allowed in _person_rules([rules.get(role, []) for role in roles], exists, children, missing):
            result.rules.append(PlannedRule(path, "user", account, allowed))
    for path in sorted(missing):
        result.notes.append(f"{path} is not there yet: its rules follow when it exists")
    return result


def _mappable_rules(policy: ACLPolicy, notes: List[str]) -> Dict[str, list]:
    """Rules per role that Nextcloud can hold: for a folder, /folder/** and /*."""
    kept: Dict[str, list] = {}
    for role, role_rules in sorted(policy.permissions.items()):
        for rule in role_rules:
            path = rule.path
            plain = path[:-3] if path.endswith("/**") else path
            if path == "/*" or not re.search(r"[*?\[]", plain):
                kept.setdefault(role, []).append(rule)
            else:
                notes.append(f"{policy.display_name(role)}: {path} is a pattern Nextcloud cannot hold: left out")
    return kept


def _nextcloud(myos_rights: Iterable[str]) -> FrozenSet[str]:
    rights = set(myos_rights)
    if "*" in rights:
        rights = set(_ALL_MYOS)
    return frozenset(p for right in rights for p in _MAP.get(right, ()))


def _parents(path: str) -> List[str]:
    """Strict ancestors of path, root first."""
    parts = [part for part in path.split("/") if part]
    return ["/" + "/".join(parts[:depth]) if depth else "/" for depth in range(len(parts))]


def _child(path: str, name: str) -> str:
    return ("" if path == "/" else path) + "/" + name


def _person_rules(role_rules: List[list], exists, children, missing: Set[str]) -> List[Tuple[str, FrozenSet[str]]]:
    def rights(path: str) -> FrozenSet[str]:
        key = _normalize_path(path)
        found: Set[str] = set()
        for rules in role_rules:
            for rule in _nearest_rules(rules, key):
                found |= set(rule.rights)
        return _nextcloud(found)

    bases = {"/"}
    for rules in role_rules:
        for rule in rules:
            base = _rule_base(rule.path) or "/"
            if exists(base):
                bases.add(base)
            else:
                missing.add(base)
    granted = [base for base in bases if rights(base)]
    walk = set(bases)
    for base in bases:
        walk.update(_parents(base))
    traverse = {p for base in granted for p in _parents(base) if "read" not in rights(p)}
    for path in traverse:
        walk.update(_child(path, name) for name in children(path))

    planned: List[Tuple[str, FrozenSet[str]]] = []
    target: Dict[str, FrozenSet[str]] = {}
    for path in sorted(walk, key=lambda p: (p.count("/") if p != "/" else 0, p)):
        own = rights(path) | ({"read"} if path in traverse else set())
        target[path] = frozenset(own)
        parent = _parents(path)[-1] if path != "/" else None
        if parent is None or target[path] != target[parent]:
            planned.append((path, target[path]))
    return planned
