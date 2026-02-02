#!/usr/bin/env python3
"""
core/config/parser.py - MyOS Config.md parser.
"""

from typing import Dict, List, Any, Optional, Union, TextIO
from pathlib import Path
import re

class MarkdownConfigParser:
    """Stream-based parser for MyOS Config.md files."""
    
    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        """Compatibility helper for string input."""
        from io import StringIO
        return MarkdownConfigParser.parse_stream(StringIO(content))
    
    @staticmethod
    def parse_stream(stream: TextIO) -> Dict[str, Any]:
        """
        Parse Config.md from a text stream (file or StringIO).
        
        Args:
            stream: Text stream (file or StringIO)
            
        Returns:
            Dict with parsed data
        """
        result = {}
        current_section = None
        current_items = []
        state = "SLEEPING"
        
        for line in stream:
            line = line.rstrip('\n')  # Strip newline only
            stripped = line.strip()
            
            # Check first: is this a header-style property? (#### key: value)
            if (stripped.startswith('#') and ' ' in stripped and 
                ': ' in stripped and stripped.find(': ') > stripped.find(' ')):
                # Example: "#### inherit: dynamic"
                if state == "PARSING" and current_section is not None:
                    # Treat as a normal property line (without the leading #)
                    content_part = stripped.lstrip('#').strip()
                    item = MarkdownConfigParser._parse_line(content_part)
                    if item is not None:
                        current_items.append(item)
                continue
            
            # Regular header (no colon, or colon before space)
            if stripped.startswith('#') and ' ' in stripped:
                # Finalize previous section
                if current_section is not None and current_items:
                    result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                
                # Start new section
                hash_end = stripped.find(' ')
                section_name = stripped[hash_end:].strip()
                current_section = section_name
                current_items = []
                state = "PARSING"
                continue
            
            # If we are in parsing state
            if state == "PARSING" and current_section is not None:
                # Empty line ends a section
                if not stripped:
                    if current_items:
                        result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                    current_section = None
                    state = "SLEEPING"
                    continue
                
                # Parse a line
                item = MarkdownConfigParser._parse_line(stripped)
                if item is not None:
                    current_items.append(item)
                else:
                    # Invalid line -> end section
                    if current_items:
                        result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                    current_section = None
                    state = "SLEEPING"
                    continue
        
        # Store last section
        if current_section is not None and current_items:
            result[current_section] = MarkdownConfigParser._finalize_items(current_items)
        
        return result
    
    @staticmethod
    def parse_file(filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Parse Config.md directly from disk.
        
        Args:
            filepath: Path to the Config.md file
            
        Returns:
            Dict with parsed data
        """
        filepath = Path(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return MarkdownConfigParser.parse_stream(f)
        except UnicodeDecodeError:
            # Fallback for other encodings
            with open(filepath, 'r', encoding='latin-1') as f:
                return MarkdownConfigParser.parse_stream(f)
    
    @staticmethod
    def _parse_line(line: str) -> Any:
        """Parse a single line into an item."""
        # Remove inline comments (anything after #)
        if '#' in line:
            line = line.split('#')[0].strip()
        
        if not line:
            return None
        
        # 1. Key-value pair with ":"
        if ': ' in line:
            key, value = line.split(': ', 1)
            key = key.strip()
            value = value.strip()
            
            if ',' in value:
                items = [item.strip() for item in value.split(',')]
                return {key: items}
            else:
                return {key: [value]}
        
        # 2. List item with "*" (optional)
        if line.startswith('* '):
            return line[2:].strip()
        
        # 3. Comma-separated list
        if ',' in line:
            items = [item.strip() for item in line.split(',')]
            # If only one item (e.g., "value,") -> keep as single value
            if len(items) == 1 and items[0]:
                return items[0]
            return items
        
        # 4. Single word (may include dashes or underscores)
        if line and ' ' not in line:
            return line
        
        # 5. Everything else is invalid (ends the section)
        return None
    
    @staticmethod
    def _finalize_items(items: List[Any]) -> Any:
        """Finalize collected items into the output format."""
        if not items:
            return []
        
        # Inspect item types
        has_dicts = any(isinstance(item, dict) for item in items)
        has_strings = any(isinstance(item, str) for item in items)
        has_lists = any(isinstance(item, list) for item in items)
        
        # 1. Only dicts -> merge into a single dict
        if has_dicts and not has_strings and not has_lists:
            result = {}
            for item in items:
                if isinstance(item, dict):
                    result.update(item)
            return result
        
        # 2. Only strings (or strings + lists) -> list
        if has_strings or has_lists:
            result = []
            for item in items:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result
        
        # 3. Only one dict -> return directly
        if len(items) == 1 and isinstance(items[0], dict):
            return items[0]
        
        # 4. Fallback: return as-is
        return items
    
    @staticmethod
    def find_inherit(section_data: Any) -> Optional[List[str]]:
        """Return the inherit value from a section, if present."""
        if isinstance(section_data, dict):
            return section_data.get("inherit")
        elif isinstance(section_data, list):
            # Look for a dict containing "inherit"
            for item in section_data:
                if isinstance(item, dict) and "inherit" in item:
                    return item["inherit"]
        return None


if __name__ == "__main__":
    # Quick self-test
    test_content = """# Templates
Standard
Website
    
#### inherit: dynamic
#### version: 2.0"""
    
    result = MarkdownConfigParser.parse(test_content)
    print("✅ Parser self-test:")
    print(f"   Result: {result}")
    
    inherit = MarkdownConfigParser.find_inherit(result["Templates"])
    print(f"   Inherit found: {inherit}")
    
    assert "Templates" in result
    assert result["Templates"]["inherit"] == ["dynamic"]
    assert inherit == ["dynamic"]
    
    print("\n✅ All parser tests passed!")
