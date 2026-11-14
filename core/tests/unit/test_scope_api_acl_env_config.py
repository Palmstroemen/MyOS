from pathlib import Path

from core.acl import ACLAuthorizer, ACLPolicy, PermissionRule
from core.scope_api import ScopeApi
from core.brand import META_DIR, env_name


def _stub_authorizer(backend: str = "legacy") -> ACLAuthorizer:
    policy = ACLPolicy(
        roles={"admin"},
        permissions={"admin": [PermissionRule(path="/*", rights={"*"})]},
        users={"local": {"admin"}},
    )
    return ACLAuthorizer(policy, backend=backend)


def test_scope_api_default_acl_mode_is_off(monkeypatch, tmp_path):
    monkeypatch.delenv(env_name("ACL_MODE"), raising=False)
    monkeypatch.delenv(env_name("ACL_AUDIT"), raising=False)
    monkeypatch.delenv(env_name("ACL_AUDIT_FILE"), raising=False)

    api = ScopeApi(str(tmp_path))

    assert api._acl_enforcement is None
    assert api._acl_audit_file is None


def test_scope_api_acl_mode_monitor_enables_service_from_env(monkeypatch, tmp_path):
    monkeypatch.setenv(env_name("ACL_MODE"), "monitor")
    monkeypatch.setenv(env_name("ACL_BACKEND"), "legacy")

    monkeypatch.setattr(
        "core.scope_api.ACLAuthorizer.from_project",
        classmethod(lambda cls, project_root, backend="auto", context=None: _stub_authorizer(backend)),
    )

    api = ScopeApi(str(tmp_path))

    assert api._acl_enforcement is not None
    assert api._acl_enforcement.mode == "monitor"
    assert api._acl_enforcement.authorizer.backend == "legacy"


def test_scope_api_acl_env_sets_default_project_audit_file(monkeypatch, tmp_path):
    root = tmp_path / "project"
    (root / META_DIR).mkdir(parents=True)
    (root / META_DIR / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")

    monkeypatch.setenv(env_name("ACL_MODE"), "monitor")
    monkeypatch.setenv(env_name("ACL_AUDIT"), "1")
    monkeypatch.delenv(env_name("ACL_AUDIT_FILE"), raising=False)
    monkeypatch.setattr(
        "core.scope_api.ACLAuthorizer.from_project",
        classmethod(lambda cls, project_root, backend="auto", context=None: _stub_authorizer(backend)),
    )

    api = ScopeApi(str(root))

    assert api._acl_audit_file is not None
    assert api._acl_audit_file.name == "audit.log"
    assert str(api._acl_audit_file).endswith(f"/{META_DIR}/audit.log")


def test_scope_api_acl_env_respects_custom_audit_file(monkeypatch, tmp_path):
    custom = tmp_path / "custom-audit.jsonl"
    monkeypatch.setenv(env_name("ACL_MODE"), "monitor")
    monkeypatch.setenv(env_name("ACL_AUDIT_FILE"), str(custom))
    monkeypatch.setattr(
        "core.scope_api.ACLAuthorizer.from_project",
        classmethod(lambda cls, project_root, backend="auto", context=None: _stub_authorizer(backend)),
    )

    api = ScopeApi(str(tmp_path))

    assert api._acl_audit_file == custom.resolve()
