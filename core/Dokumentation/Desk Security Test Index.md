# Desk Security Test Index

This file tracks security-relevant coverage for the `Desk.md` system.

## 1) Covered Attack Classes

### A. Path traversal / filename injection
- Rejects unsafe config names like `../outside.md`, separators, and spoofed names.
- Rejects overlong config names.
- Coverage:
  - `core/tests/unit/test_scope_api_tags.py`
  - `core/tests/unit/test_desk_service.py`

### B. Perspective desk escape attempts
- Rejects perspective-linked desk references escaping perspective base directory.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_desk_config.py`

### C. Symlink-based profile escape
- Rejects symlinked `Desk.md` files during desk profile parsing.
- Coverage:
  - `core/tests/unit/test_desk_config.py`

### D. Wallpaper path abuse
- Relative wallpaper presets must remain inside profile directory.
- Relative symlink escape is rejected.
- Relative symlink inside profile is accepted.
- Explicit wallpaper path is treated as intentional user override.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`

### E. Command execution abuse
- Dry-run mode does not execute subprocesses.
- Argument boundaries preserved (no shell splitting; payload remains one argument).
- Timeout and OSError are handled without crashing runtime flow.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`

### F. Parser robustness / malformed input
- Fuzz-like randomized Desk payloads and markdown content do not crash parser/resolver.
- `inherit` normalization remains within allowed values.
- Coverage:
  - `core/tests/unit/test_desk_config.py`

### G. Runtime context robustness
- Invalid path input does not crash context handling.
- Runtime reports controlled `invalid_path` / `runtime_error`.
- Coverage:
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_scope_api_tags.py`

## 2) Current Security Notes in Code

Security comments have been added at enforcement points, for example:
- `core/desk.py`
- `core/desk_runtime.py`
- `core/desk_service.py`
- `core/scope_api.py`
- `core/desktop_backends/kde.py`

These comments use the required prefix:
- `# Security: ...`

## 3) Suggested Next Hardening Steps

1. Add TOCTOU-focused tests around file existence changes between validation and command execution for wallpaper files.
2. Add high-volume fuzz corpus for markdown parser edge cases (long unicode sequences, repeated mixed sections).
3. Add optional policy mode for explicit wallpaper paths (`strict_relative_only` vs `allow_explicit_absolute`).
4. Add integration tests for Scope/PostFix context switching with desk runtime enabled and backend mocked.

## 4) Quick Status

- Desk security suite status (latest run): all targeted tests passing.
- Primary desk security test files:
  - `core/tests/unit/test_desk_config.py`
  - `core/tests/unit/test_desk_runtime_api.py`
  - `core/tests/unit/test_desk_service.py`
  - `core/tests/unit/test_scope_api_tags.py`
