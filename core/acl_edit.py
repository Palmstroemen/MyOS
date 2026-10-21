# acl_edit.py - change ACLs.md from the GUI: one rule for one role at one path
#
# See "Designdocument ACLs.md", 5.3. Because the nearest rule wins (per role), an edit is
# always the rule of one role at exactly one path. Only the affected lines change; the
# draft is checked as a whole policy before it replaces ACLs.md, and the previous version
# is kept in .MyOS/ACLs-history/ (undo, "who changed what, when").

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from core.acl import ACLPolicy, _normalize_path, _normalize_role, find_acl_project_root

# Rights an edit may grant, in the order they are written (ACL design document 2.2).
EDITABLE_RIGHTS = ("read", "write", "execute", "change", "delete")
ACL_FILE_REL = "/.MyOS/ACLs.md"
HISTORY_DIR = "ACLs-history"

_HEADING = re.compile(r"^(#{1,2})\s+(.*?)\s*$")


class ACLEditError(ValueError):
    """The edit is not possible (unknown role or right, invalid result, self lock-out)."""


def set_role_rights(path, role: str, rights: Optional[Set[str]], editor: str) -> Optional[Path]:
    """
    Set the rights of role at path (absolute) in the governing ACLs.md.

    rights: the complete set at this path; an empty set writes "none" (locked out here),
    None removes the role's rule at this path (back to inherited).
    editor: the user making the change; needs "change" on /.MyOS/ACLs.md.
    Returns the kept previous version (None when nothing had to change).
    """
    target = Path(path).expanduser().resolve()
    root = find_acl_project_root(target)
    if root is None:
        raise ACLEditError(f"no ACLs.md governs {target}")
    acl_file = root / ".MyOS" / "ACLs.md"
    policy = ACLPolicy.from_project(root)

    # Security: only users who may change ACLs.md may edit it, whatever the GUI shows.
    if "change" not in _user_rights(policy, editor, ACL_FILE_REL):
        raise PermissionError(f"{editor!r} may not change the ACLs of {root}")

    role_key = _normalize_role(role)
    if role_key not in policy.roles:
        raise ACLEditError(f"unknown role {role!r}")
    if rights is not None:
        unknown = sorted(set(rights) - set(EDITABLE_RIGHTS))
        if unknown:
            raise ACLEditError(f"unknown rights: {', '.join(unknown)}")

    rule_path = _rule_path_for(root, target)
    original = acl_file.read_text(encoding="utf-8")
    edited = _edit_text(original, policy, root, role_key, rule_path, rights)
    if edited == original:
        return None

    draft = acl_file.with_name(".ACLs.md.draft")
    draft.write_text(edited, encoding="utf-8")
    try:
        _check_draft(root, draft, role_key, rule_path, rights, editor)
        kept = _keep_previous(acl_file, original, editor)
        os.replace(draft, acl_file)  # atomic: never a half-written ACLs.md
    finally:
        if draft.exists():
            draft.unlink()
    return kept


def can_edit(path, editor: str) -> bool:
    """Whether editor may change the ACLs governing path (GUI: chips editable or not)."""
    root = find_acl_project_root(Path(path).expanduser())
    if root is None:
        return False
    try:
        policy = ACLPolicy.from_project(root)
    except Exception:
        return False
    return "change" in _user_rights(policy, editor, ACL_FILE_REL)


def own_rule(path, role: str) -> Optional[Set[str]]:
    """
    Rights of role's own rule at exactly path as written ({"none"} becomes an empty set),
    or None when the role only inherits here (then "back to inherited" has nothing to do).
    """
    target = Path(path).expanduser().resolve()
    root = find_acl_project_root(target)
    if root is None:
        return None
    acl_file = root / ".MyOS" / "ACLs.md"
    try:
        lines = acl_file.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError:
        return None
    bounds = _section_bounds(lines, _normalize_role(role))
    if bounds is None:
        return None
    rule_path = _rule_path_for(root, target)
    wanted = {_normalize_path(rule_path), _normalize_path(rule_path.rstrip("/") + "/**")}
    found: Optional[Set[str]] = None
    for line in lines[bounds[0] + 1:bounds[1]]:
        if _line_rule_path(line) in wanted:
            rights = {r.strip().lower() for r in line.split(":", 1)[1].split(",") if r.strip()}
            found = (found or set()) | (rights - {"none"})
    return found


def _user_rights(policy: ACLPolicy, user: str, rel: str) -> Set[str]:
    rights: Set[str] = set()
    for role in policy.roles_for_user(str(user or "")):
        rights |= policy.rights_for(role, rel)
    return set(EDITABLE_RIGHTS) if "*" in rights else rights - {"none"}


def _rule_path_for(root: Path, target: Path) -> str:
    """Path as written in ACLs.md: project-relative, folders with a trailing slash."""
    try:
        rel = target.relative_to(root)
    except ValueError:
        raise ACLEditError(f"{target} is outside {root}")
    text = str(rel).replace("\\", "/")
    if text in ("", "."):
        return "/*"  # the project root itself: its rule covers everything below
    return "/" + text + ("/" if target.is_dir() else "")


def _rights_text(rights: Set[str]) -> str:
    if "*" in rights:
        return "*"
    ordered = [r for r in EDITABLE_RIGHTS if r in rights]
    return ", ".join(ordered) if ordered else "none"


def _rule_line(rule_path: str, rights: Set[str]) -> str:
    return f"- {rule_path}: {_rights_text(rights)}\n"


def _line_rule_path(line: str) -> Optional[str]:
    """Normalized path of a rule line ("- /x/: read"), None for other lines."""
    stripped = line.strip()
    if not (stripped.startswith("- ") or stripped.startswith("* ")):
        return None
    raw, sep, _ = stripped[2:].partition(":")
    return _normalize_path(raw) if sep else None


def _section_bounds(lines: List[str], role_key: str):
    """(header index, end index) of the role's "## Role" section, or None."""
    start = None
    for i, line in enumerate(lines):
        match = _HEADING.match(line.rstrip("\n"))
        if not match:
            continue
        if start is not None:
            return start, i
        if len(match.group(1)) == 2 and _normalize_role(match.group(2)) == role_key:
            start = i
    return (start, len(lines)) if start is not None else None


def _edit_text(text: str, policy: ACLPolicy, root: Path, role_key: str,
               rule_path: str, rights: Optional[Set[str]]) -> str:
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    bounds = _section_bounds(lines, role_key)
    if bounds is None:
        if rights is None:
            return text  # nothing written for this role here: already inherited
        # A template folder role lives on the "## Folder" rules; a section of its own
        # replaces them, so the new section starts with the role's current folder rules.
        lines = _insert_section(lines, policy, root, role_key)
        bounds = _section_bounds(lines, role_key)

    start, end = bounds
    target = _normalize_path(rule_path)
    same_folder = {target, _normalize_path(rule_path.rstrip("/") + "/**")}
    matches = [i for i in range(start + 1, end) if _line_rule_path(lines[i]) in same_folder]
    if matches:
        first = matches[0]
        for i in reversed(matches[1:]):
            del lines[i]
        if rights is None:
            del lines[first]
        else:
            lines[first] = _rule_line(rule_path, rights)
    elif rights is not None:
        rule_lines = [i for i in range(start + 1, end) if _line_rule_path(lines[i]) is not None]
        insert_at = (rule_lines[-1] + 1) if rule_lines else start + 1
        lines.insert(insert_at, _rule_line(rule_path, rights))
    return "".join(lines)


def _insert_section(lines: List[str], policy: ACLPolicy, root: Path, role_key: str) -> List[str]:
    # Roles without a section of their own are template folder roles (see from_project).
    if role_key in policy.own_sections:
        raise ACLEditError(f"section of role {role_key!r} not found")
    header = f"## {policy.display_name(role_key)}\n"
    body = []
    for rule in policy.permissions.get(role_key, []):
        written = rule.path
        if written != "/*" and not any(ch in written for ch in "*?[") and (root / written.lstrip("/")).is_dir():
            written += "/"
        body.append(_rule_line(written, set(rule.rights)))
    section = [header] + body + ["\n"]
    # Before "# Users" (the end of the permissions), else at the end of the file.
    for i, line in enumerate(lines):
        match = _HEADING.match(line.rstrip("\n"))
        if match and len(match.group(1)) == 1 and match.group(2).strip().lower() == "users":
            return lines[:i] + section + lines[i:]
    if lines and lines[-1].strip():
        lines.append("\n")
    return lines + section


def _check_draft(root: Path, draft: Path, role_key: str, rule_path: str,
                 rights: Optional[Set[str]], editor: str) -> None:
    try:
        policy = ACLPolicy.from_project(root, acl_file=draft)
    except Exception as exc:
        raise ACLEditError(f"the edited ACLs.md is not valid: {exc}") from exc
    if rights is not None:
        wanted = set(rights) if rights else {"none"}
        got = policy.rights_for(role_key, _normalize_path(rule_path))
        if got != wanted and not ("*" in got and set(rights) >= set(EDITABLE_RIGHTS)):
            raise ACLEditError(f"edit did not take effect ({sorted(got)} instead of {sorted(wanted)})")
    # Security: nobody locks themselves out of ACL management by accident.
    if "change" not in _user_rights(policy, editor, ACL_FILE_REL):
        raise ACLEditError(f"{editor!r} would lose the right to change the ACLs")


def _keep_previous(acl_file: Path, text: str, editor: str) -> Path:
    history = acl_file.parent / HISTORY_DIR
    history.mkdir(exist_ok=True)
    who = re.sub(r"[^A-Za-z0-9_-]", "_", str(editor or "unknown")) or "unknown"
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    kept = history / f"ACLs-{stamp}-{who}.md"
    n = 1
    while kept.exists():
        n += 1
        kept = history / f"ACLs-{stamp}-{n}-{who}.md"
    kept.write_text(text, encoding="utf-8")
    return kept
