"""ACLs of a whole project tree, for myacl and adapters that copy them elsewhere (a cloud):
where a role's rights at a path come from (ACLView.origin), and every rule with the
"## Folder" rules resolved into the subprojects (ACLPolicy.for_tree)."""

from pathlib import Path

import pytest

from core.acl import ACLPolicy
from core.acl_view import ACLView
from core.brand import META_DIR, env_name


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)


ACLS = (
    "# Permissions\n\n"
    "## Folder\n- /{Folder}/: read, write\n- /Info/: read\n\n"
    f"## Admin\n- /*: read, write\n- /{META_DIR}/ACLs.md: read, write, change\n\n"
    "## Buchhaltung\n- /Finanz/: read, write, delete\n- /Finanz/Archiv/: read\n\n"
    "# Users\nOliver: Admin\nAnna: Buchhaltung\n"
)


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True)
    (path / META_DIR / "Project.md").write_text("# MyOS Project\n")
    (path / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("Finanz", "Info"):
        (path / folder).mkdir()
    return path


def _setup(tmp_path: Path) -> tuple:
    root = _project(tmp_path / "Projekte")
    for folder in ("Finanz", "Info"):
        (root / META_DIR / "Templates" / "Standard" / folder).mkdir(parents=True)
    (root / "Finanz" / "Archiv").mkdir()
    family = _project(root / "Familie")
    (root / META_DIR / "ACLs.md").write_text(ACLS)
    return root, family


def test_origin_is_the_folder_of_the_rule_that_decides(tmp_path):
    root, _family = _setup(tmp_path)
    view = ACLView.for_path(root)

    assert view.origin("buchhaltung", root / "Finanz" / "2026") == "/Finanz"
    assert view.origin("buchhaltung", root / "Finanz" / "Archiv" / "alt.pdf") == "/Finanz/Archiv"
    assert view.origin("admin", root / "Finanz") == "/"
    assert view.origin("buchhaltung", root / "Info") is None


def test_origin_in_a_subproject_is_the_resolved_folder_rule(tmp_path):
    _root, family = _setup(tmp_path)

    assert ACLView.for_path(family / "Finanz").origin("finanz", family / "Finanz") == "/Familie/Finanz"


def test_the_tree_holds_the_folder_rules_of_every_subproject(tmp_path):
    root, _family = _setup(tmp_path)
    (root / "Familie" / "Kinder").mkdir()
    _project(root / "Familie" / "Kinder" / "Schule")

    rules = {rule.path: rule.rights for rule in ACLPolicy.for_tree(root).permissions["finanz"]}

    assert rules["/Finanz"] == {"read", "write"}
    assert rules["/Familie/Finanz"] == {"read", "write"}
    assert rules["/Familie/Kinder/Schule/Finanz"] == {"read", "write"}
    assert rules["/Familie/Kinder/Schule/Info"] == {"read"}


def test_the_tree_lists_each_rule_once(tmp_path):
    root, family = _setup(tmp_path)
    _project(family / "Urlaub")

    paths = [rule.path for rule in ACLPolicy.for_tree(root).permissions["finanz"]]

    assert len(paths) == len(set(paths))


def test_a_subproject_with_its_own_acls_is_not_part_of_the_tree(tmp_path):
    root, family = _setup(tmp_path)
    (family / META_DIR / "ACLs.md").write_text("# Permissions\n\n## Familie\n- /*: read\n")

    paths = {rule.path for rules in ACLPolicy.for_tree(root).permissions.values() for rule in rules}

    assert not any(path.startswith("/Familie") for path in paths)
