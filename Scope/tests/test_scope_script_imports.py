"""Scope.py started as a script (python3 Scope/Scope.py) finds its modules.

As a script, Scope/ comes first on sys.path, and the name "Scope" means Scope.py, not
the folder: an import like "from Scope.x import ..." fails there. This once kept Scope
from ever reaching its perspective daemon, unnoticed behind an except.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_PROBE = """
import runpy, sys
sys.path.insert(0, {scope_dir!r})  # as for "python3 Scope/Scope.py"
names = runpy.run_path({script!r}, run_name="scope_probe")
from daemon.client import connect
assert names["connect_daemon"] is connect, names["connect_daemon"]
print("ok")
"""


def test_scope_script_reaches_the_daemon_client():
    scope_dir = REPO_ROOT / "Scope"
    probe = _PROBE.format(scope_dir=str(scope_dir), script=str(scope_dir / "Scope.py"))
    done = subprocess.run([sys.executable, "-c", probe], cwd=str(scope_dir),
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().endswith("ok")
