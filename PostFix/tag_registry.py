"""Tag registry and scope tag utilities for PostFix."""

import json
from pathlib import Path

from PySide6.QtGui import QColor


def find_vault_root(file_path: Path | None) -> Path | None:
    if not file_path:
        return None
    start = file_path if file_path.is_dir() else file_path.parent
    for parent in [start, *start.parents]:
        if (parent / "app.json").exists() or (parent / ".obsidian" / "app.json").exists() or (parent / ".obsidian").exists():
            return parent
    return None


def parse_scope_tags(tags_md_path: Path) -> list[str]:
    try:
        content = tags_md_path.read_text(encoding="utf-8")
    except OSError:
        return []
    tags = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.lower() == "# tags":
            continue
        if line.startswith("#"):
            tag = line[1:].strip()
            if tag:
                tags.append(tag)
    return tags


def write_scope_tags(tags_md_path: Path, tags: list[str]) -> bool:
    cleaned = [str(t).strip().lstrip("#") for t in (tags or []) if str(t).strip().lstrip("#")]
    unique = list(dict.fromkeys(cleaned))
    content = "# Tags\n" + "\n".join(f"#{tag}" for tag in unique) + ("\n" if unique else "")
    try:
        tags_md_path.parent.mkdir(parents=True, exist_ok=True)
        tags_md_path.write_text(content, encoding="utf-8")
        return True
    except OSError:
        return False


def load_tag_registry(path: Path | None) -> dict:
    if not path or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_tag_registry(path: Path | None, data: dict) -> bool:
    if not path:
        return False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def flatten_tag_colors(app_json_data: dict) -> dict[str, str]:
    root = app_json_data if isinstance(app_json_data, dict) else {}
    plugin = root.get("colored-tags-wrangler", {})
    entries = plugin.get("tags", []) if isinstance(plugin, dict) else []
    mapping = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        names_raw = str(entry.get("name", ""))
        color = str(entry.get("color", "")).strip()
        if not color:
            continue
        for tag in [p.strip() for p in names_raw.split(";") if p.strip()]:
            mapping[tag] = color
    return mapping


def lighten_hex(color_hex: str, factor: float = 0.72) -> str:
    color = QColor(color_hex)
    if not color.isValid():
        return color_hex
    r = int(color.red() + (255 - color.red()) * factor)
    g = int(color.green() + (255 - color.green()) * factor)
    b = int(color.blue() + (255 - color.blue()) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def assign_tag_color_in_registry(app_json_data: dict, tag: str, color_hex: str) -> bool:
    if not tag:
        return False
    root = app_json_data if isinstance(app_json_data, dict) else {}
    plugin = root.setdefault("colored-tags-wrangler", {})
    if not isinstance(plugin, dict):
        plugin = {}
        root["colored-tags-wrangler"] = plugin
    entries = plugin.setdefault("tags", [])
    if not isinstance(entries, list):
        entries = []
        plugin["tags"] = entries
    settings = plugin.setdefault("settings", {})
    if not isinstance(settings, dict):
        settings = {}
        plugin["settings"] = settings
    separate_background = bool(settings.get("separateBackground", True))

    target_idx = None
    target_names = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        names = [p.strip() for p in str(entry.get("name", "")).split(";") if p.strip()]
        if tag in names:
            target_idx = idx
            target_names = names
            break

    if target_idx is None:
        new_entry = {"name": tag, "color": color_hex, "luminanceOffset": 15}
        if separate_background:
            new_entry["background"] = lighten_hex(color_hex)
        entries.append(new_entry)
        return True

    entry = entries[target_idx]
    if len(target_names) <= 1:
        entry["color"] = color_hex
        if separate_background:
            entry["background"] = lighten_hex(color_hex)
        elif "background" in entry:
            entry.pop("background", None)
        return True

    remaining = [n for n in target_names if n != tag]
    entry["name"] = ";".join(remaining)
    new_entry = {"name": tag, "color": color_hex, "luminanceOffset": int(entry.get("luminanceOffset", 15))}
    if separate_background:
        new_entry["background"] = lighten_hex(color_hex)
    entries.append(new_entry)
    return True
