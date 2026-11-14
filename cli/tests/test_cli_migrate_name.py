"""cli/migrate_name.py: the plan by default, changes only with --apply."""

import os
import subprocess
import sys
from pathlib import Path

from core.brand import CONFIG_DIR, ENV_PREFIX, LEGACY_ENV_PREFIXES, META_DIR

SCRIPT = Path(__file__).resolve().parents[2] / "cli" / "migrate_name.py"


def _run(tmp_path, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith((ENV_PREFIX, *LEGACY_ENV_PREFIXES))}
    env["XDG_CONFIG_HOME"] = str(tmp_path / "config")
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)


def _old_project(tmp_path, old):
    root = tmp_path / "Haus"
    (root / old).mkdir(parents=True)
    (root / old / "ACLs.md").write_text(f"- /{old}/ACLs.md: change\n", encoding="utf-8")
    return root


def test_plan_then_apply(tmp_path):
    old = "." + "MyOS"  # the former name the command knows
    if old == META_DIR:
        return  # before the rename there is nothing to move
    root = _old_project(tmp_path, old)
    plan = _run(tmp_path, str(root))
    assert plan.returncode == 0 and "rename" in plan.stdout and "--apply" in plan.stdout
    assert (root / old).is_dir()
    done = _run(tmp_path, "--apply", str(root))
    assert done.returncode == 0, done.stderr
    assert (root / META_DIR / "ACLs.md").read_text(encoding="utf-8") == f"- /{META_DIR}/ACLs.md: change\n"


def test_config_is_moved_with_config(tmp_path):
    old = "MyOS"
    if old == CONFIG_DIR:
        return
    (tmp_path / "config" / old).mkdir(parents=True)
    done = _run(tmp_path, "--apply", "--config")
    assert done.returncode == 0, done.stderr
    assert (tmp_path / "config" / CONFIG_DIR).is_dir()


def test_nothing_to_do(tmp_path):
    result = _run(tmp_path, str(tmp_path))
    assert result.returncode == 0 and "Nothing to move" in result.stdout


def test_a_conflict_fails(tmp_path):
    old = "." + "MyOS"
    if old == META_DIR:
        return
    root = _old_project(tmp_path, old)
    (root / META_DIR).mkdir()
    result = _run(tmp_path, "--apply", str(root))
    assert result.returncode == 1 and "conflict" in result.stdout
