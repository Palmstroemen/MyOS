"""ScopeApi marks real folders that come from the project's templates (isStandard): the grid
shows them on top together with the pale ones."""

import pytest

from core.scope_api import ScopeApi


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MYOS_TEMPLATES_DIR", str(tmp_path / "Templates"))
    monkeypatch.delenv("MYOS_ACL_MODE", raising=False)
    for name in ("01_Info", "04_Finanz/Ausgaben"):
        (tmp_path / "Templates" / "Standard" / name).mkdir(parents=True)
    root = tmp_path / "Projekt"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    (root / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (root / "04_Finanz" / "Eigenes").mkdir()
    (root / "Eigenes").mkdir()
    (root / "a.txt").write_text("a")
    return root


def _by_name(project, folder=None):
    return {e["name"]: e for e in ScopeApi(str(project)).list_entries(str(folder or project))}


def test_a_born_template_folder_is_marked_and_others_are_not(project):
    entries = _by_name(project)
    assert entries["04_Finanz"].get("isStandard") is True
    assert not entries["Eigenes"].get("isStandard")
    assert not entries["a.txt"].get("isStandard")
    assert entries["01_Info"].get("isEmbryo") is True


def test_the_mark_holds_further_down(project):
    entries = _by_name(project, project / "04_Finanz")
    assert entries["Ausgaben"].get("isStandard") is True
    assert not entries["Eigenes"].get("isStandard")


def test_the_mark_holds_in_the_xray_listing(project):
    entries = {e["name"]: e for e in ScopeApi(str(project)).list_entries_xray(str(project), 1, True)}
    assert entries["04_Finanz"].get("isStandard") is True  # too little room to see through it
