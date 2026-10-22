"""ScopeApi and filing by date (core/filing.py): catching up when a folder is looked at,
after moves, across a project; the preview when moving; enabling sorting in a folder."""

from pathlib import Path

import pytest

from core.scope_api import ScopeApi


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path_factory):
    for key in ("MYOS_TEMPLATES_DIR", "MYOS_ACL_MODE", "MYOS_ACL_USER"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))


RULE = "# Sort\nPattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 2\n"


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "Projekt"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    folder = root / "Rechnungen"
    (folder / ".MyOS").mkdir(parents=True)
    (folder / ".MyOS" / "Sort.md").write_text(RULE)
    return root


def _put(folder: Path, *names: str) -> None:
    for name in names:
        (folder / name).write_text(name)


def test_looking_at_a_sorted_folder_files_what_is_due(project):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf", "c 2025-01-01.pdf")

    names = {e["name"] for e in ScopeApi(str(project)).list_entries(str(folder))}

    assert {"2024", "2025"} <= names and "a 2024-01-01.pdf" not in names
    assert (folder / "2024" / "a 2024-01-01.pdf").exists()


def test_a_moved_file_is_filed_and_reported(project, tmp_path):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf")
    incoming = project / "c 2025-01-01.pdf"
    incoming.write_text("c")
    api = ScopeApi(str(project))

    preview = api.preview_sort_target_for_move(str(incoming), str(folder))
    result = api.move_entries([str(incoming)], str(folder))

    assert preview == {"ok": True, "reason": "filed", "target": str((folder / "2025").resolve())}
    assert (folder / "2025" / "c 2025-01-01.pdf").exists()
    assert result["sorted"][0]["destination"].endswith("Rechnungen/2025/c 2025-01-01.pdf")


def test_without_a_level_to_go_to_the_preview_says_nothing(project):
    incoming = project / "a 2024-01-01.pdf"
    incoming.write_text("a")

    preview = ScopeApi(str(project)).preview_sort_target_for_move(str(incoming), str(project / "Rechnungen"))

    assert preview["ok"] is False


def test_catching_up_across_the_project(project):
    folder = project / "Rechnungen"
    _put(folder, "a 2024-01-01.pdf", "b 2024-02-01.pdf", "c 2025-01-01.pdf")

    report = ScopeApi(str(project)).catch_up_filing_all(str(project / "Rechnungen"))

    assert len(report["moved"]) == 3 and report["ok"]


def test_enabling_sorting_puts_a_rule_into_the_folder(project):
    fotos = project / "Fotos"
    fotos.mkdir()
    api = ScopeApi(str(project))

    result = api.enable_sorting(str(fotos))

    assert result["ok"] and (fotos / ".MyOS" / "Sort.md").read_text().startswith("# Sort\nPattern: {{YYYY}}/{{MM}}\n")
    assert api.enable_sorting(str(fotos))["reason"] == "exists"
    assert api.enable_sorting(str(project.parent))["reason"] == "no_project"


@pytest.fixture
def few(tmp_path):
    """A sorted folder with few files: they stay loose, shown in virtual folders."""
    root = tmp_path / "Projekt"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    folder = root / "Rechnungen"
    (folder / ".MyOS").mkdir(parents=True)
    (folder / ".MyOS" / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 10\n")
    _put(folder, "a 2024-01-01.pdf", "b 2024-03-01.pdf", "c 2025-01-01.pdf", "ohne Datum.pdf")
    return folder


def test_loose_files_are_shown_in_virtual_folders(few):
    entries = {e["name"]: e for e in ScopeApi(str(few.parent)).list_entries(str(few))}

    assert entries["2024"]["isVirtual"] is True and entries["2024"]["isDir"] is True
    assert entries["2024"]["path"] == str(few / "2024")
    assert "a 2024-01-01.pdf" not in entries and "ohne Datum.pdf" in entries
    assert not (few / "2024").exists()  # nothing moved


def test_inside_virtual_folders(few):
    api = ScopeApi(str(few.parent))

    year = {e["name"]: e for e in api.list_entries(str(few / "2024"))}
    month = api.list_entries(str(few / "2024" / "03"))

    assert sorted(year) == ["01", "03"] and year["03"]["isVirtual"] is True
    assert [(e["name"], e["path"]) for e in month] == [("b 2024-03-01.pdf", str(few / "b 2024-03-01.pdf"))]


def test_xray_sees_through_small_virtual_folders(few):
    entries = ScopeApi(str(few.parent)).list_entries_xray(str(few), 10, True)

    names = sorted(e["name"] for e in entries if not e["name"].startswith("."))
    assert names == ["a 2024-01-01.pdf", "b 2024-03-01.pdf", "c 2025-01-01.pdf", "ohne Datum.pdf"]
    assert not any(e.get("xrayVia") or e.get("isVirtual") for e in entries)


def test_the_quick_listing_shows_the_same_virtual_folders(few):
    api = ScopeApi(str(few.parent))

    quick = sorted(e["name"] for e in api.list_entries_quick(str(few)))
    inside = [e["name"] for e in api.list_entries_quick(str(few / "2024" / "03"))]

    assert quick == ["2024", "2025", "ohne Datum.pdf"] and inside == ["b 2024-03-01.pdf"]
