# MyOS Project Status

**Last updated:** 2026-10-20
**Phase:** MVP implementation with focus on stable core flows
**Active branch:** `exp/core-line-no-learning` (well ahead of `main`)

## Summary

MyOS has moved beyond early prototyping. Core components are implemented and iteratively hardened:

- **Scope** — QML file browser: Templates + Projects rows, path bar (H/V view), CWD/CTD navigation, tag filtering, DnD, multi-selection, context menu, Edge-Dock mode
- **PostFix** — Markdown editor with tag sidebar, Obsidian-compatible metadata
- **CLI tools** — myls, myproject, mytag, myedit, myimport, myexport, myfilter
- **Blueprint layer** — Embryo materialization one level at a time (including nested embryos); unused born folders turn back into embryos
- **Filters & Perspectives** — Filter runtime (include/exclude/flatten; a filter chosen by hand puts on its lens); the lens as one session in the perspective daemon, shared by Scope and SunTree, with the FUSE drive "Perspektiven"
- **Desk** — The desktop follows the projects: per-project themes (apps, taskbar) and wallpaper (KDE, Cinnamon, GNOME), changes saved automatically; project icon. Taskbar programs not yet
- **Sort** — `Sort.md` runtime for automatic project sorting
- **Tagging** — Project-scoped tags, color registry, security-tested
- **SunTree** — Experimental half-circle navigator for dropping things into folders: folders only, no files and no search (early stage, see `SunTree/ToDo.md`); shares the lens and the place with Scope (`daemon/lens_link.py`)
- **ClipboardTool** — CopyQ integration that saves text clips as Markdown

Test suite: `python3 -m pytest core/tests/unit cli/tests PostFix/tests Scope/tests/test_list_sort.py Scope/tests/test_format_utils.py Scope/tests/test_scope_i18n.py Scope/tests/test_scope_script_imports.py Scope/tests/test_lens_frame.py Scope/tests/test_lens_desk.py Scope/tests/test_folder_item_hit.py Scope/tests/test_filter_lens.py Scope/tests/test_shared_place.py Scope/tests/test_cwd_mark.py SunTree/tests` — 836 passing, 2 benchmarks deselected (2026-10-25; run them with `-m benchmark`). The other tests in `Scope/tests` (`test_scope_smoke.py`, one in `test_scope_browser_parity.py`) already failed before Oct 2026 and are not part of the suite yet.

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

## Recent Milestones (Oct 2026)

- Embryo birth materializes only the folder itself; visible subfolders stay embryos until first use
- Born template folders that hold nothing of the user turn back into embryos after delete/move (cascading upwards); `myproject tidy` does the same for folders emptied outside MyOS
- Scope: FilesPanel follows the folder preview (700 ms dwell, or on entering the panel); file drags survive list refreshes; drops inside the FilesPanel work
- Scope: FilesPanel list view (toggle in the side panel) with header, selectable columns (Geändert, Größe) and click-to-sort; folder sizes are measured only on demand (resting on the size column or the sidebar total, or a click on its head), in two passes, for the current folder only; the never-read folder-size index in Project.md is gone
- Deleting is undoable: entries go to the trash of their project (`.MyOS/Trash/`, freedesktop layout, `trash_days` in Project.md, default 30), outside projects to the system trash; Scope shows a trash button while it holds something (restore, delete for good, empty); CLI `myproject trash list|restore|delete|empty`
- UI strings are English in the code; German (default UI language) comes from `*_de.ts` translations, kept complete by tests (`scripts/update_translations.py`)
- ACLs: rules in ACLs.md are project-relative and enforced as such; per role the nearest rule wins, `none` locks a role out; subprojects without own ACLs.md inherit the parent's, and the `## Folder` rules apply again to their template folders; new right `delete` (not implied by `write`)
- Scope: ACL filter panel left of the list (only in projects with an ACLs.md, computed in the background): who may access the folder on top, who may access only some entries under "Ausnahmen"; a click shows only the entries that role or person has rights on

## Earlier Milestones (Feb–Mar 2026, committed Oct 2026)

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
