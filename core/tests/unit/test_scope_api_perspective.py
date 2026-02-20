from pathlib import Path

from core.scope_api import ScopeApi


def _write_project_marker(root: Path) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")


def _setup_tree(tmp_path: Path) -> dict:
    root = tmp_path / "MyOS"
    _write_project_marker(root)
    base = root / "Projekte"
    alpha = base / "ProjektA"
    beta = base / "ProjektB"
    (alpha / "finanz" / "ausgaben").mkdir(parents=True)
    (alpha / "finanz" / "readme.md").write_text("x", encoding="utf-8")
    (beta / "recht").mkdir(parents=True)
    return {"root": root, "base": base, "alpha": alpha, "beta": beta}


def test_perspective_cpd_survives_context_updates(tmp_path):
    paths = _setup_tree(tmp_path)
    api = ScopeApi(str(paths["alpha"] / "finanz"))
    opened = api.perspective_open(str(paths["alpha"] / "finanz"))
    assert opened.get("active") is True

    set_result = api.perspective_set_cpd("/finanz/Projekte/ProjektA/unterordner")
    assert isinstance(set_result.get("ok"), bool)
    before = api.perspective_state()
    assert before.get("active") is True

    api.update_context(str(paths["beta"] / "recht"))
    after = api.perspective_state()
    assert after.get("active") is True
    assert after.get("cpd") == before.get("cpd")


def test_perspective_list_dir_returns_virtual_nodes(tmp_path):
    paths = _setup_tree(tmp_path)
    api = ScopeApi(str(paths["alpha"]))
    api.perspective_open(str(paths["alpha"]))
    mapped = api.perspective_resolve_real(str(paths["alpha"] / "finanz"))
    assert mapped.get("ok") is True

    rows = api.perspective_list_dir(str(mapped.get("cpd") or ""))
    names = [str(item.get("name") or "") for item in rows]
    assert "ausgaben" in names
    assert "readme.md" in names
    dir_node = [item for item in rows if str(item.get("name")) == "ausgaben"][0]
    assert dir_node.get("nodeType") == "dir"


def test_perspective_fallback_fields_for_missing_branch(tmp_path):
    paths = _setup_tree(tmp_path)
    api = ScopeApi(str(paths["alpha"]))
    api.perspective_open(str(paths["alpha"]))

    result = api.perspective_resolve_cpd("/finanz/Projekte/ProjektA/does/not/exist")
    assert result.get("ok") is True
    assert result.get("fallbackApplied") is True
    assert str(result.get("fallbackFrom") or "").startswith("/finanz/Projekte/ProjektA")
    assert str(result.get("fallbackTo") or "").startswith("/finanz/Projekte/ProjektA")
    assert set(result.keys()) == {
        "ok",
        "cpd",
        "realPath",
        "effectiveReadPath",
        "fallbackApplied",
        "fallbackFrom",
        "fallbackTo",
        "nodeType",
        "errorCode",
        "message",
    }


def test_perspective_open_prefers_nearest_top_project_root(tmp_path):
    outer = tmp_path / "Outer"
    _write_project_marker(outer)
    inner = outer / "MyOS_Test"
    _write_project_marker(inner)
    target = inner / "Projekte" / "ProjektA" / "finanz"
    target.mkdir(parents=True)

    api = ScopeApi(str(target))
    opened = api.perspective_open(str(target))

    assert opened.get("active") is True
    assert opened.get("projectRoot") == str(inner / "Projekte")
    assert str(opened.get("cpd") or "").startswith("/finanz/Projekte/ProjektA")
