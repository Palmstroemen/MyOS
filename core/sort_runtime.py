#!/usr/bin/env python3
"""
sort_runtime.py - Classification, move engine, and organizer helpers.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from core.sort import SortRule, format_token

_TOKEN_RE = re.compile(r"\{\{([A-Z]+)\}\}")


class SortRuntime:
    def __init__(self) -> None:
        self._self_moves: dict[str, float] = {}
        self._debounce_by_root: dict[str, float] = {}
        self.self_move_ttl_s = 2.0
        self.root_debounce_s = 0.75

    def preview_target(self, file_path: Path, rules: Sequence[SortRule], *, event: str = "move") -> Dict[str, str]:
        chosen = self._choose_rule(file_path, rules, event=event)
        if chosen is None:
            return {"ok": "0", "reason": "no_rule", "target": ""}
        relative = self.classify(file_path, chosen)
        if not relative:
            return {"ok": "0", "reason": "classify_failed", "target": ""}
        absolute = chosen.root_path / relative
        return {"ok": "1", "reason": "resolved", "target": str(absolute), "ruleRoot": str(chosen.root_path)}

    def apply_file(self, file_path: Path, rules: Sequence[SortRule], *, event: str = "move") -> Dict[str, str]:
        source = Path(file_path).expanduser().resolve()
        if not source.exists() or not source.is_file():
            return {"ok": "0", "reason": "missing_file", "source": str(source)}
        if self.should_ignore_event(str(source)):
            return {"ok": "1", "reason": "ignored_self_move", "source": str(source)}
        chosen = self._choose_rule(source, rules, event=event)
        if chosen is None:
            return {"ok": "0", "reason": "no_rule", "source": str(source)}
        relative = self.classify(source, chosen)
        if not relative:
            return {"ok": "0", "reason": "classify_failed", "source": str(source)}
        target_dir = chosen.root_path / relative
        target_dir.mkdir(parents=True, exist_ok=True)
        destination = target_dir / source.name
        if destination == source:
            return {"ok": "1", "reason": "already_sorted", "source": str(source), "destination": str(destination)}
        if destination.exists():
            if chosen.conflict == "skip":
                return {"ok": "1", "reason": "conflict_skip", "source": str(source), "destination": str(destination)}
            if chosen.conflict == "error":
                return {"ok": "0", "reason": "conflict_error", "source": str(source), "destination": str(destination)}
            destination = self._find_rename_destination(destination)
        try:
            shutil.move(str(source), str(destination))
            self.mark_self_move(str(source), str(destination))
            return {"ok": "1", "reason": "moved", "source": str(source), "destination": str(destination)}
        except Exception:
            return {"ok": "0", "reason": "move_failed", "source": str(source), "destination": str(destination)}

    def apply_root(self, root_path: Path, rules: Sequence[SortRule], *, event: str = "move") -> Dict[str, object]:
        root = Path(root_path).expanduser().resolve()
        key = str(root)
        now = time.monotonic()
        if now - self._debounce_by_root.get(key, 0.0) < self.root_debounce_s:
            return {"ok": True, "reason": "debounced", "moved": [], "errors": []}
        self._debounce_by_root[key] = now
        moved: list[dict[str, str]] = []
        errors: list[dict[str, str]] = []
        if not root.exists() or not root.is_dir():
            return {"ok": False, "reason": "missing_root", "moved": moved, "errors": [{"path": str(root)}]}
        for entry in root.iterdir():
            if not entry.is_file():
                continue
            result = self.apply_file(entry, rules, event=event)
            if result.get("ok") == "1" and result.get("reason") == "moved":
                moved.append({"source": str(result.get("source") or ""), "destination": str(result.get("destination") or "")})
            elif result.get("ok") != "1":
                errors.append({"source": str(result.get("source") or ""), "reason": str(result.get("reason") or "error")})
        return {"ok": len(errors) == 0, "reason": "applied", "moved": moved, "errors": errors}

    def classify(self, file_path: Path, rule: SortRule) -> str:
        ts = self._resolve_datetime(file_path, rule.date_sources)
        if ts is None:
            ts = dt.datetime.fromtimestamp(file_path.stat().st_mtime)
        name = file_path.stem
        out = rule.pattern
        for match in _TOKEN_RE.finditer(rule.pattern):
            token = str(match.group(1) or "").strip().upper()
            replacement = format_token(token, ts, name)
            if not replacement:
                continue
            out = out.replace(f"{{{{{token}}}}}", replacement)
        segments = [s.strip() for s in out.split("/") if s.strip()]
        clean = [seg for seg in segments if seg not in {".", ".."} and "/" not in seg and "\\" not in seg]
        return "/".join(clean)

    def mark_self_move(self, source: str, destination: str) -> None:
        now = time.monotonic()
        self._self_moves[str(source)] = now
        self._self_moves[str(destination)] = now

    def should_ignore_event(self, path: str) -> bool:
        key = str(path)
        hit = self._self_moves.get(key)
        if hit is None:
            return False
        if time.monotonic() - hit <= self.self_move_ttl_s:
            return True
        self._self_moves.pop(key, None)
        return False

    def _choose_rule(self, file_path: Path, rules: Sequence[SortRule], *, event: str) -> Optional[SortRule]:
        for rule in rules:
            if not rule.enabled:
                continue
            if rule.apply_on != "both" and rule.apply_on != str(event):
                continue
            try:
                parent = file_path.parent.resolve()
                root_path = rule.root_path.resolve()
            except Exception:
                continue
            if parent == root_path:
                return rule
        return None

    def _resolve_datetime(self, file_path: Path, sources: Sequence[str]) -> Optional[dt.datetime]:
        for source in sources:
            key = str(source or "").strip().lower()
            if key == "fs_mtime":
                try:
                    return dt.datetime.fromtimestamp(file_path.stat().st_mtime)
                except Exception:
                    continue
            elif key == "fs_created":
                try:
                    return dt.datetime.fromtimestamp(file_path.stat().st_ctime)
                except Exception:
                    continue
            elif key == "frontmatter_date":
                resolved = self._frontmatter_datetime(file_path)
                if resolved is not None:
                    return resolved
            elif key == "exif_created":
                resolved = self._exif_datetime(file_path)
                if resolved is not None:
                    return resolved
        return None

    def _frontmatter_datetime(self, file_path: Path) -> Optional[dt.datetime]:
        if file_path.suffix.lower() not in {".md", ".markdown"}:
            return None
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
        if not text.startswith("---"):
            return None
        lines = text.splitlines()
        end_idx = -1
        for idx in range(1, min(len(lines), 40)):
            if lines[idx].strip() == "---":
                end_idx = idx
                break
        if end_idx < 0:
            return None
        for line in lines[1:end_idx]:
            raw = str(line or "").strip()
            if not raw or ":" not in raw:
                continue
            key, value = raw.split(":", 1)
            if str(key or "").strip().lower() not in {"date", "created", "created_at"}:
                continue
            parsed = self._parse_datetime_text(value.strip())
            if parsed is not None:
                return parsed
        return None

    def _exif_datetime(self, file_path: Path) -> Optional[dt.datetime]:
        # Lightweight MVP behavior: parse common date pattern from image names.
        name = file_path.stem
        match = re.search(r"(\d{4})[-_]?(\d{2})[-_]?(\d{2})", name)
        if not match:
            return None
        try:
            return dt.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except Exception:
            return None

    def _parse_datetime_text(self, value: str) -> Optional[dt.datetime]:
        text = str(value or "").strip().strip('"').strip("'")
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return dt.datetime.strptime(text, fmt)
            except ValueError:
                continue
        try:
            return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def _find_rename_destination(self, target: Path) -> Path:
        base = target.stem
        suffix = target.suffix
        parent = target.parent
        for idx in range(2, 5000):
            candidate = parent / f"{base} ({idx}){suffix}"
            if not candidate.exists():
                return candidate
        return parent / f"{base}-{int(time.time())}{suffix}"
