"""Folder sizes are measured live (two passes in Scope), never persisted."""

from pathlib import Path

from core.scope_api import ScopeApi


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "Project"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n", encoding="utf-8")
    return root


def _tree(folder: Path) -> int:
    """Folder with nested files; returns the total size in bytes."""
    (folder / "sub" / "deep").mkdir(parents=True)
    (folder / "a.bin").write_bytes(b"x" * 100)
    (folder / "sub" / "b.bin").write_bytes(b"x" * 20)
    (folder / "sub" / "deep" / "c.bin").write_bytes(b"x" * 3)
    return 123


def test_measure_folder_size_sums_nested_files(tmp_path):
    root = _project(tmp_path)
    total = _tree(root / "Docs")

    result = ScopeApi(str(root)).measure_folder_size(str(root / "Docs"))

    assert result == {"bytes": total, "complete": True}


def test_measure_folder_size_ignores_symlinks(tmp_path):
    root = _project(tmp_path)
    total = _tree(root / "Docs")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "huge.bin").write_bytes(b"x" * 5000)
    (root / "Docs" / "link_dir").symlink_to(outside)
    (root / "Docs" / "link_file").symlink_to(outside / "huge.bin")

    result = ScopeApi(str(root)).measure_folder_size(str(root / "Docs"))

    assert result == {"bytes": total, "complete": True}


def test_measure_folder_size_with_budget_returns_lower_bound(tmp_path):
    """First pass: stop after max_entries and report what was counted so far."""
    root = _project(tmp_path)
    total = _tree(root / "Docs")

    result = ScopeApi(str(root)).measure_folder_size(str(root / "Docs"), max_entries=2)

    assert result["complete"] is False
    assert 0 <= result["bytes"] < total


def test_measure_folder_size_budget_large_enough_is_complete(tmp_path):
    root = _project(tmp_path)
    total = _tree(root / "Docs")

    result = ScopeApi(str(root)).measure_folder_size(str(root / "Docs"), max_entries=1000)

    assert result == {"bytes": total, "complete": True}


def test_measure_folder_size_does_not_cross_filesystem_boundaries(tmp_path, monkeypatch):
    """Like du -x: a mount below the folder (other drive, FUSE perspective) is not walked."""
    root = _project(tmp_path)
    _tree(root / "Docs")
    mounted = root / "Docs" / "sub"
    api = ScopeApi(str(root))
    real_device_id = ScopeApi._device_id
    monkeypatch.setattr(
        ScopeApi,
        "_device_id",
        staticmethod(lambda path: -1 if Path(path) == mounted else real_device_id(path)),
    )

    result = api.measure_folder_size(str(root / "Docs"))

    assert result == {"bytes": 100, "complete": True}


def test_measure_folder_size_of_missing_folder_is_zero(tmp_path):
    root = _project(tmp_path)

    assert ScopeApi(str(root)).measure_folder_size(str(root / "Embryo")) == {"bytes": 0, "complete": True}


def test_file_entries_carry_their_size(tmp_path):
    root = _project(tmp_path)
    (root / "a.txt").write_bytes(b"x" * 42)
    (root / "Folder").mkdir()
    api = ScopeApi(str(root))

    for entries in (api.list_entries(str(root)), api.list_entries_quick(str(root), False)):
        by_name = {e["name"]: e for e in entries}
        assert by_name["a.txt"]["sizeBytes"] == 42
        assert "sizeBytes" not in by_name["Folder"]


def test_viewing_a_folder_does_not_touch_project_md(tmp_path):
    root = _project(tmp_path)
    _tree(root / "Docs")
    project_md = root / ".MyOS" / "Project.md"
    before = project_md.read_text(encoding="utf-8")
    api = ScopeApi(str(root))

    api.list_entries(str(root / "Docs"))
    api.list_tag_buckets(str(root / "Docs"))

    assert project_md.read_text(encoding="utf-8") == before


def test_measure_folder_size_works_outside_projects(tmp_path):
    """Sizes are a general file-browser feature, not limited to MyOS projects."""
    outside = tmp_path / "Plain"
    total = _tree(outside)
    api = ScopeApi(str(tmp_path))

    assert api.measure_folder_size(str(outside)) == {"bytes": total, "complete": True}


def test_measure_folder_size_can_be_cancelled_mid_walk(tmp_path):
    """A huge folder must not block navigation or quitting: the walk stops when asked."""
    root = _project(tmp_path)
    big = root / "Big"
    big.mkdir()
    for i in range(1000):
        (big / f"f{i}.bin").write_bytes(b"x")
    calls = []

    def should_continue():
        calls.append(1)
        return len(calls) < 2

    result = ScopeApi(str(root)).measure_folder_size(str(big), should_continue=should_continue)

    assert result["complete"] is False
    assert result["bytes"] < 1000


def test_list_entries_skips_details_of_unreadable_children(tmp_path):
    """One unreadable child (like /root or /lost+found) must not empty the whole listing."""
    root = _project(tmp_path)
    (root / "ok.txt").write_text("x", encoding="utf-8")
    locked = root / "Locked"
    (locked / ".MyOS").mkdir(parents=True)
    (locked / ".MyOS" / "myTags.md").write_text("#tag\n", encoding="utf-8")
    locked.chmod(0o000)
    try:
        names = {e["name"] for e in ScopeApi(str(root)).list_entries(str(root))}
    finally:
        locked.chmod(0o755)

    assert {"ok.txt", "Locked"} <= names


def test_entries_carry_modification_time(tmp_path):
    """List view column "Geändert": files and folders carry their mtime; embryos do not."""
    import os

    root = _project(tmp_path)
    (root / "a.txt").write_text("x", encoding="utf-8")
    (root / "Folder").mkdir()
    os.utime(root / "a.txt", (1_700_000_000, 1_700_000_000))
    os.utime(root / "Folder", (1_600_000_000, 1_600_000_000))
    api = ScopeApi(str(root))

    for entries in (api.list_entries(str(root)), api.list_entries_quick(str(root), False)):
        by_name = {e["name"]: e for e in entries}
        assert by_name["a.txt"]["modifiedTs"] == 1_700_000_000
        assert by_name["Folder"]["modifiedTs"] == 1_600_000_000
