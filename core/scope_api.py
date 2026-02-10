from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
from typing import List, Optional

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
        self._set_project_root(find_project_root(self.start_path))

    def _set_project_root(self, root: Optional[Path]) -> None:
        self.project_root = root
        self.blueprint = None
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

    def list_children(self, path: str, include_embryos: bool = True) -> List[str]:
        target = Path(path).expanduser().resolve()
        names: List[str] = []
        try:
            for child in sorted(target.iterdir()):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    names.append(child.name)
        except Exception:
            return []

        if include_embryos and self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if name not in names:
                    names.append(name)
            names.sort()

        return names

    def list_templates(self, path: str, include_embryos: bool = True) -> List[str]:
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
            result = sorted(self.blueprint.get_embryos_at(rel))
            if debug:
                print(
                    f"[scope_api] list_templates: rel='{rel}' templates={self.blueprint.template_names} "
                    f"result={result}"
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

    def create_project(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        return ProjectConfig.make_project(target)

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
