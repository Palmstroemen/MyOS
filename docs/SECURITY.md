# MyOS Security Overview

**⚠️ PROTOTYPE — Not for production use**

## Current Protections

- **Path traversal:** Blocked in embryo paths and API entry points
- **ACL system:** Three modes — `off`, `monitor`, `enforce` (see [ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md))
- **Audit logging:** ACL decisions logged in monitor/enforce modes
- **Security tests:** Scope API, PostFix, importer have dedicated security test suites

## ACL Rollout

See [core/Dokumentation/ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md) for the safe rollout path and operational checklist.

## Design Documents

- [Designdocument BlueprintLayer](../core/Dokumentation/Designdocument%20BlueprintLayer.md) — Path traversal, embryo handling
- [Designdocument ACLs](../core/Dokumentation/Designdocument%20ACLs.md) — ACL design
- [Designdocument Export-Import](../core/Dokumentation/Designdocument%20Export-Import.md) — Import/export security

## Reporting Issues

Please report security issues via GitHub issues. Do not disclose critical vulnerabilities in public issues.
