"""A new project gets what its template's root .MyOS holds (ACLs.md, Desk.md, ...).

Templates are ordinary folder structures; whatever lies in Templates/<name>/.MyOS is
copied into the new project's .MyOS when it is created (nothing already there is
overwritten), like the .MyOS of a template folder when an embryo is born. See
"Designdocument ACLs.md", 10 (Templates with their own ACLs)."""

from pathlib import Path

import pytest

from core.acl import ACLPolicy
from core.project import ProjectConfig


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


TEMPLATE_ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "## Buchhaltung\n- /04_Finanz/: read, write\n"
)
PARENT_ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "# Users\nOliver: Admin\nAnna: Buchhaltung  # seit 2026\n"
)


@pytest.fixture
def tree(tmp_path):
    template = tmp_path / "Templates" / "Standard"
    (template / ".MyOS" / "ACLs-history").mkdir(parents=True)
    (template / "04_Finanz").mkdir()
    (template / "01_Info").mkdir()
    (template / ".MyOS" / "ACLs.md").write_text(TEMPLATE_ACLS)
    (template / ".MyOS" / "Desk.md").write_text("# Desk\nPanelTheme: Mint-Y-Blue\n")
    (template / ".MyOS" / "ACLs-history" / "ACLs-alt.md").write_text("alt\n")
    (template / ".MyOS" / ".ACLs.md.draft").write_text("draft\n")
    projects = tmp_path / "Projekte"
    (projects / ".MyOS").mkdir(parents=True)
    (projects / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (projects / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (projects / ".MyOS" / "ACLs.md").write_text(PARENT_ACLS)
    return {"template": template, "projects": projects}


def test_a_new_project_gets_the_templates_myos_files(tree):
    project = tree["projects"] / "Kunde"

    assert ProjectConfig.make_project(project)

    myos = project / ".MyOS"
    assert (myos / "Desk.md").read_text() == "# Desk\nPanelTheme: Mint-Y-Blue\n"
    assert (myos / "ACLs.md").read_text().startswith(TEMPLATE_ACLS)
    assert (myos / "Project.md").read_text() == "# MyOS Project\n"
    assert not (myos / "ACLs-history").exists()  # the template's own history stays there
    assert not (myos / ".ACLs.md.draft").exists()


def test_the_buchhalter_gets_finanz_in_every_new_project(tree):
    project = tree["projects"] / "Kunde"
    ProjectConfig.make_project(project)

    policy = ACLPolicy.from_project(project)

    assert policy.roles_for_user("anna") == {"buchhaltung"}
    assert policy.can_access("buchhaltung", "/04_Finanz/Rechnung.pdf", "write")


def test_without_people_in_the_template_the_people_so_far_stay(tree):
    project = tree["projects"] / "Kunde"
    ProjectConfig.make_project(project)

    text = (project / ".MyOS" / "ACLs.md").read_text()

    assert text == TEMPLATE_ACLS + "\n# Users\nOliver: Admin\nAnna: Buchhaltung  # seit 2026\n"


def test_the_creator_keeps_managing_a_project_whose_template_lists_people(tree):
    (tree["template"] / ".MyOS" / "ACLs.md").write_text(TEMPLATE_ACLS + "\n# Users\nChefin: Admin\n")
    project = tree["projects"] / "Kunde"
    ProjectConfig.make_project(project)

    policy = ACLPolicy.from_project(project)

    assert (project / ".MyOS" / "ACLs.md").read_text().endswith("# Users\nChefin: Admin\nOliver: Admin\n")
    assert policy.roles_for_user("oliver") == {"admin"}
    assert policy.roles_for_user("anna") == set()  # the template's people, not the parent's


def test_nothing_already_in_the_project_is_overwritten(tree):
    project = tree["projects"] / "Kunde"
    (project / ".MyOS").mkdir(parents=True)
    (project / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Eigen\n")

    ProjectConfig.make_project(project)

    assert (project / ".MyOS" / "Desk.md").read_text() == "# Desk\nThemePreset: Eigen\n"
    assert (project / ".MyOS" / "ACLs.md").exists()


def test_with_several_templates_the_first_one_counts(tree, tmp_path):
    other = tmp_path / "Templates" / "Person" / ".MyOS"
    other.mkdir(parents=True)
    (other / "Desk.md").write_text("# Desk\nPanelTheme: Anders\n")
    (other / "Color.md").write_text("# Color\n#123456\n")
    (tree["projects"] / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\nPerson\n")
    project = tree["projects"] / "Kunde"

    ProjectConfig.make_project(project)

    assert "Mint-Y-Blue" in (project / ".MyOS" / "Desk.md").read_text()
    assert (project / ".MyOS" / "Color.md").read_text() == "# Color\n#123456\n"


def test_symlinks_in_the_template_are_not_followed(tree, tmp_path):
    secret = tmp_path / "geheim.md"
    secret.write_text("geheim\n")
    (tree["template"] / ".MyOS" / "Notes.md").symlink_to(secret)
    project = tree["projects"] / "Kunde"

    ProjectConfig.make_project(project)

    assert not (project / ".MyOS" / "Notes.md").exists()


def test_the_templates_myos_is_neither_a_role_nor_an_embryo(tree):
    from core.localBlueprintLayer import Blueprint

    project = tree["projects"] / "Kunde"
    ProjectConfig.make_project(project)

    assert ACLPolicy.from_project(project).roles == {"admin", "buchhaltung", "04_finanz", "01_info"}
    tree["template"].joinpath("04_Finanz", ".MyOS").mkdir()
    assert sorted(Blueprint(project)._load_embryo_tree()) == ["01_Info", "04_Finanz"]
    assert Blueprint(project)._load_embryo_tree()["04_Finanz"] == {}


@pytest.mark.parametrize("people", ["", "\n# Users\nHelmut: 04_Finanz\n"])
def test_the_creators_groups_come_along_when_the_template_lacks_them(tree, people):
    # Live case: the template has no "## Admin"; "Oliver: Admin" alone would leave the
    # creator without any right in the new project, unable to manage it.
    template_acls = "# Permissions\n\n## Buchhaltung\n- /04_Finanz/: read, write\n" + people
    (tree["template"] / ".MyOS" / "ACLs.md").write_text(template_acls)
    project = tree["projects"] / "Kunde"

    ProjectConfig.make_project(project)

    text = (project / ".MyOS" / "ACLs.md").read_text()
    policy = ACLPolicy.from_project(project)
    assert "## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n" in text
    assert "change" in policy.rights_for("admin", "/.MyOS/ACLs.md")
    assert policy.roles_for_user("oliver") == {"admin"}
    assert text.index("## Admin") < text.index("# Users")
