# cli/myls.py (Aktualisierung)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myls - MyOS Intelligent File Lister
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
import tempfile

try:
    # Versuche MyOS API zu importieren
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.localBlueprintLayer import Blueprint
    HAS_MYOS = True
except ImportError:
    HAS_MYOS = False

class MyOSLister:
    def __init__(self, path: str) -> None:
        self.root = Path(path).resolve()
        if not self.root.exists():
            print(f"Error: Directory does not exist: {self.root}", file=sys.stderr)
            sys.exit(1)
        
        # MyOS API initialisieren falls verfügbar
        self.api = None
        self.in_myos_project = False
        
        if HAS_MYOS:
            try:
                self.api = Blueprint(self.root)
                self.in_myos_project = True
            except (ValueError, ImportError):
                # Kein MyOS Projekt oder andere Fehler
                pass
    
    def is_embryo(self, name: str) -> bool:
        """Prüfe ob ein Name ein Embryo ist."""
        if not self.api or not self.in_myos_project:
            return False
        
        try:
            # Konvertiere zu relativem Pfad für API
            rel_path = str(Path(name).relative_to(self.root) if Path(name).is_absolute() else name)
            return self.api.is_embryo(rel_path)
        except:
            return False
    
    def get_embryos(self) -> List[str]:
        """Hole alle Embryos im aktuellen Verzeichnis."""
        if not self.api or not self.in_myos_project:
            return []
        
        try:
            rel_path = str(self.root.relative_to(self.api.project_root))
            return self.api.get_embryos_at(rel_path)
        except:
            return []
    
    def list_extended(self, color: bool = False) -> None:
        """
        Erweiterte Ansicht mit Embryo-Informationen.
        
        Args:
            color: Farbige Ausgabe verwenden
        """
        print(f"Directory: {self.root}")
        if self.in_myos_project and self.api:
            print(f"Project: {self.api.project_root.name}")
            print(f"Template: {self.api.template_names[0] if self.api.template_names else 'None'}")
        print("-" * 60)
        
        try:
            items = sorted(self.root.iterdir())
        except PermissionError:
            print(f"Error: Cannot read directory {self.root}", file=sys.stderr)
            return
        
        for item in items:
            icon = "📁" if item.is_dir() else "📄"
            name = item.name + ("/" if item.is_dir() else "")
            
            # Embryo-Status prüfen
            is_emb = self.is_embryo(item.name) if item.is_dir() else False
            
            if color and is_emb:
                # Farbcode für halbtransparent (ANSI)
                print(f"\033[2;34m{icon} {name:<40} [embryo]\033[0m")
            elif is_emb:
                print(f"{icon} {name:<40} [embryo]")
            elif item.is_dir():
                print(f"{icon} {name:<40} [physical]")
            else:
                print(f"{icon} {name}")
        
        # Embryo-Statistik
        embryos = self.get_embryos()
        if embryos:
            print(f"\nEmbryos in this directory ({len(embryos)}):")
            for embryo in sorted(embryos):
                print(f"  🥚 {embryo}")
        
        # Projekt-Info wenn verfügbar
        if self.in_myos_project and self.api:
            total_embryos = sum(len(self.api.get_embryos_at(p)) 
                              for p in [""] + list(self.api.embryo_tree.keys()))
            print(f"\nProject has {total_embryos} total embryos available")
    
    # Bestehende Methoden behalten...
    def list_normal(self) -> None:
        """Normale ls-ähnliche Ausgabe."""
        try:
            items = sorted(self.root.iterdir())
            for item in items:
                if item.is_dir():
                    print(f"📁 {item.name}/")
                else:
                    print(f"📄 {item.name}")
        except PermissionError:
            print(f"Error: Cannot read directory {self.root}", file=sys.stderr)
    
    def list_potential(self) -> None:
        """Veraltet - für Kompatibilität."""
        print("Note: % markers are deprecated. Use --extended instead.")
        self.list_extended()
    
    # Rest der bestehenden Methoden...
    def _get_all_files(self) -> List[Dict[str, Any]]:
        # ... bestehende Implementierung
        pass
    
    def list_recent(self, limit: int = 10, roentgen: bool = False) -> None:
        # ... bestehende Implementierung
        pass
    
    def list_roentgen(self, limit: int = 10) -> None:
        # ... bestehende Implementierung
        pass
    
    def list_all(self) -> None:
        print("=" * 60)
        self.list_extended()
        print("-" * 60)
        self.list_recent(limit=5, roentgen=True)
        print("=" * 60)

def parse_arguments(args=None) -> argparse.Namespace:  # ← Parameter hinzufügen
    """Parse command line arguments."""
    if args is None:
        args = sys.argv[1:]  # Default: aktuelle Kommandozeile
    
    parser = argparse.ArgumentParser(
        description='MyOS Intelligent File Lister',
        epilog='Examples:\n'
               '  myls . --extended          # Show embryo status\n'
               '  myls ~/projects --recent=5 # 5 newest files\n'
               '  myls --all                 # Combined overview',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Directory to analyze (default: current directory)'
    )
    
    # Neue extended Option
    parser.add_argument(
        '--extended', '-e',
        action='store_true',
        help='Extended view with embryo information'
    )
    
    parser.add_argument(
        '--color', '-c',
        action='store_true',
        help='Colored output (embryos in light blue)'
    )
    
    # Bestehende Optionen
    parser.add_argument(
        '--potential',
        action='store_true',
        help='[Deprecated] Show potential folders'
    )
    
    parser.add_argument(
        '--recent',
        nargs='?',
        const=10,
        type=int,
        metavar='N',
        help='Show N newest files (default: 10)'
    )
    
    parser.add_argument(
        '--roentgen',
        nargs='?',
        const=10,
        type=int,
        metavar='N',
        help='Show Roentgen view with N files (default: 10)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show combined overview with all view types'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='myls 0.2.0 (MyOS Prototype)'
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    try:
        args = parse_arguments()
        lister = MyOSLister(args.path)
        
        # Dispatch zu entsprechender View
        if args.extended or args.potential:
            lister.list_extended(color=args.color)
        elif args.recent is not None:
            lister.list_recent(limit=args.recent)
        elif args.roentgen is not None:
            lister.list_roentgen(limit=args.roentgen)
        elif args.all:
            lister.list_all()
        else:
            lister.list_normal()
            
    except FileNotFoundError as e:
        print(f"Error: Directory not found - {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
