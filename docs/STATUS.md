# MyOS Project Status

**Last updated:** 2026-10-18
**Phase:** MVP implementation with focus on stable core flows
**Active branch:** `exp/core-line-no-learning` (well ahead of `main`)

## Summary

MyOS has moved beyond early prototyping. Core components are implemented and iteratively hardened:

- **Scope** — QML file browser: Templates + Projects rows, path bar (H/V view), CWD/CTD navigation, tag filtering, DnD, multi-selection, context menu, Edge-Dock mode
- **PostFix** — Markdown editor with tag sidebar, Obsidian-compatible metadata
- **CLI tools** — myls, myproject, mytag, myedit, myimport, myexport, myfilter
- **Blueprint layer** — Embryo materialization (including nested embryos), template-based project structure
- **Filters & Perspectives** — Filter runtime (include/exclude/flatten); flipped-perspective MVP with resolver, FUSE and a perspective daemon
- **Desk** — Per-project desk profile (theme, wallpaper, dock, project icon)
- **Sort** — `Sort.md` runtime for automatic project sorting
- **Tagging** — Project-scoped tags, color registry, security-tested
- **SunTree** — Experimental half-circle navigator (early stage, see `SunTree/ToDo.md`)
- **ClipboardTool** — CopyQ integration that saves text clips as Markdown

Test suite: `python3 -m pytest core/tests/unit cli/tests PostFix/tests` — 372 passing (2026-10-18).

## Current Priorities

1. ACLs (access control)
2. Perspectives (MVP running; persistence/sharing model open)
3. Rooms concept (project-dependent desktops)
4. RecentFiles
5. Learning MyOS expansion
6. Demo data as playground
7. Scope/PostFix UI polish
8. Distribution packaging
9. i18n preparation

## Recent Milestones (Feb–Mar 2026, committed Oct 2026)

- Perspective daemon (resolver, FUSE, Scope client) with idle self-shutdown
- Scope: path bar in H/V view, Edge-Dock mode, delete via context menu, unified `navigationRequested` signal
- Scope dialogs extracted into `Scope/Dialogs/`, path helpers into `Scope/js/`
- Hidden folders optionally shown; `.MyOS` hidden in embryo/template views
- Nested embryos materialize root-to-leaf on move/mkdir
- Project root detection requires `.MyOS/Project.md`
- `Project.md` metadata writes are atomic and locked (fixes corrupted frontmatter)

## Known Open Points

- Legacy and duplicate-logic candidates in Scope: `Scope/.Legacy-Code-Kandidaten.md`, `Scope/.FolderBrowser-DoppelKandidaten.md`
- `main.qml` (~3500 lines) and `FolderBrowser.qml` (~4800 lines) are large; further splitting pending
- `.TagsHere.json` tag caches appear in many folders; decide whether to track or ignore them
- `core/context.md` and `Technical Intro.md` still describe the old `myos_core.py` prototype

## Operational Details

For the full operational roadmap, open questions, and learnings, see [ProjectLogbook.md](../ProjectLogbook.md) in the repository root.
