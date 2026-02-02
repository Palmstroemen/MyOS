# **MyOS Blueprint Layer - Design Document**

## **1. Overview**
The `Blueprint` class implements a **FUSE (Filesystem in Userspace)** layer that overlays virtual
"embryo folders" (no `%` suffix) on top of real directories. These virtual folders become real
("born") on first write access.

## **2. Core Architecture**

### **2.1 Embryo Concept**
- **Embryo Folder**: Virtual directory shown with its **plain name** (e.g., `admin`)
- **Birth**: Automatic creation of a real directory when accessed for writing
- **Template-based**: Embryo structure defined by template directories

### **2.2 Project Detection**
A project is valid if `.MyOS/Project.md` exists. `ProjectConfig` loads templates from
`.MyOS/Templates.md`.

### **2.3 Template Sources**
Templates are loaded from:
- `MYOS_TEMPLATES_DIR` (if set), otherwise
- `<project_root>/Templates`

## **3. Blueprint Responsibilities**

### **3.1 Initialization**
`Blueprint.__init__()`:
1. Finds the project root by searching for `.MyOS/Project.md`
2. Loads `ProjectConfig` for that project
3. Reads template names from `ProjectConfig.templates`
4. Builds the embryo tree from all templates
5. Initializes `BirthClinic` for safe materialization

### **3.2 Birth Process**
When a path contains embryos, `BirthClinic.give_birth()`:
- Finds the template source for the embryo path
- Validates template safety (no symlinks)
- Copies the template into the project (without symlinks)

## **4. Embryo Tree Structure**
The embryo tree is a nested dictionary of folder names:

```
Templates/Standard/
├── admin/
├── info/
└── communication/
    ├── intern/
    └── extern/

Embryo tree:
{
  "admin": {},
  "info": {},
  "communication": {
    "intern": {},
    "extern": {}
  }
}
```

## **5. Security Measures**
- Block path traversal (`..`) in embryo paths
- Block absolute and hidden paths
- Validate template names before using them
- Reject symlinks inside template directories
- Copy templates without following symlinks
- Warn when symlinks exist in the project path

## **6. FUSE Operations (Summary)**
- **`getattr()`**: Returns real attributes or read‑only attributes for embryos
- **`readdir()`**: Lists physical entries first, then embryos not yet born
- **`mkdir()` / `create()`**: Triggers birth if embryos appear in the path
- **`write()` / `release()`**: Delegate to OS file operations

## **7. Permission System (Placeholder)**
`_has_write_permission_for_embryo()` currently returns `True`.
This will later integrate ACL checks.

## **8. Mount Interface**
`Blueprint.mount(project_path, foreground=True)` mounts FUSE on the project root.

CLI usage:
```bash
python localBlueprintLayer.py /path/to/project
```

## **9. Testing Considerations**
Key scenarios:
1. Embryos are shown virtually before birth
2. Birth happens on first write
3. Template trees merge correctly
4. Path traversal is blocked
5. Symlinks in templates are rejected

## **10. Limitations / Next Steps**
- ACL integration is still pending
- Template merging is currently simple (deep merge)
- Logging could replace some `print()` statements in the future