# **MyOS Projects Configuration System - Redesign**

## **1. Core Philosophy**
**"Convention over Configuration"** - Like Git, MyOS uses a simple hidden directory (`.MyOS/`) with human-readable Markdown files. No complex manifests, no duplicate bookkeeping.

## **2. Project Definition**
A **MyOS Project** is any directory containing a `.MyOS/` directory **and** a marker file `.MyOS/Project.md`. Inside `.MyOS/`, Markdown (`.md`) files are loaded as configuration according to the parser rules.

## **3. Directory Structure**
```
project/
├── .MyOS/                    # MyOS configuration directory
│   ├── Project.md            # Required marker file
│   ├── Templates.md          # Template configuration (optional)
│   ├── Manifest.md           # Project metadata (optional)
│   ├── Config.md             # Inheritance rules (optional)
│   ├── ACLs.md               # Access lists (optional)
│   └── any-other.md          # Custom configuration files
├── documents/                # User data
├── images/
└── .git/                     # Optional: Git repository
```

## **4. File Formats (All Markdown)**

### **4.1 Templates.md (Recommended)**
```markdown
# Templates
Standard
Person
Finanzen
```

**Parsing:** Plain lines under `# Templates` are template names.

### **4.2 Manifest.md (Optional)**
```markdown
# Project
Version: MyOS v0.1
Owner: Anna
Created: 2025-01-27
Status: Active
Priority: High
```

**Parsing:** Key-value pairs (`Key: Value`) are parsed. Unknown keys are kept as metadata.

### **4.3 Other .md files**
Any `.md` file in `.MyOS/` is loaded and parsed with the MarkdownConfigParser.  
Sections are defined by `# Section` headers; values are key-value pairs (`key: value`) or lists.

**Two configuration styles (can be mixed):**
1. **Single files** (e.g. `Templates.md`, `Manifest.md`, `ACLs.md`)
2. **A single `Config.md`** with multiple `# Section` blocks

**Equivalence rule:**  
A section in `Config.md` that starts with `# Templates` is equivalent to a file named `Templates.md` with the same content.  

## **5. Configuration Loading Algorithm (Verbally)**

### **5.1 `ProjectConfig` Class (`core/project.py`)**
`ProjectConfig` encapsulates loading and writing project configuration from `.MyOS/`.

- **`is_valid()`**  
  Checks whether `.MyOS/Project.md` exists (marker file).

- **`load()`**  
  Loads **local** `.MyOS/` files only (no automatic parent merge).

- **`_load_from_myos()`**  
  Loads individual files:
  - `Templates.md` → `templates`
  - `Manifest.md` → `metadata` + `version`
  - `Config.md` → `config_data`

- **`get_inherit_status(section)`**  
  Reads the `inherit` rule for a section; default is `dynamic`.

- **`create(path)`**  
  Turns a folder into a project:  
  1) Finds a parent with `.MyOS/`  
  2) Copies the parent configuration  
  3) Removes files with `inherit: not`

- **`propagate_config(section, dry_run)`**  
  Writes a section into child projects (skips `inherit: fix`).

**Override + Inheritance rules:**
- **Single files override `Config.md`** for the same section.
- **Inheritance can be defined in both** single files and `Config.md` sections.
- If a section has **no inherit defined**, the default is **`dynamic`**.

### **5.2 Markdown Parser (`core/config/parser.py`)**
The parser reads `# Section` blocks and converts lines into simple data structures
(key-value pairs, lists), so `ProjectConfig` can extract `inherit`, `items`, and similar fields.

## **6. Template Merging Logic**
The template system combines multiple template folders into a single **embryo tree**:
1. Scan each template directory (folders only, ignore hidden items).
2. Convert folder names into embryo names by appending `%`.
3. Deep‑merge all template trees into one combined structure.
4. Missing templates are skipped with a warning.

## **7. FUSE Integration**
The FUSE blueprint layer:
- Validates the project with `ProjectConfig.is_valid()`.
- Reads `ProjectConfig.templates` and builds the embryo tree.
- Exposes the merged structure as a virtual filesystem view.

## **8. CLI Commands (Future)**
Planned CLI capabilities:
- Create and initialize projects
- Add/remove templates
- Show project status and templates
- Edit config and show inheritance chain
- Propagate config/template changes to subprojects

## **9. Testing Strategy**

### **9.1 Test Structure**
```
test_lab/
├── .MyOS/
│   └── Templates.md      # Global: Standard
└── plate/
    ├── .MyOS/
    │   └── Templates.md  # All projects: Standard
    ├── Haus/
    │   ├── .MyOS/
    │   │   └── Templates.md  # Standard, Person
    │   └── Dach/
    │       ├── .MyOS/
    │       │   └── Templates.md  # Standard, Person, Finanzen
    │       └── Webseite/
    │           └── .MyOS/
    │               └── Templates.md  # Standard
    └── Garten/
        └── .MyOS/
            └── Templates.md  # Person
```

### **9.2 Key Test Cases**
1. **Empty .MyOS/** with `Project.md` - Valid project
2. **Missing Templates.md** - Templates list is empty
3. **inherit:not** - File is deleted on `create()`
4. **propagate_config(dry_run)** - Reports affected children
5. **Malformed Markdown** - Parser falls back safely

## **10. Error Handling & Validation**

### **10.1 Graceful Degradation**
- Missing `.MyOS/` or `.MyOS/Project.md` → Clear error message
- Missing template → Warning log, skip that template
- Invalid Markdown → Fallback to default parsing

### **10.2 Validation**
- Template names must exist in templates directory
- Check for Markdown syntax errors (basic)
- Detect circular inheritance in hierarchy

## **11. Migration Path**

### **11.1 From Old System**
```python
# Old: .project.cfg
# New: .MyOS/Templates.md

# Migration script:
def migrate_old_project(project_path):
    old_cfg = project_path / ".project.cfg"
    new_dir = project_path / ".MyOS"
    
    if old_cfg.exists():
        new_dir.mkdir(exist_ok=True)
        content = old_cfg.read_text()
        # Convert to Templates.md format
        new_content = convert_to_markdown(content)
        (new_dir / "Templates.md").write_text(new_content)
        old_cfg.unlink()
```

---

## **Implementation Priority**

1. **Phase 1**: New `ProjectConfig` class with `.MyOS/` detection
2. **Phase 2**: Markdown parser for configuration files
3. **Phase 3**: Template inheritance and merging
4. **Phase 4**: Update Blueprint to use new system
5. **Phase 5**: Update all tests
6. **Phase 6**: CLI tools for project management

This design provides a **simple, extensible, and intuitive** configuration system that follows Unix/Git conventions while maintaining MyOS's human-readable philosophy.
