#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myacl - MyOS ACLs CLI: who may do what, every rule of a project, and its rules in a Nextcloud
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.acl import ACLPolicy
from core.acl_enforcement import configured_mode
from core.acl_nextcloud import BITS, FULL_MASK, NEXTCLOUD_PERMISSIONS, local_tree, plan, read_nextcloud_md, rights_files
from core.acl_view import RIGHTS_ORDER, ACLView
from core.cloud_embryos import embryo_sets, readable_paths
from core.identity import acl_user_for
from core.nextcloud_dav import NextcloudDAV, NextcloudError
from core.nextcloud_sync import NextcloudSync, SyncRefused, all_paths, team_groups, with_embryos


class _Refused(Exception):
    pass


def parse_args(args=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MyOS ACLs utility")
    sub = parser.add_subparsers(dest="command", required=True)

    show_cmd = sub.add_parser("show", help="Who may do what at a path, and where it comes from")
    show_cmd.add_argument("path", nargs="?", default=".")

    check_cmd = sub.add_parser("check", help="A person's rights at a path (exit 1: right missing)")
    check_cmd.add_argument("person")
    check_cmd.add_argument("path")
    check_cmd.add_argument("right", nargs="?", choices=RIGHTS_ORDER)

    rules_cmd = sub.add_parser("rules", help="Every rule of the project, folder rules resolved into subprojects")
    rules_cmd.add_argument("path", nargs="?", default=".")
    rules_cmd.add_argument("--json", action="store_true", help="Output as JSON")

    sync_cmd = sub.add_parser("sync", help="The project's rules in a Nextcloud Team folder (settings: .MyOS/Nextcloud.md)")
    sync_cmd.add_argument("path", nargs="?", default=".")
    sync_cmd.add_argument("--plan", action="store_true", help="Only show the rules Nextcloud should hold (no network)")
    sync_cmd.add_argument("--dry-run", action="store_true",
                          help="Read the rules Nextcloud holds and show what would change; sends nothing "
                               "(login: MYOS_NEXTCLOUD_USER, MYOS_NEXTCLOUD_PASSWORD)")
    sync_cmd.add_argument("--yes", action="store_true", help="Send without asking (needed without a terminal)")
    sync_cmd.add_argument("--json", action="store_true", help="Output as JSON")

    return parser.parse_args(args)


def main() -> None:
    args = parse_args()
    try:
        if args.command == "show":
            code = _show(args.path)
        elif args.command == "check":
            code = _check(args.person, args.path, args.right)
        elif args.command == "rules":
            code = _rules(args.path, args.json)
        else:
            code = _sync(args.path, args.plan, args.dry_run, args.yes, args.json)
        sys.exit(code)
    except BrokenPipeError:  # output cut short (myacl rules | head)
        sys.exit(0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


def _view(path: str):
    """View of the ACLs.md governing path, or None. Raises when the user may not see it."""
    view = ACLView.for_path(path)
    if view is None:
        return None
    # Security: with enforcement on, only a user who may read ACLs.md sees its content
    # (same rule as Scope's ACL panel and PostFix).
    viewer = acl_user_for(path) if configured_mode() == "enforce" else None
    if not view.may_view(viewer):
        raise _Refused(f"{viewer} may not see the ACLs of {path}")
    return view


def _rights_text(rights) -> str:
    """Rights in RIGHTS_ORDER ("*" = all), others after them; "none" without any."""
    rights = set(RIGHTS_ORDER) if "*" in rights else set(rights) - {"none"}
    ordered = [r for r in RIGHTS_ORDER if r in rights] + sorted(rights - set(RIGHTS_ORDER))
    return ", ".join(ordered) or "none"


def _rights_list(rights) -> list:
    text = _rights_text(rights)
    return [] if text == "none" else text.split(", ")


def _table(rows) -> None:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]) - 1)]
    for row in rows:
        print("  " + "  ".join(cell.ljust(width) for cell, width in zip(row, widths)) + "  " + row[-1])


def _show(path: str) -> int:
    view = _view(path)
    if view is None:
        print(f"No ACLs.md governs {path}.")
        return 0
    rel = view.relative_path(path) or "/"
    print(f"{rel}   (rules: {view.project_root / '.MyOS' / 'ACLs.md'})")
    principals = view.principals(path)
    roles = [p for p in principals if p.kind == "role"]
    people = [p for p in principals if p.kind == "user"]
    if not principals:
        print("\nNobody has rights here.")
    if roles:
        print("\nRoles")
        rows = []
        for p in roles:
            origin = view.origin(p.key, path)
            rows.append([p.name, _rights_text(p.rights), "here" if origin == rel else f"from {origin}"])
        _table(rows)
    if people:
        print("\nPeople")
        name = view.policy.display_name
        _table([[p.name, _rights_text(p.rights), ", ".join(sorted(name(r) for r in view.policy.users[p.key]))]
                for p in people])
    return 0


def _check(person: str, path: str, right) -> int:
    view = _view(path)
    if view is None:
        raise _Refused(f"No ACLs.md governs {path}")
    if person.strip().lower() not in view.policy.users:
        print(f"{person} is not listed in # Users of {view.project_root / '.MyOS' / 'ACLs.md'}", file=sys.stderr)
    rights = view.rights_for_user(person, path)
    if right is None:
        print(_rights_text(rights))
        return 0
    print("yes" if right in rights else "no")
    return 0 if right in rights else 1


def _rules(path: str, as_json: bool) -> int:
    view = _view(path)
    if view is None:
        raise _Refused(f"No ACLs.md governs {path}")
    policy = ACLPolicy.for_tree(view.project_root)
    name = policy.display_name
    roles = {
        name(role): {(rule.path or "/"): _rights_list(rule.rights) for rule in sorted(rules, key=lambda r: r.path)}
        for role, rules in sorted(policy.permissions.items(), key=lambda item: name(item[0]).lower())
        if rules
    }
    users = {name(user): sorted(name(r) for r in roles_of) for user, roles_of in sorted(policy.users.items())}
    if as_json:
        print(json.dumps({"project": str(view.project_root), "roles": roles, "users": users}, indent=2, ensure_ascii=False))
        return 0
    print(f"{view.project_root}")
    rows = [[role, rule_path, ", ".join(rights) or "none"] for role, rules in roles.items() for rule_path, rights in rules.items()]
    if rows:
        print("\nRules")
        _table(rows)
    if users:
        print("\nPeople")
        _table([[user, ", ".join(roles_of) or "-"] for user, roles_of in users.items()])
    return 0


def _nextcloud_order(allowed) -> list:
    return [p for p in NEXTCLOUD_PERMISSIONS if p in allowed]


def _describe(rule) -> str:
    """A rule Nextcloud holds, as permissions: all fixed ("read, write") or partly ("+read, -write; rest inherited")."""
    if rule.mask == FULL_MASK:
        return ", ".join(p for p in NEXTCLOUD_PERMISSIONS if rule.permissions & BITS[p]) or "-"
    fixed = [("+" if rule.permissions & BITS[p] else "-") + p for p in NEXTCLOUD_PERMISSIONS if rule.mask & BITS[p]]
    return ", ".join(fixed) + "; rest inherited"


def _print_notes(notes) -> None:
    if notes:
        print("\nNotes")
        for note in notes:
            print(f"  {note}")


def _sync(path: str, plan_only: bool, dry_run: bool, yes: bool, as_json: bool) -> int:
    if as_json and not (plan_only or dry_run):
        raise _Refused("--json only with --plan or --dry-run")
    view = _view(path)
    if view is None:
        raise _Refused(f"No ACLs.md governs {path}")
    settings_file = view.project_root / ".MyOS" / "Nextcloud.md"
    if not settings_file.is_file():
        raise _Refused(f"{settings_file} is missing (# Nextcloud: url, folder, group; # Accounts: person: account)")
    settings, accounts = read_nextcloud_md(settings_file)
    if plan_only:
        embryos = embryo_sets(view.project_root)
        exists, children = with_embryos(*local_tree(view.project_root), embryos)
        result = plan(ACLPolicy.for_tree(view.project_root), accounts, exists, children,
                      base_groups=team_groups(settings), readable=readable_paths(embryos),
                      protected=rights_files(all_paths(children)))
        return _show_plan(view.project_root, result, as_json)

    missing = [key for key in ("url", "folder", "group") if not settings.get(key)]
    if missing:
        # group: the groups the Team folder is given to are locked out at the root; rules
        # on the way rely on it (they leave share to be inherited from there).
        raise _Refused(f"{settings_file} needs {', '.join(missing)} in # Nextcloud")
    user, password = os.environ.get("MYOS_NEXTCLOUD_USER", ""), os.environ.get("MYOS_NEXTCLOUD_PASSWORD", "")
    if not (user and password):
        raise _Refused("set MYOS_NEXTCLOUD_USER and MYOS_NEXTCLOUD_PASSWORD (best an app password) for the login")
    try:
        sync = NextcloudSync(view.project_root, NextcloudDAV(settings["url"], user, password, settings["folder"]))
        comparison = sync.compare()
    except (NextcloudError, SyncRefused) as exc:
        raise _Refused(str(exc)) from exc
    changes = comparison.changes
    if as_json:
        rows = [{"path": c.path, "kind": c.kind, "account": c.account,
                 "before": None if c.before is None else {"mask": c.before.mask, "permissions": c.before.permissions},
                 "after": None if c.after is None else _nextcloud_order(c.after)} for c in changes]
        embryo_rows = [{"project": c.project, "missing": c.missing, "manifest": c.manifest_changed,
                        "upload": c.upload, "remove": c.remove} for c in comparison.embryo_changes]
        print(json.dumps({"changes": rows, "embryos": embryo_rows, "tags": comparison.tags, "notes": comparison.plan.notes},
                         indent=2, ensure_ascii=False))
        return 0
    sent = "nothing sent (--dry-run)" if dry_run else ("in sync" if comparison.in_step else "to send")
    print(f"{settings['url']}  {settings['folder']}  (as {user}): {len(changes)} change(s), {sent}")
    _print_embryo_changes(comparison.embryo_changes)
    if comparison.tags:
        print("\nTags to make (from Tags.md): " + ", ".join(comparison.tags))
    _print_changes(changes)
    _print_notes(comparison.plan.notes)
    if dry_run or comparison.in_step:
        return 0
    if not yes:
        if not sys.stdin.isatty():
            raise _Refused("not sent: confirm with --yes when there is no terminal to ask")
        if input(f"\nSend this to {settings['url']}? [y/N] ").strip().lower() not in ("y", "yes", "j", "ja"):
            print("Nothing sent.")
            return 1
    try:
        left = sync.send(comparison)
    except NextcloudError as exc:
        raise _Refused(f"{exc} (part of it may already be sent; run again)") from exc
    if sync.refused_tags:
        print("\nTags not made (may only admins make tags?): " + ", ".join(sync.refused_tags))
    if left:
        print(f"\nSent, but {len(left)} change(s) are still open:")
        _print_changes(left)
        return 1
    print("\nSent; Nextcloud now holds the rules of ACLs.md.")
    return 0


def _print_embryo_changes(embryo_changes) -> None:
    for c in embryo_changes:
        if c.missing:
            print(f"Embryos of {c.project}: the folder is not in the cloud yet, left out")
        elif c.manifest_changed or c.upload or c.remove:
            parts = (["Embryos.json"] if c.manifest_changed else []) + \
                    ([f"{len(c.upload)} file(s) up"] if c.upload else []) + ([f"{len(c.remove)} removed"] if c.remove else [])
            print(f"Embryos of {c.project}: {', '.join(parts)}")


def _print_changes(changes) -> None:
    rows = []
    for c in changes:
        if c.before is None:
            rows.append(["+", c.path, c.kind, c.account, ", ".join(_nextcloud_order(c.after)) or "-"])
        elif c.after is None:
            rows.append(["-", c.path, c.kind, c.account, f"was {_describe(c.before)}; not from ACLs.md"])
        else:
            rows.append(["~", c.path, c.kind, c.account,
                         f"{', '.join(_nextcloud_order(c.after)) or '-'}  (was {_describe(c.before)})"])
    if rows:
        print()
        _table(rows)


def _show_plan(project_root, result, as_json: bool) -> int:
    if as_json:
        rules = [{"path": r.path, "kind": r.kind, "account": r.account, "allowed": _nextcloud_order(r.allowed),
                  "way": r.traverse} for r in result.rules]
        print(json.dumps({"project": str(project_root), "rules": rules, "notes": result.notes}, indent=2, ensure_ascii=False))
        return 0
    print(f"{project_root}  ->  Nextcloud rules (all other permissions denied)")
    rows = [[r.path, r.kind, r.account, (", ".join(_nextcloud_order(r.allowed)) or "-") + (" (way)" if r.traverse else "")]
            for r in sorted(result.rules, key=lambda r: (r.path, r.kind, r.account))]
    if rows:
        print()
        _table(rows)
    _print_notes(result.notes)
    return 0

if __name__ == "__main__":
    main()
