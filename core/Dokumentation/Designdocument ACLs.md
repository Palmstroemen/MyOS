# **MyOS ACLs - Design Document (Draft)**

## **1. Purpose**
MyOS ACLs define **human‑readable, project‑level access rules** that are **self‑explanatory** and
portable across platforms. The system must work even when OS‑native ACLs are unavailable, and it
should be adaptable via plugins.

---

## **2. ACLs.md Format (Draft)**
`ACLs.md` lives in `.MyOS/` and follows the same parser rules as other config files,
with one exception for its layout (see 2.3).

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
- /*: read, write, execute
- /.MyOS/ACLs.md: read, write, change

## Buchhalter
- /finanz/: read, write, execute
- /rechtliches/: read

## Entwickler
- /finanz/eingang/: read, write
- /ressources/: read
- /ressources/datenblaetter/: read, write
- /work/scrum/: read, write, execute
- /work/personal/: none

# Users
anna: Admin
karl: Entwickler, Buchhalter
```

Notes:
- Rights are explicit. **MVP rights set**: `read`, `write`, `execute`, `change`, `delete`.
- `change` only grants write access to `.MyOS/ACLs.md` (ACL management).
- `delete` allows deleting entries. It is **not** implied by `write`: who may edit a folder
  may not automatically delete in it (moving entries needs `write`). `*` includes `delete`.
- Paths are **relative to the project root** (e.g. `/finanz/`).
- `*` can be used as a wildcard path (e.g. `/*: read, write`).
- **Nearest rule wins (per role):** a rule on a deeper folder *replaces* what the role
  would inherit from rules on its parent folders – also when it grants less. So rights
  can be taken away in sub-folders. `none` locks a role out of a folder
  (e.g. `/work/personal/: none`). Roles without a rule on the sub-folder keep inheriting.
  Rules written for the same folder (`/finanz/` and `/finanz/**`) are combined.
- A user's rights are the **union of their roles**: if one role is locked out of a folder
  but another role of the same user may enter it, the user may enter it.
- Because the nearest rule wins, a file-specific rule must list all intended rights
  (e.g. `/.MyOS/ACLs.md: read, write, change`, not just `change`).
- **Subprojects inherit directly:** a subproject without its own `ACLs.md` is governed by
  the nearest parent project's `ACLs.md`; paths stay relative to that parent project
  (e.g. `/Familie/Ich/` for the subproject `Familie/Ich`). A subproject with its own
  `ACLs.md` uses only that file.
- **Folder rules in subprojects:** the `## Folder` rules apply again to the template
  folders of every subproject below, with the subproject's path in front (for the role
  `04_Finanz`, `/{Folder}/` also becomes `/Familie/04_Finanz/`). The rules of a role's own
  section stay paths of the project holding `ACLs.md` (see 2.4).
- If no `inherit` is defined, the default is **`dynamic`**.

### **2.3 Layout: blank lines, notes and comments**
Unlike other config files, a blank line or a line of free text does **not** end a section
in `ACLs.md`. A rule line (`- /path: rights`) belongs to the nearest heading above it, a
user line (`name: roles`) to `# Users` — whatever stands in between. So an `ACLs.md` may be
structured with blank lines, notes and `<!-- comments -->`.

Reason (security): in the general parser one blank line before `- /Arbeit/Geheim/: none`
silently dropped that rule and opened the locked folder again (2026-10-21).

- Lines in `<!-- … -->` are ignored, also over several lines: a commented-out rule does
  not apply.
- `# …` after a rule is an inline comment (`- /Geheim/: none  # since 2026`).
- A line starting with `#` is a **heading**, never a comment: it starts a new section.
- In role sections only list lines with a `:` are rules; other lines are notes.
- Editing in the GUI and rules following a rename leave comments alone; a rule that is
  rewritten loses a comment at the end of its line.

### **2.4 Template folder roles: inherited and explicit entries (like Windows)**
A template folder role (e.g. `Finanz`) **inherits** the `## Folder` rules — in the project
and in every subproject. A section of its own (`## Finanz`) holds **explicit** entries,
which apply **in addition**: writing one never takes the inherited ones away elsewhere.
For the **same folder**, an explicit entry replaces the inherited one (nearest rule
wins), so rights can also be reduced right at the template folder:
```markdown
## Folder
- /{Folder}/: read, write

## Finanz
- /Finanz/Belege/: read        # added; /Finanz/ and /Familie/Finanz/ stay read, write
- /Familie/Finanz/: none       # replaces the inherited entry there
```
Decided 2026-10-21: before, a section of its own replaced *all* folder rules; the first
GUI edit copied the project's folder rules into it and so silently dropped the role's
rights in subprojects. Windows users know this model (inherited and explicit entries);
the difference is that an explicit entry *replaces* the inherited one for its folder,
where Windows would need a deny entry or switching inheritance off.

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
They are the role's **inherited** entries; a role-specific block adds **explicit** entries,
and an explicit entry replaces the inherited one for the same folder (see 2.4). So rights
can be removed as well as added.
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

### **5.3 Editing in the GUI (Concept)**
Rights are edited where they are shown (PostFix ACL sidebar: click on a chip; Scope ACL
panel: right click on a chip, as a left click filters). The model is the Windows
**“Security” tab** many users know: a principal, one switch per right (in our chip
pictogram `◂` read, `▸` write, `x`, `c`, `d`), inherited rights shown as such
(“inherited from `/Familie/`”), and **“back to inherited”**.
- **Who may edit:** users with `change` on `/.MyOS/ACLs.md` (the current user as for
  enforcement: `MYOS_ACL_USER`, else `$USER`). For everybody else the chips only display.
- **What an edit writes:** because the nearest rule wins, an edit is always one rule for
  one role at exactly this path (`- /path/: read, write`); all rights off writes `none`,
  “back to inherited” removes the line. A person has no rules of their own: editing a
  person changes their role memberships (`# Users`).
- **Groups of a person** (same gesture on a person's chip): one switch per group, and next
  to it what the group may do here (“member · here: read, write”), so one sees where the
  person's rights come from. Memberships hold in the **whole project**, the dialog says
  so. Only the person's line changes (groups already written keep place and spelling);
  without any group the line is removed (no rights, no chip). Groups written for the
  person but unknown at this place (a template folder role of another subproject) stay.
  Adding a person is a separate step (open). Losing one's own `change` right is refused.
- **Template folder roles** (from `## Folder`) have no section at first; the first edit
  creates one with just that explicit entry. The folder rules stay inherited (2.4), so
  nothing else changes for the role, also not in subprojects.
- **Writing:** only the affected line changes (comments, order and spelling elsewhere
  stay); the result is validated (`acl_schema`) before it is written, atomically.
- **Rules follow renames and moves:** renaming or moving an entry inside the project
  rewrites the rules for its old path (and below) to the new one; rights stay, `{Folder}`
  rules are no fixed paths and stay. This needs no `change` right (nothing about the
  rights changes). Security: if rules already wait for the new path, the rename or move is
  refused — rights of the same folder add up, so a prepared `none` could be undone.
- **History instead of audit:** before each GUI edit the previous `ACLs.md` is kept
  (dated copy in `.MyOS/`). That gives undo and a simple “who changed what, when” trail
  without a separate audit system; formal audits are not an MVP goal.

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

### **6.4.1 Mapping to Windows, macOS and Linux**
The MyOS model is no invention of its own: its building blocks match the native ACLs.

| MyOS | Windows (NTFS) | macOS (extended ACLs) | Linux |
|---|---|---|---|
| role | group | group | group (several via POSIX ACLs) |
| person | user | user | user |
| `read`, `write`, `execute` | read, write, execute | read, write, execute | `r`, `w`, `x` (`x` on folders = enter) |
| `delete` | delete | delete | no right of its own (`w` on the parent folder) |
| `change` | change permissions | writesecurity | owner only (not delegable) |
| inheritance (live) | inheritance | copied when created | default ACL, copied when created |
| `none` / fewer rights deeper | disable inheritance there | same | leave the entry out |

**Decision: no “deny”.** Windows and macOS know deny entries, and there a deny wins over
an allow through another group. MyOS deliberately has none: a user's rights are the union
of their roles (Karl in Team and Geschäftsleitung may enter a folder closed to Team). Hence
`none` and “fewer rights deeper” mean **“stop inheriting for this role here”**, which
Windows/macOS express by disabling inheritance at that folder and listing the remaining
entries, and Linux by leaving the entry out. Without deny the model translates into all
three systems, including Linux, which has no deny at all.

**Inheritance:** MyOS evaluates inheritance live (a change on a folder applies below it at
once). Windows propagates changes; macOS and POSIX default ACLs are copied when a file is
created. A mapping plugin therefore writes explicit entries where needed and re-applies
them after changes.

### **6.5 Live‑MyOS on USB (Exploratory)**
Consider a **portable “Live‑MyOS”** image for USB sticks that enforces ACLs at runtime,
independent of the underlying filesystem.

---

## **7. Public API (Draft)**
Public API should live in `core/acl.py` and be used by CLI/GUI:
- `ACLPolicy.from_project(project_root)`
- `ACLPolicy.can_access(role, path, right)`
- `ACLPolicy.roles_for_user(username)`

---

## **8. MVP Scope**
The MVP should demonstrate that **access control is real and intentional**:
- ACLs stored in `.MyOS/ACLs.md`
- Role‑based checks in the MyOS layer (FUSE/CLI)
- Export restricted by role (USB or share)
- Clear API boundaries for future plugins

---

## **9. Plugin‑Ready Architecture (Concept)**
Define a small, stable interface for ACL backends:
- **Read rules** from `.MyOS/ACLs.md`
- **Resolve role → allowed paths**
- **Enforce** rules in MyOS tooling
- **Optionally sync** to OS‑native ACLs

---

## **10. Open Questions**
- Do we need additional rights beyond the MVP set? (e.g., list, birth)
- Do we ever need a dedicated `mychmod` command, or is ACL editing sufficient?
- How should role inheritance be expressed?
- Should template roles auto‑generate users/groups?
- ~~How is auditing handled (who changed ACLs, when)?~~ No audit system in the MVP: GUI
  edits keep the previous `ACLs.md` (see 5.3). Access logging exists in the enforcement
  layer but is off by default.

---

## **11. Summary**
MyOS ACLs are **human‑first** and **portable**:
- **Self‑explanatory** because they mirror project structure
- **Adaptable** via templates
- **Portable** across systems via plugins and exports
- **Enforceable** through MyOS tooling, even without OS ACL support
