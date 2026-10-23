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
4. The path line now reads `Projekte › Musikstudio › [✕ 04_Finanz › Ausgangsrechnungen ›
   2026]`. A click on `Projekte` (left of the frame) lets me choose `Reisen`: the frame
   stays, I am at once in `Reisen/04_Finanz/Ausgangsrechnungen/2026` and drop the invoice
   there. (If `2026` does not exist there yet, it shows as an embryo inside the frame; the
   folder is born by the drop, or sorting by date files it into its year.)
5. Back to the studio: `Projekte` → `Musikstudio` (the frame comes along), then ✕ - the
   frame is gone, I am in `Musikstudio/04_Finanz/Ausgangsrechnungen/2026` with the
   studio's desktop.

## A2. Terms

- **CWD** - where I am: the path line without a frame (A3). Its project's Desk applies
  without a lens.
- **CTD** - where I look and drop (see "Vision/GUI Filebrowser.md"). With a lens on, the
  lens is the CTD: it can point into another project than the CWD.
- **Lens (CPD)** - the turned path, e.g. `/04_Finanz/Ausgangsrechnungen/2026/Projekte/Reisen`
  in the resolver's form: the department path (template side), the project, and a tail.
  A lens may sit at any depth of the department (`/04_Finanz`, `/04_Finanz/Ausgangsrechnungen/2026`).
- **Department** - a template folder (`00_Admin` ... `08_Dokumentation`).
- **CLD** (current lens directory, 2026-10-23) - the department path the lens fixes, e.g.
  `04_Finanz/Ausgaben`. Scope shows it framed inside the one path line (A3). The CPD is the
  same lens in the turned form of the drive.

## A3. The Path Line With the Frame (CLD)

Decided 2026-10-23 after a clickable sketch (artifact "Brillenrahmen"); replaces the two
menus (left: CWD, right: lens) decided on 2026-10-22, which did not work in Scope.

**One line, one place.** Scope shows one path line. Without a lens:
`Projekte › Job › 04_Finanz › Ausgaben`. With a lens the department part is framed:
`Projekte › Job › [✕ 04_Finanz › Ausgaben]`. The frame shows what is fixed: the CLD. There
is no second place to come back to - the line is where one is, with or without a frame.

1. **Put on a lens:** a double click on a MyOS folder (department folder or any folder
   below it, at any depth, born or embryo) frames the department path down to it. A
   double click elsewhere sets the CWD as before. So inside the MyOS folders a double click
   always puts on a lens; one never sets a plain CWD there. Within one's own project this
   is not felt - the line and the FilesPanel look as if the CWD had been set; the frame
   only matters when the project changes. (Decided 2026-10-23.)
2. **Left of the frame - which project:** a click on `Projekte` opens a list (on click,
   never on hover) of the projects and "Shelf: all projects". Choosing a project moves
   only the part left of the frame; the frame and its depth stay (`.../Ausgaben/2026`).
   Without a lens, the same list changes the project one is in.
3. **The shelf:** `Projekte › [✕ 04_Finanz › Ausgaben]` - the CLD of all projects, real
   projects only (no `Clipboard`, no plain folders); the FilesPanel lists them with a
   "Project" column.
4. **Inside the frame - which department path:** a click on a segment makes the lens
   flatter; the folders below the frame make it sharper; a double click on another MyOS
   folder changes the lens.
5. **The frame never changes for embryos.** A folder of the CLD not born in the shown
   project is drawn as an embryo (pale, dashed) inside the frame, as everywhere; the frame
   itself stays as it is. The FilesPanel shows the fallback (A4).
6. **✕ takes off only the frame.** One stays where the lens looked:
   `Projekte › Job › [✕ 04_Finanz › Ausgaben]` becomes `Projekte › Job › 04_Finanz ›
   Ausgaben`, now the CWD (an embryo there stays an embryo until something is dropped).
   The Desk turns back to the project's (A5).
7. **Without a lens:** a click on a folder goes into it (a MyOS folder of the CWD's
   project, born or embryo - not the real `Templates` folder); a click on a segment goes
   back up.

**The frame in tutorials (and later perhaps in Scope).** The frame shows the turned path
directly: an animation slides the framed part to the left in front of `Projekte › Job`,
giving the drive's form `04_Finanz › Ausgaben › Projekte › Job`, and back again.

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

While a lens is on, the department's Desk applies (the nearest `Desk.md` up the department
path: `2026` → `Ausgangsrechnungen` → `04_Finanz`, prepared in the template, e.g.
`Templates/Standard/04_Finanz/.MyOS/Desk.md`), wherever the lens or the CWD is moved. The
lens' Desk overrules the project's: moving the lens from `Musikstudio` (dark) to `Reisen`
keeps the finance Desk (light); Reisen's Desk is ignored while the frame is on. Taking the
lens off (✕) brings the Desk of the project one then stands in: in `Reisen/04_Finanz/...`
that is Reisen's, not Musikstudio's. Dropping something into a department folder without a
lens does not change the Desk.

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
  a script: there "Scope" means Scope.py).
- Scope on the session (E3, 2026-10-23; the gestures below are an interim state - the
  path line with the framed lens (CLD, A3) replaces them in E3b): `Backend.lens(method, params)` asks the session
  (the daemon's, or without a daemon `LocalSession`, the same answers in Scope's process);
  `lensBear()` bears the lens' folder where the user may write. QML builds no lens paths:
  the MyOS-folder row shows the lens' folder as a real path in its project (`target`, path
  bar from `project_dir`), so its menus, embryos and hover preview work as without a lens;
  the FilesPanel shows `shown` (the lens' folder or the fallback). Gestures: a double click
  on a MyOS folder puts on its lens (`look_at`, any depth); with a lens on, a click on a
  folder of the row or a path segment moves the lens there (sharper, flatter, another
  department); a double click in the left menu changes the CWD and the lens follows (a
  single click browses as without a lens: its menus open, the FilesPanel shows the folder,
  the lens stays on; a single click on the lens' folder shows the lens again);
  a double click in the FilesPanel on a folder of the department makes the lens sharper,
  on any other folder takes it off and goes there; "End perspective" or a double click on
  the CWD takes it off (the latter never worked: the handler named the function without
  calling it). Something new in the fallback (drop on the panel, new folder, new note)
  goes into the lens' folder, born then. On the shelf (the CWD a folder of projects) Scope
  shows the CWD until E4; the session then puts the shelf at the projects root, not at
  the folder of projects (to fix with E4).
- The path line with the frame (E3b, 2026-10-23, A3): the MyOS-folder row's path line
  frames the segments below the lens' project (`Job › [✕ 04_Finanz › Ausgaben]`; in the
  vertical view the framed segments are outlined, the ✕ stands before them). Path
  segments whose folder does not exist are pale, as embryos are in the rows - in every
  path line, with or without a lens (the path line never showed embryos before); asked
  again with each new listing, so a birth shows at once. The frame stays. The projects row
  is left of the frame: with a lens on, a double click on a project moves the lens there
  (`move_to`, a real path) and the row shows that project; on any other folder it takes
  the lens off. ✕ (`take_off`) leaves one where the lens looked: its project becomes the
  CWD, the row stays on the lens' folder, the FilesPanel keeps what it showed. The session
  no longer lets the lens follow the CWD; "End perspective", the pin and the double click
  on the CWD are gone. Not yet: the shelf and the project list on a click on `Projekte`
  (E4), the department's Desk (E3c; until then the Desk follows the project in the row).
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
- **Two menus and a CWD to come back to** (decided 2026-10-22) gave way to one path line
  with the framed lens (A3, 2026-10-23): ✕ keeps the place, the project left of the frame
  is chosen with a click on `Projekte`.
- **The drive's mapping** no longer goes through the CPD resolver (Part B, B7): it is
  `core/perspective_drive.py` (A7). Part B still serves Scope's lens display until E3.
- **Unchanged:** the resolver contract (Part B), the directory fallback with folders
  (A4), a template double click sets only the lens.

## A9. The Drive Belongs to MyOS (Concept, 2026-10-23)

Not built yet; to be decided whether before E3.

**A MyOS service, not a Scope feature.** LibreOffice, the command line (`cd
Perspektiven/04_Finanz/Projekte`) and every other program use the drive without Scope. So
the daemon lives with the login session, not with a Scope window:

- "Starting MyOS" is logging in: a systemd user service (`systemctl --user`) starts the
  daemon at login and ends it at logout (SIGTERM; the ending of A7 - busy drive waits,
  never killed - already holds). `myos start`, `myos stop` and `myos status` as plain
  commands.
- Scope only connects; it neither starts nor stops the daemon (at most it starts a missing
  one). Closing Scope does not end MyOS; the small Scope instance (top left) may offer
  "Quit MyOS".
- Service and small Scope stay separate (invisible base / user interface) but start
  together (autostart).
- More may move into the service later: catching up on filing (Designdocument Sort.md,
  section 4), the Desk and taskbar switching, SunTree.

**Mounted like a network drive.** A drive always mounted next to `Projekte` would show
every project file twice: backups (Déjà Dup, rsync), search indexes, `du ~` and `find ~`
would see and store everything twice. Mounting over `Projekte` instead (either/or) was
weighed and rejected: the daemon needs the real tree it would hide; a crashed daemon would
make all projects seem gone (dead mount point), not only the view; shells, open documents
and backups inside `Projekte` would suddenly see the turned tree. Instead, as gvfs does
for network drives (`/run/user/<uid>/gvfs`):

- The drive is mounted outside the home folder: `/run/user/<uid>/myos/Perspektiven`
  (one per projects root).
- Next to `Projekte` lies only a symlink `Perspektiven` to it. In file managers, in
  LibreOffice and on the command line it behaves like a folder; tools walking the home
  folder from above do not follow symlinks by default (`find`, `rsync`, `du`; to be
  checked for Nemo, Déjà Dup and the search indexes on the real desktop before deciding).
- Without MyOS running, the symlink points nowhere - more honest than an empty folder one
  could save into by mistake.

**Searching in the perspective.** The perspectives are where one searches most: "Where is
the invoice from FirmaX from two weeks ago? In which project was it?"

- Global search (desktop search, indexes) finds the real file once, under
  `Projekte/Job/04_Finanz/...`; the path names the project. Without the symlink every hit
  would appear twice.
- A search started *inside* the perspective (the file manager's search in
  `Perspektiven/04_Finanz/Projekte`, `find . -iname '*FirmaX*' -mtime -14` there) walks
  the drive and finds everything; the first part of the path is the project.
- Scope answers the same question faster on the real tree, since it knows the mapping:
  with the lens `04_Finanz` on, a search for "FirmaX", last two weeks, looks only into the
  `04_Finanz` folders of all projects and lists the hits with a "Project" column. This
  belongs to E6 (a filter puts on a lens); the dates come from the sort rules' date
  sources (Designdocument Sort.md, section 5), right even when copying changed the
  modification time.
- Energy: such a search touches only the department's folders, not the whole disk or the
  whole home folder. For one person this is irrelevant; across many users and data
  centres it may be a real argument for MyOS. Claim (Oliver): about one hundredth of the
  energy for such searches. To be measured - it depends on the share of files in the
  department's folders, and against a search that already uses an index the gain is
  smaller than against a full scan.

## A10. Open

- ✕ on the shelf: the sketch goes to `Projekte` (the list of projects), since there is no
  place `Projekte/04_Finanz`.
- Going deeper without changing the lens (right of the frame) - not drawn yet.
- Whether the CWD survives as a word: with one line it is simply where one is.
- The default of the fallback: with or without folders (A4).
- The MyOS service (A9): which projects roots it serves (a small configuration: the real
  one, `MyOS_Test`); autostart of the small Scope; how Nemo, Déjà Dup and the search
  indexes treat the `Perspektiven` symlink on the real desktop.

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
