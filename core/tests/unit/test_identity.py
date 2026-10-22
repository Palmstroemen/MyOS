"""Who the user is in a project (see "Designdocument ACLs.md", 5.3).

People in "# Users" are people of the project, not login names. Each computer keeps the
user's names locally (~/.config/MyOS/Identity.md); in a project the user is the first of
them that the project lists, else (as before) the login name."""

from pathlib import Path

import pytest

from core import identity
from core.acl_edit import ACLEditError


@pytest.fixture(autouse=True)
def _own_config_home(monkeypatch, tmp_path_factory):
    # Security: Identity.md is the user's own file; never touch the real one.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    monkeypatch.delenv("MYOS_ACL_USER", raising=False)
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.setenv("LOGNAME", "orafelsberger")
    monkeypatch.setenv("USER", "orafelsberger")


ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "## Team\n- /work/: read, write\n\n"
    "# Users\nOliver Rafelsberger: Admin\nAnna Huber: Team\nKarl: Team\n"
)


def _project(tmp_path: Path, acls: str = ACLS) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / "work").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(acls)
    return root


def test_without_own_names_the_login_name_counts():
    assert identity.own_names() == []
    assert identity.person_in({"karl", "orafelsberger"}) == "orafelsberger"


def test_the_first_own_name_the_project_lists_counts():
    identity.identity_file().parent.mkdir(parents=True, exist_ok=True)
    identity.identity_file().write_text("# Identity\nNames: Oliver, Oliver Rafelsberger  # Kunden\n")

    assert identity.own_names() == ["Oliver", "Oliver Rafelsberger"]
    assert identity.person_in({"oliver rafelsberger", "anna"}) == "oliver rafelsberger"
    assert identity.person_in({"oliver", "oliver rafelsberger"}) == "oliver"
    assert identity.person_in({"anna"}) == "orafelsberger"  # listed nowhere: the login


def test_myos_acl_user_wins(monkeypatch):
    identity.add_own_name("Oliver")
    monkeypatch.setenv("MYOS_ACL_USER", "Anna")

    assert identity.person_in({"oliver", "anna"}) == "anna"


def test_adding_a_name_keeps_the_file_and_adds_each_name_once():
    path = identity.identity_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Meine Namen\n\n# Identity\nNames: Oliver\n")

    identity.add_own_name("Oliver Rafelsberger")
    identity.add_own_name("oliver")

    assert path.read_text() == "Meine Namen\n\n# Identity\nNames: Oliver, Oliver Rafelsberger\n"


def test_adding_a_name_creates_the_file_and_refuses_symlinks(tmp_path):
    identity.add_own_name("Oliver")
    assert identity.identity_file().read_text() == "# Identity\nNames: Oliver\n"

    target = tmp_path / "elsewhere.md"
    target.write_text("# Identity\n")
    identity.identity_file().unlink()
    identity.identity_file().symlink_to(target)
    with pytest.raises(OSError):
        identity.add_own_name("Anna")
    assert target.read_text() == "# Identity\n"


def test_the_user_of_a_project_follows_identity_and_acls(tmp_path):
    root = _project(tmp_path)
    assert identity.acl_user_for(root / "work") == "orafelsberger"

    identity.add_own_name("Oliver Rafelsberger")
    assert identity.acl_user_for(root / "work") == "oliver rafelsberger"

    (root / ".MyOS" / "ACLs.md").write_text(ACLS.replace("Oliver Rafelsberger: Admin\n", "Oliver R.: Admin\n"))
    assert identity.acl_user_for(root) == "orafelsberger"


def test_who_one_may_claim_to_be_leaves_out_people_who_may_change_the_rights(tmp_path):
    # Until there is real authentication, being an admin takes a name written by hand.
    root = _project(tmp_path)

    assert identity.claimable_people(root / "work") == ["Anna Huber", "Karl"]


def test_claiming_a_person_adds_the_name_and_admins_are_refused(tmp_path):
    root = _project(tmp_path)

    identity.claim_person(root, "anna huber")
    assert identity.own_names() == ["Anna Huber"]
    assert identity.acl_user_for(root) == "anna huber"

    with pytest.raises(ACLEditError):
        identity.claim_person(root, "Oliver Rafelsberger")
    with pytest.raises(ACLEditError):
        identity.claim_person(root, "Niemand")
    assert identity.own_names() == ["Anna Huber"]
