from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from core.perspective_resolver import (
    PerspectiveContext,
    perspective_open,
    prepare_create,
    prepare_rename,
    resolve_real_path,
    resolve_virtual_path,
    list_virtual_dir,
)


@pytest.fixture()
def workspace(tmp_path: Path) -> dict[str, Path]:
    proj_root = tmp_path / "Projekte"
    a = proj_root / "ProjektA"
    b = proj_root / "ProjektB"
    a_email_inbox = a / "kommunikation" / "email" / "inbox"
    a_email_inbox.mkdir(parents=True)
    (a_email_inbox / "mail1.eml").write_text("hello", encoding="utf-8")
    (a_email_inbox / "draft.txt").write_text("draft", encoding="utf-8")
    b.mkdir(parents=True)
    return {
        "projekte": proj_root,
        "a": a,
        "b": b,
        "a_email": a / "kommunikation" / "email",
        "a_mail": a_email_inbox / "mail1.eml",
        "a_inbox": a_email_inbox,
    }


@pytest.fixture()
def ctx(workspace: dict[str, Path]) -> PerspectiveContext:
    return perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a_email"]),
        role=None,
    )


def test_t01_open_context_from_real_path(ctx: PerspectiveContext, workspace: dict[str, Path]):
    assert ctx.perspective_id == "flipped"
    assert ctx.project_root == str(workspace["projekte"])
    assert ctx.cwd_real == str(workspace["a_email"])
    assert ctx.cpd == "/kommunikation/email/Projekte/ProjektA"


def test_t02_resolve_existing_cpd_directory(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    assert out.ok is True
    assert out.node_type == "dir"
    assert out.real_path == str(workspace["a_email"])


def test_t03_resolve_existing_cpd_file(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml")
    assert out.ok is True
    assert out.node_type == "file"
    assert out.real_path == str(workspace["a_mail"])


def test_t04_reverse_mapping_real_to_cpd(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = resolve_real_path(ctx=ctx, real_path=str(workspace["a_mail"]))
    assert out.ok is True
    assert out.cpd == "/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml"


def test_t05_mapping_is_deterministic(ctx: PerspectiveContext):
    one = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    two = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    assert repr(one) == repr(two)


def test_t06_not_found_branch_returns_not_found(ctx: PerspectiveContext):
    out = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA/not-there")
    assert out.ok is False
    assert out.error_code == "not_found"
    assert out.node_type == "missing"


def test_t07_invalid_path_traversal_rejected(ctx: PerspectiveContext):
    out = resolve_virtual_path(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA/../../etc")
    assert out.ok is False
    assert out.error_code == "invalid_path"


def test_t08_acl_denied_read_returns_denied(workspace: dict[str, Path]):
    deny_ctx = perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a_email"]),
        role="deny",
    )
    out = resolve_virtual_path(ctx=deny_ctx, cpd="/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml")
    assert out.ok is False
    assert out.error_code == "denied"


def test_t09_ambiguous_mapping_returns_explicit_error(ctx: PerspectiveContext, workspace: dict[str, Path]):
    # Path is valid real path but not under context template_head "kommunikation/email".
    foreign = workspace["a"] / "finanz" / "rechnung.pdf"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("x", encoding="utf-8")
    out = resolve_real_path(ctx=ctx, real_path=str(foreign))
    assert out.ok is False
    assert out.error_code == "ambiguous"


def test_t10_list_virtual_directory_shape(ctx: PerspectiveContext):
    entries = list_virtual_dir(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    assert isinstance(entries, list)
    assert entries
    item = entries[0]
    assert isinstance(item, dict)
    for key in ("name", "cpd", "nodeType", "realPath", "isVirtual"):
        assert key in item


def test_t11_listing_and_resolve_are_consistent(ctx: PerspectiveContext):
    entries = list_virtual_dir(ctx=ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    for item in entries:
        child_cpd = str(item.get("cpd") or "")
        if child_cpd:
            out = resolve_virtual_path(ctx=ctx, cpd=child_cpd)
            assert out.ok is True


def test_t12_listing_acl_policy_is_stable(workspace: dict[str, Path]):
    deny_ctx = perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a_email"]),
        role="deny",
    )
    entries = list_virtual_dir(ctx=deny_ctx, cpd="/kommunikation/email/Projekte/ProjektA")
    assert entries == []


def test_t13_prepare_create_file_resolves_target(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = prepare_create(
        ctx=ctx,
        cpd_parent="/kommunikation/email/Projekte/ProjektA/inbox",
        name="new.eml",
        node_type="file",
    )
    assert out.ok is True
    assert out.real_path == str(workspace["a_inbox"] / "new.eml")


def test_t14_prepare_create_denied(workspace: dict[str, Path]):
    deny_ctx = perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a_email"]),
        role="deny",
    )
    out = prepare_create(
        ctx=deny_ctx,
        cpd_parent="/kommunikation/email/Projekte/ProjektA/inbox",
        name="denied.eml",
        node_type="file",
    )
    assert out.ok is False
    assert out.error_code == "denied"


def test_t15_prepare_rename_within_scope(ctx: PerspectiveContext):
    src, dst = prepare_rename(
        ctx=ctx,
        source_cpd="/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml",
        target_parent_cpd="/kommunikation/email/Projekte/ProjektA/inbox",
        target_name="mail1-renamed.eml",
    )
    assert src.ok is True
    assert dst.ok is True
    assert str(dst.real_path or "").endswith("/mail1-renamed.eml")


def test_t16_prepare_rename_cross_branch_unsupported(ctx: PerspectiveContext):
    _src, dst = prepare_rename(
        ctx=ctx,
        source_cpd="/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml",
        target_parent_cpd="/kommunikation/email/Projekte/ProjektB",
        target_name="mail1.eml",
    )
    assert dst.ok is False
    assert dst.error_code == "unsupported"
