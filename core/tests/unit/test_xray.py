"""X-ray view: look through small folders at their files while the listing still fits.

The budget is how many entries fit without scrolling (Scope: the window, myls: the
terminal). Folders are seen through smallest first (by their number of files, then by
name), each completely or not at all, as long as the listing stays within the budget.
Projects, empty, hidden and unreadable folders stay folders."""

from pathlib import Path

import pytest

from core.xray import xray_listing


def _files(base: Path, *names: str) -> None:
    for name in names:
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)


@pytest.fixture
def folder(tmp_path):
    _files(tmp_path, "x.txt", "Rechnungen/r1.pdf", "Rechnungen/r2.pdf",
           "Fotos/a.jpg", "Fotos/b.jpg", "Fotos/c.jpg", "Fotos/d.jpg", "Fotos/e.jpg",
           "Projekt/p.txt", ".versteckt/h.txt")
    (tmp_path / "Leer").mkdir()
    (tmp_path / "Projekt" / ".MyOS").mkdir()
    (tmp_path / "Projekt" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return tmp_path


def _shown(entries):
    return sorted((e.path.name, e.via) for e in entries)


def test_small_folders_are_seen_through_while_the_listing_fits(folder):
    # x.txt, Rechnungen, Fotos, Leer, Projekt: 5 entries; Rechnungen (2 files) adds 1.
    assert _shown(xray_listing(folder, budget=6)) == [
        ("Fotos", ""), ("Leer", ""), ("Projekt", ""),
        ("r1.pdf", "Rechnungen"), ("r2.pdf", "Rechnungen"), ("x.txt", ""),
    ]


def test_bigger_folders_follow_when_there_is_room(folder):
    shown = _shown(xray_listing(folder, budget=10))

    assert ("Fotos", "") not in shown and ("a.jpg", "Fotos") in shown
    assert len(shown) == 10


def test_a_full_listing_stays_as_it_is(folder):
    assert _shown(xray_listing(folder, budget=5)) == [
        ("Fotos", ""), ("Leer", ""), ("Projekt", ""), ("Rechnungen", ""), ("x.txt", ""),
    ]
    assert _shown(xray_listing(folder, budget=0)) == _shown(xray_listing(folder, budget=5))


def test_entries_shown_besides_count_too(folder):
    # e.g. embryos Scope lists next to the real entries
    assert ("Rechnungen", "") in _shown(xray_listing(folder, budget=6, extra=1))


def test_deep_folders_show_where_the_file_lies(tmp_path):
    _files(tmp_path, "Tief/A/B/datei.txt")

    assert _shown(xray_listing(tmp_path, budget=5)) == [("datei.txt", "Tief/A/B")]


def test_folders_holding_a_project_or_unreadable_parts_stay_closed(tmp_path):
    _files(tmp_path, "Mix/m.txt", "Mix/Sub/s.txt", "Zu/z.txt", "Offen/o.txt")
    (tmp_path / "Mix" / "Sub" / ".MyOS").mkdir()
    (tmp_path / "Mix" / "Sub" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")

    shown = _shown(xray_listing(tmp_path, budget=20, may_read=lambda p: p.name != "Zu"))

    assert shown == [("Mix", ""), ("Zu", ""), ("o.txt", "Offen")]


def test_equal_folders_open_in_alphabetical_order(tmp_path):
    _files(tmp_path, "B/b1.txt", "B/b2.txt", "A/a1.txt", "A/a2.txt")

    assert _shown(xray_listing(tmp_path, budget=3)) == [("B", ""), ("a1.txt", "A"), ("a2.txt", "A")]


def test_symlinked_folders_are_not_followed(tmp_path):
    _files(tmp_path, "elsewhere/secret.txt")
    (tmp_path / "here").mkdir()
    (tmp_path / "here" / "Link").symlink_to(tmp_path / "elsewhere")

    assert _shown(xray_listing(tmp_path / "here", budget=10)) == [("Link", "")]


def test_with_folders_hidden_only_files_take_room(folder):
    # The panel shows only x.txt; Rechnungen's 2 files fit into a budget of 3.
    shown = _shown(xray_listing(folder, budget=3, folders_shown=False))

    assert [s for s in shown if s[1]] == [("r1.pdf", "Rechnungen"), ("r2.pdf", "Rechnungen")]


def test_a_folder_with_one_file_opens_even_when_the_listing_is_just_full(tmp_path):
    _files(tmp_path, "a.txt", "Eins/e.txt")

    assert _shown(xray_listing(tmp_path, budget=2)) == [("a.txt", ""), ("e.txt", "Eins")]
