# test_filter_config.py

import tempfile
from pathlib import Path

import pytest

from core.perspective import FilterConfig
from core.perspective import apply_filter_projection, find_filters, find_filters_layers, resolve_active_filter
from core.perspective import resolve_effective_filter
from core.brand import META_DIR


def _write_filter(path: Path) -> None:
    content = """# Filter
Name: Finance
Scope: /finanz/

## Include
/finanz/
/rechtliches/

## Exclude
/finanz/schwarzgeld/

## Filter
*/rechnung.pdf
*/invoice.pdf
*/*rechnung.*
*/*invoice.*
/*.jpg

## Flatten
true

## Group
project
tags

## Desk
Desk.md
"""
    path.write_text(content)


def _write_named_filter(path: Path, name: str) -> None:
    path.write_text(f"# Filter\nName: {name}\n")


def test_filter_parse_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Filter.md"
        _write_filter(cfg)

        parsed = FilterConfig.from_file(cfg)

        assert parsed.name == "Finance"
        assert parsed.scope == "/finanz/"
        assert parsed.include == ["/finanz/", "/rechtliches/"]
        assert parsed.exclude == ["/finanz/schwarzgeld/"]
        assert "*/rechnung.pdf" in parsed.filters
        assert parsed.flatten is True
        assert parsed.groups == ["project", "tags"]
        assert parsed.desk == "Desk.md"


def test_filter_missing_name_is_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Filter.md"
        cfg.write_text("# Filter\nScope: /finanz/\n")

        with pytest.raises(ValueError):
            FilterConfig.from_file(cfg)


def test_filter_flatten_default_false():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Filter.md"
        cfg.write_text("# Filter\nName: Simple\n")

        parsed = FilterConfig.from_file(cfg)

        assert parsed.flatten is False


def test_filter_missing_scope_is_allowed():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Filter.md"
        cfg.write_text("# Filter\nName: Minimal\n")

        parsed = FilterConfig.from_file(cfg)

        assert parsed.scope is None


def test_filter_duplicate_sections_merge():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Filter.md"
        cfg.write_text(
            "# Filter\n"
            "Name: Finance\n"
            "\n"
            "## Include\n"
            "/finanz/\n"
            "\n"
            "### Include\n"
            "/rechtliches/\n"
            "\n"
            "## Group\n"
            "project\n"
            "\n"
            "### Group\n"
            "tags\n"
        )

        parsed = FilterConfig.from_file(cfg)

        assert parsed.include == ["/finanz/", "/rechtliches/"]
        assert parsed.groups == ["project", "tags"]


def test_find_filters_orders_by_specificity():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / META_DIR
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_filter(myos_dir / "Filter.md", "Root")
        _write_named_filter(sub_dir / "Filter.md", "Sub")

        results = find_filters(sub_dir)

        assert [cfg.name for _, cfg in results] == ["Sub", "Root"]


def test_resolve_active_filter_manual_wins():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / META_DIR
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        manual = myos_dir / "Filter.md"
        auto = sub_dir / "Filter.md"
        _write_named_filter(manual, "Manual")
        _write_named_filter(auto, "Auto")

        cfg = resolve_active_filter(sub_dir, manual=str(manual))

        assert cfg.name == "Manual"


def test_resolve_active_filter_auto_nearest_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / META_DIR
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_filter(myos_dir / "Filter.md", "Root")
        _write_named_filter(sub_dir / "Filter.md", "Sub")

        cfg = resolve_active_filter(sub_dir)

        assert cfg.name == "Sub"


def test_resolve_active_filter_falls_back_to_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / META_DIR
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_filter(myos_dir / "Filter.md", "Root")

        cfg = resolve_active_filter(sub_dir)

        assert cfg.name == "Root"


def test_find_filters_layers_includes_collection_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        coll = root / META_DIR / "Filters"
        sub.mkdir(parents=True)
        coll.mkdir(parents=True)
        _write_named_filter(coll / "Finance.md", "Finance")
        _write_named_filter(sub / "Filter.md", "Sub")

        layers = find_filters_layers(sub)

        names = [layer.config.name for layer in layers]
        assert names[0] == "Sub"
        assert "Finance" in names


def test_resolve_effective_filter_merges_lists_and_nearest_scalars():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        root.mkdir(parents=True)
        sub.mkdir(parents=True)
        (root / "Filter.md").write_text(
            "\n".join(
                [
                    "# Filter",
                    "Name: Root",
                    "",
                    "## Include",
                    "/finanz/",
                    "",
                    "## Group",
                    "project",
                    "",
                    "## Desk",
                    "DeskRoot.md",
                    "",
                    "## Flatten",
                    "false",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (sub / "Filter.md").write_text(
            "\n".join(
                [
                    "# Filter",
                    "Name: Sub",
                    "",
                    "## Include",
                    "/finanz/rechnungen/",
                    "",
                    "## Group",
                    "tags",
                    "",
                    "## Desk",
                    "DeskSub.md",
                    "",
                    "## Flatten",
                    "true",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        effective = resolve_effective_filter(sub)

        assert effective is not None
        assert effective.config.name == "Sub"
        assert effective.config.include == ["/finanz/", "/finanz/rechnungen/"]
        assert effective.config.groups == ["project", "tags"]
        assert effective.config.desk == "DeskSub.md"
        assert effective.config.flatten is True


def test_resolve_effective_filter_inherit_not_clears_parent_layers():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        root.mkdir(parents=True)
        sub.mkdir(parents=True)
        (root / "Filter.md").write_text(
            "# Filter\nName: Root\n\n## Include\n/finanz/\n",
            encoding="utf-8",
        )
        (sub / "Filter.md").write_text(
            "# Filter\nName: Sub\nInherit: not\n\n## Include\n/recht/\n",
            encoding="utf-8",
        )

        effective = resolve_effective_filter(sub)

        assert effective is not None
        assert effective.config.include == ["/recht/"]
        assert effective.layers[0].config.name == "Sub"


def test_apply_filter_projection_applies_include_exclude_and_group():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cwd = tmp / "Project"
        finance = cwd / "finanz"
        invoices = finance / "rechnungen"
        invoices.mkdir(parents=True)
        keep = invoices / "invoice1.pdf"
        drop = invoices / "image.jpg"
        keep.write_text("ok", encoding="utf-8")
        drop.write_text("x", encoding="utf-8")
        cfg_file = cwd / "Filter.md"
        cfg_file.write_text(
            "\n".join(
                [
                    "# Filter",
                    "Name: Finance",
                    "",
                    "## Include",
                    "/finanz/",
                    "",
                    "## Filter",
                    "*.pdf",
                    "",
                    "## Group",
                    "folder",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        effective = resolve_effective_filter(cwd)
        assert effective is not None
        entries = [
            {"name": "invoice1.pdf", "path": str(keep), "isDir": False, "tags": []},
            {"name": "image.jpg", "path": str(drop), "isDir": False, "tags": []},
        ]

        projected = apply_filter_projection(entries, cwd=cwd, filter_state=effective, project_root=cwd)

        assert len(projected) == 1
        assert projected[0]["name"] == "invoice1.pdf"
        assert projected[0]["filterActive"] is True
        assert "filterGroup" in projected[0]


# A filter may put on a lens (Designdocument Perspective Resolver MVP.md, A6, E6): its
# department and deeper levels, without a project - put on where one stands.

@pytest.mark.parametrize("written, lens", [
    ("04_Finanz", ("04_Finanz",)),
    ("04_Finanz/Ausgaben", ("04_Finanz", "Ausgaben")),
    ("/04_Finanz/Ausgaben/", ("04_Finanz", "Ausgaben")),
])
def test_a_filter_names_its_lens(tmp_path, written, lens):
    cfg = tmp_path / "Filter.md"
    cfg.write_text(f"# Filter\nName: Finance\n\n## Perspective\n{written}\n")

    assert FilterConfig.from_file(cfg).lens == lens


@pytest.mark.parametrize("written", ["../04_Finanz", "04_Finanz/../../etc", "./04_Finanz"])
def test_a_lens_never_leaves_the_project(tmp_path, written):
    # Security: the lens names folders inside a project; no way out of it.
    cfg = tmp_path / "Filter.md"
    cfg.write_text(f"# Filter\nName: Finance\n\n## Perspective\n{written}\n")

    assert FilterConfig.from_file(cfg).lens == ()


def test_without_perspective_no_lens(tmp_path):
    cfg = tmp_path / "Filter.md"
    _write_filter(cfg)

    assert FilterConfig.from_file(cfg).lens == ()


def test_the_nearest_filter_names_the_lens(tmp_path):
    sub = tmp_path / "Sub"
    sub.mkdir()
    (tmp_path / "Filter.md").write_text("# Filter\nName: Root\n\n## Perspective\n04_Finanz\n")
    (sub / "Filter.md").write_text("# Filter\nName: Sub\n\n## Perspective\n05_Rechtliches/Verträge\n")

    assert resolve_effective_filter(sub).config.lens == ("05_Rechtliches", "Verträge")


# The collection in .MyOS/Filters is there to choose from: it acts only when chosen by hand
# (myfilter), so a file lying there cannot change a whole project unasked. Filter.md acts by itself.
def _collection(tmp_path, body="# Filter\nName: Ausgaben\n\n## Perspective\n04_Finanz/Ausgaben\n"):
    root = tmp_path / "Job"
    (root / "Belege").mkdir(parents=True)
    (root / META_DIR / "Filters").mkdir(parents=True)
    path = root / META_DIR / "Filters" / "Ausgaben.md"
    path.write_text(body, encoding="utf-8")
    return root, path


def test_a_filter_of_the_collection_does_not_act_by_itself(tmp_path):
    root, _ = _collection(tmp_path)
    assert resolve_effective_filter(root) is None
    assert resolve_effective_filter(root / "Belege") is None
    assert find_filters(root) == []


def test_a_filter_of_the_collection_can_still_be_chosen(tmp_path):
    root, path = _collection(tmp_path)
    assert [layer.config.name for layer in find_filters_layers(root)] == ["Ausgaben"]
    assert resolve_effective_filter(root, manual=path).config.name == "Ausgaben"


def test_a_filter_md_still_acts_by_itself(tmp_path):
    root, _ = _collection(tmp_path)
    (root / "Filter.md").write_text("# Filter\nName: Hier\n", encoding="utf-8")
    assert resolve_effective_filter(root).config.name == "Hier"


def test_an_entry_of_the_folder_itself_has_no_origin(tmp_path):
    (tmp_path / "Filter.md").write_text("# Filter\nName: Hier\n", encoding="utf-8")
    entries = [{"name": "Belege", "path": str(tmp_path / "Belege")}]
    projected = apply_filter_projection(entries, cwd=tmp_path, filter_state=resolve_effective_filter(tmp_path))
    assert projected[0]["filterActive"] is True and projected[0]["originPath"] == ""


def test_an_entry_from_deeper_down_says_where_from_seen_from_here(tmp_path):
    (tmp_path / "Filter.md").write_text("# Filter\nName: Hier\n", encoding="utf-8")
    entries = [{"name": "a.pdf", "path": str(tmp_path / "2024" / "Belege" / "a.pdf")}]
    projected = apply_filter_projection(entries, cwd=tmp_path, filter_state=resolve_effective_filter(tmp_path))
    assert projected[0]["originPath"] == "2024/Belege"
