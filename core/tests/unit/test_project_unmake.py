"""A project becomes an ordinary folder again (crossed-out P-Button).

What creating the project wrote is remembered (.MyOS/.created.json); without anything of
its own since, .MyOS is simply removed. Settings of its own (changed rights, tags, a
trash, ...) are not lost: .MyOS goes into the parent project's trash as "MyOS settings".
Not possible for the top project and outside the projects tree; subprojects stay."""

from pathlib import Path

import pytest

from core import trash
from core.project import ProjectConfig
from core.project_unmake import ProjectHasOwnSettings, can_unmake, own_settings, unmake_project


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def tree(tmp_path):
    template = tmp_path / "Templates" / "Standard"
    (template / ".MyOS").mkdir(parents=True)
    (template / "04_Finanz").mkdir()
    (template / ".MyOS" / "ACLs.md").write_text("# Permissions\n\n## Buchhaltung\n- /04_Finanz/: read, write\n")
    (template / ".MyOS" / "Desk.md").write_text("# Desk\nPanelTheme: Mint-Y-Blue\n")
    projects = tmp_path / "Projekte"
    (projects / ".MyOS").mkdir(parents=True)
    (projects / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (projects / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (projects / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
        "# Users\nOliver: Admin\nAnna: Buchhaltung\n")
    kunde = projects / "Kunde"
    (kunde / "Rechnungen").mkdir(parents=True)
    (kunde / "Rechnungen" / "r1.pdf").write_text("pdf\n")
    assert ProjectConfig.make_project(kunde)
    return {"projects": projects, "kunde": kunde, "tmp": tmp_path}


def test_a_fresh_project_becomes_a_folder_again(tree):
    kunde = tree["kunde"]
    (kunde / ".MyOS" / ".TagsHere.json").write_text("{}")  # a cache, not a setting

    assert can_unmake(kunde)
    assert own_settings(kunde) == []
    unmake_project(kunde, "oliver")

    assert not (kunde / ".MyOS").exists()
    assert (kunde / "Rechnungen" / "r1.pdf").read_text() == "pdf\n"


def test_settings_of_its_own_are_named_and_not_removed_without_consent(tree):
    kunde = tree["kunde"]
    acls = kunde / ".MyOS" / "ACLs.md"
    acls.write_text(acls.read_text() + "Karl: Admin\n")
    (kunde / ".MyOS" / "Tags.md").write_text("# Tags\nwichtig\n")
    (kunde / ".MyOS" / "ACLs-history").mkdir()
    (kunde / ".MyOS" / "ACLs-history" / "alt.md").write_text("alt\n")
    (kunde / ".MyOS" / "Trash" / "files").mkdir(parents=True)  # empty trash: nothing of its own

    assert own_settings(kunde) == ["ACLs-history", "ACLs.md", "Tags.md"]
    with pytest.raises(ProjectHasOwnSettings):
        unmake_project(kunde, "oliver")
    assert (kunde / ".MyOS" / "Tags.md").exists()


def test_with_consent_they_go_into_the_parents_trash(tree):
    kunde = tree["kunde"]
    (kunde / ".MyOS" / "Tags.md").write_text("# Tags\nwichtig\n")

    unmake_project(kunde, "oliver", keep_own=True)

    assert not (kunde / ".MyOS").exists()
    entries = trash.list_trash(tree["projects"])
    assert [(e.original, e.is_dir, e.deleted_by) for e in entries] == [("Kunde/MyOS settings", True, "oliver")]
    restored = trash.restore(tree["projects"], entries[0].name)
    assert (restored / "Tags.md").read_text() == "# Tags\nwichtig\n"


def test_subprojects_stay_projects(tree):
    sub = tree["kunde"] / "Teilprojekt"
    assert ProjectConfig.make_project(sub)

    unmake_project(tree["kunde"], "oliver")

    assert (sub / ".MyOS" / "Project.md").exists()


def test_projects_made_before_count_everything_but_the_marker_as_their_own(tree):
    old = tree["projects"] / "Alt"
    (old / ".MyOS").mkdir(parents=True)
    (old / ".MyOS" / "Project.md").write_text("---\nwindow_x: 10\n---\n# MyOS Project\n")
    assert own_settings(old) == []
    (old / ".MyOS" / "Desk.md").write_text("# Desk\n")
    assert own_settings(old) == ["Desk.md"]


def test_what_cannot_be_turned_back(tree):
    assert not can_unmake(tree["projects"])                       # the top project
    assert not can_unmake(tree["kunde"] / "Rechnungen")           # no project
    assert not can_unmake(tree["tmp"] / "Templates" / "Standard")  # a template
    with pytest.raises(ValueError):
        unmake_project(tree["projects"], "oliver")
    assert (tree["projects"] / ".MyOS" / "Project.md").exists()
