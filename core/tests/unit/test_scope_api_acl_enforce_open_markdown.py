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


def test_scope_api_enforce_blocks_open_markdown_when_read_denied(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    hr = root / "HR"
    hr.mkdir(parents=True)
    note = hr / "note.md"
    note.write_text("# note\n", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    called = {"n": 0}

    def _fake_run(*args, **kwargs):
        called["n"] += 1
        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr("core.scope_api.subprocess.run", _fake_run)

    ok = api.open_markdown(str(note))

    assert ok is False
    assert called["n"] == 0


def test_scope_api_enforce_allows_open_markdown_when_read_allowed(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    finanz = root / "Finanz"
    finanz.mkdir(parents=True)
    note = finanz / "report.md"
    note.write_text("# report\n", encoding="utf-8")

    api = ScopeApi(str(root))
    api.set_acl_enforcement(_build_service("enforce", root), user="bertha")

    called = {"n": 0}

    def _fake_run(*args, **kwargs):
        called["n"] += 1
        class _R:
            returncode = 0
        return _R()

    monkeypatch.setattr("core.scope_api.subprocess.run", _fake_run)

    ok = api.open_markdown(str(note))

    assert ok is True
    assert called["n"] == 1
