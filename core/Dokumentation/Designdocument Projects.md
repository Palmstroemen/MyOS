# **MyOS Projects Configuration System - Redesign**

## **1. Core Philosophy**
**"Convention over Configuration"** - Like Git, MyOS uses a simple hidden directory (`.MyOS/`) with human-readable Markdown files. No complex manifests, no duplicate bookkeeping.

## **2. Project Definition**
A **MyOS Project** is any directory containing a `.MyOS/` directory **and** a marker file `.MyOS/project.md`. Inside `.MyOS/`, Markdown (`.md`) files are loaded as configuration according to the parser rules.

## **3. Directory Structure**
```
project/
├── .MyOS/                    # MyOS configuration directory
│   ├── project.md            # Required marker file
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
`Config.md` is special: it defines inheritance rules per section (e.g. `inherit: dynamic|fix|not`).

## **5. Configuration Loading Algorithm**

### **5.1 `ProjectConfig` Class (`core/project.py`)**
```python
class ProjectConfig:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.myos_dir = self.path / ".MyOS"
        self.project_md = self.myos_dir / "project.md"
        self.templates = []
        self.version = None
        self.metadata = {}
        self.config_data = {}

    def is_valid(self) -> bool:
        return self.project_md.exists()

    def load(self) -> None:
        # Loads only local project files
        if self.myos_dir.exists():
            self._load_from_myos()

    def _load_from_myos(self) -> None:
        # Templates.md -> self.templates
        # Manifest.md  -> self.metadata + self.version
        # Config.md    -> self.config_data
        pass

    def get_inherit_status(self, section: str) -> str:
        # "fix" | "dynamic" | "not"
        return "dynamic"

    @classmethod
    def create(cls, dir_path: Path) -> "ProjectConfig":
        # Copies parent .MyOS/ and deletes files with inherit:not
        # (inheritance is applied on project creation, not on every load)
        pass
```

**Inheritance model (current):**
- **On creation:** `ProjectConfig.create()` copies the parent `.MyOS/` directory and removes files with `inherit: not`.
- **On changes:** `ProjectConfig.propagate_config(section, dry_run)` pushes a section to child projects, skipping `inherit: fix`.
- **On load:** No automatic parent merge; only local `.MyOS/` is loaded.

### **5.2 Markdown Parser Helper (`core/config/parser.py`)**
```python
class MarkdownConfigParser:
    @staticmethod
    def parse_file(path: Path) -> Dict[str, Any]:
        # Parses sections like:
        #   # Templates
        #   inherit: dynamic
        #   items: Standard, Person
        # and returns a dict structure used by ProjectConfig
        pass

    @staticmethod
    def find_inherit(section_data: Any) -> Optional[List[str]]:
        # Extracts "inherit" from a section (list or dict)
        pass
```

## **6. Template Merging Logic**

### **6.1 Building Embryo Tree**
```python
def build_embryo_tree(template_names: List[str], templates_dir: Path) -> Dict:
    """Build combined embryo tree from multiple templates."""
    combined_tree = {}
    
    for template_name in template_names:
        template_path = templates_dir / template_name
        if not template_path.exists():
            logging.warning(f"Template not found: {template_name}")
            continue
        
        # Load template structure (folders without %)
        template_tree = scan_directory_tree(template_path)
        
        # Convert to embryo names (add % to folder names)
        embryo_tree = convert_to_embryo_tree(template_tree)
        
        # Deep merge with existing tree
        combined_tree = deep_merge_trees(combined_tree, embryo_tree)
    
    return combined_tree
```

### **6.2 Directory Scanning**
```python
def scan_directory_tree(path: Path) -> Dict:
    """Scan directory and return tree structure."""
    tree = {}
    
    for item in path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            tree[item.name] = scan_directory_tree(item)
    
    return tree
```

### **6.3 Embryo Conversion**
```python
def convert_to_embryo_tree(tree: Dict) -> Dict:
    """Convert folder names to embryo names (add % suffix)."""
    embryo_tree = {}
    
    for name, subtree in tree.items():
        embryo_name = f"{name}%"
        embryo_tree[embryo_name] = convert_to_embryo_tree(subtree)
    
    return embryo_tree
```

## **7. FUSE Integration**

### **7.1 Updated Blueprint Class**
```python
class Blueprint(Operations):
    def __init__(self, project_root: Path, templates_dir: Path = "~/.myos/templates"):
        self.project = ProjectConfig(project_root)
        
        if not self.project.is_valid():
            raise ValueError(f"No MyOS project at {project_root}")
        
        self.templates_dir = Path(templates_dir).expanduser()
        self.template_names = self.project.templates
        self.embryo_tree = build_embryo_tree(self.template_names, self.templates_dir)
        
        print(f"[Blueprint] Project: {self.project.path}")
        print(f"[Blueprint] Templates: {self.template_names}")
```

## **8. CLI Commands (Future)**

### **8.1 Project Management**
```bash
# Create new project
myos init /path/to/project

# Add template to project
myos template add Standard /path/to/project

# Show project info
myos status /path/to/project

# List all templates
myos template list
```

### **8.2 Configuration**
```bash
# Edit configuration
myos config edit /path/to/project

# Show inheritance chain
myos config parents /path/to/project

# Propagate template to subprojects
myos template propagate Standard /path/to/project --recursive
```

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
1. **Empty .MyOS/** with `project.md` - Valid project
2. **Missing Templates.md** - Templates list is empty
3. **inherit:not** - File is deleted on `create()`
4. **propagate_config(dry_run)** - Reports affected children
5. **Malformed Markdown** - Parser falls back safely

## **10. Error Handling & Validation**

### **10.1 Graceful Degradation**
- Missing `.MyOS/` or `.MyOS/project.md` → Clear error message
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
