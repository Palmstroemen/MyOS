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


def _write_templates_config(project_root: Path, names: list[str]) -> None:
    myos = project_root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    body = "\n".join(["# Templates"] + [str(name) for name in names]) + "\n"
    (myos / "Templates.md").write_text(body, encoding="utf-8")


def _setup_merged_templates_tree(tmp_path: Path) -> dict:
    root = tmp_path / "MyOS"
    _write_project_marker(root)
    project = root / "Projekte" / "ProjektA"
    (project / ".MyOS").mkdir(parents=True, exist_ok=True)
    (project / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    _write_templates_config(project, ["Standard", "Person"])
    (project / "finanz").mkdir(parents=True, exist_ok=True)

    templates = root / "Templates"
    (templates / "Standard" / "admin").mkdir(parents=True, exist_ok=True)
    (templates / "Standard" / "info").mkdir(parents=True, exist_ok=True)
    (templates / "Standard" / "finanz" / "ausgaben").mkdir(parents=True, exist_ok=True)
    (templates / "Standard" / "finanz" / "einnahmen").mkdir(parents=True, exist_ok=True)
    (templates / "Person" / "gesundheit").mkdir(parents=True, exist_ok=True)
    (templates / "Person" / "bildung").mkdir(parents=True, exist_ok=True)
    (templates / "Person" / "info").mkdir(parents=True, exist_ok=True)
    (templates / "Person" / "finanz" / "steuern").mkdir(parents=True, exist_ok=True)
    return {"root": root, "project": project}


def test_perspective_list_templates_off_returns_union_first_level(tmp_path):
    paths = _setup_merged_templates_tree(tmp_path)
    api = ScopeApi(str(paths["project"] / "finanz"))
    api.perspective_open(str(paths["project"] / "finanz"))

    rows = api.perspective_list_templates("/Templates")
    names = sorted(str(item.get("name") or "") for item in rows)

    assert names == ["admin", "bildung", "finanz", "gesundheit", "info"]


def test_perspective_list_templates_deep_tail_keeps_union_and_hint_fallback(tmp_path):
    paths = _setup_merged_templates_tree(tmp_path)
    api = ScopeApi(str(paths["project"] / "finanz"))
    api.perspective_open(str(paths["project"] / "finanz"))

    rows = api.perspective_list_templates("/Templates/Standard/finanz")
    by_name = {str(item.get("name") or ""): item for item in rows}

    assert sorted(by_name.keys()) == ["ausgaben", "einnahmen", "steuern"]
    assert str(by_name["ausgaben"].get("cpd") or "").startswith("/Standard/Projekte/ProjektA/finanz/ausgaben")
    # Exists only in Person -> fallback must switch hint deterministically.
    assert str(by_name["steuern"].get("cpd") or "").startswith("/Person/Projekte/ProjektA/finanz/steuern")


def test_perspective_list_templates_collision_prefers_current_hint(tmp_path):
    paths = _setup_merged_templates_tree(tmp_path)
    api = ScopeApi(str(paths["project"] / "finanz"))
    api.perspective_open(str(paths["project"] / "finanz"))

    rows_standard = api.perspective_list_templates("/Templates/Standard")
    rows_person = api.perspective_list_templates("/Templates/Person")
    by_name_standard = {str(item.get("name") or ""): item for item in rows_standard}
    by_name_person = {str(item.get("name") or ""): item for item in rows_person}

    assert str(by_name_standard["info"].get("cpd") or "").startswith("/Standard/Projekte/ProjektA/info")
    assert str(by_name_person["info"].get("cpd") or "").startswith("/Person/Projekte/ProjektA/info")


def _write_templates_config_names(root: Path, names: list[str]) -> None:
    myos = root / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    body = "# Templates\n" + "\n".join(names) + "\n"
    (myos / "Templates.md").write_text(body, encoding="utf-8")


def _setup_merge_templates_workspace(tmp_path: Path) -> dict:
    root = tmp_path / "MyOS"
    _write_project_marker(root)
    _write_templates_config_names(root, ["Standard", "Person"])
    (root / "Templates" / "Standard" / "finanz" / "ausgaben").mkdir(parents=True, exist_ok=True)
    (root / "Templates" / "Person" / "finanz" / "bildung").mkdir(parents=True, exist_ok=True)
    project = root / "Projekte" / "Finanz"
    project.mkdir(parents=True, exist_ok=True)
    return {"root": root, "project": project}


def test_perspective_templates_off_anchor_lists_merged_first_level(tmp_path):
    paths = _setup_merge_templates_workspace(tmp_path)
    api = ScopeApi(str(paths["project"]))
    opened = api.perspective_open(str(paths["project"]))
    assert opened.get("active") is True

    set_off = api.perspective_set_cpd("/Templates/")
    assert set_off.get("ok") is True
    assert set_off.get("cpd") == "/Templates"

    rows = api.perspective_list_templates("/Templates/")
    names = [str(item.get("name") or "") for item in rows]
    assert names == ["finanz"]
    assert str(rows[0].get("cpd") or "").startswith("/Standard/Projekte/Finanz/finanz")


def test_perspective_templates_deep_tail_merges_children_across_templates(tmp_path):
    paths = _setup_merge_templates_workspace(tmp_path)
    api = ScopeApi(str(paths["project"]))
    opened = api.perspective_open(str(paths["project"]))
    assert opened.get("active") is True

    assert api.perspective_set_cpd("/Templates/").get("ok") is True
    root_rows = api.perspective_list_templates("/Templates/")
    finanz_row = [row for row in root_rows if str(row.get("name") or "") == "finanz"][0]
    finanz_cpd = str(finanz_row.get("cpd") or "")

    assert api.perspective_set_cpd(finanz_cpd).get("ok") is True
    deep_rows = api.perspective_list_templates(finanz_cpd)
    deep_names = sorted(str(item.get("name") or "") for item in deep_rows)
    assert deep_names == ["ausgaben", "bildung"]


def test_perspective_templates_collision_uses_deterministic_hint_template(tmp_path):
    paths = _setup_merge_templates_workspace(tmp_path)
    shared_a = paths["root"] / "Templates" / "Standard" / "finanz" / "shared"
    shared_b = paths["root"] / "Templates" / "Person" / "finanz" / "shared"
    shared_a.mkdir(parents=True, exist_ok=True)
    shared_b.mkdir(parents=True, exist_ok=True)

    api = ScopeApi(str(paths["project"]))
    api.perspective_open(str(paths["project"]))
    api.perspective_set_cpd("/Templates/")
    root_rows = api.perspective_list_templates("/Templates/")
    finanz_cpd = str([row for row in root_rows if str(row.get("name") or "") == "finanz"][0].get("cpd") or "")

    deep_rows = api.perspective_list_templates(finanz_cpd)
    shared = [row for row in deep_rows if str(row.get("name") or "") == "shared"][0]
    assert str(shared.get("cpd") or "") == "/Standard/Projekte/Finanz/finanz/shared"


def test_folder_type_enum_for_children_embryo_born_normal(tmp_path):
    paths = _setup_merged_templates_tree(tmp_path)
    project = paths["project"]
    (project / "finanz").mkdir(parents=True, exist_ok=True)
    (project / "manual").mkdir(parents=True, exist_ok=True)

    api = ScopeApi(str(project))
    rows = api.list_children(str(project), include_embryos=True)
    by_name = {str(item.get("name") or ""): item for item in rows}

    assert int(by_name["finanz"].get("folderType")) == 1
    assert bool(by_name["finanz"].get("isEmbryo")) is False

    assert int(by_name["admin"].get("folderType")) == 2
    assert bool(by_name["admin"].get("isEmbryo")) is True

    assert int(by_name["manual"].get("folderType")) == 0
    assert bool(by_name["manual"].get("isEmbryo")) is False


def test_folder_type_enum_for_templates_is_embryo_only(tmp_path):
    paths = _setup_merged_templates_tree(tmp_path)
    project = paths["project"]
    api = ScopeApi(str(project))

    rows = api.list_templates(str(project), include_embryos=True)
    assert rows
    for item in rows:
        assert int(item.get("folderType")) == 2
        assert bool(item.get("isEmbryo")) is True
