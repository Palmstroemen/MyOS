# **MyOS Filters & Perspectives - Design Document (Draft)**

## **1. Purpose**
The currently implemented system in MyOS is called **Filter**. Filters shape how data is shown without changing permissions and provide include/exclude/rule/group/flatten behavior.

The term **Perspective** is reserved for a future flipped path-space navigation model and is intentionally not used for the current filter runtime API.

---

## **2. Core Principles**
- **ACLs rule**: filters never reveal data beyond ACL permissions.
- **Flattened but traceable**: flattened views always know about origin and path and can show or use it on demand.
- **Self‑explanatory**: filter rules should be readable by non‑technical users.
- **Portable**: filters are stored as Markdown configs in `.MyOS/`.

---

## **3. What a Filter Can Do**
- Include or exclude paths and folders (e.g., `/finanz/` with exceptions)
- Filter by filename patterns or extensions (e.g., `*.pdf`, `*rechnung*`)
- Filter by tags (future)
- Filter by AI analysis (future)
- Flatten deep trees while preserving provenance
- Group by project, folder, tag, or date
- Provide a custom UI profile (`Desk.md`)

---

## **4. Types of Filters**
### **4.1 Auto Filter**
Automatically applied when entering a folder context (e.g., CWD in `/finanz/`).

### **4.2 Manual Filter**
Explicitly selected by the user. Manual filters override auto filters.

Rule: The most specific explicit manual filter wins. If none is set, auto filter applies.

---

## **5. Persistence and Inheritance**
Filters are stored in `.MyOS/` as Markdown files and can exist in:
- project roots (inherited by subprojects)
- template roots (shared by template instances)
- normal folders in the tree or in templates (e.g., `/finanz/` in the template for auto perspective)

Inheritance follows standard rules with `dynamic` as default. A future global mode `sparse` may store only deltas instead of full copies.

---

## **6. Filter Definition (Draft)**
Filters are defined with sections for scope, rules, and display. The parser accepts simple lines directly under headers and stops at empty lines, so the draft format below avoids blank lines inside sections.

```
# Filter
Name: Finance
Scope: /finanz/

## Include
/finanz/
/rechtliches/

## Exclude
/finanz/schwarzgeld/

## Filter
*/rechnung.pdf
*/invoice.pdf
*/*rechnung.*
*/*invoice.*
/*.jpg

## Flatten
true

## Group
project
tags

## Desk
Desk.md
```

Open item: we may evolve the parser to allow more natural inline formatting later (e.g., `## Group_by: project`). We also keep “friendly input” options like pipe-separated lists (`| A | B | C`) in mind for the future, but not for MVP.

---

## **7. Flattening**
Flattening shows items in a single view while preserving origin:
- show source path as a badge or breadcrumb
- provide quick navigation back to original location

Flattening is a core USP for MyOS.
Flattening is already prototyped in the myls command via `--roentgen`.

---

## **8. Grouping**
Grouping defines how views are organized:
- by project
- by folder segment
- by tag
- by date

---

## **9. Security Considerations**
- filters never bypass ACLs
- hidden/system folders are excluded by default
- perspective rules are data, not executable scripts

---

## **10. Public API (Current)**
Public API currently lives in `core/perspective.py` and is used by CLI/GUI:
- `FilterConfig.from_file(path)`
- `FilterConfig.from_data(data)`
- `find_filters(start_path)`
- `resolve_active_filter(cwd, manual=None)`

Reserved term note: **Perspective** is reserved for the upcoming flipped path-space navigation model and will be implemented via new, separate APIs.

---

## **11. Open Questions**
- default storage location for global filters
- rule syntax for tags and AI filters

---

## **12. Not Realized Yet**
- tag‑based filters
- AI‑based filters
- `sparse` inheritance mode

---

## **13. Summary**
Filters provide user‑friendly, powerful views over MyOS data:
- they filter and shape data without changing permissions
- they can flatten and group complex trees
- they are stored as portable Markdown configs

---

## **14. Next Step: Perspective Runtime Contract**
The upcoming flipped path-space Perspective runtime uses a separate contract document:

- `core/Dokumentation/Designdocument Perspective Resolver MVP.md`

This split keeps current Filter behavior stable while defining CPD/CWD resolver semantics for the new Perspective model.
