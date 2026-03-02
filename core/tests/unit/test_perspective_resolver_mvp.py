from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from core.perspective_resolver import (
    PerspectiveContext,
    build_hint_cpd,
    list_virtual_dir,
    parse_merged_templates_cpd,
    perspective_open,
    perspective_open_from_cpd,
    prepare_create,
    prepare_rename,
    resolve_virtual_dir_for_read,
    resolve_real_path,
    resolve_virtual_path,
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


def test_t01b_open_context_at_project_root_yields_projects_anchor(workspace: dict[str, Path]):
    """CWD at project_root (Projekte container) is valid; initial CPD is /Projekte."""
    ctx = perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["projekte"]),
        role=None,
    )
    assert ctx.cpd == "/Projekte"
    assert ctx.cwd_real == str(workspace["projekte"])


def test_perspective_open_from_cpd_projects_anchor(workspace: dict[str, Path]):
    """perspective_open_from_cpd with /Projekte yields context at project_root."""
    ctx = perspective_open_from_cpd(
        project_root=str(workspace["projekte"]),
        cpd="/Projekte",
    )
    assert ctx.cpd == "/Projekte"
    assert ctx.cwd_real == str(workspace["projekte"])
    assert ctx.project_root == str(workspace["projekte"])


def test_perspective_open_from_cpd_project_path(workspace: dict[str, Path]):
    """perspective_open_from_cpd with project CPD yields same context as perspective_open."""
    cpd = "/kommunikation/email/Projekte/ProjektA"
    ctx_from_cpd = perspective_open_from_cpd(
        project_root=str(workspace["projekte"]),
        cpd=cpd,
    )
    assert ctx_from_cpd.cpd == cpd
    assert ctx_from_cpd.cwd_real == str(workspace["a_email"])
    ctx_from_path = perspective_open(
        perspective_id="flipped",
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a_email"]),
    )
    assert ctx_from_cpd.cpd == ctx_from_path.cpd
    assert ctx_from_cpd.cwd_real == ctx_from_path.cwd_real


def test_perspective_open_from_cpd_invalid_raises(workspace: dict[str, Path]):
    """perspective_open_from_cpd with invalid CPD raises ValueError."""
    with pytest.raises(ValueError, match="invalid CPD"):
        perspective_open_from_cpd(
            project_root=str(workspace["projekte"]),
            cpd="/../Projekte/ProjektA",
        )


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


def test_dir_read_falls_back_to_nearest_existing_parent(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = resolve_virtual_dir_for_read(
        ctx=ctx,
        cpd="/kommunikation/email/Projekte/ProjektA/inbox/2026",
    )
    assert out.ok is True
    assert out.node_type == "dir"
    assert out.fallback_applied is True
    assert out.effective_read_path == str(workspace["a_inbox"])
    assert out.fallback_to == "/kommunikation/email/Projekte/ProjektA/inbox"


def test_dir_read_fallback_stays_in_same_project(ctx: PerspectiveContext, workspace: dict[str, Path]):
    out = resolve_virtual_dir_for_read(
        ctx=ctx,
        cpd="/kommunikation/email/Projekte/ProjektB/inbox/2026",
    )
    assert out.ok is True
    assert out.fallback_applied is True
    assert out.effective_read_path == str(workspace["b"])
    assert out.fallback_to == "/Projekte/ProjektB"


def test_dir_read_projects_anchor_has_no_parent_fallback(ctx: PerspectiveContext):
    out = resolve_virtual_dir_for_read(
        ctx=ctx,
        cpd="/kommunikation/email/Projekte",
    )
    assert out.ok is True
    assert out.node_type == "virtual_anchor"
    assert out.fallback_applied is False
    assert out.effective_read_path is None


def test_dir_read_fallback_denied_on_effective_parent(ctx: PerspectiveContext, workspace: dict[str, Path]):
    inbox_path = workspace["a_inbox"].resolve()

    def _checker(_role: str | None, path: Path, action: str) -> bool:
        # Allow canonical missing path checks, but deny the fallback parent.
        if action != "read":
            return True
        return path.resolve() != inbox_path

    deny_fallback_ctx = replace(ctx, acl_checker=_checker)
    out = resolve_virtual_dir_for_read(
        ctx=deny_fallback_ctx,
        cpd="/kommunikation/email/Projekte/ProjektA/inbox/2026",
    )
    assert out.ok is False
    assert out.error_code == "denied"


def test_file_read_remains_strict_not_found(ctx: PerspectiveContext):
    out = resolve_virtual_path(
        ctx=ctx,
        cpd="/kommunikation/email/Projekte/ProjektA/inbox/2026/missing.eml",
    )
    assert out.ok is False
    assert out.error_code == "not_found"


def test_prepare_create_in_unborn_branch_stays_strict_not_found(ctx: PerspectiveContext):
    out = prepare_create(
        ctx=ctx,
        cpd_parent="/kommunikation/email/Projekte/ProjektA/inbox/2026",
        name="new.eml",
        node_type="file",
    )
    assert out.ok is False
    assert out.error_code == "not_found"


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


def test_parse_merged_templates_cpd_extracts_hint_and_tail_from_templates_path():
    parsed = parse_merged_templates_cpd(
        cpd="/Templates/Person/finanz",
        fallback_project_name="ProjektA",
        fallback_template_hint="Standard",
    )
    assert parsed.valid is True
    assert parsed.project_name == "ProjektA"
    assert parsed.template_hint == "Person"
    assert list(parsed.tail_parts) == ["finanz"]
    assert parsed.is_off is False


def test_build_hint_cpd_keeps_tail_after_project_anchor():
    cpd = build_hint_cpd(project_name="ProjektA", template_hint="Person", tail_parts=["finanz", "steuern"])
    assert cpd == "/Person/Projekte/ProjektA/finanz/steuern"
