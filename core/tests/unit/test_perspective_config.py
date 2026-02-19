# test_perspective_config.py

import tempfile
from pathlib import Path

import pytest

from core.perspective import PerspectiveConfig
from core.perspective import find_perspectives, resolve_active_perspective
from core.perspective import find_perspectives_layers, project_entries, resolve_effective_perspective


def _write_perspective(path: Path) -> None:
    content = """# Perspective
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


def _write_named_perspective(path: Path, name: str) -> None:
    path.write_text(f"# Perspective\nName: {name}\n")


def test_perspective_parse_basic():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Perspective.md"
        _write_perspective(cfg)

        perspective = PerspectiveConfig.from_file(cfg)

        assert perspective.name == "Finance"
        assert perspective.scope == "/finanz/"
        assert perspective.include == ["/finanz/", "/rechtliches/"]
        assert perspective.exclude == ["/finanz/schwarzgeld/"]
        assert "*/rechnung.pdf" in perspective.filters
        assert perspective.flatten is True
        assert perspective.groups == ["project", "tags"]
        assert perspective.desk == "Desk.md"


def test_perspective_missing_name_is_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Perspective.md"
        cfg.write_text("# Perspective\nScope: /finanz/\n")

        with pytest.raises(ValueError):
            PerspectiveConfig.from_file(cfg)


def test_perspective_flatten_default_false():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Perspective.md"
        cfg.write_text("# Perspective\nName: Simple\n")

        perspective = PerspectiveConfig.from_file(cfg)

        assert perspective.flatten is False


def test_perspective_missing_scope_is_allowed():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Perspective.md"
        cfg.write_text("# Perspective\nName: Minimal\n")

        perspective = PerspectiveConfig.from_file(cfg)

        assert perspective.scope is None


def test_perspective_duplicate_sections_merge():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        cfg = tmp / "Perspective.md"
        cfg.write_text(
            "# Perspective\n"
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

        perspective = PerspectiveConfig.from_file(cfg)

        assert perspective.include == ["/finanz/", "/rechtliches/"]
        assert perspective.groups == ["project", "tags"]


def test_find_perspectives_orders_by_specificity():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / ".MyOS"
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_perspective(myos_dir / "Perspective.md", "Root")
        _write_named_perspective(sub_dir / "Perspective.md", "Sub")

        results = find_perspectives(sub_dir)

        assert [cfg.name for _, cfg in results] == ["Sub", "Root"]


def test_resolve_active_perspective_manual_wins():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / ".MyOS"
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        manual = myos_dir / "Perspective.md"
        auto = sub_dir / "Perspective.md"
        _write_named_perspective(manual, "Manual")
        _write_named_perspective(auto, "Auto")

        cfg = resolve_active_perspective(sub_dir, manual=str(manual))

        assert cfg.name == "Manual"


def test_resolve_active_perspective_auto_nearest_folder():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / ".MyOS"
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_perspective(myos_dir / "Perspective.md", "Root")
        _write_named_perspective(sub_dir / "Perspective.md", "Sub")

        cfg = resolve_active_perspective(sub_dir)

        assert cfg.name == "Sub"


def test_resolve_active_perspective_falls_back_to_project():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        project_root = tmp / "Project"
        myos_dir = project_root / ".MyOS"
        sub_dir = project_root / "sub"
        sub_dir.mkdir(parents=True)
        myos_dir.mkdir(parents=True)

        _write_named_perspective(myos_dir / "Perspective.md", "Root")

        cfg = resolve_active_perspective(sub_dir)

        assert cfg.name == "Root"


def test_find_perspectives_layers_includes_collection_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        coll = root / ".MyOS" / "Perspectives"
        sub.mkdir(parents=True)
        coll.mkdir(parents=True)
        _write_named_perspective(coll / "Finance.md", "Finance")
        _write_named_perspective(sub / "Perspective.md", "Sub")

        layers = find_perspectives_layers(sub)

        names = [layer.config.name for layer in layers]
        assert names[0] == "Sub"
        assert "Finance" in names


def test_resolve_effective_perspective_merges_lists_and_nearest_scalars():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        root.mkdir(parents=True)
        sub.mkdir(parents=True)
        (root / "Perspective.md").write_text(
            "\n".join(
                [
                    "# Perspective",
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
        (sub / "Perspective.md").write_text(
            "\n".join(
                [
                    "# Perspective",
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

        effective = resolve_effective_perspective(sub)

        assert effective is not None
        assert effective.config.name == "Sub"
        assert effective.config.include == ["/finanz/", "/finanz/rechnungen/"]
        assert effective.config.groups == ["project", "tags"]
        assert effective.config.desk == "DeskSub.md"
        assert effective.config.flatten is True


def test_resolve_effective_perspective_inherit_not_clears_parent_layers():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        root = tmp / "Project"
        sub = root / "Sub"
        root.mkdir(parents=True)
        sub.mkdir(parents=True)
        (root / "Perspective.md").write_text(
            "# Perspective\nName: Root\n\n## Include\n/finanz/\n",
            encoding="utf-8",
        )
        (sub / "Perspective.md").write_text(
            "# Perspective\nName: Sub\nInherit: not\n\n## Include\n/recht/\n",
            encoding="utf-8",
        )

        effective = resolve_effective_perspective(sub)

        assert effective is not None
        assert effective.config.include == ["/recht/"]
        assert effective.layers[0].config.name == "Sub"


def test_project_entries_applies_include_exclude_and_group():
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
        cfg_file = cwd / "Perspective.md"
        cfg_file.write_text(
            "\n".join(
                [
                    "# Perspective",
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
        effective = resolve_effective_perspective(cwd)
        assert effective is not None
        entries = [
            {"name": "invoice1.pdf", "path": str(keep), "isDir": False, "tags": []},
            {"name": "image.jpg", "path": str(drop), "isDir": False, "tags": []},
        ]

        projected = project_entries(entries, cwd=cwd, perspective=effective, project_root=cwd)

        assert len(projected) == 1
        assert projected[0]["name"] == "invoice1.pdf"
        assert projected[0]["perspectiveActive"] is True
        assert "perspectiveGroup" in projected[0]
