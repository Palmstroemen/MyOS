"""Moving what carries a former name over to the current one (core/name_migration.py)."""

import os

import pytest

from core import brand
from core.name_migration import migrate_config, migrate_tree

OLD = ".OldName"


@pytest.fixture(autouse=True)
def former_names(monkeypatch):
    monkeypatch.setattr(brand, "LEGACY_META_DIRS", (OLD,))
    monkeypatch.setattr(brand, "LEGACY_CONFIG_DIRS", ("OldName",))
    monkeypatch.setattr(brand, "LEGACY_XATTR_PREFIXES", ("user.oldname.",))


def _project(root, acls=f"# Permissions\n\n## Admin\n- /*: read\n- /{OLD}/ACLs.md: read, write, change\n"):
    (root / OLD).mkdir(parents=True)
    (root / OLD / "Project.md").write_text("color: #123456\n", encoding="utf-8")
    (root / OLD / "ACLs.md").write_text(acls, encoding="utf-8")
    return root


def test_without_apply_nothing_changes(tmp_path):
    root = _project(tmp_path / "Haus")
    report = migrate_tree(root)
    assert (root / OLD).is_dir() and not brand.meta_dir(root).exists()
    assert [s.kind for s in report] == ["rewrite", "rename"]
    assert f"/{OLD}/ACLs.md" in (root / OLD / "ACLs.md").read_text(encoding="utf-8")


def test_apply_renames_the_folder_and_rewrites_its_rules(tmp_path):
    root = _project(tmp_path / "Haus")
    migrate_tree(root, apply=True)
    assert not (root / OLD).exists()
    acls = (brand.meta_dir(root) / "ACLs.md").read_text(encoding="utf-8")
    assert f"- /{brand.META_DIR}/ACLs.md: read, write, change" in acls and OLD not in acls
    assert (brand.meta_dir(root) / "Project.md").read_text(encoding="utf-8") == "color: #123456\n"


def test_nested_folders_in_templates_and_subprojects(tmp_path):
    root = _project(tmp_path / "Firma")
    template = root / OLD / "Templates" / "Standard" / "04_Finanz"
    (template / OLD).mkdir(parents=True)
    (template / OLD / "Desk.md").write_text("wallpaper: icons/euro.svg\n", encoding="utf-8")
    sub = _project(root / "Projekte" / "Bau")
    migrate_tree(root, apply=True)
    meta = brand.META_DIR
    assert (root / meta / "Templates" / "Standard" / "04_Finanz" / meta / "Desk.md").is_file()
    assert (sub / meta / "ACLs.md").is_file()
    assert not list(root.rglob(OLD))


def test_only_settings_files_are_rewritten_not_documents(tmp_path):
    root = _project(tmp_path / "Haus")
    note = root / "Notiz.md"
    note.write_text(f"Die Rechte stehen in {OLD}/ACLs.md.\n", encoding="utf-8")
    migrate_tree(root, apply=True)
    assert note.read_text(encoding="utf-8") == f"Die Rechte stehen in {OLD}/ACLs.md.\n"


def test_history_of_the_rules_is_rewritten_too(tmp_path):
    root = _project(tmp_path / "Haus")
    history = root / OLD / "ACLs-history"
    history.mkdir()
    (history / "ACLs-2026-10-21.md").write_text(f"- /{OLD}/ACLs.md: change\n", encoding="utf-8")
    migrate_tree(root, apply=True)
    text = (brand.meta_dir(root) / "ACLs-history" / "ACLs-2026-10-21.md").read_text(encoding="utf-8")
    assert text == f"- /{brand.META_DIR}/ACLs.md: change\n"


def test_names_merely_starting_alike_stay(tmp_path):
    root = _project(tmp_path / "Haus", acls=f"- /{OLD}x/a.md: read\n- /a{OLD}/b.md: read\n")
    migrate_tree(root, apply=True)
    assert (brand.meta_dir(root) / "ACLs.md").read_text(encoding="utf-8") == f"- /{OLD}x/a.md: read\n- /a{OLD}/b.md: read\n"


def test_a_folder_already_under_the_new_name_is_a_conflict(tmp_path):
    root = _project(tmp_path / "Haus")
    brand.meta_dir(root).mkdir()
    report = migrate_tree(root, apply=True)
    assert [s.kind for s in report if s.path == root / OLD] == ["conflict"]
    assert (root / OLD / "ACLs.md").is_file()  # untouched
    assert f"/{OLD}/ACLs.md" in (root / OLD / "ACLs.md").read_text(encoding="utf-8")


def test_symlinks_are_not_followed(tmp_path):
    outside = _project(tmp_path / "Fremd")
    root = tmp_path / "Haus"
    root.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    migrate_tree(root, apply=True)
    assert (outside / OLD).is_dir()


@pytest.mark.skipif(not hasattr(os, "setxattr"), reason="no xattr")
def test_tags_in_extended_attributes_move_to_the_new_key(tmp_path):
    root = _project(tmp_path / "Haus")
    doc = root / "Rechnung.pdf"
    doc.write_bytes(b"%PDF")
    try:
        os.setxattr(doc, "user.oldname.tags", b"bezahlt")
    except OSError:
        pytest.skip("file system without user xattrs")
    migrate_tree(root, apply=True)
    assert os.getxattr(doc, brand.XATTR_PREFIX + "tags") == b"bezahlt"
    assert "user.oldname.tags" not in os.listxattr(doc)


def test_config_moves_with_its_settings_file(tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    old = tmp_path / "OldName"
    old.mkdir()
    (old / "OldName.conf").write_text("[Scope]\nlast = /p/.OldName/Desk.md\n", encoding="utf-8")
    (old / "Identity.md").write_text("Names: Oliver\n", encoding="utf-8")
    assert [s.kind for s in migrate_config(env=env)] == ["rewrite", "rename", "rename"]
    assert old.is_dir()  # nothing yet
    migrate_config(env=env, apply=True)
    new = brand.config_dir(env)
    assert not old.exists() and (new / "Identity.md").read_text(encoding="utf-8") == "Names: Oliver\n"
    conf = (new / f"{brand.CONFIG_DIR}.conf").read_text(encoding="utf-8")
    assert conf == f"[Scope]\nlast = /p/{brand.META_DIR}/Desk.md\n"


def test_config_under_both_names_is_a_conflict(tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    (tmp_path / "OldName").mkdir()
    brand.config_dir(env).mkdir()
    assert [s.kind for s in migrate_config(env=env, apply=True)] == ["conflict"]
    assert (tmp_path / "OldName").is_dir()


def test_nothing_to_do(tmp_path):
    assert migrate_tree(tmp_path) == [] and migrate_config(env={"XDG_CONFIG_HOME": str(tmp_path)}) == []


def test_mounted_drives_are_left_alone(tmp_path, monkeypatch):
    root = _project(tmp_path / "Haus")
    drive = _project(root / "Perspektiven" / "Sicht")
    mount = root / "Perspektiven"
    import core.name_migration as nm
    monkeypatch.setattr(nm.os.path, "ismount", lambda p: os.fspath(p) == os.fspath(mount))
    steps = migrate_tree(root, apply=True)
    assert (drive / OLD).is_dir() and brand.meta_dir(root).is_dir()
    assert all(mount not in s.path.parents for s in steps)
