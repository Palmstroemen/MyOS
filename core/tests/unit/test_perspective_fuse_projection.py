from __future__ import annotations

import errno
import os
import stat
from pathlib import Path

import pytest

from core.perspective_fuse import FuseOSError, PerspectiveFuseAdapter, resolver_error_to_errno
from core.perspective_resolver import list_virtual_dir, prepare_create, resolve_virtual_path


@pytest.fixture()
def workspace(tmp_path: Path) -> dict[str, Path]:
    proj_root = tmp_path / "Projekte"
    a = proj_root / "ProjektA"
    b = proj_root / "ProjektB"
    inbox = a / "kommunikation" / "email" / "inbox"
    inbox.mkdir(parents=True)
    (inbox / "mail1.eml").write_text("hello", encoding="utf-8")
    b.mkdir(parents=True)
    return {"projekte": proj_root, "a": a, "b": b, "inbox": inbox}


@pytest.fixture()
def adapter(workspace: dict[str, Path]) -> PerspectiveFuseAdapter:
    return PerspectiveFuseAdapter(
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a"] / "kommunikation" / "email"),
        perspective_id="flipped",
        role=None,
    )


def test_t17_getattr_matches_resolver_state(adapter: PerspectiveFuseAdapter):
    cpd = "/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml"
    resolved = resolve_virtual_path(ctx=adapter.ctx, cpd=cpd)
    st = adapter.getattr(cpd)
    assert resolved.ok is True
    assert resolved.node_type == "file"
    assert stat.S_ISREG(int(st["st_mode"]))

    anchor = resolve_virtual_path(ctx=adapter.ctx, cpd="/kommunikation/email/Projekte")
    anchor_st = adapter.getattr("/kommunikation/email/Projekte")
    assert anchor.ok is True
    assert anchor.node_type == "virtual_anchor"
    assert stat.S_ISDIR(int(anchor_st["st_mode"]))


def test_t18_readdir_matches_list_virtual_dir(adapter: PerspectiveFuseAdapter):
    cpd = "/kommunikation/email/Projekte/ProjektA"
    expected = {"..", "."}
    expected.update(str(item.get("name") or "") for item in list_virtual_dir(ctx=adapter.ctx, cpd=cpd))
    got = set(adapter.readdir(cpd, None))
    assert got == expected


def test_t19_create_persists_to_prepared_real_path(adapter: PerspectiveFuseAdapter):
    cpd_file = "/kommunikation/email/Projekte/ProjektA/inbox/new.eml"
    prepared = prepare_create(
        ctx=adapter.ctx,
        cpd_parent="/kommunikation/email/Projekte/ProjektA/inbox",
        name="new.eml",
        node_type="file",
    )
    assert prepared.ok is True
    assert prepared.real_path is not None

    fh = adapter.create(cpd_file, 0o644)
    try:
        written = adapter.write(cpd_file, b"content", 0, fh)
        assert written == len(b"content")
    finally:
        adapter.release(cpd_file, fh)

    target = Path(str(prepared.real_path))
    assert target.exists()
    assert target.read_bytes() == b"content"


def test_readdir_uses_directory_fallback(adapter: PerspectiveFuseAdapter):
    got = set(adapter.readdir("/kommunikation/email/Projekte/ProjektA/inbox/2026", None))
    # Fallback to inbox should expose its children.
    assert "mail1.eml" in got
    assert "." in got
    assert ".." in got


def test_getattr_directory_uses_fallback(adapter: PerspectiveFuseAdapter):
    st = adapter.getattr("/kommunikation/email/Projekte/ProjektA/inbox/2026")
    assert stat.S_ISDIR(int(st["st_mode"]))


def test_readdir_fallback_order_is_stable(adapter: PerspectiveFuseAdapter):
    first = list(adapter.readdir("/kommunikation/email/Projekte/ProjektA/inbox/2026", None))
    second = list(adapter.readdir("/kommunikation/email/Projekte/ProjektA/inbox/2026", None))
    assert first == second


def test_open_missing_file_stays_strict_enoent(adapter: PerspectiveFuseAdapter):
    with pytest.raises(FuseOSError) as exc:
        adapter.open("/kommunikation/email/Projekte/ProjektA/inbox/2026/missing.eml", os.O_RDONLY)
    assert exc.value.errno == errno.ENOENT


def test_create_in_unborn_branch_stays_strict_enoent(adapter: PerspectiveFuseAdapter):
    with pytest.raises(FuseOSError) as exc:
        adapter.create("/kommunikation/email/Projekte/ProjektA/inbox/2026/new.eml", 0o644)
    assert exc.value.errno == errno.ENOENT


def test_error_mapping_is_stable():
    assert resolver_error_to_errno("not_found") == errno.ENOENT
    assert resolver_error_to_errno("denied") == errno.EACCES
    assert resolver_error_to_errno("unsupported") == errno.ENOTSUP


def test_negative_not_found_maps_to_enoent(adapter: PerspectiveFuseAdapter):
    with pytest.raises(FuseOSError) as exc:
        adapter.getattr("/kommunikation/email/Projekte/ProjektA/missing.txt")
    assert exc.value.errno == errno.ENOENT


def test_negative_denied_maps_to_eacces(workspace: dict[str, Path]):
    denied_adapter = PerspectiveFuseAdapter(
        project_root=str(workspace["projekte"]),
        start_real_path=str(workspace["a"] / "kommunikation" / "email"),
        perspective_id="flipped",
        role="deny",
    )
    with pytest.raises(FuseOSError) as exc:
        denied_adapter.getattr("/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml")
    assert exc.value.errno == errno.EACCES


def test_negative_unsupported_maps_to_enotsup(adapter: PerspectiveFuseAdapter):
    src = "/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml"
    dst = "/kommunikation/email/Projekte/ProjektB/mail1.eml"
    with pytest.raises(FuseOSError) as exc:
        adapter.rename(src, dst)
    assert exc.value.errno == errno.ENOTSUP
