"""The shadow tree ("Designdocument MyOS Core Service.md", 5): every folder of the Team folder
(empty) and every file of a .MyOS, built from a WebDAV walk; no user documents. Rebuilt when
the Team folder's ETag changes; a rebuild that fails keeps the shadow there was."""

import pytest

from cloud.service.shadow import ShadowKeeper, build_shadow, matters
from core.nextcloud_dav import Entry, NextcloudError
from core.brand import META_DIR

FILES = {
    f"/{META_DIR}/Project.md": b"# MyOS Project\n",
    f"/{META_DIR}/ACLs.md": b"# Permissions\n",
    f"/{META_DIR}/Templates/Standard/04_Finanz/{META_DIR}/Desk.md": b"theme: light\n",
    f"/Familie/{META_DIR}/Project.md": b"# MyOS Project\n",
    "/Familie/Rechnung.pdf": b"%PDF",
}
FOLDERS = ["/", f"/{META_DIR}", f"/{META_DIR}/Templates", f"/{META_DIR}/Templates/Standard", f"/{META_DIR}/Templates/Standard/04_Finanz",
           f"/{META_DIR}/Templates/Standard/04_Finanz/{META_DIR}", "/Familie", f"/Familie/{META_DIR}", "/Familie/Fotos"]


class FakeDAV:
    def __init__(self, files=FILES, folders=FOLDERS):
        self.files, self.folders, self.tag, self.fail, self.got = dict(files), list(folders), '"1"', False, []
        self.etags = {}

    def tree(self):
        if self.fail:
            raise NextcloudError("Nextcloud is not reachable")
        tree = {path: Entry(path, True) for path in self.folders}
        tree.update({path: Entry(path, False, etag=self.etags.get(path, '"a"')) for path in self.files})
        return tree

    def get(self, path):
        self.got.append(path)
        return self.files.get(path)

    def etag(self):
        return self.tag


def test_folders_and_settings_files_come_documents_do_not(tmp_path):
    dav = FakeDAV()
    build_shadow(dav, tmp_path / "s")

    assert (tmp_path / "s" / "Familie" / "Fotos").is_dir()
    assert (tmp_path / "s" / META_DIR / "ACLs.md").read_bytes() == b"# Permissions\n"
    assert (tmp_path / "s" / META_DIR / "Templates" / "Standard" / "04_Finanz" / META_DIR / "Desk.md").is_file()
    assert not (tmp_path / "s" / "Familie" / "Rechnung.pdf").exists()
    assert "/Familie/Rechnung.pdf" not in dav.got


@pytest.mark.parametrize("bad", [f"/../{META_DIR}/x.md", f"/a/./{META_DIR}/x.md", f"/a\\..\\{META_DIR}/x.md"])
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


@pytest.mark.parametrize("path, is_dir, expected", [
    ("/Familie/Neu", True, True),  # a folder: in the shadow
    (f"/Familie/{META_DIR}/ACLs.md", False, True),  # a .MyOS file: in the shadow
    (f"/{META_DIR}/Templates/Standard/04_Finanz/Liesmich.md", False, True),
    ("/Familie/Rechnung.pdf", False, False),  # a document: not
])
def test_only_folders_and_settings_files_matter_to_the_shadow(path, is_dir, expected):
    assert matters(path, is_dir) is expected


def test_a_rebuild_takes_unchanged_files_from_the_shadow_before(tmp_path):
    # Every request costs (a quarter of a second on the test instance): only what changed comes.
    dav = FakeDAV()
    keeper = ShadowKeeper(tmp_path / "base", dav)
    keeper.refresh()
    dav.got.clear()
    dav.files[f"/{META_DIR}/ACLs.md"], dav.etags[f"/{META_DIR}/ACLs.md"] = b"# Permissions\nneu\n", '"b"'
    dav.tag = '"2"'

    keeper.refresh()

    assert dav.got == [f"/{META_DIR}/ACLs.md"]
    assert (keeper.root / META_DIR / "ACLs.md").read_bytes() == b"# Permissions\nneu\n"
    assert (keeper.root / META_DIR / "Project.md").read_bytes() == b"# MyOS Project\n"
