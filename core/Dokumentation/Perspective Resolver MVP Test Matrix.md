# Perspective Resolver MVP - Test Matrix

## Purpose

This matrix defines the minimum behavioral tests for the flipped Perspective resolver v1.
It is written in Given/When/Then form and should be used for:
- core resolver unit tests (first)
- integration tests in FUSE adapter
- consistency checks for Scope/SunTree/CLI adapters

Initial pytest skeleton:
- `core/tests/unit/test_perspective_resolver_mvp.py`

---

## Shared Fixture Assumptions

- Real root: `/Projekte`
- Projects:
  - `/Projekte/ProjektA`
  - `/Projekte/ProjektB`
- Template branch (born in ProjektA):
  - `/Projekte/ProjektA/kommunikation/email`
- Optional content:
  - `/Projekte/ProjektA/kommunikation/email/inbox/mail1.eml`
  - `/Projekte/ProjektB/kommunikation` may or may not exist depending on case
- Perspective ID: `flipped`
- Virtual root mount style:
  - `/Meine Struktur/kommunikation/email/Projekte/ProjektA/...`

For resolver tests, normalize this to CPD form (without mount prefix if desired):
- `/kommunikation/email/Projekte/ProjektA/...`

---

## Core Mapping Tests

### T01 - Open Context From Real Path

- **Given** a real path `/Projekte/ProjektA/kommunikation/email`
- **When** `perspective_open(flipped, project_root=/Projekte, start_real_path=...)` is called
- **Then** context is created with:
  - `perspective_id = flipped`
  - `cwd_real` normalized to the given path
  - `cpd` mapped to `/kommunikation/email/Projekte/ProjektA`
  - no error

### T02 - Resolve Existing CPD Directory

- **Given** a valid context and existing CPD `/kommunikation/email/Projekte/ProjektA`
- **When** `resolve_virtual_path` is called
- **Then** result is `ok=True`, `node_type=dir`, `real_path=/Projekte/ProjektA/kommunikation/email`

### T03 - Resolve Existing CPD File

- **Given** existing file CPD `/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml`
- **When** `resolve_virtual_path` is called
- **Then** result is `ok=True`, `node_type=file`, canonical `real_path` points to `mail1.eml`

### T04 - Reverse Mapping Real -> CPD

- **Given** real path `/Projekte/ProjektA/kommunikation/email/inbox/mail1.eml`
- **When** `resolve_real_path` is called
- **Then** result returns CPD `/kommunikation/email/Projekte/ProjektA/inbox/mail1.eml`
- **And** mapping is stable (same input returns same output)

### T05 - Determinism

- **Given** unchanged filesystem and unchanged context
- **When** same CPD is resolved multiple times
- **Then** result tuple (`ok`, `node_type`, `real_path`, `error_code`) stays identical

---

## Error and Safety Tests

### T06 - Not Found Branch

- **Given** CPD points to non-existing branch part
- **When** `resolve_virtual_path` is called
- **Then** result is `ok=False`, `error_code=not_found`, `node_type=missing`
- **And** no implicit fallback to unrelated directories occurs in v1

### T07 - Invalid Path Traversal

- **Given** CPD contains invalid traversal segments (e.g. `..` escaping scope)
- **When** resolver is called
- **Then** result is `ok=False`, `error_code=invalid_path`

### T07b - Directory-Read Parent Fallback (v1.1)

- **Given** CPD points to a non-existing directory below an existing parent
- **When** directory-read resolver path is used
- **Then** result is `ok=True` with `fallback_applied=True`
- **And** `effective_read_path` is the nearest existing parent in the same project branch

### T07c - File-Read Stays Strict (v1.1)

- **Given** CPD points to a non-existing file in a non-born branch
- **When** strict file resolver path is used
- **Then** result is `ok=False`, `error_code=not_found` (no fallback)

### T08 - ACL Denied Read

- **Given** path resolves physically but ACL denies read
- **When** resolver/list is called with role context
- **Then** result is `ok=False`, `error_code=denied`

### T09 - Ambiguous Mapping

- **Given** a synthetic case where multiple real targets could match one CPD
- **When** resolver is called
- **Then** result is `ok=False`, `error_code=ambiguous`
- **And** resolver does not pick an arbitrary branch

---

## Directory Listing Tests

### T10 - List Virtual Directory Basic

- **Given** CPD directory resolves
- **When** `list_virtual_dir` is called
- **Then** each item contains:
  - `name`
  - `cpd`
  - `nodeType`
  - `realPath` (or `None` for virtual anchors)
  - `isVirtual`

### T11 - Listing Consistency With Resolver

- **Given** `list_virtual_dir` returns N children
- **When** each child CPD is passed to `resolve_virtual_path`
- **Then** each child resolves consistently with listed metadata

### T12 - ACL-Filtered Listing

- **Given** mixed readable and non-readable children
- **When** directory is listed
- **Then** denied items are either omitted or returned with deterministic denied metadata (choose one policy and keep stable)

---

## Mutation Preparation Tests

### T13 - Prepare Create File

- **Given** CPD parent directory exists and write ACL allows
- **When** `prepare_create(..., node_type=file)` is called
- **Then** result is `ok=True`, `real_path` points to canonical target file path
- **And** function has no side effects by itself

### T14 - Prepare Create Denied

- **Given** parent resolves but write ACL denies
- **When** `prepare_create` is called
- **Then** result is `ok=False`, `error_code=denied`

### T15 - Prepare Rename Within Scope

- **Given** source and target parent both resolve inside same perspective scope
- **When** `prepare_rename` is called
- **Then** both results are `ok=True` and canonical source/target real paths are returned

### T16 - Prepare Rename Cross-Branch Unsupported (MVP)

- **Given** rename target crosses disallowed branch boundary in v1
- **When** `prepare_rename` is called
- **Then** result is `ok=False`, `error_code=unsupported`

---

## Adapter Parity Tests (After Core)

### T17 - FUSE getattr Parity

- **Given** a CPD path
- **When** FUSE `getattr` is invoked
- **Then** status and node type match `resolve_virtual_path`

### T17b - FUSE getattr(dir) Uses Fallback (v1.1)

- **Given** directory CPD in a non-born branch
- **When** FUSE `getattr` is invoked for directory intent
- **Then** adapter returns directory stat from `effective_read_path`

### T18 - FUSE readdir Parity

- **Given** a CPD directory
- **When** FUSE `readdir` is invoked
- **Then** entries match `list_virtual_dir` contract (name and node identity)

### T18b - FUSE open(file) Remains Strict (v1.1)

- **Given** non-existing file CPD in a non-born branch
- **When** FUSE `open` is invoked
- **Then** adapter returns `ENOENT` (no fallback)

### T19 - FUSE Create + Real Filesystem Persistence

- **Given** writable CPD parent
- **When** file is created through FUSE path
- **Then** file appears at expected real path resolved by `prepare_create`

### T20 - Scope/CLI Location Pair Consistency

- **Given** one selected node
- **When** Scope and CLI both query resolver state
- **Then** both show the same `CPD <-> real_path` pair

---

## Suggested Execution Order

1. Implement and pass T01-T16 in core resolver tests.
2. Add FUSE parity tests T17-T19.
3. Add adapter consistency test T20 for Scope/CLI.
4. Add v2 fallback cases in a separate section once small-project fallback is introduced.
