"""Born template folders that hold nothing of the user turn back into embryos."""

from pathlib import Path

import pytest

from core.localBlueprintLayer import Blueprint


@pytest.fixture(autouse=True)
def _no_external_templates(monkeypatch):
    # Templates come from the project's own Templates/ folder in these tests.
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.delenv("MYOS_ROLES", raising=False)


def _project(tmp_path: Path) -> Path:
    """Standard template: 04_Finanz (.MyOS, Liesmich.md) with sub-embryos Ausgaben/2026 and Einnahmen."""
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    finanz = root / "Templates" / "Standard" / "04_Finanz"
    (finanz / ".MyOS").mkdir(parents=True)
    (finanz / ".MyOS" / "batch.svg").write_text("<svg/>")
    (finanz / "Liesmich.md").write_text("Finanzen")
    (finanz / "Ausgaben" / "2026").mkdir(parents=True)
    (finanz / "Einnahmen").mkdir(parents=True)
    return root


def _born(tmp_path: Path, rel: str = "04_Finanz"):
    root = _project(tmp_path)
    layer = Blueprint(root)
    layer._birth_path(f"/{rel}")
    return root, layer


def test_untouched_birth_turns_back_into_embryo(tmp_path):
    root, layer = _born(tmp_path)

    removed = layer.reabsorb_upwards("04_Finanz")

    assert removed == [root / "04_Finanz"]
    assert not (root / "04_Finanz").exists()
    assert layer.is_embryo("04_Finanz") is True


def test_folder_with_user_file_is_kept(tmp_path):
    root, layer = _born(tmp_path)
    (root / "04_Finanz" / "Rechnung.pdf").write_bytes(b"%PDF")

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert (root / "04_Finanz" / "Rechnung.pdf").is_file()
    assert layer.is_embryo("04_Finanz") is False


def test_modified_template_copy_is_user_content(tmp_path):
    root, layer = _born(tmp_path)
    (root / "04_Finanz" / "Liesmich.md").write_text("Finanzen, von mir ergänzt")

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert (root / "04_Finanz" / "Liesmich.md").read_text() == "Finanzen, von mir ergänzt"


def test_folder_tags_keep_the_folder(tmp_path):
    root, layer = _born(tmp_path)
    (root / "04_Finanz" / ".MyOS" / "myTags.md").write_text("#steuer\n")

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert (root / "04_Finanz" / ".MyOS" / "myTags.md").is_file()


def test_tag_cache_alone_does_not_keep_the_folder(tmp_path):
    root, layer = _born(tmp_path)
    (root / "04_Finanz" / ".TagsHere.json").write_text("{}")
    (root / "04_Finanz" / ".MyOS" / "empty_leftover").mkdir()

    assert layer.reabsorb_upwards("04_Finanz") == [root / "04_Finanz"]
    assert not (root / "04_Finanz").exists()


def test_user_folder_without_template_is_never_removed(tmp_path):
    root = _project(tmp_path)
    layer = Blueprint(root)
    (root / "Privat").mkdir()

    assert layer.reabsorb_upwards("Privat") == []
    assert (root / "Privat").is_dir()


def test_empty_user_subfolder_keeps_born_parent(tmp_path):
    root, layer = _born(tmp_path)
    (root / "04_Finanz" / "Eigenes").mkdir()

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert (root / "04_Finanz" / "Eigenes").is_dir()


def test_symlink_inside_keeps_the_folder(tmp_path):
    root, layer = _born(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("x")
    (root / "04_Finanz" / "link.txt").symlink_to(outside)

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert outside.read_text() == "x"
    assert (root / "04_Finanz" / "link.txt").is_symlink()


def test_reabsorb_cascades_upwards_through_unused_parents(tmp_path):
    root, layer = _born(tmp_path, "04_Finanz/Ausgaben")

    removed = layer.reabsorb_upwards("04_Finanz/Ausgaben")

    assert removed == [root / "04_Finanz" / "Ausgaben", root / "04_Finanz"]
    assert layer.is_embryo("04_Finanz/Ausgaben") is True
    assert layer.is_embryo("04_Finanz") is True


def test_cascade_stops_at_parent_with_user_content(tmp_path):
    root, layer = _born(tmp_path, "04_Finanz/Ausgaben")
    (root / "04_Finanz" / "Notiz.md").write_text("bleibt")

    removed = layer.reabsorb_upwards("04_Finanz/Ausgaben")

    assert removed == [root / "04_Finanz" / "Ausgaben"]
    assert (root / "04_Finanz" / "Notiz.md").is_file()


def test_project_root_is_never_removed(tmp_path):
    root = _project(tmp_path)
    layer = Blueprint(root)

    assert layer.reabsorb_upwards("") == []
    assert root.is_dir()


def test_folder_hidden_from_user_by_acl_is_kept(tmp_path, monkeypatch):
    root, layer = _born(tmp_path)
    monkeypatch.setattr(layer, "_can_write_embryo", lambda rel_path: False)

    assert layer.reabsorb_upwards("04_Finanz") == []
    assert (root / "04_Finanz").is_dir()


def test_reabsorb_all_tidies_the_whole_project_bottom_up(tmp_path):
    root, layer = _born(tmp_path, "04_Finanz/Ausgaben/2026")
    layer._birth_path("/04_Finanz/Einnahmen")
    (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").write_bytes(b"%PDF")

    removed = layer.reabsorb_all()

    assert set(removed) == {root / "04_Finanz" / "Ausgaben" / "2026", root / "04_Finanz" / "Ausgaben"}
    assert (root / "04_Finanz" / "Einnahmen" / "Beleg.pdf").is_file()
    assert layer.is_embryo("04_Finanz/Ausgaben") is True


def test_sub_project_is_not_reabsorbed_with_parent_templates(tmp_path):
    """A sub-project named like a template folder belongs to its own project context."""
    root = _project(tmp_path)
    layer = Blueprint(root)
    sub = root / "04_Finanz"
    (sub / ".MyOS").mkdir(parents=True)
    (sub / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (sub / "Ausgaben").mkdir()

    assert layer.reabsorb_all() == []
    assert (sub / "Ausgaben").is_dir()
