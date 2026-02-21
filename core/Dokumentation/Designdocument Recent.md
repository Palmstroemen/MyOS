
Interpretation notes:

- `Scope`: `project` (MVP default), later `perspective`.
- `Strategy`:
  - `os-delta` (MVP baseline),
  - `event-first` (future hybrid; MyOS events preferred, OS delta fallback).
- `Limit`: max entries shown/stored in active view.
- Include/exclude rules are optional and can be inherited.

---

## 9. Relationship to Desk.md

Recents should not be embedded into `Desk.md` runtime state.

`Desk.md` may reference how recents are displayed (UI preference), but activity data should remain in dedicated recents storage.

Suggested boundary:

- `Desk.md`: visual/environment profile.
- `Recent.md`: recents policy.
- `.cache/recent.*`: recents runtime data.

---

## 10. Future Evolution (Post-MVP)

1. Add direct MyOS activity events (PostFix/Scope/CLI open/save) for higher precision.
2. Use OS recent list as fallback/import source only.
3. Add optional confidence scoring (`source_weight`, `session_match`).
4. Add perspective-aware recents (`scope: perspective`).
5. Support desktop-environment adapters (KDE, GNOME) without changing MyOS recents model.

---

## 11. Security and Privacy Considerations

- Process recents as data, never as executable instructions.
- Restrict to local file paths by default.
- Do not expose entries beyond current ACL/project boundaries.
- Allow user to clear project recents quickly.
- Log parse/import failures safely (no crashes on malformed external entries).

---

## 12. Summary

MVP recents in MyOS should use a practical snapshot-delta approach against OS recents, filtered strictly to project scope and merged into a project-local data store.

This provides immediate value with low complexity while preserving a clean migration path toward precise event-based recents later.