#!/usr/bin/env python3
"""
core/config/parser.py - MyOS Config.md Parser
"""

from typing import Dict, List, Any, Optional, Union, TextIO
from pathlib import Path
import re

class MarkdownConfigParser:
    """Parser für MyOS Config.md Dateien - Stream-basiert."""
    
    @staticmethod
    def parse(content: str) -> Dict[str, Any]:
        """Kompatibilitäts-Methode für String-Input."""
        from io import StringIO
        return MarkdownConfigParser.parse_stream(StringIO(content))
    
    @staticmethod
    def parse_stream(stream: TextIO) -> Dict[str, Any]:
        """
        Parst Config.md aus Stream (Datei oder StringIO).
        
        Args:
            stream: Text stream (Datei oder StringIO)
            
        Returns:
            Dict mit geparsten Daten
        """
        result = {}
        current_section = None
        current_items = []
        state = "SLEEPING"
        
        for line in stream:
            line = line.rstrip('\n')  # Nur Newline entfernen
            stripped = line.strip()
            
            # PRÜFE ZUERST: Ist das ein Property in Überschrift-Form? (#### key: value)
            if (stripped.startswith('#') and ' ' in stripped and 
                ': ' in stripped and stripped.find(': ') > stripped.find(' ')):
                # Ja, das ist wie "#### inherit: dynamic"
                if state == "PARSING" and current_section is not None:
                    # Als normale Property-Zeile behandeln (ohne führende #)
                    content_part = stripped.lstrip('#').strip()
                    item = MarkdownConfigParser._parse_line(content_part)
                    if item is not None:
                        current_items.append(item)
                continue
            
            # Normale Überschrift (ohne Doppelpunkt oder Doppelpunkt vor Space)
            if stripped.startswith('#') and ' ' in stripped:
                # Vorherige Section abschließen
                if current_section is not None and current_items:
                    result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                
                # Neue Section starten
                hash_end = stripped.find(' ')
                section_name = stripped[hash_end:].strip()
                current_section = section_name
                current_items = []
                state = "PARSING"
                continue
            
            # Wenn wir im PARSING Zustand sind
            if state == "PARSING" and current_section is not None:
                # Leerzeile beendet Section
                if not stripped:
                    if current_items:
                        result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                    current_section = None
                    state = "SLEEPING"
                    continue
                
                # Zeile parsen
                item = MarkdownConfigParser._parse_line(stripped)
                if item is not None:
                    current_items.append(item)
                else:
                    # Ungültige Zeile → Section beenden
                    if current_items:
                        result[current_section] = MarkdownConfigParser._finalize_items(current_items)
                    current_section = None
                    state = "SLEEPING"
                    continue
        
        # Letzte Section speichern
        if current_section is not None and current_items:
            result[current_section] = MarkdownConfigParser._finalize_items(current_items)
        
        return result
    
    @staticmethod
    def parse_file(filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Parst Config.md Datei direkt von Festplatte.
        
        Args:
            filepath: Pfad zur Config.md Datei
            
        Returns:
            Dict mit geparsten Daten
        """
        filepath = Path(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return MarkdownConfigParser.parse_stream(f)
        except UnicodeDecodeError:
            # Fallback für andere Encodings
            with open(filepath, 'r', encoding='latin-1') as f:
                return MarkdownConfigParser.parse_stream(f)
    
    @staticmethod
    def _parse_line(line: str) -> Any:
        """Parst eine einzelne Zeile in ein Item."""
        # Kommentar entfernen (alles nach #)
        if '#' in line:
            line = line.split('#')[0].strip()
        
        if not line:
            return None
        
        # 1. Key-Value Paar mit ":"
        if ': ' in line:
            key, value = line.split(': ', 1)
            key = key.strip()
            value = value.strip()
            
            if ',' in value:
                items = [item.strip() for item in value.split(',')]
                return {key: items}
            else:
                return {key: [value]}
        
        # 2. List-Item mit "*" (optional)
        if line.startswith('* '):
            return line[2:].strip()
        
        # 3. Komma-separierte Liste
        if ',' in line:
            items = [item.strip() for item in line.split(',')]
            # Wenn nur ein Item (z.B. "value,") → als Einzelwert
            if len(items) == 1 and items[0]:
                return items[0]
            return items
        
        # 4. Einzelnes Wort (kann auch mit Bindestrich oder Unterstrichen sein)
        if line and ' ' not in line:
            return line
        
        # 5. Alles andere ist ungültig (beendet Section)
        return None
    
    @staticmethod
    def _finalize_items(items: List[Any]) -> Any:
        """Verarbeitet gesammelte Items in finales Format."""
        if not items:
            return []
        
        # Prüfe Typen
        has_dicts = any(isinstance(item, dict) for item in items)
        has_strings = any(isinstance(item, str) for item in items)
        has_lists = any(isinstance(item, list) for item in items)
        
        # 1. Nur Dicts → zu einem Dict mergen
        if has_dicts and not has_strings and not has_lists:
            result = {}
            for item in items:
                if isinstance(item, dict):
                    result.update(item)
            return result
        
        # 2. Nur Strings (oder Strings + Listen) → als Liste
        if has_strings or has_lists:
            result = []
            for item in items:
                if isinstance(item, list):
                    result.extend(item)
                else:
                    result.append(item)
            return result
        
        # 3. Nur ein Dict → direkt zurückgeben
        if len(items) == 1 and isinstance(items[0], dict):
            return items[0]
        
        # 4. Sonst unverändert
        return items
    
    @staticmethod
    def find_inherit(section_data: Any) -> Optional[List[str]]:
        """Findet inherit-Wert in einer Section."""
        if isinstance(section_data, dict):
            return section_data.get("inherit")
        elif isinstance(section_data, list):
            # In Liste nach Dict mit "inherit" suchen
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
