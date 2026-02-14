---
window_width_px: 900
window_height_px: 650
window_x_permille: 78
window_y_permille: 44
note_style: cloud
---
# MyOS Design Document

## Purpose
This document is the practical entry point for contributors. It explains:
- what MyOS is trying to achieve,
- how the current codebase is structured,
- which design principles should guide new changes.

The goal is fast orientation and consistent decisions.

## Product Direction
MyOS is a project-centric environment. It treats project context as a first-class concept rather than an afterthought on top of generic folders.

Key ideas:
- Human workflows are project-shaped, not file-shaped.
- Structure should evolve with usage, not be fully fixed upfront.
- Existing Unix tooling should continue to work.
- System behavior should be understandable and recoverable.

## Core Design Principles

### 1) Progressive Disclosure
Start simple. Reveal complexity only when needed.

Implications:
- New users get low cognitive load.
- Power users can still access advanced behavior.
- UI and filesystem views should avoid unnecessary noise.

### 2) Explicit Over Magical
Automation is welcome, but behavior must be predictable.

Implications:
- Deterministic transforms.
- Clear naming for generated/derived structures.
- Avoid hidden side effects across unrelated components.

### 3) Local-First and File-First
Project state lives in files that can be read, versioned, and audited.

Implications:
- Prefer Markdown/YAML/JSON over opaque storage.
- Keep metadata colocated with projects when practical.
- Preserve interoperability with external tools.

### 4) Backward-Compatible Evolution
Refactors should preserve behavior unless a change is intentional and documented.

Implications:
- Small, testable steps.
- Migration paths when formats or APIs change.
- Avoid "big bang" rewrites.

### 5) Modular Boundaries
Organize code by responsibilities, not by convenience.

Implications:
- UI composition, theme logic, tag context logic, and editor behavior should be separable.
- Shared logic should move to modules once patterns stabilize.
- Main entrypoints should orchestrate, not contain most logic.

## Current Architecture Overview

MyOS currently has two major domains:
- the broader project/filesystem domain (`core`, `Scope`, CLI tools),
- the PostFix editor domain (`PostFix`).

This section focuses on PostFix, because it is currently under active refactoring.

## PostFix Architecture (Current)

### Module Map
- `PostFix/main.py`
  - `PostFixWindow` orchestration
  - app/window lifecycle
  - final wiring of modules and signals
- `PostFix/smart_editor.py`
  - inline focus editing model
  - markdown rendering flow
  - cursor/line mapping behavior
  - tag and color-definition extraction from document text
- `PostFix/ui_panels.py`
  - top-level reusable UI widgets:
    - `TagSidebar`
    - `ACLSidebar` (currently hidden dummy)
    - `BottomToolbar`
- `PostFix/window_layout.py`
  - layout construction helpers for the main window
- `PostFix/window_theme.py`
  - color/theme transitions and visual state updates
- `PostFix/window_tags.py`
  - tag context orchestration:
    - sync with scope tags
    - color registry updates
    - sidebar refresh behavior
- `PostFix/tag_registry.py`
  - read/write logic for tag configuration data (Obsidian-compatible)
- `PostFix/metadata.py`
  - frontmatter read/write helper logic
- `PostFix/obsidian_embed.py`
  - optional embed integration behavior
- `PostFix/resize_overlay.py`
  - frameless resize interaction support
- `PostFix/cli.py`
  - CLI entrypoint and argument wiring

### Runtime Responsibility Flow
1. `PostFixWindow` boots and wires editor + sidebars.
2. `SmartEditor` owns document interaction and preview rendering.
3. `WindowTagsMixin` observes editor tag events and updates:
   - local UI chips,
   - project scope tags,
   - tag color registry.
4. Theme/layout mixins apply visual composition and transitions.

### Fast-Start Strategy
PostFix uses deferred non-critical startup:
- show readable markdown as early as possible,
- initialize non-critical visuals and context shortly after first paint.

This keeps perceived startup responsive.

## Data and Configuration Model

### Document-Level
- Markdown body and optional frontmatter (handled by `metadata.py` / `SmartEditor`).
- Inline color definitions in text are parsed as color entries for UI.

### Project-Level
- `.MyOS/Tags.md` is used as project scope tag filter/list.
- New document tags can be synced into scope tags.
- Scope tag changes can trigger propagation hooks through `core.project` signaling.

### Vault-Level (Obsidian Compatibility)
- Tag color registry is persisted in Obsidian-compatible app config data.
- Tag color edits from PostFix update registry structures directly.

## Contributor Guidance

### Where to Put New Logic
- New editor behavior: `smart_editor.py`
- Tag context / sync / registry behavior: `window_tags.py` or `tag_registry.py`
- Pure UI widget behavior: `ui_panels.py`
- Window composition or theming: corresponding mixin modules
- Cross-cutting orchestration only: `main.py`

### What Not to Do
- Do not re-centralize large feature logic in `main.py`.
- Do not mix parsing/business logic into pure UI widget classes.
- Do not break existing save/sync flows without explicit migration notes.

### Safe Change Pattern
1. Make one focused change.
2. Run syntax checks and a minimal smoke test.
3. Commit in small increments.
4. Only then proceed to next refactor step.

This is especially important because large PySide refactors can create transient crash-prone states.

## Scope Drag-and-Drop Status

Current Scope behavior is intentionally conservative and safety-oriented.

### Implemented
- Multi-selection in `FilesPanel`:
  - `Ctrl+Click` toggles item selection.
  - Rectangle selection (marquee) on free panel area.
- Batch drag payloads from current selection.
- Drop targets in Scope folder views and file panel folders.
- Batch move backend with structured result reporting:
  - `moved`
  - `skipped`
  - `errors`
- Safety prompt only when at least one moved item is a folder.
- Human-readable post-move report messages (English).

### Interaction Policy
- File-only moves execute directly (no confirmation dialog).
- Folder-involved moves require confirmation.
- Moving into invalid targets is blocked and reported.

### Follow-up Refinement Targets
- Optional OR/AND toggle visibility polish in the tag rail if needed.
- Additional UI affordances for move progress and undo strategy.
- Broader integration tests for mixed source payloads (folders + files).

## Minimal Smoke Test Checklist
- Open a Markdown file from Scope/PostFix.
- Verify top-panel interactions (including window move on top free area).
- Verify focus editing and line navigation.
- Verify tag sidebar updates from document tags.
- Verify color definition chip behavior.
- Verify save, close, reopen persistence.
- Verify startup still feels fast.

## Design Quality Bar
A change is "good enough" when:
- behavior is at least as stable as before,
- module boundaries are clearer after the change,
- startup and interaction latency do not regress noticeably,
- a new contributor can find the right place to modify behavior in under a few minutes.

---

This document should evolve with the architecture. Keep it concise, practical, and implementation-aligned.