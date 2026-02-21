# MyOS Project Status

**Last updated:** 2026-02-17  
**Phase:** MVP implementation with focus on stable core flows

## Summary

MyOS has moved beyond early prototyping. Core components are implemented and iteratively hardened:

- **Scope** — QML file browser with tag filtering, DnD, multi-selection
- **PostFix** — Markdown editor with tag sidebar, Obsidian-compatible metadata
- **CLI tools** — myls, myproject, mytag, myedit, myimport, myexport, myfilter
- **Blueprint layer** — Embryo materialization, template-based project structure
- **Tagging** — Project-scoped tags, color registry, security-tested
- **Markdown thumbnailing** — Linux integration

## Current Priorities

1. ACLs (access control)
2. Perspectives
3. Rooms concept (project-dependent desktops)
4. Learning MyOS expansion
5. Demo data as playground
6. Scope/PostFix UI polish
7. Distribution packaging
8. i18n preparation

## Recent Milestones

- PostFix modularized (main.py slimmed, responsibilities separated)
- PostFix fast-start and interaction improvements
- Tag handling hardened (including security tests)
- Linux Markdown thumbnailer built and integrated
- Scope tagbar with filter logic (project/visible, OR-default)
- Multi-selection and Drag&Drop in Scope
- Safety dialog for folder moves
- Batch-move API with structured feedback (moved/skipped/errors)

## Operational Details

For the full operational roadmap, open questions, and learnings, see [ProjectLogbook.md](../ProjectLogbook.md) in the repository root.
