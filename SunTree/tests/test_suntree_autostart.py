"""SunTree starts hidden at login, ready for its shortcut (SunTree/install_autostart.py):
an autostart entry in $XDG_CONFIG_HOME/autostart, as Cinnamon and GNOME read it."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "install_autostart.py"


def _run(config, *args):
    env = {"XDG_CONFIG_HOME": str(config), "PATH": "/usr/bin:/bin", "HOME": str(config)}
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, capture_output=True, text=True)


def test_the_entry_starts_suntree_at_the_projects_root(tmp_path):
    root = tmp_path / "Meine Projekte"
    root.mkdir()
    config = tmp_path / "config"

    assert _run(config, str(root)).returncode == 0

    entry = (config / "autostart" / "myos-suntree.desktop").read_text(encoding="utf-8")
    exec_line = next(line for line in entry.splitlines() if line.startswith("Exec="))
    assert "SunTree.py" in exec_line and f'"{root}"' in exec_line  # quoted: the space
    assert "X-GNOME-Autostart-enabled=true" in entry and "Type=Application" in entry


def test_it_can_be_removed(tmp_path):
    root = tmp_path / "Projekte"
    root.mkdir()
    config = tmp_path / "config"
    _run(config, str(root))

    assert _run(config, "--remove").returncode == 0
    assert not (config / "autostart" / "myos-suntree.desktop").exists()


@pytest.mark.parametrize("name", [None, 'with"quote', "with$dollar"])
def test_only_an_existing_plain_folder(tmp_path, name):
    # None: a folder that does not exist; the others exist but the Exec line cannot hold them.
    bad = tmp_path / "does-not-exist" if name is None else tmp_path / name
    if name is not None:
        bad.mkdir()
    config = tmp_path / "config"
    result = _run(config, str(bad))
    assert result.returncode != 0
    assert not (config / "autostart" / "myos-suntree.desktop").exists()
