# MyOS Perspective Resolver v1 (MVP Contract)

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
