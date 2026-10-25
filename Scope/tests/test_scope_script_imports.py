"""Scope.py and SunTree.py started as scripts (python3 Scope/Scope.py) find their modules.

As a script, Scope/ comes first on sys.path, and the name "Scope" means Scope.py, not
the folder: an import like "from Scope.x import ..." fails there. This once kept Scope
from ever reaching its perspective daemon, unnoticed behind an except.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_PROBE = """
import runpy, sys
sys.path.insert(0, {scope_dir!r})  # as for "python3 Scope/Scope.py"
names = runpy.run_path({script!r}, run_name="scope_probe")
from daemon.lens_link import LensLink
assert names["LensLink"] is LensLink, names["LensLink"]
print("ok")
"""


@pytest.mark.parametrize("program", ["Scope/Scope.py", "SunTree/SunTree.py"])
def test_the_script_reaches_the_lens(program):
    # SunTree shares the lens with Scope (Designdocument Perspective Resolver MVP.md, A6).
    script = REPO_ROOT / program
    probe = _PROBE.format(scope_dir=str(script.parent), script=str(script))
    done = subprocess.run([sys.executable, "-c", probe], cwd=str(script.parent),
                          capture_output=True, text=True, timeout=60)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip().endswith("ok")
