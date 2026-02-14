# PostFix Design Document

## Purpose
This document helps new contributors quickly understand PostFix:
- architecture and module boundaries,
- runtime flow,
- design principles for safe changes.

PostFix is a focused Markdown editor inside MyOS, optimized for fast reading/editing and project-aware tag workflows.

## Product Goals
- Fast time-to-first-readable-content.
- Inline "focus editing" with minimal UI friction.
- Strong Markdown compatibility.
- Obsidian-friendly tag color interoperability.
- Predictable behavior with incremental, low-risk evolution.

## Design Principles

### 1) Fast First Paint
Render readable content first, then initialize non-critical UI/context.

### 2) Editor-Centric Interaction
Core editing logic belongs to the editor module, not to window orchestration.

### 3) Explicit Tag Pipeline
Tag extraction, scope sync, and color-registry writes are separate steps with clear ownership.

### 4) Safe Refactoring
Small modular steps, compile checks, and smoke tests after each step.

### 5) Interoperability Over Lock-in
Use portable, file-based formats and compatible registry structures.

## Current Module Architecture

### `main.py`
- Contains `PostFixWindow` and app orchestration.
- Wires editor, sidebars, toolbars, and mixins.
- Handles lifecycle events (save, print, open/send actions).

### `smart_editor.py`
- Owns document editing and preview rendering.
- Implements focus-line editing behavior.
- Parses document tags and color definitions.
- Applies runtime tag color rendering in preview.

### `ui_panels.py`
- Reusable UI components:
  - `TagSidebar`
  - `ACLSidebar` (currently hidden dummy)
  - `BottomToolbar`

### `window_layout.py`
- Window layout and composition helper logic.

### `window_theme.py`
- Theme/color transitions and visual synchronization.

### `window_tags.py`
- Tag-context orchestration:
  - reacts to editor tag/color events,
  - syncs project scope tags (`.MyOS/Tags.md`),
  - updates sidebar tag UI,
  - writes registry-backed tag colors.

### `tag_registry.py`
- Pure data-layer helpers for:
  - scope tag file parsing/writing,
  - vault root discovery,
  - tag color registry load/save/flatten/update.

### `metadata.py`
- Frontmatter parsing/building helpers.

### `obsidian_embed.py`
- Optional embed integration behavior.

### `resize_overlay.py`
- Frameless window edge resize behavior.

### `cli.py`
- CLI argument parsing and app bootstrap.

## Runtime Flow (High Level)
1. `PostFixWindow` initializes UI and editor.
2. Markdown is loaded and rendered early.
3. Deferred startup initializes non-critical context.
4. `SmartEditor` emits tag/color-definition signals.
5. `WindowTagsMixin` updates scope/config/sidebar state.
6. Save pipeline writes document and synced tag scope.

## Data and Config Model

### Document Level
- Markdown content (+ optional frontmatter).
- Inline color definitions parsed as UI "color chips".

### Project Level
- `.MyOS/Tags.md` as scope tag list/filter.
- Missing document tags can be added into scope automatically.

### Vault Level
- Obsidian-compatible tag color registry structures.
- Tag color changes write back to registry data.

## Note Style and Thumbnail Rules

PostFix stores note style intent in frontmatter and the thumbnail pipeline consumes the same semantics.

### Manual style selection (preferred)
- Canonical key: `note_style`.
- Legacy fallback key: `myos_note_style` (read for compatibility, written back to canonical key).
- Explicit style always wins over autodetection.

### Conservative autodetection policy
Autodetection is intentionally narrow and predictable:

1. If file path is inside `/.MyOS/`, style is `config`.
2. Else if content looks like a long structured dialog, style is `chat`.
3. Else line-count thresholds apply:
   - fewer than 10 content lines -> `postit`
   - fewer than 100 content lines -> `sheet` (A4-like)
   - 100 or more content lines -> `notebook`

No other styles are auto-selected by default.

### Why these rules
- They are deterministic and easy to reason about.
- They map visual density to document size.
- They keep "smart" behavior limited, so users can still trust what happens.

## Contributor Rules of Thumb

### Put new code where responsibility already exists
- Editor behavior -> `smart_editor.py`
- Tag sync/registry behavior -> `window_tags.py` / `tag_registry.py`
- Pure widget behavior -> `ui_panels.py`
- Window visuals/layout -> `window_theme.py` / `window_layout.py`
- Cross-module wiring only -> `main.py`

### Avoid
- Re-centralizing logic into `main.py`.
- Mixing data parsing into visual widgets.
- Large multi-concern refactors in a single commit.

## Minimal Smoke Test Checklist
- Open markdown file.
- Verify top-panel drag-to-move and window controls.
- Verify focus editing and cursor movement behavior.
- Verify tag sidebar reflects document tags.
- Verify color chip click/double-click behavior.
- Verify style selector persists via frontmatter `note_style`.
- Verify thumbnail style thresholds:
  - 9 lines -> post-it
  - 10 lines -> A4 sheet
  - 100 lines -> notebook
- Verify files inside `/.MyOS/` render as config style.
- Verify save, close, reopen persistence.
- Verify startup remains fast.

## Definition of Done for Changes
A change is acceptable when:
- no functional regressions in core flows,
- module boundaries are clearer or unchanged,
- startup/editing responsiveness is not degraded,
- the change location is obvious to the next contributor.
