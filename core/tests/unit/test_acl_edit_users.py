"""Editing a person's groups in ACLs.md (# Users), see ACL design document 5.3."""

from pathlib import Path

import pytest

from core.acl_edit import ACLEditError, set_user_roles
from core.acl_view import ACLView


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


ACLS = (
    "# Permissions\n"
    "\n"
    "## Folder\n"
    "- /{Folder}/: read, write\n"
    "\n"
    "## Admin\n"
    "- /*: read, write, execute\n"
    "- /.MyOS/ACLs.md: read, write, change\n"
    "\n"
    "## Buchhalter\n"
    "- /finanz/: read, write\n"
    "\n"
    "## Team\n"
    "- /work/: read\n"
    "\n"
    "# Users\n"
    "Anna: Admin\n"
    "Karl: Buchhalter  # seit 2026\n"
    "\n"
    "Mia: Team\n"
)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("finanz", "work", "info"):
        (root / "Templates" / "Standard" / folder).mkdir(parents=True)
        (root / folder).mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    return root


def _acls(root: Path) -> str:
    return (root / ".MyOS" / "ACLs.md").read_text()


def _roles(root: Path, user: str) -> set:
    return set(ACLView.for_path(root).policy.roles_for_user(user))


def test_adding_a_group_keeps_the_written_ones_first(tmp_path):
    root = _project(tmp_path)

    kept = set_user_roles(root / "work", "karl", {"Buchhalter", "Team"}, editor="anna")

    assert "Karl: Buchhalter, Team\n" in _acls(root)
    assert _acls(root).replace("Karl: Buchhalter, Team\n", "Karl: Buchhalter  # seit 2026\n") == ACLS
    assert _roles(root, "Karl") == {"buchhalter", "team"}
    assert kept is not None and kept.read_text() == ACLS


def test_template_folder_roles_can_be_given(tmp_path):
    root = _project(tmp_path)

    set_user_roles(root, "Mia", {"team", "info"}, editor="anna")

    assert "Mia: Team, info\n" in _acls(root)
    assert _roles(root, "mia") == {"team", "info"}


def test_no_groups_removes_the_line(tmp_path):
    root = _project(tmp_path)

    set_user_roles(root, "Mia", set(), editor="anna")

    assert "Mia" not in _acls(root)
    assert _roles(root, "mia") == set()


def test_unchanged_groups_write_nothing(tmp_path):
    root = _project(tmp_path)

    assert set_user_roles(root, "Mia", {"Team"}, editor="anna") is None
    assert _acls(root) == ACLS


def test_only_users_with_change_may_edit_groups(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(PermissionError):
        set_user_roles(root, "Karl", {"Admin"}, editor="karl")
    assert _acls(root) == ACLS


def test_editor_cannot_take_away_their_own_change_right(tmp_path):
    from core.acl_edit import ACLSelfLockoutError

    root = _project(tmp_path)

    with pytest.raises(ACLSelfLockoutError):
        set_user_roles(root, "Anna", {"Team"}, editor="anna")
    assert _acls(root) == ACLS


def test_unknown_person_and_unknown_group_are_rejected(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(ACLEditError):
        set_user_roles(root, "Zoe", {"Team"}, editor="anna")  # adding people is a step of its own
    with pytest.raises(ACLEditError):
        set_user_roles(root, "Mia", {"Gibtsnicht"}, editor="anna")
    assert _acls(root) == ACLS


def test_commented_out_user_lines_are_left_alone(tmp_path):
    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("Mia: Team\n", "<!--\nMia: Admin\n-->\nMia: Team\n"))

    set_user_roles(root, "Mia", {"Buchhalter"}, editor="anna")

    assert "<!--\nMia: Admin\n-->\nMia: Buchhalter\n" in _acls(root)
    assert _roles(root, "mia") == {"buchhalter"}


def test_groups_unknown_here_are_kept(tmp_path):
    # e.g. a template folder role of another subproject: not offered here, so not dropped
    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("Mia: Team\n", "Mia: Kind, Team\n"))

    set_user_roles(root, "Mia", {"Buchhalter"}, editor="anna")

    assert "Mia: Kind, Buchhalter\n" in _acls(root)
    assert _roles(root, "mia") == {"kind", "buchhalter"}
