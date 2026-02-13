from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import re
import shutil
from typing import List, Optional, Dict, Any

try:
    from core.localBlueprintLayer import Blueprint
    from core.project import ProjectConfig
except Exception:  # pragma: no cover - optional for non-MyOS paths
    Blueprint = None


def find_project_root(start_path: Path) -> Optional[Path]:
    start_path = start_path.resolve()
    for candidate in [start_path] + list(start_path.parents):
        if (candidate / ".MyOS").exists():
            return candidate
    return None


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


class ScopeApi:
    def __init__(self, start_path: str) -> None:
        self.start_path = Path(start_path).expanduser().resolve()
        self.project_root = None
        self.blueprint = None
        self._color_cache: Dict[str, Optional[str]] = {}
        self._set_project_root(find_project_root(self.start_path))

    def _set_project_root(self, root: Optional[Path]) -> None:
        self.project_root = root
        self.blueprint = None
        self._color_cache = {}
        if self.project_root and Blueprint is not None:
            try:
                self.blueprint = Blueprint(self.project_root)
            except Exception:
                self.blueprint = None

    def get_start_path(self) -> str:
        return str(self.start_path)

    def get_project_root(self) -> Optional[str]:
        return str(self.project_root) if self.project_root else None

    def update_context(self, path: str) -> None:
        target = Path(path).expanduser().resolve()
        root = find_project_root(target)
        if root != self.project_root:
            self._set_project_root(root)

    def list_children(self, path: str, include_embryos: bool = True) -> List[Dict[str, Any]]:
        target = Path(path).expanduser().resolve()
        entries: List[Dict[str, Any]] = []
        parent_color = self._resolve_project_color(target)
        try:
            for child in sorted(target.iterdir()):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    is_project = self.is_project(str(child))
                    entries.append(
                        {
                            "name": child.name,
                            "isProject": is_project,
                            "isEmbryo": False,
                            "color": self._resolve_project_color(child) if is_project else None,
                        }
                    )
        except Exception:
            return []

        if include_embryos and self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if not any(item["name"] == name for item in entries):
                    embryo_color = self._resolve_template_color(rel, name)
                    entries.append(
                        {
                            "name": name,
                            "isProject": False,
                            "isEmbryo": True,
                            "color": embryo_color or parent_color,
                        }
                    )
            entries.sort(key=lambda item: item["name"])

        return entries

    def list_templates(self, path: str, include_embryos: bool = True) -> List[Dict[str, Any]]:
        target = Path(path).expanduser().resolve()
        debug = os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}
        if not include_embryos:
            if debug:
                print(f"[scope_api] list_templates: include_embryos=False -> []")
            return []
        if not self.blueprint or not self.project_root or not is_within(target, self.project_root):
            if debug:
                print(
                    f"[scope_api] list_templates: blueprint={bool(self.blueprint)} "
                    f"project_root={self.project_root} target={target} -> []"
                )
            return []
        rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
        try:
            parent_color = self._resolve_project_color(target)
            embryos = sorted(self.blueprint.get_embryos_at(rel))
            result = []
            for name in embryos:
                embryo_color = self._resolve_template_color(rel, name)
                result.append(
                    {
                        "name": name,
                        "isProject": False,
                        "isEmbryo": True,
                        "color": embryo_color or parent_color,
                    }
                )
            if debug:
                print(
                    f"[scope_api] list_templates: rel='{rel}' templates={self.blueprint.template_names} "
                    f"result={[item['name'] for item in result]}"
                )
            return result
        except Exception:
            if debug:
                print(f"[scope_api] list_templates: error for rel='{rel}'")
            return []

    def list_entries(self, path: str) -> List[dict]:
        target = Path(path).expanduser().resolve()
        entries: List[dict] = []
        try:
            for child in sorted(target.iterdir()):
                is_dir = child.is_dir()
                entry = {"name": child.name, "isDir": is_dir, "path": str(child)}
                entries.append(entry)
        except Exception:
            return []

        if self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if not any(item["name"] == name for item in entries):
                    entries.append(
                        {
                            "name": name,
                            "isDir": True,
                            "isEmbryo": True,
                            "path": str(target / name),
                        }
                    )
            entries.sort(key=lambda item: item["name"])

        return entries

    def has_myos_dir(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        return (target / ".MyOS").is_dir()

    def is_project(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        return (target / ".MyOS" / "Project.md").is_file()

    def get_project_color(self, path: str) -> Optional[str]:
        return self._resolve_project_color(Path(path).expanduser().resolve())

    def _resolve_project_color(self, path: Path) -> Optional[str]:
        if not self.project_root:
            return None
        cache_key = str(path)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]
        current = path
        while True:
            color = self._read_color_file(current / ".MyOS" / "Color.md")
            if not color:
                color = self._read_color_file(current / ".MyOS" / "Project.md")
            if color:
                self._color_cache[cache_key] = color
                return color
            if current == self.project_root or current == current.parent:
                break
            current = current.parent
        self._color_cache[cache_key] = None
        return None

    def _resolve_template_color(self, rel_path: str, name: str) -> Optional[str]:
        if not self.blueprint:
            return None
        parts = [p for p in rel_path.split("/") if p]
        parts.append(name)
        for template_name in self.blueprint.template_names:
            base = self.blueprint.templates_dir / template_name
            candidate = base.joinpath(*parts)
            if not candidate.exists():
                continue
            color = self._find_color_upwards(candidate, base)
            if color:
                return color
        return None

    def _find_color_upwards(self, start: Path, stop: Path) -> Optional[str]:
        current = start
        while True:
            color = self._read_color_file(current / ".MyOS" / "Color.md")
            if not color:
                color = self._read_color_file(current / "Color.md")
            if color:
                return color
            if current == stop or current == current.parent:
                return None
            current = current.parent

    def _read_color_file(self, path: Path) -> Optional[str]:
        """Liest eine Farbe aus einer Datei, robust gegenüber Whitespace und Formatierung."""
        try:
            if not path.exists():
                return None
            
            content = path.read_text(encoding="utf-8")
            
            # Debug: Siehst du das?
            print(f"DEBUG _read_color_file: {path}")
            print(f"DEBUG content: {repr(content)}")
            
            # Extrahiere die Farbe
            color = self._extract_color(content)
            
            print(f"DEBUG extracted: {repr(color)}")
            return color
            
        except Exception as e:
            print(f"DEBUG error: {e}")
            return None

    def _extract_color(self, text: str) -> Optional[str]:
        """Extrahiert einen Hex-Farbcode aus einem Text, robust gegenüber Whitespace."""
        if not text:
            return None
        
        # Suche nach # gefolgt von 6 oder 3 Hex-Ziffern
        match = re.search(r"(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})\b", text)
        if not match:
            return None
        
        raw = match.group(0)
        raw = raw.strip()
        
        # Stelle sicher, dass wir einen sauberen String haben
        if len(raw) == 4:  # 3-stellig
            r, g, b = raw[1], raw[2], raw[3]
            # Expandiere zu 6-stellig für QML-Kompatibilität
            expanded = f"#{r}{r}{g}{g}{b}{b}"
            return expanded.upper()
        
        if len(raw) == 7:  # 6-stellig
            return raw.upper()
        
        return None

    def create_project(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        return ProjectConfig.make_project(target)

    def move_entry(self, source: str, target_dir: str) -> bool:
        src = Path(source).expanduser().resolve()
        dst_dir = Path(target_dir).expanduser().resolve()
        if not src.exists():
            return False
        if not dst_dir.is_dir():
            return False
        if src == dst_dir or is_within(dst_dir, src):
            return False
        destination = dst_dir / src.name
        try:
            shutil.move(str(src), str(destination))
            return True
        except Exception:
            return False

    def open_markdown(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        opener = Path(__file__).resolve().parent / "bin" / "open_md.py"
        if not opener.exists():
            return False
        if os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}:
            print(f"[scope_api] open_markdown: {target}")
            print(f"[scope_api] opener: {opener}")
        result = subprocess.run(
            [sys.executable, str(opener), str(target)], check=False
        )
        if os.environ.get("MYOS_MD_DEBUG") in {"1", "true", "yes"}:
            print(f"[scope_api] returncode: {result.returncode}")
        return result.returncode == 0
