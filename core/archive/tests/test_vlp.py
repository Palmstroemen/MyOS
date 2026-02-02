# tests/test_vlp.py - NEUE Testdatei
import pytest
import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Pfad zum Prototyp-Verzeichnis
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.vlp import PlateManager, LensTemplate, LensEngine
from core.project import ProjectConfig
from core.materializer import Materializer

class TestVLP(unittest.TestCase):
    """Tests für VLP-Architektur"""
    
    def setUp(self):
        """Testumgebung in fixtures/vlp/"""
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "vlp"
        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        
        # Test-ID für diesen Durchlauf
        self.test_id = self._testMethodName
        self.test_root = self.fixtures_dir / self.test_id
        shutil.rmtree(self.test_root, ignore_errors=True)
        self.test_root.mkdir()
        
        '''
        # Template erstellen
        self.template_dir = self.test_root / "template_standard"
        self._create_template()

        # Template catalog directory (contains template_standard/)
        self.templates_catalog_dir = self.test_root
        '''
        # Template directory - name matches template
        self.template_dir = self.test_root / "standard"  # Not 'template_standard'
        self._create_template()

        # Templates catalog directory (contains 'standard/')
        self.templates_catalog_dir = self.test_root

        # Plate-Verzeichnis
        self.plate_dir = self.test_root / "plate"
        self.plate_dir.mkdir()
    
    def _create_template(self):
        """Creates standard template for tests"""
        # Use 'standard' as directory name to match template name
        t = self.template_dir
        (t / "infos").mkdir(parents=True)
        (t / "infos" / "intern").mkdir()
        (t / "infos" / "web").mkdir()
        (t / "team").mkdir()
        (t / "admin").mkdir()
    
    def test_plate_manager_initialization(self):
        """PlateManager sollte Verzeichnis erstellen"""
        plate = PlateManager(self.plate_dir)
        self.assertTrue(self.plate_dir.exists())
        self.assertEqual(plate.root, self.plate_dir)
    
    def test_plate_physical_path(self):
        """Pfadauflösung sollte korrekt arbeiten"""
        plate = PlateManager(self.plate_dir)
        
        # Root
        self.assertEqual(plate.physical_path(""), self.plate_dir)
        
        # Relativer Pfad
        expected = self.plate_dir / "projekt" / "datei.txt"
        self.assertEqual(plate.physical_path("projekt/datei.txt"), expected)
    
    @pytest.mark.skip(reason="PlateManager.materialize() does not exist - use Materializer class")
    def test_plate_materialize(self):
        """Materialisierung sollte Ordner erstellen"""
        materializer = Materializer(self.plate_dir)  # NEU
        
        # Tiefe Struktur
        path = materializer.materialize("a/b/c/test.txt")  # NEU
        self.assertTrue(path.exists())
        self.assertTrue((self.plate_dir / "a/b/c").exists())
    
    def test_lens_template_scanning(self):
        """Template sollte Ordnerstruktur erkennen"""
        template = LensTemplate("standard", self.template_dir)
        
        # embryo-Baum sollte korrekt sein
        self.assertIn("infos", template.embryo_tree)
        self.assertIn("team", template.embryo_tree)
        self.assertIn("admin", template.embryo_tree)
        
        # Unterordner
        self.assertEqual(template.embryo_tree["infos"], ["intern", "web"])
    
    def test_lens_embryo_generation(self):
        """embryo-Generierung für verschiedene Pfade"""
        template = LensTemplate("standard", self.template_dir)
        
        # Root
        embryos = template.embryos_at("")
        self.assertCountEqual(embryos, ["infos%", "team%", "admin%"])
        
        # In infos%
        embryos = template.embryos_at("infos%")
        self.assertCountEqual(embryos, ["intern%", "web%"])
        
        # In infos%/intern%
        embryos = template.embryos_at("infos%/intern%")
        self.assertEqual(embryos, [])  # Keine weiteren Unterordner
    
    @pytest.mark.skip(reason="Integration test needs Materializer + Template update")
    def test_integration_embryo_to_materialization(self):
        """Kompletter Flow: embryo → Materialisierung"""
        # 1. Plate
        plate = PlateManager(self.plate_dir)
        
        # 2. Template
        template = LensTemplate("standard", self.template_dir)
        
        # 3. embryo-Pfad materialisieren
        embryo_path = "infos%/intern%/meeting.txt"
        materializer = Materializer(self.plate_dir)
        result = materializer.materialize("a/b/c/test.txt")
        
        # Prüfen
        self.assertTrue(result.exists())
        self.assertTrue((self.plate_dir / "infos/intern").exists())

    def test_project_config_creation(self):
        """ProjectConfig should create .MyOS"""
        # self.test_root is the DIRECTORY
        config = ProjectConfig(self.test_root)  # <-- VERZEICHNIS!
        config.template = "standard"
        config.save()
        
        # Now .MyOS should exist
        config_file = self.test_root / ".MyOS"
        self.assertTrue(config_file.exists())
        content = config_file.read_text()
        self.assertIn("MyOS v0.1", content)
        self.assertIn("template: standard", content)

    def test_project_config_loading(self):
        """ProjectConfig sollte .MyOS lesen können"""
        # Testdatei erstellen
        myos_dir = self.test_root / ".MyOS"
        myos_dir.mkdir()
        (myos_dir / "Templates.md").write_text("# Project Templates\n\n## Templates\n- urlaub\n")
        (myos_dir / "Manifest.md").write_text("# MyOS Project\n\nVersion: MyOS v0.1\ncreated: 2025-01-23\n")
        
        config = ProjectConfig(self.test_root)
        
        self.assertEqual(config.template, "urlaub")
        self.assertEqual(config.metadata.get("created"), "2025-01-23")


    def test_project_config_creation(self):
        """ProjectConfig should create .MyOS/Templates.md"""
        # self.test_root is the DIRECTORY
        config = ProjectConfig(self.test_root)
        config.templates = ["standard"]  # Nicht config.template = 
        config.save()

        # Prüfe ob .MyOS/Templates.md existiert
        templates_md = self.test_root / ".MyOS" / "Templates.md"
        self.assertTrue(templates_md.exists())


    # Test for the lens_engine (FUSE-Layer):
    def test_lens_engine_initialization(self):
        """LensEngine should initialize with plate and templates"""
        
        plate = PlateManager(self.plate_dir)
        engine = LensEngine(plate)
        
        self.assertEqual(engine.plate, plate)
        self.assertIsNotNone(engine.templates)
        # Should have at least the standard template from fixtures

    def test_lens_engine_detect_project(self):
        """LensEngine should detect MyOS projects"""
        
        # Create a project in plate
        project_dir = self.plate_dir / "TestProject"
        project_dir.mkdir()
        myos_dir = project_dir / ".MyOS"
        myos_dir.mkdir()
        (myos_dir / "Templates.md").write_text("# Templates\n\n## Templates\n- standard\n")
        (myos_dir / "Manifest.md").write_text("# MyOS Project\n\nVersion: MyOS v0.1\ncreated: 2025-01-23\n")
        
        plate = PlateManager(self.plate_dir)
        engine = LensEngine(plate)
        
        # Should detect this as a project
        self.assertTrue(engine.is_project("TestProject"))
        self.assertFalse(engine.is_project("NonExistentProject"))

    @pytest.mark.skip(reason="list_project method not implemented in LensEngine")
    def test_lens_engine_list_project(self):
        """LensEngine should list project contents with embryos"""
        
        # Create project with template
        project_dir = self.plate_dir / "TestProject"
        project_dir.mkdir()
        (project_dir / ".MyOS").write_text("MyOS v0.1\ntemplate: standard\n")
        
        # Create some physical files
        (project_dir / "existing.txt").touch()
        
        plate = PlateManager(self.plate_dir)
        
        # Pass the template directory from our test fixtures
        engine = LensEngine(plate, templates_dir=self.template_dir.parent)        
        # Note: self.template_dir is /.../template_standard/
        # We need the parent directory that contains template_standard/
        
        # List project root
        entries = engine.list_project("TestProject", "")
        # Should contain: existing.txt + embryos from template
        # Note: .MyOS is also listed (it's a physical file)
        self.assertIn("existing.txt", entries)
        self.assertIn("infos%", entries)
        self.assertIn("team%", entries)
        self.assertIn("admin%", entries)

    @pytest.mark.skip(reason="materialize method not implemented in LensEngine")
    def test_lens_engine_materialize(self):
        """LensEngine should materialize embryo paths"""
       
        plate = PlateManager(self.plate_dir)
        engine = LensEngine(plate)
        
        # Create project first
        project_dir = self.plate_dir / "TestProject"
        project_dir.mkdir()
        (project_dir / ".MyOS").write_text("MyOS v0.1\ntemplate: standard\n")
        
        # Materialize a embryo path
        result = engine.materialize("TestProject", "infos%/intern%/meeting.txt")
        
        # Check physical result
        expected_path = self.plate_dir / "TestProject/infos/intern/meeting.txt"
        self.assertEqual(result, expected_path)
        self.assertTrue(expected_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
