"""Exercise links in notes (PostFix/exercise_links.py): a lesson says
[Übung öffnen](<myos:open?scope=Urlaub 2025&files=Urlaub 2025>) and a click opens Scope in the
exercise folder - and the classic file browser beside it, if the exercise needs one. Nothing
is started for real here: the launches are recorded."""

import os
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from PostFix import exercise_links as ex

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def lesson(tmp_path):
    (tmp_path / "Lektion07" / "Urlaub 2025").mkdir(parents=True)
    (tmp_path / "Lektion07" / "Virtuelle Ordner.md").write_text("x", encoding="utf-8")
    (tmp_path / "Secret").mkdir()
    return tmp_path / "Lektion07"


def test_a_link_names_folders_relative_to_the_lesson(lesson):
    action = ex.parse("myos:open?scope=Urlaub%202025&files=Urlaub%202025", lesson)
    assert action == ex.ExerciseAction(scope=lesson / "Urlaub 2025", files=lesson / "Urlaub 2025")
    assert ex.parse("myos:open?scope=.", lesson) == ex.ExerciseAction(scope=lesson, files=None)
    assert ex.parse("myos:open?files=Urlaub 2025", lesson).scope is None


def test_a_link_may_not_leave_the_lesson(lesson):
    # Security: a note opens folders of its own lesson only, nothing else on the computer.
    for url in ("myos:open?scope=../Secret", "myos:open?scope=/etc", "myos:open?scope=%2Fhome",
                "myos:open?scope=Urlaub 2025/../../Secret", "myos:open?scope=Missing",
                "myos:open", "myos:delete?scope=Urlaub 2025", "https://example.org"):
        assert ex.parse(url, lesson) is None, url


def test_the_commands_start_scope_and_the_desktops_file_browser(lesson):
    action = ex.ExerciseAction(scope=lesson / "Urlaub 2025", files=lesson / "Urlaub 2025")
    scope, files = ex.commands(action, REPO, python="/usr/bin/python3")
    assert scope == ["/usr/bin/python3", str(REPO / "Scope" / "Scope.py"), str(lesson / "Urlaub 2025")]
    assert files == ["xdg-open", str(lesson / "Urlaub 2025")]
    assert ex.commands(ex.ExerciseAction(scope=lesson, files=None), REPO, python="py") == \
        [["py", str(REPO / "Scope" / "Scope.py"), str(lesson)]]


def test_scope_left_the_file_browser_right():
    left, right = ex.halves((0, 30, 1920, 1050))
    assert left == (0, 30, 960, 1050) and right == (960, 30, 960, 1050)


def test_new_windows_are_told_apart_by_process_and_title():
    before = {"0x01"}
    listing = ("0x01  0 111 host Scope - MyOS GUI Stub\n"
               "0x02  0 222 host Scope - MyOS GUI Stub\n"
               "0x03  0 333 host Urlaub 2025\n"
               "0x04  0 444 host Something else\n")
    windows = ex.new_windows(before, listing)
    assert [w.wid for w in windows] == ["0x02", "0x03", "0x04"]
    assert ex.pick(windows, scope_pid=222, folder_name="Urlaub 2025") == ("0x02", "0x03")
    assert ex.pick(windows, scope_pid=999, folder_name="Nope") == (None, None)


class _Recorder:
    def __init__(self):
        self.started, self.ran, self.envs = [], [], []

    def popen(self, argv, **kwargs):
        self.started.append(argv)
        self.envs.append(kwargs.get("env") or {})
        return type("P", (), {"pid": 222})()

    def run(self, argv, **kwargs):
        self.ran.append(argv)
        out = ("0x02  0 222 host Scope - MyOS GUI Stub\n0x03  0 333 host Urlaub 2025\n"
               if argv[:2] == ["wmctrl", "-lp"] else "")
        return type("R", (), {"stdout": out, "returncode": 0})()


def _launcher(lesson, recorder, can_place=True):
    QApplication.instance() or QApplication([])
    return ex.ExerciseLauncher(lambda: lesson, REPO, popen=recorder.popen, run=recorder.run,
                               screen=lambda: (0, 0, 1000, 800), can_place=can_place, before=lambda: set())


def test_a_click_starts_both_and_places_them_side_by_side(lesson):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder)
    launcher.open(QUrl("myos:open?scope=Urlaub 2025&files=Urlaub 2025"))
    assert [argv[0] for argv in recorder.started] == [sys.executable, "xdg-open"]
    launcher.place_tick()  # what the timer does once the windows are there
    moves = [argv for argv in recorder.ran if "-e" in argv]
    assert ["wmctrl", "-i", "-r", "0x02", "-e", "0,0,0,500,800"] in moves
    assert ["wmctrl", "-i", "-r", "0x03", "-e", "0,500,0,500,800"] in moves
    assert not launcher.placing  # done


def test_only_scope_is_not_moved_and_a_refused_link_starts_nothing(lesson):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder)
    launcher.open(QUrl("myos:open?scope=."))
    assert len(recorder.started) == 1 and not launcher.placing
    launcher.open(QUrl("myos:open?scope=../Secret"))
    assert len(recorder.started) == 1


def test_without_wmctrl_both_still_open(lesson):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder, can_place=False)
    launcher.open(QUrl("myos:open?scope=Urlaub 2025&files=Urlaub 2025"))
    assert len(recorder.started) == 2 and not launcher.placing


def test_a_rendered_lesson_link_reaches_the_handler(lesson):
    # The way a click takes in PostFix: the note's Markdown becomes HTML, Qt hands the
    # link's URL to the handler registered for "myos".
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import re
    from PostFix.markdown_render import render_markdown

    html = render_markdown("[Übung öffnen](<myos:open?scope=Urlaub 2025&files=Urlaub 2025>)")
    href = re.search(r'href="([^"]+)"', html).group(1).replace("&amp;", "&")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder)
    QDesktopServices.setUrlHandler(ex.SCHEME, launcher, "open")
    try:
        QDesktopServices.openUrl(QUrl(href))
    finally:
        QDesktopServices.unsetUrlHandler(ex.SCHEME)
    assert recorder.started[0][-1] == str(lesson / "Urlaub 2025")


class _Preview:
    def __init__(self, source):
        self._source = source

    def source(self):
        return self._source


def test_links_are_relative_to_the_note_shown(tmp_path):
    # The lessons' "next lesson" links move the preview on to another note in the same
    # window: exercise links then belong to that note, not to the one opened first.
    from PostFix.main import PostFixWindow

    first, shown = tmp_path / "Lektion01" / "Beginne HIER.md", tmp_path / "Lektion07" / "Virtuelle Ordner.md"
    window = type("W", (), {"_exercise_base": PostFixWindow._exercise_base})()
    window.editor = type("E", (), {})()
    window.editor.current_path = first
    window.editor.preview = _Preview(QUrl())
    assert window._exercise_base() == first.parent
    window.editor.preview = _Preview(QUrl.fromLocalFile(str(shown)))
    assert window._exercise_base() == shown.parent
    window.editor.current_path, window.editor.preview = None, _Preview(QUrl())
    assert window._exercise_base() is None


def test_postfix_registers_the_handler():
    main = (REPO / "PostFix" / "main.py").read_text(encoding="utf-8")
    assert "QDesktopServices.setUrlHandler(EXERCISE_SCHEME, self.exercise_launcher, \"open\")" in main


def test_every_exercise_link_of_the_tutorial_opens_a_folder_of_its_lesson():
    import re

    links = []
    for note in (REPO / "Learning MyOS").rglob("*.md"):
        for target in re.findall(r"\]\(<(myos:[^>]+)>\)", note.read_text(encoding="utf-8")):
            links.append((note, target))
    assert len(links) >= 14  # lessons 4, 5, 7, 8 and the sheets of 10, 11, in both languages
    for note, target in links:
        command = ex.command_of(QUrl(target).toString())
        assert command is not None, (note, target)
        if command == "open":
            assert ex.parse(QUrl(target).toString(), note.parent) is not None, (note, target)


def test_every_german_lesson_ends_with_a_comment_link_and_the_last_with_finish():
    lessons = sorted(p for p in (REPO / "Learning MyOS" / "DE").iterdir() if p.name.startswith("Lektion"))
    assert len(lessons) == 16
    for folder in lessons:
        texts = [n.read_text(encoding="utf-8") for n in folder.glob("*.md")]
        assert any("(<myos:comment>)" in t for t in texts), folder
    assert any("(<myos:finish>)" in n.read_text(encoding="utf-8") for n in lessons[-1].glob("*.md"))


@pytest.fixture
def tutorial_copy(tmp_path):
    # A minimal tutorial copy as scripts/testrun.py makes it (marker in its root).
    from scripts import testrun

    root = tmp_path / "MyOS-Tutorial"
    (root / "DE" / "Lektion07" / "Urlaub 2025").mkdir(parents=True)
    (root / "DE" / "Lektion16").mkdir(parents=True)
    (root / testrun.MARKER).write_text('{"started": "now"}', encoding="utf-8")
    return root


def test_the_comment_link_opens_the_comment_note_with_a_heading(tutorial_copy):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(tutorial_copy / "DE" / "Lektion07", recorder)
    launcher.open(QUrl("myos:comment"))
    note = tutorial_copy / "Meine Kommentare.md"
    assert "## Lektion 7" in note.read_text(encoding="utf-8")
    assert recorder.started == [[sys.executable, str(REPO / "PostFix" / "cli.py"), str(note)]]


def test_finish_asks_first_and_then_hands_over_to_the_test_run(tutorial_copy):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(tutorial_copy / "DE" / "Lektion16", recorder)
    launcher.confirm_finish = lambda: (False, "")
    launcher.open(QUrl("myos:finish"))
    assert recorder.started == []  # not confirmed: nothing happens
    launcher.confirm_finish = lambda: (True, "Anna")
    launcher.open(QUrl("myos:finish"))
    assert recorder.started == [[sys.executable, str(REPO / "scripts" / "testrun.py"), "finish", "--name", "Anna"]]
    assert recorder.envs[-1]["MYOS_TUTORIAL_DIR"] == str(tutorial_copy.resolve())


def test_comment_and_finish_only_work_in_a_tutorial_copy(lesson):
    # Security: "finish" deletes the copy - a note anywhere else (the repository's lessons,
    # any note at all) must not be able to start it.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder)
    launcher.confirm_finish = lambda: (True, "")
    launcher.open(QUrl("myos:finish"))
    launcher.open(QUrl("myos:comment"))
    assert recorder.started == []


def test_scope_from_an_exercise_starts_without_the_lens_drive(lesson):
    # The tutorial does not use the "Perspektiven" drive; started at a lesson's project,
    # Scope would mount it inside the tutorial copy, which "Bin fertig" deletes.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    recorder = _Recorder()
    launcher = _launcher(lesson, recorder)
    launcher.open(QUrl("myos:open?scope=Urlaub 2025&files=Urlaub 2025"))
    scope_env = recorder.envs[0]
    assert scope_env.get("MYOS_SCOPE_START_DAEMON") == "0"
