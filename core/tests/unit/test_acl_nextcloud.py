"""Planning a project's ACLs as Nextcloud Team folder rules ("advanced permissions").

Rules are set per person (Nextcloud account), each one fixing every permission bit, so the
nearest rule wins as in MyOS. Nextcloud needs read on every parent folder: who has rights
only deep down gets read on the way there, and the other entries on the way are locked."""

from pathlib import Path

import pytest

from core.acl import ACLPolicy
from core.acl_nextcloud import local_tree, plan, read_nextcloud_md

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, change\n\n"
    "## Familie\n- /Familie/: read, write\n- /Familie/Finanz/: read\n\n"
    "## Kinder\n- /Familie/Kind/: read, write\n\n"
    "## Buchhaltung\n- /Familie/Finanz/: read, write, delete\n\n"
    "## Team\n- /Job/**: read, write\n- /Job/*.pdf: read\n- /Neu/: read\n\n"
    "# Users\nOliver: Admin\nLisa: Familie\nTom: Kinder\nAnna: Buchhaltung, Team\nMia: Familie\nPaul: Gast\n"
)
ACCOUNTS = {"oliver": "oliver", "lisa": "lisa", "tom": "tom", "anna": "anna", "paul": "paul"}


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "Projekte"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    for folder in ("Familie/Finanz/2026", "Familie/Fotos", "Familie/Kind/Schule", "Job"):
        (root / folder).mkdir(parents=True)
    (root / "Familie" / "Notiz.md").write_text("x")
    return root


def _rules(root, accounts=ACCOUNTS, base_groups=()):
    exists, children = local_tree(root)
    result = plan(ACLPolicy.for_tree(root), accounts, exists, children, base_groups=base_groups)
    return {(r.kind, r.account, r.path): set(r.allowed) for r in result.rules}, result.notes


def _of(rules, account):
    return {path: allowed for (kind, who, path), allowed in rules.items() if kind == "user" and who == account}


def _effective(person_rules, path):
    """What Nextcloud applies at path: the nearest rule above it (every bit fixed)."""
    while path not in person_rules:
        path = path.rsplit("/", 1)[0] or "/"
    return person_rules[path]


def test_everyone_gets_a_rule_at_the_root(project):
    rules, _notes = _rules(project)

    assert _of(rules, "oliver")["/"] == {"read", "write", "create"}
    assert _of(rules, "lisa")["/"] == {"read"}  # on the way to /Familie
    assert _of(rules, "paul") == {"/": set()}  # no rights: the folder's own permissions must not apply


def test_rules_only_where_the_rights_change(project):
    lisa = _of(_rules(project)[0], "lisa")

    assert lisa["/Familie"] == {"read", "write", "create"}
    assert lisa["/Familie/Finanz"] == {"read"}
    assert lisa["/Job"] == set() and lisa["/.MyOS"] == set()
    assert set(lisa) == {"/", "/.MyOS", "/Job", "/Familie", "/Familie/Finanz"}


def test_rights_deep_down_need_read_on_the_way_and_lock_the_rest(project):
    tom = _of(_rules(project)[0], "tom")

    assert tom["/"] == {"read"}
    assert _effective(tom, "/Familie") == {"read"}
    assert tom["/Job"] == set()
    assert tom["/.MyOS"] == set()
    assert tom["/Familie/Finanz"] == set()
    assert tom["/Familie/Fotos"] == set()
    assert tom["/Familie/Notiz.md"] == set()
    assert tom["/Familie/Kind"] == {"read", "write", "create"}
    assert "/Familie/Kind/Schule" not in tom and _effective(tom, "/Familie/Kind/Schule") == {"read", "write", "create"}


def test_the_rights_of_a_persons_roles_add_up(project):
    anna = _of(_rules(project)[0], "anna")

    assert anna["/Familie/Finanz"] == {"read", "write", "create", "delete"}
    assert anna["/Job"] == {"read", "write", "create"}
    assert _effective(anna, "/Familie") == {"read"}  # only on the way to Finanz
    assert anna["/Familie/Fotos"] == set()


def test_people_without_an_account_get_no_rules_and_a_note(project):
    rules, notes = _rules(project)

    assert not _of(rules, "mia")
    assert any("Mia" in note and "account" in note for note in notes)


def test_rules_that_cannot_be_mapped_are_left_out_with_a_note(project):
    rules, notes = _rules(project)

    assert any("/Job/*.pdf" in note for note in notes)
    assert any("/Neu" in note and "not there" in note for note in notes)
    assert "/Neu" not in _of(rules, "anna")
    assert any("change" in note for note in notes)


def test_the_base_group_is_locked_out_at_the_root(project):
    rules, _notes = _rules(project, base_groups=["Projekte", "Team"])

    assert rules[("group", "Projekte", "/")] == set() and rules[("group", "Team", "/")] == set()


def test_settings_and_accounts_are_read_from_nextcloud_md(tmp_path):
    md = tmp_path / "Nextcloud.md"
    md.write_text("# Nextcloud\nurl: https://cloud.example.org\ngroup: Projekte\n\n# Accounts\nAnna Huber: anna.h\nOliver: oliver\n")

    settings, accounts = read_nextcloud_md(md)

    assert settings == {"url": "https://cloud.example.org", "group": "Projekte"}
    assert accounts == {"anna huber": "anna.h", "oliver": "oliver"}


def _ways(root):
    exists, children = local_tree(root)
    result = plan(ACLPolicy.for_tree(root), ACCOUNTS, exists, children)
    return {(r.account, r.path) for r in result.rules if r.traverse}, {(r.account, r.path): r for r in result.rules}


def test_every_folder_on_the_way_has_a_marked_rule_of_its_own(project):
    ways, rules = _ways(project)

    # A server app locks what is created in such a folder later: it looks at the
    # folder's own rules only, so /Familie needs one although it inherits the same.
    assert ("tom", "/") in ways and ("tom", "/Familie") in ways
    assert rules[("tom", "/Familie")].allowed == {"read"}
    assert ("lisa", "/") in ways and ("anna", "/Familie") in ways
    assert ("tom", "/Familie/Kind") not in ways and ("oliver", "/") not in ways
    assert ("lisa", "/Familie") not in ways  # Lisa may read there by ACLs.md


def test_a_way_rule_leaves_share_to_be_inherited(project):
    from core.acl_nextcloud import TRAVERSE_MASK, mask_of

    _ways_, rules = _ways(project)

    assert TRAVERSE_MASK == 15
    assert mask_of(rules[("tom", "/Familie")]) == 15 and mask_of(rules[("tom", "/Familie/Kind")]) == 31


# --- the embryos: readable for everyone with rights in the project ---

EMBRYOS = ("/.MyOS/Embryos.json", "/.MyOS/Embryos")


def _with_embryos(root):
    (root / ".MyOS" / "Embryos.json").write_text("{}")
    (root / ".MyOS" / "Embryos" / "04_Finanz").mkdir(parents=True)
    (root / ".MyOS" / "Embryos" / "04_Finanz" / "Liesmich.md").write_text("x")
    return root


def _readable_rules(root, readable):
    exists, children = local_tree(root)
    result = plan(ACLPolicy.for_tree(root), ACCOUNTS, exists, children, readable=readable)
    return {(r.kind, r.account, r.path): set(r.allowed) for r in result.rules}, result.notes


def test_who_works_deep_down_may_read_the_embryos_but_nothing_else_in_myos(project):
    rules, _notes = _readable_rules(_with_embryos(project), EMBRYOS)
    tom = _of(rules, "tom")

    assert _effective(tom, "/.MyOS/Embryos.json") == {"read"}
    assert _effective(tom, "/.MyOS/Embryos/04_Finanz/Liesmich.md") == {"read"}
    assert _effective(tom, "/.MyOS") == {"read"}  # on the way
    assert _effective(tom, "/.MyOS/ACLs.md") == set()
    assert _effective(tom, "/.MyOS/Project.md") == set()


def test_reading_the_embryos_adds_no_write(project):
    rules, _notes = _readable_rules(_with_embryos(project), EMBRYOS)

    assert _effective(_of(rules, "lisa"), "/.MyOS/Embryos.json") == {"read"}
    assert _effective(_of(rules, "oliver"), "/.MyOS/Embryos.json") == {"read", "write", "create"}


def test_who_has_no_rights_in_the_project_does_not_see_the_embryos(project):
    rules, _notes = _readable_rules(_with_embryos(project), EMBRYOS)

    assert _effective(_of(rules, "paul"), "/.MyOS/Embryos.json") == set()


def test_embryos_not_there_yet_are_no_note(project):
    _rules_found, notes = _readable_rules(project, EMBRYOS)

    assert not any("Embryos" in note for note in notes)


def test_an_entry_on_the_way_gets_its_own_rule_even_when_it_reads_as_the_way(project):
    # The app locks what is new below a rule on the way; a rule of its own keeps its read.
    rules, _notes = _readable_rules(_with_embryos(project), EMBRYOS)
    tom = _of(rules, "tom")

    assert tom["/.MyOS/Embryos.json"] == {"read"}
    assert tom["/.MyOS/Embryos"] == {"read"}
