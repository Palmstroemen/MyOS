"""ACLView: side-effect-free ACL answers for display (Scope, PostFix).

ACLs.md paths are relative to the project root; the view takes absolute filesystem
paths as the GUI has them and maps them into the project.
"""

from pathlib import Path

import pytest

from core.acl_view import ACLView


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


def _project(tmp_path: Path, acls: str = None) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("finanz", "info", "work"):
        (root / "Templates" / "Standard" / folder).mkdir(parents=True)
    if acls is not None:
        (root / ".MyOS" / "ACLs.md").write_text(acls)
    return root


ACLS = (
    "# Permissions\n"
    "\n"
    "## Folder\n"
    "- /{Folder}/: read, write\n"
    "- /info/: read\n"
    "\n"
    "## Admin\n"
    "- /*: read, write, execute\n"
    "- /.MyOS/ACLs.md: change\n"
    "\n"
    "## Buchhalter\n"
    "- /finanz/: read, write, execute\n"
    "- /rechtliches/: read\n"
    "\n"
    "## Entwickler\n"
    "- /finanz/eingang/: read, write\n"
    "- /work/scrum/: read, write, execute\n"
    "\n"
    "# Users\n"
    "Anna: Admin\n"
    "Karl: Entwickler, Buchhalter\n"
    "Mia: Entwickler\n"
)


def test_no_acls_file_means_no_view(tmp_path):
    assert ACLView.for_path(_project(tmp_path) / "finanz") is None


def test_user_rights_at_absolute_paths(tmp_path):
    root = _project(tmp_path, ACLS)
    view = ACLView.for_path(root)

    assert view.rights_for_user("karl", root / "finanz") == {"read", "write", "execute"}
    assert view.rights_for_user("karl", root / "finanz" / "2026" / "beleg.pdf") == {"read", "write", "execute"}
    assert view.rights_for_user("Karl", root / "rechtliches") == {"read"}
    assert view.rights_for_user("mia", root / "finanz") == set()
    assert view.rights_for_user("mia", root / "finanz" / "eingang") == {"read", "write"}
    assert view.rights_for_user("anna", root / "work") == {"read", "write", "execute"}
    assert view.rights_for_user("nobody", root / "info") == set()


def test_paths_outside_the_project_have_no_rights(tmp_path):
    root = _project(tmp_path, ACLS)
    view = ACLView.for_path(root)

    assert view.rights_for_user("anna", tmp_path / "elsewhere") == set()
    assert view.relative_path(tmp_path / "elsewhere") is None
    assert view.relative_path(root) == "/"
    assert view.relative_path(root / "finanz" / "eingang") == "/finanz/eingang"


def test_principals_list_roles_and_users_with_their_rights(tmp_path):
    root = _project(tmp_path, ACLS)
    view = ACLView.for_path(root)

    roles = {p.name: p.rights for p in view.principals(root / "finanz") if p.kind == "role"}
    users = {p.name: p.rights for p in view.principals(root / "finanz") if p.kind == "user"}

    # Names as written in ACLs.md / on disk; keys stay lower-case for lookups.
    assert roles == {
        "Admin": {"read", "write", "execute"},
        "Buchhalter": {"read", "write", "execute"},
        "finanz": {"read", "write"},
    }
    assert users == {"Anna": {"read", "write", "execute"}, "Karl": {"read", "write", "execute"}}
    assert {p.key for p in view.principals(root / "finanz") if p.kind == "user"} == {"anna", "karl"}


def test_own_rules_versus_inherited(tmp_path):
    root = _project(tmp_path, ACLS)
    view = ACLView.for_path(root)

    assert view.has_own_rules(root / "finanz") is True
    assert view.has_own_rules(root / "finanz" / "eingang") is True
    assert view.has_own_rules(root / "finanz" / "2026") is False
    # The admin's "/*" applies everywhere but is nobody's own rule for a folder.
    assert view.has_own_rules(root / "work") is True  # /{Folder}/ -> /work/
    assert view.has_own_rules(root / "work" / "notes") is False


def test_for_path_finds_the_project_from_any_depth(tmp_path):
    root = _project(tmp_path, ACLS)
    deep = root / "finanz" / "2026"
    deep.mkdir(parents=True)

    view = ACLView.for_path(deep)

    assert view is not None
    assert view.project_root == root.resolve()


def test_locked_out_role_is_not_listed_and_folder_has_own_rules(tmp_path):
    root = _project(tmp_path, ACLS.replace(
        "- /rechtliches/: read\n",
        "- /rechtliches/: read\n- /finanz/geheim/: none\n",
    ))
    view = ACLView.for_path(root)
    geheim = root / "finanz" / "geheim"

    names = {p.name for p in view.principals(geheim)}

    assert "Buchhalter" not in names
    assert "Karl" not in names  # his other role (Entwickler) has no rule here either
    assert "Admin" in names and "Anna" in names
    assert view.rights_for_user("karl", geheim) == set()
    assert view.has_own_rules(geheim) is True
