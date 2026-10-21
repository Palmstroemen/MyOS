"""Editing ACLs.md: one rule for one role at one path (see ACL design document 5.3)."""

from pathlib import Path

import pytest

from core.acl_edit import ACLEditError, set_role_rights
from core.acl_view import ACLView


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


ACLS = (
    "# Permissions\n"
    "\n"
    "## Folder\n"
    "- /{Folder}/: read, write\n"
    "- /info/: read\n"
    "\n"
    "## Admin\n"
    "- /*: read, write, execute\n"
    "- /.MyOS/ACLs.md: read, write, change\n"
    "\n"
    "## Buchhalter\n"
    "- /finanz/: read, write\n"
    "\n"
    "# Users\n"
    "Anna: Admin\n"
    "Karl: Buchhalter\n"
)


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("finanz", "info", "work"):
        (root / "Templates" / "Standard" / folder).mkdir(parents=True)
        (root / folder).mkdir()
    (root / "finanz" / "archiv").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    return root


def _acls(root: Path) -> str:
    return (root / ".MyOS" / "ACLs.md").read_text()


def _rights(root: Path, role: str, path: Path) -> set:
    return set(ACLView.for_path(path).rights_for_role(role, path))


def test_new_rule_is_added_to_the_role_section_and_nothing_else_changes(tmp_path):
    root = _project(tmp_path)

    set_role_rights(root / "finanz" / "archiv", "Buchhalter", {"read"}, editor="anna")

    text = _acls(root)
    assert "- /finanz/archiv/: read\n" in text
    assert text.replace("- /finanz/archiv/: read\n", "") == ACLS  # order, spelling, blank lines kept
    assert text.index("/finanz/archiv/") < text.index("# Users")  # inside the Buchhalter section
    assert _rights(root, "buchhalter", root / "finanz" / "archiv") == {"read"}
    assert _rights(root, "buchhalter", root / "finanz") == {"read", "write"}


def test_existing_rule_is_replaced(tmp_path):
    root = _project(tmp_path)

    set_role_rights(root / "finanz", "buchhalter", {"read", "write", "delete"}, editor="anna")

    text = _acls(root)
    assert "- /finanz/: read, write, delete\n" in text
    assert text.count("/finanz/") == 1
    assert _rights(root, "buchhalter", root / "finanz") == {"read", "write", "delete"}


def test_no_rights_writes_none_and_none_rights_restores_inheritance(tmp_path):
    root = _project(tmp_path)

    set_role_rights(root / "finanz" / "archiv", "Buchhalter", set(), editor="anna")
    assert "- /finanz/archiv/: none\n" in _acls(root)
    assert _rights(root, "buchhalter", root / "finanz" / "archiv") == set()

    set_role_rights(root / "finanz" / "archiv", "Buchhalter", None, editor="anna")
    assert _acls(root) == ACLS
    assert _rights(root, "buchhalter", root / "finanz" / "archiv") == {"read", "write"}


def test_template_folder_role_gets_a_section_with_only_the_explicit_entry(tmp_path):
    root = _project(tmp_path)

    set_role_rights(root / "finanz" / "archiv", "finanz", {"read"}, editor="anna")

    text = _acls(root)
    section = text[text.index("## finanz"):text.index("# Users")]
    # The folder rules stay inherited (not copied), so nothing else changes for the role ...
    assert section == "## finanz\n- /finanz/archiv/: read\n\n"
    assert _rights(root, "finanz", root / "finanz") == {"read", "write"}
    assert _rights(root, "finanz", root / "info") == {"read"}
    assert _rights(root, "finanz", root / "finanz" / "archiv") == {"read"}
    # ... and the other folder roles keep the defaults.
    assert _rights(root, "work", root / "work") == {"read", "write"}


def test_only_users_with_change_on_acls_may_edit(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(PermissionError):
        set_role_rights(root / "finanz", "Buchhalter", {"read"}, editor="karl")
    with pytest.raises(PermissionError):
        set_role_rights(root / "finanz", "Buchhalter", {"read"}, editor="nobody")
    assert _acls(root) == ACLS


def test_editor_cannot_take_away_their_own_change_right(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(ACLEditError):
        set_role_rights(root / ".MyOS" / "ACLs.md", "Admin", {"read", "write"}, editor="anna")
    assert _acls(root) == ACLS


def test_previous_version_is_kept_with_date_and_editor(tmp_path):
    root = _project(tmp_path)

    set_role_rights(root / "finanz", "Buchhalter", {"read"}, editor="anna")

    kept = list((root / ".MyOS" / "ACLs-history").glob("ACLs-*-anna.md"))
    assert len(kept) == 1
    assert kept[0].read_text() == ACLS


def test_unknown_role_and_unknown_right_are_rejected(tmp_path):
    root = _project(tmp_path)

    with pytest.raises(ACLEditError):
        set_role_rights(root / "finanz", "Marketing", {"read"}, editor="anna")
    with pytest.raises(ACLEditError):
        set_role_rights(root / "finanz", "Buchhalter", {"fly"}, editor="anna")
    assert _acls(root) == ACLS


def test_paths_in_subprojects_are_written_relative_to_the_acl_project(tmp_path):
    root = _project(tmp_path)
    sub = root / "Familie"
    (sub / ".MyOS").mkdir(parents=True)
    (sub / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (sub / "Ich").mkdir()

    set_role_rights(sub / "Ich", "Buchhalter", {"read"}, editor="anna")

    assert "- /Familie/Ich/: read\n" in _acls(root)
    assert _rights(root, "buchhalter", sub / "Ich") == {"read"}


def test_can_edit_and_own_rule(tmp_path):
    from core.acl_edit import can_edit, own_rule

    root = _project(tmp_path)

    assert can_edit(root / "finanz", "anna") is True
    assert can_edit(root / "finanz", "karl") is False
    assert can_edit(tmp_path / "elsewhere", "anna") is False

    assert own_rule(root / "finanz", "Buchhalter") == {"read", "write"}
    assert own_rule(root / "finanz" / "archiv", "Buchhalter") is None  # inherited only
    set_role_rights(root / "finanz" / "archiv", "Buchhalter", set(), editor="anna")
    assert own_rule(root / "finanz" / "archiv", "Buchhalter") == set()  # "none"


def test_rules_follow_a_renamed_folder(tmp_path):
    from core.acl_edit import move_rules

    root = _project(tmp_path)
    set_role_rights(root / "finanz" / "archiv", "Buchhalter", {"read"}, editor="anna")
    (root / "finanz").rename(root / "Finanzen")

    changed = move_rules(root / "finanz", root / "Finanzen", editor="karl")  # karl has no change right

    text = _acls(root)
    assert changed is True
    assert "- /Finanzen/: read, write\n" in text and "- /Finanzen/archiv/: read\n" in text
    assert "/finanz/" not in text
    assert "- /{Folder}/: read, write\n" in text  # folder rules are no fixed paths
    assert _rights(root, "buchhalter", root / "Finanzen" / "archiv") == {"read"}
    assert list((root / ".MyOS" / "ACLs-history").glob("ACLs-*-karl.md"))


def test_moving_without_rules_changes_nothing(tmp_path):
    from core.acl_edit import move_rules

    root = _project(tmp_path)
    (root / "work" / "notes").mkdir()

    assert move_rules(root / "work" / "notes", root / "info" / "notes", editor="karl") is False
    assert _acls(root) == ACLS


def test_rules_waiting_at_the_new_path_block_the_move(tmp_path):
    from core.acl_edit import check_move_rules

    root = _project(tmp_path)
    set_role_rights(root / "Neu", "Buchhalter", set(), editor="anna")  # a prepared lock for /Neu/

    with pytest.raises(ACLEditError):
        check_move_rules(root / "finanz", root / "Neu")
    check_move_rules(root / "work", root / "Anders")  # no rules at either place: fine


COMMENTED = (
    "<!--\n"
    "- /finanz/archiv/: read, write, delete\n"
    "- /Neu/: none\n"
    "-->\n"
)


def test_commented_out_rules_are_not_edited(tmp_path):
    from core.acl_edit import own_rule

    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("- /finanz/: read, write\n", "- /finanz/: read, write\n" + COMMENTED))

    assert own_rule(root / "finanz" / "archiv", "Buchhalter") is None
    set_role_rights(root / "finanz" / "archiv", "Buchhalter", {"read"}, editor="anna")

    assert COMMENTED in _acls(root)
    assert _rights(root, "buchhalter", root / "finanz" / "archiv") == {"read"}
    assert own_rule(root / "finanz" / "archiv", "Buchhalter") == {"read"}


def test_commented_out_rules_neither_follow_nor_block_a_move(tmp_path):
    from core.acl_edit import check_move_rules, move_rules

    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("- /finanz/: read, write\n", "- /finanz/: read, write\n" + COMMENTED))

    check_move_rules(root / "work", root / "Neu")  # only a commented rule waits there
    (root / "finanz").rename(root / "Finanzen")
    assert move_rules(root / "finanz", root / "Finanzen", editor="karl") is True

    assert COMMENTED in _acls(root)
    assert "- /Finanzen/: read, write\n" in _acls(root)


def test_own_rule_ignores_an_inline_comment(tmp_path):
    from core.acl_edit import own_rule

    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("- /finanz/: read, write\n",
                                     "- /finanz/: read, write  # seit 2026\n- /finanz/archiv/: none # gesperrt\n"))

    assert own_rule(root / "finanz", "Buchhalter") == {"read", "write"}
    assert own_rule(root / "finanz" / "archiv", "Buchhalter") == set()


def test_a_rule_with_a_trailing_comment_is_edited_like_any_rule(tmp_path):
    from core.acl_edit import own_rule

    root = _project(tmp_path)
    acl_file = root / ".MyOS" / "ACLs.md"
    acl_file.write_text(ACLS.replace("- /finanz/: read, write\n", "- /finanz/: read, write <!-- seit 2026 -->\n"))

    assert own_rule(root / "finanz", "Buchhalter") == {"read", "write"}
    set_role_rights(root / "finanz", "Buchhalter", {"read"}, editor="anna")

    assert _rights(root, "buchhalter", root / "finanz") == {"read"}
    assert _acls(root).count("/finanz/") == 1
