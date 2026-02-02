# core/api.py

class MyOSAPI:
    """Minimal API für CLI-Integration"""
    
    def __init__(self, cwd: Path = None):
        self.cwd = cwd or Path.cwd()
        self.blueprint = None  # Wird lazy geladen
        
    # ─── NAVIGATION ──────────────────────────────────────────
    def get_cwd(self) -> Path:
        """Gibt aktuelles Arbeitsverzeichnis zurück"""
        return self.cwd
    
    def set_cwd(self, path: Path | str) -> bool:
        """Setzt neues Arbeitsverzeichnis"""
        path = Path(path)
        if path.is_dir():
            self.cwd = path.resolve()
            self.blueprint = None  # Reset blueprint cache
            return True
        return False
    
    def cd(self, path: Path | str) -> bool:
        """Alias für set_cwd (für CLI intuitiver)"""
        return self.set_cwd(path)
    
    # ─── LISTING ─────────────────────────────────────────────
    def ls(self, path: Path = None) -> List[Dict]:
        """
        Listet Verzeichnis mit MyOS-Metadaten
        
        Returns:
            List of dicts mit:
            - name: str
            - type: "file" | "directory" | "embryo"
            - size: int (bytes)
            - modified: datetime
            - is_embryo: bool
            - template: str | None
        """
        target = (path or self.cwd).resolve()
        
        entries = []
        for item in target.iterdir():
            entry = self._stat_to_entry(item)
            
            # Embryo-Check
            if self._is_embryo(item):
                entry["type"] = "embryo"
                entry["is_embryo"] = True
                entry["name_display"] = f"{item.name}%"  # Für CLI-Anzeige
            
            entries.append(entry)
        
        return entries
    
    # ─── EMBRYO OPERATIONS ───────────────────────────────────
    def create_embryo(self, name: str, template: str = None) -> bool:
        """
        Erstellt einen neuen Embryo-Ordner
        
        Args:
            name: Name des Embryos
            template: Template-Name (optional, default vom Projekt)
        """
        embryo_path = self.cwd / name
        
        # 1. Prüfen ob schon existiert
        if embryo_path.exists():
            raise MyOSError("ALREADY_EXISTS", f"{name} existiert bereits")
        
        # 2. Template finden
        template = template or self._get_default_template()
        
        # 3. Embryo im Blueprint registrieren
        blueprint = self._get_blueprint()
        blueprint.register_embryo(embryo_path, template)
        
        return True
    
    def birth_embryo(self, name: str) -> bool:
        """
        Wandelt Embryo in echten Ordner um
        
        Args:
            name: Name des Embryos oder Pfad
        """
        embryo_path = self.cwd / name if "/" not in name else Path(name)
        
        # 1. Prüfen ob Embryo existiert
        if not self._is_embryo(embryo_path):
            raise MyOSError("NOT_EMBRYO", f"{name} ist kein Embryo")
        
        # 2. Template-Inhalt kopieren
        blueprint = self._get_blueprint()
        template_info = blueprint.get_embryo_template(embryo_path)
        
        # 3. Echten Ordner erstellen
        embryo_path.mkdir(exist_ok=True)
        
        # 4. Template-Inhalt kopieren
        self._copy_template_content(template_info, embryo_path)
        
        # 5. Embryo-Markierung entfernen
        blueprint.mark_as_born(embryo_path)
        
        return True
    
    def list_embryos(self) -> List[str]:
        """Listet alle Embryos im aktuellen Verzeichnis"""
        embryos = []
        for item in self.cwd.iterdir():
            if item.is_dir() and self._is_embryo(item):
                embryos.append(item.name)
        return embryos
    
    # ─── PROJECT OPERATIONS ──────────────────────────────────
    def get_current_project(self) -> Dict:
        """Gibt Informationen zum aktuellen Projekt zurück"""
        project_root = self._find_project_root(self.cwd)
        if not project_root:
            return None
        
        return {
            "name": project_root.name,
            "path": project_root,
            "templates": self._get_project_templates(project_root),
            "has_info": (project_root / ".MyOS" / "project.md").exists()
        }
    
    def create_project(self, name: str, template: str = "Standard") -> bool:
        """Erstellt ein neues Projekt"""
        project_path = self.cwd / name
        
        # Projekt-Struktur erstellen
        from core.project import make_project
        return make_project(project_path, template)
    
    # ─── PRIVATE HELPER ──────────────────────────────────────
    def _get_blueprint(self) -> Blueprint:
        """Lazy loading des Blueprint-Layers"""
        if self.blueprint is None:
            self.blueprint = Blueprint(self.cwd)
        return self.blueprint
    
    def _is_embryo(self, path: Path) -> bool:
        """Prüft ob Pfad ein Embryo ist"""
        if not path.exists():
            return False
        
        blueprint = self._get_blueprint()
        return blueprint.is_embryo(path)
    
    def _stat_to_entry(self, path: Path) -> Dict:
        """Konvertiert Path.stat() zu API-Entry"""
        stat = path.stat()
        
        return {
            "name": path.name,
            "type": "directory" if path.is_dir() else "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "is_embryo": False,  # Wird überschrieben wenn nötig
            "template": None
        }
    
    def _find_project_root(self, start: Path) -> Path | None:
        """Findet Projekt-Root (aufwärts suchen)"""
        from core.project import ProjectFinder
        return ProjectFinder.find_nearest(start)

# Ergänzungen zur API

class MyOSAPI:
    # ... bestehende Methoden ...
    
    def search(self, query: str, path: Path = None) -> List[Dict]:
        """Einfache Suche (später erweitern)"""
        target = path or self.cwd
        results = []
        
        for item in target.rglob("*"):
            if query.lower() in item.name.lower():
                entry = self._stat_to_entry(item)
                entry["path"] = item.relative_to(target)
                results.append(entry)
        
        return results
    
    def get_info(self, path: Path = None) -> str:
        """Liest .MyOS/project.md oder andere Info-Dateien"""
        target = path or self.cwd
        
        # Projekt-Info
        project_info = target / ".MyOS" / "project.md"
        if project_info.exists():
            return project_info.read_text()
        
        # Fallback: README.md oder info.txt
        for info_file in ["README.md", "info.txt", "INFO.md"]:
            if (target / info_file).exists():
                return (target / info_file).read_text()
        
        return "No info available"
    
    def set_info(self, content: str, path: Path = None) -> bool:
        """Schreibt Projekt-Info"""
        target = path or self.cwd
        project_info = target / ".MyOS" / "project.md"
        
        # .MyOS Verzeichnis sicherstellen
        project_info.parent.mkdir(exist_ok=True)
        project_info.write_text(content)
        return True
