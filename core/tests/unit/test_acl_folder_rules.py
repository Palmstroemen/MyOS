"""Template folder roles with a section of their own (ACL design document 2.4): the
"## Folder" rules are their inherited entries everywhere, the section holds explicit
entries. An explicit entry for the same folder replaces the inherited one there."""

from pathlib import Path

import pytest

from core.acl_edit import own_rule, set_role_rights
from core.acl_view import ACLView


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


BASE = (
    "# Permissions\n\n"
    "## Folder\n- /{Folder}/: read, write\n- /Info/: read\n\n"
    "## Admin\n- /*: read, write\n- /.MyOS/ACLs.md: read, write, change\n\n"
)
USERS = "# Users\nOliver: Admin\n"


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (path / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("Finanz", "Info"):
        (path / folder).mkdir()
    return path


def _setup(tmp_path: Path, section: str = "") -> tuple:
    root = _project(tmp_path / "Projekte")
    for folder in ("Finanz", "Info"):
        (root / "Templates" / "Standard" / folder).mkdir(parents=True)
    (root / "Finanz" / "Belege").mkdir()
    sub = _project(root / "Familie")
    (root / ".MyOS" / "ACLs.md").write_text(BASE + section + USERS)
    return root, sub


def _rights(path: Path, role: str = "finanz") -> set:
    return set(ACLView.for_path(path).rights_for_role(role, path))


def test_editing_a_folder_role_keeps_its_rights_in_subprojects(tmp_path):
    root, sub = _setup(tmp_path)

    set_role_rights(root / "Finanz" / "Belege", "Finanz", {"read"}, editor="oliver")

    assert _rights(root / "Finanz" / "Belege") == {"read"}
    assert _rights(root / "Finanz") == {"read", "write"}
    assert _rights(sub / "Finanz") == {"read", "write"}
    assert _rights(sub / "Info") == {"read"}


def test_the_section_holds_only_the_explicit_entry(tmp_path):
    root, _sub = _setup(tmp_path)

    set_role_rights(root / "Finanz" / "Belege", "Finanz", {"read"}, editor="oliver")

    text = (root / ".MyOS" / "ACLs.md").read_text()
    section = text[text.index("## Finanz"):text.index("# Users")]
    assert section == "## Finanz\n- /Finanz/Belege/: read\n\n"
    assert own_rule(root / "Finanz", "Finanz") is None  # inherited from "## Folder"


def test_an_explicit_entry_replaces_the_inherited_one_for_the_same_folder(tmp_path):
    root, sub = _setup(tmp_path, "## Finanz\n- /Finanz/: none\n- /Familie/Info/: none\n\n")

    assert _rights(root / "Finanz") == set()
    assert _rights(root / "Info") == {"read"}
    assert _rights(sub / "Finanz") == {"read", "write"}  # inherited, nothing explicit there
    assert _rights(sub / "Info") == set()


def test_explicit_entries_elsewhere_add_to_the_inherited_ones(tmp_path):
    root, sub = _setup(tmp_path, "## Finanz\n- /Archiv/: read\n\n")
    (root / "Archiv").mkdir()

    assert _rights(root / "Archiv") == {"read"}
    assert _rights(root / "Finanz") == {"read", "write"}
    assert _rights(sub / "Finanz") == {"read", "write"}


def test_back_to_inherited_at_the_template_folder(tmp_path):
    root, sub = _setup(tmp_path)

    set_role_rights(root / "Finanz", "Finanz", {"read"}, editor="oliver")
    assert _rights(root / "Finanz") == {"read"}
    assert own_rule(root / "Finanz", "Finanz") == {"read"}

    set_role_rights(root / "Finanz", "Finanz", None, editor="oliver")
    assert _rights(root / "Finanz") == {"read", "write"}
    assert _rights(sub / "Finanz") == {"read", "write"}
