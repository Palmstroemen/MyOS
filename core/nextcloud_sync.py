# nextcloud_sync.py - bring a project's ACLs.md and embryos into its Nextcloud Team folder
#
# What `myacl sync` does, as one piece the CLI and the MyOS core service share
# ("cloud/nextcloud/Designdocument MyOS Core Service.md", 8, step 2): compare the Team folder
# with what MyOS says - the rules of ACLs.md (core/acl_nextcloud.py) and the embryos of the
# templates (core/cloud_embryos.py) - and send what differs. The project may be a local copy
# (myacl sync) or the shadow tree of the Team folder itself (the core service).

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from core.acl import ACLPolicy
from core.acl_edit import may_change_acls
from core.acl_nextcloud import Change, Plan, diff, plan, read_nextcloud_md, rights_files, updates
from core.cloud_embryos import EmbryoChange, EmbryoSet, cloud_paths, compare as compare_embryos, embryo_sets, readable_paths
from core.cloud_embryos import send as send_embryos
from core.nextcloud_dav import tree_functions


class SyncRefused(Exception):
    """The project cannot be brought into the cloud as it is (the reason is the message)."""


@dataclass
class Comparison:
    plan: Plan  # the rules ACLs.md gives, with notes on what Nextcloud cannot hold
    changes: List[Change]  # rules that differ from the Team folder's
    embryo_changes: List[EmbryoChange]

    @property
    def pending(self) -> List[EmbryoChange]:
        """Embryo changes that send something."""
        return [c for c in self.embryo_changes if c.manifest_changed or c.upload or c.remove]

    @property
    def in_step(self) -> bool:
        return not (self.changes or self.pending)


class NextcloudSync:
    """The Team folder dav (core.nextcloud_dav.NextcloudDAV) against the project at
    project_root, whose .MyOS/Nextcloud.md names the accounts and the Team folder's groups."""

    def __init__(self, project_root: Path, dav) -> None:
        self.project_root = Path(project_root)
        settings_file = self.project_root / ".MyOS" / "Nextcloud.md"
        if not settings_file.is_file():
            raise SyncRefused(f"{settings_file} is missing (# Nextcloud: url, folder, group; # Accounts: person: account)")
        self.settings, self.accounts = read_nextcloud_md(settings_file)
        if not self.groups:
            # The groups the Team folder is given to are locked out at the root; rules on the
            # way rely on it (they leave share to be inherited from there).
            raise SyncRefused(f"{settings_file} needs group in # Nextcloud")
        self.policy = ACLPolicy.for_tree(self.project_root)
        self.embryos: List[EmbryoSet] = embryo_sets(self.project_root)
        self.dav = dav

    def someone_may_change(self) -> bool:
        """Whether one of the people of ACLs.md may still change the rights. Not so, the file
        is most likely broken (its parser is lenient: garbage names no one) - sending it would
        take every rule away. MyOS refuses such an edit too (core/acl_edit.py, no lock-out)."""
        return any(may_change_acls(self.policy, user) for user in self.policy.users)

    @property
    def groups(self) -> List[str]:
        """The groups the Team folder is given to ("group: Projekte, Gäste")."""
        return team_groups(self.settings)

    def compare(self) -> Comparison:
        """The rules as the Team folder holds them now, with the embryos as they will be."""
        embryo_changes = compare_embryos(self.embryos, self.dav)
        tree = self.dav.tree()
        there = [e for e, c in zip(self.embryos, embryo_changes) if not c.missing]
        exists, children = with_embryos(*tree_functions(tree), there)
        result = plan(self.policy, self.accounts, exists, children, base_groups=self.groups,
                      readable=readable_paths(there), protected=rights_files(all_paths(children)))
        return Comparison(result, diff(result.rules, tree), embryo_changes)

    def send(self, comparison: Comparison) -> List[Change]:
        """Send what comparison found; the changes still open afterwards (none when all went)."""
        # The embryos first: their rules (readable for who may read where they are born) need them there.
        by_path = {e.path: e for e in self.embryos}
        for change in comparison.pending:
            send_embryos(by_path[change.project], change, self.dav)
        now = self.compare()
        for rule_path, rules in updates(now.plan.rules, now.changes):
            self.dav.set_rules(rule_path, rules)
        return self.compare().changes


def team_groups(settings: Dict[str, str]) -> List[str]:
    """The groups the Team folder is given to ("group: Projekte, Gäste")."""
    return [g.strip() for g in settings.get("group", "").split(",") if g.strip()]


def all_paths(children: Callable[[str], List[str]]) -> List[str]:
    """Every path of a tree given by children(path), from the root."""
    found, pending = [], ["/"]
    while pending:
        path = pending.pop()
        found.append(path)
        pending.extend(("" if path == "/" else path) + "/" + name for name in children(path))
    return found


def with_embryos(exists, children, embryos: List[EmbryoSet]) -> Tuple[Callable[[str], bool], Callable[[str], List[str]]]:
    """exists and children as they are once the embryos are uploaded."""
    added = {path for e in embryos for path in cloud_paths(e)}
    kids: Dict[str, set] = {}
    for path in added:
        parent, _, name = path.rpartition("/")
        kids.setdefault(parent or "/", set()).add(name)

    def with_exists(path):
        return path in added or exists(path)

    def with_children(path):
        return sorted(set(children(path)) | kids.get(path, set()))

    return with_exists, with_children
