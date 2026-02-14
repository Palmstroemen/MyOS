# **MyOS Tags - Design Document (Draft)**

## **1. Purpose**
Tags add human-readable meaning to files and folders. They should be explicit words, not just colors, and can optionally carry color or icon hints.

---

## **2. Core Principles**
- Tags are always text labels (self-explanatory).
- Colors are optional and must never replace the label.
- Icons are optional and can reinforce meaning.
- Tags may optionally carry numeric values for classification (e.g., 0–100).

---

## **3. Tag Format (Draft)**
Tags are defined as simple label entries with optional attributes:

```
# Tags
wichtig, rot, !
dringend, orange, clock
in Arbeit, gelb
erledigt, grün, check
```

Interpretation:
- first value is the label
- second value is optional color
- third value is optional icon

---

## **4. Multi-Word Tags**
Multi-word labels are allowed and kept as-is:
- `in Arbeit`
- `zu prüfen`

No forced underscore format is required.

---

## **5. Storage**
Primary storage uses filesystem metadata:
- macOS/Linux: extended attributes (xattr)
- Windows/NTFS: to be evaluated

Fallback storage (if metadata is unavailable) may use `.MyOS/Tags.md`, but MVP will prefer native metadata and may not support tags on filesystems without it.

Folder tagging is prepared via a non-project sidecar file:
- `/.MyOS/myTags.md` on the tagged folder itself
- this sidecar does **not** make a folder a MyOS project (`Project.md` remains the project marker)

For MVP, this sidecar path is considered an optional technical bridge and is not actively expanded in UI/semantics yet.

---

## **6. Open Questions**
- icon naming convention (emoji vs icon id)
- icon set selection and theming (global preference, not per project)
- whether tags can be scoped by project or global
- whether tags apply to folders, files, or both
- how numeric tag values are stored and visualized (e.g., Eisenhower/Disney quadrants, 2D charts)
- NTFS metadata mapping strategy

---

## **7. Summary**
Tags are text-first labels with optional color and icon hints. They remain readable without UI decoration and align with the MyOS “self-explanatory” principle.

---

## **8. MVP Checkpoint**
- File tags via xattr are the primary shipped behavior.
- Folder-tag sidecar support (`/.MyOS/myTags.md`) is prepared but intentionally not pushed further for now.
- Reason: keep MVP focused and avoid premature divergence from Obsidian’s tag model (which is primarily note-centric, not native folder-tag-centric).
