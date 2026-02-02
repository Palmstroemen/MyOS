# **MyOS Blueprint Layer - Design Document**

## **1. Overview**
The `Blueprint` class implements a **FUSE (Filesystem in Userspace)** layer that overlays virtual "embryo folders" (with `%` suffix) on top of real directories. These virtual folders become real ("born") on first write access.

## **2. Core Architecture**

### **2.1 Embryo Concept**
- **Embryo Folder**: Virtual directory displayed with `%` suffix (e.g., `admin%`)
- **Birth**: Automatic creation of real directory when accessed for writing
- **Template-based**: Embryo structure defined by templates in `~/.myos/templates/`

### **2.2 Current File Detection**
```
Old System (to be replaced):
project/
└── .project.cfg          # Single config file
    template: Standard
```

```
New System (planned):
project/
└── .MyOS/               # Configuration directory
    ├── Templates.md     # Markdown template list
    └── Manifest.md      # Project metadata
```

## **3. Blueprint Class API**

### **3.1 Initialization**
```python
class Blueprint(Operations):
    def __init__(self, project_root: Path, templates_dir: Path = "~/.myos/templates"):
        # 1. Find project root (searching for .project.cfg upwards)
        # 2. Load template name from .project.cfg
        # 3. Build embryo tree from template
```

### **3.2 Key Internal Methods**

#### **`_find_project_root()`**
- **Purpose**: Locate nearest project root by searching upwards for `.project.cfg`
- **Algorithm**: 
  1. Start at given path
  2. Move to parent directory
  3. Stop when `.project.cfg` found or filesystem root reached
  4. Throw `ValueError` if no project found

#### **`_load_template_name()`**
- **Purpose**: Extract template name from `.project.cfg`
- **Format**: Looks for `template: <name>` line
- **Fallback**: Returns `"no Template"` if not found

#### **`_load_embryo_tree()`**
- **Purpose**: Recursively scan template directory to build embryo tree
- **Key Logic**: Adds `%` suffix to all directory names
- **Output**: Nested dictionary: `{"admin%": {}, "info%": {}, ...}`

#### **`_embryos_at(rel_path)`**
- **Purpose**: Get list of embryo folders at given relative path
- **Key Features**:
  - Navigates embryo tree using `%`-normalized keys
  - Only returns embryos not yet physically created
  - Returns empty list if path not in embryo tree

#### **`_birth_path(fuse_path)`**
- **Purpose**: Create real directories for all `%`-folders in path
- **Algorithm**:
  1. Split path by `/`
  2. For each part ending with `%`:
     - Remove `%` suffix
     - Create real directory if not exists
     - Print birth notification
  3. Create any remaining non-`%` directories

## **4. Embryo Tree Structure**

### **4.1 Template → Embryo Conversion**
```
Template Filesystem:          Embryo Tree:
~/.myos/templates/Standard/   {
├── admin/                      "admin%": {},
├── info/          →           "info%": {},
└── communication/             "communication%": {
    ├── intern/                  "intern%": {}
    └── extern/                  "extern%": {}
                                }
                              }
```

### **4.2 Tree Navigation**
```python
# Example: Navigate to communication%/intern%
tree = {
    "admin%": {},
    "info%": {},
    "communication%": {
        "intern%": {},
        "extern%": {}
    }
}

# _embryos_at("communication%") 
# → ["intern%", "extern%"]
```

## **5. FUSE Operations**

### **5.1 `getattr(path)` - File/Directory Attributes**
- **Physical files**: Return actual filesystem attributes
- **Embryo folders**: Return read-only directory attributes (mode `0o555`)
- **Non-existent**: Throw `ENOENT` error

### **5.2 `readdir(path)` - Directory Listing**
1. List physical files/directories (excluding hidden `.` files)
2. Add embryo folders at that level (if not yet physical)
3. Filter by write permissions (placeholder - currently all allowed)

### **5.3 `mkdir(path, mode)` - Create Directory**
1. Trigger `_birth_path()` to create embryo directories
2. Create actual directory with given mode

### **5.4 `create(path, mode)` - Create File**
1. Trigger `_birth_path()` for parent directories
2. Open file for writing with given mode

### **5.5 `write(path, data, offset, fh)` - Write to File**
- Delegate to OS write operation
- Birth already happened in `create()`

### **5.6 `release(path, fh)` - Close File**
- Close file handle

## **6. Permission System (Placeholder)**

### **6.1 `_has_write_permission_for_embryo()`**
- **Current**: Always returns `True` (all embryos can be born)
- **Planned**: Check permissions from template or `.access.cfg`

### **6.2 Embryo Attributes**
- Read-only until birth (`0o555`)
- Become writable after birth (inherit parent/actual mode)

## **7. Mount Interface**

### **7.1 Static Method**
```python
@staticmethod
def mount(project_path: Path, foreground: bool = True):
    """Mount Blueprint FUSE layer on project."""
    fuse = Blueprint(project_path)
    FUSE(fuse, str(fuse.project_root), foreground=foreground, allow_other=False)
```

### **7.2 Command Line**
```bash
python localBlueprintLayer.py /path/to/project
```

## **8. Current Limitations**

### **8.1 Single Template Support**
- Only loads one template (`self.template_name`)
- No template merging capability yet

### **8.2 Legacy Configuration**
- Uses `.project.cfg` instead of new `.MyOS/` system
- Simple `template: <name>` format

### **8.3 No Inheritance**
- Project hierarchy inheritance not implemented
- Each project standalone

## **9. Planned Migration to `.MyOS/`**

### **9.1 Changes Required**
1. **`_find_project_root()`**: Search for `.MyOS/` instead of `.project.cfg`
2. **`_load_template_name()`**: Replace with `_load_template_names()` from `.MyOS/Templates.md`
3. **`_load_embryo_tree()`**: Merge multiple templates instead of single
4. **Template Merging**: Implement deep tree merging

### **9.2 New Initialization Flow**
```python
def __init__(self, project_root: Path):
    # NEW: Use MyOSProject class
    self.project = MyOSProject(project_root)
    
    # Get template list (with inheritance)
    self.template_names = self.project.get_templates()
    
    # Build merged embryo tree
    self.embryo_tree = self._load_merged_embryo_tree(self.template_names)
```

### **9.3 Template Merging Algorithm**
```python
def _load_merged_embryo_tree(self, template_names: List[str]) -> Dict:
    """Load and merge multiple template trees."""
    merged_tree = {}
    
    for template_name in template_names:
        template_tree = self._load_single_embryo_tree(template_name)
        merged_tree = self._deep_merge_trees(merged_tree, template_tree)
    
    return merged_tree
```

## **10. Testing Considerations**

### **10.1 Key Test Cases**
1. **Embryo Display**: Virtual folders show with `%` suffix
2. **Birth on Write**: Embryo becomes real directory on access
3. **Template Loading**: Correct tree built from template
4. **Path Navigation**: `_embryos_at()` returns correct embryos
5. **Permission Filtering**: Embryos respect write permissions

### **10.2 Migration Tests**
1. **Backward Compatibility**: Old `.project.cfg` still works
2. **New `.MyOS/`**: New system loads correctly
3. **Template Merging**: Multiple templates combine properly
4. **Inheritance**: Child projects inherit parent templates

## **11. Performance Considerations**

### **11.1 Caching**
- Embryo tree built once at mount time
- Physical existence checked on each `_embryos_at()` call

### **11.2 Tree Navigation**
- O(n) where n = depth of path in tree
- Optimized with direct dictionary lookups

## **12. Error Handling**

### **12.1 Graceful Degradation**
- Missing template → Empty embryo tree (no crash)
- Invalid path in `_embryos_at()` → Empty list
- Missing `.project.cfg` → Clear error message

### **12.2 User Feedback**
- Print statements for debugging (`[BlueprintLayer]`, `[Birth]`)
- FUSE errors for filesystem operations

---

## **Migration Priority**

1. **Phase 1**: Create `MyOSProject` class with `.MyOS/` support
2. **Phase 2**: Update Blueprint to use `MyOSProject`
3. **Phase 3**: Implement template merging in `_load_embryo_tree()`
4. **Phase 4**: Add inheritance support in `MyOSProject`
5. **Phase 5**: Update all tests for new system

This design maintains backward compatibility while enabling the powerful new `.MyOS/` configuration system with template merging and inheritance.