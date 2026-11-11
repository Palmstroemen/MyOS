# reconcile.py - the Team folder in step with its ACLs.md, after each change
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 8, step 2. What `myacl sync`
# does from a desktop (core/nextcloud_sync.py), the core service does after each rebuild of
# the shadow tree, with the service account: a folder born in the browser gets its rights
# from ACLs.md within seconds, an ACLs.md edited in the cloud changes the rules. Who may
# write ACLs.md there is up to Nextcloud already: only who has "change" on it.

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from core.nextcloud_sync import NextcloudSync, SyncRefused


def reconcile(root: Path, dav) -> str:
    """Send what the Team folder (dav) lacks of what its shadow root says; a summary.
    SyncRefused when it is not sent - the rules there stay as they are."""
    sync = NextcloudSync(root, dav)
    # Security: an ACLs.md that leaves no one to change the rights is most likely broken;
    # sending it would take every rule away.
    if not sync.someone_may_change():
        raise SyncRefused("ACLs.md leaves no one who may change the rights: the rules there are kept")
    comparison = sync.compare()
    if comparison.in_step:
        return "in step"
    left = sync.send(comparison)
    summary = (f"sent {len(comparison.changes)} rule change(s), {len(comparison.pending)} embryo change(s), "
               f"{len(comparison.tags)} tag(s)")
    return summary + (f"; {len(left)} still open" if left else "")


class Steward:
    """Keeps the shadow current (keeper: cloud/service/shadow.py) and the Team folder (dav) in
    step with it. A round reconciles after a change - and again after a round that failed, even
    without one (Nextcloud was gone for a moment). A refused ACLs.md stays refused until it
    changes."""

    def __init__(self, keeper, dav, reconcile: Callable[[Path, object], str] = reconcile) -> None:
        self.keeper = keeper
        self.dav = dav
        self._reconcile = reconcile
        self._pending = False

    def round(self) -> Optional[str]:
        """One round: the summary of the reconcile, None when there was nothing to do."""
        changed = self.keeper.refresh()
        if not (changed or self._pending):
            return None
        self._pending = True
        try:
            summary = self._reconcile(self.keeper.root, self.dav)
        except SyncRefused:
            self._pending = False
            raise
        self._pending = False
        return summary
