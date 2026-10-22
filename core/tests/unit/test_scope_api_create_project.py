"""ScopeApi: which folder may become a project (P-Button), and creating it.

A folder can become a project when it exists, is no project yet, lies below a .MyOS
(inside the projects tree) and is no template folder and no .MyOS folder."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_USER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def tree(tmp_path):
    projects = tmp_path / "Projekte"
    (projects / ".MyOS").mkdir(parents=True)
    (projects / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (projects / "Garten" / "Hecke").mkdir(parents=True)
    (projects / "notiz.md").write_text("x\n")
    (tmp_path / "Templates" / "Standard" / "04_Finanz").mkdir(parents=True)
    (tmp_path / "Musik").mkdir()
    return {"projects": projects, "tmp": tmp_path}


def test_folders_in_the_projects_tree_can_become_projects(tree):
    api = ScopeApi(str(tree["projects"]))

    assert api.can_create_project(str(tree["projects"] / "Garten"))
    assert api.can_create_project(str(tree["projects"] / "Garten" / "Hecke"))


@pytest.mark.parametrize("where", [
    "Projekte",                        # a project already
    "Projekte/notiz.md",               # a file
    "Projekte/Embryo",                 # not on disk (an embryo)
    "Projekte/.MyOS",                  # MyOS' own folder
    "Musik",                           # outside the projects tree: no .MyOS above
    "Templates/Standard/04_Finanz",    # a template folder
    "Templates/Standard",
])
def test_these_cannot_become_projects(tree, where):
    api = ScopeApi(str(tree["projects"]))

    assert not api.can_create_project(str(tree["tmp"] / where))


def test_creating_refuses_what_cannot_become_a_project(tree):
    api = ScopeApi(str(tree["projects"]))
    (tree["tmp"] / "Templates" / ".MyOS").mkdir()  # a .MyOS above, still a template

    assert api.create_project(str(tree["tmp"] / "Templates" / "Standard" / "04_Finanz")) is False
    assert not (tree["tmp"] / "Templates" / "Standard" / "04_Finanz" / ".MyOS").exists()

    assert api.create_project(str(tree["projects"] / "Garten")) is True
    assert api.is_project(str(tree["projects"] / "Garten"))
    assert not api.can_create_project(str(tree["projects"] / "Garten"))


def test_listed_project_folders_say_so(tree):
    api = ScopeApi(str(tree["projects"]))
    api.create_project(str(tree["projects"] / "Garten"))

    entries = {e["name"]: e for e in api.list_entries(str(tree["projects"]))}

    assert entries["Garten"].get("isProject") is True
    assert "isProject" not in entries["notiz.md"]


def test_a_project_becomes_a_folder_again(tree):
    api = ScopeApi(str(tree["projects"]))
    garten = str(tree["projects"] / "Garten")
    api.create_project(garten)

    assert api.can_remove_project(garten) and not api.can_remove_project(str(tree["projects"]))
    assert api.remove_project(garten, False) == {"ok": True, "reason": "", "own": []}
    assert not api.is_project(garten)


def test_settings_of_its_own_need_consent(tree):
    api = ScopeApi(str(tree["projects"]))
    garten = tree["projects"] / "Garten"
    api.create_project(str(garten))
    (garten / ".MyOS" / "Tags.md").write_text("# Tags\nx\n")

    assert api.remove_project(str(garten), False) == {"ok": False, "reason": "own", "own": ["Tags.md"]}
    assert api.is_project(str(garten))
    assert api.remove_project(str(garten), True)["ok"]
    assert not api.is_project(str(garten))


def test_only_who_may_change_its_rights_may_unmake_a_project_with_own_acls(tree, monkeypatch):
    garten = tree["projects"] / "Garten"
    ScopeApi(str(tree["projects"])).create_project(str(garten))
    (garten / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
        "# Users\nOliver: Admin\nAnna: Gast\n")

    monkeypatch.setenv("MYOS_ACL_USER", "anna")
    assert ScopeApi(str(tree["projects"])).remove_project(str(garten), True)["reason"] == "permission"
    assert (garten / ".MyOS" / "Project.md").exists()
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    assert ScopeApi(str(tree["projects"])).remove_project(str(garten), True)["ok"]


def test_listed_projects_carry_their_colour(tree):
    api = ScopeApi(str(tree["projects"]))
    garten = tree["projects"] / "Garten"
    api.create_project(str(garten))
    (garten / ".MyOS" / "Color.md").write_text("# Color\n#4ea35a\n")

    entries = {e["name"]: e for e in api.list_entries(str(tree["projects"]))}

    assert entries["Garten"]["projectColor"].lower() == "#4ea35a"
    assert "projectColor" not in entries["notiz.md"]
