"""Where a project's templates live: <project>/.MyOS/Templates, the nearest one upward.

A plain Templates/ folder is never taken: ~/Templates (XDG), a cloud's own Templates folder
and the like are not MyOS'. MYOS_TEMPLATES_DIR overrides the search."""

import pytest

from core.template_place import find_templates_dir
from core.brand import META_DIR, env_name


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)


def _project(path):
    (path / META_DIR).mkdir(parents=True)
    (path / META_DIR / "Project.md").write_text("# MyOS Project\n")
    return path


def test_the_templates_of_a_project_lie_in_its_settings_folder(tmp_path):
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates" / "Standard").mkdir(parents=True)

    assert find_templates_dir(root) == (root / META_DIR / "Templates").resolve()


def test_a_subproject_uses_the_templates_of_the_project_above(tmp_path):
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates" / "Standard").mkdir(parents=True)
    sub = _project(root / "Familie")
    (sub / "Fotos").mkdir()

    assert find_templates_dir(sub / "Fotos") == (root / META_DIR / "Templates").resolve()


def test_the_nearest_templates_win_as_a_whole(tmp_path):
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates" / "Standard").mkdir(parents=True)
    sub = _project(root / "Familie")
    (sub / META_DIR / "Templates" / "Person").mkdir(parents=True)

    assert find_templates_dir(sub) == (sub / META_DIR / "Templates").resolve()


def test_a_plain_templates_folder_is_not_taken(tmp_path):
    root = _project(tmp_path / "home" / "Projekte")
    (tmp_path / "home" / "Templates" / "Standard").mkdir(parents=True)  # like ~/Templates
    (root / "Templates" / "Standard").mkdir(parents=True)  # like a cloud's own Templates

    assert find_templates_dir(root) is None


def test_inside_a_template_its_own_set_is_found(tmp_path):
    root = _project(tmp_path / "Projekte")
    finanz = root / META_DIR / "Templates" / "Standard" / "04_Finanz"
    finanz.mkdir(parents=True)

    assert find_templates_dir(finanz) == (root / META_DIR / "Templates").resolve()


def test_the_environment_overrides_the_search(tmp_path, monkeypatch):
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "Templates").mkdir()
    monkeypatch.setenv(env_name("TEMPLATES_DIR"), str(tmp_path / "Global"))

    assert find_templates_dir(root) == (tmp_path / "Global").resolve()
