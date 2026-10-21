"""GNOME family desktop backend (Cinnamon, GNOME) via gsettings, and backend selection.

subprocess is always faked: tests must never change the real desktop."""

import subprocess
from pathlib import Path

import pytest

from core.desk import DeskConfig
from core.desktop_backends import build_backend, detect_backend_name
from core.desktop_backends.base import DesktopState


def _config(tmp_path: Path, **values) -> DeskConfig:
    data = {"Desk": {key: [value] for key, value in values.items()}}
    return DeskConfig.from_data(tmp_path / ".MyOS" / "Desk.md", data)


class FakeGsettings:
    """Records gsettings calls and answers "get" from a dict of (schema, key) -> output."""

    def __init__(self, values=None, returncode=0):
        self.values = dict(values or {})
        self.calls = []
        self.returncode = returncode

    def run(self, argv, **kwargs):
        self.calls.append(list(argv))
        if argv[1] == "get":
            out = self.values.get((argv[2], argv[3]))
            if out is None:
                return subprocess.CompletedProcess(argv, 1, "", "No such key")
            return subprocess.CompletedProcess(argv, 0, out, "")
        return subprocess.CompletedProcess(argv, self.returncode, "", "")


@pytest.fixture
def gsettings(monkeypatch):
    fake = FakeGsettings()
    monkeypatch.setattr("core.desktop_backends.command.subprocess.run", fake.run)
    monkeypatch.setattr("core.desktop_backends.command.shutil.which", lambda name: "/usr/bin/" + name)
    return fake


@pytest.mark.parametrize("desktop, expected", [
    ("X-Cinnamon", "cinnamon"),
    ("Cinnamon", "cinnamon"),
    ("ubuntu:GNOME", "gnome"),
    ("GNOME", "gnome"),
    ("KDE", "kde"),
    ("XFCE", "none"),
    ("", "none"),
])
def test_auto_detects_the_running_desktop(monkeypatch, desktop, expected):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", desktop)
    assert detect_backend_name() == expected
    monkeypatch.setenv("MYOS_DESK_BACKEND", "auto")
    assert build_backend("auto").name == expected


def test_cinnamon_sets_wallpaper_as_file_uri(gsettings, tmp_path):
    picture = tmp_path / "Garten Bild.jpg"
    picture.write_bytes(b"x")
    backend = build_backend("cinnamon")

    result = backend.apply_wallpaper(_config(tmp_path, wallpaperpath=str(picture)), dry_run=False)

    assert result.ok, result.message
    uri = picture.as_uri()
    assert gsettings.calls == [["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", f"'{uri}'"]]


def test_gnome_sets_light_and_dark_wallpaper(gsettings, tmp_path):
    picture = tmp_path / "bild.png"
    picture.write_bytes(b"x")
    gsettings.values[("org.gnome.desktop.background", "picture-uri-dark")] = "'file:///old.png'\n"
    backend = build_backend("gnome")

    assert backend.apply_wallpaper(_config(tmp_path, wallpaperpath=str(picture)), dry_run=False).ok

    sets = [c for c in gsettings.calls if c[1] == "set"]
    assert [c[3] for c in sets] == ["picture-uri", "picture-uri-dark"]


def test_cinnamon_sets_the_theme(gsettings, tmp_path):
    backend = build_backend("cinnamon")

    assert backend.apply_theme(_config(tmp_path, themepreset="Mint-Y-Dark-Aqua"), dry_run=False).ok

    assert gsettings.calls == [["gsettings", "set", "org.cinnamon.desktop.interface", "gtk-theme", "'Mint-Y-Dark-Aqua'"]]


@pytest.mark.parametrize("preset", ["-a", "--help", "Dark'; rm", "a\nb", "x" * 200])
def test_unsafe_theme_names_are_refused_without_running_anything(gsettings, tmp_path, preset):
    backend = build_backend("cinnamon")

    result = backend.apply_theme(_config(tmp_path, themepreset=preset), dry_run=False)

    assert result.ok is False
    assert gsettings.calls == []


def test_capture_reads_theme_and_wallpaper_as_plain_path(gsettings):
    gsettings.values.update({
        ("org.cinnamon.desktop.interface", "gtk-theme"): "'Mint-L-Darker-Aqua'\n",
        ("org.cinnamon.desktop.background", "picture-uri"): "'file:///usr/share/backgrounds/Mein%20Bild.jpg'\n",
    })

    state = build_backend("cinnamon").capture()

    assert state == DesktopState(theme="Mint-L-Darker-Aqua", wallpaper="/usr/share/backgrounds/Mein Bild.jpg")


def test_capture_without_gsettings_gives_nothing(monkeypatch):
    monkeypatch.setattr("core.desktop_backends.command.shutil.which", lambda name: None)

    assert build_backend("cinnamon").capture() is None


def test_dry_run_and_failures(gsettings, tmp_path):
    backend = build_backend("cinnamon")
    assert backend.apply_theme(_config(tmp_path, themepreset="Adwaita"), dry_run=True).ok
    assert gsettings.calls == []

    gsettings.returncode = 1
    assert backend.apply_theme(_config(tmp_path, themepreset="Adwaita"), dry_run=False).ok is False


def test_cinnamon_sets_and_reads_the_panel_theme(gsettings, tmp_path):
    backend = build_backend("cinnamon")

    assert backend.apply_panel_theme(_config(tmp_path, paneltheme="Mint-Y-Dark-Red"), dry_run=False).ok
    assert gsettings.calls == [["gsettings", "set", "org.cinnamon.theme", "name", "'Mint-Y-Dark-Red'"]]

    gsettings.values[("org.cinnamon.theme", "name")] = "'Linux Mint'\n"
    assert backend.capture().panel_theme == "Linux Mint"


def test_panel_theme_names_are_checked_and_gnome_skips_it(gsettings, tmp_path):
    assert build_backend("cinnamon").apply_panel_theme(_config(tmp_path, paneltheme="-x"), dry_run=False).ok is False
    result = build_backend("gnome").apply_panel_theme(_config(tmp_path, paneltheme="Mint-Y"), dry_run=False)
    assert result.ok is True and "not supported" in result.message
    assert gsettings.calls == []
