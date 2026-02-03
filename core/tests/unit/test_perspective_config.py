# test_perspective_config.py

import tempfile
from pathlib import Path

import pytest

from core.perspective import PerspectiveConfig
from core.perspective import find_perspectives, resolve_active_perspective


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
