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
#   Security: entries created later in such a folder would inherit that read. So these
#   rules are marked - they leave share to be inherited (mask 15; share is denied at the
#   root for everyone, so the rights are the same) - and the server app myos_acl
#   (cloud/nextcloud) locks new entries of a folder with marked rules right away. Every
#   folder on the way gets a marked rule of its own, also where it would inherit the same.
# - Without a rule the Team folder's own permissions apply: everyone gets a rule at the root.

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from core.acl import ACLPolicy, _nearest_rules, _normalize_path, _rule_base
from core.brand import META_DIR

# MyOS right -> Nextcloud permissions. execute and change have none; share is never given
# (it would pass files on beyond ACLs.md).
NEXTCLOUD_PERMISSIONS = ("read", "write", "create", "delete", "share")
_MAP = {"read": {"read"}, "write": {"write", "create"}, "delete": {"delete"}}
_ALL_RIGHTS = {"read", "write", "execute", "change", "delete"}


@dataclass(frozen=True)
class PlannedRule:
    path: str  # project-relative, "/" for the root
    kind: str  # "user" | "group"
    account: str  # Nextcloud user or group id
    allowed: FrozenSet[str]  # Nextcloud permissions; all others are denied
    traverse: bool = False  # read only to pass on the way down (marked, see above)


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
    base_groups: Iterable[str] = (),
    readable: Iterable[Tuple[str, Optional[str]]] = (),
    protected: Iterable[str] = (),
) -> Plan:
    """
    The Nextcloud rules for policy (ACLPolicy.for_tree of the project, whose root is the
    Team folder's root): per person with an account, rules only where their rights change.
    base_groups, the groups the Team folder is given to, get a rule without rights at the
    root, so only the people's own rules let anyone in. readable: (path, reader) pairs - path
    (with all below, up to a deeper pair) may be read besides by who may read reader, by
    everyone with rights in the project when reader is None: the embryos the Files app shows,
    each for who may read where it is born (core/cloud_embryos.readable_paths); those not
    there yet are skipped. protected: the rights and sync
    files of .MyOS folders (rights_files): only who may change the rights there (change on that
    .MyOS/ACLs.md) may write them, everyone else keeps at most read.
    """
    result = Plan()
    rules = _mappable_rules(policy, result.notes)
    if any("change" in r.rights or "*" in r.rights for role_rules in rules.values() for r in role_rules):
        result.notes.append("change is not copied: who may manage the rules is set for the whole Team folder")
    missing: Set[str] = set()
    for group in base_groups:
        result.rules.append(PlannedRule("/", "group", group, frozenset()))
    for person, roles in sorted(policy.users.items()):
        account = accounts.get(person)
        if not account:
            result.notes.append(f"{policy.display_name(person)} has no Nextcloud account in # Accounts: no rules")
            continue
        for path, allowed, way in _person_rules([rules.get(role, []) for role in roles], exists, children, missing, list(readable), list(protected)):
            result.rules.append(PlannedRule(path, "user", account, allowed, traverse=way))
    for path in sorted(missing):
        result.notes.append(f"{path} is not there yet: its rules follow when it exists")
    return result


# In a .MyOS folder: what manages the rights and the sync (ACLs.md as in MyOS, where change
# grants writing it; its history, the cloud settings, the embryos myacl sync uploads).
RIGHTS_FILES = ("ACLs.md", "ACLs-history", "Nextcloud.md", "Embryos.json", "Embryos")


def rights_files(paths: Iterable[str]) -> List[str]:
    """The RIGHTS_FILES among paths (project-relative): entries right inside a .MyOS folder."""
    found = []
    for path in paths:
        parent, _, name = path.rpartition("/")
        if name in RIGHTS_FILES and parent.rpartition("/")[2] == META_DIR:
            found.append(path)
    return sorted(found)


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


def _nextcloud(our_rights: Iterable[str]) -> FrozenSet[str]:
    rights = set(our_rights)
    if "*" in rights:
        rights = set(_ALL_RIGHTS)
    return frozenset(p for right in rights for p in _MAP.get(right, ()))


def _parents(path: str) -> List[str]:
    """Strict ancestors of path, root first."""
    parts = [part for part in path.split("/") if part]
    return ["/" + "/".join(parts[:depth]) if depth else "/" for depth in range(len(parts))]


def _child(path: str, name: str) -> str:
    return ("" if path == "/" else path) + "/" + name


def _below(path: str, top: str) -> bool:
    return path == top or path.startswith(top + "/")


def _person_rules(
    role_rules: List[list], exists, children, missing: Set[str], readable: List[Tuple[str, Optional[str]]] = (),
    protected: List[str] = (),
) -> List[Tuple[str, FrozenSet[str], bool]]:
    opened: Dict[str, bool] = {}  # readable path -> read for this person, once they have rights at all

    def own_rights(path: str) -> Set[str]:
        key = _normalize_path(path)
        found: Set[str] = set()
        for rules in role_rules:
            for rule in _nearest_rules(rules, key):
                found |= set(rule.rights)
        return found

    def our_rights(path: str) -> Set[str]:
        found = own_rights(path)
        tops = [top for top in opened if _below(path, top)]
        if tops and opened[max(tops, key=len)]:  # the deepest pair decides
            found.add("read")
        return found

    def may_change(path: str) -> bool:
        acls = path.rsplit(f"/{META_DIR}/", 1)[0] + f"/{META_DIR}/ACLs.md"
        return bool({"change", "*"} & our_rights(acls))

    def rights(path: str) -> FrozenSet[str]:
        allowed = _nextcloud(our_rights(path))
        if any(_below(path, top) and not may_change(top) for top in protected):
            allowed = allowed & {"read"}
        return allowed

    bases = {"/"}
    for rules in role_rules:
        for rule in rules:
            base = _rule_base(rule.path) or "/"
            if exists(base):
                bases.add(base)
            else:
                missing.add(base)
    if any(rights(base) for base in bases):
        for path, reader in readable:
            if exists(path):
                opened[path] = reader is None or bool({"read", "*"} & own_rights(reader))
        bases.update(opened)
        bases.update(path for path in protected if exists(path))
    granted = [base for base in bases if rights(base)]
    walk = set(bases)
    for base in bases:
        walk.update(_parents(base))
    traverse = {p for base in granted for p in _parents(base) if "read" not in rights(p)}
    for path in traverse:
        walk.update(_child(path, name) for name in children(path))

    planned: List[Tuple[str, FrozenSet[str], bool]] = []
    target: Dict[str, FrozenSet[str]] = {}
    for path in sorted(walk, key=lambda p: (p.count("/") if p != "/" else 0, p)):
        own = rights(path) | ({"read"} if path in traverse else set())
        target[path] = frozenset(own)
        parent = _parents(path)[-1] if path != "/" else None
        # Below a rule on the way every entry gets its own: the server app locks what is new there.
        if parent is None or path in traverse or parent in traverse or target[path] != target[parent]:
            planned.append((path, target[path], path in traverse))
    return planned


# Nextcloud's permission bits; a planned rule fixes all of them, a rule on the way all
# but share.
BITS = {"read": 1, "write": 2, "create": 4, "delete": 8, "share": 16}
FULL_MASK = 31
TRAVERSE_MASK = FULL_MASK & ~BITS["share"]


def mask_of(rule: PlannedRule) -> int:
    return TRAVERSE_MASK if rule.traverse else FULL_MASK


def bits(allowed: Iterable[str]) -> int:
    return sum(BITS[p] for p in set(allowed))


@dataclass(frozen=True)
class Change:
    path: str
    kind: str
    account: str
    before: Optional[object]  # the rule Nextcloud holds (core.nextcloud_dav.ExistingRule), None: new
    after: Optional[FrozenSet[str]]  # the planned permissions, None: the rule goes


def diff(planned: Iterable[PlannedRule], tree) -> List[Change]:
    """What would change in Nextcloud (tree: core.nextcloud_dav tree) to hold the planned
    rules; rules not planned (not from ACLs.md) would go."""
    existing = {(path, r.kind, r.account): r for path, entry in tree.items() for r in entry.rules}
    wanted = {(r.path, r.kind, r.account): r for r in planned}
    changes = []
    for key in sorted(set(existing) | set(wanted)):
        before, rule = existing.get(key), wanted.get(key)
        if before is not None and rule is not None and (before.mask, before.permissions) == (mask_of(rule), bits(rule.allowed)):
            continue
        changes.append(Change(*key, before=before, after=None if rule is None else rule.allowed))
    return changes


def updates(planned: Iterable[PlannedRule], changes: Iterable[Change]) -> List[Tuple[str, List[PlannedRule]]]:
    """
    What to send for changes: Nextcloud replaces all rules of a path at once, so per changed
    path its whole planned list (empty: all its rules go). Deepest paths first, so the
    account that syncs keeps its way down until the parents are done.
    """
    planned = list(planned)
    paths = {change.path for change in changes}
    ordered = sorted(paths, key=lambda p: (-(p.count("/") if p != "/" else 0), p))
    return [(path, [rule for rule in planned if rule.path == path]) for path in ordered]
