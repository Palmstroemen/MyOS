# cli/tests/test_cli_myacl.py

import json
import os
import subprocess
import sys
from pathlib import Path

ACLS = (
    "# Permissions\n\n"
    "## Folder\n- /{Folder}/: read, write\n- /Info/: read\n\n"
    "## Admin\n- /*: read, write\n- /.MyOS/ACLs.md: read, write, change\n\n"
    "## Buchhaltung\n- /Finanz/: read, write, delete\n- /Finanz/Archiv/: read\n\n"
    "# Users\nOliver: Admin\nAnna: Buchhaltung\n"
)


def _run(args, tmp_path, **env):
    script = Path(__file__).parent.parent.parent / "cli" / "myacl.py"
    environ = {k: v for k, v in os.environ.items() if not k.startswith("MYOS_")}
    environ.update({"XDG_CONFIG_HOME": str(tmp_path / "config"), **env})
    return subprocess.run(
        [sys.executable, str(script)] + args, capture_output=True, text=True, cwd=tmp_path, env=environ
    )


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (path / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    for folder in ("Finanz", "Info"):
        (path / folder).mkdir()
    return path


def _setup(tmp_path: Path) -> Path:
    root = _project(tmp_path / "Projekte")
    for folder in ("Finanz", "Info"):
        (root / "Templates" / "Standard" / folder).mkdir(parents=True)
    (root / "Finanz" / "Archiv").mkdir()
    _project(root / "Familie")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    return root


def _line(output: str, start: str) -> str:
    return next(line for line in output.splitlines() if line.strip().startswith(start))


def test_show_lists_who_may_what_and_where_it_comes_from(tmp_path):
    root = _setup(tmp_path)

    result = _run(["show", str(root / "Finanz" / "Archiv")], tmp_path)

    assert result.returncode == 0, result.stderr
    assert "/Finanz/Archiv" in result.stdout
    assert "read" in _line(result.stdout, "Buchhaltung") and "here" in _line(result.stdout, "Buchhaltung")
    assert "write" not in _line(result.stdout, "Buchhaltung")
    assert "read, write" in _line(result.stdout, "Admin") and "from /" in _line(result.stdout, "Admin")
    assert "Buchhaltung" in _line(result.stdout, "Anna")


def test_show_outside_any_acls_says_so(tmp_path):
    root = _project(tmp_path / "Ohne")

    result = _run(["show", str(root)], tmp_path)

    assert result.returncode == 0
    assert "No ACLs.md" in result.stdout


def test_check_answers_with_the_exit_code(tmp_path):
    root = _setup(tmp_path)

    allowed = _run(["check", "Anna", str(root / "Finanz"), "delete"], tmp_path)
    denied = _run(["check", "Anna", str(root / "Finanz" / "Archiv"), "write"], tmp_path)

    assert allowed.returncode == 0 and "yes" in allowed.stdout
    assert denied.returncode == 1 and "no" in denied.stdout


def test_check_without_a_right_lists_the_rights(tmp_path):
    root = _setup(tmp_path)

    result = _run(["check", "anna", str(root / "Finanz")], tmp_path)

    assert result.returncode == 0
    assert result.stdout.strip() == "read, write, delete"


def test_rules_as_json_resolve_the_folder_rules_into_subprojects(tmp_path):
    root = _setup(tmp_path)

    result = _run(["rules", str(root), "--json"], tmp_path)

    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["project"] == str(root.resolve())
    assert data["roles"]["Finanz"]["/Familie/Finanz"] == ["read", "write"]
    assert data["roles"]["Admin"]["/*"] == ["read", "write"]  # paths as written in ACLs.md
    assert data["users"]["Anna"] == ["Buchhaltung"]


def test_rules_as_text_list_role_path_and_rights(tmp_path):
    root = _setup(tmp_path)

    result = _run(["rules", str(root)], tmp_path)

    assert result.returncode == 0
    assert ["Buchhaltung", "/Finanz/Archiv", "read"] in [line.split() for line in result.stdout.splitlines()]


def test_with_enforcement_only_who_may_read_the_acls_sees_them(tmp_path):
    root = _setup(tmp_path)

    anna = _run(["show", str(root / "Finanz")], tmp_path, MYOS_ACL_MODE="enforce", MYOS_ACL_USER="anna")
    oliver = _run(["show", str(root / "Finanz")], tmp_path, MYOS_ACL_MODE="enforce", MYOS_ACL_USER="oliver")

    assert anna.returncode == 2 and "may not see" in anna.stderr
    assert oliver.returncode == 0 and "Buchhaltung" in oliver.stdout


def _nextcloud_md(root: Path) -> None:
    (root / ".MyOS" / "Nextcloud.md").write_text(
        "# Nextcloud\nurl: http://localhost:8081\nfolder: Projekte\ngroup: Projekte\n\n# Accounts\nOliver: oliver\nAnna: anna\n"
    )


def test_sync_plan_shows_the_nextcloud_rules(tmp_path):
    root = _setup(tmp_path)
    _nextcloud_md(root)

    result = _run(["sync", "--plan", str(root)], tmp_path)

    assert result.returncode == 0, result.stderr
    rows = [line.split(None, 3) for line in result.stdout.splitlines()]
    assert ["/", "group", "Projekte", "-"] in rows
    assert ["/", "user", "oliver", "read, write, create"] in rows
    assert ["/Finanz", "user", "anna", "read, write, create, delete"] in rows
    assert "change is not copied" in result.stdout


def test_sync_plan_as_json(tmp_path):
    root = _setup(tmp_path)
    _nextcloud_md(root)

    data = json.loads(_run(["sync", "--plan", "--json", str(root)], tmp_path).stdout)

    assert {"path": "/Finanz/Archiv", "kind": "user", "account": "anna", "allowed": ["read"]} in data["rules"]
    assert data["notes"]


def test_sync_without_nextcloud_md_explains_what_is_missing(tmp_path):
    root = _setup(tmp_path)

    result = _run(["sync", "--plan", str(root)], tmp_path)

    assert result.returncode == 2 and "Nextcloud.md" in result.stderr


def test_sync_without_plan_is_not_there_yet(tmp_path):
    root = _setup(tmp_path)
    _nextcloud_md(root)

    result = _run(["sync", str(root)], tmp_path)

    assert result.returncode == 2 and "--plan" in result.stderr


def test_dry_run_needs_the_login_from_the_environment(tmp_path):
    root = _setup(tmp_path)
    _nextcloud_md(root)

    result = _run(["sync", "--dry-run", str(root)], tmp_path)

    assert result.returncode == 2 and "MYOS_NEXTCLOUD_USER" in result.stderr


def test_dry_run_needs_url_and_folder(tmp_path):
    root = _setup(tmp_path)
    (root / ".MyOS" / "Nextcloud.md").write_text("# Accounts\nAnna: anna\n")

    result = _run(["sync", "--dry-run", str(root)], tmp_path, MYOS_NEXTCLOUD_USER="oliver", MYOS_NEXTCLOUD_PASSWORD="x")

    assert result.returncode == 2 and "url" in result.stderr and "folder" in result.stderr
