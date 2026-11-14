"""CLI entrypoint for PostFix."""

import argparse
import signal
import sys
from pathlib import Path

# Started as a script (python3 PostFix/cli.py): make the repo root importable for
# `core`, as Scope/Scope.py does. As a module (python3 -m PostFix.main) it already is.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.brand import getenv

try:
    from .single_instance import InstanceServer, hand_over, server_name
except ImportError:
    from single_instance import InstanceServer, hand_over, server_name


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PostFix Markdown editor")
    parser.add_argument("path", nargs="?", help="Markdown file to open")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show YAML frontmatter in the editor",
    )
    parser.add_argument(
        "--embed-obsidian",
        action="store_true",
        help="Embed an existing Obsidian window into the editor area (X11 only)",
    )
    parser.add_argument("--obsidian-path", help="Path to Obsidian executable (if not in PATH)")
    parser.add_argument(
        "--obsidian-command",
        help="Advanced URI command name or id (requires Advanced URI plugin)",
    )
    parser.add_argument(
        "--obsidian-view",
        choices=["live", "source", "preview"],
        help="Open Obsidian in a specific view (requires Advanced URI plugin)",
    )
    parser.add_argument(
        "--obsidian-zen-hotkey",
        help="Send a zen-mode hotkey via xdotool (e.g. ctrl+shift+z)",
    )
    parser.add_argument(
        "--obsidian-zen-delay-ms",
        type=int,
        default=2500,
        help="Delay before sending zen hotkey (ms)",
    )
    parser.add_argument(
        "--obsidian-hotkey",
        action="append",
        help="Send additional hotkeys via xdotool (repeatable)",
    )
    parser.add_argument(
        "--obsidian-hotkey-gap-ms",
        type=int,
        default=300,
        help="Gap between additional hotkeys (ms)",
    )
    parser.add_argument(
        "--obsidian-close-hotkey",
        default="ctrl+shift+w",
        help="Hotkey to close Obsidian window on exit",
    )
    parser.add_argument(
        "--obsidian-vault",
        help="Vault name to open (uses obsidian://open?vault=...&file=...)",
    )
    parser.add_argument(
        "--obsidian-file",
        help="File path inside vault (relative, without extension if desired)",
    )
    parser.add_argument(
        "--obsidian-open-delay-ms",
        type=int,
        default=1500,
        help="Delay before opening file via URI (ms)",
    )
    parser.add_argument(
        "--obsidian-no-open",
        action="store_true",
        help="Do not open a file/vault via URI at startup",
    )
    parser.add_argument(
        "--obsidian-debug-window-search",
        action="store_true",
        help="Print window search output for embedding Obsidian",
    )
    parser.add_argument(
        "--obsidian-open-mode",
        choices=["window", "split", "tab"],
        help="Open mode for Advanced URI (requires plugin)",
    )
    parser.add_argument(
        "--obsidian-window-title",
        help="Prefer embedding window with this title fragment",
    )
    parser.add_argument(
        "--obsidian-close-other-windows",
        action="store_true",
        help="Close other Obsidian windows after embed (requires xdotool)",
    )
    parser.add_argument(
        "--obsidian-vault-path",
        help="Vault base path (used to compute vault name + file path)",
    )
    parser.add_argument(
        "--lang",
        choices=["de", "en"],
        default=getenv("UI_LANG", "de"),
        help="UI language (de or en)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    open_path = None
    if args.path:
        candidate = Path(args.path).expanduser()
        if candidate.suffix.lower() == ".md":
            open_path = candidate

    # One PostFix for all notes (single_instance.py): a later start hands its note over and ends
    # - before loading the rest of PostFix, which only the running one needs.
    single = getenv("POSTFIX_SINGLE", "1") != "0"
    if single and hand_over(server_name(), str(open_path.resolve()) if open_path else None):
        return 0

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    try:
        from .main import PostFixWindow
    except ImportError:
        from main import PostFixWindow

    app = QApplication(sys.argv)
    app.setApplicationName("PostFix")
    app.setOrganizationName("PostFixDev")
    icon_path = Path(__file__).with_name("icons").joinpath("postit.svg")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    def new_window(path):
        return PostFixWindow(
            open_path=path,
            debug=args.debug,
            embed_obsidian=args.embed_obsidian,
            obsidian_path=args.obsidian_path,
            obsidian_command=args.obsidian_command,
            obsidian_view=args.obsidian_view,
            zen_hotkey=args.obsidian_zen_hotkey,
            zen_delay_ms=args.obsidian_zen_delay_ms,
            obsidian_hotkeys=args.obsidian_hotkey,
            obsidian_hotkey_gap_ms=args.obsidian_hotkey_gap_ms,
            obsidian_close_hotkey=args.obsidian_close_hotkey,
            obsidian_vault=args.obsidian_vault,
            obsidian_file=args.obsidian_file,
            obsidian_open_delay_ms=args.obsidian_open_delay_ms,
            obsidian_no_open=args.obsidian_no_open,
            obsidian_debug_window_search=args.obsidian_debug_window_search,
            obsidian_open_mode=args.obsidian_open_mode,
            obsidian_window_title=args.obsidian_window_title,
            obsidian_close_other_windows=args.obsidian_close_other_windows,
            obsidian_vault_path=args.obsidian_vault_path,
            ui_language=args.lang,
        )

    windows = []

    def open_window(path):
        """A note in a window of its own - or, if it is open already, that window to the front."""
        target = Path(path).resolve() if path else None
        for window in windows:
            current = getattr(window.editor, "current_path", None)
            if target and current and Path(current).resolve() == target:
                window.showNormal()
                window.raise_()
                window.activateWindow()
                return window
        window = new_window(target)
        window.setAttribute(Qt.WA_DeleteOnClose)  # a closed note's window really goes
        windows.append(window)
        window.destroyed.connect(lambda _obj=None, w=window: windows.remove(w) if w in windows else None)
        window.show()
        print(f"[PostFix] opened {target}", file=sys.stderr, flush=True)
        return window

    # Asked to end (SIGTERM, e.g. "Bin fertig" on the test machine): close every note as the
    # user would - pending edits saved, the connection cleaned up - instead of dying mid-way.
    # Python only sees the signal while it runs; a quiet timer lets it run now and then.
    signal.signal(signal.SIGTERM, lambda *_: app.closeAllWindows())
    from PySide6.QtCore import QTimer

    signal_check = QTimer(app)
    signal_check.timeout.connect(lambda: None)
    signal_check.start(300)

    if single:  # this one is the PostFix now: it takes the notes of later starts
        server = InstanceServer(server_name(), app)
        server.listen()
        server.openRequested.connect(open_window)

    open_window(open_path)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
