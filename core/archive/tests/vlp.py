#!/usr/bin/env python3
"""
MyOS VLP - View/Lens/Plate Architecture
Clean version with fixed imports.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import os

# ========== PLATE ==========
@dataclass
class PlateManager:
    """Physical storage (PLATE)"""
    
    def __init__(self, root=None):
        """Initialize with root path (str, Path, or None for default)"""
        if root is None:
            self.root = Path.home() / "myos_plates"
        elif isinstance(root, str):
            self.root = Path(root)
        elif isinstance(root, Path):
            self.root = root
        else:
            raise ValueError(f"Invalid root type: {type(root)}")
        
        self.root = self.root.expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
    
    def physical_path(self, virtual_path: str = "") -> Path:
        """Convert virtual path to physical path"""
        if not virtual_path or virtual_path == ".":
            return self.root
        
        if virtual_path.startswith("/"):
            virtual_path = virtual_path[1:]
        
        return self.root / virtual_path
    
    def exists(self, virtual_path: str = "") -> bool:
        """Check if path exists"""
        return self.physical_path(virtual_path).exists()
    '''
    def materialize(self, virtual_path: str) -> Path:
        """Create physical structure"""
        path = self.physical_path(virtual_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix:
            if not path.exists():
                path.touch()
        
        return path
    '''
    def list_dir(self, virtual_path: str = "") -> List[str]:
        """List physical directory"""
        path = self.physical_path(virtual_path)
        if path.exists():
            return os.listdir(path)
        return []

# ========== TEMPLATE ==========
@dataclass
class LensTemplate:
    """Template definition (part of LENS)"""
    name: str
    path: Path
    embryo_tree: Dict[str, List[str]] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.embryo_tree:
            self.embryo_tree = self._scan_template()
    
    def _scan_template(self) -> Dict[str, List[str]]:
        """Scan template directory recursively"""
        tree = {}
        try:
            for item in self.path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    subtemplate = LensTemplate("", item)
                    tree[item.name] = list(subtemplate._scan_template().keys())
        except FileNotFoundError:
            pass
        return tree
    
    def embryos_at(self, current_path: str = "") -> List[str]:
        """Get embryos for current path"""
        if not current_path or current_path == "/":
            current_path = ""
        else:
            current_path = current_path.strip('/')
        
        node = self.embryo_tree
        
        if current_path:
            parts = current_path.split('/')
            for part in parts:
                part = part.rstrip('%')
                if part in node:
                    node = {k: [] for k in node[part]}
                else:
                    return []
        
        return [f"{name}%" for name in node.keys()]

'''
# ========== PROJECT CONFIG ==========
@dataclass
class ProjectConfig:
    """Reads and writes .project.cfg files"""
    path: Path
    template: Optional[str] = None
    version: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.path.exists():
            self.load()
    
    def load(self):
        """Load configuration from file"""
        try:
            lines = self.path.read_text().strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key == "template":
                        self.template = value
                    elif key == "version":
                        self.version = value
                    else:
                        self.metadata[key] = value
                elif line.startswith("MyOS"):
                    self.version = line
        except FileNotFoundError:
            pass
    
    def save(self, template: str = None, version: str = "MyOS v0.1"):
        """Save configuration to file"""
        if template:
            self.template = template
        if version:
            self.version = version
        
        lines = []
        if self.version:
            lines.append(self.version)
        if self.template:
            lines.append(f"template: {self.template}")
        
        for key, value in self.metadata.items():
            lines.append(f"{key}: {value}")
        
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text('\n'.join(lines) + '\n')
'''
# ========== LENS ENGINE ==========
@dataclass
class LensEngine:
    """Core engine that combines Plate, Templates, and ProjectConfig"""
    
    def __init__(self, plate: PlateManager, templates_dir=None):
        self.plate = plate
        
        if templates_dir is None:
            self.templates_dir = Path.home() / ".myos" / "lenses"
        elif isinstance(templates_dir, str):
            self.templates_dir = Path(templates_dir)
        elif isinstance(templates_dir, Path):
            self.templates_dir = templates_dir
        else:
            raise ValueError(f"Invalid templates_dir type: {type(templates_dir)}")
        
        self.templates = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from templates directory"""
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        for item in self.templates_dir.iterdir():
            if item.is_dir():
                try:
                    self.templates[item.name] = LensTemplate(item.name, item)
                except Exception as e:
                    print(f"Warning: Could not load template '{item.name}': {e}")
    
    def is_project(self, project_name: str) -> bool:
        """Check if directory is a MyOS project"""
        project_path = self.plate.physical_path(project_name)
        config_file = project_path / ".MyOS"
        return config_file.exists()

# ========== HELPER ==========
def create_standard_template(path: Path) -> LensTemplate:
    """Create standard template for tests"""
    template_dir = path / "standard"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    (template_dir / "infos").mkdir()
    (template_dir / "infos" / "intern").mkdir()
    (template_dir / "infos" / "web").mkdir()
    (template_dir / "team").mkdir()
    (template_dir / "admin").mkdir()
    
    return LensTemplate("standard", template_dir)

if __name__ == "__main__":
    print("MyOS VLP Module - Clean Version")
    print("Use: python3 -m pytest tests/test_vlp.py -v")
