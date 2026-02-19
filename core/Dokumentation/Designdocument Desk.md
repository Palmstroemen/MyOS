# MyOS Desk Profiles - Design Document (Draft)

## 1. Purpose

`Desk.md` defines a project-aware desktop profile for MyOS.
It controls environment-facing preferences (for example wallpaper and theme) while MyOS remains the source of truth.

The MVP targets deterministic behavior:
- resolve the active desk profile from the current path,
- apply it only when the effective source changes,
- delegate actual desktop changes to backend adapters (KDE first).

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
2. Walk upward to filesystem root.
3. Pick first matching candidate path.
4. If none is found, use global fallback profile (if configured).

This rule removes direction-specific logic (no separate "going up/down" behavior).
Resolver implementation should remain generic (for example `find_config_in_parents(path, "Desk.md")`)
instead of introducing file-specific API methods.

## 4. Inheritance Semantics

- Child projects inherit desk settings automatically when they have no local `Desk.md`.
- No copy of `Desk.md` is required in each subproject.
- Moving from a nested folder with local `Desk.md` to parent context activates the next ancestor profile.
- Template-root desk files participate naturally if they are in the active upward path.

## 5. MVP Config Schema

Expected top-level section:

```md
# Desk
ThemePreset: BreezeDark
WallpaperPreset: finance_clean_01
WallpaperPath: /absolute/or/project/relative/path.png
DockPreset: finance_tools
RecentPolicy: project-first
Inherit: dynamic
```

Notes:
- `ThemePreset`: symbolic name resolved by backend adapter or local catalog.
- `WallpaperPreset`: symbolic wallpaper selector.
- `WallpaperPath`: optional direct override.
- `DockPreset`: optional dock favorites preset key.
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

KDE backend is first implementation target.
Other desktop environments can be added later without changing `Desk.md` schema.

## 9. Safety and Failure Behavior

- Missing `Desk.md`: no crash, continue with fallback/none.
- Parse errors: skip invalid profile and continue upward/fallback.
- `inherit:not` in a local `Desk.md` blocks upward resolution for that branch.
- Backend command failure: report structured error, keep app alive.
- Partial apply failure: keep last successful profile marker unchanged.

## 10. Operational Controls (MVP)

Environment toggles:
- `MYOS_DESK_ENABLE=1` to enable runtime apply
- `MYOS_DESK_DRY_RUN=1` to log planned actions without executing
- `MYOS_DESK_BACKEND=kde|none` to select backend

Default in development:
- apply disabled unless explicitly enabled.

## 11. Acceptance Criteria (MVP)

- Nearest valid `/.MyOS/Desk.md` is resolved deterministically.
- Entering subprojects without local desk does not trigger re-apply.
- Leaving a local desk area activates the next ancestor profile.
- Broken configs do not crash navigation.
- KDE integration is capability-gated and observable through logs.
