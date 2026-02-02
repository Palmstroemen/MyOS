#!/usr/bin/env python3
"""
MyOS VLP - View/Lens/Plate Architektur
Minimal implementiert für erste Tests
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os

@dataclass
class PlateManager:
    """Physischer Storage (PLATE)"""
    root: Path = field(default_factory=lambda: Path.home() / "myos_plates")
    
        def __init__(self, plate: PlateManager, templates_dir = None):
        """
        Core engine that combines Plate, Templates, and ProjectConfig.
        This will later become the FUSE layer logic.
        """
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
        try:
            for item in self.path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Rekursiv scannen
                    subtemplate = LensTemplate("", item)
                    tree[item.name] = list(subtemplate._scan_template().keys())
        except FileNotFoundError:
            pass
        return tree
    
    def ghosts_at(self, current_path: str = "") -> List[str]:
        """
        Gibt Ghosts für aktuellen Pfad zurück.
        
        Args:
            current_path: Aktueller Pfad (z.B. "infos%", "infos%/intern%")
        
        Returns:
            Liste von Ghost-Namen mit % Suffix
        """
        # Normalisiere Pfad
        if current_path == "/" or not current_path:
            current_path = ""
        else:
            current_path = current_path.strip('/')
        
        # Starte bei Root des Baums
        node = self.ghost_tree
        
        # Navigiere durch Pfadsegmente
        if current_path:
            parts = current_path.split('/')
            for part in parts:
                part = part.rstrip('%')  # % entfernen
                if part in node:
                    node = {k: [] for k in node[part]}
                else:
                    return []  # Pfad existiert nicht im Template
        
        # Gib Ghosts zurück
        return [f"{name}%" for name in node.keys()]

# In myos_vlp.py ergänzen:

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
                    continue  # Skip empty lines and comments
                
                # Check if line contains key-value pair (with colon)
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
                    # Handle version line like "MyOS v0.1" (without colon)
                    self.version = line
                elif '=' in line:
                    # Alternative format: key=value
                    key, value = line.split('=', 1)
                    self.metadata[key.strip()] = value.strip()
        except FileNotFoundError:
            pass  # File doesn't exist yet
    
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
        
        # Add metadata
        for key, value in self.metadata.items():
            lines.append(f"{key}: {value}")
        
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text('\n'.join(lines) + '\n')
    
    def get(self, key: str, default: str = None) -> str:
        """Get value from metadata"""
        return self.metadata.get(key, default)
    
    def set(self, key: str, value: str):
        """Set value in metadata"""
        self.metadata[key] = value
    
    def __str__(self) -> str:
        """String representation for debugging"""
        return f"ProjectConfig(template={self.template}, version={self.version}, metadata={self.metadata})"


@dataclass
class LensEngine:
    """
    Core engine that combines Plate, Templates, and ProjectConfig.
    This will later become the FUSE layer logic.
    """
    plate: PlateManager
    templates_dir: Optional[Path] = None  # Custom templates directory
    templates: Dict[str, LensTemplate] = field(default_factory=dict)
    
    def __post_init__(self):
        self._load_templates()
    
    def _load_templates(self):
        """Load all templates from templates directory"""
        if self.templates_dir:
            templates_dir = self.templates_dir
        else:
            # Default location
            templates_dir = Path.home() / ".myos" / "lenses"
        
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        for item in templates_dir.iterdir():
            if item.is_dir():
                try:
                    self.templates[item.name] = LensTemplate(item.name, item)
                except Exception as e:
                    print(f"Warning: Could not load template '{item.name}': {e}")

    def is_project(self, project_name: str) -> bool:
        """Check if directory is a MyOS project"""
        project_path = self.plate.physical_path(project_name)
        config_file = project_path / ".project.cfg"
        return config_file.exists()
    
    def get_project_config(self, project_name: str) -> Optional[ProjectConfig]:
        """Load ProjectConfig for a project"""
        if not self.is_project(project_name):
            return None
        
        project_path = self.plate.physical_path(project_name)
        config_file = project_path / ".project.cfg"
        return ProjectConfig(config_file)
    
    def get_project_template(self, project_name: str) -> Optional[LensTemplate]:
        """Get template for a project"""
        config = self.get_project_config(project_name)
        if not config or not config.template:
            return None
        
        return self.templates.get(config.template)
    
    def list_project(self, project_name: str, path: str = "") -> List[str]:
        """
        List contents of a project at given path.
        Returns combined list of physical entries and ghosts.
        """
        # Get physical entries
        physical_path = self.plate.physical_path(f"{project_name}/{path}")
        entries = []
        
        if physical_path.exists():
            for item in os.listdir(physical_path):
                # Filter out hidden files (starting with .)
                if not item.startswith('.'):
                    entries.append(item)
        
        # Get ghosts from template
        template = self.get_project_template(project_name)
        if template:
            ghosts = template.ghosts_at(path)
            
            # Filter out already materialized ghosts
            for ghost in ghosts:
                ghost_name = ghost.rstrip('%')
                if ghost_name not in entries:
                    entries.append(ghost)
        
        return sorted(entries)
    
    def materialize(self, project_name: str, virtual_path: str) -> Path:
        """
        Materialize a ghost path within a project.
        
        Args:
            project_name: Name of the project
            virtual_path: Virtual path (may contain % for ghosts)
        
        Returns:
            Physical path that was created
        """
        # Clean path (remove %)
        clean_path = virtual_path.replace('%', '')
        
        # Full path in plate
        full_virtual_path = f"{project_name}/{clean_path}"
        
        return self.plate.materialize(full_virtual_path)
    
    def create_project(self, project_name: str, template_name: str = "standard") -> bool:
        """
        Create a new MyOS project.
        
        Returns:
            True if successful, False otherwise
        """
        # Check if template exists
        if template_name not in self.templates:
            print(f"Error: Template '{template_name}' not found")
            return False
        
        # Create project directory
        project_path = self.plate.physical_path(project_name)
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create .project.cfg
        config = ProjectConfig(project_path / ".project.cfg")
        config.save(template=template_name)
        
        return True



# TODO: View, etc.




# --- Hilfsfunktionen für Tests ---
def create_standard_template(path: Path) -> LensTemplate:
    """Erstellt Standard-Template für Tests"""
    template_dir = path / "template_standard"
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Struktur
    (template_dir / "infos").mkdir()
    (template_dir / "infos" / "intern").mkdir()
    (template_dir / "infos" / "web").mkdir()
    (template_dir / "team").mkdir()
    (template_dir / "admin").mkdir()
    
    # Konfiguration
    (template_dir / ".project.cfg").write_text("MyOS v0.1\ntemplate: standard\n")
    
    return LensTemplate("standard", template_dir)

if __name__ == "__main__":
    print("MyOS VLP Module")
    print("Use: python3 -m pytest tests/test_vlp.py -v")
