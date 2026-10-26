"""Exercise links in notes: a lesson of Learning MyOS says

    [Übung öffnen](<myos:open?scope=Urlaub 2025&files=Urlaub 2025>)

and a click opens Scope in the exercise folder (scope=) and, if the exercise needs it, the
desktop's classic file browser (files=) - Scope on the left half of the screen, the file
browser on the right. Folders are relative to the note shown. PostFix registers the handler
for "myos" links itself (QDesktopServices); nothing on the system changes, so these links work
in PostFix only.

On the test machine (scripts/testrun.py) two more: myos:comment opens the tutorial's comment
note with a heading for the lesson, myos:finish ("Bin fertig") hands the tutorial copy over to
the test run, which collects the tester's work and starts over.
"""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, NamedTuple, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote, urlsplit

from PySide6.QtCore import QObject, QTimer, QUrl, Slot
from PySide6.QtWidgets import QInputDialog, QLineEdit

SCHEME = "myos"
PLACE_INTERVAL_MS = 250
PLACE_TRIES = 80  # the windows have 20 seconds to appear (a file browser starting cold is slow)


@dataclass(frozen=True)
class ExerciseAction:
    scope: Optional[Path]  # open Scope here
    files: Optional[Path]  # open the classic file browser here


class Window(NamedTuple):
    wid: str
    pid: int
    title: str


def _inside(base: Path, relative: str) -> Optional[Path]:
    """base/relative as an existing folder inside base, else None."""
    # Security: a note may only open folders of its own lesson - no absolute paths, no way
    # out with "..", no symlink leading elsewhere (resolve() follows them before the check).
    if not relative or relative.startswith(("/", "\\", "~")):
        return None
    root = base.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        return None
    return target if target.is_dir() else None


def command_of(url: str) -> Optional[str]:
    """"open", "comment" or "finish" of a myos link, None for anything else."""
    parts = urlsplit(str(url or ""))
    if parts.scheme != SCHEME:
        return None
    command = unquote(parts.path)
    return command if command in ("open", "comment", "finish") else None


def parse(url: str, base: Path) -> Optional[ExerciseAction]:
    """The action of a "myos:open?..." link in a note lying in base, None if refused."""
    parts = urlsplit(str(url or ""))
    if parts.scheme != SCHEME or unquote(parts.path) != "open":
        return None
    query = parse_qs(parts.query, keep_blank_values=True)
    folders = {}
    for key in ("scope", "files"):
        if key not in query:
            folders[key] = None
            continue
        folder = _inside(Path(base), unquote(query[key][0]).strip())
        if folder is None:
            return None
        folders[key] = folder
    if folders["scope"] is None and folders["files"] is None:
        return None
    return ExerciseAction(scope=folders["scope"], files=folders["files"])


def commands(action: ExerciseAction, repo_root: Path, python: str = sys.executable) -> List[List[str]]:
    """The programs to start: Scope (this repository's) and the desktop's file browser."""
    argv = []
    if action.scope is not None:
        argv.append([python, str(Path(repo_root) / "Scope" / "Scope.py"), str(action.scope)])
    if action.files is not None:
        argv.append(["xdg-open", str(action.files)])
    return argv


def halves(screen: Tuple[int, int, int, int]) -> Tuple[Tuple[int, int, int, int], Tuple[int, int, int, int]]:
    """Left and right half of the screen's free area (x, y, width, height)."""
    x, y, width, height = screen
    left = width // 2
    return (x, y, left, height), (x + left, y, width - left, height)


def new_windows(before: Set[str], listing: str) -> List[Window]:
    """The windows of a "wmctrl -lp" listing that were not there before."""
    windows = []
    for line in listing.splitlines():
        fields = line.split(None, 4)
        if len(fields) < 4 or fields[0] in before:
            continue
        try:
            pid = int(fields[2])
        except ValueError:
            continue
        windows.append(Window(fields[0], pid, fields[4] if len(fields) > 4 else ""))
    return windows


def pick(windows: List[Window], scope_pid: Optional[int], folder_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Scope's new window (by its process) and the file browser's (by the folder's name)."""
    scope = next((w.wid for w in windows if scope_pid is not None and w.pid == scope_pid), None)
    files = next((w.wid for w in windows if w.wid != scope and folder_name and folder_name in w.title), None)
    return scope, files


def _window_ids(run) -> Set[str]:
    try:
        listing = run(["wmctrl", "-lp"], capture_output=True, text=True, timeout=2).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    return {line.split(None, 1)[0] for line in listing.splitlines() if line.strip()}


class ExerciseLauncher(QObject):
    """Handler of "myos" links (QDesktopServices.setUrlHandler(SCHEME, launcher, "open"))."""

    def __init__(self, base: Callable[[], Optional[Path]], repo_root: Path, popen=subprocess.Popen,
                 run=subprocess.run, screen: Optional[Callable[[], Tuple[int, int, int, int]]] = None,
                 can_place: Optional[bool] = None, before: Optional[Callable[[], Set[str]]] = None, parent=None):
        super().__init__(parent)
        self._base = base
        self._repo_root = Path(repo_root)
        self._popen = popen
        self._run = run
        self._screen = screen or _available_geometry
        # Placing windows needs wmctrl (X11); without it both simply open.
        self._can_place = shutil.which("wmctrl") is not None if can_place is None else can_place
        self._before = before or (lambda: _window_ids(self._run))
        self._timer = QTimer(self)
        self._timer.setInterval(PLACE_INTERVAL_MS)
        self._timer.timeout.connect(self.place_tick)
        self._pending = None  # (windows before, scope pid, folder name, tries left)
        self._placed = {}
        self.confirm_finish = self._ask_finish  # -> (confirmed, name); replaceable in tests

    @property
    def placing(self) -> bool:
        return self._pending is not None

    @Slot(QUrl)
    def open(self, url: QUrl) -> None:
        base = self._base()
        command = command_of(url.toString())
        if command in ("comment", "finish"):
            self._test_run(command, base)
            return
        action = parse(url.toString(), base) if base is not None else None
        if action is None:
            print(f"[PostFix] exercise link refused: {url.toString()}", file=sys.stderr)
            return
        both = action.scope is not None and action.files is not None
        before = self._before() if both and self._can_place else set()
        scope_pid = None
        for argv in commands(action, self._repo_root):
            try:
                process = self._popen(argv, cwd=str(self._repo_root), start_new_session=True)
            except OSError as error:
                print(f"[PostFix] could not start {argv[0]}: {error}", file=sys.stderr)
                continue
            if argv[0] != "xdg-open":
                scope_pid = process.pid
        if both and self._can_place:
            self._pending = (before, scope_pid, action.files.name, PLACE_TRIES)
            self._placed = {}
            self._timer.start()

    def _test_run(self, command: str, base: Optional[Path]) -> None:
        from scripts import testrun

        # Security: "finish" deletes the tutorial copy - only notes inside a copy made by
        # scripts/testrun.py (marker in its root) may start it, and only after asking.
        root = testrun.copy_root(base) if base is not None else None
        if root is None:
            print(f"[PostFix] myos:{command} only works in a tutorial copy", file=sys.stderr)
            return
        if command == "comment":
            note = testrun.comment_note(base)
            argv = [sys.executable, str(self._repo_root / "PostFix" / "cli.py"), str(note)]
            self._start(argv)
            return
        confirmed, name = self.confirm_finish()
        if not confirmed:
            return
        env = dict(os.environ, MYOS_TUTORIAL_DIR=str(root))
        self._start([sys.executable, str(self._repo_root / "scripts" / "testrun.py"), "finish", "--name", name.strip()],
                    env=env)

    def _start(self, argv, **kwargs) -> None:
        try:
            self._popen(argv, cwd=str(self._repo_root), start_new_session=True, **kwargs)
        except OSError as error:
            print(f"[PostFix] could not start {argv[0]}: {error}", file=sys.stderr)

    def _ask_finish(self):
        name, confirmed = QInputDialog.getText(
            None, self.tr("Finished"),
            self.tr("Done with the tutorial? Your notes and comments are collected and the "
                    "computer is made ready for the next tester.\n\nYour name (optional):"),
            QLineEdit.Normal, "")
        return confirmed, name or ""

    def place_tick(self) -> None:
        """Once both new windows are there, Scope goes left and the file browser right."""
        if self._pending is None:
            self._timer.stop()
            return
        before, scope_pid, folder_name, tries = self._pending
        try:
            listing = self._run(["wmctrl", "-lp"], capture_output=True, text=True, timeout=2).stdout
        except (OSError, subprocess.SubprocessError):
            listing = ""
        scope, files = pick(new_windows(before, listing), scope_pid, folder_name)
        left, right = halves(self._screen())
        for key, wid, area in (("scope", scope, left), ("files", files, right)):
            if wid is None or key in self._placed:
                continue
            self._run(["wmctrl", "-i", "-r", wid, "-b", "remove,maximized_vert,maximized_horz"], timeout=2)
            self._run(["wmctrl", "-i", "-r", wid, "-e", "0,{},{},{},{}".format(*area)], timeout=2)
            self._placed[key] = wid
        tries -= 1
        if len(self._placed) == 2 or tries <= 0:
            self._pending = None
            self._timer.stop()
        else:
            self._pending = (before, scope_pid, folder_name, tries)


def _available_geometry() -> Tuple[int, int, int, int]:
    from PySide6.QtGui import QGuiApplication

    screen = QGuiApplication.primaryScreen()
    if screen is None:
        return (0, 0, 1280, 800)
    area = screen.availableGeometry()
    return (area.x(), area.y(), area.width(), area.height())
