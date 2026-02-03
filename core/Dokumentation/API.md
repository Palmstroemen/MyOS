# **MyOS API Overview (Draft)**

## **1. Purpose**
This document provides a high-level overview of the public Python APIs used by CLI, GUI, and plugins. It is an onboarding map for developers.

---

## **2. Core Modules**
### **2.1 Projects**
**Module:** `core/project.py`  
**Public API (examples):**
- `ProjectConfig(path)`
- `ProjectConfig.is_valid()`
- `ProjectConfig.get_parent_project()`
- `ProjectConfig.get_child_projects()`
- `ProjectFinder.find_nearest(start_path)`

### **2.2 ACLs**
**Module:** `core/acl.py`  
**Public API (examples):**
- `ACLPolicy.from_project(project_root)`
- `ACLPolicy.can_access(role, path, right)`

### **2.3 Exporter**
**Module:** `core/exporter.py`  
**Public API (examples):**
- `export_subtree(source_path, output_dir, package_name=None, zip_output=False)`

### **2.4 Importer**
**Module:** `core/importer.py`  
**Public API (examples):**
- `import_package(package_path, target_root=None, mode="adopt", conflict="merge")`

### **2.5 Perspectives**
**Module:** `core/perspective.py`  
**Public API (examples):**
- `PerspectiveConfig.from_file(path)`
- `PerspectiveConfig.from_data(data)`

---

## **3. CLI as API Consumer**
The CLI should be a thin wrapper around these public APIs. It should not reimplement logic that already exists in the core modules.

---

## **4. Notes**
- This overview lists public entry points only.
- Each design document contains module-specific details and rules.
