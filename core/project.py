#!/usr/bin/env python3
"""
project.py - MyOS project detection and configuration handling.
Handles .MyOS/Project.md and project hierarchy detection.
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


def _coerce_search_dir(start_path: Union[str, Path]) -> Path:
    target = Path(start_path).expanduser().resolve()
    return target.parent if target.is_file() else target


def _read_inherit_value_from_config_file(config_path: Path) -> Optional[str]:
    """
    Read inherit value from a <Section>.md config file.
    Returns normalized inherit value or None when missing/unreadable.
    """
    try:
        data = MarkdownConfigParser.parse_file(config_path)
    except Exception:
        return None
    section_name = config_path.stem
    section_data = None
    if isinstance(data, dict):
        section_data = data.get(section_name, data)
    else:
        section_data = data
    inherit_values = MarkdownConfigParser.find_inherit(section_data)
    if inherit_values is None:
        return None
    if isinstance(inherit_values, list):
        if not inherit_values:
            return None
        value = str(inherit_values[0]).strip().lower()
    else:
        value = str(inherit_values).strip().lower()
    if value in {"fix", "dynamic", "not"}:
        return value
    return None


def find_config_in_parents(
    start_path: Union[str, Path],
    config_name: str,
    *,
    require_project_marker: bool = True,
    honor_inherit_not: bool = True,
) -> Optional[Path]:
    """
    Find nearest `.MyOS/<config_name>` by walking up from start_path.
    """
    search_dir = _coerce_search_dir(start_path)
    for candidate in [search_dir, *search_dir.parents]:
        if require_project_marker and not (candidate / ".MyOS" / "Project.md").exists():
            continue
        config_path = candidate / ".MyOS" / str(config_name)
        if not (config_path.exists() and config_path.is_file()):
            continue
        if honor_inherit_not:
            inherit_value = _read_inherit_value_from_config_file(config_path)
            if inherit_value == "not":
                return None
        return config_path
    return None


def find_next_parent_config(
    current_project: Union[str, Path],
    config_name: str,
    *,
    require_project_marker: bool = True,
    honor_inherit_not: bool = True,
) -> Optional[Path]:
    """
    Find nearest parent config above the current project directory.
    """
    project_dir = _coerce_search_dir(current_project)
    parent = project_dir.parent
    if parent == project_dir:
        return None
    return find_config_in_parents(
        parent,
        config_name,
        require_project_marker=require_project_marker,
        honor_inherit_not=honor_inherit_not,
    )




class ProjectConfig:
    """Load, write, and manage project configuration stored in .MyOS/."""

    def __init__(self, path: Path):
        """Initialize a ProjectConfig for the given path."""
        self.path = Path(path)
        self.myos_dir = self.path / ".MyOS"
        
        # Marker file that defines a project root
        self.project_md = self.myos_dir / "Project.md"
        
        self.templates = []
        self.version = None
        self.metadata = {}
        self.config_data = {}
        
        # Load config if this is a valid project
        if self.is_valid():
            self.load()
            logger.debug("ProjectConfig created at %s", self.path)
    
    def _is_project(self) -> bool:
        """Return True when the project marker file exists."""
        return self.project_md.exists()
    
    def load(self):
        """Load configuration from local .MyOS/ files."""
        if self.myos_dir.exists():
            self._load_from_myos()
    
    def _load_from_myos(self):
        """Load Templates.md, Manifest.md, and Config.md from .MyOS/."""
        # Templates.md -> self.templates
        templates_md = self.myos_dir / "Templates.md"
        if templates_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(templates_md)
                logger.debug("Parsed Templates.md: %s", data)
                
                if data:
                    # Case 1: list under "Templates"
                    if "Templates" in data:
                        templates_data = data["Templates"]
                        if isinstance(templates_data, list):
                            self.templates = templates_data
                        elif isinstance(templates_data, dict):
                            # Look for "items" in a section dict
                            if "items" in templates_data:
                                items = templates_data["items"]
                                if isinstance(items, list):
                                    self.templates = items
                                elif isinstance(items, str):
                                    self.templates = [items]
                    
                    # Case 2: root list
                    elif isinstance(data, list):
                        self.templates = data
                    
                logger.debug("Loaded templates = %s", self.templates)
            except Exception as e:
                logger.exception("Error parsing Templates.md: %s", e)
        
        # Manifest.md -> self.metadata, self.version
        manifest_md = self.myos_dir / "Manifest.md"
        if manifest_md.exists():
            try:
                data = MarkdownConfigParser.parse_file(manifest_md)
                logger.debug("Parsed Manifest.md: %s", data)
                
                if data and "Project" in data:
                    manifest_data = data["Project"]
                    if isinstance(manifest_data, dict):
                        # Normalize keys for consistent access
                        self.metadata = {}
                        for key, value in manifest_data.items():
                            # Store values as strings for easier use
                            if isinstance(value, list):
                                self.metadata[key.lower()] = ", ".join(value)
                            else:
                                self.metadata[key.lower()] = str(value)
                        
                        # Extract version separately if present
                        if "version" in self.metadata:
                            self.version = self.metadata.pop("version")
                        
                logger.debug("Loaded metadata = %s, version = %s", self.metadata, self.version)
            except Exception as e:
                logger.exception("Error parsing Manifest.md: %s", e)
        
        # Config.md -> self.config_data
        self._load_config_data()
    
    def _load_config_data(self):
        """Load Config.md into self.config_data."""
        config_md = self.myos_dir / "Config.md"
        if config_md.exists():
            try:
                self.config_data = MarkdownConfigParser.parse_file(config_md)
                logger.debug("Loaded config_data from Config.md")
            except Exception as e:
                logger.exception("Error parsing Config.md: %s", e)
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
            
            # Ensure Project.md exists as a minimal marker file
            if not self.project_md.exists():
                self.project_md.write_text("# MyOS Project\n")
            
            # Write Templates.md in the current format
            templates_md = self.myos_dir / "Templates.md"
            if self.templates:
                # Format: "# Templates" followed by one template per line
                content = "# Templates\n"
                content += "\n".join(f"{t}" for t in self.templates)
                content += "\n"
                templates_md.write_text(content)
                logger.debug("Wrote %s", templates_md)
            elif templates_md.exists():
                templates_md.unlink()  # Remove if no templates
            
            # Write Manifest.md in the current format
            manifest_md = self.myos_dir / "Manifest.md"
            # Always write manifest if we have version or metadata
            if self.version is not None or self.metadata:
                # Format: "# Project" followed by key/value lines
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
            logger.exception("Error saving config: %s", e)
            return False
    
    def get_inherit_status(self, section_name: str) -> str:
        """
        Read the inherit status for a section.
        
        Args:
            section_name: Section name (e.g., "Templates")
                
        Returns:
            "fix" | "dynamic" | "not"; missing/invalid -> "dynamic"
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
        logger.warning("Invalid inherit value '%s' in section '%s', defaulting to dynamic", inherit_value, section_name)
        return "dynamic"

    def _get_local_section_data(self, section_name: str) -> Tuple[Any, bool]:
        """
        Return local section data from <Section>.md first, then Config.md.
        """
        section = str(section_name or "").strip()
        if not section:
            return None, False

        section_file = self.myos_dir / f"{section}.md"
        if section_file.exists():
            try:
                parsed = MarkdownConfigParser.parse_file(section_file)
            except Exception:
                parsed = None
            if isinstance(parsed, dict):
                if section in parsed:
                    return parsed.get(section), True
                return parsed, True
            if parsed is not None:
                return parsed, True

        if not self.config_data:
            self._load_config_data()
        if section in self.config_data:
            return self.config_data.get(section), True
        return None, False

    @staticmethod
    def _inherit_from_section_data(section_data: Any) -> str:
        inherit_values = MarkdownConfigParser.find_inherit(section_data)
        if inherit_values is None:
            return "dynamic"
        if isinstance(inherit_values, list):
            if not inherit_values:
                return "dynamic"
            inherit_value = str(inherit_values[0]).strip().lower()
        else:
            inherit_value = str(inherit_values).strip().lower()
        if inherit_value in ("fix", "dynamic", "not"):
            return inherit_value
        return "dynamic"

    def resolve_effective_section(self, section_name: str) -> Any:
        """
        Resolve a section by walking project ancestors.
        Nearest local section wins. Missing inherit defaults to dynamic.
        """
        section = str(section_name or "").strip()
        if not section:
            return None

        current = self.path
        while True:
            marker = current / ".MyOS" / "Project.md"
            if marker.exists():
                myos_dir = current / ".MyOS"
                local_data = None
                found = False

                section_file = myos_dir / f"{section}.md"
                if section_file.exists():
                    try:
                        parsed = MarkdownConfigParser.parse_file(section_file)
                    except Exception:
                        parsed = None
                    if isinstance(parsed, dict):
                        if section in parsed:
                            local_data = parsed.get(section)
                        else:
                            local_data = parsed
                        found = True
                    elif parsed is not None:
                        local_data = parsed
                        found = True

                if not found:
                    config_md = myos_dir / "Config.md"
                    if config_md.exists():
                        try:
                            parsed_config = MarkdownConfigParser.parse_file(config_md)
                        except Exception:
                            parsed_config = {}
                        if isinstance(parsed_config, dict) and section in parsed_config:
                            local_data = parsed_config.get(section)
                            found = True

                if found:
                    inherit_state = self._inherit_from_section_data(local_data)
                    if inherit_state == "not":
                        return None
                    return local_data
            if current == current.parent:
                break
            current = current.parent
        return None

    @staticmethod
    def _extract_templates_from_section(section_data: Any) -> List[str]:
        if section_data is None:
            return []
        values: List[str] = []
        if isinstance(section_data, list):
            for item in section_data:
                if isinstance(item, dict):
                    items = item.get("items")
                    if isinstance(items, list):
                        values.extend(str(v).strip() for v in items if str(v).strip())
                    elif isinstance(items, str) and items.strip():
                        values.append(items.strip())
                else:
                    text = str(item).strip()
                    if text:
                        values.append(text)
        elif isinstance(section_data, dict):
            items = section_data.get("items")
            if isinstance(items, list):
                values.extend(str(v).strip() for v in items if str(v).strip())
            elif isinstance(items, str) and items.strip():
                values.append(items.strip())
            elif "Templates" in section_data:
                inner = section_data.get("Templates")
                if isinstance(inner, list):
                    values.extend(str(v).strip() for v in inner if str(v).strip())
                elif isinstance(inner, str) and inner.strip():
                    values.append(inner.strip())
        elif isinstance(section_data, str):
            text = section_data.strip()
            if text:
                values.append(text)
        # Keep insertion order while removing duplicates.
        unique: List[str] = []
        seen = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            unique.append(value)
        return unique

    def get_effective_templates(self) -> List[str]:
        """
        Resolve effective Templates section from nearest project ancestor.
        """
        section_data = self.resolve_effective_section("Templates")
        return self._extract_templates_from_section(section_data)

    def get_parent_project(self) -> Optional['ProjectConfig']:
        """Find the nearest parent project (one directory above)."""
        parent_dir = self.path.parent
        if parent_dir == self.path:
            return None
        parent_config = ProjectConfig(parent_dir)
        if parent_config.is_valid():
            return parent_config
        return None

    def get_child_projects(self) -> List['ProjectConfig']:
        """Return direct child projects under this path."""
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
        """Return True when this path is a valid MyOS project."""
        return self._is_project()

    
    def _parse_section_markdown(self, text: str) -> dict:
        """Parse a single-file section into items + inherit."""
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
        """Parse legacy Config.md content into sections."""
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
        """Load all sections from single files and Config.md (legacy style)."""
        sections = {}

        # Single-file sections
        for md in self.myos_dir.glob("*.md"):
            if md.name.lower() == "project.md":
                continue
            name = md.stem
            sections[name] = self._parse_section_markdown(md.read_text())

        # Config.md sections
        config = self.myos_dir / "Config.md"
        if config.exists():
            legacy = self._parse_legacy_config(config.read_text())
            for name, data in legacy.items():
                sections.setdefault(name, data)

        return sections

    @classmethod
    def create(cls, dir_path: Union[str, Path]) -> 'ProjectConfig':
        """
        Create a new project marker without copying dynamic config files.
        """
        dir_path = Path(dir_path)
        
        # Find nearest parent with .MyOS
        parent_myos = cls._find_parent_myos(dir_path)
        if not parent_myos:
            raise ValueError(f"No parent .MyOS directory found for {dir_path}")
        # Ensure target directory exists and initialize minimal .MyOS marker.
        dir_path.mkdir(parents=True, exist_ok=True)
        target_myos = dir_path / ".MyOS"
        target_myos.mkdir(parents=True, exist_ok=True)
        project_marker = target_myos / "Project.md"
        if not project_marker.exists():
            project_marker.write_text("# MyOS Project\n")

        # Return fresh ProjectConfig.
        project = cls(dir_path)
        project._load_config_data()
        return project

    @staticmethod
    def _find_parent_myos(dir_path: Path) -> Optional[Path]:
        """Find parent .MyOS directory by walking up the directory tree."""
        current = dir_path.parent
        while current and current != current.parent:  # Stop at filesystem root
            myos_dir = current / ".MyOS"
            if myos_dir.exists():
                return myos_dir
            current = current.parent
        return None

    def propagate_config(self, section_name: str, dry_run: bool = False) -> Dict[str, Union[bool, str]]:
        """
        Materialize a config section to child projects on demand.
        
        Args:
            section_name: Config section name (e.g., "Templates")
            dry_run: When True, only report what would change
        
        Returns:
            Dict mapping {child_path: success_or_status}
        """
        logger.debug("propagate_config: section=%s path=%s dry_run=%s", section_name, self.path, dry_run)
        results = {}
        
        # Load own config data
        self._load_config_data()
        if section_name not in self.config_data:
            logger.debug("Section '%s' not found in config", section_name)
            return results
        
        # Recursively update child projects.
        # Important: descendants inherit from their direct parent, not always from root.
        def _propagate_from(parent_cfg: 'ProjectConfig') -> None:
            children = parent_cfg.get_child_projects()
            for child in children:
                child_inherit = child.get_inherit_status(section_name)
                child_key = str(child.path)
                if child_inherit == "not":
                    results[child_key] = "skipped_not"
                    # inherit:not stops propagation in this branch.
                    continue
                if child_inherit == "fix":
                    results[child_key] = "skipped_fix"
                    # Keep propagating to descendants from this fixed child.
                    _propagate_from(child)
                    continue
                success = child._update_from_parent(parent_cfg, section_name, dry_run)
                results[child_key] = success
                _propagate_from(child)

        _propagate_from(self)
        return results

    def _update_from_parent(self, parent: 'ProjectConfig', section_name: str, dry_run: bool = False) -> bool:
        """Update a section from a parent ProjectConfig (internal)."""
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
            logger.exception("Error updating %s: %s", section_name, e)
            return False

    def _save_config_data(self) -> bool:
        """Write current config_data back to Config.md."""
        try:
            config_md = self.myos_dir / "Config.md"
            if not self.config_data:
                if config_md.exists():
                    config_md.unlink()
                return True
            
            # Build Config.md content
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
            logger.exception("Error saving Config.md: %s", e)
            return False

    def propagate_command():
        """CLI entry point to propagate config sections."""
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
        
        # Summary
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
            
            # Create project config (copies .MyOS from parent)
            config = ProjectConfig.create(path)
            return config.is_valid()
            
        except (OSError, PermissionError) as e:
            # Catch actual filesystem errors
            logger.error("Error creating project at %s: %s", dir_path, e)
            return False
        except Exception as e:
            # Catch any other errors
            logger.exception("Unexpected error creating project at %s: %s", dir_path, e)
            return False


def notify_config_changed(changed_file: Union[str, Path], dry_run: bool = False) -> Dict[str, Any]:
    """
    Core-level entry point for config propagation after a file change.

    - Only reacts to files inside a `.MyOS/` directory.
    - `.MyOS/<Section>.md` triggers propagation for `<Section>`.
    - `.MyOS/Config.md` triggers propagation for all sections currently present.
    """
    changed_path = Path(changed_file).expanduser().resolve()
    results: Dict[str, Any] = {"ok": False, "sections": {}, "reason": ""}

    if not changed_path.exists():
        results["reason"] = "missing_file"
        return results

    parent = changed_path.parent
    if parent.name != ".MyOS":
        results["reason"] = "outside_myos"
        return results

    project_dir = parent.parent
    config = ProjectConfig(project_dir)
    if not config.is_valid():
        results["reason"] = "invalid_project"
        return results

    section_names: List[str] = []
    if changed_path.name == "Project.md":
        results["reason"] = "project_marker_only"
        return results
    elif changed_path.name == "Config.md":
        config._load_config_data()
        section_names = sorted(config.config_data.keys()) if config.config_data else []
    elif changed_path.suffix.lower() == ".md":
        section_names = [changed_path.stem]
    else:
        results["reason"] = "unsupported_file"
        return results

    if not section_names:
        results["reason"] = "no_sections"
        return results

    sections_result: Dict[str, Any] = {}
    for section in section_names:
        sections_result[section] = config.propagate_config(section, dry_run=dry_run)

    results["ok"] = True
    results["sections"] = sections_result
    return results


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
            # Check for .MyOS/Project.md marker
            if (current / ".MyOS" / "Project.md").exists():
                return current
            
            current = current.parent
        
        return None

    @staticmethod
    def is_project(path: Union[str, Path]) -> bool:
        """Check if directory contains a MyOS project."""
        path = Path(path)
        
        # Check for .MyOS/Project.md marker
        if (path / ".MyOS" / "Project.md").exists():
            return True
        
        return False


def find_projects(start_path: Union[str, Path]) -> List[ProjectConfig]:
    """
    Find project configs from the given path upwards.
    Order is most specific first.
    """
    start_path = Path(start_path).expanduser().resolve()
    if start_path.is_file():
        start_path = start_path.parent

    results: List[ProjectConfig] = []
    current = start_path
    while True:
        candidate = ProjectConfig(current)
        if candidate.is_valid():
            results.append(candidate)
        if current == current.parent:
            break
        current = current.parent
    return results


def resolve_cwp(start_path: Union[str, Path]) -> Optional[ProjectConfig]:
    """Resolve current working project for a given path."""
    found = ProjectFinder.find_nearest(start_path)
    if not found:
        return None
    return ProjectConfig(found)



if __name__ == "__main__":
    # Smoke test. Run from repo root: python3 -m core.project
    # Full tests: python3 -m pytest core/tests/unit/test_project_config.py -v
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()
        parent_myos = test_dir.parent / ".MyOS"
        parent_myos.mkdir(exist_ok=True)
        (parent_myos / "Project.md").write_text("# MyOS Project\n")
        result = ProjectConfig.make_project(test_dir, template="standard")
        assert result, "make_project should succeed"
        config = ProjectConfig(test_dir)
        assert config.is_valid(), "Project should be valid"
        found = ProjectFinder.find_nearest(test_dir / "subdir")
        assert found == test_dir, f"Should find {test_dir}, got {found}"
        print("✓ Smoke test passed")
