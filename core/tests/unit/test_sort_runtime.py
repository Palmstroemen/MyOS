from pathlib import Path

from core.sort import SortRule
from core.sort_runtime import SortRuntime


def _rule(root: Path, pattern: str, date_sources=None, conflict: str = "rename") -> SortRule:
    return SortRule(
        source_path=root / ".MyOS" / "Sort.md",
        owner_root=root,
        root="/Pictures",
        pattern=pattern,
        date_sources=list(date_sources or ["frontmatter_date", "fs_mtime"]),
        apply_on="both",
        materialization="on_use",
        conflict=conflict,
        enabled=True,
    )


def test_sort_runtime_uses_frontmatter_before_fs_mtime(tmp_path):
    project = tmp_path / "Project"
    pictures = project / "Pictures"
    pictures.mkdir(parents=True)
    note = pictures / "trip.md"
    note.write_text("---\ndate: 2024-05-01\n---\n# Trip\n", encoding="utf-8")
    runtime = SortRuntime()
    rule = _rule(project, "{{YYYY}}/{{MM}}/{{DD}}")

    preview = runtime.preview_target(note, [rule], event="move")

    assert preview["ok"] == "1"
    assert preview["target"].endswith("/Pictures/2024/05/01")


def test_sort_runtime_apply_file_moves_and_renames_on_conflict(tmp_path):
    project = tmp_path / "Project"
    pictures = project / "Pictures"
    pictures.mkdir(parents=True)
    runtime = SortRuntime()
    rule = _rule(project, "{{YYYY}}", date_sources=["fs_mtime"], conflict="rename")

    source_a = pictures / "a.txt"
    source_b = pictures / "a.txt.copy"
    source_a.write_text("A", encoding="utf-8")
    source_b.write_text("B", encoding="utf-8")

    # Force same target name by renaming before second apply.
    first = runtime.apply_file(source_a, [rule], event="move")
    moved_first = Path(first["destination"])
    moved_first_parent = moved_first.parent
    conflict_target = moved_first_parent / source_b.name
    if conflict_target.exists():
        conflict_target.unlink()
    source_b.rename(pictures / "a.txt")
    second_source = pictures / "a.txt"
    runtime.self_move_ttl_s = 0.0

    second = runtime.apply_file(second_source, [rule], event="move")

    assert first["ok"] == "1"
    assert second["ok"] == "1"
    assert Path(second["destination"]).exists()
    assert Path(second["destination"]).name.startswith("a")


def test_sort_runtime_apply_root_is_idempotent_for_already_sorted_files(tmp_path):
    project = tmp_path / "Project"
    pictures = project / "Pictures"
    pictures.mkdir(parents=True)
    file_path = pictures / "x.txt"
    file_path.write_text("x", encoding="utf-8")
    runtime = SortRuntime()
    rule = _rule(project, "{{YYYY}}", date_sources=["fs_mtime"])

    first = runtime.apply_root(pictures, [rule], event="move")
    second = runtime.apply_root(pictures, [rule], event="move")

    assert first["ok"] is True
    assert isinstance(first["moved"], list)
    assert second["ok"] is True
