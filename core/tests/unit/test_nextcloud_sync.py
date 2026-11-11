"""Bringing a project's ACLs.md and embryos into its Team folder (myacl sync, and the MyOS
core service after each change). No network: a fake Team folder holds entries, their rules
and files as Nextcloud does."""

import pytest

from core.acl_nextcloud import bits, mask_of
from core.nextcloud_dav import Entry, ExistingRule
from core.nextcloud_sync import NextcloudSync, SyncRefused

ACLS = (
    "# Permissions\n\n## Admin\n- /*: read, write, delete, change\n\n"
    "## Familie\n- /Familie/: read, write\n\n# Users\nOliver: Admin\nLisa: Familie\n"
)
NEXTCLOUD_MD = "# Nextcloud\nurl: http://localhost:8081\nfolder: Projekte\ngroup: Projekte\n\n# Accounts\nOliver: oliver\nLisa: lisa\n"


class FakeTeamFolder:
    def __init__(self, folders):
        self.entries = {path: Entry(path, True, acl_enabled=True, can_manage=True) for path in folders}
        self.files = {}
        self.tags = []

    def tree(self):
        return {path: Entry(e.path, e.is_dir, list(e.rules), e.acl_enabled, e.can_manage) for path, e in self.entries.items()}

    def set_rules(self, path, rules):
        self.entries[path].rules = [ExistingRule(r.kind, r.account, mask_of(r), bits(r.allowed)) for r in rules]

    def system_tags(self):
        return {name: str(i) for i, name in enumerate(self.tags, 1)}

    def create_system_tag(self, name):
        self.tags.append(name)

    def get(self, path):
        return self.files.get(path)

    def exists(self, path):
        return path in self.entries

    def mkcol(self, path):
        self.entries.setdefault(path, Entry(path, True))

    def put(self, path, data):
        self.files[path] = data
        self.entries.setdefault(path, Entry(path, False))

    def delete(self, path):
        self.files.pop(path, None)
        self.entries.pop(path, None)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "Projekte"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    (root / ".MyOS" / "Nextcloud.md").write_text(NEXTCLOUD_MD)
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    finanz = root / ".MyOS" / "Templates" / "Standard" / "04_Finanz"
    finanz.mkdir(parents=True)
    (finanz / "Liesmich.md").write_text("Finanzen")
    (root / "Familie").mkdir()
    return root


def test_what_differs_is_sent_and_then_all_is_in_step(project):
    cloud = FakeTeamFolder(["/", "/.MyOS", "/Familie"])
    sync = NextcloudSync(project, cloud)

    first = sync.compare()
    assert first.changes and first.pending and not first.in_step

    assert sync.send(first) == []
    assert cloud.files["/.MyOS/Embryos/04_Finanz/Liesmich.md"] == b"Finanzen"
    assert any(r.account == "lisa" for r in cloud.entries["/Familie"].rules)
    assert NextcloudSync(project, cloud).compare().in_step


def test_without_the_team_folder_s_groups_nothing_is_compared(project):
    (project / ".MyOS" / "Nextcloud.md").write_text("# Nextcloud\nfolder: Projekte\n\n# Accounts\nLisa: lisa\n")

    with pytest.raises(SyncRefused, match="group"):
        NextcloudSync(project, FakeTeamFolder(["/"]))


def test_without_nextcloud_md_nothing_is_compared(project):
    (project / ".MyOS" / "Nextcloud.md").unlink()

    with pytest.raises(SyncRefused, match="Nextcloud.md"):
        NextcloudSync(project, FakeTeamFolder(["/"]))


@pytest.mark.parametrize("acls", ["Unsinn ohne Abschnitte\n", ACLS.replace("read, write, delete, change", "read, write")])
def test_an_acls_md_that_leaves_no_one_to_change_the_rights_is_noticed(project, acls):
    assert NextcloudSync(project, FakeTeamFolder(["/"])).someone_may_change()
    (project / ".MyOS" / "ACLs.md").write_text(acls)

    assert not NextcloudSync(project, FakeTeamFolder(["/"])).someone_may_change()


def test_the_tags_of_every_project_s_tags_md_are_made_once(project):
    (project / ".MyOS" / "Tags.md").write_text("# Tags\n#Wichtig\n#Rechnung\n")
    (project / "Familie" / ".MyOS").mkdir()
    (project / "Familie" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (project / "Familie" / ".MyOS" / "Tags.md").write_text("# Tags\n#Urlaub\n#Wichtig\n")
    cloud = FakeTeamFolder(["/", "/.MyOS", "/Familie"])
    cloud.tags = ["Rechnung"]  # there already, from someone else on the instance
    sync = NextcloudSync(project, cloud)

    comparison = sync.compare()
    assert comparison.tags == ["Urlaub", "Wichtig"] and not comparison.in_step
    sync.send(comparison)

    assert sorted(cloud.tags) == ["Rechnung", "Urlaub", "Wichtig"]
    assert NextcloudSync(project, cloud).compare().tags == []


def test_a_tag_the_instance_refuses_does_not_hold_up_the_rights(project):
    # Tag creation may be for admins only (Nextcloud's setting): the rules must still go.
    from core.nextcloud_dav import NextcloudError

    (project / ".MyOS" / "Tags.md").write_text("# Tags\n#Wichtig\n")
    cloud = FakeTeamFolder(["/", "/.MyOS", "/Familie"])

    def refuse(name):
        raise NextcloudError(f"Nextcloud answered 403 to POST /remote.php/dav/systemtags/{name}")

    cloud.create_system_tag = refuse
    sync = NextcloudSync(project, cloud)

    assert sync.send(sync.compare()) == []  # no rule left open
    assert any(r.account == "lisa" for r in cloud.entries["/Familie"].rules)
    assert sync.refused_tags == ["Wichtig"]
