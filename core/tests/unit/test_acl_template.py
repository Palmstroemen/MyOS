"""Rights of a template: seen and edited in its folders like in a project.

A template is no project (no Project.md); its .MyOS/ACLs.md takes effect in the projects
made from it. Its "# Users" are the people of those future projects, so whoever may
write the template may edit its rights (no lock-out check there). Who may write it is up
to the project whose .MyOS/Templates holds it, not to the template's own rights."""

import os
from pathlib import Path

import pytest

from core.acl_edit import add_user, can_edit, set_role_rights
from core.acl_view import ACLView
from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


ACLS = "# Permissions\n\n## Folder\n- /{Folder}/: read, write\n\n## Buchhaltung\n- /04_Finanz/: read, write\n"
PROJECT_ACLS = (
    "# Permissions\n\n## Admin\n- /*: read, write\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "## Buchhaltung\n- /Finanz/: read, write\n\n# Users\nOliver: Admin\nAnna: Buchhaltung\n"
)


@pytest.fixture
def template(tmp_path):
    project = tmp_path / "Projekte"
    (project / ".MyOS").mkdir(parents=True)
    (project / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (project / ".MyOS" / "ACLs.md").write_text(PROJECT_ACLS)
    root = project / ".MyOS" / "Templates" / "Standard"
    (root / ".MyOS").mkdir(parents=True)
    (root / "04_Finanz").mkdir()
    (root / "01_Info").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    return root


def test_the_rights_of_a_template_are_shown_in_its_folders(template):
    view = ACLView.for_path(template / "04_Finanz")

    assert view is not None and view.project_root == template.resolve()
    assert view.policy.roles == {"buchhaltung", "04_finanz", "01_info"}
    assert view.rights_for_role("buchhaltung", template / "04_Finanz") >= {"read", "write"}


def test_rights_in_a_template_are_edited_without_people(template):
    assert can_edit(template / "04_Finanz", "oliver")

    set_role_rights(template / "01_Info", "Buchhaltung", {"read"}, editor="oliver")

    assert "- /01_Info/: read\n" in (template / ".MyOS" / "ACLs.md").read_text()
    assert list((template / ".MyOS" / "ACLs-history").iterdir())


def test_who_may_edit_a_template_is_up_to_the_project_that_holds_it(template):
    # Anna is Buchhaltung in the template's future projects, but may not write the
    # project's .MyOS, where the template lies.
    assert not can_edit(template / "04_Finanz", "anna")
    with pytest.raises(PermissionError):
        set_role_rights(template / "01_Info", "Buchhaltung", {"read"}, editor="anna")
    assert (template / ".MyOS" / "ACLs.md").read_text() == ACLS


def test_a_template_outside_any_project_is_governed_by_the_file_system(tmp_path, monkeypatch):
    monkeypatch.setenv("MYOS_TEMPLATES_DIR", str(tmp_path / "Global"))
    root = tmp_path / "Global" / "Standard"
    (root / ".MyOS").mkdir(parents=True)
    (root / "01_Info").mkdir()
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)

    assert can_edit(root / "01_Info", "anna")


def test_people_can_be_added_to_a_template(template):
    add_user(template, "Anna Huber", {"Buchhaltung"}, editor="oliver")
    add_user(template, "Karl", {"04_Finanz"}, editor="oliver")  # no lock-out check in templates

    assert (template / ".MyOS" / "ACLs.md").read_text() == ACLS + "\n# Users\nAnna Huber: Buchhaltung\nKarl: 04_Finanz\n"


def test_a_template_one_may_not_write_cannot_be_edited(template):
    acl_file = template / ".MyOS" / "ACLs.md"
    acl_file.chmod(0o444)
    try:
        if os.access(acl_file, os.W_OK):
            pytest.skip("running as root: file permissions do not apply")
        assert not can_edit(template, "oliver")
        with pytest.raises(PermissionError):
            set_role_rights(template / "01_Info", "Buchhaltung", {"read"}, editor="oliver")
    finally:
        acl_file.chmod(0o644)


def test_the_acl_panel_in_a_template(template, monkeypatch):
    monkeypatch.delenv("MYOS_ACL_USER")
    (template / ".MyOS" / "ACLs.md").write_text(ACLS + "\n# Users\nChefin: Buchhaltung\n")

    summary = ScopeApi(str(template)).acl_summary(str(template), [str(template / "04_Finanz")])

    assert summary["hasAcls"] and summary["canEdit"]
    assert summary["listed"] is True and summary["whoChoices"] == []  # its people are future ones
