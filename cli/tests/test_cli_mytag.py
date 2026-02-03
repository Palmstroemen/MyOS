# cli/tests/test_cli_mytag.py

import subprocess
import sys
import tempfile
from pathlib import Path
import os

import pytest


def _run_cmd(args, cwd):
    script = Path(__file__).parent.parent.parent / "cli" / "mytag.py"
    return subprocess.run(
        [sys.executable, str(script)] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _skip_if_no_xattr():
    if not hasattr(os, "setxattr") or not hasattr(os, "getxattr"):
        pytest.skip("xattr not available on this platform")


def test_mytag_set_and_list():
    _skip_if_no_xattr()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        target = tmp / "file.txt"
        target.write_text("x")

        result = _run_cmd(["set", str(target), "wichtig=60"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "wichtig=60" in result.stdout


def test_mytag_add_remove_clear():
    _skip_if_no_xattr()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        target = tmp / "file.txt"
        target.write_text("x")

        result = _run_cmd(["add", str(target), "dringend"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "dringend" in result.stdout

        result = _run_cmd(["remove", str(target), "dringend"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "No tags" in result.stdout

        result = _run_cmd(["add", str(target), "foo"], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["clear", str(target)], cwd=tmpdir)
        assert result.returncode == 0

        result = _run_cmd(["list", str(target)], cwd=tmpdir)
        assert "No tags" in result.stdout
