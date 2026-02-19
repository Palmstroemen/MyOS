from pathlib import Path

from core.localBlueprintLayer import Blueprint


def _create_project(path: Path) -> None:
    myos = path / ".MyOS"
    myos.mkdir(parents=True, exist_ok=True)
    (myos / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")


def test_blueprint_projects_virtual_sort_level(monkeypatch, tmp_path):
    project = tmp_path / "Project"
    templates = tmp_path / "Templates"
    templates.mkdir(parents=True)
    _create_project(project)
    (project / ".MyOS" / "Sort.md").write_text(
        "# Sort\nRoot: /Pictures\nPattern: {{YYYY}}/{{MM}}\nDateSource: fs_mtime\n",
        encoding="utf-8",
    )
    pictures = project / "Pictures"
    pictures.mkdir(parents=True)
    (pictures / "a.txt").write_text("A", encoding="utf-8")
    monkeypatch.setenv("MYOS_TEMPLATES_DIR", str(templates))

    layer = Blueprint(project)
    entries = layer.readdir("/Pictures", None)

    assert any(item.isdigit() and len(item) == 4 for item in entries)


def test_blueprint_create_materializes_sort_virtual_parents(monkeypatch, tmp_path):
    project = tmp_path / "Project"
    templates = tmp_path / "Templates"
    templates.mkdir(parents=True)
    _create_project(project)
    (project / ".MyOS" / "Sort.md").write_text(
        "# Sort\nRoot: /Pictures\nPattern: {{YYYY}}/{{MM}}/{{DD}}\nDateSource: fs_mtime\n",
        encoding="utf-8",
    )
    (project / "Pictures").mkdir(parents=True)
    monkeypatch.setenv("MYOS_TEMPLATES_DIR", str(templates))

    layer = Blueprint(project)
    fd = layer.create("/Pictures/2024/05/new.txt", 0o644, None)
    layer.write("/Pictures/2024/05/new.txt", b"x", 0, fd)
    layer.release("/Pictures/2024/05/new.txt", fd)

    assert (project / "Pictures" / "2024" / "05" / "new.txt").exists()
