"""PostFix starts as a script (python3 PostFix/cli.py, PostFix/main.py) from any directory."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

POSTFIX = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script", ["cli.py", "main.py"])
def test_script_start_finds_core(script, tmp_path):
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env["QT_QPA_PLATFORM"] = "offscreen"

    result = subprocess.run(
        [sys.executable, str(POSTFIX / script), "--help"],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "PostFix" in result.stdout
