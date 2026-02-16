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


def test_scope_api_enforce_filters_list_entries_to_allowed_paths(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    hr = root / "HR"
    root.mkdir()
    finanz.mkdir()
    hr.mkdir()
    (finanz / "budget.md").write_text("# b\n", encoding="utf-8")
    (hr / "people.md").write_text("# p\n", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    entries = api.list_entries(str(root))
    names = sorted(item["name"] for item in entries)

    assert names == ["Finanz"]


def test_scope_api_enforce_filters_list_children_to_allowed_paths(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    hr = root / "HR"
    root.mkdir()
    finanz.mkdir()
    hr.mkdir()

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    children = api.list_children(str(root))
    names = sorted(item["name"] for item in children)

    assert names == ["Finanz"]


def test_scope_api_monitor_keeps_unfiltered_read_lists(tmp_path):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    hr = root / "HR"
    root.mkdir()
    finanz.mkdir()
    hr.mkdir()

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("monitor", root), user="bertha")

    entries = api.list_entries(str(root))
    names = sorted(item["name"] for item in entries)

    assert names == ["Finanz", "HR"]
