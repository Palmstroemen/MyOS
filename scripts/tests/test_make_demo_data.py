"""The data of the three-minute demo (scripts/make_demo_data.py): built fresh on every run,
an earlier demo rebuilt, anything else left alone."""

from pathlib import Path

import pytest
from core.brand import META_DIR

pytest.importorskip("reportlab")
pytest.importorskip("PIL")

from scripts import make_demo_data  # noqa: E402


@pytest.fixture
def templates(tmp_path):
    standard = tmp_path / "templates" / "Standard"
    for folder in ("00_Admin", "04_Finanz/Ausgaben", "04_Finanz/Einnahmen", "08_Dokumentation/Bilder"):
        (standard / folder).mkdir(parents=True)
    (standard / META_DIR).mkdir()
    (standard / META_DIR / "ACLs.md").write_text("# Permissions\n", encoding="utf-8")
    return tmp_path / "templates"


@pytest.fixture
def demo(tmp_path, templates, monkeypatch):
    monkeypatch.setattr(make_demo_data, "write_odt", lambda path, html: False)  # no LibreOffice run
    return make_demo_data.generate(tmp_path / "demo", templates)


def _is_project(folder: Path) -> bool:
    return (folder / META_DIR / "Project.md").is_file()


def test_the_scenes_find_what_they_need(demo):
    root = demo / "Projekte"
    assert _is_project(root)
    urlaub = root / "Urlaub 2025"
    assert not _is_project(urlaub) and len(list(urlaub.iterdir())) == 5  # scene 2 makes it one
    for name in ("Familie", "Job", "Auto"):
        assert _is_project(root / name)
        assert list((root / name / "04_Finanz").rglob("*.pdf")), name  # the lens has something to show
    assert _is_project(root / "Wohnen") and not (root / "Wohnen" / "04_Finanz").exists()  # scene 5 bears it
    assert len(list((demo / "Downloads").iterdir())) >= 30  # the mess of scene 1


def test_the_templates_lie_in_the_projects_root(demo):
    assert (demo / "Projekte" / META_DIR / "Templates" / "Standard" / "04_Finanz").is_dir()
    assert not (demo / "Templates").exists()


def test_the_demo_has_no_access_rights(demo):
    assert not list(demo.rglob("ACLs.md"))


def test_an_earlier_demo_is_rebuilt(demo, templates, monkeypatch):
    monkeypatch.setattr(make_demo_data, "write_odt", lambda path, html: False)
    (demo / "Projekte" / "Urlaub 2025" / "04_Finanz").mkdir()  # as after a run of the demo
    make_demo_data.generate(demo, templates)
    assert not (demo / "Projekte" / "Urlaub 2025" / "04_Finanz").exists()


def test_a_folder_that_is_no_demo_is_left_alone(tmp_path, templates):
    mine = tmp_path / "mine"
    mine.mkdir()
    (mine / "Wichtig.md").write_text("bleibt", encoding="utf-8")
    with pytest.raises(SystemExit):
        make_demo_data.generate(mine, templates)
    assert [p.name for p in mine.iterdir()] == ["Wichtig.md"]
