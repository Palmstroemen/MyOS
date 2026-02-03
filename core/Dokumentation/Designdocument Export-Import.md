# **MyOS Export/Import - Design Document (Draft)**

## **1. Purpose**
Define a portable export/import flow that:
- preserves project context and rules
- supports partial subtree exports
- allows safe re-import or adoption elsewhere

---

## **2. Scope**
**In scope (MVP):**
- export a subtree starting at a given path
- include project root config and ACLs
- include templates so a target system can continue working
- record reference path for re-import
- import with merge as default and explicit conflict modes

**Out of scope (MVP):**
- Live-MyOS bundle (optional later)
- OS-native ACL mapping
- advanced conflict UI

---

## **3. Terminology**
- **Project Root**: nearest folder containing `.MyOS/Project.md`
- **Export Root**: the Project Root of the subtree being exported
- **Export Subtree**: the selected path under Export Root
- **Reference Path**: original absolute path of Export Root in source system
- **Package**: exported content as folder or zip archive

---

## **4. Export Modes**
### **4.1 Default: Folder**
The default export is a directory containing:
- the selected subtree
- `.MyOS/` from Export Root (config, ACLs, templates reference)
- templates for the project
- export metadata
Default export name: `<ProjectName>_export_<YYYYMMDD>`.

### **4.2 Optional: Zip**
If `--zip` is set, the same content is packaged into a zip archive and the export folder is removed afterwards.

---

## **5. Export Contents**
### **5.1 Subtree**
Only real (physical) files and folders are exported. Embryos are not exported. The target can recreate them from templates.

### **5.2 Project Config**
Include `.MyOS/` from Export Root:
- `Project.md`
- `Templates.md`
- `Manifest.md` (if present)
- `Config.md` or equivalent single files
- `ACLs.md`

### **5.3 Templates**
Templates are always included so the receiver can continue working. Optional future behavior: include templates read-only.

### **5.4 Metadata**
Export metadata records:
- source system identity (placeholder)
- export timestamp
- reference path for re-import
- export subtree path
Optional: a local export history log in the original project (for cloud binding or audit trails), e.g. `.MyOS/ExportHistory.md` or a dedicated section in `Project.md`.

---

## **6. Reference Path**
The export stores the original location in `.MyOS/Project.md`.

Example:
- Export subtree: `/Projekte/Haus/Dach/finanz/ausgaben/`
- Export Root: `/Projekte/Haus/Dach/`
- Reference Path: `/Projekte/Haus/Dach/`

---

## **7. Import Modes**
### **7.1 Restore Into Origin**
If the reference path exists, import attempts to reattach the subtree to its original location.

### **7.2 Adopt as New Project**
If reference path is absent or user chooses adoption, import creates or merges into a new target location.

---

## **8. Importer Design (MVP)**
### **8.1 Inputs**
- import source: folder or zip
- target base path (optional override)
- mode: restore or adopt
- conflict mode: merge, overwrite, skip, or per-file/per-folder decisions
- template handling: accept, ignore, or stage for review
- ACL handling: accept, ignore, or stage for review

### **8.2 Steps**
1) Resolve package (unzip if needed into a temp directory)
2) Validate package structure (`.MyOS/Project.md` exists)
3) Read export metadata from `Project.md` (`ReferencePath`, `Subtree`, `ExportedAt`, `Source`)
4) Run external virus scan (stub for MVP)
5) Resolve target root based on mode
6) Dry-run scan for conflicts and security checks
7) Apply selected conflict strategy
8) Apply ACL/template changes only if explicitly accepted
9) Write import summary report (optional)

### **8.3 Outputs**
- imported subtree placed at target location
- optional import report for conflicts and decisions

---

## **9. Conflict Strategy**
Default: **merge**.
Support conflict modes:
- merge (default)
- overwrite
- skip
- per-file/per-folder decision (interactive or batch rule)

---

## **10. ACL and Template Deltas**
Template or ACL changes from the export have to be made **visible** and can be explicitly accepted or ignored.
Use case: team lead reviews ACLs prepared by another person.

---

## **11. Source Identity**
Record a source identifier for provenance and collaboration.
Options (non-binding):
- hostname + user
- MAC address
- generated project UUID

---

## **12. Security Considerations**
- do not export hidden/system folders outside the subtree
- keep ACLs as data, do not apply OS ACLs during import
- validate paths to prevent traversal during import

---

## **13. Open Questions**
- live MyOS bundle as optional export target?
- read-only template export mode?
- conflict resolution UI for large imports?
- path length constraints and project "splitting" support?

---

## **14. Not Realized Yet**
- Importer module (merge modes, conflict UI, and adoption flow)
- Export history log in the original project
- Live-MyOS bundle option
- Read-only template export option
- Path splitting for very long paths

---

## **15. Summary**
The export/import design aims for portability and clarity:
- subtree exports rooted in a project
- config and ACLs always travel with the data
- templates included to keep MyOS functional
- reference path enables re-import into the original location
