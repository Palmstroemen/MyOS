#!/usr/bin/env python3
"""
The test machine: several people play through the tutorial one after the other.

Every tester works in a fresh copy of the tutorial (~/MyOS-Tutorial), the repository stays
untouched. Comments go into one note, "Meine Kommentare.md", which a link at the end of each
lesson opens. At the end, the last lesson's link "Bin fertig" collects what the tester did -
comments, every note changed, added or gone, the settings - into ~/MyOS-Testergebnisse,
resets everything and opens lesson 1 for the next one.

    python3 scripts/testrun.py install            # once: open the tutorial at login
    python3 scripts/testrun.py start              # open lesson 1 (a copy is made if missing)
    python3 scripts/testrun.py prepare            # fresh copy, settings reset
    python3 scripts/testrun.py finish [--name N]  # collect, reset, open lesson 1 again

MYOS_TUTORIAL_DIR and MYOS_RESULTS_DIR change where the copy and the results lie.
"""

import argparse
import datetime
import difflib
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

MARKER = ".myos-tutorial-copy"  # in the copy's root: it is ours, and when the tester started
COMMENTS = "Meine Kommentare.md"
FIRST_LESSON = Path("DE") / "Lektion01" / "Beginne HIER.md"
# Settings a tester changes, reset for the next one (relative to the config home).
SETTINGS = ("MyOS", "PostFixDev")
# Files the programs write on their own; not what the tester did.
NOISE = {".TagsHere.json"}

COMMENTS_TEXT = (
    "# Meine Kommentare\n\n"
    "Schreib hier alles hinein, was dir beim Durchspielen auffällt: was unklar war, was "
    "nicht funktioniert hat, was dir gefallen hat. Unter jeder Lektion findest du einen Link, "
    "der diese Notiz öffnet und eine Überschrift für die Lektion anlegt.\n"
)


class NotATutorialCopy(RuntimeError):
    """The folder to be replaced is not a copy made by this script."""


@dataclass(frozen=True)
class Places:
    repo: Path
    tutorial: Path
    results: Path
    config: Path

    @classmethod
    def default(cls) -> "Places":
        home = Path.home()
        return cls(
            repo=REPO_ROOT,
            tutorial=Path(os.environ.get("MYOS_TUTORIAL_DIR") or home / "MyOS-Tutorial"),
            results=Path(os.environ.get("MYOS_RESULTS_DIR") or home / "MyOS-Testergebnisse"),
            config=Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config"),
        )


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def first_lesson(places: Places) -> Path:
    return places.tutorial / FIRST_LESSON


def copy_root(path: Path) -> Optional[Path]:
    """The tutorial copy path lies in (the folder with the marker), None outside of one."""
    path = Path(path).resolve()
    for folder in (path, *path.parents):
        if (folder / MARKER).is_file():
            return folder
    return None


def _committed_lessons(repo: Path, target: Path) -> bool:
    """The lessons as committed (git archive HEAD) into target; False without git."""
    try:
        archive = subprocess.run(["git", "-C", str(repo), "archive", "--format=tar", "HEAD", "Learning MyOS"],
                                 capture_output=True, check=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    with tempfile.TemporaryDirectory() as scratch:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            # Security: only regular files and folders below "Learning MyOS" are unpacked.
            members = [m for m in tar.getmembers()
                       if (m.isfile() or m.isdir()) and m.name.split("/")[0] == "Learning MyOS" and ".." not in m.name.split("/")]
            tar.extractall(scratch, members=members)
        shutil.copytree(Path(scratch) / "Learning MyOS", target, ignore=shutil.ignore_patterns(*NOISE, "__pycache__"))
    return True


def _build_pristine(places: Places, target: Path) -> None:
    """The tutorial as a tester finds it: the repository's lessons as last committed (a note
    opened in the repository itself never reaches a tester) and the example data."""
    from scripts.make_tutorial_data import generate  # Pillow, reportlab: only when building

    if not _committed_lessons(places.repo, target):  # no git (e.g. an unpacked release)
        shutil.copytree(places.repo / "Learning MyOS", target,
                        ignore=shutil.ignore_patterns(*NOISE, "__pycache__"))
    generate(target)
    (target / COMMENTS).write_text(COMMENTS_TEXT, encoding="utf-8")


def prepare(places: Places) -> None:
    """A fresh copy of the tutorial and the programs' settings back to their defaults."""
    if places.tutorial.exists():
        # Security: only ever delete a folder this script made (it holds the marker).
        if not (places.tutorial / MARKER).is_file():
            raise NotATutorialCopy(f"{places.tutorial} is no tutorial copy, it is left alone")
        shutil.rmtree(places.tutorial)
    _build_pristine(places, places.tutorial)
    (places.tutorial / MARKER).write_text(json.dumps({"started": _now()}), encoding="utf-8")
    for name in SETTINGS:
        shutil.rmtree(places.config / name, ignore_errors=True)


def _files(root: Path) -> dict:
    found = {}
    for path in root.rglob("*"):
        if path.is_file() and path.name not in NOISE and path.name != MARKER and "__pycache__" not in path.parts:
            found[path.relative_to(root).as_posix()] = path
    return found


def _without_window_place(data: bytes) -> bytes:
    """A note without the window place PostFix keeps in its front matter (window_...: ...),
    and without a front matter left empty by that: opening a note moves no content."""
    text = data.decode("utf-8", errors="replace")
    if not text.startswith("---\n"):
        return data
    end = text.find("\n---\n", 4)
    if end < 0:
        return data
    kept = [line for line in text[4:end].splitlines() if not line.startswith("window_")]
    body = text[end + 5:]
    return (("---\n" + "\n".join(kept) + "\n---\n" if kept else "") + body).encode("utf-8")


def _same(before: Path, after: Path) -> bool:
    a, b = before.read_bytes(), after.read_bytes()
    if a == b:
        return True
    return before.suffix.lower() == ".md" and _without_window_place(a) == _without_window_place(b)


def _is_text(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".txt", ".json", ".csv", ".eml"}


def _safe_name(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip()).strip("._")[:40]


def _next_tester_number(results: Path) -> int:
    numbers = [int(m.group(1)) for p in results.glob("*_Tester_*")
               for m in [re.search(r"_Tester_(\d+)$", p.name)] if m]
    return max(numbers, default=0) + 1


def collect(places: Places, name: str = "") -> Path:
    """What the tester did, into a folder of its own under the results."""
    places.results.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = _safe_name(name) or f"Tester_{_next_tester_number(places.results)}"
    result = places.results / f"{stamp}_{label}"
    suffix = 2
    while result.exists():
        result = places.results / f"{stamp}_{label}_{suffix}"
        suffix += 1
    result.mkdir()

    comments = places.tutorial / COMMENTS
    if comments.is_file():
        shutil.copy2(comments, result / COMMENTS)

    with tempfile.TemporaryDirectory() as scratch:
        pristine = Path(scratch) / "tutorial"
        _build_pristine(places, pristine)
        before, after = _files(pristine), _files(places.tutorial)
        before.pop(COMMENTS, None)
        after.pop(COMMENTS, None)
        added = sorted(set(after) - set(before))
        gone = sorted(set(before) - set(after))
        changed = sorted(k for k in set(after) & set(before) if not _same(before[k], after[k]))
        lines = ["# Änderungen", "", f"{len(added)} neu, {len(changed)} geändert, {len(gone)} weg.", ""]
        for title, names in (("Neu", added), ("Geändert", changed), ("Weg (verschoben oder gelöscht)", gone)):
            lines += [f"## {title}", ""] + [f"- {n}" for n in names] + [""]
        for key in changed:
            if _is_text(after[key]):
                diff = difflib.unified_diff(
                    before[key].read_text(encoding="utf-8", errors="replace").splitlines(),
                    after[key].read_text(encoding="utf-8", errors="replace").splitlines(),
                    f"vorher/{key}", f"nachher/{key}", lineterm="")
                lines += [f"### {key}", "", "```diff", *diff, "```", ""]
        (result / "Änderungen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for folder, names in (("Neu", added), ("Geändert", changed)):
            for key in names:
                target = result / folder / key
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(after[key], target)

    for setting in SETTINGS:
        if (places.config / setting).is_dir():
            shutil.copytree(places.config / setting, result / "Einstellungen" / setting)

    started = ""
    try:
        started = json.loads((places.tutorial / MARKER).read_text(encoding="utf-8")).get("started", "")
    except (OSError, ValueError):
        pass
    (result / "Zusammenfassung.md").write_text(
        "# Zusammenfassung\n\n"
        f"- Tester: {name.strip() or label.replace('_', ' ')}\n"
        f"- Beginn: {started or 'unbekannt'}\n"
        f"- Ende: {_now()}\n"
        f"- Notizen neu: {len(added)}, geändert: {len(changed)}, weg: {len(gone)}\n",
        encoding="utf-8")
    return result


def finish(places: Places, name: str = "") -> Path:
    """Collect the tester's work, then make the machine ready for the next one."""
    result = collect(places, name)
    prepare(places)
    return result


def is_ours(argv: List[str], cwd: Path, repo: Path, copy: Path) -> bool:
    """Whether a process is Scope or PostFix of this repository showing something of the
    tutorial copy (by its command line) - other windows on the computer are left alone."""
    programs = {(repo / "Scope" / "Scope.py").resolve(), (repo / "PostFix" / "cli.py").resolve()}

    def path_of(arg):
        return (Path(arg) if Path(arg).is_absolute() else Path(cwd) / arg).resolve()

    program = any(arg.endswith(("Scope.py", "cli.py")) and path_of(arg) in programs for arg in argv[:3])
    copy = Path(copy).resolve()
    shows_copy = any(path_of(arg) == copy or copy in path_of(arg).parents for arg in argv[1:] if arg)
    return program and shows_copy


def close_programs(places: Places) -> None:
    """Close the Scope and PostFix windows showing the tutorial copy (it is about to go)."""
    me = os.getpid()
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == me:
            continue
        try:
            argv = (proc / "cmdline").read_bytes().decode(errors="replace").split("\0")
            cwd = Path(os.readlink(proc / "cwd"))
            if proc.stat().st_uid != os.getuid():
                continue
        except OSError:
            continue
        if is_ours([a for a in argv if a], cwd, places.repo, places.tutorial):
            try:
                os.kill(int(proc.name), signal.SIGTERM)
            except OSError:
                pass


def open_lesson(places: Places, note: Optional[Path] = None) -> None:
    subprocess.Popen([sys.executable, str(places.repo / "PostFix" / "cli.py"), str(note or first_lesson(places))],
                     cwd=str(places.repo), start_new_session=True)


def comment_note(lesson_folder: Path) -> Path:
    """The tutorial's comment note, with a heading for the lesson lesson_folder belongs to."""
    root = copy_root(lesson_folder)
    if root is None:
        raise NotATutorialCopy(f"{lesson_folder} is not in a tutorial copy")
    note = root / COMMENTS
    if not note.is_file():
        note.write_text(COMMENTS_TEXT, encoding="utf-8")
    relative = Path(lesson_folder).resolve().relative_to(root)
    match = next((re.match(r"(?:Lektion|Lesson)0*(\d+)$", part) for part in relative.parts
                  if re.match(r"(?:Lektion|Lesson)0*(\d+)$", part)), None)
    heading = f"## Lektion {match.group(1)}" if match else "## Allgemein"
    text = note.read_text(encoding="utf-8")
    if heading not in text.splitlines():
        note.write_text(text.rstrip("\n") + f"\n\n{heading}\n\n", encoding="utf-8")
    return note


def install_autostart(places: Places) -> Path:
    """At login the tutorial opens (lesson 1 of the current copy)."""
    entry = places.config / "autostart" / "myos-tutorial.desktop"
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(
        "[Desktop Entry]\nType=Application\nName=MyOS Tutorial\n"
        f"Exec={sys.executable} \"{places.repo / 'scripts' / 'testrun.py'}\" start\n"
        "X-GNOME-Autostart-enabled=true\n", encoding="utf-8")
    return entry


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("install", help="open the tutorial at login")
    sub.add_parser("start", help="open lesson 1 (makes a copy if there is none)")
    sub.add_parser("prepare", help="fresh copy, settings reset")
    finish_cmd = sub.add_parser("finish", help="collect, reset, open lesson 1 again")
    finish_cmd.add_argument("--name", default="")
    finish_cmd.add_argument("--no-restart", action="store_true", help="only collect and reset")
    args = parser.parse_args(argv)
    places = Places.default()
    if args.command == "install":
        print(install_autostart(places))
    elif args.command == "start":
        if copy_root(places.tutorial) != places.tutorial.resolve():
            prepare(places)
        open_lesson(places)
    elif args.command == "prepare":
        prepare(places)
    elif args.command == "finish":
        if not args.no_restart:
            close_programs(places)
        result = finish(places, args.name)
        print(f"Ergebnisse: {result}")
        if not args.no_restart:
            open_lesson(places)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
