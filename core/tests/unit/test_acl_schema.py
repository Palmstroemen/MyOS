import pytest

from core.acl import ACLAuthorizer
from core.acl_schema import ACLDocumentModel, acl_policy_from_document


def test_acl_schema_builds_policy_with_normalized_names():
    payload = {
        "roles": {
            " Finance ": [{"path": "/Finanz/**", "rights": {"Read", "write"}}],
            "Admin": [{"path": "/*", "rights": {"*"}}],
        },
        "users": {
            " Bertha ": {"Finance"},
            "ALFRED": {"Admin"},
        },
    }

    policy = acl_policy_from_document(payload)
    authorizer = ACLAuthorizer(policy, backend="legacy")

    assert "finance" in policy.roles
    assert "admin" in policy.roles
    assert authorizer.can_user_access("bertha", "/Finanz/Q1", "read")
    assert not authorizer.can_user_access("bertha", "/HR", "read")
    assert authorizer.can_user_access("alfred", "/Anything", "delete")


def test_acl_schema_rejects_unknown_rights():
    with pytest.raises(ValueError):
        ACLDocumentModel.model_validate(
            {
                "roles": {"finance": [{"path": "/Finanz/**", "rights": {"read", "hack"}}]},
                "users": {"bertha": {"finance"}},
            }
        )


def test_acl_schema_rejects_path_traversal_fragments():
    with pytest.raises(ValueError):
        ACLDocumentModel.model_validate(
            {
                "roles": {"finance": [{"path": "/Finanz/../Admin", "rights": {"read"}}]},
                "users": {"bertha": {"finance"}},
            }
        )


def test_acl_schema_rejects_user_with_unknown_role():
    with pytest.raises(ValueError):
        ACLDocumentModel.model_validate(
            {
                "roles": {"finance": [{"path": "/Finanz/**", "rights": {"read"}}]},
                "users": {"bertha": {"accounting"}},
            }
        )
