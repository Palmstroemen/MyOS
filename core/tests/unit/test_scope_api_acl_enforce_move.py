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


def test_scope_api_enforce_blocks_move_entries_when_target_not_allowed(tmp_path):
    root = tmp_path / "lab"
    src_dir = root / "Finanz"
    dst_dir = root / "HR"
    src_dir.mkdir(parents=True)
    dst_dir.mkdir(parents=True)
    src = src_dir / "doc.txt"
    src.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    report = api.move_entries([str(src)], str(dst_dir))

    assert report["ok"] is False
    assert report["moved"] == []
    assert any(err["reason"] == "acl_denied_target" for err in report["errors"])
    assert src.exists()


def test_scope_api_enforce_blocks_move_entries_when_source_not_allowed(tmp_path):
    root = tmp_path / "lab"
    src_dir = root / "HR"
    dst_dir = root / "Finanz"
    src_dir.mkdir(parents=True)
    dst_dir.mkdir(parents=True)
    src = src_dir / "doc.txt"
    src.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    report = api.move_entries([str(src)], str(dst_dir))

    assert report["ok"] is False
    assert report["moved"] == []
    assert any(err["reason"] == "acl_denied_source" for err in report["errors"])
    assert src.exists()


def test_scope_api_enforce_allows_move_entries_when_permissions_match(tmp_path):
    root = tmp_path / "lab"
    src_dir = root / "Finanz" / "Inbox"
    dst_dir = root / "Finanz" / "Archive"
    src_dir.mkdir(parents=True)
    dst_dir.mkdir(parents=True)
    src = src_dir / "doc.txt"
    src.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    report = api.move_entries([str(src)], str(dst_dir))

    assert report["ok"] is True
    assert len(report["moved"]) == 1
    assert not src.exists()
    assert (dst_dir / "doc.txt").exists()


def test_scope_api_enforce_blocks_single_move_entry_on_acl_denied(tmp_path):
    root = tmp_path / "lab"
    src_dir = root / "HR"
    dst_dir = root / "Finanz"
    src_dir.mkdir(parents=True)
    dst_dir.mkdir(parents=True)
    src = src_dir / "single.txt"
    src.write_text("x", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    ok = api.move_entry(str(src), str(dst_dir))

    assert ok is False
    assert src.exists()
    assert not (dst_dir / "single.txt").exists()
