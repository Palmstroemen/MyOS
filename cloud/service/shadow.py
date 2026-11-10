# shadow.py - the shadow tree of a Team folder, what the core reads in the cloud
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 5: every folder (empty) and every
# file of a .MyOS (with .MyOS/Templates), no user documents. Built from a WebDAV walk with the
# service account; a cache, never a source - on doubt it is rebuilt. Here it is rebuilt when
# the Team folder's ETag changes (Nextcloud changes it for anything below); file events from
# myos_acl come later.

from __future__ import annotations

import itertools
import shutil
from pathlib import Path
from typing import List, Optional

from core.nextcloud_dav import NextcloudError

MYOS = ".MyOS"


def build_shadow(dav, target: Path) -> None:
    """Build the shadow of dav's Team folder at target (which must not exist yet)."""
    target = Path(target)
    tree = dav.tree()
    target.mkdir(parents=True)
    for path in sorted(tree):
        parts = _parts(path)
        entry = tree[path]
        if entry.is_dir:
            target.joinpath(*parts).mkdir(parents=True, exist_ok=True)
        elif MYOS in parts[:-1]:
            data = dav.get(path)
            if data is not None:  # gone since the walk: the next ETag change brings it right
                file = target.joinpath(*parts)
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(data)


class ShadowKeeper:
    """Keeps the shadow of dav's Team folder current below base; root is the one to read."""

    def __init__(self, base: Path, dav) -> None:
        self.base = Path(base)
        self.root: Optional[Path] = None
        self._dav = dav
        self._etag: Optional[str] = None
        self._count = itertools.count(1)
        self._built: List[Path] = []

    def refresh(self) -> bool:
        """Rebuild when the Team folder changed; whether it did. NextcloudError when the
        rebuild fails - root then stays the shadow there was."""
        etag = self._dav.etag()
        if self.root is not None and etag == self._etag:
            return False
        self.base.mkdir(parents=True, exist_ok=True)
        target = self.base / f"shadow-{next(self._count)}"
        shutil.rmtree(target, ignore_errors=True)  # left from an earlier run of the service
        try:
            build_shadow(self._dav, target)
        except Exception:
            shutil.rmtree(target, ignore_errors=True)
            raise
        self.root, self._etag = target, etag
        self._built.append(target)
        # The one before stays: a request may still be reading it.
        while len(self._built) > 2:
            shutil.rmtree(self._built.pop(0), ignore_errors=True)
        return True


def _parts(path: str) -> List[str]:
    parts = [p for p in path.split("/") if p]
    # Security: a path from the server never leads out of the shadow.
    if any(p in (".", "..") or "\\" in p for p in parts):
        raise NextcloudError(f"refused a path from the server: {path!r}")
    return parts
