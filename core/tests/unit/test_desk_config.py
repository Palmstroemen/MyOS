from pathlib import Path

import pytest
import random
import string

from core.desk import find_desks, resolve_active_desk
from core.desk_runtime import DeskRuntime, DeskRuntimeSettings
from core.desktop_backends.base import BackendStepResult, DesktopBackend


def _write_desk(path: Path, theme: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Desk",
                f"ThemePreset: {theme}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


class _RecordingBackend(DesktopBackend):
    name = "recording"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _ok(self, name: str) -> BackendStepResult:
        self.calls.append(name)
        return BackendStepResult(ok=True, message=name)

    def apply_theme(self, config, *, dry_run: bool = True) -> BackendStepResult:
        return self._ok("theme")

    def apply_wallpaper(self, config, *, dry_run: bool = True) -> BackendStepResult:
        return self._ok("wallpaper")

    def apply_dock(self, config, *, dry_run: bool = True) -> BackendStepResult:
        return self._ok("dock")

    def apply_recent_policy(self, config, *, dry_run: bool = True) -> BackendStepResult:
        return self._ok("recent_policy")


class _FailingDockBackend(_RecordingBackend):
    def __init__(self) -> None:
        super().__init__()
        self.rollback_calls: list[list[str]] = []

    def apply_dock(self, config, *, dry_run: bool = True) -> BackendStepResult:
        self.calls.append("dock")
        return BackendStepResult(ok=False, message="dock boom")

    def apply_recent_policy(self, config, *, dry_run: bool = True) -> BackendStepResult:
        self.calls.append("recent_policy")
        return BackendStepResult(ok=True, message="recent_policy")

    def rollback(self, config, *, applied_steps: list[str], dry_run: bool = True) -> BackendStepResult:
        self.rollback_calls.append(list(applied_steps))
        return BackendStepResult(ok=True, message="rollback ok")


def test_find_desks_and_nearest_ancestor_selection(tmp_path):
    root = tmp_path / "Project"
    deep = root / "Sub" / "Deep"
    deep.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    _write_desk(root / "Sub" / ".MyOS" / "Desk.md", "SubTheme")

    matches = find_desks(deep)

    assert len(matches) >= 2
    assert matches[0][0] == (root / "Sub" / ".MyOS" / "Desk.md")
    assert matches[0][1].theme_preset == "SubTheme"
    assert matches[1][0] == (root / ".MyOS" / "Desk.md")
    assert matches[1][1].theme_preset == "RootTheme"


def test_resolve_active_desk_inherits_from_parent_when_child_missing(tmp_path):
    root = tmp_path / "Project"
    child = root / "Child"
    child.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")

    resolved = resolve_active_desk(child)

    assert resolved is not None
    assert resolved.source_path == (root / ".MyOS" / "Desk.md")
    assert resolved.theme_preset == "RootTheme"


def test_resolve_active_desk_skips_malformed_local_file_and_falls_back(tmp_path):
    root = tmp_path / "Project"
    child = root / "Child"
    child.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    malformed = child / ".MyOS" / "Desk.md"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    malformed.write_text("this line is not parser compatible\n", encoding="utf-8")

    resolved = resolve_active_desk(child)

    assert resolved is not None
    assert resolved.source_path == (root / ".MyOS" / "Desk.md")
    assert resolved.theme_preset == "RootTheme"


def test_manual_override_wins_over_nearest_ancestor(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    manual = tmp_path / "ManualDesk.md"
    _write_desk(manual, "ManualTheme")

    resolved = resolve_active_desk(sub, manual=manual)

    assert resolved is not None
    assert resolved.source_path == manual
    assert resolved.theme_preset == "ManualTheme"


def test_root_desk_candidate_requires_opt_in(tmp_path):
    root = tmp_path / "Project"
    child = root / "Child"
    child.mkdir(parents=True)
    _write_desk(root / "Desk.md", "RootDeskTheme")

    without_opt_in = resolve_active_desk(child, include_root_desk=False)
    with_opt_in = resolve_active_desk(child, include_root_desk=True)

    assert without_opt_in is None
    assert with_opt_in is not None
    assert with_opt_in.source_path == (root / "Desk.md")


def test_filter_linked_desk_overrides_nearest_ancestor(tmp_path):
    root = tmp_path / "Project"
    work = root / "Work"
    work.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    _write_desk(work / "FinanceDesk.md", "FinanceTheme")
    (work / "Filter.md").write_text(
        "\n".join(
            [
                "# Filter",
                "Name: Finance",
                "",
                "## Desk",
                "FinanceDesk.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    resolved = resolve_active_desk(work)

    assert resolved is not None
    assert resolved.source_path == (work / "FinanceDesk.md")
    assert resolved.theme_preset == "FinanceTheme"


def test_symlinked_local_desk_is_ignored_for_security(tmp_path):
    root = tmp_path / "Project"
    child = root / "Child"
    child.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    outside = tmp_path / "OutsideDesk.md"
    _write_desk(outside, "OutsideTheme")
    symlink_path = child / ".MyOS" / "Desk.md"
    symlink_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        symlink_path.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation not supported in this environment")

    resolved = resolve_active_desk(child)

    assert resolved is not None
    assert resolved.source_path == (root / ".MyOS" / "Desk.md")
    assert resolved.theme_preset == "RootTheme"


def test_filter_symlink_escape_is_ignored_for_security(tmp_path):
    root = tmp_path / "Project"
    work = root / "Work"
    work.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    outside = tmp_path / "OutsideDesk.md"
    _write_desk(outside, "OutsideTheme")
    desk_link = work / "DeskLink.md"
    try:
        desk_link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation not supported in this environment")
    (work / "Filter.md").write_text(
        "# Filter\nName: Unsafe\n\n## Desk\nDeskLink.md\n",
        encoding="utf-8",
    )

    resolved = resolve_active_desk(work)

    assert resolved is not None
    assert resolved.source_path == (root / ".MyOS" / "Desk.md")
    assert resolved.theme_preset == "RootTheme"


def test_runtime_reapplies_only_when_profile_identity_changes(tmp_path):
    root = tmp_path / "Project"
    sub = root / "Sub"
    sub.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")
    _write_desk(sub / ".MyOS" / "Desk.md", "SubTheme")

    backend = _RecordingBackend()
    runtime = DeskRuntime(
        settings=DeskRuntimeSettings(
            enabled=True,
            dry_run=True,
            backend_name="none",
            include_root_desk=False,
            prefer_filter_desk=True,
            fallback_profile=None,
        ),
        backend=backend,
    )

    first = runtime.handle_context(sub)
    second = runtime.handle_context(sub)
    third = runtime.handle_context(root)

    assert first["ok"] is True
    assert first["reason"] == "dry_run"
    assert first["source"] == str(sub / ".MyOS" / "Desk.md")
    assert second["reason"] == "unchanged"
    assert third["ok"] is True
    assert third["reason"] == "dry_run"
    assert third["source"] == str(root / ".MyOS" / "Desk.md")
    # Two apply cycles x 4 ordered operations.
    assert backend.calls == [
        "theme",
        "wallpaper",
        "dock",
        "recent_policy",
        "theme",
        "wallpaper",
        "dock",
        "recent_policy",
    ]


def test_runtime_stops_on_first_failed_step_and_triggers_rollback(tmp_path):
    root = tmp_path / "Project"
    root.mkdir(parents=True)
    _write_desk(root / ".MyOS" / "Desk.md", "RootTheme")

    backend = _FailingDockBackend()
    runtime = DeskRuntime(
        settings=DeskRuntimeSettings(
            enabled=True,
            dry_run=False,
            backend_name="none",
            include_root_desk=False,
            prefer_filter_desk=True,
            fallback_profile=None,
        ),
        backend=backend,
    )

    result = runtime.handle_context(root)

    assert result["ok"] is False
    assert result["reason"] == "apply_failed"
    assert [step["name"] for step in result["steps"]] == ["theme", "wallpaper", "dock", "rollback"]
    assert backend.calls == ["theme", "wallpaper", "dock"]
    assert backend.rollback_calls == [["theme", "wallpaper"]]


def test_desk_config_from_data_handles_weird_types_without_crash(tmp_path):
    path = tmp_path / "Project" / ".MyOS" / "Desk.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    weird = {
        "Desk": [
            {"ThemePreset": 123},
            {"WallpaperPreset": ["a.png", None, ""]},
            {"DockPreset": {"nested": "value"}},
            {"RecentPolicy": False},
            {"Inherit": ["invalid-value"]},
        ]
    }

    parsed = resolve_active_desk(tmp_path, manual=path, fallback=None)
    assert parsed is None

    from core.desk import DeskConfig

    cfg = DeskConfig.from_data(path, weird)

    assert cfg.theme_preset == "123"
    assert cfg.wallpaper_preset == "a.png"
    assert cfg.dock_preset == "{'nested': 'value'}"
    assert cfg.recent_policy == "False"
    assert cfg.inherit == "dynamic"


def test_resolve_active_desk_handles_malformed_manual_path_and_uses_fallback(tmp_path):
    fallback = tmp_path / "fallback" / ".MyOS" / "Desk.md"
    _write_desk(fallback, "FallbackTheme")

    resolved = resolve_active_desk(tmp_path, manual="bad\0path", fallback=fallback)

    assert resolved is not None
    assert resolved.source_path == fallback
    assert resolved.theme_preset == "FallbackTheme"


def test_desk_config_fuzz_from_data_is_stable_and_never_throws(tmp_path):
    from core.desk import DeskConfig

    rng = random.Random(1337)
    allowed_inherit = {"dynamic", "fix", "not"}
    source = tmp_path / "Project" / ".MyOS" / "Desk.md"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("# Desk\n", encoding="utf-8")

    def _random_scalar():
        choice = rng.randint(0, 8)
        if choice == 0:
            return None
        if choice == 1:
            return rng.randint(-10_000, 10_000)
        if choice == 2:
            return rng.random()
        if choice == 3:
            return bool(rng.randint(0, 1))
        if choice == 4:
            length = rng.randint(0, 80)
            alphabet = string.ascii_letters + string.digits + " _-:;#/\\[]{}"
            return "".join(rng.choice(alphabet) for _ in range(length))
        if choice == 5:
            return []
        if choice == 6:
            return {}
        if choice == 7:
            return ["dynamic", "fix", "not", "invalid", "", "###"][rng.randint(0, 5)]
        return "DeskValue"

    def _random_value(depth: int = 0):
        if depth > 2:
            return _random_scalar()
        kind = rng.randint(0, 4)
        if kind <= 1:
            return _random_scalar()
        if kind == 2:
            return [_random_value(depth + 1) for _ in range(rng.randint(0, 5))]
        if kind == 3:
            return {f"key_{rng.randint(0, 9)}": _random_value(depth + 1) for _ in range(rng.randint(0, 4))}
        return [{"k": _random_value(depth + 1)} for _ in range(rng.randint(0, 4))]

    for _ in range(300):
        desk_payload = _random_value()
        data = {"Desk": desk_payload}
        cfg = DeskConfig.from_data(source, data)
        assert cfg.inherit in allowed_inherit
        assert isinstance(cfg.raw, dict)


def test_desk_config_fuzz_markdown_parse_is_stable(tmp_path):
    rng = random.Random(4242)
    root = tmp_path / "Project"
    root.mkdir(parents=True, exist_ok=True)
    fallback = root / ".MyOS" / "Desk.md"
    _write_desk(fallback, "FallbackTheme")
    manual = root / "manual.md"

    for _ in range(120):
        lines = []
        # Randomly include header, random gibberish, and random key/value-ish lines.
        if rng.randint(0, 1):
            lines.append("# Desk")
        line_count = rng.randint(1, 40)
        for _line in range(line_count):
            pick = rng.randint(0, 6)
            if pick == 0:
                lines.append("")
            elif pick == 1:
                lines.append("ThemePreset: " + "".join(rng.choice(string.ascii_letters + string.digits + "_-") for _ in range(rng.randint(0, 30))))
            elif pick == 2:
                lines.append("WallpaperPath: " + "".join(rng.choice(string.printable.replace("\n", "")) for _ in range(rng.randint(0, 60))))
            elif pick == 3:
                lines.append("Inherit: " + rng.choice(["dynamic", "fix", "not", "invalid", "", "x:y:z"]))
            elif pick == 4:
                lines.append("#### inherit: " + rng.choice(["dynamic", "not", "oops"]))
            elif pick == 5:
                lines.append("* " + "".join(rng.choice(string.ascii_letters + string.digits + " _-") for _ in range(rng.randint(0, 25))))
            else:
                lines.append("".join(rng.choice(string.printable.replace("\n", "")) for _ in range(rng.randint(0, 70))))
        manual.write_text("\n".join(lines) + "\n", encoding="utf-8", errors="replace")

        resolved = resolve_active_desk(root, manual=manual, fallback=fallback)
        assert resolved is not None
        assert resolved.inherit in {"dynamic", "fix", "not"}
