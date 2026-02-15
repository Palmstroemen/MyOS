from core.scope_api import ScopeApi


def test_get_project_color_prefers_color_md_over_project_md(tmp_path):
    root = tmp_path / "ProjectA"
    myos = root / ".MyOS"
    myos.mkdir(parents=True)
    (myos / "Project.md").write_text("color: #112233\n", encoding="utf-8")
    (myos / "Color.md").write_text("#445566\n", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api.get_project_color(str(root)) == "#445566"


def test_resolve_project_color_inherits_from_parent_project(tmp_path):
    root = tmp_path / "ProjectA"
    child = root / "notes" / "daily"
    child.mkdir(parents=True)
    myos = root / ".MyOS"
    myos.mkdir(parents=True)
    (myos / "Project.md").write_text("Theme #A1B2C3", encoding="utf-8")

    api = ScopeApi(str(root))
    assert api._resolve_project_color(child) == "#A1B2C3"


def test_resolve_project_color_uses_cache_after_first_read(tmp_path):
    root = tmp_path / "ProjectA"
    root.mkdir()
    myos = root / ".MyOS"
    myos.mkdir()
    (myos / "Color.md").write_text("#101112", encoding="utf-8")

    api = ScopeApi(str(root))
    first = api._resolve_project_color(root)
    # Change file after first lookup; cached value should remain stable.
    (myos / "Color.md").write_text("#FFFFFF", encoding="utf-8")
    second = api._resolve_project_color(root)

    assert first == "#101112"
    assert second == "#101112"


def test_find_color_upwards_checks_dotmyos_then_plain_color(tmp_path):
    base = tmp_path / "Templates"
    leaf = base / "One" / "Sub"
    leaf.mkdir(parents=True)
    (leaf / "Color.md").write_text("#999999", encoding="utf-8")
    (leaf / ".MyOS").mkdir()
    (leaf / ".MyOS" / "Color.md").write_text("#123ABC", encoding="utf-8")

    api = ScopeApi(str(tmp_path))
    assert api._find_color_upwards(leaf, base) == "#123ABC"

