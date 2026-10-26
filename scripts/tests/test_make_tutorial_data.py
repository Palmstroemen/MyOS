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
