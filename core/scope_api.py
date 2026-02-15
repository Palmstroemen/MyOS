from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import re
import shutil
from typing import List, Optional, Dict, Any
from core.tags import read_tags

try:
    from core.localBlueprintLayer import Blueprint
    from core.project import ProjectConfig, notify_config_changed as notify_project_config_changed
except Exception:  # pragma: no cover - optional for non-MyOS paths
    Blueprint = None
    notify_project_config_changed = None


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


def _read_markdown_tag_list(path: Path) -> List[str]:
    if not path.exists():
        return []
    tags: List[str] = []
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line.startswith("#"):
                continue
            tag = line.lstrip("#").strip()
            if tag:
                tags.append(tag)
    except Exception:
        return []
    return sorted(set(tags), key=str.lower)


def _split_stem_and_ext(name: str) -> tuple[str, str]:
    file_name = str(name or "")
    dot = file_name.rfind(".")
    if dot <= 0:
        return file_name, ""
    return file_name[:dot], file_name[dot:]


def _longest_common_prefix(values: List[str]) -> str:
    if not values:
        return ""
    prefix = str(values[0] or "")
    for current in values[1:]:
        text = str(current or "")
        while prefix and not text.startswith(prefix):
            prefix = prefix[:-1]
        if not prefix:
            break
    return prefix


def _clean_entry_name(name: str, *, allow_empty: bool = False) -> Optional[str]:
    cleaned = str(name or "").strip()
    if not cleaned:
        return "" if allow_empty else None
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        return None
    return cleaned


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
        target = self._resolve_path(path)
        root = find_project_root(target)
        if root != self.project_root:
            self._set_project_root(root)

    def _resolve_path(self, path: str) -> Path:
        return Path(path).expanduser().resolve()

    def _resolve_dir(self, path: str) -> Optional[Path]:
        target = self._resolve_path(path)
        return target if target.is_dir() else None

    def list_children(self, path: str, include_embryos: bool = True) -> List[Dict[str, Any]]:
        target = self._resolve_dir(path)
        if target is None:
            return []
        entries: List[Dict[str, Any]] = []
        parent_color = self._resolve_project_color(target)
        try:
            for child in sorted(target.iterdir()):
                if child.name.startswith("."):
                    continue
                if child.is_dir():
                    is_project = self.is_project(str(child))
                    project_color = self._resolve_direct_project_color(child) if is_project else None
                    entries.append(
                        {
                            "name": child.name,
                            "isProject": is_project,
                            "isEmbryo": False,
                            "color": project_color,
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
        target = self._resolve_dir(path)
        if target is None:
            return []
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
        target = self._resolve_dir(path)
        if target is None:
            return []
        entries: List[dict] = []
        try:
            for child in sorted(target.iterdir()):
                is_dir = child.is_dir()
                entry_tags = self._read_entry_tags(child)
                entry = {
                    "name": child.name,
                    "isDir": is_dir,
                    "path": str(child),
                    "tags": entry_tags,
                }
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
                            "tags": [],
                        }
                    )
        # File-browser style order: folders first, then files, both alphabetic.
        entries.sort(key=lambda item: (not bool(item.get("isDir")), str(item.get("name", "")).lower()))

        return entries

    def list_entries_filtered(self, path: str, tags: List[str], match_all: bool = False) -> List[dict]:
        selected = [str(tag or "").strip() for tag in (tags or [])]
        selected = [tag for tag in selected if tag]
        if not selected:
            return self.list_entries(path)

        selected_set = set(selected)
        filtered: List[dict] = []
        for entry in self.list_entries(path):
            entry_tags = set(entry.get("tags") or [])
            if not entry_tags:
                continue
            if match_all:
                if selected_set.issubset(entry_tags):
                    filtered.append(entry)
            else:
                if entry_tags.intersection(selected_set):
                    filtered.append(entry)
        return filtered

    def list_project_tags(self, path: str) -> List[str]:
        target = self._resolve_path(path)
        root = find_project_root(target)
        if not root:
            return []
        tags_file = root / ".MyOS" / "Tags.md"
        return _read_markdown_tag_list(tags_file)

    def _read_entry_tags(self, entry_path: Path) -> List[str]:
        tags: List[str] = []
        if entry_path.is_dir():
            # Directory tags live in a sidecar and do NOT imply "project".
            tags.extend(_read_markdown_tag_list(entry_path / ".MyOS" / "myTags.md"))
        try:
            tags_map = read_tags(entry_path)
        except Exception:
            tags_map = {}
        tags.extend(str(tag).strip() for tag in tags_map.keys())
        tags = [tag for tag in tags if tag]
        return sorted(set(tags), key=str.lower)

    def has_myos_dir(self, path: str) -> bool:
        target = self._resolve_path(path)
        return (target / ".MyOS").is_dir()

    def is_project(self, path: str) -> bool:
        target = self._resolve_path(path)
        return (target / ".MyOS" / "Project.md").is_file()

    def is_dir(self, path: str) -> bool:
        target = self._resolve_path(path)
        return target.is_dir()

    def get_project_color(self, path: str) -> Optional[str]:
        target = self._resolve_path(path)
        return self._resolve_direct_project_color(target)

    def _resolve_direct_project_color(self, path: Path) -> Optional[str]:
        return self._read_first_color(path, [".MyOS/Color.md", ".MyOS/Project.md"])

    def _resolve_project_color(self, path: Path) -> Optional[str]:
        if not self.project_root:
            return None
        cache_key = str(path)
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]
        color = self._find_first_color_upwards(
            path,
            self.project_root,
            [".MyOS/Color.md", ".MyOS/Project.md"],
        )
        if color:
            self._color_cache[cache_key] = color
            return color
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
        return self._find_first_color_upwards(start, stop, [".MyOS/Color.md", "Color.md"])

    def _read_first_color(self, base: Path, relative_paths: List[str]) -> Optional[str]:
        for rel in relative_paths:
            color = self._read_color_file(base / rel)
            if color:
                return color
        return None

    def _find_first_color_upwards(self, start: Path, stop: Path, relative_paths: List[str]) -> Optional[str]:
        current = start
        while True:
            color = self._read_first_color(current, relative_paths)
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
            color = self._extract_color(content)
            return color

        except Exception:
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

    def create_folder(self, path: str, name: str) -> Optional[str]:
        base = self._resolve_dir(path)
        if base is None:
            return None
        cleaned = _clean_entry_name(name)
        if cleaned is None:
            return None
        target = base / cleaned
        if target.exists():
            return None
        try:
            target.mkdir(parents=False, exist_ok=False)
        except Exception:
            return None
        return str(target)

    def create_note(self, path: str, name: str) -> Optional[str]:
        base = self._resolve_dir(path)
        if base is None:
            return None

        cleaned = _clean_entry_name(name, allow_empty=True)
        if cleaned is None:
            return None
        if not cleaned:
            cleaned = "New Note"
        if not cleaned.lower().endswith(".md"):
            cleaned = f"{cleaned}.md"

        target = base / cleaned
        if target.exists():
            stem = target.stem
            suffix = target.suffix or ".md"
            for idx in range(2, 200):
                candidate = base / f"{stem} {idx}{suffix}"
                if not candidate.exists():
                    target = candidate
                    break
            else:
                return None
        try:
            title = target.stem.strip() or "New Note"
            target.write_text(f"# {title}\n\n", encoding="utf-8")
        except Exception:
            return None
        return str(target)

    def rename_entry(self, path: str, new_name: str) -> Optional[str]:
        source = self._resolve_path(path)
        if not source.exists():
            return None
        return self._rename_one(source, new_name)

    def _rename_one(self, source: Path, target_name: str) -> Optional[str]:
        cleaned = _clean_entry_name(target_name)
        if cleaned is None:
            return None

        resolved_target_name = cleaned
        if source.is_file() and "." not in cleaned and source.suffix:
            resolved_target_name = f"{cleaned}{source.suffix}"
        target = source.with_name(resolved_target_name)
        if target == source:
            return str(source)
        if target.exists():
            return None
        try:
            source.rename(target)
        except Exception:
            return None
        return str(target)

    def _iter_unique_sources(self, values: List[str]):
        seen: set[str] = set()
        for raw in (values or []):
            source_text = str(raw or "").strip()
            if not source_text:
                continue
            source = Path(source_text).expanduser().resolve()
            source_key = str(source)
            duplicate = source_key in seen
            if not duplicate:
                seen.add(source_key)
            yield source, source_key, duplicate

    def _prepare_move(self, source: Path, target_dir: Path):
        source_key = str(source)
        if not source.exists():
            return {"status": "error", "reason": "source_missing", "source": source_key}
        if source == target_dir:
            return {"status": "skip", "reason": "same_as_target", "source": source_key}
        if is_within(target_dir, source):
            return {"status": "error", "reason": "target_inside_source", "source": source_key}
        destination = target_dir / source.name
        if destination.exists():
            return {
                "status": "error",
                "reason": "destination_exists",
                "source": source_key,
                "destination": str(destination),
            }
        return {
            "status": "ok",
            "source": source_key,
            "destination": destination,
        }

    def rename_entries_batch(self, paths: List[str], replace_from: str, replace_to: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": True,
            "renamed": [],
            "unchanged": 0,
            "failed": 0,
            "errors": [],
        }
        token_from = str(replace_from or "")
        token_to = str(replace_to or "")
        if token_from == "":
            result["ok"] = False
            result["errors"].append({"source": "", "reason": "missing_replace_from"})
            return result

        for source, source_key, duplicate in self._iter_unique_sources(paths):
            if duplicate:
                continue

            if not source.exists():
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "source_missing"})
                continue
            if source.is_dir():
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "unsupported_type"})
                continue

            stem = source.stem
            suffix = source.suffix
            new_stem = stem.replace(token_from, token_to)
            if new_stem == stem:
                result["unchanged"] += 1
                continue

            first_target = f"{new_stem}{suffix}"
            renamed = self._rename_one(source, first_target)
            if not renamed:
                for idx in range(1, 1000):
                    candidate = f"{new_stem}({idx}){suffix}"
                    renamed = self._rename_one(source, candidate)
                    if renamed:
                        break
            if renamed:
                result["renamed"].append(renamed)
            else:
                result["failed"] += 1
                result["errors"].append({"source": source_key, "reason": "rename_failed"})

        result["ok"] = result["failed"] == 0
        return result

    def suggest_batch_rename_token(self, paths: List[str]) -> str:
        stems: List[str] = []
        for source, _, duplicate in self._iter_unique_sources(paths):
            if duplicate:
                continue
            stem, _ = _split_stem_and_ext(source.name)
            stems.append(str(stem or ""))

        prefix = _longest_common_prefix(stems)
        while len(prefix) > 1 and prefix[-1] in "0123456789_- ":
            prefix = prefix[:-1]
        if prefix:
            return prefix
        return stems[0] if stems else ""

    def delete_entries(self, paths: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {"ok": True, "deleted": [], "errors": []}
        for source, key, duplicate in self._iter_unique_sources(paths):
            if duplicate:
                continue
            if not source.exists():
                result["errors"].append({"source": key, "reason": "missing"})
                continue
            try:
                if source.is_dir():
                    shutil.rmtree(source)
                else:
                    source.unlink()
                result["deleted"].append(key)
            except Exception:
                result["errors"].append({"source": key, "reason": "delete_failed"})
        result["ok"] = len(result["errors"]) == 0
        return result

    def move_entry(self, source: str, target_dir: str) -> bool:
        src = self._resolve_path(source)
        dst_dir = self._resolve_dir(target_dir)
        if dst_dir is None:
            return False
        if not dst_dir.is_dir():
            return False
        move_plan = self._prepare_move(src, dst_dir)
        if move_plan.get("status") != "ok":
            return False
        destination = move_plan["destination"]
        try:
            shutil.move(str(src), str(destination))
            return True
        except Exception:
            return False

    def move_entries(self, sources: List[str], target_dir: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "ok": True,
            "moved": [],
            "skipped": [],
            "errors": [],
        }
        dst_dir = self._resolve_path(target_dir)
        if not dst_dir.is_dir():
            result["ok"] = False
            result["errors"].append({"source": "", "reason": "target_not_directory", "target": str(dst_dir)})
            return result

        for src, src_key, duplicate in self._iter_unique_sources(sources):
            if duplicate:
                result["skipped"].append({"source": src_key, "reason": "duplicate_source"})
                continue

            move_plan = self._prepare_move(src, dst_dir)
            status = move_plan.get("status")
            if status == "skip":
                result["skipped"].append({"source": src_key, "reason": move_plan["reason"]})
                continue
            if status != "ok":
                error_item = {"source": src_key, "reason": move_plan["reason"]}
                if "destination" in move_plan:
                    error_item["destination"] = move_plan["destination"]
                result["errors"].append(error_item)
                continue

            destination = move_plan["destination"]
            try:
                shutil.move(str(src), str(destination))
                result["moved"].append({"source": src_key, "destination": str(destination)})
            except Exception:
                result["errors"].append({"source": src_key, "reason": "move_failed"})

        result["ok"] = len(result["errors"]) == 0
        return result

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

    def notify_config_changed(self, path: str) -> bool:
        target = Path(path).expanduser().resolve()
        if notify_project_config_changed is None:
            return False
        try:
            result = notify_project_config_changed(target, dry_run=False)
            return bool(result.get("ok"))
        except Exception:
            return False
