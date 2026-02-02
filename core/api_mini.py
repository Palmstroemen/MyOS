# core/api.py
from pathlib import Path
from typing import Dict, List
from .localBlueprintLayer import Blueprint
from .project import ProjectFinder

class MyOSAPI:
    def __init__(self, cwd: Path = None):
        self.cwd = cwd or Path.cwd()
    
    def ls(self) -> List[Dict]:
        """Listet Verzeichnis mit Embryo-Info"""
        entries = []
        for item in self.cwd.iterdir():
            entry = {
                "name": item.name,
                "is_embryo": False,
                "type": "dir" if item.is_dir() else "file"
            }
            
            # Embryo-Check (über Blueprint)
            blueprint = Blueprint(self.cwd)
            if blueprint.is_embryo(item):
                entry["is_embryo"] = True
                entry["name_display"] = f"{item.name}%"
            
            entries.append(entry)
        return entries
    
    def get_project(self):
        """Aktuelles Projekt"""
        return ProjectFinder.find_nearest(self.cwd)
    
    def create_embryo(self, name: str):
        """Embryo erstellen"""
        # TODO: Implementieren
        pass
