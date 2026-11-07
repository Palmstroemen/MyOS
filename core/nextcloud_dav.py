# nextcloud_dav.py - a Nextcloud Team folder over WebDAV: its tree and its "advanced
# permissions" rules (read only; for myacl sync --dry-run)
#
# The Team folders app (groupfolders) hands its rules out as the property nc:acl-list of
# every entry; reading them needs "manage advanced permissions" for the folder, not a
# Nextcloud admin. Security: the account sees only what it may read, so it should be one
# that may read the whole folder (e.g. a person of the role Admin).

from __future__ import annotations

import base64
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple
from urllib.parse import quote, unquote

_DAV = "{DAV:}"
_NC = "{http://nextcloud.org/ns}"
_PROPFIND = (
    '<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:nc="http://nextcloud.org/ns"><d:prop>'
    "<d:resourcetype/><nc:acl-enabled/><nc:acl-can-manage/><nc:acl-list/></d:prop></d:propfind>"
).encode()

# (method, url, body, headers, (user, password)) -> (HTTP status, body)
Transport = Callable[[str, str, bytes, Dict[str, str], Tuple[str, str]], Tuple[int, bytes]]


class NextcloudError(Exception):
    pass


@dataclass(frozen=True)
class ExistingRule:
    kind: str  # "user" | "group" | "circle"
    account: str
    mask: int  # bits the rule fixes (read 1, update 2, create 4, delete 8, share 16)
    permissions: int  # of those, the allowed ones


@dataclass
class Entry:
    path: str  # relative to the Team folder, "/" for its root
    is_dir: bool
    rules: List[ExistingRule] = field(default_factory=list)
    acl_enabled: bool = False
    can_manage: bool = False


def _urllib_transport(method, url, body, headers, auth):
    token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
    request = urllib.request.Request(url, data=body, method=method, headers={**headers, "Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except urllib.error.URLError as error:
        raise NextcloudError(f"Nextcloud is not reachable at {url}: {error.reason}") from error


class NextcloudDAV:
    def __init__(self, url: str, user: str, password: str, folder: str, transport: Transport = None) -> None:
        self.url = url.rstrip("/")
        self.user = user
        self.folder = folder.strip("/")
        self._auth = (user, password)
        self._transport = transport or _urllib_transport
        self._base = "/remote.php/dav/files/" + quote(user) + "".join("/" + quote(p) for p in self.folder.split("/") if p)

    def tree(self) -> Dict[str, Entry]:
        """Every entry of the Team folder that the account may see, with its rules."""
        root = self._list("/")
        top = root.get("/")
        if top is None:
            raise NextcloudError(f"{self.folder} not found in the files of {self.user}")
        if not top.acl_enabled:
            raise NextcloudError(f"{self.folder} is not a Team folder with advanced permissions switched on")
        if not top.can_manage:
            raise NextcloudError(f"{self.user} may not manage the advanced permissions of {self.folder}")
        tree = dict(root)
        pending = [path for path, entry in root.items() if entry.is_dir and path != "/"]
        while pending:
            path = pending.pop()
            for child, entry in self._list(path).items():
                if child not in tree:
                    tree[child] = entry
                    if entry.is_dir:
                        pending.append(child)
        return tree

    def _list(self, path: str) -> Dict[str, Entry]:
        dav_path = self._base + "".join("/" + quote(p) for p in path.split("/") if p) + "/"
        headers = {"Depth": "1", "Content-Type": "application/xml; charset=utf-8"}
        status, body = self._transport("PROPFIND", self.url + dav_path, _PROPFIND, headers, self._auth)
        if status == 401:
            raise NextcloudError(f"Nextcloud refused the login of {self.user} (app password?)")
        if status == 404:
            return {}
        if status != 207:
            raise NextcloudError(f"Nextcloud answered {status} for {path}")
        return {entry.path: entry for entry in self._parse(body)}

    def _parse(self, body: bytes) -> List[Entry]:
        base = unquote(self._base)
        entries = []
        for response in ET.fromstring(body).iter(_DAV + "response"):
            href = unquote(response.findtext(_DAV + "href") or "").rstrip("/")
            if href != base and not href.startswith(base + "/"):
                continue
            prop = response.find(f"{_DAV}propstat/{_DAV}prop")
            if prop is None:
                continue
            rules = [
                ExistingRule(
                    acl.findtext(_NC + "acl-mapping-type") or "",
                    acl.findtext(_NC + "acl-mapping-id") or "",
                    int(acl.findtext(_NC + "acl-mask") or 0),
                    int(acl.findtext(_NC + "acl-permissions") or 0),
                )
                for acl in prop.iter(_NC + "acl")
            ]
            entries.append(Entry(
                path=href[len(base):] or "/",
                is_dir=prop.find(f"{_DAV}resourcetype/{_DAV}collection") is not None,
                rules=rules,
                acl_enabled=(prop.findtext(_NC + "acl-enabled") or "").strip() == "1",
                can_manage=(prop.findtext(_NC + "acl-can-manage") or "").strip() == "1",
            ))
        return entries


def tree_functions(tree: Dict[str, Entry]):
    """exists(path) and children(path) of a fetched tree, for core.acl_nextcloud.plan."""
    kids: Dict[str, List[str]] = {}
    for path in tree:
        if path != "/":
            parent, _, name = path.rpartition("/")
            kids.setdefault(parent or "/", []).append(name)

    def exists(path: str) -> bool:
        return path in tree

    def children(path: str) -> List[str]:
        return sorted(kids.get(path, []))

    return exists, children
