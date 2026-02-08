from __future__ import annotations

from pathlib import Path
from typing import List, Optional

try:
    from core.localBlueprintLayer import Blueprint
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
        self.project_root = find_project_root(self.start_path)
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

    def list_children(self, path: str) -> List[str]:
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

        if self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if name not in names:
                    names.append(name)
            names.sort()

        return names

    def list_entries(self, path: str) -> List[dict]:
        target = Path(path).expanduser().resolve()
        entries: List[dict] = []
        try:
            for child in sorted(target.iterdir()):
                entries.append({"name": child.name, "isDir": child.is_dir()})
        except Exception:
            return []

        if self.blueprint and self.project_root and is_within(target, self.project_root):
            rel = "" if target == self.project_root else str(target.relative_to(self.project_root))
            embryos = self.blueprint.get_embryos_at(rel)
            for name in embryos:
                if not any(item["name"] == name for item in entries):
                    entries.append({"name": name, "isDir": True})
            entries.sort(key=lambda item: item["name"])

        return entries

    def has_myos_dir(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        return (target / ".MyOS").is_dir()
