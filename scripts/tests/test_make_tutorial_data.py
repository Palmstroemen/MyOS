"""The tutorial's exercise files (scripts/make_tutorial_data.py): the vacation of lessons 4
and 5 and the vacation of lesson 7, in German and English - generated reproducibly and
committed as generated."""

import filecmp
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TUTORIAL = REPO / "Learning MyOS"

pytest.importorskip("reportlab")
pytest.importorskip("PIL")
if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg is needed for the vacation video", allow_module_level=True)

from scripts.make_tutorial_data import generate  # noqa: E402


@pytest.fixture(scope="module")
def made(tmp_path_factory):
    out = tmp_path_factory.mktemp("tutorial")
    generate(out)
    return out


def _files(root):
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


def test_lesson_4_has_the_vacation_loose_and_lesson_5_the_same_in_one_folder(made):
    for lesson4, lesson5, folder in (("DE/Lektion04", "DE/Lektion05", "Urlaub Sommer 2026"),
                                     ("EN/Lesson04", "EN/Lesson05", "vacation summer 2026")):
        loose = _files(made / lesson4)
        assert len(loose) >= 14
        assert _files(made / lesson5 / folder) == loose  # the same files, put back unsorted
        kinds = {Path(name).suffix for name in loose}
        assert {".md", ".pdf", ".jpg", ".mp4", ".eml"} <= kinds  # notes, bookings, photos, a video, a mail


def test_lesson_7_has_another_vacation_in_its_folder(made):
    for lesson, folder in (("DE/Lektion07", "Urlaub 2025"), ("EN/Lesson07", "vacation 2025")):
        files = _files(made / lesson / folder)
        assert len(files) >= 10 and {".pdf", ".jpg", ".md"} <= {Path(f).suffix for f in files}


def test_both_languages_have_as_many_files(made):
    for de, en in (("DE/Lektion04", "EN/Lesson04"), ("DE/Lektion07", "EN/Lesson07")):
        assert len(_files(made / de)) == len(_files(made / en))


def test_generating_twice_gives_the_same_bytes(made, tmp_path):
    generate(tmp_path)
    for name in _files(made):
        assert filecmp.cmp(made / name, tmp_path / name, shallow=False), name


def test_the_committed_files_are_the_generated_ones(made):
    for name in _files(made):
        assert (TUTORIAL / name).is_file(), f"not committed: {name}"
        assert filecmp.cmp(made / name, TUTORIAL / name, shallow=False), f"differs: {name}"


def test_lesson_10_has_two_projects_each_with_its_own_tags(made):
    # Projects contain the flood of tags: each brings its own (.MyOS/Tags.md); its notes use
    # only those, and some notes are left to be tagged by the learner.
    from core.scope_api import _read_markdown_content_tags, _read_markdown_tag_list

    for lesson, sheet in (("DE/Lektion10", "Übungen zu Tags.md"), ("EN/Lesson10", "Tag exercises.md")):
        assert (made / lesson / sheet).is_file()
        projects = [p.parent.parent for p in (made / lesson).rglob(".MyOS/Project.md")]
        assert len(projects) == 2
        vocabularies = []
        for project in projects:
            vocabulary = set(_read_markdown_tag_list(project / ".MyOS" / "Tags.md"))
            assert len(vocabulary) >= 4
            vocabularies.append(vocabulary)
            notes = [n for n in project.rglob("*.md") if ".MyOS" not in n.parts]
            used = [set(_read_markdown_content_tags(n)) for n in notes]
            assert all(tags <= vocabulary for tags in used), project
            assert any(not tags for tags in used) and sum(1 for tags in used if tags) >= 3
            assert any(p.is_dir() for p in project.iterdir() if p.name != ".MyOS")  # a folder to tag
        assert not vocabularies[0] & vocabularies[1]  # different projects, different tags


def test_lesson_11_has_a_company_whose_rights_are_as_the_exercises_say(made):
    from core.acl import ACLPolicy

    for lesson, sheet, company, work, secret, finance, info in (
            ("DE/Lektion11", "Übungen zu Zugriffsrechten.md", "Musterfirma", "/07_Arbeit/", "/07_Arbeit/Vertraulich/",
             "/04_Finanz/", "/01_Info/"),
            ("EN/Lesson11", "Access rights exercises.md", "Sample Company", "/07_Work/", "/07_Work/Confidential/",
             "/04_Finance/", "/01_Info/")):
        assert (made / lesson / sheet).is_file()
        root = made / lesson / company
        for folder in (work, secret, finance, info):
            assert (root / folder.strip("/")).is_dir(), folder
        policy = ACLPolicy.from_project(root)
        assert all(policy.roles_for_user(person) for person in ("anna huber", "karl berger", "mia novak", "eva muster"))
        can = lambda person, path, right: any(policy.can_access(r, path, right) for r in policy.roles_for_user(person))  # noqa: E731
        assert can("anna huber", finance, "write") and not can("karl berger", finance, "read")
        assert can("karl berger", work, "write") and not can("karl berger", secret, "read")
        assert can("eva muster", secret, "read")  # the management
        assert can("mia novak", info, "read") and not can("mia novak", work, "read")
        changers = [p for p in policy.users if can(p, "/.MyOS/ACLs.md", "change")]
        assert changers == []  # nobody yet: the learner writes themselves in as admin
