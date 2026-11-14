"""ScopeApi.list_entries_xray: the FilesPanel's listing with small folders seen through."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi
from core.brand import META_DIR, env_name


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in (env_name("TEMPLATES_DIR"), env_name("ACL_MODE"), env_name("ACL_USER")):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "Projekt"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# MyOS Project\n")
    (root / "Rechnungen" / "2024").mkdir(parents=True)
    (root / "Rechnungen" / "2024" / "r1.pdf").write_text("r1")
    (root / "notiz.md").write_text("n")
    return root


def test_files_of_small_folders_appear_with_where_they_lie(project):
    entries = ScopeApi(str(project)).list_entries_xray(str(project), 10, True)

    by_name = {e["name"]: e for e in entries}
    assert "Rechnungen" not in by_name
    assert by_name["r1.pdf"]["xrayVia"] == "Rechnungen/2024"
    assert by_name["r1.pdf"]["path"] == str(project / "Rechnungen" / "2024" / "r1.pdf")
    assert "xrayVia" not in by_name["notiz.md"]


def test_without_room_the_listing_is_the_normal_one(project):
    api = ScopeApi(str(project))

    def visible(entries):  # hidden ones (.MyOS, the tag cache written meanwhile) aside
        return sorted(e["name"] for e in entries if not e["name"].startswith("."))

    assert visible(api.list_entries_xray(str(project), 1, True)) == visible(api.list_entries(str(project)))
