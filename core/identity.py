# identity.py - who the user is in a project
#
# See "Designdocument ACLs.md", 5.3. People in "# Users" are people of the project, not
# login names: projects travel (cloud, USB stick) to computers where not every person has
# an account. So each computer keeps the user's names locally, in
# ~/.config/MyOS/Identity.md ("Names: Oliver, Oliver Rafelsberger"); in a project the user
# is the first of them that the project lists, else (as before) the login name.
# MYOS_ACL_USER overrides everything (development and tests).
#
# Security: this is a claim, not authentication. Claiming a person from the GUI
# (claim_person) is only possible for people who may not change the rights; an admin's
# name has to be written into Identity.md by hand.

from __future__ import annotations

import getpass
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

from core.acl import ACLPolicy, find_acl_project_root
from core.acl_edit import ACLEditError, is_person_name, may_change_acls

# ACLs.md -> ((mtime_ns, size), lower-case people listed): resolved for every ACL check.
_listed_cache: Dict[Path, Tuple[Tuple[int, int], Set[str]]] = {}


def identity_file() -> Path:
    config_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config_home) / "MyOS" / "Identity.md"


def login_name() -> str:
    try:
        name = getpass.getuser()
    except Exception:  # no login name in the environment and no passwd entry
        name = ""
    return str(name or "local").strip().lower()


def own_names() -> List[str]:
    """The user's names on this computer ("Names:" in "# Identity"), in their order."""
    try:
        text = identity_file().read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    in_identity = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            in_identity = stripped.lstrip("#").strip().lower() == "identity"
            continue
        key, sep, value = stripped.partition(":")
        if in_identity and sep and key.strip().lower() == "names":
            value = re.split(r"\s#", value, maxsplit=1)[0]
            return [name.strip() for name in value.split(",") if name.strip()]
    return []


def person_in(users: Iterable[str]) -> str:
    """The user's (lower-case) key in a project listing users (lower-case keys)."""
    override = str(os.environ.get("MYOS_ACL_USER") or "").strip().lower()
    if override:
        return override
    listed = set(users)
    for name in own_names():
        if name.strip().lower() in listed:
            return name.strip().lower()
    return login_name()


def acl_user_for(path: Union[str, Path]) -> str:
    """The user ACLs are checked for at path (in the project whose ACLs.md governs it)."""
    root = find_acl_project_root(Path(path).expanduser())
    return person_in(_listed_people(root) if root is not None else ())


def is_listed(path: Union[str, Path]) -> bool:
    """Whether the user is one of the people of the project governing path."""
    root = find_acl_project_root(Path(path).expanduser())
    return root is not None and acl_user_for(path) in _listed_people(root)


def claimable_people(path: Union[str, Path]) -> List[str]:
    """People of the project governing path the user may say they are, sorted by name:
    all listed people except those who may change the rights."""
    policy = _policy(path)
    if policy is None:
        return []
    names = [policy.display_name(user) for user in policy.users if not may_change_acls(policy, user)]
    return sorted(names, key=str.lower)


def claim_person(path: Union[str, Path], name: str) -> None:
    """Remember on this computer that the user is name (a person of path's project)."""
    wanted = str(name or "").strip().lower()
    match = next((n for n in claimable_people(path) if n.lower() == wanted), None)
    if match is None:
        raise ACLEditError(f"{name!r} cannot be chosen here")
    add_own_name(match)


def add_own_name(name: str) -> None:
    """Add name to the user's names (after the others), keeping every other line."""
    name = str(name or "").strip()
    if not is_person_name(name):
        raise ACLEditError(f"not a usable name: {name!r}")
    path = identity_file()
    # Security: never write through a symlink (the file decides who the user is).
    if path.is_symlink():
        raise OSError(f"refusing to write symlinked {path}")
    names = own_names()
    if name.lower() in {n.lower() for n in names}:
        return
    line = "Names: " + ", ".join([*names, name])
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    heading = next((i for i, l in enumerate(lines)
                    if l.strip().startswith("#") and l.strip().lstrip("#").strip().lower() == "identity"), None)
    if heading is None:
        lines = (lines + [""] if lines and lines[-1].strip() else lines) + ["# Identity", line]
    else:
        end = next((i for i in range(heading + 1, len(lines)) if lines[i].strip().startswith("#")), len(lines))
        hit = next((i for i in range(heading + 1, end) if lines[i].partition(":")[0].strip().lower() == "names"), None)
        if hit is None:
            lines.insert(heading + 1, line)
        else:
            lines[hit] = line
    path.parent.mkdir(parents=True, exist_ok=True)
    draft = path.with_name("." + path.name + ".draft")
    draft.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(draft, path)


def _policy(path: Union[str, Path]) -> Optional[ACLPolicy]:
    root = find_acl_project_root(Path(path).expanduser())
    if root is None:
        return None
    try:
        return ACLPolicy.from_project(root)
    except Exception:
        return None


def _listed_people(root: Path) -> Set[str]:
    acl_file = Path(root).resolve() / ".MyOS" / "ACLs.md"
    try:
        stat = acl_file.stat()
    except OSError:
        return set()
    stamp = (stat.st_mtime_ns, stat.st_size)
    cached = _listed_cache.get(acl_file)
    if cached is not None and cached[0] == stamp:
        return cached[1]
    try:
        people = set(ACLPolicy.from_project(acl_file.parent.parent).users)
    except Exception:
        people = set()
    _listed_cache[acl_file] = (stamp, people)
    return people
