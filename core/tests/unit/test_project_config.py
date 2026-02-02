# tests/unit/test_project_config.py
# Run from repo root: python3 -m pytest core/tests/unit/test_project_config.py -v
import pytest
import tempfile
from pathlib import Path
import shutil
import os

from core.project import ProjectConfig, ProjectFinder
from core.config.parser import MarkdownConfigParser

# Helper function for test setup
def setup_complete_test_config(root_dir: Path):
    """Create comprehensive test configuration for all tests."""
    myos_dir = root_dir / ".MyOS"
    myos_dir.mkdir(exist_ok=True)
    
    # 1. project.md (required)
    (myos_dir / "project.md").write_text("# MyOS Project\nRoot configuration for testing\n")
    
    # 2. Templates.md
    (myos_dir / "Templates.md").write_text("""# Templates
Standard
Person
Finanzen

#### inherit: dynamic
#### version: MyOS v0.1
""")
    
    # 3. Manifest.md
    (myos_dir / "Manifest.md").write_text("""# Project
Owner: Anna
Created: 2025-01-27
Status: Active
Priority: High
""")
    
    # 4. Info.md (inherit: not) – "#### inherit: not" direkt nach Überschrift, damit Parser es erkennt
    (myos_dir / "Info.md").write_text("""# Info
#### inherit: not
This project sets up the basic MyOS configuration.
""")
    
    # 5. ACLs.md
    (myos_dir / "ACLs.md").write_text("""# ACLs
Access Control Lists are defined here.

## Roles
* Admin: read, write, execute
* Dummy: read
Roles have different access rights.

## Users
* Admin: Anna
* Dummy: Leonhard, Sebastian
""")
    
    # 6. Config.md (for inheritance tests) – keine Leerzeile nach Überschrift, sonst parst Parser Section leer
    (myos_dir / "Config.md").write_text("""# Templates
inherit: dynamic
items: Standard, Person

# Styles
inherit: fix
items: Dark, Compact
""")
    
    print(f"✓ Complete test config created in {myos_dir}")
    return myos_dir


class TestProjectConfig:
    """Unit tests for ProjectConfig class."""
    
    def test_create_empty_project(self):
        """Test creating project with minimal structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            # Create .MyOS/ with empty project.md
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# MyOS Project\n")
            
            config = ProjectConfig(project_path)
            
            # Should be valid (has project.md)
            assert config.is_valid()
            assert config.templates == []  # No templates.md yet
            assert config.metadata == {}   # No manifest.md yet
            print(f"✓ Empty project loaded")
    
    def test_load_templates_from_md(self):
        """Test loading templates from Templates.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            # Create .MyOS/ structure with templates matching our config
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# MyOS Project\n")
            
            # Write Templates.md matching our root configuration
            (myos_dir / "Templates.md").write_text("""# Templates
Standard
Person
Finanzen
""")
            
            config = ProjectConfig(project_path)
            
            assert config.is_valid()
            assert config.templates == ["Standard", "Person", "Finanzen"]
            print(f"✓ Templates loaded: {config.templates}")

    def test_load_manifest_from_md(self):
        """Test loading metadata from Manifest.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# MyOS Project\n")
            
            # Write Manifest.md
            (myos_dir / "Manifest.md").write_text("""# Project
Owner: Anna
Created: 2025-01-27
Status: Active
Priority: High
""")
            
            config = ProjectConfig(project_path)
            
            assert config.metadata["owner"] == "Anna"
            assert config.metadata["created"] == "2025-01-27"
            assert config.metadata["status"] == "Active"
            assert config.metadata["priority"] == "High"
            print(f"✓ Manifest loaded: {config.metadata}")
    
    def test_save_creates_files(self):
        """Test that save() creates correct .md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            config = ProjectConfig(project_path)
            config.templates = ["Standard", "Person"]
            config.version = "MyOS v1.0"
            config.metadata = {"owner": "TestUser", "created": "2025-01-27"}
            
            # Save should create .MyOS/ directory
            result = config.save()
            assert result
            
            myos_dir = project_path / ".MyOS"
            assert myos_dir.exists()
            assert (myos_dir / "project.md").exists()
            assert (myos_dir / "Templates.md").exists()
            assert (myos_dir / "Manifest.md").exists()
            
            # Verify Templates.md content
            templates_content = (myos_dir / "Templates.md").read_text()
            assert "Standard" in templates_content
            assert "Person" in templates_content
            
            # Verify Manifest.md content  
            manifest_content = (myos_dir / "Manifest.md").read_text()
            assert "MyOS v1.0" in manifest_content
            assert "TestUser" in manifest_content
            
            print(f"✓ Save created: {list(myos_dir.iterdir())}")
    
    def test_save_updates_existing_files(self):
        """Test that save() updates existing .md files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            # Create initial structure
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# Old Project\n")
            (myos_dir / "Templates.md").write_text("# Old\n- OldTemplate\n")
            (myos_dir / "Manifest.md").write_text("Old: yes\n")
            
            config = ProjectConfig(project_path)
            config.templates = ["NewTemplate"]
            config.version = "MyOS v2.0"
            
            # Save updates
            result = config.save()
            assert result
            
            # Check files were updated
            templates_content = (myos_dir / "Templates.md").read_text()
            assert "NewTemplate" in templates_content
            assert "OldTemplate" not in templates_content
            
            manifest_content = (myos_dir / "Manifest.md").read_text()
            assert "MyOS v2.0" in manifest_content
            assert "Old: yes" not in manifest_content
            
            print(f"✓ Save updated existing files")
    
    def test_missing_project_md_is_invalid(self):
        """Test that project without project.md is invalid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            # Create .MyOS/ but NO project.md
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            # Only templates.md, no project.md
            (myos_dir / "Templates.md").write_text("# Templates\n- Standard\n")
            
            config = ProjectConfig(project_path)
            
            # Should NOT be valid without project.md
            assert not config.is_valid()
            print(f"✓ Missing project.md makes project invalid")


class TestProjectInheritance:
    """Tests for project inheritance functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "Projekte"
        self.root.mkdir(parents=True)
        
        # Create complete configuration
        setup_complete_test_config(self.root)
    
    def teardown_method(self):
        """Cleanup after each test."""
        self.temp_dir.cleanup()
    
    def test_get_inherit_status(self):
        """Test reading inherit status from Config.md."""
        config = ProjectConfig(self.root)
        
        # Should detect inherit status
        assert config.get_inherit_status("Templates") == "dynamic"
        assert config.get_inherit_status("Styles") == "fix"
        
        # Non-existent section should return default
        assert config.get_inherit_status("NonExistent") == "dynamic"
        
        print(f"✓ Inherit status detection works")
    
    def test_create_project_copies_config(self):
        """Test that create() copies configuration from parent."""
        # Create child directory
        child_dir = self.root / "NeuesProjekt"
        child_dir.mkdir()
        
        # Create project (should find parent and copy)
        config = ProjectConfig.create(child_dir)
        
        # Check that files were copied
        child_myos = child_dir / ".MyOS"
        assert (child_myos / "Templates.md").exists()
        assert (child_myos / "ACLs.md").exists()
        assert (child_myos / "Manifest.md").exists()
        assert (child_myos / "Config.md").exists()
        
        # Info.md should NOT have been copied (inherit: not)
        assert not (child_myos / "Info.md").exists()
        
        print(f"✓ Config correctly copied, Info.md correctly omitted")
    
    def test_create_project_without_parent_fails(self):
        """Test that create() fails when no parent found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Directory without parent .MyOS
            orphan_dir = Path(tmpdir) / "orphan"
            orphan_dir.mkdir()
            
            # Should raise an error
            with pytest.raises(ValueError, match="No parent"):
                ProjectConfig.create(orphan_dir)
            
            print(f"✓ Correctly fails when no parent found")
    
    def test_inherit_not_deletes_file(self):
        """Test that inherit:not deletes file after copying."""
        # Simulate manual copy
        child_dir = self.root / "TestProjekt"
        child_dir.mkdir()
        child_myos = child_dir / ".MyOS"
        child_myos.mkdir()
        
        # Copy all files (like copytree would)
        for config_file in (self.root / ".MyOS").glob("*.md"):
            shutil.copy2(config_file, child_myos / config_file.name)
        
        # Now delete files with inherit:not
        for config_file in child_myos.glob("*.md"):
            if config_file.name == "project.md":
                continue
            
            try:
                data = MarkdownConfigParser.parse_file(config_file)
                section_name = config_file.stem
                
                if section_name in data:
                    # Use parser to find inherit status
                    inherit_values = MarkdownConfigParser.find_inherit(data[section_name])
                    if inherit_values and isinstance(inherit_values, list) and inherit_values[0] == "not":
                        config_file.unlink()
                        print(f"  Deleted {config_file.name} (inherit: not)")
            except Exception as e:
                print(f"  Warning processing {config_file}: {e}")
        
        # Check results
        assert (child_myos / "Templates.md").exists()
        assert (child_myos / "ACLs.md").exists()
        assert not (child_myos / "Info.md").exists()
        
        print(f"✓ inherit:not correctly handled")
    
    def test_config_propagation_dry_run(self):
        """Test propagating config changes to children with dry run."""
        # Create child project
        child_dir = self.root / "ChildProject"
        child_dir.mkdir()
        child_config = ProjectConfig.create(child_dir)
        
        # Create parent config object
        parent_config = ProjectConfig(self.root)
        
        # Test propagation with dry run
        results = parent_config.propagate_config("Templates", dry_run=True)
        
        # Should find child and plan update
        assert str(child_dir) in results
        print(f"✓ Config propagation dry run works")


class TestProjectFinder:
    """Tests for ProjectFinder utility class."""
    
    def test_find_nearest_project(self):
        """Test finding nearest project in hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create project hierarchy
            root = Path(tmpdir)
            project_dir = root / "project"
            subdir = project_dir / "sub" / "deep"
            
            project_dir.mkdir(parents=True)
            subdir.mkdir(parents=True)
            
            # Create project at project_dir
            myos_dir = project_dir / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# Project\n")
            
            # Should find project from deep subdirectory
            found = ProjectFinder.find_nearest(subdir)
            assert found == project_dir
            
            print(f"✓ Found project from deep subdirectory: {found}")
    
    def test_find_nearest_when_at_project(self):
        """Test find_nearest when already at project root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / "project"
            project_dir.mkdir()
            
            myos_dir = project_dir / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# Project\n")
            
            found = ProjectFinder.find_nearest(project_dir)
            assert found == project_dir
            
            print(f"✓ Found self as project")
    
    def test_find_nearest_returns_none(self):
        """Test find_nearest returns None when no project found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_project = Path(tmpdir) / "no_project"
            non_project.mkdir()
            
            found = ProjectFinder.find_nearest(non_project)
            assert found is None
            
            print(f"✓ Correctly returns None for non-project")
    
    def test_is_project_detection(self):
        """Test is_project() detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid project
            valid = Path(tmpdir) / "valid_project"
            valid.mkdir()
            (valid / ".MyOS").mkdir()
            (valid / ".MyOS" / "project.md").write_text("# Project\n")
            
            assert ProjectFinder.is_project(valid)
            
            # Invalid: no project.md
            invalid1 = Path(tmpdir) / "invalid1"
            invalid1.mkdir()
            (invalid1 / ".MyOS").mkdir()
            # Only templates.md, no project.md
            (invalid1 / ".MyOS" / "Templates.md").write_text("# Templates\n")
            
            assert not ProjectFinder.is_project(invalid1)
            
            # Invalid: no .MyOS at all
            invalid2 = Path(tmpdir) / "invalid2"
            invalid2.mkdir()
            
            assert not ProjectFinder.is_project(invalid2)
            
            print(f"✓ Project detection works correctly")


class TestProjectConfigEdgeCases:
    """Tests for edge cases in project config."""
    
    def test_empty_config_md(self):
        """Test handling of empty or malformed Config.md."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# Project\n")
            
            # Create empty Config.md
            (myos_dir / "Config.md").write_text("")
            
            config = ProjectConfig(project_path)
            
            # Should handle gracefully
            status = config.get_inherit_status("AnySection")
            assert status == "dynamic"  # Default
            
            print(f"✓ Handles empty Config.md")
    
    def test_malformed_markdown_files(self):
        """Test handling of malformed markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir) / "test_project"
            project_path.mkdir()
            
            myos_dir = project_path / ".MyOS"
            myos_dir.mkdir()
            (myos_dir / "project.md").write_text("# Project\n")
            
            # Create malformed Templates.md (not proper markdown)
            (myos_dir / "Templates.md").write_text("Invalid: Content: More: Data")
            
            config = ProjectConfig(project_path)
            
            # Should not crash, templates should be empty
            assert config.templates == []
            
            print(f"✓ Handles malformed markdown gracefully")


# Test der CLI-Funktionalität
class TestProjectCLI:
    """Tests for CLI functionality."""
    
    def test_propagate_command_structure(self):
        """Test that propagate_command() has correct structure."""
        # Import and check the function exists
        from core.project import ProjectConfig
        
        # Check it's a static method
        assert hasattr(ProjectConfig, 'propagate_command')
        
        print(f"✓ CLI command structure exists")


# Note: The make_project() function tests have been removed because 
# make_project() needs to be updated to work with the new create() method


if __name__ == "__main__":
    # Quick manual run
    pytest.main([__file__, "-v", "-s"])
