"""The test machine's run (scripts/testrun.py): every tester gets a fresh copy of the tutorial,
comments in one note, and at the end "Bin fertig" collects what they did and makes the
machine ready for the next one. Everything here runs in temporary folders - never in the
real ~/.config or home."""

import json
import shutil
from pathlib import Path

import pytest

pytest.importorskip("reportlab")
pytest.importorskip("PIL")
if shutil.which("ffmpeg") is None:
    pytest.skip("ffmpeg is needed for the tutorial's example data", allow_module_level=True)

from scripts import testrun  # noqa: E402


@pytest.fixture
def machine(tmp_path):
    places = testrun.Places(
        repo=testrun.REPO_ROOT,
        tutorial=tmp_path / "MyOS-Tutorial",
        results=tmp_path / "MyOS-Testergebnisse",
        config=tmp_path / "config",
    )
    (places.config / "MyOS").mkdir(parents=True)
    (places.config / "MyOS" / "MyOS.conf").write_text("[Scope]\npreview = false\n", encoding="utf-8")
    (places.config / "MyOS" / "Identity.md").write_text("# Identity\nNames: Mia Novak\n", encoding="utf-8")
    (places.config / "PostFixDev").mkdir()
    (places.config / "PostFixDev" / "PostFix.conf").write_text("[General]\n", encoding="utf-8")
    return places


def test_prepare_gives_a_fresh_copy_with_the_comment_note_and_default_settings(machine):
    testrun.prepare(machine)
    lesson1 = machine.tutorial / "DE" / "Lektion01" / "Beginne HIER.md"
    assert lesson1.is_file() and testrun.first_lesson(machine) == lesson1
    assert (machine.tutorial / "DE" / "Lektion04" / "Packliste.md").is_file()  # the example data
    comments = machine.tutorial / testrun.COMMENTS
    assert comments.is_file() and "Kommentare" in comments.read_text(encoding="utf-8")
    marker = json.loads((machine.tutorial / testrun.MARKER).read_text(encoding="utf-8"))
    assert "started" in marker
    assert not (machine.config / "MyOS").exists() and not (machine.config / "PostFixDev").exists()


def test_finish_collects_what_the_tester_did_and_starts_over(machine):
    testrun.prepare(machine)
    lesson = machine.tutorial / "DE" / "Lektion04"
    (lesson / "Urlaub Sommer 2026").mkdir()
    (lesson / "Packliste.md").rename(lesson / "Urlaub Sommer 2026" / "Packliste.md")  # sorted
    (lesson / "Reiseideen.md").write_text("# Reiseideen\n\nLieber nach Island!\n", encoding="utf-8")
    (machine.tutorial / testrun.COMMENTS).write_text(
        "# Meine Kommentare\n\n## Lektion 4\nZu viele Dateien.\n", encoding="utf-8")
    (machine.config / "MyOS").mkdir()
    (machine.config / "MyOS" / "MyOS.conf").write_text("[Scope]\npathBar = false\n", encoding="utf-8")

    result = testrun.finish(machine, name="Anna B.")

    assert result.parent == machine.results and "Anna_B" in result.name
    assert "Zu viele Dateien." in (result / testrun.COMMENTS).read_text(encoding="utf-8")
    changes = (result / "Änderungen.md").read_text(encoding="utf-8")
    assert "DE/Lektion04/Urlaub Sommer 2026/Packliste.md" in changes  # added
    assert "DE/Lektion04/Packliste.md" in changes  # gone from where it was
    assert "+Lieber nach Island!" in changes  # a changed note, as a diff
    assert (result / "Geändert" / "DE" / "Lektion04" / "Reiseideen.md").is_file()
    assert (result / "Einstellungen" / "MyOS" / "MyOS.conf").is_file()
    summary = (result / "Zusammenfassung.md").read_text(encoding="utf-8")
    assert "Anna B." in summary and "Beginn" in summary
    # Ready for the next one: everything as at the start.
    assert (lesson / "Packliste.md").is_file() and not (lesson / "Urlaub Sommer 2026").exists()
    assert "Zu viele" not in (machine.tutorial / testrun.COMMENTS).read_text(encoding="utf-8")
    assert not (machine.config / "MyOS").exists()


def test_without_a_name_testers_are_numbered(machine):
    testrun.prepare(machine)
    first = testrun.finish(machine, name="")
    second = testrun.finish(machine, name="  ")
    assert first.name.endswith("Tester_1") and second.name.endswith("Tester_2")


def test_nothing_is_deleted_that_is_not_a_tutorial_copy(machine):
    # Security: prepare deletes the folder it copies into - only if it is one of its copies.
    machine.tutorial.mkdir()
    (machine.tutorial / "important.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(testrun.NotATutorialCopy):
        testrun.prepare(machine)
    assert (machine.tutorial / "important.txt").is_file()


def test_the_copy_root_is_found_from_any_lesson(machine):
    testrun.prepare(machine)
    assert testrun.copy_root(machine.tutorial / "DE" / "Lektion07" / "Urlaub 2025") == machine.tutorial
    assert testrun.copy_root(testrun.REPO_ROOT / "Learning MyOS" / "DE" / "Lektion07") is None


def test_a_comment_heading_per_lesson(machine):
    testrun.prepare(machine)
    note = testrun.comment_note(machine.tutorial / "DE" / "Lektion07")
    testrun.comment_note(machine.tutorial / "DE" / "Lektion07")  # twice: one heading
    testrun.comment_note(machine.tutorial / "DE" / "Lektion10")
    text = note.read_text(encoding="utf-8")
    assert text.count("## Lektion 7") == 1 and "## Lektion 10" in text
    assert text.index("## Lektion 7") < text.index("## Lektion 10")


def test_only_windows_of_the_tutorial_copy_are_closed(tmp_path):
    # Scope or PostFix of this repository showing something of the copy - not the other
    # windows of whoever uses the computer.
    repo, copy = Path("/opt/MyOS"), Path("/home/t/MyOS-Tutorial")
    lesson = "/home/t/MyOS-Tutorial/DE/Lektion01/Beginne HIER.md"
    assert testrun.is_ours(["python3", "/opt/MyOS/PostFix/cli.py", lesson], Path("/"), repo, copy)
    assert testrun.is_ours(["python3", "Scope/Scope.py", "/home/t/MyOS-Tutorial/DE/Lektion07"], repo, repo, copy)
    assert not testrun.is_ours(["python3", "/opt/MyOS/Scope/Scope.py", "/home/t/Projekte"], Path("/"), repo, copy)
    assert not testrun.is_ours(["python3", "scripts/testrun.py", "finish"], repo, repo, copy)
    assert not testrun.is_ours(["nemo", "/home/t/MyOS-Tutorial"], repo, repo, copy)


def test_the_autostart_opens_the_tutorial(machine):
    entry = testrun.install_autostart(machine)
    text = entry.read_text(encoding="utf-8")
    assert entry.parent == machine.config / "autostart"
    assert "testrun.py" in text and " start" in text


def test_a_note_only_moved_on_the_screen_is_no_change(machine):
    # PostFix keeps a note's window place in its front matter: opening a lesson is no change.
    testrun.prepare(machine)
    lesson = machine.tutorial / "DE" / "Lektion02" / "Markdown-Dateien.md"
    lesson.write_text("---\nwindow_width_px: 900\nwindow_x_permille: 71\n---\n" + lesson.read_text(encoding="utf-8"),
                      encoding="utf-8")
    first = machine.tutorial / "DE" / "Lektion01" / "Beginne HIER.md"
    first.write_text(first.read_text(encoding="utf-8").replace("window_x_permille: 78", "window_x_permille: 300"),
                     encoding="utf-8")
    result = testrun.finish(machine)
    assert "0 neu, 0 geändert, 0 weg" in (result / "Änderungen.md").read_text(encoding="utf-8")


def test_the_copy_comes_from_the_last_commit_not_from_edited_lessons(tmp_path):
    # A note opened in the repository itself (PostFix saves window places, someone types)
    # must never reach a tester: the copy is built from what is committed.
    import subprocess

    repo = tmp_path / "repo"
    lesson = repo / "Learning MyOS" / "DE" / "Lektion01" / "Beginne HIER.md"
    lesson.parent.mkdir(parents=True)
    lesson.write_text("# Hallo!\n", encoding="utf-8")
    git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.org"]
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "lesson"], check=True)
    lesson.write_text("---\nwindow_x_permille: 300\n---\n# Hallo!\nangetippt\n", encoding="utf-8")
    (lesson.parent / "stray.md").write_text("not committed", encoding="utf-8")

    places = testrun.Places(repo=repo, tutorial=tmp_path / "copy", results=tmp_path / "results",
                            config=tmp_path / "config")
    testrun.prepare(places)
    copied = places.tutorial / "DE" / "Lektion01"
    assert (copied / "Beginne HIER.md").read_text(encoding="utf-8") == "# Hallo!\n"
    assert not (copied / "stray.md").exists()
