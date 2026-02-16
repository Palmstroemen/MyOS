from pathlib import Path

from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.acl_enforcement import ACLEnforcementService
from core.scope_api import ScopeApi


def _build_service(mode: str, root: Path) -> ACLEnforcementService:
    finance_rule = f"{(root / 'Finanz').resolve()}/**"
    policy = ACLPolicy(
        roles={"admin", "finance"},
        permissions={
            "admin": [PermissionRule(path="/*", rights={"*"})],
            "finance": [PermissionRule(path=finance_rule, rights={"read", "write"})],
        },
        users={"alfred": {"admin"}, "bertha": {"finance"}},
    )
    return ACLEnforcementService(ACLAuthorizer(policy, backend="legacy"), mode=mode)


def test_scope_api_enforce_blocks_create_folder_when_target_dir_denied(tmp_path):
    root = tmp_path / "lab"
    hr = root / "HR"
    hr.mkdir(parents=True)

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    created = api.create_folder(str(hr), "Private")

    assert created is None
    assert not (hr / "Private").exists()


def test_scope_api_enforce_blocks_create_note_when_target_dir_denied(tmp_path):
    root = tmp_path / "lab"
    hr = root / "HR"
    hr.mkdir(parents=True)

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    created = api.create_note(str(hr), "Roadmap")

    assert created is None
    assert not (hr / "Roadmap.md").exists()


def test_scope_api_enforce_allows_create_folder_and_note_when_allowed(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    finanz.mkdir(parents=True)

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    folder = api.create_folder(str(finanz), "Inbox")
    note = api.create_note(str(finanz), "Q1")

    assert folder is not None
    assert note is not None
    assert (finanz / "Inbox").exists()
    assert (finanz / "Q1.md").exists()
