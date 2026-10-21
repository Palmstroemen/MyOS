"""PostFix ACL sidebar: who may access the open note (left = set by the system)."""

import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PostFix import window_acls as wa

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, execute\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "## Buchhaltung\n- /finanz/: read, write\n- /finanz/geheim/: none\n\n"
    "# Users\nOliver: Admin\nBertha: Buchhaltung\n"
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_USER"):
        monkeypatch.delenv(key, raising=False)


def _project(tmp_path: Path, acls: str = ACLS) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    if acls is not None:
        (root / ".MyOS" / "ACLs.md").write_text(acls)
    (root / "finanz" / "geheim").mkdir(parents=True)
    return root


def test_principals_of_a_note_roles_then_users_with_ordered_rights(tmp_path):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("# Plan\n")

    principals = wa.acl_principals_for_document(note)

    assert [(p["kind"], p["name"]) for p in principals] == [
        ("role", "Admin"), ("role", "Buchhaltung"), ("user", "Bertha"), ("user", "Oliver")]
    assert principals[1]["rights"] == ["read", "write"]
    assert principals[0]["rights"] == ["read", "write", "execute"]


def test_locked_folder_and_no_acls_and_no_file(tmp_path):
    root = _project(tmp_path)
    secret = root / "finanz" / "geheim" / "x.md"
    secret.write_text("x")

    assert [p["name"] for p in wa.acl_principals_for_document(secret)] == ["Admin", "Oliver"]
    assert wa.acl_principals_for_document(None) == []
    assert wa.acl_principals_for_document(tmp_path / "loose.md") == []


def test_enforced_viewer_without_read_on_acls_sees_nothing(tmp_path, monkeypatch):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    monkeypatch.setenv("MYOS_ACL_MODE", "enforce")

    monkeypatch.setenv("MYOS_ACL_USER", "bertha")
    assert wa.acl_principals_for_document(note) == []
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    assert wa.acl_principals_for_document(note) != []


class _Sidebar:
    def __init__(self):
        self.principals = None

    def set_principals(self, principals):
        self.principals = list(principals)

    def set_editable(self, editable):
        self.editable = editable

    def preferred_width(self):
        return 130


class _Host:
    def __init__(self):
        self.visible = None
        self.width = None

    def setVisible(self, visible):
        self.visible = visible

    def setFixedWidth(self, width):
        self.width = width


class _Editor:
    current_path = None


class _Window(wa.WindowAclsMixin):
    def __init__(self):
        self.left_sidebar = _Sidebar()
        self.acl_host = _Host()
        self.editor = _Editor()

    def tr(self, text):  # QObject.tr of the real window
        return text


def test_reload_shows_sidebar_only_with_acls(tmp_path):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    w = _Window()

    w.editor.current_path = note
    w._reload_acl_context()
    assert w.acl_host.visible is True and w.acl_host.width == 130
    assert len(w.left_sidebar.principals) == 4

    w.editor.current_path = tmp_path / "loose.md"
    w._reload_acl_context()
    assert w.acl_host.visible is False and w.acl_host.width == 0
    assert w.left_sidebar.principals == []


def test_acl_sidebar_builds_one_chip_per_principal():
    from PySide6.QtWidgets import QApplication, QPushButton
    from PostFix.ui_panels import ACLSidebar

    app = QApplication.instance() or QApplication([])
    sidebar = ACLSidebar()
    sidebar.set_principals([
        {"name": "Buchhaltung", "kind": "role", "rights": ["read", "write"]},
        {"name": "Bertha", "kind": "user", "rights": ["read", "write"]},
    ])
    app.processEvents()

    chips = [b for b in sidebar.findChildren(QPushButton) if b.isVisibleTo(sidebar)]
    assert [c.property("aclName") for c in chips] == ["Buchhaltung", "Bertha"]
    assert "#b5b5b5" in chips[0].styleSheet() and "#d6d6d6" in chips[1].styleSheet()
    assert "Read" in chips[1].toolTip()
    assert sidebar.preferred_width() > 0


def test_acl_chip_shows_rights_as_arrows():
    from PySide6.QtWidgets import QApplication
    from PostFix.ui_panels import ACLSidebar

    QApplication.instance() or QApplication([])
    sidebar = ACLSidebar()
    chip = sidebar._chip_text

    # read: arrow out of the document (left of the name); write: arrow into it (right).
    assert chip({"name": "Tom", "rights": ["read"]}) == ("", "◂", "Tom", "")
    assert chip({"name": "Lisa", "rights": ["read", "write"]}) == ("", "◂", "Lisa", "▸")
    assert chip({"name": "Bot", "rights": ["write"]}) == ("", "", "Bot", "▸")
    # execute stays "x", change stays "c" (left, on the system side).
    assert chip({"name": "Admin", "rights": ["read", "write", "execute", "change"]}) == ("x c", "◂", "Admin", "▸")


def test_acl_chip_arrows_are_equally_far_from_the_name():
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton
    from PostFix.ui_panels import ACLSidebar

    app = QApplication.instance() or QApplication([])
    sidebar = ACLSidebar()
    sidebar.set_principals([{"name": "Admin", "kind": "role", "rights": ["read", "write"]}])
    sidebar.resize(200, 200)
    sidebar.show()
    app.processEvents()

    chip = [b for b in sidebar.findChildren(QPushButton) if b.isVisibleTo(sidebar)][0]
    labels = {l.text(): l for l in chip.findChildren(QLabel)}
    read, name, write = labels["◂"], labels["Admin"], labels["▸"]
    name_left = name.x() + name.width() - name.fontMetrics().horizontalAdvance("Admin")
    gap_left = name_left - (read.x() + read.width())
    gap_right = write.x() - (name.x() + name.width())
    assert abs(gap_left - gap_right) <= 1  # label widths round to whole pixels


def test_acl_chip_shows_delete_as_d():
    from PySide6.QtWidgets import QApplication
    from PostFix.ui_panels import ACLSidebar

    QApplication.instance() or QApplication([])
    assert ACLSidebar()._chip_text({"name": "A", "rights": ["read", "execute", "delete"]}) == ("x d", "◂", "A", "")


def test_principals_carry_their_key(tmp_path):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")

    keys = {p["name"]: p["key"] for p in wa.acl_principals_for_document(note)}

    assert keys["Buchhaltung"] == "buchhaltung" and keys["Bertha"] == "bertha"


def test_chips_are_editable_only_for_users_with_change(tmp_path, monkeypatch):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    w = _Window()
    w.editor.current_path = note

    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    w._reload_acl_context()
    assert w.left_sidebar.editable is True

    monkeypatch.setenv("MYOS_ACL_USER", "bertha")
    w._reload_acl_context()
    assert w.left_sidebar.editable is False


def test_apply_role_rights_writes_and_reloads(tmp_path, monkeypatch):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    w = _Window()
    w.editor.current_path = note
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    w._reload_acl_context()

    error = w._apply_role_rights("buchhaltung", {"read"})

    assert error == ""
    assert "- /finanz/plan.md: read\n" in (root / ".MyOS" / "ACLs.md").read_text()
    rights = {p["name"]: p["rights"] for p in w.left_sidebar.principals}
    assert rights["Buchhaltung"] == ["read"]

    assert w._apply_role_rights("buchhaltung", None) == ""  # back to inherited
    assert "plan.md" not in (root / ".MyOS" / "ACLs.md").read_text()


def test_apply_without_permission_reports_and_changes_nothing(tmp_path, monkeypatch):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    w = _Window()
    w.editor.current_path = note
    monkeypatch.setenv("MYOS_ACL_USER", "bertha")

    error = w._apply_role_rights("buchhaltung", {"read"})

    assert error
    assert (root / ".MyOS" / "ACLs.md").read_text() == ACLS


def test_role_editor_shows_rights_and_returns_the_choice():
    from PySide6.QtWidgets import QApplication
    from PostFix.ui_panels import ACLRoleEditor

    QApplication.instance() or QApplication([])
    editor = ACLRoleEditor("Buchhaltung", ["read", "write"], own_rule=False)

    assert editor.chosen_rights() == {"read", "write"}
    assert editor.reset_button.isEnabled() is False  # inherited only: nothing to reset
    editor.toggle("write")
    editor.toggle("delete")
    assert editor.chosen_rights() == {"read", "delete"}
    assert ACLRoleEditor("X", [], own_rule=True).reset_button.isEnabled() is True


def test_role_editor_says_in_words_what_is_allowed():
    from PySide6.QtWidgets import QApplication
    from PostFix.ui_panels import ACLRoleEditor

    QApplication.instance() or QApplication([])
    editor = ACLRoleEditor("Buchhaltung", ["read"], own_rule=False)

    # Source strings are English; the German UI comes from postfix_de.qm.
    assert editor.meaning["read"].text() == "✓ may read"
    assert editor.meaning["write"].text() == "✗ may not write"
    editor.toggle("write")
    assert editor.meaning["write"].text() == "✓ may write"
    assert "what this group may do with this note" in editor.intro.text()
    assert "inherited" in editor.origin.text()


def test_person_chips_are_editable_too():
    from PySide6.QtWidgets import QApplication, QPushButton
    from PostFix.ui_panels import ACLSidebar

    QApplication.instance() or QApplication([])
    sidebar = ACLSidebar()
    sidebar.set_principals([{"name": "Bertha", "kind": "user", "key": "bertha", "rights": ["read"]}])
    asked = []
    sidebar.personEditRequested.connect(lambda key, name, chip: asked.append((key, name)))

    [chip] = [b for b in sidebar.findChildren(QPushButton) if b.property("aclName") == "Bertha"]
    chip.click()
    assert asked == []  # not editable: display only
    sidebar.set_editable(True)
    chip = [b for b in sidebar.findChildren(QPushButton) if b.property("aclName") == "Bertha"][-1]  # rebuilt
    chip.click()

    assert asked == [("bertha", "Bertha")]
    assert "groups" in chip.toolTip()


def test_apply_user_groups_writes_and_reloads(tmp_path, monkeypatch):
    root = _project(tmp_path)
    note = root / "finanz" / "plan.md"
    note.write_text("x")
    w = _Window()
    w.editor.current_path = note
    monkeypatch.setenv("MYOS_ACL_USER", "oliver")
    w._reload_acl_context()

    groups = {g["key"]: g for g in w._user_groups("bertha")["groups"]}
    assert groups["buchhaltung"]["member"] is True and groups["buchhaltung"]["rights"] == ["read", "write"]

    assert w._apply_user_groups("bertha", {"buchhaltung", "admin"}) == ""
    assert "Bertha: Buchhaltung, Admin\n" in (root / ".MyOS" / "ACLs.md").read_text()
    assert w._apply_user_groups("oliver", set()) == "You would lose your own right to change the rights."
    assert w._apply_user_groups("bertha", set()) == ""
    assert "Bertha" not in (root / ".MyOS" / "ACLs.md").read_text()
    assert "Bertha" not in [p["name"] for p in w.left_sidebar.principals]


def test_person_editor_shows_groups_and_returns_the_choice():
    from PySide6.QtWidgets import QApplication
    from PostFix.ui_panels import ACLPersonEditor

    QApplication.instance() or QApplication([])
    groups = [
        {"key": "admin", "name": "Admin", "member": False, "rights": ["read", "write", "execute"]},
        {"key": "buchhaltung", "name": "Buchhaltung", "member": True, "rights": []},
    ]
    editor = ACLPersonEditor("Bertha", groups)

    assert editor.chosen_groups() == {"buchhaltung"}
    assert editor.meaning["admin"].text() == "✗ not a member · here: read, write, execute"
    assert editor.meaning["buchhaltung"].text() == "✓ member · here: no access"
    assert "whole project" in editor.intro.text()
    assert editor.empty_note.isHidden()
    editor.toggle("buchhaltung")
    assert editor.chosen_groups() == set()
    assert not editor.empty_note.isHidden()
