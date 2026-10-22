"""Filing by date (see "Designdocument Sort.md"): flat, virtual, real.

A folder carries its rule (.MyOS/Sort.md). A level (year, month) only becomes real when
the level above holds more than NewLevelFrom files; before that it is only virtual (a
grouping, nothing moves). Once a level folder exists, the level stays real. Filing is
idempotent: what is due is filed whenever MyOS catches up."""

import os
from pathlib import Path

import pytest

from core.filing import date_of, file_due, read_rule, virtual_groups


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Projekt"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return root


def _sorted_folder(root: Path, rule: str = "Pattern: {{YYYY}}/{{MM}}\nDateSource: filename\nNewLevelFrom: 3\n") -> Path:
    folder = root / "Rechnungen"
    (folder / ".MyOS").mkdir(parents=True)
    (folder / ".MyOS" / "Sort.md").write_text("# Sort\n" + rule)
    return folder


def _put(folder: Path, *names: str) -> None:
    for name in names:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)


def _tree(folder: Path):
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*")
                  if p.is_file() and ".MyOS" not in p.parts and not p.name.startswith("."))


@pytest.fixture
def folder(tmp_path):
    return _sorted_folder(_project(tmp_path))


# --- the rule -----------------------------------------------------------------------

def test_the_rule_is_read_from_the_folder_itself(folder):
    rule = read_rule(folder)

    assert rule.folder == folder.resolve()
    assert rule.levels == ["{{YYYY}}", "{{MM}}"]
    assert rule.date_sources == ("filename",)
    assert rule.new_level_from == 3


def test_defaults_and_where_rules_count(tmp_path):
    root = _project(tmp_path)
    folder = _sorted_folder(root, "Pattern: {{YYYY}}\n")
    rule = read_rule(folder)
    assert rule.date_sources == ("exif", "filename", "frontmatter", "modified")
    assert rule.new_level_from == 20

    outside = tmp_path / "Lose"
    (outside / ".MyOS").mkdir(parents=True)
    (outside / ".MyOS" / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}\n")
    assert read_rule(outside) is None  # only inside projects
    assert read_rule(root) is None     # no rule there


@pytest.mark.parametrize("pattern", ["../{{YYYY}}", "{{YYYY}}/{{YYYY}}", "{{FOO}}", "/etc/{{YYYY}}"])
def test_unsafe_or_invalid_patterns_give_no_rule(tmp_path, pattern):
    folder = _sorted_folder(_project(tmp_path), f"Pattern: {pattern}\n")

    assert read_rule(folder) is None


# --- dates --------------------------------------------------------------------------

@pytest.mark.parametrize("name, expected", [
    ("Rechnung 2024-05-17.pdf", (2024, 5, 17)),
    ("IMG_20230102_101010.jpg", (2023, 1, 2)),
    ("scan_2022_11_30.pdf", (2022, 11, 30)),
])
def test_dates_from_file_names(tmp_path, name, expected):
    path = tmp_path / name
    path.write_text("x")

    assert date_of(path, ("filename",)).timetuple()[:3] == expected


def test_dates_from_front_matter_and_modification_time(tmp_path):
    note = tmp_path / "notiz.md"
    note.write_text("---\ndate: 2021-04-05\n---\n# Notiz\n")
    assert date_of(note, ("frontmatter", "modified")).timetuple()[:3] == (2021, 4, 5)

    plain = tmp_path / "plain.pdf"
    plain.write_text("x")
    os.utime(plain, (1600000000, 1600000000))  # 2020-09-13
    assert date_of(plain, ("filename", "modified")).timetuple()[:3] == (2020, 9, 13)


def test_dates_from_a_photos_exif(tmp_path):
    from PIL import Image

    photo = tmp_path / "IMG_1234.jpg"
    exif = Image.Exif()
    exif[0x9003] = "2019:07:08 10:11:12"  # DateTimeOriginal
    Image.new("RGB", (4, 4)).save(photo, exif=exif)

    assert date_of(photo, ("exif", "modified")).timetuple()[:3] == (2019, 7, 8)


# --- flat, virtual, real ------------------------------------------------------------

def test_few_files_stay_flat_and_are_grouped_only_virtually(folder):
    _put(folder, "a 2024-01-10.pdf", "b 2024-03-02.pdf", "c 2025-02-01.pdf")

    report = file_due(folder)

    assert report.moved == []
    assert _tree(folder) == ["a 2024-01-10.pdf", "b 2024-03-02.pdf", "c 2025-02-01.pdf"]
    groups = virtual_groups(folder)
    assert {name: sorted(p.name for p in files) for name, files in groups.items()} == {
        "2024": ["a 2024-01-10.pdf", "b 2024-03-02.pdf"], "2025": ["c 2025-02-01.pdf"]}


def test_more_than_the_threshold_makes_the_years_real(folder):
    _put(folder, "a 2024-01-10.pdf", "b 2024-03-02.pdf", "c 2025-02-01.pdf", "d 2025-06-01.pdf")

    file_due(folder)

    # each year holds two files: no months yet
    assert _tree(folder) == ["2024/a 2024-01-10.pdf", "2024/b 2024-03-02.pdf",
                             "2025/c 2025-02-01.pdf", "2025/d 2025-06-01.pdf"]
    assert virtual_groups(folder) == {}
    assert sorted(virtual_groups(folder / "2024")) == ["01", "03"]


def test_a_busy_year_gets_real_months(folder):
    _put(folder, *[f"r{i} 2024-0{i}-01.pdf" for i in range(1, 6)])

    file_due(folder)

    assert _tree(folder) == [f"2024/0{i}/r{i} 2024-0{i}-01.pdf" for i in range(1, 6)]


def test_an_existing_level_stays_real_and_new_folders_are_born_when_needed(folder):
    _put(folder, "2026/03/m 2026-03-01.pdf", "neu 2026-05-02.pdf", "alt 2019-01-01.pdf")

    file_due(folder)

    assert _tree(folder) == ["2019/alt 2019-01-01.pdf", "2026/03/m 2026-03-01.pdf", "2026/05/neu 2026-05-02.pdf"]


def test_own_folders_and_hidden_files_are_left_alone(folder):
    _put(folder, "Alt/x 2020-01-01.pdf", ".versteckt 2020-01-01.pdf", *[f"r{i} 2021-01-0{i}.pdf" for i in range(1, 5)])

    file_due(folder)

    assert "Alt/x 2020-01-01.pdf" in _tree(folder) and (folder / ".versteckt 2020-01-01.pdf").exists()
    assert all(p.startswith(("2021/", "Alt/")) for p in _tree(folder))


def test_filing_twice_changes_nothing_more(folder):
    _put(folder, *[f"r{i} 2024-0{i}-01.pdf" for i in range(1, 6)])
    file_due(folder)
    before = _tree(folder)

    assert file_due(folder).moved == []
    assert _tree(folder) == before


def test_name_clashes_get_a_number(folder):
    _put(folder, "2024/Rechnung 2024-05-01.pdf", "Rechnung 2024-05-01.pdf")

    report = file_due(folder)

    assert _tree(folder) == ["2024/Rechnung 2024-05-01 (2).pdf", "2024/Rechnung 2024-05-01.pdf"]
    assert len(report.moved) == 1


def test_nothing_moves_where_writing_is_not_allowed(folder):
    _put(folder, *[f"r{i} 2024-0{i}-01.pdf" for i in range(1, 6)])

    report = file_due(folder, may_write=lambda path: False)

    assert report.moved == [] and len(report.skipped) == 5
    assert all("/" not in p for p in _tree(folder))


def test_symlinks_are_not_filed(folder, tmp_path):
    secret = tmp_path / "geheim 2024-01-01.pdf"
    secret.write_text("x")
    (folder / "link 2024-01-01.pdf").symlink_to(secret)
    _put(folder, *[f"r{i} 2024-0{i}-01.pdf" for i in range(1, 5)])

    file_due(folder)

    assert (folder / "link 2024-01-01.pdf").is_symlink()


# --- helpers for Scope ----------------------------------------------------------------

def test_the_sorting_folder_of_a_level_folder(folder):
    from core.filing import sorted_folder_for

    _put(folder, "2024/03/x 2024-03-01.pdf", "Alt/y.pdf")

    assert sorted_folder_for(folder / "2024" / "03") == folder.resolve()
    assert sorted_folder_for(folder) == folder.resolve()
    assert sorted_folder_for(folder / "Alt") is None


def test_where_a_dropped_file_would_go(folder, tmp_path):
    from core.filing import destination_for

    incoming = tmp_path / "Rechnung 2024-05-17.pdf"
    incoming.write_text("x")
    assert destination_for(incoming, folder) == folder.resolve()  # few files: stays flat

    _put(folder, "2024/x 2024-03-01.pdf")
    assert destination_for(incoming, folder) == folder.resolve() / "2024"  # years real; 2024 too small for months
    _put(folder, "2024/03/y 2024-03-02.pdf")
    assert destination_for(incoming, folder) == folder.resolve() / "2024" / "05"  # months real there


def test_all_sorted_folders_below_a_path(tmp_path):
    from core.filing import sorted_folders

    root = _project(tmp_path)
    one = _sorted_folder(root)
    two = root / "Fotos"
    (two / ".MyOS").mkdir(parents=True)
    (two / ".MyOS" / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}\n")
    (root / ".versteckt" / ".MyOS").mkdir(parents=True)
    (root / ".versteckt" / ".MyOS" / "Sort.md").write_text("# Sort\nPattern: {{YYYY}}\n")

    assert sorted_folders(root) == sorted([one.resolve(), two.resolve()])


def test_inside_a_virtual_folder(folder):
    from core.filing import virtual_listing

    _put(folder, "a 2024-01-10.pdf", "b 2024-03-02.pdf", "c 2025-02-01.pdf")

    year = virtual_listing(folder / "2024")
    assert sorted(year.groups) == ["01", "03"] and year.files == []
    month = virtual_listing(folder / "2024" / "03")
    assert month.groups == {} and [p.name for p in month.files] == ["b 2024-03-02.pdf"]
    assert virtual_listing(folder / "2023") is None   # nothing there
    assert virtual_listing(folder / "Alt") is None    # not a level name
