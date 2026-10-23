# MyOS Perspective - The Lens (Behaviour) and the Resolver Contract

Part A describes how the perspective behaves for the user (decided 2026-10-22). Part B is
the resolver contract it is built on (v1/v1.1, February/March 2026). Section A8 lists what
changes against what was built before.

# Part A - The Lens

## A1. The Picture

A perspective is a **lens**: one looks at the projects from a department's point of view.
Normally one looks from a project: `/Projekte/Job/04_Finanz/Rechnungen`. Wearing the lens
of the finance department, the path is turned round: `/04_Finanz/Projekte/Job/Rechnungen`.
Below `/04_Finanz` one sees only finances, but those of all projects ("the shelf",
`/04_Finanz/Projekte`). See "Vision/Brillen und die runde Halle.md".

Example. Two passions: making music and travelling, so two projects, `/Musikstudio` and
`/Reisen`.

1. I am in the music studio: top left in my slim Scope, `/Musikstudio` is the CWD; dark
   theme, Ableton and MuseScore in the taskbar (Desk).
2. An invoice for the studio comes in. Mouse up: I see the studio's MyOS folders and drop
   it onto `/04_Finanz` (embryo or born; an embryo is born by that). No lens needed.
3. An invoice for the travels comes in. I do not want to go to `/Reisen`. I hover through
   `/04_Finanz` → `/Ausgangsrechnungen` → `/2026` and double-click `2026`: I now wear the
   `/04_Finanz/Ausgangsrechnungen/2026` lens. The desktop turns into the finance one
   (light theme, spreadsheet and accounting in the taskbar).
4. Below the lens folder a project menu lets me go to `/Reisen`: I am at once in
   `Reisen/04_Finanz/Ausgangsrechnungen/2026` and drop the invoice there. (If `2026` does
   not exist there yet, the folder is born or sorting by date files it into its year.)
5. Back to the studio: `/Musikstudio` still stands top left. A double click on it (or
   "End perspective") takes the lens off - I am in the studio again, with its desktop.

## A2. Terms

- **CWD** - where I am: the project shown top left. Its Desk applies without a lens.
- **CTD** - where I look and drop (see "Vision/GUI Filebrowser.md"). With a lens on, the
  lens is the CTD: it can point into another project than the CWD.
- **Lens (CPD)** - the turned path, e.g. `/04_Finanz/Ausgangsrechnungen/2026/Projekte/Reisen`
  in the resolver's form: the department path (template side), the project, and a tail.
  A lens may sit at any depth of the department (`/04_Finanz`, `/04_Finanz/Ausgangsrechnungen/2026`).
- **Department** - a template folder (`00_Admin` ... `08_Dokumentation`).

## A3. Gestures

1. **Put on a lens:** double click on a department folder - or any folder below it, at
   any depth - in the CWD's MyOS folders (hover menu / template row). The lens starts at
   the CWD's project (`/04_Finanz/Projekte/Musikstudio`), not at the shelf. The CWD stays.
2. **Two menus, one meaning each:**
   - **Left menu (CWD):** always changes the project one is in - with or without a lens.
     With a lens on, the lens follows the new CWD (it looks from where one is); a project
     chosen before in the right menu is forgotten. Taking the lens off then leaves one in
     the new CWD.
   - **Right menu (below the lens folder, the CTD):** moves only the lens to another
     project. The CWD stays; taking the lens off brings one back to it.
3. **Keep the depth:** moving the lens to another project keeps the whole department path
   and tail (`.../Ausgangsrechnungen/2026`).
4. **The shelf:** going up to `/04_Finanz/Projekte` shows all projects as the
   department's folders - real projects only (no `Clipboard`, no plain folders).
5. **Change the lens:** a double click on another department folder while wearing one.
6. **Take the lens off:** a double click on the CWD, or "End perspective". The lens is
   really off (no special "OFF" path); one is in the CWD again, with its Desk.
7. **Without a lens:** a single click on a department folder opens that folder *of the
   CWD's project* (born or embryo) - not the real `Templates` folder.

## A4. What the Lens Shows

- The FilesPanel shows the lens' content, not the real folder of the CWD. Opening,
  dragging, deleting, renaming act on the real files.
- **Department folder not born in a project:** the nearest existing parent of the same
  project is shown (v1.1 fallback, B15), with its folders - e.g. a few invoices lying at
  the project's top. Scope's switch to hide folders lets the user see only the files; we
  try out which is better and make one variant the default later.
- Dropping into the lens creates the canonical target (department folder born on the way,
  B6/B15); sorting by date (core/filing.py) and the x-ray view apply as everywhere.
- ACLs apply to the real paths, identically in Scope, CLI and FUSE.

## A5. Desk With a Lens

While a lens is on, the department's Desk applies (the nearest `Desk.md` up the
department path: `2026` → `Ausgangsrechnungen` → `04_Finanz`, prepared in the template, e.g.
`Templates/Standard/04_Finanz/.MyOS/Desk.md`), wherever the lens or the CWD is moved.
Taking the lens off brings back the CWD project's Desk. Dropping something into a
department folder without a lens does not change the Desk.

## A6. One Session: Daemon and FUSE

- The lens' state (off, or on with its CPD and the CWD it looks from) lives in **one place:
  the perspective daemon**. Scope, SunTree and the CLI only ask it; they build no CPDs
  themselves. The daemon uses the same core as `ScopeApi` (no logic of its own).
- Scope starts *its* daemon for its projects root when none runs, and does not attach to a
  daemon serving another root.
- The **FUSE drive** is why the daemon exists: third-party programs (LibreOffice "Save
  as") write into `/04_Finanz/Projekte/Job` and the file lands in `Projekte/Job/04_Finanz`.
  The drive always shows the **whole turned tree** of the projects root -
  `/<department>/Projekte/<project>/...` - independent of the lens Scope shows.
- **Where:** a visible folder `Perspektiven` next to `Projekte` (decided 2026-10-22):
  `.../Perspektiven/04_Finanz/Projekte/Job`. Its top level shows the departments
  (`00_Admin` ... `08_Dokumentation`), each with `Projekte` below. It is not mounted over
  `Projekte`: programs (file managers, backups, git, Scope) keep seeing the real projects,
  and the daemon reads them without reading itself.
- A filter may put on a lens (`## Perspective`, see "Designdocument Perspectives.md"):
  activating it puts the lens on through the session, like the gesture.

## A7. Built In Core

The gesture rules live in the core as a perspective session (actions such as put on,
move to project, go, take off; the lens' listing), tested there; the daemon serves it, the
GUIs show it. No CPD building in QML (Scope, SunTree).

Built (2026-10-22):
- `core/perspective_session.py` - the session (E1). Its state is kept as parts (project
  path below the projects root, lens path), not as a parsed CPD: projects may be nested
  (`Wohnen/Garten`).
- `core/perspective_drive.py` - the drive's turned tree (E2), independent of the session:
  `/` the departments, `/04_Finanz[/...]` template subfolders and `Projekte`, the shelf
  (real projects and the folders leading to them), then the project. Saving into a project
  without the department folder bears it (`Blueprint.materialize_dir`, with its template
  content). Denied access is reported as denied, not as missing. Where the lens enters a
  project cannot be removed or renamed through the drive. Subprojects are reached through
  their project. Hidden files other than `.MyOS` are allowed (LibreOffice lock files).
- `core/perspective_fuse.py` - `PerspectiveDriveFuse`, the FUSE operations on the real
  paths; `cli/myperspectivefs.py --projects-root ... --mount-point ...`.
- `daemon/perspective_daemon.py` - the session plus the drive, one socket per projects
  root (`socket_path_for`). FUSE runs in the daemon's own process: a FUSE fork kept only
  one thread, and the socket server was gone (the reason the daemon never answered when
  Scope started it).
- Ending (2026-10-23): the drive ends with the Scope that started it. Scope only asks; the
  daemon unmounts (`fusermount -u`), and its process ends with the drive. While a program
  still has a file open on it (LibreOffice), unmounting is refused: the drive stays and it
  is tried again every 2 s; a client coming back meanwhile (a new Scope) cancels the
  ending. Never killed (a killed daemon left a dead drive, "Transport endpoint is not
  connected") and never unmounted lazily (a program still open would save into the empty
  mount point, outside the projects). SIGTERM takes the same way: it is blocked in all
  threads and received by one of its own (Python runs signal handlers only in the main
  thread, which stays inside FUSE). The former idle timeout (24 h without a request) is
  gone: it would have taken the drive away under a running Scope.
- Scope connects only to the daemon of its projects root and starts it when none runs
  (`MYOS_SCOPE_START_DAEMON=0` switches that off; the tests do). The client is
  `daemon/client.py` (as `Scope/daemon_client.py` it was never imported when Scope runs as
  a script: there "Scope" means Scope.py). Scope's lens display does not use the session
  yet (E3).
- LibreOffice reads its lock file right after creating it: the drive opens created files
  for reading and writing (fusepy does not pass the open flags to `create`).

## A8. Changed Against What Was Built Before

- **"Off" is off.** Before, "Perspective OFF" set the CPD `/Templates` (canonical OFF
  anchor); the perspective stayed active, the OFF button and pin stayed visible.
- **The drive does not follow Scope's lens.** Before, the FUSE context came from the
  session's current state.
- **One state.** Before, the state lived in ScopeApi, in the daemon (with its own,
  diverging `set_cpd`: no OFF anchor, no fallback, other CPD form, "ok" with the old CPD on
  failure), in Scope's QML (display path and CPD cache), in SunTree's QML, and in filters
  (changing ScopeApi past the daemon). Scope attached to any running daemon and sent some
  calls to it, others to its local ScopeApi.
- **Single click on a department folder** opened the real `Templates` folder.
- **The drive's mapping** no longer goes through the CPD resolver (Part B, B7): it is
  `core/perspective_drive.py` (A7). Part B still serves Scope's lens display until E3.
- **Unchanged:** the resolver contract (Part B), the directory fallback with folders
  (A4), double click on the CWD ends the perspective, a template double click sets only the
  lens.

## A9. Open

- The default of the fallback: with or without folders (A4).

# Part B - Resolver Contract (v1, MVP)


## 1. Goal

Define one canonical core contract for virtual perspective navigation before UI/FUSE integration.

This contract is the single source of truth for:
- CPD (current perspective directory) and CWD separation
- virtual-to-real path mapping
- read/write filesystem operations in perspective space
- deterministic error behavior for API, FUSE, CLI, Scope, and SunTree

---

## 2. Scope (MVP)

Included:
- one flipped perspective mode (`flipped`)
- path mapping and directory listing
- create/write/rename/delete behavior
- ACL enforcement through existing core ACL checks

Explicitly not included in v1:
- small-project fallback rule ("if template branch not born, show top-level files")
- multiple perspective types
- optimization/caching beyond basic safety

---

## 3. Terminology

- `CWD` (Current Working Directory): canonical real filesystem path.
- `CPD` (Current Perspective Directory): canonical virtual path in perspective space.
- `Perspective ID`: name of perspective runtime, e.g. `flipped`.
- `Tail`: template-side relative suffix preserved while switching project branch.

Example:
- CPD: `/kommunikation/email/Projekte/ProjektA/Inbox`
- resolved real path (CWD target): `/Projekte/ProjektA/kommunikation/email/Inbox`

---

## 4. Canonical Data Model

```python
from dataclasses import dataclass
from typing import Literal, Optional

ResolverErrorCode = Literal[
    "not_found",
    "denied",
    "invalid_path",
    "ambiguous",
    "conflict",
    "unsupported",
    "io_error",
]

@dataclass(frozen=True)
class PerspectiveContext:
    perspective_id: str              # "flipped"
    project_root: str                # canonical absolute path
    cpd: str                         # canonical absolute virtual path
    cwd_real: str                    # canonical absolute real path
    role: Optional[str] = None       # ACL role if used

@dataclass(frozen=True)
class ResolveResult:
    ok: bool
    cpd: str
    real_path: Optional[str]
    node_type: Literal["file", "dir", "missing", "virtual_anchor"]
    error_code: Optional[ResolverErrorCode] = None
    message: Optional[str] = None
```

Rules:
- all returned paths are absolute and normalized
- no silent fallback to unrelated branches
- ACL denied must return `denied`, never "pretend missing"

---

## 5. Core Resolver API (v1)

```python
def perspective_open(
    *,
    perspective_id: str,
    project_root: str,
    start_real_path: str,
    role: str | None = None,
) -> PerspectiveContext:
    """Initialize context from a real path; derive initial CPD."""

def resolve_virtual_path(
    *,
    ctx: PerspectiveContext,
    cpd: str,
) -> ResolveResult:
    """Resolve CPD path into real node (or explicit error/missing)."""

def resolve_real_path(
    *,
    ctx: PerspectiveContext,
    real_path: str,
) -> ResolveResult:
    """Project real path into CPD for breadcrumbs/location sync."""

def list_virtual_dir(
    *,
    ctx: PerspectiveContext,
    cpd: str,
) -> list[dict]:
    """
    List children in CPD.
    Each item minimally:
      - name: str
      - cpd: str
      - nodeType: "file" | "dir"
      - realPath: str | None
      - isVirtual: bool
    """

def prepare_create(
    *,
    ctx: PerspectiveContext,
    cpd_parent: str,
    name: str,
    node_type: Literal["file", "dir"],
) -> ResolveResult:
    """Return final real target path for create; no I/O side effects."""

def prepare_rename(
    *,
    ctx: PerspectiveContext,
    source_cpd: str,
    target_parent_cpd: str,
    target_name: str,
) -> tuple[ResolveResult, ResolveResult]:
    """Return resolved source and target real paths for atomic rename flow."""
```

---

## 6. Operation Semantics

Read path:
1. resolve CPD
2. ACL check
3. perform operation on resolved real path

Write path:
1. resolve CPD parent/target
2. ACL write check
3. materialize missing real directories only if they are on the mapped target branch
4. perform operation

`rename`:
- cross-branch rename allowed only if both source and target resolve in current perspective/project scope
- otherwise `unsupported` (MVP simplification)

`delete`:
- only if exact node resolves
- deleting a virtual anchor is `unsupported`

---

## 7. FUSE Adapter Mapping (MVP)

FUSE should be a thin adapter over resolver calls:

- `getattr(path)` -> `resolve_virtual_path`
- `readdir(path)` -> `list_virtual_dir`
- `open(path)` / `read(path)` -> `resolve_virtual_path` then OS read
- `create(path)` / `mkdir(path)` -> `prepare_create` then OS create
- `rename(src, dst)` -> `prepare_rename` then OS rename
- `unlink(path)` / `rmdir(path)` -> `resolve_virtual_path` then OS delete

No mapping logic should live only in FUSE.

---

## 8. Error Mapping

Recommended errno mapping:
- `not_found` -> `ENOENT`
- `denied` -> `EACCES`
- `invalid_path` -> `EINVAL`
- `ambiguous` -> `ELOOP` or `EINVAL` (pick one and keep stable)
- `conflict` -> `EEXIST`
- `unsupported` -> `ENOTSUP`
- `io_error` -> `EIO`

---

## 9. Invariants (Must Hold)

- Same CPD input always resolves deterministically for same context.
- `resolve_virtual_path` and `resolve_real_path` are stable inverses where mapping is representable.
- ACL semantics are identical across API/FUSE/CLI/GUI.
- Resolver owns perspective semantics; adapters own transport/protocol only.

---

## 10. Acceptance Criteria (MVP)

1. A file browser can mount `/Meine Struktur` and traverse the flipped tree.
2. A third-party app can "Save As" into CPD and file lands in correct real project path.
3. Rename/create/delete works for resolved nodes without perspective leaks.
4. CLI and Scope can query resolver and show same CPD/real location pair.
5. No small-project fallback yet; missing branch parts return deterministic `not_found`.

---

## 11. Suggested Implementation Order

1. Implement resolver contract in core (tests first).
2. Add FUSE adapter with only contract calls.
3. Add convenience API wrappers for Scope/SunTree.
4. Align CLI commands on same resolver.
5. Introduce fallback behavior as v2 extension.

---

## 12. Test Matrix

Use the dedicated Given/When/Then matrix:

- `core/Dokumentation/Perspective Resolver MVP Test Matrix.md`

---

## 13. Runtime Guardrails (Implemented for MVP)

- No path escapes outside `project_root` after any resolver mapping.
- No silent fallback when CPD branch parts are missing.
- Virtual anchors are non-deletable (`unsupported`).
- FUSE adapter maps resolver errors to stable errno values.
- Debug logging includes operation name plus CPD/real/error triplet for diagnostics.

---

## 14. Explicit MVP Limits

- Only perspective id `flipped` is supported.
- No file-read fallback rule in v1.1.
- Cross-project rename is rejected as `unsupported`.
- Performance optimizations/caching beyond safety are postponed to v2.

---

## 15. v1.1 Directory-Read Fallback Semantics

- `readdir` and directory-oriented `getattr` may fall back to the nearest
  existing parent in the same project branch when the canonical CPD directory
  is not physically present yet.
- File reads (`open/read`) remain strict-canonical and return `not_found`/`ENOENT`
  when the canonical target file does not exist.
- Write operations remain strict-canonical.
- Birth/materialization of missing parents is owned by BlueprintLayer and must
  not be re-implemented in perspective resolver/FUSE logic.
