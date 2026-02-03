# **MyOS Perspectives - Design Document (Draft)**

## **1. Purpose**
Perspectives are view layers that shape how data is shown without changing permissions. They are the “glasses” through which users see a subset of data in a structured, understandable way. They are like complex filters that let you work inside your data (create, edit, delete, ...). Filters are short‑lived, while perspectives shape the environment you are working in.

---

## **2. Core Principles**
- **ACLs rule**: perspectives never reveal data beyond ACL permissions.
- **Flattened but traceable**: flattened views always know about origin and path and can show or use it on demand.
- **Self‑explanatory**: perspective rules should be readable by non‑technical users.
- **Portable**: perspectives are stored as Markdown configs in `.MyOS/`.

---

## **3. What a Perspective Can Do**
- Include or exclude paths and folders (e.g., `/finanz/` with exceptions)
- Filter by filename patterns or extensions (e.g., `*.pdf`, `*rechnung*`)
- Filter by tags (future)
- Filter by AI analysis (future)
- Flatten deep trees while preserving provenance
- Group by project, folder, tag, or date
- Provide a custom UI profile (`Desk.md`)

---

## **4. Types of Perspectives**
### **4.1 Auto Perspective**
Automatically applied when entering a folder context (e.g., CWD in `/finanz/`).

### **4.2 Manual Perspective**
Explicitly selected by the user. Manual perspectives override auto perspectives.

Rule: The most specific explicit manual perspective wins. If none is set, auto perspective applies.

---

## **5. Persistence and Inheritance**
Perspectives are stored in `.MyOS/` as Markdown files and can exist in:
- project roots (inherited by subprojects)
- template roots (shared by template instances)
- normal folders in the tree or in templates (e.g., `/finanz/` in the template for auto perspective)

Inheritance follows standard rules with `dynamic` as default. A future global mode `sparse` may store only deltas instead of full copies.

---

## **6. Perspective Definition (Draft)**
Perspectives are defined with sections for scope, rules, and display. The parser accepts simple lines directly under headers and stops at empty lines, so the draft format below avoids blank lines inside sections.

```
# Perspective
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
- perspectives never bypass ACLs
- hidden/system folders are excluded by default
- perspective rules are data, not executable scripts

---

## **10. Open Questions**
- final file format and section names
- default storage location for global perspectives
- rule syntax for tags and AI filters

---

## **11. Not Realized Yet**
- tag‑based perspectives
- AI‑based perspectives
- `sparse` inheritance mode

---

## **12. Summary**
Perspectives provide user‑friendly, powerful views over MyOS data:
- they filter and shape data without changing permissions
- they can flatten and group complex trees
- they are stored as portable Markdown configs
