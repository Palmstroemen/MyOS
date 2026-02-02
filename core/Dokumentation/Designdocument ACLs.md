# **MyOS ACLs - Design Document (Draft)**

## **1. Purpose**
MyOS ACLs define **human‑readable, project‑level access rules** that are **self‑explanatory** and
portable across platforms. The system must work even when OS‑native ACLs are unavailable, and it
should be adaptable via plugins.

---

## **2. ACLs.md Format (Draft)**
`ACLs.md` lives in `.MyOS/` and follows the same parser rules as other config files.

### **2.1 Sections**
Recommended sections:
- **`# Permissions`**: Role → allowed paths + rights
- **`# Users`** *(optional for MVP)*: User → role(s)
- **`# inherit`** *(optional)*: Inherit rules if used (default: `dynamic`)

### **2.2 Example**
```markdown
# Permissions

## Folder
- /{Folder}/: read, write
- /info/: read

## Admin
- /*: read, write, execute, change

## Buchhalter
- /finanz/: read, write, execute
- /rechtliches/: read

## Entwickler
- /finanz/eingang/: read, write
- /ressources/: read
- /ressources/datenblaetter/: read, write
- /work/scrum/: read, write, execute

# Users
anna: Admin
karl: Entwickler, Buchhalter
```

Notes:
- Rights are explicit. **MVP rights set**: `read`, `write`, `execute`, `change`.
- `change` only grants write access to `.MyOS/ACLs.md` (ACL management).
- Paths are **relative to the project root** (e.g. `/finanz/`).
- `*` can be used as a wildcard path (e.g. `/*: read, write`).
- If no `inherit` is defined, the default is **`dynamic`**.

---

## **2. Core Philosophy**
- **Self‑explanatory**: Access rules should be understandable at a glance.
- **Project‑centric**: ACLs live with the project and reflect its structure.
- **Role‑first**: Roles map to top‑level project domains.
- **Portable**: The ACL model is OS‑agnostic and can be mapped to platform ACLs when possible.

---

## **3. Default Domain Structure (Suggested)**
This is a **default template** that can be adapted by users via their own templates:

- **/admin/** → leadership / management
- **/info/** → reception / first information
- **/team/** → HR and team administration (not the work area)
- **/communikation/** → internal/external communication (web, social, customers, investors, vendors)
- **/finanz/** → finance
- **/rechtliches/** → legal
- **/ressources/** → assets, inventory, manuals, infrastructure
- **/work/** → actual work (scrum, shifts, patients, clients, etc.)
- **/dokumentation/** → archive, documentation, media

Users can **customize** this structure by creating their own templates.

---

## **4. ACL Concepts**
### **4.1 Roles from Structure**
Each top‑level folder implies a **default role**:
- `/finanz/` → **Finance**
- `/team/` → **HR**
- `/admin/` → **Admin**
- etc.

**Folder defaults:**  
The `## Folder` block defines rights that apply to all auto‑generated roles.
These defaults **do not merge** with role‑specific permissions; the role‑specific block
must list all intended rights explicitly. This allows rights to be removed as well as added.
Within the `## Folder` block, **duplicate paths are merged** (rights are unioned) so that
global defaults like `/info/` remain additive.

### **4.2 Custom Roles**
Admins can define **custom roles**, e.g. **“Prokura”** with access to `/finanz/` and `/rechtliches/`.

### **4.3 Admin Role**
The **Admin** role:
- has full access to all domains
- can change ACLs
Other roles may **read** ACLs but not change them.

---

## **5. Storage & Management**
### **5.1 Source of Truth**
ACL rules live in **`.MyOS/ACLs.md`** (technical source of truth).

### **5.2 Team Management View**
The **/team/** area is the **human management space** for teams:
- team lists, CVs, staffing, goals
- **UI / workflow** to edit ACLs (writes to `.MyOS/ACLs.md`)

This keeps technical config hidden while remaining **accessible and self‑explanatory**.

---

## **6. Cross‑Platform & External Media**
### **6.1 General Principle**
MyOS ACLs are **logical rules** that can be:
1) enforced internally (FUSE, CLI, GUI)
2) mapped to OS‑native ACLs when possible

### **6.2 USB / FAT32 / exFAT**
These filesystems lack proper ACL support.  
**Proposed MVP behavior:** provide **role‑based export** instead of native ACLs.  
Example: a “Finance” export includes only `/finanz/` (and any other paths granted to that role).

### **6.3 Clouds & Sync**
Cloud providers vary in ACL support.  
**MVP approach:** keep `.MyOS/ACLs.md` as the portable source of truth and enforce access
through MyOS tooling when the project is mounted or opened.

### **6.4 Windows / macOS Integration (Future)**
Provide **optional mapping plugins**:
- **NTFS plugin** (Windows)
- **APFS plugin** (macOS)
- **POSIX ACL plugin** (Linux)

These plugins would translate MyOS roles into native ACL entries when supported.

### **6.5 Live‑MyOS on USB (Exploratory)**
Consider a **portable “Live‑MyOS”** image for USB sticks that enforces ACLs at runtime,
independent of the underlying filesystem.

---

## **7. MVP Scope**
The MVP should demonstrate that **access control is real and intentional**:
- ACLs stored in `.MyOS/ACLs.md`
- Role‑based checks in the MyOS layer (FUSE/CLI)
- Export restricted by role (USB or share)
- Clear API boundaries for future plugins

---

## **8. Plugin‑Ready Architecture (Concept)**
Define a small, stable interface for ACL backends:
- **Read rules** from `.MyOS/ACLs.md`
- **Resolve role → allowed paths**
- **Enforce** rules in MyOS tooling
- **Optionally sync** to OS‑native ACLs

---

## **9. Open Questions**
- Do we need additional rights beyond the MVP set? (e.g., list, birth)
- Do we ever need a dedicated `mychmod` command, or is ACL editing sufficient?
- How should role inheritance be expressed?
- Should template roles auto‑generate users/groups?
- How is auditing handled (who changed ACLs, when)?

---

## **10. Summary**
MyOS ACLs are **human‑first** and **portable**:
- **Self‑explanatory** because they mirror project structure
- **Adaptable** via templates
- **Portable** across systems via plugins and exports
- **Enforceable** through MyOS tooling, even without OS ACL support
