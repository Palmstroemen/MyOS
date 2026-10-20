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


def test_acl_roles_from_inherited_templates_runtime_resolution():
    from core.acl import ACLPolicy

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "RootProject"
        child = root / "SubProject"
        root.mkdir(parents=True)
        child.mkdir(parents=True)

        _write_templates(root, "Standard", ["admin", "info", "kommunikation"])
        _write_project_config(root, "Standard")
        _write_acls(root)

        child_myos = child / ".MyOS"
        child_myos.mkdir(parents=True)
        (child_myos / "Project.md").write_text("# MyOS Project\n")

        policy = ACLPolicy.from_project(child)
        assert "admin" in policy.roles
        assert "info" in policy.roles
        assert "kommunikation" in policy.roles


def test_acl_finance_glob_patterns_and_default_deny():
    from core.acl import ACLPolicy, PermissionRule

    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"read", "write", "execute"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )

    assert policy.can_access("finance", "/Finanz", "read")
    assert policy.can_access("finance", "/Finanz/Q1", "write")
    assert policy.can_access("finance", "/Finanz/Reports/2026", "read")
    assert not policy.can_access("finance", "/HR", "read")
    assert not policy.can_access("finance", "/Finanzen", "read")
    assert not policy.can_access("finance", "/Finanz", "delete")


def _build_authorizer_fixture(backend: str):
    from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule

    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path="/Finanz/**", rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLAuthorizer(policy, backend=backend)


def test_acl_authorizer_auto_backend_available():
    authorizer = _build_authorizer_fixture("auto")
    assert authorizer.backend in {"legacy", "casbin"}
    assert authorizer.can_access("finance", "/Finanz/Q1", "read")


def test_acl_authorizer_legacy_user_checks():
    authorizer = _build_authorizer_fixture("legacy")
    assert authorizer.backend == "legacy"
    assert authorizer.can_user_access("bertha", "/Finanz/Q1", "read")
    assert not authorizer.can_user_access("bertha", "/HR", "read")
    assert authorizer.can_user_access("alfred", "/Admin", "execute")


def test_acl_authorizer_casbin_backend_parity_if_installed():
    import core.acl as acl_module

    if acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")

    legacy = _build_authorizer_fixture("legacy")
    casbin_auth = _build_authorizer_fixture("casbin")
    assert casbin_auth.backend == "casbin"

    checks = [
        ("finance", "/Finanz", "read"),
        ("finance", "/Finanz/2026/report", "write"),
        ("finance", "/Finanzen", "read"),
        ("admin", "/Any/Path", "delete"),
    ]
    for role, path, right in checks:
        assert casbin_auth.can_access(role, path, right) == legacy.can_access(role, path, right)

    user_checks = [
        ("bertha", "/Finanz/Q2", "read"),
        ("bertha", "/HR", "read"),
        ("alfred", "/whatever", "write"),
    ]
    for user, path, right in user_checks:
        assert casbin_auth.can_user_access(user, path, right) == legacy.can_user_access(user, path, right)


def test_template_role_gets_its_folder_with_original_case(tmp_path):
    """{Folder} expands to the template folder's real name; paths are case-sensitive."""
    from core.acl import ACLPolicy

    project_root = tmp_path / "Project"
    project_root.mkdir()
    _write_templates(project_root, "Standard", ["04_Finanz", "01_Info"])
    _write_project_config(project_root, "Standard")
    (project_root / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Folder\n- /{Folder}/: read, write\n"
    )

    policy = ACLPolicy.from_project(project_root)

    assert policy.can_access("04_finanz", "/04_Finanz", "write")
    assert not policy.can_access("04_finanz", "/01_Info", "read")


def test_display_names_keep_original_case(tmp_path):
    from core.acl import ACLPolicy

    project_root = tmp_path / "Project"
    project_root.mkdir()
    _write_templates(project_root, "Standard", ["04_Finanz"])
    _write_project_config(project_root, "Standard")
    (project_root / ".MyOS" / "ACLs.md").write_text(
        "# Permissions\n\n## Buchhaltung\n- /04_Finanz/: read\n\n# Users\nAnna: Buchhaltung\n"
    )

    policy = ACLPolicy.from_project(project_root)

    assert policy.display_name("anna") == "Anna"
    assert policy.display_name("buchhaltung") == "Buchhaltung"
    assert policy.display_name("04_finanz") == "04_Finanz"
    assert policy.display_name("unknown") == "unknown"


# --- Nearest rule per role wins (rights can be taken away in sub-folders) ---

def _nearest_policy():
    from core.acl import ACLPolicy, PermissionRule

    return ACLPolicy(
        roles={"team", "gl", "admin", "reader"},
        permissions={
            "team": [
                PermissionRule(path="/07_Arbeit", rights={"read", "write"}),
                PermissionRule(path="/07_Arbeit/Vertraulich", rights={"none"}),
            ],
            "gl": [PermissionRule(path="/07_Arbeit/Vertraulich", rights={"read", "write"})],
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "reader": [
                PermissionRule(path="/Archiv", rights={"read", "write"}),
                PermissionRule(path="/Archiv/Alt", rights={"read"}),
                PermissionRule(path="/Docs/**", rights={"read"}),
                PermissionRule(path="/Docs", rights={"write"}),
            ],
        },
        users={"anna": {"team"}, "karl": {"team", "gl"}},
    )


NEAREST_CHECKS = [
    # none at a sub-folder locks the role out there, the rest of the parent stays open
    ("team", "/07_Arbeit/Vertraulich", "read", False),
    ("team", "/07_Arbeit/Vertraulich/plan.md", "write", False),
    ("team", "/07_Arbeit/Projekt", "write", True),
    # roles not named at the sub-folder are unaffected
    ("gl", "/07_Arbeit/Vertraulich", "write", True),
    ("admin", "/07_Arbeit/Vertraulich", "read", True),
    # a deeper rule with fewer rights replaces the inherited ones
    ("reader", "/Archiv/Alt/x", "write", False),
    ("reader", "/Archiv/Alt/x", "read", True),
    ("reader", "/Archiv/Neu", "write", True),
    # rules written for the same folder (/Docs and /Docs/**) are combined
    ("reader", "/Docs/a", "read", True),
    ("reader", "/Docs/a", "write", True),
]


@pytest.mark.parametrize("role,path,right,expected", NEAREST_CHECKS)
def test_nearest_rule_per_role_wins(role, path, right, expected):
    assert _nearest_policy().can_access(role, path, right) is expected


def test_user_rights_are_the_union_of_their_roles():
    from core.acl import ACLAuthorizer

    authorizer = ACLAuthorizer(_nearest_policy(), backend="legacy")

    assert not authorizer.can_user_access("anna", "/07_Arbeit/Vertraulich", "read")
    assert authorizer.can_user_access("karl", "/07_Arbeit/Vertraulich", "read")


def test_nearest_rule_casbin_parity_if_installed():
    import core.acl as acl_module
    from core.acl import ACLAuthorizer

    if acl_module._casbin is None:
        pytest.skip("casbin not installed in test environment")

    casbin_auth = ACLAuthorizer(_nearest_policy(), backend="casbin")
    assert casbin_auth.backend == "casbin"
    for role, path, right, expected in NEAREST_CHECKS:
        assert casbin_auth.can_access(role, path, right) is expected, (role, path, right)
    assert not casbin_auth.can_user_access("anna", "/07_Arbeit/Vertraulich", "read")
    assert casbin_auth.can_user_access("karl", "/07_Arbeit/Vertraulich", "read")
