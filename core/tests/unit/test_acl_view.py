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


def _summary(view, folder):
    entries = sorted(str(p) for p in folder.iterdir())
    return view.listing_summary(folder, entries)


def test_listing_summary_folder_principals_and_exceptions(tmp_path):
    root = _project(tmp_path, ACLS)
    for name in ("finanz", "info", "work"):
        (root / name).mkdir()
    view = ACLView.for_path(root)

    summary = _summary(view, root)
    sections = {p["id"]: p["section"] for p in summary["principals"]}

    # Only the admin's "/*" covers the project root itself.
    assert {i for i, s in sections.items() if s == "folder"} == {"role:admin", "user:anna"}
    # Who has rights on some entries only is listed below, as an exception.
    assert sections["role:buchhalter"] == "exception"
    assert sections["user:karl"] == "exception"
    assert sections["role:finanz"] == "exception"
    assert "user:mia" not in sections  # Entwickler rules are all deeper than this listing


def test_listing_summary_access_per_entry(tmp_path):
    root = _project(tmp_path, ACLS)
    for name in ("finanz", "info", "work"):
        (root / name).mkdir()
    view = ACLView.for_path(root)

    access = _summary(view, root)["access"]

    assert set(access[str(root / "finanz")]) == {
        "role:admin", "role:buchhalter", "role:finanz", "user:anna", "user:karl"}
    assert "user:karl" not in access[str(root / "info")]
    assert "role:info" in access[str(root / "info")]


def test_listing_summary_rights_order_names_and_partial(tmp_path):
    root = _project(tmp_path, ACLS.replace(
        "- /rechtliches/: read\n",
        "- /rechtliches/: read\n- /finanz/geheim/: none\n",
    ))
    (root / "finanz" / "geheim").mkdir(parents=True)
    (root / "finanz" / "eingang").mkdir()
    view = ACLView.for_path(root)

    principals = {p["id"]: p for p in _summary(view, root / "finanz")["principals"]}

    buchhalter = principals["role:buchhalter"]
    assert buchhalter["name"] == "Buchhalter" and buchhalter["kind"] == "role"
    assert buchhalter["rights"] == ["read", "write", "execute"]
    # Locked out of "geheim": the filter would hide an entry, the chip says so.
    assert buchhalter["partial"] is True
    assert principals["role:admin"]["partial"] is False
    # Mia gets in only through Entwickler's rule on "eingang".
    assert principals["user:mia"]["section"] == "exception"
    assert principals["user:mia"]["count"] == 1


def test_listing_summary_without_entries_lists_folder_principals(tmp_path):
    root = _project(tmp_path, ACLS)
    (root / "work").mkdir()
    view = ACLView.for_path(root)

    summary = view.listing_summary(root / "work", [])

    assert summary["access"] == {}
    assert all(p["section"] == "folder" and not p["partial"] for p in summary["principals"])
    assert "role:work" in {p["id"] for p in summary["principals"]}


def test_listing_summary_accepts_unresolved_entry_paths(tmp_path):
    root = _project(tmp_path, ACLS)
    (root / "finanz").mkdir()
    view = ACLView.for_path(root)
    odd = str(root / "info" / ".." / "finanz")

    access = view.listing_summary(root, [odd])["access"]

    assert "role:buchhalter" in access[odd]


def _subproject(parent: Path, rel: str, acls: str = None) -> Path:
    sub = parent / rel
    (sub / ".MyOS").mkdir(parents=True)
    (sub / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    if acls is not None:
        (sub / ".MyOS" / "ACLs.md").write_text(acls)
    return sub


def test_subproject_without_acls_inherits_the_parent_rules(tmp_path):
    root = _project(tmp_path, ACLS)
    sub = _subproject(root, "finanz/Kunde")
    (sub / "rechnungen").mkdir()

    view = ACLView.for_path(sub / "rechnungen")

    assert view is not None
    assert view.project_root == root.resolve()
    assert view.relative_path(sub / "rechnungen") == "/finanz/Kunde/rechnungen"
    assert view.rights_for_user("karl", sub / "rechnungen") == {"read", "write", "execute"}
    assert view.rights_for_user("mia", sub) == set()


def test_subproject_with_own_acls_uses_them(tmp_path):
    root = _project(tmp_path, ACLS)
    sub = _subproject(root, "finanz/Kunde", "# Permissions\n\n## Kunde\n- /*: read\n\n# Users\nMia: Kunde\n")

    view = ACLView.for_path(sub)

    assert view.project_root == sub.resolve()
    assert view.rights_for_user("mia", sub) == {"read"}
    assert view.rights_for_user("karl", sub) == set()


def test_may_view_requires_read_on_acls_file_for_a_named_viewer(tmp_path):
    root = _project(tmp_path, ACLS.replace("- /.MyOS/ACLs.md: change\n", "- /.MyOS/ACLs.md: read, change\n"))
    view = ACLView.for_path(root)

    assert view.may_view(None) is True  # no enforcement: everybody sees the panel
    assert view.may_view("anna") is True  # Admin
    assert view.may_view("karl") is False
    assert view.may_view("nobody") is False
