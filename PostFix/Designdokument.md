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

## One PostFix For All Notes

`PostFix/single_instance.py`, decided 2026-11-03 (the new editor in QtWebEngine costs about
300 MB per program; one program shares it):

- A later start (Scope, a double click, an exercise link) hands its note to the PostFix already
  running and ends - in plain Python before loading Qt, in about half a second. The running
  one opens the note in a window of its own, or brings its window to the front.
- One PostFix per user, display and settings folder (`XDG_CONFIG_HOME`): tests and test
  harnesses with settings of their own never reach the user's. `MYOS_POSTFIX_SINGLE=0` turns it off.
- Security: the connection lies in the user's private runtime folder (`$XDG_RUNTIME_DIR`,
  owner-only socket); only existing `.md` files are taken.
- A closed note's window is really gone (`WA_DeleteOnClose`); the program ends with the last.
- On SIGTERM ("Bin fertig" on the test machine) every note is closed as by the user: pending
  edits saved, the connection removed.
- Exercise links: one handler for all windows, which hands each click to the window it came from.

## One Editor For All Notes (in the works)

`PostFix/editor_host.py`, behind `MYOS_POSTFIX_EDITOR=codemirror` (off by default). Measured: every
further CodeMirror page costs 40-80 MB and leaks some when dropped; moving one page between
windows takes 40-120 ms. So one page serves all notes of a PostFix:

- A note that is only read never loads the editor: it shows its light rendering (below). A
  click or a key in the text loads it (about 0.5 s, once) - the cursor at the letter clicked,
  what was typed meanwhile typed in; a link clicked is followed without it. Once loaded, the
  editor follows the window activated (moved after the activation event: moved during it,
  QtWebEngine crashes in X).
- Every note keeps its own text, cursor, selection and undo history in the page (one
  CodeMirror state per note); changes from outside go into that state without being reported back
  as typing.
- PostFix keeps the front matter; the editor only sees the body. Typed text goes through the
  usual save (merge with changes from outside, conflict copy).
- Links in the editor: notes open in the same window, other files with their program, myos links
  as exercise links.
- The editor leaves a note before it is deleted (window closed or deleted), so it lives on for
  the others; the page itself is deleted before Qt ends (otherwise QtWebEngine crashes on exit).

### The light rendering (`light_render.py`, `light_view.py`)

What the editor shows with the cursor elsewhere, drawn by Qt (a QTextBrowser): line for line
like CodeMirror (an empty line is an empty line), Markdown marks hidden, the editor's fonts,
sizes, colours and widths. Measured against the real editor side by side in Xephyr (screen
photos, line by line): text lines within 0-1 px, same line breaks. What it took:

- One font for both sides, resolved by PostFix (`system-ui` may resolve differently).
- Qt sets text at the top of a line, the browser centres it: each line moved by the difference;
  Qt knows no negative margins, so the line before gets shorter instead.
- The browser lays out in 64ths of a pixel (26.4 -> 26.390625 px per line).
- CodeMirror wraps with `white-space: break-spaces`: a zero-width break after every space makes
  Qt count a space at a line's end too.
- Code backgrounds, quote bars and rules painted over the full line; check boxes drawn as the
  browser's; tables, empty cells, pictures (as high as the line) measured one by one.
- The editor page gets PostFix's scroll bar, so both have the same width to lay out in.

Switching keeps the place: the rendering hands its first line in view (and its offset) to the
editor, the editor reports its own back while scrolling; the rendering takes it over when the
editor leaves.

## Changes From Outside

A note open in PostFix may change on disk meanwhile (another program, a sync, Scope, a test
machine's reset). `PostFix/live_file.py`, decided 2026-11-03 after PostFix wrote its older copy
of lesson 7 back on closing:

- PostFix watches the note (and its folder: many programs replace a file instead of writing it).
- Without unsaved edits a change from outside shows at once, like in Google Docs.
- With unsaved edits both are merged line by line against the version both started from
  (three-way merge): a moved window (its place lives in the note's front matter) and a paragraph
  added elsewhere both survive.
- A real conflict (the same lines changed differently): the file keeps the version from outside,
  PostFix's own goes beside it as "<name> (Konflikt).md", and a short notice says so.
- Every save reconciles first; a note deleted elsewhere is not written back.

## Exercise Links (Learning MyOS)

A lesson says `[▶ Übung öffnen](<myos:open?scope=Urlaub 2025&files=Urlaub 2025>)`: a click
opens Scope in the exercise folder (`scope=`) and, if the exercise needs it, the desktop's
classic file browser (`files=`, via `xdg-open`) - with wmctrl (X11) Scope on the left half of
the screen, the file browser on the right. `PostFix/exercise_links.py`, decided 2026-10-26:

- PostFix registers the handler for `myos` itself (`QDesktopServices.setUrlHandler`); nothing
  on the system changes, so these links work in PostFix only (Obsidian shows dead links).
- Folders are relative to the note shown (lesson links move the preview on to other notes).
- Security: only folders inside the note's own folder; absolute paths and `..` are refused.
- Every click opens a new Scope window (Scope has no single-instance mode yet).

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
