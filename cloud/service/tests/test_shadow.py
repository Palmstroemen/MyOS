"""The shadow tree ("Designdocument MyOS Core Service.md", 5): every folder of the Team folder
(empty) and every file of a .MyOS, built from a WebDAV walk; no user documents. Rebuilt when
the Team folder's ETag changes; a rebuild that fails keeps the shadow there was."""

import pytest

from cloud.service.shadow import ShadowKeeper, build_shadow
from core.nextcloud_dav import Entry, NextcloudError

FILES = {
    "/.MyOS/Project.md": b"# MyOS Project\n",
    "/.MyOS/ACLs.md": b"# Permissions\n",
    "/.MyOS/Templates/Standard/04_Finanz/.MyOS/Desk.md": b"theme: light\n",
    "/Familie/.MyOS/Project.md": b"# MyOS Project\n",
    "/Familie/Rechnung.pdf": b"%PDF",
}
FOLDERS = ["/", "/.MyOS", "/.MyOS/Templates", "/.MyOS/Templates/Standard", "/.MyOS/Templates/Standard/04_Finanz",
           "/.MyOS/Templates/Standard/04_Finanz/.MyOS", "/Familie", "/Familie/.MyOS", "/Familie/Fotos"]


class FakeDAV:
    def __init__(self, files=FILES, folders=FOLDERS):
        self.files, self.folders, self.tag, self.fail, self.got = dict(files), list(folders), '"1"', False, []

    def tree(self):
        if self.fail:
            raise NextcloudError("Nextcloud is not reachable")
        tree = {path: Entry(path, True) for path in self.folders}
        tree.update({path: Entry(path, False) for path in self.files})
        return tree

    def get(self, path):
        self.got.append(path)
        return self.files.get(path)

    def etag(self):
        return self.tag


def test_folders_and_myos_files_come_documents_do_not(tmp_path):
    dav = FakeDAV()
    build_shadow(dav, tmp_path / "s")

    assert (tmp_path / "s" / "Familie" / "Fotos").is_dir()
    assert (tmp_path / "s" / ".MyOS" / "ACLs.md").read_bytes() == b"# Permissions\n"
    assert (tmp_path / "s" / ".MyOS" / "Templates" / "Standard" / "04_Finanz" / ".MyOS" / "Desk.md").is_file()
    assert not (tmp_path / "s" / "Familie" / "Rechnung.pdf").exists()
    assert "/Familie/Rechnung.pdf" not in dav.got


@pytest.mark.parametrize("bad", ["/../.MyOS/x.md", "/a/./.MyOS/x.md", "/a\\..\\.MyOS/x.md"])
def test_a_path_that_could_leave_the_shadow_is_refused(tmp_path, bad):
    dav = FakeDAV(files={bad: b"x", **FILES})

    with pytest.raises(NextcloudError):
        build_shadow(dav, tmp_path / "s")


def test_the_keeper_rebuilds_only_when_the_etag_changed(tmp_path):
    dav = FakeDAV()
    keeper = ShadowKeeper(tmp_path / "base", dav)

    assert keeper.refresh() and (keeper.root / "Familie").is_dir()
    first = keeper.root
    assert not keeper.refresh() and keeper.root == first

    dav.folders.append("/Job")
    dav.tag = '"2"'
    assert keeper.refresh() and (keeper.root / "Job").is_dir() and keeper.root != first


def test_old_shadows_go_but_the_one_before_stays_for_requests_under_way(tmp_path):
    dav = FakeDAV()
    keeper = ShadowKeeper(tmp_path / "base", dav)
    roots = []
    for tag in ('"1"', '"2"', '"3"'):
        dav.tag = tag
        keeper.refresh()
        roots.append(keeper.root)

    assert [root.exists() for root in roots] == [False, True, True]


def test_a_failed_rebuild_keeps_the_shadow_there_was(tmp_path):
    dav = FakeDAV()
    keeper = ShadowKeeper(tmp_path / "base", dav)
    keeper.refresh()
    first = keeper.root
    dav.tag, dav.fail = '"2"', True

    with pytest.raises(NextcloudError):
        keeper.refresh()
    assert keeper.root == first and (first / "Familie").is_dir()
    dav.fail = False
    assert keeper.refresh()  # tried again: the ETag it failed on is not taken as done
