# MyOS Desk Profiles - Design Document (Draft)

## 1. Purpose

`Desk.md` defines a project-aware desktop profile for MyOS.
It controls environment-facing preferences (for example wallpaper and theme) while MyOS remains the source of truth.

The MVP targets deterministic behavior:
- resolve the active desk profile from the current path,
- apply it only when the effective source changes,
- delegate actual desktop changes to backend adapters (KDE, GNOME, Cinnamon).

How the desktop follows the projects, and how user changes are kept, is section 12.

## 2. Core Principles

- Path-based inheritance with "nearest ancestor wins"
- Explicit, file-first configuration in `/.MyOS/Desk.md`
- Safe defaults and graceful fallback when profiles are missing or invalid
- Backend-agnostic core, backend-specific adapters
- Idempotent application (no repeated apply for same effective profile)

## 3. File Location and Resolution

### Canonical location

Primary candidate:
- `/.MyOS/Desk.md`

Optional compatibility candidate:
- `/Desk.md` at folder root (disabled by default, feature-flagged)

### Resolver algorithm

For each context change:
1. Start at target directory (`cwd` or active file parent).
2. Walk upward, **at most to the top project** of the projects tree (e.g. `/Projekte`);
   folders outside the projects tree have no desk search at all.
3. Pick first matching candidate path. A `Desk.md` without values that says
   `Inherit: not` stops the search.
4. If none is found, use the system default (the user's own desktop, section 12).
5. Each setting the found `Desk.md` leaves open comes from the next `Desk.md` above that
   has it, at last from the system default (see 4).

This rule removes direction-specific logic (no separate "going up/down" behavior).
Resolver implementation should remain generic (for example `find_config_in_parents(path, "Desk.md")`)
instead of introducing file-specific API methods.

## 4. Inheritance Semantics

- Child projects inherit desk settings automatically when they have no local `Desk.md`.
- No copy of `Desk.md` is required in each subproject.
- Moving from a nested folder with local `Desk.md` to parent context activates the next ancestor profile.
- Template-root desk files participate naturally if they are in the active upward path.
- **Each setting is inherited on its own** (decided 2026-10-21): a `Desk.md` with only a
  wallpaper still gets theme and panel theme from the desks above, at last from the system
  default. Otherwise the value of the project visited before would simply stay (a blue
  taskbar from Garten would stay blue in Haus).
- `WallpaperPreset` and `WallpaperPath` count as one setting. An inherited relative
  `WallpaperPreset` stays relative to its own `Desk.md` (and inside its folder).
- `ProjectIcon` is not inherited: it belongs to its project.
- `Inherit: not` takes nothing from the desks above, only from the system default.

## 5. MVP Config Schema

Expected top-level section:

```md
# Desk
ThemePreset: BreezeDark
PanelTheme: Mint-Y-Dark-Teal
WallpaperPreset: finance_clean_01
WallpaperPath: /absolute/or/project/relative/path.png
DockPreset: finance_tools
RecentPolicy: project-first
ProjectIcon: plant
Inherit: dynamic
```

Notes:
- `ThemePreset`: theme of the applications (GTK theme; KDE look-and-feel package).
- `PanelTheme`: theme of taskbar, menus and notifications (Cinnamon "Desktop" theme,
  `org.cinnamon.theme name`); visible even with many windows open. Plain GNOME has
  none (skipped), KDE not yet.
- Values may contain spaces (`PanelTheme: Linux Mint`, paths); blank lines, notes and
  `<!-- comments -->` do not end the section (unlike the general config parser, which
  dropped every setting after such a line).
- `WallpaperPreset`: a picture relative to the `Desk.md` (must stay inside its folder) or
  an absolute path; symbolic names are not implemented.
- `WallpaperPath`: optional direct override (plain path; MyOS writes this one).
- `DockPreset`: optional dock favorites preset key (not implemented yet).
- `ProjectIcon`: icon of the project in Scope (theme icon name, path or URL).
- `RecentPolicy`: optional UI-level recents display hint.
- `Inherit`: recognized values `dynamic | fix | not` (default `dynamic`).

## 6. Precedence Rules

When multiple sources can provide a desk profile:

1. Manual profile override (explicit path argument)  
2. Active perspective-linked desk profile  
3. Nearest ancestor `/.MyOS/Desk.md`  
4. Global fallback desk profile  

If both root `Desk.md` and `/.MyOS/Desk.md` are enabled for one directory, `/.MyOS/Desk.md` wins.

## 7. Runtime Apply Rules

- Resolve on every context update.
- Compute `source_path + content_hash` as active profile identity.
- Skip apply when identity is unchanged.
- Apply in stable order:
  1) theme,
  2) wallpaper,
  3) dock,
  4) optional recents policy handoff.

## 8. Backend Model

Core modules do not call KDE directly.
They call a backend interface, for example:
- `apply_theme(config)`
- `apply_wallpaper(config)`
- `apply_dock(config)`

Backends (`core/desktop_backends/`), chosen from `XDG_CURRENT_DESKTOP`:
- **KDE**: `lookandfeeltool -a <theme>`, `plasma-apply-wallpaperimage <path>`; reads the
  KDE config files.
- **Cinnamon / GNOME** (`gnome.py`): `gsettings` on `org.cinnamon.desktop.*` resp.
  `org.gnome.desktop.*` — wallpaper `picture-uri` (GNOME also `picture-uri-dark`),
  theme = application theme `gtk-theme`, panel theme = `org.cinnamon.theme name`
  (Cinnamon only).
- Every backend can also `capture()` the desktop as it is (theme, wallpaper).
Other desktop environments can be added later without changing `Desk.md` schema.
Security: commands are argv lists (no shell); theme names are checked (no leading `-`,
no quotes or control characters).

## 9. Safety and Failure Behavior

- Missing `Desk.md`: no crash, continue with fallback/none.
- Parse errors: skip invalid profile and continue upward/fallback.
- `Inherit: not` in a local `Desk.md` stops the upward search (system default applies,
  also for the settings it leaves open).
- Backend command failure: report structured error, keep app alive.
- Partial apply failure: keep last successful profile marker unchanged.

## 10. Operational Controls (MVP)

Always on, no switch in the UI (decided 2026-10-21). Environment variables only serve
development and tests:
- `MYOS_DESK_BACKEND=auto|kde|cinnamon|gnome|none` (default `auto`); the tests run with
  `none` (root `conftest.py`), so a test run never changes the real desktop.
- `MYOS_DESK_ENABLE=0` / `MYOS_DESK_DRY_RUN=1` to switch applying off / only log it.

## 11. Acceptance Criteria (MVP)

- Nearest valid `/.MyOS/Desk.md` is resolved deterministically.
- Entering subprojects without local desk does not trigger re-apply.
- Leaving a local desk area activates the next ancestor profile.
- Broken configs do not crash navigation.
- KDE integration is capability-gated and observable through logs.

## 12. The Desktop Follows the Projects (decided 2026-10-21)

- **Inside the projects tree** (`/Projekte` and below) the nearest `Desk.md` applies (see
  3); `/Projekte/.MyOS/Desk.md` is the fallback for all projects.
- **Outside** (Documents, Music, …) the user's own desktop applies: the **system
  default**, `~/.config/MyOS/Desk.md`. Desktops do not keep a second copy of their
  settings once MyOS changed them, so MyOS saves the user's desktop there once, before it
  changes anything.
- **Changes by the user are kept, without asking**: when the desktop differs from what
  MyOS set last, MyOS writes themes and wallpaper into the `.MyOS/Desk.md` of the project
  where the user was (creating it), keeping every other line (`ProjectIcon`, …).
  Outside projects the change goes into the system default. There is no "where to save"
  question: where it lands is not the user's concern.
- **Scope and PostFix** both follow (PostFix with the folder of the open note). They
  share what MyOS set last in `~/.config/MyOS/desk-state.json`, so neither takes the
  other's switch for a change by the user.
- Open: projects shared by several people (sync, team) would get the personal desktop
  of whoever changed it; belongs to the sharing model. Taskbar programs (`DockPreset`)
  are a next step.
- Observed (2026-10-21): switching the panel theme makes Cinnamon reload its theme, and
  the order of the windows in the taskbar changed. MyOS only switches when the profile
  differs; keep an eye on it.
- Ideas from the user: finance golden, law dark green, music purple, cars a dark theme.

