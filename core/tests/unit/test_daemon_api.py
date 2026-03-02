"""
Tests for perspective daemon API (state + request handling, no FUSE/socket).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Ensure repo root on path
_REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from daemon.api import decode_request, decode_response, encode_response
from daemon.perspective_daemon import DaemonState, _handle_request


@pytest.fixture
def project_workspace(tmp_path: Path) -> Path:
    """Minimal project root with Projekte/ProjektA."""
    projekte = tmp_path / "Projekte"
    (projekte / "ProjektA").mkdir(parents=True)
    (tmp_path / ".MyOS").mkdir(exist_ok=True)
    (tmp_path / ".MyOS" / "Project.md").write_text("# Project\n", encoding="utf-8")
    return tmp_path


def test_daemon_state_set_cpd_and_get_context(project_workspace: Path) -> None:
    root = str(project_workspace / "Projekte")
    state = DaemonState(project_root=root, cpd="/Projekte", mount_point="")
    ctx = state.get_context()
    assert ctx.cpd == "/Projekte"
    assert ctx.project_root == root
    state.set_cpd(None, "/Projekte/ProjektA")
    ctx2 = state.get_context()
    assert ctx2.cpd == "/Projekte/ProjektA"


def test_handle_request_ping() -> None:
    state = DaemonState(project_root="/tmp", cpd="/Projekte", mount_point="")
    req = {"method": "ping"}
    resp = _handle_request(state, req)
    data = decode_response(resp)
    assert data is not None and data.get("ok") is True and data.get("result", {}).get("pong") is True


def test_handle_request_get_state(project_workspace: Path) -> None:
    root = str(project_workspace / "Projekte")
    state = DaemonState(project_root=root, cpd="/Projekte", mount_point="/mnt")
    req = {"method": "get_state"}
    resp = _handle_request(state, req)
    data = decode_response(resp)
    assert data is not None and data.get("ok") is True
    result = data.get("result", {})
    assert result.get("project_root") == root
    assert result.get("mount_point") == "/mnt"
    assert result.get("active") is True


def test_handle_request_set_cpd(project_workspace: Path) -> None:
    root = str(project_workspace / "Projekte")
    state = DaemonState(project_root=root, cpd="/Projekte", mount_point="")
    req = {"method": "set_cpd", "params": {"cpd": "/Projekte/ProjektA"}}
    resp = _handle_request(state, req)
    data = decode_response(resp)
    assert data is not None and data.get("ok") is True
    assert data.get("result", {}).get("cpd") == "/Projekte/ProjektA"
    assert state.cpd == "/Projekte/ProjektA"
