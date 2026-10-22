# acl_edit.py - change ACLs.md from the GUI: one rule for one role at one path, or the
# groups of one person
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
from core.project import ProjectFinder

# Rights an edit may grant, in the order they are written (ACL design document 2.2).
EDITABLE_RIGHTS = ("read", "write", "execute", "change", "delete")
ACL_FILE_REL = "/.MyOS/ACLs.md"
HISTORY_DIR = "ACLs-history"

_HEADING = re.compile(r"^(#{1,2})\s+(.*?)\s*$")


def _visible(lines: List[str]) -> List[str]:
    """Each line as the reader sees it: without <!-- comments --> (also over several lines),
    so commented-out rules are neither edited nor moved, like in core.acl._acl_rule_text."""
    inside, seen = False, []
    for line in lines:
        rest, kept = line, ""
        while rest:
            if inside:
                end = rest.find("-->")
                if end < 0:
                    rest = ""
                else:
                    inside, rest = False, rest[end + 3:]
            else:
                start = rest.find("<!--")
                if start < 0:
                    kept, rest = kept + rest, ""
                else:
                    inside, kept, rest = True, kept + rest[:start], rest[start + 4:]
        seen.append(kept)
    return seen


class ACLEditError(ValueError):
    """The edit is not possible (unknown role or right, invalid result, self lock-out)."""


class ACLSelfLockoutError(ACLEditError):
    """The editor would lose their own right to change the ACLs."""


class ACLPersonExistsError(ACLEditError):
    """A person of that name is already listed in # Users."""


# Names of people in "# Users": people of the project, not login names, so spaces, accents,
# "-", "." and "'" are fine. Security: nothing that would break or change the line ("Name:
# groups"): no ":", ",", "#", line breaks, comment or list markers; letter or digit first.
_PERSON_NAME = re.compile(r"^[^\W_][\w .'-]{0,59}$")


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
    return _replace_checked(acl_file, original, edited, editor,
                            lambda draft: _check_draft(root, draft, role_key, rule_path, rights, editor))


def set_user_roles(path, user: str, roles: Set[str], editor: str) -> Optional[Path]:
    """
    Set the groups (roles) of user in "# Users" of the ACLs.md governing path.

    Memberships hold in the whole project, not only at path; path selects the ACLs.md
    and the (sub)project whose template folder roles may be given. An empty set removes
    the user's line (no groups, no rights). Only users already listed can be edited.
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

    user_key = str(user or "").strip().lower()
    if user_key not in policy.users:
        raise ACLEditError(f"unknown person {user!r}")
    context = _context_policy(policy, root, target)
    role_keys = {_normalize_role(r) for r in roles}
    unknown = sorted(role_keys - context.roles)
    if unknown:
        raise ACLEditError(f"unknown groups: {', '.join(unknown)}")

    # Groups written for the user but unknown here (e.g. a template folder role of another
    # subproject) are not offered here, so they stay.
    keep = {r for r in policy.users[user_key] if r not in context.roles}
    original = acl_file.read_text(encoding="utf-8")
    edited = _edit_user_line(original, user_key, [context.display_name(r) for r in sorted(role_keys)], keep)
    return _replace_checked(acl_file, original, edited, editor,
                            lambda draft: _check_user_draft(root, draft, user_key, role_keys | keep, editor))


def add_user(path, name: str, roles: Set[str], editor: str) -> Optional[Path]:
    """
    Add a person with their groups (roles) to "# Users" of the ACLs.md governing path, as
    a new line after the people listed. name is free (a person of the project, see
    "Designdocument ACLs.md", 5.3); at least one known group is needed.
    editor: the user making the change; needs "change" on /.MyOS/ACLs.md.
    Returns the kept previous version.
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

    written_name = str(name or "").strip()
    user_key = written_name.lower()
    if not is_person_name(written_name):
        raise ACLEditError(f"not a usable name: {written_name!r}")
    if user_key in policy.users:
        raise ACLPersonExistsError(f"{written_name!r} is already listed")
    context = _context_policy(policy, root, target)
    if _normalize_role(written_name) in policy.roles | context.roles:
        raise ACLEditError(f"{written_name!r} is the name of a group")
    role_keys = {_normalize_role(r) for r in roles}
    if not role_keys:
        raise ACLEditError("a person needs at least one group")
    unknown = sorted(role_keys - context.roles)
    if unknown:
        raise ACLEditError(f"unknown groups: {', '.join(unknown)}")

    original = acl_file.read_text(encoding="utf-8")
    line = f"{written_name}: {', '.join(context.display_name(r) for r in sorted(role_keys))}\n"
    edited = _insert_user_line(original, line)
    return _replace_checked(acl_file, original, edited, editor,
                            lambda draft: _check_user_draft(root, draft, user_key, role_keys, editor))


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
    for line in _visible(lines)[bounds[0] + 1:bounds[1]]:
        if _line_rule_path(line) in wanted:
            written = line.split(":", 1)[1].partition("#")[0]  # without an inline comment
            rights = {r.strip().lower() for r in written.split(",") if r.strip()}
            found = (found or set()) | (rights - {"none"})
    return found


def check_move_rules(old_path, new_path) -> None:
    """
    Raise ACLEditError when rules for new_path (or below) exist already.
    Security: rules waiting for a path (e.g. a prepared "none") would be combined with the
    rules that follow the moved entry, and rights of the same folder add up, so a rename
    or move could undo such a lock. Call before renaming or moving.
    """
    root = find_acl_project_root(Path(new_path).expanduser().parent)
    if root is None:
        return
    new_rel = _plain_rel(root, Path(new_path))
    if new_rel is None:
        return
    lines = (root / ".MyOS" / "ACLs.md").read_text(encoding="utf-8").splitlines(keepends=True)
    if _rule_lines_under(lines, new_rel):
        raise ACLEditError(f"ACLs.md already has rules for {new_rel}")


def move_rules(old_path, new_path, editor: str) -> bool:
    """
    After a rename or move inside the project: rewrite rules for old_path (and below)
    to new_path. Rights stay as they were, only the paths follow; folder rules
    ({Folder}) are no fixed paths and stay. Returns whether ACLs.md changed.
    Not restricted to users with "change": who may rename or move an entry keeps its
    rules intact (check_move_rules prevents that rights add up at the new path).
    """
    old_path, new_path = Path(old_path).expanduser(), Path(new_path).expanduser()
    root = find_acl_project_root(old_path.parent)
    if root is None or find_acl_project_root(new_path.parent) != root:
        return False  # moved out of the project: its rules stay with the old path
    old_rel, new_rel = _plain_rel(root, old_path), _plain_rel(root, new_path)
    if old_rel is None or new_rel is None:
        return False
    acl_file = root / ".MyOS" / "ACLs.md"
    original = acl_file.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    hits = _rule_lines_under(lines, old_rel)
    if not hits:
        return False
    for i in hits:
        indent, rest = lines[i][: len(lines[i]) - len(lines[i].lstrip())], lines[i].lstrip()
        bullet, raw_and_rights = rest[:2], rest[2:]
        raw, sep, rights = raw_and_rights.partition(":")
        written = raw.strip()
        written = written if written.startswith("/") else "/" + written
        lines[i] = f"{indent}{bullet}{new_rel}{written[len(old_rel):]}{sep}{rights}"
    edited = "".join(lines)
    draft = acl_file.with_name(".ACLs.md.draft")
    draft.write_text(edited, encoding="utf-8")
    try:
        try:
            ACLPolicy.from_project(root, acl_file=draft)
        except Exception as exc:
            raise ACLEditError(f"the edited ACLs.md is not valid: {exc}") from exc
        _keep_previous(acl_file, original, editor)
        os.replace(draft, acl_file)
    finally:
        if draft.exists():
            draft.unlink()
    return True


def _plain_rel(root: Path, path: Path) -> Optional[str]:
    """"/a/b" for root/a/b (no trailing slash, not resolved: the path may be gone)."""
    try:
        rel = path.absolute().relative_to(root)
    except ValueError:
        return None
    text = "/".join(rel.parts)
    return "/" + text if text else None


def _rule_lines_under(lines: List[str], rel: str) -> List[int]:
    """Indices of rule lines whose path is rel or below it ({Folder} rules excluded)."""
    hits = []
    for i, line in enumerate(_visible(lines)):
        stripped = line.strip()
        if not (stripped.startswith("- ") or stripped.startswith("* ")) or ":" not in stripped:
            continue
        written = stripped[2:].partition(":")[0].strip()
        if "{" in written:
            continue
        written = written if written.startswith("/") else "/" + written
        if written.rstrip("/") == rel or written.startswith(rel + "/"):
            hits.append(i)
    return hits


def is_person_name(name: str) -> bool:
    """Whether name can stand as a person in "# Users" (see _PERSON_NAME)."""
    return bool(_PERSON_NAME.match(str(name or "").strip()))


def may_change_acls(policy: ACLPolicy, user: str) -> bool:
    """Whether user has "change" on the project's ACLs.md (may change the rights)."""
    return "change" in _user_rights(policy, user, ACL_FILE_REL)


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
    for i, line in enumerate(_visible(lines)):
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
        # A template folder role inherits the "## Folder" rules; its new section holds
        # only explicit entries (the inherited ones keep applying, see ACLPolicy).
        lines = _insert_section(lines, policy, role_key)
        bounds = _section_bounds(lines, role_key)

    start, end = bounds
    target = _normalize_path(rule_path)
    same_folder = {target, _normalize_path(rule_path.rstrip("/") + "/**")}
    seen = _visible(lines)
    matches = [i for i in range(start + 1, end) if _line_rule_path(seen[i]) in same_folder]
    if matches:
        first = matches[0]
        for i in reversed(matches[1:]):
            del lines[i]
        if rights is None:
            del lines[first]
        else:
            lines[first] = _rule_line(rule_path, rights)
    elif rights is not None:
        rule_lines = [i for i in range(start + 1, end) if _line_rule_path(seen[i]) is not None]
        insert_at = (rule_lines[-1] + 1) if rule_lines else start + 1
        lines.insert(insert_at, _rule_line(rule_path, rights))
    return "".join(lines)


def _insert_section(lines: List[str], policy: ACLPolicy, role_key: str) -> List[str]:
    # Roles without a section of their own are template folder roles (see from_project).
    if role_key in policy.own_sections:
        raise ACLEditError(f"section of role {role_key!r} not found")
    section = [f"## {policy.display_name(role_key)}\n", "\n"]
    # Before "# Users" (the end of the permissions), else at the end of the file.
    for i, line in enumerate(_visible(lines)):
        match = _HEADING.match(line.rstrip("\n"))
        if match and len(match.group(1)) == 1 and match.group(2).strip().lower() == "users":
            return lines[:i] + section + lines[i:]
    if lines and lines[-1].strip():
        lines.append("\n")
    return lines + section


def _context_policy(policy: ACLPolicy, root: Path, target: Path) -> ACLPolicy:
    """policy as seen from the (sub)project target lies in (its template folder roles)."""
    try:
        context = ProjectFinder.find_nearest(target)
    except OSError:
        context = None
    return policy.for_context(root, context.resolve() if context is not None else root)


def _user_line_key(line: str) -> Optional[str]:
    """Lower-case person of a "# Users" line ("Anna: Admin, Team"), None for other lines."""
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "- ", "* ")):
        return None
    name, sep, _ = stripped.partition(":")
    return name.strip().lower() if sep and name.strip() else None


def _edit_user_line(text: str, user_key: str, role_names: List[str], keep: Set[str]) -> str:
    """text with the user's line in "# Users" listing role_names and the written groups
    in keep (none at all: line removed). Groups already written keep their place and
    spelling, new ones follow."""
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    seen = _visible(lines)
    start = end = None
    for i, line in enumerate(seen):
        match = _HEADING.match(line.rstrip("\n"))
        if not match:
            continue
        if start is not None:
            end = i
            break
        if len(match.group(1)) == 1 and match.group(2).strip().lower() == "users":
            start = i
    if start is None:
        raise ACLEditError("ACLs.md has no # Users section")
    hits = [i for i in range(start + 1, end or len(lines)) if _user_line_key(seen[i]) == user_key]
    if not hits:
        raise ACLEditError(f"person {user_key!r} not found in # Users")

    written_name, _, rest = seen[hits[0]].strip().partition(":")
    written = [n.strip() for n in rest.partition("#")[0].split(",") if n.strip()]
    wanted = {_normalize_role(n): n for n in role_names}
    names = [n for n in written if _normalize_role(n) in keep or wanted.pop(_normalize_role(n), None)]
    names += list(wanted.values())
    if names == written and len(hits) == 1:
        return text  # nothing changes (a comment at the end of the line stays)

    for i in reversed(hits[1:]):
        del lines[i]
    if names:
        indent = lines[hits[0]][: len(lines[hits[0]]) - len(lines[hits[0]].lstrip())]
        lines[hits[0]] = f"{indent}{written_name.strip()}: {', '.join(names)}\n"
    else:
        del lines[hits[0]]
    return "".join(lines)


def _insert_user_line(text: str, line: str) -> str:
    """text with line after the last person in "# Users" (or right after the heading)."""
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    seen = _visible(lines)
    start = end = None
    for i, visible in enumerate(seen):
        match = _HEADING.match(visible.rstrip("\n"))
        if not match:
            continue
        if start is not None:
            end = i
            break
        if len(match.group(1)) == 1 and match.group(2).strip().lower() == "users":
            start = i
    if start is None:
        raise ACLEditError("ACLs.md has no # Users section")
    people = [i for i in range(start + 1, end or len(lines)) if _user_line_key(seen[i]) is not None]
    at = (people[-1] + 1) if people else start + 1
    return "".join(lines[:at] + [line] + lines[at:])


def _replace_checked(acl_file: Path, original: str, edited: str, editor: str, check) -> Optional[Path]:
    """Write edited over ACLs.md after check(draft) passed, keeping the previous version."""
    if edited == original:
        return None
    draft = acl_file.with_name(".ACLs.md.draft")
    draft.write_text(edited, encoding="utf-8")
    try:
        check(draft)
        kept = _keep_previous(acl_file, original, editor)
        os.replace(draft, acl_file)  # atomic: never a half-written ACLs.md
    finally:
        if draft.exists():
            draft.unlink()
    return kept


def _check_user_draft(root: Path, draft: Path, user_key: str, role_keys: Set[str], editor: str) -> None:
    try:
        policy = ACLPolicy.from_project(root, acl_file=draft)
    except Exception as exc:
        raise ACLEditError(f"the edited ACLs.md is not valid: {exc}") from exc
    got = policy.roles_for_user(user_key)
    if got != role_keys:
        raise ACLEditError(f"edit did not take effect ({sorted(got)} instead of {sorted(role_keys)})")
    # Security: nobody locks themselves out of ACL management by accident.
    if "change" not in _user_rights(policy, editor, ACL_FILE_REL):
        raise ACLSelfLockoutError(f"{editor!r} would lose the right to change the ACLs")


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
        raise ACLSelfLockoutError(f"{editor!r} would lose the right to change the ACLs")


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
