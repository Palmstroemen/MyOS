"""The core service keeps the Team folder in step with its ACLs.md (core/nextcloud_sync.py
does the work and is tested there); here what it refuses to send."""

import pytest

from cloud.service.reconcile import Steward, reconcile
from core.nextcloud_sync import SyncRefused
from core.brand import META_DIR


class Untouchable:
    """A Team folder that must not be asked anything."""

    def __getattr__(self, name):
        raise AssertionError(f"the Team folder was asked: {name}")


def test_an_acls_md_that_leaves_no_one_to_change_the_rights_is_not_sent(shadow):
    (shadow / META_DIR / "Nextcloud.md").write_text("# Nextcloud\ngroup: Projekte\n\n# Accounts\nLisa: lisa\n")
    (shadow / META_DIR / "ACLs.md").write_text("kaputt\n")

    with pytest.raises(SyncRefused, match="kept"):
        reconcile(shadow, Untouchable())


def test_without_nextcloud_md_nothing_is_sent(shadow):
    with pytest.raises(SyncRefused):
        reconcile(shadow, Untouchable())


class FakeKeeper:
    def __init__(self, changes):
        self.changes, self.root = list(changes), "/shadow"

    def refresh(self):
        return self.changes.pop(0)


def test_a_round_brings_the_rules_in_step_only_after_a_change():
    done = []
    steward = Steward(FakeKeeper([True, False]), "dav", reconcile=lambda root, dav: done.append(root) or "in step")

    steward.round()
    steward.round()

    assert done == ["/shadow"]


def test_a_round_that_failed_is_tried_again_without_a_change():
    calls = []

    def flaky(root, dav):
        calls.append(root)
        if len(calls) == 1:
            raise OSError("Nextcloud is not reachable")
        return "sent"

    steward = Steward(FakeKeeper([True, False, False]), "dav", reconcile=flaky)
    with pytest.raises(OSError):
        steward.round()
    steward.round()  # no change, but the last round failed
    steward.round()

    assert len(calls) == 2


def test_a_refused_acls_md_is_not_tried_again_until_it_changes():
    calls = []

    def refused(root, dav):
        calls.append(root)
        raise SyncRefused("ACLs.md leaves no one who may change the rights")

    steward = Steward(FakeKeeper([True, False]), "dav", reconcile=refused)
    with pytest.raises(SyncRefused):
        steward.round()
    steward.round()

    assert len(calls) == 1
