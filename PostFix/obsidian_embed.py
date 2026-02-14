"""Obsidian window embedding widget for PostFix."""

import shlex
import shutil
import subprocess
import urllib.parse
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QWindow


class ObsidianEmbed(QWidget):
    """Embed an external Obsidian window inside the editor area."""

    def __init__(
        self,
        open_path: Path | None = None,
        obsidian_path: str | None = None,
        obsidian_command: str | None = None,
        obsidian_view: str | None = None,
        zen_hotkey: str | None = None,
        zen_delay_ms: int = 2500,
        hotkeys: list[str] | None = None,
        hotkey_gap_ms: int = 300,
        close_hotkey: str | None = "ctrl+shift+w",
        obsidian_vault: str | None = None,
        obsidian_file: str | None = None,
        open_delay_ms: int = 1500,
        no_open: bool = False,
        debug_window_search: bool = False,
        open_mode: str | None = None,
        window_title: str | None = None,
        close_other_windows: bool = False,
        obsidian_vault_path: str | None = None,
    ):
        super().__init__()
        self.current_bg = "#ffffff"
        self.current_path = open_path
        self._obsidian_cmd = self._resolve_obsidian_command(obsidian_path)
        self._obsidian_command = obsidian_command
        self._obsidian_view = obsidian_view
        self._zen_hotkey = zen_hotkey
        self._zen_delay_ms = zen_delay_ms
        self._hotkeys = hotkeys or []
        self._hotkey_gap_ms = hotkey_gap_ms
        self._close_hotkey = close_hotkey
        self._obsidian_vault = obsidian_vault
        self._obsidian_file = obsidian_file
        self._obsidian_vault_path = obsidian_vault_path
        self._open_delay_ms = open_delay_ms
        self._no_open = no_open
        self._debug_window_search = debug_window_search
        self._open_mode = open_mode
        self._window_title = window_title
        self._close_other_windows = close_other_windows
        self._last_win_id = None
        self._debug_printed = False
        self._watch_timer = QTimer(self)
        self._watch_timer.setInterval(1000)
        self._watch_timer.timeout.connect(self._watch_embedded_window)
        self._can_find_window = bool(
            shutil.which("xdotool") or shutil.which("wmctrl") or shutil.which("xwininfo")
        )
        self._container = None
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(500)
        self._poll_timer.timeout.connect(self._try_embed)
        self._poll_attempts = 0
        self._max_attempts = 60

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._status = QLabel("Starting Obsidian...")
        self._status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("QWidget { background-color: #ffffff; } QLabel { color: #333333; }")

        if not self._obsidian_cmd:
            self._status.setText("Obsidian not found in PATH. Install or provide --obsidian-path.")
            return

        self._launch_obsidian()
        if not self._can_find_window:
            self._status.setText("Install xdotool, wmctrl, or use xwininfo to embed Obsidian.")
            return
        self._poll_timer.start()

    def _launch_obsidian(self):
        try:
            subprocess.Popen(self._obsidian_cmd)
        except OSError:
            self._status.setText("Failed to start Obsidian.")
            return
        if not self._no_open:
            uri = self._build_open_uri()
            if uri:
                QTimer.singleShot(self._open_delay_ms, lambda: subprocess.Popen(["xdg-open", uri]))
        if self._obsidian_command or self._obsidian_view:
            QTimer.singleShot(2500, self._send_advanced_uri)

    def _try_embed(self):
        self._poll_attempts += 1
        require_title = bool(self._window_title)
        win_id = self._find_obsidian_window_id(require_title=require_title)
        if win_id:
            self._poll_timer.stop()
            self._last_win_id = win_id
            self._embed_window(win_id)
            self._watch_timer.start()
            if self._close_other_windows:
                QTimer.singleShot(self._zen_delay_ms, self._close_other_obsidian_windows)
            if self._zen_hotkey:
                QTimer.singleShot(self._zen_delay_ms, self._send_zen_hotkey)
            if self._hotkeys and self.current_path:
                QTimer.singleShot(self._zen_delay_ms, self._send_hotkeys)
            return
        if self._poll_attempts >= self._max_attempts:
            self._poll_timer.stop()
            self._status.setText("Unable to find Obsidian window. Install xdotool or wmctrl.")

    def _find_obsidian_window_id(self, require_title: bool = False) -> int | None:
        if shutil.which("xdotool"):
            for args in (["--classname", "obsidian"], ["--name", "Obsidian"]):
                result = subprocess.run(
                    ["xdotool", "search", "--onlyvisible", *args],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if self._debug_window_search and not self._debug_printed:
                    print(f"[ObsidianEmbed] xdotool search {args}: {result.stdout.strip()}")
                if result.stdout.strip():
                    line = result.stdout.strip().splitlines()[0]
                    try:
                        return int(line, 0)
                    except ValueError:
                        return None
        if shutil.which("wmctrl"):
            result = subprocess.run(["wmctrl", "-lx"], capture_output=True, text=True, check=False)
            if self._debug_window_search and not self._debug_printed:
                print("[ObsidianEmbed] wmctrl -lx output:")
                print(result.stdout)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) < 3:
                    continue
                win_id, wm_class = parts[0], parts[2]
                if "obsidian" in wm_class.lower():
                    try:
                        return int(win_id, 16)
                    except ValueError:
                        return None
        if shutil.which("xwininfo"):
            candidates: list[tuple[int, int, str]] = []
            if self._debug_window_search and not self._debug_printed:
                tree = subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True, check=False)
                print("[ObsidianEmbed] xwininfo -root -tree matches:")
                for line in tree.stdout.splitlines():
                    if "Obsidian" in line or "obsidian" in line:
                        print(line.strip())
            tree = subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True, check=False)
            for line in tree.stdout.splitlines():
                line = line.strip()
                if not line.startswith("0x"):
                    continue
                if "Obsidian" not in line and "obsidian" not in line:
                    continue
                parts = line.split()
                if not parts:
                    continue
                try:
                    win_id = int(parts[0], 16)
                except ValueError:
                    continue
                if "InputOnly" in line or "20x20" in line:
                    continue
                size = self._parse_window_size(line)
                title = self._parse_window_title(line)
                candidates.append((size, win_id, title))
            if self._window_title:
                title_lower = self._window_title.lower()
                for _, win_id, title in sorted(candidates, reverse=True):
                    if title_lower in title.lower():
                        return win_id
                if require_title:
                    return None
            for _, win_id, _ in sorted(candidates, reverse=True):
                if self._is_window_mapped(win_id):
                    return win_id
            if candidates:
                return sorted(candidates, reverse=True)[0][1]
            for name in ("Obsidian", "obsidian"):
                result = subprocess.run(["xwininfo", "-name", name], capture_output=True, text=True, check=False)
                if self._debug_window_search and not self._debug_printed:
                    print(f"[ObsidianEmbed] xwininfo -name {name}: {result.stdout.strip()}")
                for line in result.stdout.splitlines():
                    if "Window id:" not in line:
                        continue
                    parts = line.strip().split()
                    try:
                        win_id = parts[2]
                        parsed_id = int(win_id, 16)
                    except (IndexError, ValueError):
                        continue
                    if self._window_title and require_title:
                        continue
                    if self._is_window_mapped(parsed_id):
                        return parsed_id
                    return parsed_id
            if self._debug_window_search and not self._debug_printed:
                self._debug_printed = True
        return None

    def _is_window_mapped(self, win_id: int) -> bool:
        if not shutil.which("xwininfo"):
            return True
        result = subprocess.run(["xwininfo", "-id", hex(win_id)], capture_output=True, text=True, check=False)
        for line in result.stdout.splitlines():
            if "Map State:" in line:
                return "IsViewable" in line
        return False

    def _parse_window_size(self, line: str) -> int:
        for token in line.split():
            if "x" in token and "+" in token:
                size = token.split("+", 1)[0]
                try:
                    width, height = size.split("x", 1)
                    return int(width) * int(height)
                except ValueError:
                    continue
        return 0

    def _parse_window_title(self, line: str) -> str:
        if "\"" not in line:
            return ""
        parts = line.split("\"", 2)
        if len(parts) < 2:
            return ""
        return parts[1]

    def _close_other_obsidian_windows(self):
        if not shutil.which("xdotool") or not shutil.which("xwininfo"):
            return
        target_fragment = (self._window_title or "").lower()
        tree = subprocess.run(["xwininfo", "-root", "-tree"], capture_output=True, text=True, check=False)
        for line in tree.stdout.splitlines():
            line = line.strip()
            if not line.startswith("0x"):
                continue
            if "Obsidian" not in line and "obsidian" not in line:
                continue
            win_id = line.split()[0]
            title = self._parse_window_title(line).lower()
            if target_fragment and target_fragment in title:
                continue
            if self._last_win_id and win_id == hex(self._last_win_id):
                continue
            subprocess.run(["xdotool", "windowactivate", "--sync", win_id, "key", "ctrl+shift+w"], check=False)

    def _send_advanced_uri(self):
        params = {}
        if self.current_path:
            params["filepath"] = str(self.current_path)
        if self._obsidian_view:
            params["view"] = self._obsidian_view
        if self._obsidian_command:
            params["commandid"] = self._obsidian_command
        query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        uri = f"obsidian://advanced-uri?{query}"
        subprocess.Popen(["xdg-open", uri])

    def _build_open_uri(self) -> str | None:
        vault_info = self._resolve_vault_info()
        vault_name = vault_info.get("vault")
        vault_file = vault_info.get("file")
        if self._obsidian_command or self._obsidian_view or self._open_mode:
            params = {}
            if vault_name and vault_file:
                params["vault"] = vault_name
                params["file"] = vault_file
            elif self.current_path:
                params["filepath"] = str(self.current_path)
            if self._obsidian_view:
                params["view"] = self._obsidian_view
            if self._obsidian_command:
                params["commandid"] = self._obsidian_command
            if self._open_mode:
                params["openmode"] = self._open_mode
            if params:
                query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                return f"obsidian://advanced-uri?{query}"
        if vault_name and vault_file:
            vault = urllib.parse.quote(vault_name)
            file_path = urllib.parse.quote(vault_file)
            return f"obsidian://open?vault={vault}&file={file_path}"
        if self.current_path:
            path = urllib.parse.quote(str(self.current_path))
            return f"obsidian://open?path={path}"
        return None

    def _resolve_vault_info(self) -> dict:
        if self._obsidian_vault and self._obsidian_file:
            return {"vault": self._obsidian_vault, "file": self._obsidian_file}
        if self._obsidian_vault_path and self.current_path:
            vault_path = Path(self._obsidian_vault_path).expanduser().resolve()
            try:
                rel_path = self.current_path.resolve().relative_to(vault_path)
            except ValueError:
                return {}
            return {"vault": vault_path.name, "file": rel_path.as_posix()}
        return {}

    def _watch_embedded_window(self):
        if not self._last_win_id:
            return
        if self._is_window_mapped(self._last_win_id):
            return
        self._watch_timer.stop()
        if self._container:
            self._container.setVisible(False)
        self._status.setText("Obsidian window lost. Waiting to re-attach...")
        self._status.show()
        self._last_win_id = None
        if not self._poll_timer.isActive():
            self._poll_timer.start()

    def _send_zen_hotkey(self):
        if not self._last_win_id:
            return
        if shutil.which("xdotool"):
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", str(self._last_win_id), "key", self._zen_hotkey],
                check=False,
            )

    def _send_hotkeys(self):
        if not self._last_win_id or not shutil.which("xdotool"):
            return
        for idx, hotkey in enumerate(self._hotkeys):
            delay = idx * self._hotkey_gap_ms
            QTimer.singleShot(
                delay,
                lambda hk=hotkey: subprocess.run(
                    ["xdotool", "windowactivate", "--sync", str(self._last_win_id), "key", hk],
                    check=False,
                ),
            )

    def send_close_hotkey(self):
        if not self._last_win_id or not self._close_hotkey:
            return
        if shutil.which("xdotool"):
            subprocess.run(
                ["xdotool", "windowactivate", "--sync", str(self._last_win_id), "key", self._close_hotkey],
                check=False,
            )

    def _resolve_obsidian_command(self, obsidian_path: str | None) -> list[str] | None:
        if obsidian_path:
            return shlex.split(obsidian_path)
        found = shutil.which("obsidian")
        if not found:
            return None
        return [found]

    def _embed_window(self, win_id: int):
        window = QWindow.fromWinId(win_id)
        if not window:
            self._status.setText("Failed to attach to Obsidian window.")
            return
        self._container = QWidget.createWindowContainer(window, self)
        self.layout().addWidget(self._container)
        self._status.hide()

    def set_view_mode(self, mode: str):
        return

    def apply_background(self, color_hex: str):
        return

    def wrap_selection(self, *args, **kwargs):
        return

    def update_window_metadata(self, *args, **kwargs):
        return

    def get_markdown(self) -> str:
        if self.current_path and self.current_path.exists():
            return self.current_path.read_text(encoding="utf-8")
        return ""

    def set_path(self, path: Path):
        self.current_path = path
