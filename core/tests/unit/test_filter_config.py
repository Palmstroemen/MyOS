# test_filter_config.py

import tempfile
from pathlib import Path

import pytest

from core.perspective import FilterConfig
from core.perspective import apply_filter_projection, find_filters, find_filters_layers, resolve_active_filter
from core.perspective import resolve_effective_filter


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
        myos_dir = project_root / ".MyOS"
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
        myos_dir = project_root / ".MyOS"
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
        myos_dir = project_root / ".MyOS"
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
        myos_dir = project_root / ".MyOS"
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
        coll = root / ".MyOS" / "Filters"
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
