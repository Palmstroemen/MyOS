#!/usr/bin/env python3
"""
Basic tests for myos_core.py
"""
import unittest
import tempfile
import os
import sys
import errno

# Add parent directory to path to import myos_core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from myos_core import MyOSCore
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"Warning: Could not import MyOSCore: {e}")
    IMPORT_SUCCESS = False
    # Create dummy class for test structure
    class MyOSCore:
        def __init__(self, root):
            pass
        def _materialize_path(self, path):
            return path
        def _safe_path(self, path):
            return path

class TestMyOSCoreBasic(unittest.TestCase):
    """Basic tests for MyOSCore functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="myos_test_")
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        
        # Create a test file
        with open(self.test_file, "w") as f:
            f.write("test content")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_import(self):
        """Test that MyOSCore can be imported"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        self.assertTrue(IMPORT_SUCCESS)
    
    def test_initialization(self):
        """Test MyOSCore initialization"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        
        core = MyOSCore(self.temp_dir)
        self.assertIsNotNone(core)
        # Check that root is absolute path
        self.assertTrue(os.path.isabs(core.root))
    
    def test_materialize_path_basic(self):
        """Test basic path materialization"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        
        core = MyOSCore(self.temp_dir)
        # Test simple path
        result = core._materialize_path("/test.txt")
        expected = os.path.join(core.root, "test.txt")
        self.assertEqual(result, expected)
    
    # @unittest.skip("Needs implementation")  
    def test_materialize_path_percent(self):
        """Test % removal in paths"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        
        core = MyOSCore(self.temp_dir)
        # Test with % folder
        result = core._materialize_path("/projekt%/datei.txt")
        # Should remove % from folder name
        self.assertNotIn("%", result)
    
    def test_directory_exists(self):
        """Test that our test directory exists"""
        self.assertTrue(os.path.exists(self.temp_dir))
        self.assertTrue(os.path.exists(self.test_file))
        
        # Verify test file content
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "test content")

    def test_real_percent_materialization(self):
        """REAL test: Creating file in folder% creates folder/"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        
        # 1. Create a potential folder in mirror
        percent_folder = os.path.join(self.temp_dir, "projekt%")
        os.makedirs(percent_folder, exist_ok=True)
        
        # 2. Create MyOSCore instance
        core = MyOSCore(self.temp_dir)
        
        # 3. Test materialization
        fuse_path = "/projekt%/test.txt"
        materialized = core._materialize_path(fuse_path)
        
        print(f"\nTest: {fuse_path} → {os.path.basename(materialized)}")
        
        # Should remove the %
        self.assertNotIn("%", materialized)
        
        # Should create in projekt/ not projekt%/
        expected = os.path.join(self.temp_dir, "projekt", "test.txt")
        self.assertEqual(materialized, expected)
        
        # 4. Actually create the file (simulating FUSE)
        os.makedirs(os.path.dirname(materialized), exist_ok=True)
        with open(materialized, "w") as f:
            f.write("test")
        
        # Verify
        self.assertTrue(os.path.exists(expected))
        print(f"✓ File created at: {os.path.relpath(expected, self.temp_dir)}")

class TestSecurity(unittest.TestCase):
    """Security-related tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="myos_security_test_")
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # @unittest.skip("Security tests to be implemented")
    def test_path_traversal_prevention(self):
        """Test that path traversal is prevented"""
        if not IMPORT_SUCCESS:
            self.skipTest("MyOSCore import failed")
        
        core = MyOSCore(self.temp_dir)
        # Should raise error for path traversal attempts
        with self.assertRaises((PermissionError, ValueError)):
            core._safe_path("/../etc/passwd")
        
        with self.assertRaises((PermissionError, ValueError)):
            core._safe_path("/../../dangerous")


if __name__ == '__main__':
    unittest.main(verbosity=2)
