#!/usr/bin/env python3
"""
project.py - MyOS project detection and configuration handling
Handles -MyOS/project.me files and project hierarchy detection.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import os
import sys
import logging

from core.config.parser import MarkdownConfigParser

logger = logging.getLogger(__name__)

# System-wide version constant
MYOS_VERSION = os.environ.get("MYOS_VERSION", "MyOS v0.1")




class ProjectConfig:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.myos_dir = self.path / ".MyOS"
        
        # check if /.MyOS/project.md exists
        self.project_md = self.myos_dir / "project.md"
        
        self.templates = []
        self.version = None
        self.metadata = {}
        self.config_data = {}  # WICHTIG: Hier initialisieren!
        
        # Load if project exists
        if self.is_valid():
            self.load()
            logger.debug("ProjectConfig created at %s", self.path)
    
    def _is_project(self) -> bool:
        """Check if this is a valid MyOS project."""
        return self.project_md.exists()
    
    def load(self):
        """Load configuration from project files."""
        # Try .MyOS/ first
        if self.myos_dir.exists():
            self._load_from_myos()
    
    def _load_from_myos(self):
        """Load from .MyOS/ directory."""
        # Load Templates.md
        templates_md = self.myos_dir / "Templates.md"
        if templates_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(templates_md)
                logger.debug("Parsed Templates.md: %s", data)
                
                if data:
                    # Versuche 1: Direkte Liste unter "Templates"
                    if "Templates" in data:
                        templates_data = data["Templates"]
                        if isinstance(templates_data, list):
                            self.templates = templates_data
                        elif isinstance(templates_data, dict):
                            # Versuche "items" zu finden
                            if "items" in templates_data:
                                items = templates_data["items"]
                                if isinstance(items, list):
                                    self.templates = items
                                elif isinstance(items, str):
                                    self.templates = [items]
                    
                    # Versuche 2: Direkte Liste als Wurzel
                    elif isinstance(data, list):
                        self.templates = data
                    
                logger.debug("Loaded templates = %s", self.templates)
            except Exception as e:
                print(f"MyOS ProjectConfig: Error parsing Templates.md: {e}")
                import traceback
                traceback.print_exc()
        
        # Load Manifest.md
        manifest_md = self.myos_dir / "Manifest.md"
        if manifest_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(manifest_md)
                logger.debug("Parsed Manifest.md: %s", data)
                
                if data and "Project" in data:
                    manifest_data = data["Project"]
                    if isinstance(manifest_data, dict):
                        # Konvertiere Schlüssel zu lowercase für konsistenten Zugriff
                        self.metadata = {}
                        for key, value in manifest_data.items():
                            # Speichere als String, nicht als Liste
                            if isinstance(value, list):
                                self.metadata[key.lower()] = ", ".join(value)
                            else:
                                self.metadata[key.lower()] = str(value)
                        
                        # Extrahiere version separat
                        if "version" in self.metadata:
                            self.version = self.metadata.pop("version")
                        
                logger.debug("Loaded metadata = %s, version = %s", self.metadata, self.version)
            except Exception as e:
                print(f"MyOS ProjectConfig: Error parsing Manifest.md: {e}")
                import traceback
                traceback.print_exc()
        
        # Load Config.md (falls existiert)
        self._load_config_data()
    
    def _load_config_data(self):
        """Lädt Config.md Daten."""
        config_md = self.myos_dir / "Config.md"
        if config_md.exists():
            try:
                self.config_data = MarkdownConfigParser.parse_file(config_md)
                logger.debug("Loaded config_data from Config.md")
            except Exception as e:
                print(f"MyOS ProjectConfig: Error parsing Config.md: {e}")
                self.config_data = {}
        else:
            self.config_data = {}
            logger.debug("Config.md does not exist at %s", config_md)
    
    def save(self, templates: Optional[List[str]] = None,
             version: Optional[str] = None) -> bool:
        """
        Save configuration to .MyOS/ directory.
        
        Args:
            templates: List of template names (None = keep current)
            version: MyOS version string (None = keep current)
            
        Returns:
            True if successful
        """
        try:
            logger.debug("save: templates=%s, version=%s", templates, version)
            
            # Update templates if provided
            if templates is not None:
                self.templates = templates if isinstance(templates, list) else [templates]
            
            # Update version if provided
            if version is not None:
                self.version = version
            elif self.version is None:
                self.version = MYOS_VERSION
            
            # Ensure .MyOS/ exists
            self.myos_dir.mkdir(exist_ok=True, parents=True)
            
            # Write project.md (MINIMAL!)
            if not self.project_md.exists():
                self.project_md.write_text("# MyOS Project\n")
            
            # Write Templates.md im NEUEN Format
            templates_md = self.myos_dir / "Templates.md"
            if self.templates:
                # NEUES FORMAT: "# Templates" ohne ## und ohne -
                content = "# Templates\n"
                content += "\n".join(f"{t}" for t in self.templates)
                content += "\n"
                templates_md.write_text(content)
                logger.debug("Wrote %s", templates_md)
            elif templates_md.exists():
                templates_md.unlink()  # Remove if no templates
            
            # Write Manifest.md im NEUEN Format
            manifest_md = self.myos_dir / "Manifest.md"
            # Always write manifest if we have version or metadata
            if self.version is not None or self.metadata:
                # NEUES FORMAT: "# Project" nicht "# MyOS Project"
                content = "# Project\n"
                if self.version:
                    content += f"Version: {self.version}\n"
                for key, value in self.metadata.items():
                    if isinstance(value, list):
                        content += f"{key}: {', '.join(value)}\n"
                    else:
                        content += f"{key}: {value}\n"
                manifest_md.write_text(content)
                logger.debug("Wrote %s", manifest_md)
            elif manifest_md.exists():
                manifest_md.unlink()
                        
            return True
            
        except Exception as e:
            print(f"MyOS ProjectConfig: Error saving config: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_inherit_status(self, section_name: str) -> str:
        """
        Liest den inherit-Status einer Section.
        
        Args:
            section_name: Name der Section (z.B. "Templates")
                
        Returns:
            "fix" | "dynamic" | "not"; fehlend/ungültig = "dynamic"
        """
        if not self.config_data:
            self._load_config_data()
        if section_name not in self.config_data:
            logger.debug("Section '%s' not found in config data, default dynamic", section_name)
            return "dynamic"
        section_data = self.config_data[section_name]
        inherit_values = MarkdownConfigParser.find_inherit(section_data)
        if inherit_values is None:
            return "dynamic"
        if isinstance(inherit_values, list):
            if not inherit_values:
                return "dynamic"
            inherit_value = inherit_values[0].lower()
        else:
            inherit_value = str(inherit_values).lower()
        if inherit_value in ("fix", "dynamic", "not"):
            return inherit_value
        logger.warning("Ungültiger inherit-Wert '%s' in Section '%s', default dynamic", inherit_value, section_name)
        return "dynamic"

    def get_parent_project(self) -> Optional['ProjectConfig']:
        """Findet Parent-Projekt (ein Verzeichnis darüber)."""
        parent_dir = self.path.parent
        if parent_dir == self.path:
            return None
        parent_config = ProjectConfig(parent_dir)
        if parent_config.is_valid():
            return parent_config
        return None

    def get_child_projects(self) -> List['ProjectConfig']:
        """Findet alle direkten Child-Projekte."""
        children = []
        try:
            for item in self.path.iterdir():
                if item.is_dir():
                    child_config = ProjectConfig(item)
                    if child_config.is_valid():
                        children.append(child_config)
        except (PermissionError, OSError) as e:
            logger.debug("Error accessing directory %s: %s", self.path, e)
        return children

    def is_valid(self) -> bool:
        """Check if this is a valid MyOS project."""
        return self._is_project()

    
    # 2. Parsing / Loading    
    def _parse_section_markdown(self, text: str) -> dict:
        items = []
        inherit = None

        for line in text.splitlines():
            line = line.strip()
            if not line:
                break

            if "inherit" in line.lower():
                if ":" in line:
                    inherit = line.split(":", 1)[1].strip()
                continue

            if line.startswith("*"):
                items.append(line.lstrip("* ").strip())
            elif ":" in line:
                items.append(line.strip())

        return {
            "items": items,
            "inherit": inherit or "dynamic"
        }

    def _parse_legacy_config(self, text: str) -> dict:
        sections = {}
        current = None
        buffer = []

        for line in text.splitlines():
            raw = line.strip()

            if raw.startswith("# "):
                name = raw[2:].strip()
                if " " in name:
                    current = None
                    continue
                current = name
                buffer = []
                sections[current] = {"items": [], "inherit": "dynamic"}
                continue

            if not raw or current is None:
                continue

            buffer.append(raw)

            if "inherit" in raw.lower():
                if ":" in raw:
                    sections[current]["inherit"] = raw.split(":", 1)[1].strip()

            elif raw.startswith("*"):
                sections[current]["items"].append(raw.lstrip("* ").strip())
            elif ":" in raw:
                sections[current]["items"].append(raw)

        return sections

    def load_sections(self) -> dict:
        sections = {}

        # Neue Welt: einzelne Dateien
        for md in self.myos_dir.glob("*.md"):
            if md.name.lower() == "project.md":
                continue
            name = md.stem
            sections[name] = self._parse_section_markdown(md.read_text())

        # Alte Welt: Config.md
        config = self.myos_dir / "Config.md"
        if config.exists():
            legacy = self._parse_legacy_config(config.read_text())
            for name, data in legacy.items():
                sections.setdefault(name, data)

        return sections

    @classmethod
    def create(cls, dir_path: Union[str, Path]) -> 'ProjectConfig':
        """
        Create a new project by copying .MyOS/ from parent directory.
        """
        dir_path = Path(dir_path)
        
        # 1. Parent finden (wo .MyOS existiert)
        parent_myos = cls._find_parent_myos(dir_path)
        if not parent_myos:
            raise ValueError(f"No parent .MyOS directory found for {dir_path}")
        
        # 2. .MyOS/ kopieren
        target_myos = dir_path / ".MyOS"
        import shutil
        shutil.copytree(parent_myos, target_myos)
        
        # 3. Dateien mit inherit:"not" löschen
        for config_file in list(target_myos.glob("*.md")):  # Liste erstellen, da wir während Iteration löschen
            if config_file.name == "project.md":
                continue
                
            try:
                # Versuche, Datei zu parsen
                data = MarkdownConfigParser.parse_file(config_file)
                section_name = config_file.stem
                
                if section_name in data:
                    inherit_status = None
                    # Versuche, inherit-Wert zu finden
                    inherit_values = MarkdownConfigParser.find_inherit(data[section_name])
                    
                    if inherit_values:
                        if isinstance(inherit_values, list):
                            if inherit_values:
                                inherit_status = inherit_values[0].lower()
                        else:
                            inherit_status = str(inherit_values).lower()
                        
                        if inherit_status == "not":
                            config_file.unlink()
                            logger.debug("Removed %s (inherit: not)", config_file.name)
            except Exception as e:
                print(f"Warning: Could not process {config_file}: {e}")
                # Datei behalten wenn wir sie nicht parsen können
        
        # 4. Projektobjekt erstellen und zurückgeben
        project = cls(dir_path)
        project._load_config_data()  # Geparste Daten laden
        return project

    @staticmethod
    def _find_parent_myos(dir_path: Path) -> Optional[Path]:
        """Find parent .MyOS directory by walking up the directory tree."""
        current = dir_path.parent
        while current and current != current.parent:  # Bis zum root
            myos_dir = current / ".MyOS"
            if myos_dir.exists():
                return myos_dir
            current = current.parent
        return None

    def propagate_config(self, section_name: str, dry_run: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Propagiert Config-Änderungen an alle Child-Projekte.
        
        Args:
            section_name: Name der Config-Section (z.B. "Templates")
            dry_run: Wenn True, nur zeigen was passieren würde
        
        Returns:
            Dict mit {child_path: success_or_status}
        """
        logger.debug("propagate_config: section=%s path=%s dry_run=%s", section_name, self.path, dry_run)
        results = {}
        
        # 1. Eigene Config laden
        self._load_config_data()
        if section_name not in self.config_data:
            logger.debug("Section '%s' nicht in Config gefunden", section_name)
            return results
        
        # 2. Alle Children finden
        children = self.get_child_projects()
        for child in children:
            child_inherit = child.get_inherit_status(section_name)
            if child_inherit == "fix":
                results[str(child.path)] = "skipped_fix"
                continue
            success = child._update_from_parent(self, section_name, dry_run)
            results[str(child.path)] = success
        return results

    def _update_from_parent(self, parent: 'ProjectConfig', section_name: str, dry_run: bool = False) -> bool:
        """Aktualisiert Config von Parent (interne Methode)."""
        try:
            if not hasattr(parent, 'config_data') or not parent.config_data:
                parent._load_config_data()
            parent_section = parent.config_data.get(section_name)
            if not parent_section:
                return False
            self._load_config_data()
            self.config_data[section_name] = parent_section
            if not dry_run:
                return self._save_config_data()
            return True
        except Exception as e:
            logger.debug("Error updating %s: %s", section_name, e)
            import traceback
            traceback.print_exc()
            return False

    def _save_config_data(self) -> bool:
        """Speichert Config.md Daten."""
        try:
            config_md = self.myos_dir / "Config.md"
            if not self.config_data:
                if config_md.exists():
                    config_md.unlink()
                return True
            
            # Config.md Inhalt generieren
            content = ""
            for section_name, section_data in self.config_data.items():
                content += f"# {section_name}\n"
                
                if isinstance(section_data, list):
                    for item in section_data:
                        if isinstance(item, dict):
                            for key, values in item.items():
                                if isinstance(values, list):
                                    value_str = ", ".join(str(v) for v in values)
                                    content += f"{key}: {value_str}\n"
                        else:
                            content += f"{item}\n"
                elif isinstance(section_data, dict):
                    for key, values in section_data.items():
                        if isinstance(values, list):
                            value_str = ", ".join(str(v) for v in values)
                            content += f"{key}: {value_str}\n"
                        else:
                            content += f"{key}: {values}\n"
                
                content += "\n"
            config_md.write_text(content)
            return True
            
        except Exception as e:
            print(f"Error saving Config.md: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _copy_parent_config(self, parent: 'ProjectConfig'):
        """Kopiert Config vom Parent (beim Erstellen)."""
        try:
            # Parent Config laden
            parent._load_config_data()
            
            # .MyOS/ Verzeichnisstruktur kopieren
            for item in parent.myos_dir.iterdir():
                if item.is_file():
                    # Config.md separat behandeln
                    if item.name == "Config.md":
                        self._process_parent_config(item, parent)
                    else:
                        # Andere Files kopieren
                        import shutil
                        shutil.copy2(item, self.myos_dir / item.name)
                        
        except Exception as e:
            print(f"Warning: Could not copy parent config: {e}")

    def _process_parent_config(self, config_path: Path, parent: 'ProjectConfig'):
        """Verarbeitet parent Config.md mit inherit-Logik."""
        from core.config.parser import MarkdownConfigParser
        
        data = MarkdownConfigParser.parse_file(config_path)
        
        # Filtere Sections mit inherit: fix
        filtered_data = {}
        for section_name, section_data in data.items():
            inherit = MarkdownConfigParser.find_inherit(section_data)
            if inherit and isinstance(inherit, list) and inherit[0].lower() == "fix":
                # Nicht kopieren (lokal fix)
                continue
            filtered_data[section_name] = section_data
        
        # Speichere gefilterte Config
        self.config_data = filtered_data
        self._save_config_data()

    def propagate_command():
        """CLI Command für Config Propagation."""
        import argparse
        
        parser = argparse.ArgumentParser(description="Propagate config changes to child projects")
        parser.add_argument("section", help="Config section name (e.g., Templates)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making changes")
        parser.add_argument("--path", default=".", help="Project path (default: current directory)")
        
        args = parser.parse_args()
        
        config = ProjectConfig(Path(args.path))
        if not config.is_valid():
            print(f"Error: {args.path} is not a valid MyOS project")
            return 1
        
        print(f"Propagating '{args.section}' from {config.path}")
        results = config.propagate_config(args.section, args.dry_run)
        
        # Zusammenfassung
        print(f"\n{'='*50}")
        print(f"Summary: {sum(1 for r in results.values() if r == True)} updated, "
              f"{sum(1 for r in results.values() if r == 'skipped_fix')} skipped (fix), "
              f"{sum(1 for r in results.values() if r == False)} failed")
        
        return 0

    @staticmethod
    def make_project(dir_path: Union[str, Path], template: str = "standard") -> bool:
        """
        Turns an ordinary folder into a project.
        
        Args:
            dir_path: Path to directory
            template: Template name
        
        Returns:
            True if successful, False on error
        """
        try:
            path = Path(dir_path)
            
            # Check if parent directory exists
            if not path.parent.exists():
                print(f"Error: Parent directory does not exist: {path.parent}")
                return False
            
            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
            
            # Create project config (copies .MyOS from parent, template name currently unused)
            config = ProjectConfig.create(path)
            return config.is_valid()
            
        except (OSError, PermissionError) as e:
            # Catch actual filesystem errors
            print(f"Error creating project at {dir_path}: {e}")
            return False
        except Exception as e:
            # Catch any other errors
            print(f"Unexpected error creating project at {dir_path}: {e}")
            return False


class ProjectFinder:
    """
    Finds MyOS projects in the directory hierarchy.
    
    Walks up from a starting directory to find the nearest project.
    """
    
    @staticmethod
    def find_nearest(start_path: Union[str, Path]) -> Optional[Path]:
        """
        Find nearest project root from starting path.
        
        Args:
            start_path: Starting directory path
            
        Returns:
            Path to project root directory, or None if not found
        """
        current = Path(start_path).expanduser().absolute()
        
        while current != current.parent:  # Stop at filesystem root
            # Check for new .MyOS/project.md format first
            if (current / ".MyOS" / "project.md").exists():
                return current
            
            current = current.parent
        
        return None

    @staticmethod
    def is_project(path: Union[str, Path]) -> bool:
        """Check if directory contains a MyOS project."""
        path = Path(path)
        
        # Check for new .MyOS/project.md format
        if (path / ".MyOS" / "project.md").exists():
            return True
        
        return False



if __name__ == "__main__":
    # Smoke test. Run from repo root: python3 -m core.project
    # Full tests: python3 -m pytest core/tests/unit/test_project_config.py -v
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        parent_myos = test_dir.parent / ".MyOS"
        parent_myos.mkdir(exist_ok=True)
        (parent_myos / "project.md").write_text("# MyOS Project\n")
        result = ProjectConfig.make_project(test_dir, template="standard")
        assert result, "make_project should succeed"
        config = ProjectConfig(test_dir)
        assert config.is_valid(), "Project should be valid"
        found = ProjectFinder.find_nearest(test_dir / "subdir")
        assert found == test_dir, f"Should find {test_dir}, got {found}"
        print("✓ Smoke test passed")
