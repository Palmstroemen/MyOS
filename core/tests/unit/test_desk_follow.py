"""The desktop follows the projects (see "Designdocument Desk.md", 12).

Inside the projects tree the nearest .MyOS/Desk.md applies (up to the top project);
outside it, or when none is found, the user's own desktop (system default, kept in
~/.config/MyOS/Desk.md). Changes the user makes are saved, without asking, into the
Desk.md of the project they were made in (outside projects: the system default).
A fake backend stands in for the real desktop."""

from dataclasses import replace
from pathlib import Path
from typing import Optional

import pytest

from core.desk_runtime import DeskRuntime, DeskRuntimeSettings
from core.desk_service import DeskService, desk_home
from core.desktop_backends.base import BackendStepResult, DesktopBackend, DesktopState


@pytest.fixture(autouse=True)
def _own_config_home(monkeypatch, tmp_path_factory):
    # Security: these tests write the system default and desk-state.json. Isolate them
    # here too, not only in the root conftest.py (which is missing when the file is
    # run from elsewhere), so the user's ~/.config/MyOS is never touched.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path_factory.mktemp("config")))
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")


class FakeDesktop(DesktopBackend):
    """A desktop that applies Desk.md values and can be changed by "the user"."""

    name = "fake"

    def __init__(self, theme="Mint-Y", wallpaper="/usr/share/backgrounds/default.jpg", panel_theme="Linux Mint",
                 taskbar=("nemo.desktop",)):
        self.state = DesktopState(theme=theme, wallpaper=wallpaper, panel_theme=panel_theme, taskbar=taskbar)
        self.applied = 0

    def capture(self) -> Optional[DesktopState]:
        return self.state

    def apply_theme(self, config, *, dry_run=True):
        if config.theme_preset and not dry_run:
            self.state = replace(self.state, theme=config.theme_preset)
            self.applied += 1
        return BackendStepResult(ok=True)

    def apply_panel_theme(self, config, *, dry_run=True):
        if config.panel_theme and not dry_run:
            self.state = replace(self.state, panel_theme=config.panel_theme)
        return BackendStepResult(ok=True)

    def apply_wallpaper(self, config, *, dry_run=True):
        if config.wallpaper_path and not dry_run:
            self.state = replace(self.state, wallpaper=config.wallpaper_path)
            self.applied += 1
        return BackendStepResult(ok=True)

    def apply_dock(self, config, *, dry_run=True):
        if config.taskbar is not None and not dry_run:
            self.state = replace(self.state, taskbar=config.taskbar)
        return BackendStepResult(ok=True)

    def user_changes(self, theme=None, wallpaper=None, panel_theme=None, taskbar=None):
        self.state = DesktopState(
            theme=theme or self.state.theme,
            wallpaper=wallpaper or self.state.wallpaper,
            panel_theme=panel_theme or self.state.panel_theme,
            taskbar=self.state.taskbar if taskbar is None else taskbar,
        )


SETTINGS = DeskRuntimeSettings(
    enabled=True, dry_run=False, backend_name="fake",
    include_root_desk=False, prefer_filter_desk=True, fallback_profile=None,
)


def _service(desktop: FakeDesktop) -> DeskService:
    return DeskService(runtime=DeskRuntime(settings=SETTINGS, backend=desktop))


def _project(path: Path, desk: Optional[str] = None) -> Path:
    (path / ".MyOS").mkdir(parents=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    if desk is not None:
        (path / ".MyOS" / "Desk.md").write_text(desk)
    return path


@pytest.fixture
def tree(tmp_path):
    """Projekte (top project, with a desk) / Garten (own desk) / Hecke, and Haus (no desk)."""
    top = _project(tmp_path / "Projekte", "# Desk\nThemePreset: Projekte-Theme\nWallpaperPath: /bg/projekte.jpg\n")
    garten = _project(top / "Garten", "# Desk\nThemePreset: Garten-Theme\nWallpaperPath: /bg/garten.jpg\nProjectIcon: plant\n")
    (garten / "Hecke").mkdir()
    haus = _project(top / "Haus")
    outside = tmp_path / "Musik"
    outside.mkdir()
    return {"top": top, "garten": garten, "hecke": garten / "Hecke", "haus": haus, "outside": outside}


def _desk(path: Path) -> str:
    return (path / ".MyOS" / "Desk.md").read_text()


def test_entering_projects_applies_the_nearest_desk(tree):
    desktop = FakeDesktop()
    service = _service(desktop)

    service.refresh_context(tree["hecke"])
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Garten-Theme", "/bg/garten.jpg")

    service.refresh_context(tree["haus"])  # no Desk.md of its own: the parent's
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Projekte-Theme", "/bg/projekte.jpg")


def test_the_users_own_desktop_is_kept_and_restored_outside_projects(tree):
    desktop = FakeDesktop("Mint-Y", "/usr/share/backgrounds/default.jpg")
    service = _service(desktop)

    service.refresh_context(tree["garten"])
    system_default = (desk_home() / "Desk.md").read_text()
    assert "ThemePreset: Mint-Y\n" in system_default
    assert "WallpaperPath: /usr/share/backgrounds/default.jpg\n" in system_default

    service.refresh_context(tree["outside"])
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Mint-Y", "/usr/share/backgrounds/default.jpg")


def test_a_desk_above_the_projects_tree_is_ignored(tree, tmp_path):
    (tmp_path / ".MyOS").mkdir()
    (tmp_path / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Fremd\n")
    desktop = FakeDesktop()

    _service(desktop).refresh_context(tree["outside"])

    assert desktop.state.theme == "Mint-Y"


def test_changes_are_saved_into_the_project_they_were_made_in(tree):
    desktop = FakeDesktop()
    service = _service(desktop)
    service.refresh_context(tree["hecke"])

    desktop.user_changes(theme="Mein-Theme", wallpaper="/bg/mein.jpg")
    service.refresh_context(tree["haus"])

    text = _desk(tree["garten"])
    assert "ThemePreset: Mein-Theme\n" in text and "WallpaperPath: /bg/mein.jpg\n" in text
    assert "ProjectIcon: plant\n" in text  # other settings stay
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Projekte-Theme", "/bg/projekte.jpg")

    service.refresh_context(tree["garten"])
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Mein-Theme", "/bg/mein.jpg")


def test_a_project_without_desk_gets_one_when_the_user_changes_the_desktop(tree):
    desktop = FakeDesktop()
    service = _service(desktop)
    service.refresh_context(tree["haus"])

    desktop.user_changes(wallpaper="/bg/haus.jpg")
    service.refresh_context(tree["garten"])

    text = _desk(tree["haus"])
    assert text.startswith("# Desk\n")
    assert "WallpaperPath: /bg/haus.jpg\n" in text and "ThemePreset: Projekte-Theme\n" in text


def test_changes_outside_projects_update_the_system_default(tree):
    desktop = FakeDesktop()
    service = _service(desktop)
    service.refresh_context(tree["outside"])

    desktop.user_changes(theme="Neu-Theme")
    service.refresh_context(tree["garten"])
    service.refresh_context(tree["outside"])

    assert "ThemePreset: Neu-Theme\n" in (desk_home() / "Desk.md").read_text()
    assert desktop.state.theme == "Neu-Theme"


def test_myos_own_changes_are_not_saved_as_user_changes(tree):
    desktop = FakeDesktop()
    service = _service(desktop)

    for place in ("garten", "haus", "hecke", "outside", "haus"):
        service.refresh_context(tree[place])

    assert not (tree["haus"] / ".MyOS" / "Desk.md").exists()
    assert "Projekte-Theme" not in (desk_home() / "Desk.md").read_text()


def test_scope_and_postfix_share_what_myos_set_last(tree):
    desktop = FakeDesktop()
    scope, postfix = _service(desktop), _service(desktop)

    scope.refresh_context(tree["garten"])
    postfix.refresh_context(tree["haus"])  # PostFix opens a note elsewhere
    scope.refresh_context(tree["hecke"])

    assert "Projekte-Theme" not in _desk(tree["garten"])
    assert (desktop.state.theme, desktop.state.wallpaper) == ("Garten-Theme", "/bg/garten.jpg")


def test_without_a_desktop_backend_nothing_is_written(tree):
    service = DeskService(runtime=DeskRuntime(settings=SETTINGS, backend=DesktopBackend()))

    service.refresh_context(tree["haus"])
    service.refresh_context(tree["garten"])

    assert not (desk_home() / "Desk.md").exists()
    assert not (tree["haus"] / ".MyOS" / "Desk.md").exists()


def test_writing_keeps_other_lines_and_refuses_symlinks(tmp_path):
    from core.desk_service import write_desk_values

    desk = tmp_path / "Desk.md"
    desk.write_text("Notiz oben\n\n# Desk\nProjectIcon: plant\nWallpaperPath: /alt.jpg\n\n# Andere\nx: 1\n")
    write_desk_values(desk, DesktopState(theme="Neu", wallpaper="/neu.jpg"))
    assert desk.read_text() == (
        "Notiz oben\n\n# Desk\nThemePreset: Neu\nProjectIcon: plant\nWallpaperPath: /neu.jpg\n\n# Andere\nx: 1\n"
    )

    target = tmp_path / "elsewhere.md"
    target.write_text("# Desk\n")
    link = tmp_path / "Link.md"
    link.symlink_to(target)
    with pytest.raises(OSError):
        write_desk_values(link, DesktopState(theme="Neu"))
    assert target.read_text() == "# Desk\n"


def test_inherit_not_stops_the_search_upwards(tree):
    (tree["haus"] / ".MyOS" / "Desk.md").write_text("# Desk\nInherit: not\n")
    desktop = FakeDesktop("Mint-Y", "/usr/share/backgrounds/default.jpg")
    service = _service(desktop)
    service.refresh_context(tree["garten"])

    service.refresh_context(tree["haus"])  # not the parent's look: the user's own desktop

    assert (desktop.state.theme, desktop.state.wallpaper) == ("Mint-Y", "/usr/share/backgrounds/default.jpg")


def test_after_a_change_the_same_profile_is_applied_again(tree):
    # Haus inherits the Projekte desk; the top project uses the same one. After the user
    # changed the desktop in Haus, going to the top must still restore its look.
    desktop = FakeDesktop()
    service = _service(desktop)
    service.refresh_context(tree["haus"])

    desktop.user_changes(wallpaper="/bg/haus.jpg")
    service.refresh_context(tree["top"])

    assert (desktop.state.theme, desktop.state.wallpaper) == ("Projekte-Theme", "/bg/projekte.jpg")
    assert "WallpaperPath: /bg/haus.jpg\n" in _desk(tree["haus"])


def test_after_a_change_outside_projects_the_own_desktop_is_restored(tree):
    # The live case: no desks at all, so everything uses the system default.
    for desk in tree["top"].rglob("Desk.md"):
        desk.unlink()
    desktop = FakeDesktop("Mint-Y", "/usr/share/backgrounds/default.jpg")
    service = _service(desktop)
    service.refresh_context(tree["garten"])

    desktop.user_changes(wallpaper="/bg/gruen.jpg")
    service.refresh_context(tree["outside"])

    assert (desktop.state.theme, desktop.state.wallpaper) == ("Mint-Y", "/usr/share/backgrounds/default.jpg")
    assert "WallpaperPath: /bg/gruen.jpg\n" in _desk(tree["garten"])


def test_the_panel_theme_follows_the_projects_too(tree):
    desktop = FakeDesktop(panel_theme="Linux Mint")
    service = _service(desktop)
    service.refresh_context(tree["garten"])

    desktop.user_changes(panel_theme="Mint-Y-Dark-Teal")  # set in the system settings
    service.refresh_context(tree["outside"])

    assert "PanelTheme: Mint-Y-Dark-Teal\n" in _desk(tree["garten"])
    assert "PanelTheme: Linux Mint\n" in (desk_home() / "Desk.md").read_text()
    assert desktop.state.panel_theme == "Linux Mint"

    service.refresh_context(tree["hecke"])
    assert desktop.state.panel_theme == "Mint-Y-Dark-Teal"


def test_what_a_desk_leaves_open_does_not_stay_from_the_previous_project(tree):
    # Garten has a blue taskbar; Haus only sets a wallpaper. In Haus the taskbar must not
    # stay blue: the theme comes from Projekte, the taskbar from the user's own desktop.
    (tree["garten"] / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Garten-Theme\nPanelTheme: Mint-Y-Blue\n")
    (tree["haus"] / ".MyOS" / "Desk.md").write_text("# Desk\nWallpaperPath: /bg/haus.jpg\n")
    desktop = FakeDesktop(panel_theme="Linux Mint")
    service = _service(desktop)
    service.refresh_context(tree["garten"])
    assert desktop.state.panel_theme == "Mint-Y-Blue"

    service.refresh_context(tree["haus"])

    assert desktop.state == DesktopState(theme="Projekte-Theme", wallpaper="/bg/haus.jpg", panel_theme="Linux Mint",
                                         taskbar=("nemo.desktop",))


def test_the_taskbar_follows_the_projects(tree):
    (tree["garten"] / ".MyOS" / "Desk.md").write_text(
        "# Desk\nThemePreset: Garten-Theme\n\n## Taskbar\n- nemo.desktop\n- gimp.desktop\n"
    )
    desktop = FakeDesktop(taskbar=("nemo.desktop", "firefox.desktop"))
    service = _service(desktop)

    service.refresh_context(tree["hecke"])
    assert desktop.state.taskbar == ("nemo.desktop", "gimp.desktop")

    desktop.user_changes(taskbar=("gimp.desktop", "inkscape.desktop"))  # pinned in the taskbar
    service.refresh_context(tree["outside"])

    assert desktop.state.taskbar == ("nemo.desktop", "firefox.desktop")
    assert _desk(tree["garten"]).endswith("## Taskbar\n- gimp.desktop\n- inkscape.desktop\n")
    service.refresh_context(tree["garten"])
    assert desktop.state.taskbar == ("gimp.desktop", "inkscape.desktop")


def test_an_existing_system_default_learns_the_own_taskbar(tree):
    # Before MyOS knew the taskbar the system default was saved without it; MyOS never
    # changed the taskbar, so what is pinned now is the user's own.
    desktop = FakeDesktop(taskbar=None)
    service = _service(desktop)
    service.refresh_context(tree["outside"])
    assert "Taskbar" not in (desk_home() / "Desk.md").read_text()
    (tree["garten"] / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Garten-Theme\n## Taskbar\n- gimp.desktop\n")

    desktop.state = replace(desktop.state, taskbar=("nemo.desktop", "firefox.desktop"))  # MyOS now reads it
    service.refresh_context(tree["garten"])
    assert desktop.state.taskbar == ("gimp.desktop",)
    service.refresh_context(tree["outside"])

    assert desktop.state.taskbar == ("nemo.desktop", "firefox.desktop")
    assert "## Taskbar\n- nemo.desktop\n- firefox.desktop\n" in (desk_home() / "Desk.md").read_text()
    assert "nemo.desktop" not in _desk(tree["garten"])


def test_writing_the_taskbar_replaces_only_its_list(tmp_path):
    from core.desk_service import write_desk_values

    desk = tmp_path / "Desk.md"
    desk.write_text("# Desk\nThemePreset: Alt\n\n## Taskbar\n- alt.desktop\n\nNotiz\n\n# Andere\nx: 1\n")
    write_desk_values(desk, DesktopState(theme="Neu", taskbar=("a.desktop", "b.desktop:flatpak")))
    assert desk.read_text() == (
        "# Desk\nThemePreset: Neu\n\n## Taskbar\n- a.desktop\n- b.desktop:flatpak\n\nNotiz\n\n# Andere\nx: 1\n"
    )

    desk.write_text("# Desk\nThemePreset: Alt\n\n# Andere\nx: 1\n")
    write_desk_values(desk, DesktopState(taskbar=()))
    assert desk.read_text() == "# Desk\nThemePreset: Alt\n\n## Taskbar\n\n# Andere\nx: 1\n"
