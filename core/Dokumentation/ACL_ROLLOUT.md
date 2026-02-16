# ACL Rollout Guide (MyOS)

This document defines a safe rollout path for ACL enforcement in MyOS.
The goal is to enable security controls incrementally without breaking daily workflows.

## 1) Rollout Modes

- `off`: No blocking, no authorization effect. Use for baseline operation.
- `monitor`: No blocking, but all ACL decisions are evaluated and audited.
- `enforce`: ACL decisions are binding; denied operations are blocked.

Unknown mode values must fail closed to `enforce`.

## 2) Current Enforcement Scope

The code currently supports ACL probing broadly and enforce-mode blocking for:

- `delete_entries`
- `move_entry` / `move_entries`
- `rename_entry` / `rename_entries_batch`
- `create_folder` / `create_note`
- `open_markdown`
- read filtering in `list_entries` / `list_children` (hidden denied paths in enforce mode)

`monitor` mode keeps behavior non-blocking but produces audit evidence.

## 3) Recommended Rollout Sequence

### Phase A - Baseline (`off`)

- Keep ACL disabled in production behavior.
- Verify no regressions in normal project usage.
- Validate policy loading and schema checks in tests.

Exit criteria:

- Unit test suite green.
- No runtime errors in ACL initialization path.

### Phase B - Observe (`monitor`)

- Turn on monitor mode for pilot projects.
- Keep operations non-blocking.
- Collect audit events and inspect denied patterns.

Exit criteria:

- Deny patterns are explainable and expected.
- No excessive noise or malformed audit events.

### Phase C - Selective Enforce

- Enable `enforce` for low-risk and high-value operations first:
  - delete
  - move
  - rename
- Keep remaining areas in monitor if needed.

Exit criteria:

- No unexpected block reports for target cohorts.
- Support team has clear remediation playbook.

### Phase D - Full Enforce

- Enable enforce globally for all ACL-covered operations.
- Keep monitor-style audit logging active.

Exit criteria:

- Stable behavior over agreed soak period.
- No high-severity ACL bypass findings.

## 4) Operational Checklist

Before each rollout step:

- Confirm ACL policy validity (schema + references).
- Confirm mode configuration and fallback behavior.
- Confirm audit sink availability (memory/file).
- Confirm storage bounds for audit logs (rotation active).
- Confirm deny behavior is explicit and user-visible in UI/UX surfaces.

After enabling:

- Review denied events by action (`delete`, `move`, `rename`, `read`, ...).
- Track false positives and adjust policy safely.
- Keep rollback option ready.

## 5) Rollback Strategy

If unexpected blocking occurs:

1. Move from `enforce` -> `monitor` immediately.
2. If instability persists, move to `off`.
3. Preserve audit logs for root-cause analysis.
4. Patch policy or action mapping, then retry rollout on pilot scope.

## 6) Security Notes

- Treat ACL files/policies as privileged configuration.
- Prefer signed canonical policy artifacts for runtime trust.
- Keep default posture deny-oriented where uncertainty exists.
- Never rely on UI-only checks for security enforcement.

## 7) Suggested Configuration Surface

Use a single source of truth in runtime configuration:

- `ACL_ENFORCEMENT_MODE=off|monitor|enforce`
- optional:
  - `ACL_BACKEND=legacy|casbin|auto`
  - `ACL_AUDIT_FILE=<path>`
  - `ACL_USER=<effective-user>`

Keep defaults conservative and explicitly documented.
