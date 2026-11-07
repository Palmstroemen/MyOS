#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myacl - MyOS ACLs CLI: who may do what, every rule of a project, and its rules in a Nextcloud
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.acl import ACLPolicy
from core.acl_enforcement import configured_mode
from core.acl_nextcloud import NEXTCLOUD_PERMISSIONS, local_tree, plan, read_nextcloud_md
from core.acl_view import RIGHTS_ORDER, ACLView
from core.identity import acl_user_for


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
            code = _sync(args.path, args.plan, args.json)
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


def _sync(path: str, plan_only: bool, as_json: bool) -> int:
    if not plan_only:
        raise _Refused("only --plan is there yet: the rules are not sent to Nextcloud")
    view = _view(path)
    if view is None:
        raise _Refused(f"No ACLs.md governs {path}")
    settings_file = view.project_root / ".MyOS" / "Nextcloud.md"
    if not settings_file.is_file():
        raise _Refused(f"{settings_file} is missing (# Nextcloud: url, group; # Accounts: person: account)")
    settings, accounts = read_nextcloud_md(settings_file)
    exists, children = local_tree(view.project_root)
    result = plan(ACLPolicy.for_tree(view.project_root), accounts, exists, children, base_group=settings.get("group"))
    if as_json:
        rules = [{"path": r.path, "kind": r.kind, "account": r.account, "allowed": _nextcloud_order(r.allowed)} for r in result.rules]
        print(json.dumps({"project": str(view.project_root), "rules": rules, "notes": result.notes}, indent=2, ensure_ascii=False))
        return 0
    print(f"{view.project_root}  ->  Nextcloud rules (all other permissions denied)")
    rows = [[r.path, r.kind, r.account, ", ".join(_nextcloud_order(r.allowed)) or "-"]
            for r in sorted(result.rules, key=lambda r: (r.path, r.kind, r.account))]
    if rows:
        print()
        _table(rows)
    if result.notes:
        print("\nNotes")
        for note in result.notes:
            print(f"  {note}")
    return 0


if __name__ == "__main__":
    main()
