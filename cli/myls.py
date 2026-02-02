# cli/myls.py (update)
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
    # Try to import the MyOS API
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
        
        # Initialize MyOS API if available
        self.api = None
        self.in_myos_project = False
        
        if HAS_MYOS:
            try:
                self.api = Blueprint(self.root)
                self.in_myos_project = True
            except (ValueError, ImportError):
                # Not a MyOS project or other error
                pass
    
    def is_embryo(self, name: str) -> bool:
        """Check whether a name is an embryo."""
        if not self.api or not self.in_myos_project:
            return False
        
        try:
            # Convert to relative path for the API
            rel_path = str(Path(name).relative_to(self.root) if Path(name).is_absolute() else name)
            return self.api.is_embryo(rel_path)
        except:
            return False
    
    def get_embryos(self) -> List[str]:
        """Return all embryos in the current directory."""
        if not self.api or not self.in_myos_project:
            return []
        
        try:
            rel_path = str(self.root.relative_to(self.api.project_root))
            return self.api.get_embryos_at(rel_path)
        except:
            return []
    
    def list_extended(self, color: bool = False) -> None:
        """
        Extended view with embryo information.
        
        Args:
            color: Use colored output
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
            
            # Check embryo status
            is_emb = self.is_embryo(item.name) if item.is_dir() else False
            
            if color and is_emb:
                # ANSI color for embryos
                print(f"\033[2;34m{icon} {name:<40} [embryo]\033[0m")
            elif is_emb:
                print(f"{icon} {name:<40} [embryo]")
            elif item.is_dir():
                print(f"{icon} {name:<40} [physical]")
            else:
                print(f"{icon} {name}")
        
        # Embryo summary
        embryos = self.get_embryos()
        if embryos:
            print(f"\nEmbryos in this directory ({len(embryos)}):")
            for embryo in sorted(embryos):
                print(f"  🥚 {embryo}")
        
        # Project info if available
        if self.in_myos_project and self.api:
            total_embryos = sum(len(self.api.get_embryos_at(p)) 
                              for p in [""] + list(self.api.embryo_tree.keys()))
            print(f"\nProject has {total_embryos} total embryos available")
    
    # Existing methods retained
    def list_normal(self) -> None:
        """Normal ls-like output."""
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
        """Deprecated - kept for compatibility."""
        print("Note: % markers are deprecated. Use --extended instead.")
        self.list_extended()
    
    # Remaining existing methods
    def _get_all_files(self) -> List[Dict[str, Any]]:
        # ... existing implementation
        pass
    
    def list_recent(self, limit: int = 10, roentgen: bool = False) -> None:
        # ... existing implementation
        pass
    
    def list_roentgen(self, limit: int = 10) -> None:
        # ... existing implementation
        pass
    
    def list_all(self) -> None:
        print("=" * 60)
        self.list_extended()
        print("-" * 60)
        self.list_recent(limit=5, roentgen=True)
        print("=" * 60)

def parse_arguments(args=None) -> argparse.Namespace:
    """Parse command line arguments."""
    if args is None:
        args = sys.argv[1:]  # Default: current command line
    
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
    
    # Extended option
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
    
    # Existing options
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
        
        # Dispatch to the selected view
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
