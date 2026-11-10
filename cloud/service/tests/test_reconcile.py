"""The core service keeps the Team folder in step with its ACLs.md (core/nextcloud_sync.py
does the work and is tested there); here what it refuses to send."""

import pytest

from cloud.service.reconcile import reconcile
from core.nextcloud_sync import SyncRefused


class Untouchable:
    """A Team folder that must not be asked anything."""

    def __getattr__(self, name):
        raise AssertionError(f"the Team folder was asked: {name}")


def test_an_acls_md_that_leaves_no_one_to_change_the_rights_is_not_sent(shadow):
    (shadow / ".MyOS" / "Nextcloud.md").write_text("# Nextcloud\ngroup: Projekte\n\n# Accounts\nLisa: lisa\n")
    (shadow / ".MyOS" / "ACLs.md").write_text("kaputt\n")

    with pytest.raises(SyncRefused, match="kept"):
        reconcile(shadow, Untouchable())


def test_without_nextcloud_md_nothing_is_sent(shadow):
    with pytest.raises(SyncRefused):
        reconcile(shadow, Untouchable())
