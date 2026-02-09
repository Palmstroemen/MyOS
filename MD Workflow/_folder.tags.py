#!/usr/bin/env python3
# folder_tags.py
import yaml
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import shutil

class MDFirstWorkflow:
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.tags_file = self.base_path / "_folder.tags.md"
        self.workflow_dir = self.base_path / ".md-workflow"
        self.workflow_dir.mkdir(exist_ok=True)
        
    # --- Tag Management ---
    def get_folder_tags(self) -> List[str]:
        """Lese Tags für diesen Ordner"""
        if not self.tags_file.exists():
            return []
        
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if '---' not in content:
            return []
            
        yaml_content = content.split('---')[1]
        try:
            meta = yaml.safe_load(yaml_content)
            return meta.get('folder-tags', [])
        except yaml.YAMLError:
            return []
    
    def set_folder_tags(self, tags: List[str]):
        """Setze Tags für den Ordner"""
        meta = self._load_or_create_meta()
        meta['folder-tags'] = list(set(tags))  # Duplikate entfernen
        self._save_meta(meta)
    
    def add_file_tags(self, filename: str, tags: List[str]):
        """Füge Tags für spezifische Datei hinzu"""
        meta = self._load_or_create_meta()
        if 'file-tags' not in meta:
            meta['file-tags'] = {}
        
        current = set(meta['file-tags'].get(filename, []))
        current.update(tags)
        meta['file-tags'][filename] = list(current)
        self._save_meta(meta)
    
    # --- Export Actions ---
    def export_to_office(self, md_file: str, target_format: str, 
                         selection: str = None) -> Dict:
        """
        Exportiere MD zu Office-Format
        
        Args:
            md_file: Markdown-Datei
            target_format: 'docx', 'pptx', 'pdf', 'odt', 'html'
            selection: Optionaler markierter Text (für Kontext)
        """
        md_path = self.base_path / md_file
        
        if not md_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {md_file}")
        
        # Lese Markdown
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrahiere Tags aus MD und Ordner
        tags = self._extract_all_tags(md_path, content)
        
        # Generiere Ziel-Dateiname
        stem = md_path.stem
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        export_file = f"{stem}_{timestamp}.{target_format}"
        export_path = self.base_path / export_file
        
        # Export je nach Format
        result = {
            'source': md_file,
            'export': export_file,
            'format': target_format,
            'tags': tags,
            'timestamp': timestamp,
            'selection': bool(selection)
        }
        
        if target_format == 'pdf':
            self._export_to_pdf(md_path, export_path, tags)
        elif target_format in ['docx', 'odt']:
            self._export_to_word(md_path, export_path, tags, target_format)
        elif target_format == 'pptx':
            self._export_to_powerpoint(md_path, export_path, tags)
        elif target_format == 'html':
            self._export_to_html(md_path, export_path, tags)
        
        # Protokolliere Export
        self._log_export(result)
        
        # Tags in Office-Metadaten schreiben (wenn unterstützt)
        if target_format in ['docx', 'pptx', 'odt']:
            self._write_tags_to_office(export_path, tags)
        
        return result
    
    def _export_to_pdf(self, md_path: Path, pdf_path: Path, tags: List[str]):
        """Export zu PDF mit Pandoc"""
        import subprocess
        
        # Pandoc-Befehl mit Tags als Metadaten
        cmd = [
            'pandoc', str(md_path), '-o', str(pdf_path),
            '--pdf-engine=xelatex',
            f'--metadata=keywords:{",".join(tags)}',
            '--variable', 'documentclass=article',
            '--variable', 'papersize=a4'
        ]
        
        subprocess.run(cmd, check=True)
    
    def _export_to_word(self, md_path: Path, doc_path: Path, 
                       tags: List[str], format: str):
        """Export zu Word/LibreOffice"""
        import subprocess
        
        cmd = [
            'pandoc', str(md_path), '-o', str(doc_path),
            f'--metadata=keywords:{",".join(tags)}'
        ]
        
        subprocess.run(cmd, check=True)
    
    def _export_to_powerpoint(self, md_path: Path, pptx_path: Path, 
                            tags: List[str):
        """Export zu PowerPoint (einfache Slides)"""
        # Pandoc kann einfache PPTX
        import subprocess
        
        # Markdown mit --- als Slide-Trenner
        cmd = [
            'pandoc', str(md_path), '-o', str(pptx_path),
            '-t', 'pptx',
            f'--metadata=keywords:{",".join(tags)}',
            '--slide-level=2'
        ]
        
        subprocess.run(cmd, check=True)
    
    def _write_tags_to_office(self, office_path: Path, tags: List[str]):
        """Schreibe Tags in Office-Metadaten (Python-pptx, python-docx)"""
        try:
            if office_path.suffix == '.docx':
                import docx
                doc = docx.Document(str(office_path))
                core_props = doc.core_properties
                core_props.keywords = ', '.join(tags)
                doc.save(str(office_path))
                
            elif office_path.suffix == '.pptx':
                from pptx import Presentation
                prs = Presentation(str(office_path))
                prs.core_properties.keywords = ', '.join(tags)
                prs.save(str(office_path))
                
        except ImportError:
            print("Python-pptx oder python-docx nicht installiert")
            # Alternative: Exiftool für Metadaten
            self._write_tags_with_exiftool(office_path, tags)
    
    def _write_tags_with_exiftool(self, file_path: Path, tags: List[str]):
        """Schreibe Tags mit exiftool (falls installiert)"""
        import subprocess
        try:
            tags_str = ' -keywords="' + '" -keywords="'.join(tags) + '"'
            cmd = f'exiftool {tags_str} "{file_path}"'
            subprocess.run(cmd, shell=True, check=True)
            
            # Original backup löschen
            backup = file_path.with_suffix(file_path.suffix + '_original')
            if backup.exists():
                backup.unlink()
        except:
            pass
    
    # --- Helper Methods ---
    def _load_or_create_meta(self) -> Dict:
        """Lade oder erstelle Meta-Datei"""
        if not self.tags_file.exists():
            return {
                'folder-tags': [],
                'file-tags': {},
                'created': datetime.now().isoformat()
            }
        
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '---' not in content:
            return {'folder-tags': [], 'file-tags': {}}
        
        yaml_content = content.split('---')[1]
        try:
            meta = yaml.safe_load(yaml_content)
            if not isinstance(meta, dict):
                meta = {}
            return meta
        except yaml.YAMLError:
            return {'folder-tags': [], 'file-tags': {}}
    
    def _save_meta(self, meta: Dict):
        """Speichere Meta-Datei"""
        # Behalte Markdown-Kommentare
        existing_content = ""
        if self.tags_file.exists():
            with open(self.tags_file, 'r', encoding='utf-8') as f:
                full_content = f.read()
                if '---' in full_content:
                    parts = full_content.split('---', 2)
                    if len(parts) > 2:
                        existing_content = parts[2].strip()
        
        yaml_content = yaml.dump(meta, allow_unicode=True, 
                                default_flow_style=False)
        
        content = f"---\n{yaml_content}---\n"
        if existing_content:
            content += f"\n{existing_content}\n"
        
        with open(self.tags_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _extract_all_tags(self, md_path: Path, content: str) -> List[str]:
        """Extrahiere alle Tags für eine MD-Datei"""
        tags = set()
        
        # 1. Tags aus Ordner
        tags.update(self.get_folder_tags())
        
        # 2. Tags aus Datei-Metadaten
        meta = self._load_or_create_meta()
        file_tags = meta.get('file-tags', {}).get(md_path.name, [])
        tags.update(file_tags)
        
        # 3. Tags aus Markdown-Inhalt (#tag)
        import re
        md_tags = re.findall(r'#([a-zA-Z0-9_\-/äöüß]+)', content)
        tags.update(md_tags)
        
        # 4. Tags aus YAML Frontmatter (falls vorhanden)
        if content.startswith('---'):
            try:
                parts = content.split('---', 2)
                if len(parts) > 1:
                    frontmatter = yaml.safe_load(parts[1])
                    if isinstance(frontmatter, dict):
                        fm_tags = frontmatter.get('tags', [])
                        if isinstance(fm_tags, list):
                            tags.update(fm_tags)
                        elif isinstance(fm_tags, str):
                            tags.add(fm_tags)
            except:
                pass
        
        return list(tags)
    
    def _log_export(self, export_info: Dict):
        """Protokolliere Export für Nachverfolgung"""
        log_file = self.workflow_dir / "exports.json"
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                try:
                    log = json.load(f)
                except json.JSONDecodeError:
                    log = []
        else:
            log = []
        
        log.append(export_info)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
    
    # --- Utility Methods ---
    def open_with_office(self, md_file: str, office_app: str = "libreoffice"):
        """
        Öffne Markdown in Office-App
        
        Args:
            md_file: Markdown-Datei
            office_app: 'libreoffice', 'msword', 'browser', 'email'
        """
        md_path = self.base_path / md_file
        
        if not md_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {md_file}")
        
        if office_app == "libreoffice":
            # Export zu ODT und öffne
            result = self.export_to_office(md_file, "odt")
            import subprocess
            subprocess.run(["libreoffice", str(self.base_path / result['export'])])
            
        elif office_app == "email":
            # Export zu HTML für Email
            result = self.export_to_office(md_file, "html")
            html_path = self.base_path / result['export']
            
            # Öffne in Standard-Email-Client
            import subprocess
            # Einfache Version: Öffne im Browser
            import webbrowser
            webbrowser.open(f"file://{html_path}")
            
        elif office_app == "print":
            # Drucke direkt
            result = self.export_to_office(md_file, "pdf")
            pdf_path = self.base_path / result['export']
            
            # Linux: Drucke mit lp
            import subprocess
            subprocess.run(["lp", str(pdf_path)])
    
    def get_export_history(self, md_file: str = None) -> List[Dict]:
        """Hole Export-Historie"""
        log_file = self.workflow_dir / "exports.json"
        
        if not log_file.exists():
            return []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                return []
        
        if md_file:
            return [entry for entry in log if entry.get('source') == md_file]
        return log


# --- CLI Interface ---
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MD-first Workflow Manager")
    parser.add_argument("action", choices=["tags", "export", "open", "history"])
    parser.add_argument("--file", help="Markdown file")
    parser.add_argument("--format", choices=["pdf", "docx", "pptx", "odt", "html"])
    parser.add_argument("--app", choices=["libreoffice", "email", "print"])
    parser.add_argument("--add-tag", help="Add tag to folder")
    
    args = parser.parse_args()
    
    workflow = MDFirstWorkflow()
    
    if args.action == "tags":
        if args.add_tag:
            tags = workflow.get_folder_tags()
            tags.append(args.add_tag)
            workflow.set_folder_tags(tags)
            print(f"Tag '{args.add_tag}' hinzugefügt")
        else:
            print("Folder tags:", workflow.get_folder_tags())
            
    elif args.action == "export" and args.file and args.format:
        result = workflow.export_to_office(args.file, args.format)
        print(f"Exportiert: {result['export']}")
        print(f"Tags: {result['tags']}")
        
    elif args.action == "open" and args.file and args.app:
        workflow.open_with_office(args.file, args.app)
        
    elif args.action == "history":
        history = workflow.get_export_history(args.file)
        for entry in history:
            print(f"{entry['timestamp']}: {entry['source']} -> {entry['export']}")