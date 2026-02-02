# tests/test_parser.py
import unittest
import sys
import os
from typing import List, Optional, Any
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config.parser import MarkdownConfigParser

class TestMarkdownConfigParser(unittest.TestCase):
    def test_basic_list(self):
        """Einfache Liste ohne Leerzeile"""
        content = """# Templates
Standard
Website"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_basic_list: {result}")
        
        self.assertEqual(result["Templates"], ["Standard", "Website"])
    
    def test_list_with_blankline(self):
        """Liste mit Leerzeile dazwischen"""
        content = """# Templates
Standard

Website"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_list_with_blankline: {result}")
        
        self.assertEqual(result["Templates"], ["Standard"])  # Website ignoriert!
    
    def test_key_value_pair(self):
        """Key-Value Paar"""
        content = """# Config
    #### inherit: dynamic
    #### version: 2.0"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_key_value_pair: {result}")
        
        # Sollte sein: {'Config': [{'inherit': ['dynamic']}, {'version': ['2.0']}]}
        inherit = MarkdownConfigParser.find_inherit(result["Config"])
        self.assertEqual(inherit, ["dynamic"])
  
    def test_comma_separated(self):
        """Komma-separierte Liste"""
        content = """# Tags
red, yellow, green"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_comma_separated: {result}")
        
        self.assertEqual(result["Tags"], ["red", "yellow", "green"])
    
    def test_mixed_items(self):
        """Gemischte Items"""
        content = """# ACLs
Admin: Alfred
Member: Bertha, Christian
Guest"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_mixed_items: {result}")
        
        # Sollte sein: [{"Admin": ["Alfred"]}, {"Member": ["Bertha", "Christian"]}, "Guest"]
        self.assertEqual(len(result["ACLs"]), 3)
        self.assertEqual(result["ACLs"][0], {"Admin": ["Alfred"]})
        self.assertEqual(result["ACLs"][1], {"Member": ["Bertha", "Christian"]})
        self.assertEqual(result["ACLs"][2], "Guest")
    
    def test_ignore_after_text(self):
        """Ignoriert nach Text"""
        content = """# Section
Item1
Das ist ein Text
Item2"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_ignore_after_text: {result}")
        
        self.assertEqual(result["Section"], ["Item1"])  # Nur Item1, Text bricht ab
    
    def test_multiple_sections(self):
        """Mehrere Sections"""
        content = """# Templates
Standard

# Tags
red, green"""
        
        result = MarkdownConfigParser.parse(content)
        print(f"\nDEBUG test_multiple_sections: {result}")
        
        self.assertEqual(result["Templates"], ["Standard"])
        self.assertEqual(result["Tags"], ["red", "green"])
    

    def test_parse_stream(self):
        """Testet Stream-Parsing"""
        from io import StringIO
        
        content = """# Templates
    Standard
    Website

    # Tags
    red, green"""
        
        stream = StringIO(content)
        result = MarkdownConfigParser.parse_stream(stream)
        
        self.assertEqual(result["Templates"], ["Standard", "Website"])
        self.assertEqual(result["Tags"], ["red", "green"])

    def test_parse_file(self):
        """Testet Datei-Parsing"""
        import tempfile
        import os
        
        content = """# Test
    Item1
    Item2"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            result = MarkdownConfigParser.parse_file(temp_path)
            self.assertEqual(result["Test"], ["Item1", "Item2"])
        finally:
            os.unlink(temp_path)
