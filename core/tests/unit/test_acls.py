import tempfile
from pathlib import Path

import pytest


def _write_templates(project_root: Path, template_name: str, folders: list[str]) -> None:
    templates_root = project_root / "Templates" / template_name
    templates_root.mkdir(parents=True, exist_ok=True)
    for folder in folders:
        (templates_root / folder).mkdir(parents=True, exist_ok=True)


def _write_project_config(project_root: Path, template_name: str) -> None:
    myos_dir = project_root / ".MyOS"
    myos_dir.mkdir(parents=True, exist_ok=True)
    (myos_dir / "Project.md").write_text("# MyOS Project\n")
    (myos_dir / "Templates.md").write_text(f"# Templates\n{template_name}\n")


def _write_acls(project_root: Path) -> None:
    myos_dir = project_root / ".MyOS"
    (myos_dir / "ACLs.md").write_text(
        "# Permissions\n"
        "\n"
        "## Folder\n"
        "- /{Folder}/: read, write\n"
        "- /info/: read\n"
        "\n"
        "## Admin\n"
        "- /*: read, write, execute\n"
        "- /.MyOS/ACLs.md: change\n"
        "\n"
        "## Worker\n"
        "- /info/: read\n"
        "- /kommunikation/: read\n"
        "\n"
        "# Users\n"
        "Oliver: Admin, Worker\n"
        "Mia: Worker\n"
    )


def test_acl_roles_from_template_and_custom_roles():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert "admin" in policy.roles
        assert "info" in policy.roles
        assert "kommunikation" in policy.roles
        assert "worker" in policy.roles


def test_acl_permissions_basic_checks():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert policy.can_access("worker", "/info", "read")
        assert not policy.can_access("worker", "/info", "write")
        assert policy.can_access("worker", "/kommunikation/extern", "read")
        assert not policy.can_access("worker", "/admin")

        assert policy.can_access("admin", "/admin", "read")
        assert policy.can_access("admin", "/any/other/path", "write")
        assert not policy.can_access("admin", "/any/other/path", "change")
        assert policy.can_access("admin", "/.MyOS/ACLs.md", "change")

        assert policy.can_access("info", "/info", "write")
        assert policy.can_access("kommunikation", "/kommunikation", "read")


def test_acl_users_role_mapping():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "Project"
        project_root.mkdir(parents=True)

        _write_templates(project_root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(project_root, "Standard")
        _write_acls(project_root)

        policy = ACLPolicy.from_project(project_root)

        assert policy.roles_for_user("Oliver") == {"admin", "worker"}
        assert policy.roles_for_user("mia") == {"worker"}
        assert policy.roles_for_user("Unknown") == set()
