# filing.py - filing by date: flat, virtual, real (see "Designdocument Sort.md")
#
# A folder carries its rule in its own .MyOS/Sort.md (prepared in templates, copied along
# when the folder is born). A level of the pattern (year, month, ...) only becomes real
# when the level above holds more than NewLevelFrom files; before that it is only
# virtual - a grouping shown, nothing moves. Once a level folder exists, the level stays
# real, and new level folders are born when a file goes in (never empty, never ahead).
# Filing is idempotent: MyOS catches up whenever it looks (no watcher that can miss).

from __future__ import annotations

import datetime as dt
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Union

SORT_FILE = "Sort.md"
DATE_SOURCES = ("exif", "filename", "frontmatter", "modified")
DEFAULT_NEW_LEVEL_FROM = 20
_TOKEN_RE = re.compile(r"\{\{([A-Z]+)\}\}")
# token -> what a level folder name looks like there
_TOKEN_PATTERNS = {
    "YYYY": r"\d{4}",
    "YY": r"\d{2}",
    "MM": r"0[1-9]|1[0-2]",
    "MMMM": r"[^/]+",
    "DD": r"0[1-9]|[12]\d|3[01]",
    "ABC": r"[A-Z_]",
}
_DATE_TOKENS = {"YYYY", "YY", "MM", "MMMM", "DD"}
_FILENAME_DATE_RE = re.compile(r"(?<!\d)((?:19|20)\d{2})[-_.]?(\d{2})[-_.]?(\d{2})(?!\d)")


@dataclass(frozen=True)
class SortRule:
    folder: Path                    # the folder this rule sorts
    pattern: str                    # "{{YYYY}}/{{MM}}"
    date_sources: Tuple[str, ...]   # in this order, the first that gives a date wins
    new_level_from: int             # a level becomes real above this many files
    conflict: str = "rename"        # rename | skip | error
    enabled: bool = True

    @property
    def levels(self) -> List[str]:
        return self.pattern.split("/")


@dataclass
class FilingReport:
    moved: List[Tuple[Path, Path]] = field(default_factory=list)
    skipped: List[Tuple[Path, str]] = field(default_factory=list)


def read_rule(folder: Union[str, Path]) -> Optional[SortRule]:
    """The rule folder carries (.MyOS/Sort.md), or None: none there, not inside a project,
    or not usable (unknown token, '..', an absolute path, a date token twice)."""
    folder = Path(folder).expanduser().resolve()
    sort_file = folder / ".MyOS" / SORT_FILE
    # Security: a symlinked rule could make files go elsewhere.
    if sort_file.is_symlink() or not sort_file.is_file():
        return None
    if not any((p / ".MyOS" / "Project.md").is_file() for p in [folder, *folder.parents]):
        return None
    try:
        values = _sort_section(sort_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    pattern = _checked_pattern(values.get("pattern", ""))
    if pattern is None:
        return None
    sources = tuple(s for s in (v.strip().lower() for v in values.get("datesource", "").split(","))
                    if s in DATE_SOURCES) or DATE_SOURCES
    try:
        threshold = int(re.match(r"\s*(\d+)", values.get("newlevelfrom", "")).group(1))
    except (AttributeError, ValueError):
        threshold = DEFAULT_NEW_LEVEL_FROM
    conflict = values.get("conflict", "rename").strip().lower()
    return SortRule(
        folder=folder,
        pattern=pattern,
        date_sources=sources,
        new_level_from=threshold,
        conflict=conflict if conflict in ("rename", "skip", "error") else "rename",
        enabled=values.get("enabled", "true").strip().lower() not in ("false", "no", "0", "off"),
    )


def date_of(path: Path, sources: Tuple[str, ...]) -> Optional[dt.datetime]:
    """The date of a file from the first of sources that has one."""
    for source in sources:
        found = {
            "exif": _exif_date,
            "filename": _filename_date,
            "frontmatter": _frontmatter_date,
            "modified": _modified_date,
        }[source](path)
        if found is not None:
            return found
    return None


def file_due(folder: Union[str, Path], may_write: Optional[Callable[[Path], bool]] = None) -> FilingReport:
    """File what is due in folder by its rule (idempotent). may_write(path) says whether
    a file may be moved from / a folder written to (the caller's ACL check)."""
    report = FilingReport()
    rule = read_rule(folder)
    if rule is not None and rule.enabled:
        _file_level(rule.folder, rule, 0, report, may_write or (lambda path: True))
    return report


def virtual_groups(folder: Union[str, Path]) -> Dict[str, List[Path]]:
    """The virtual folders of folder: its loose files grouped by the next level of the
    rule above it - {} where that level is real (or no rule applies)."""
    folder = Path(folder).expanduser().resolve()
    found = _rule_and_level(folder)
    if found is None:
        return {}
    rule, level = found
    if level >= len(rule.levels) or _is_real(folder, rule, level):
        return {}
    groups: Dict[str, List[Path]] = {}
    for path in _loose_files(folder):
        name = _level_name(rule, level, path)
        if name:
            groups.setdefault(name, []).append(path)
    return groups


@dataclass
class VirtualView:
    """Inside a virtual folder: its virtual subfolders (next level) or, at the last level,
    the files that would lie there."""
    groups: Dict[str, List[Path]]
    files: List[Path]


def sorted_folder_for(path: Union[str, Path]) -> Optional[Path]:
    """The folder carrying the rule that sorts path (path itself or a level folder in it)."""
    found = _rule_and_level(Path(path).expanduser().resolve())
    return found[0].folder if found is not None else None


def sorted_folders(root: Union[str, Path]) -> List[Path]:
    """All folders with a rule at or below root (hidden folders are not searched)."""
    found = []
    for current, dirs, _files in os.walk(Path(root).expanduser().resolve()):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))
        if read_rule(current) is not None:
            found.append(Path(current))
    return sorted(found)


def destination_for(path: Path, folder: Union[str, Path]) -> Path:
    """Where a file put into folder now would be filed (folder itself when it stays)."""
    current = Path(folder).expanduser().resolve()
    found = _rule_and_level(current)
    if found is None:
        return current
    rule, level = found
    while level < len(rule.levels):
        level_folders = _level_folders(current, rule, level)
        if not level_folders and len(_loose_files(current)) + 1 <= rule.new_level_from:
            break
        name = _level_name(rule, level, path)
        if not name:
            break
        current = current / name
        level += 1
        if not current.is_dir():
            break  # born for this file: alone in it, no deeper level yet
    return current


def virtual_listing(path: Union[str, Path]) -> Optional[VirtualView]:
    """The content of a virtual folder (a level name below a sorted folder whose level is
    not real), or None when path is no virtual folder with content."""
    path = Path(path).expanduser()
    existing, parts = path, []
    while not existing.exists():
        if existing == existing.parent:
            return None
        parts.insert(0, existing.name)
        existing = existing.parent
    if not parts:
        return None
    found = _rule_and_level(existing.resolve())
    if found is None:
        return None
    rule, level = found
    if level + len(parts) > len(rule.levels) or _is_real(existing, rule, level):
        return None
    files = [f for f in _loose_files(existing)
             if all(_level_name(rule, level + i, f) == part for i, part in enumerate(parts))]
    if not files:
        return None
    depth = level + len(parts)
    if depth >= len(rule.levels):
        return VirtualView(groups={}, files=files)
    groups: Dict[str, List[Path]] = {}
    for f in files:
        groups.setdefault(_level_name(rule, depth, f), []).append(f)
    return VirtualView(groups=groups, files=[])


def _file_level(folder: Path, rule: SortRule, level: int, report: FilingReport,
                may_write: Callable[[Path], bool]) -> None:
    if level >= len(rule.levels) or not _is_real(folder, rule, level):
        return
    for path in _loose_files(folder):
        name = _level_name(rule, level, path)
        if not name:
            report.skipped.append((path, "no_date"))
            continue
        target_dir = folder / name
        # Security: never move what the user may not write, nor into where they may not.
        if not may_write(path) or not may_write(target_dir):
            report.skipped.append((path, "permission"))
            continue
        destination = target_dir / path.name
        if destination.exists():
            if rule.conflict == "skip":
                report.skipped.append((path, "exists"))
                continue
            if rule.conflict == "error":
                report.skipped.append((path, "conflict"))
                continue
            destination = _free_name(destination)
        target_dir.mkdir(exist_ok=True)
        shutil.move(str(path), str(destination))
        report.moved.append((path, destination))
    for level_folder in _level_folders(folder, rule, level):
        _file_level(level_folder, rule, level + 1, report, may_write)


def _is_real(folder: Path, rule: SortRule, level: int) -> bool:
    """A level is real once a folder of it exists or when the folder holds more files
    than the rule's threshold."""
    level_folders = _level_folders(folder, rule, level)
    if level_folders:
        return True
    return len(_loose_files(folder)) > rule.new_level_from


def _loose_files(folder: Path) -> List[Path]:
    """Files lying directly in folder (hidden ones and symlinks not)."""
    try:
        items = sorted(folder.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []
    return [p for p in items if not p.name.startswith(".") and not p.is_symlink() and p.is_file()]


def _level_folders(folder: Path, rule: SortRule, level: int) -> List[Path]:
    matcher = _level_matcher(rule.levels[level])
    try:
        items = sorted(folder.iterdir(), key=lambda p: p.name)
    except OSError:
        return []
    return [p for p in items if not p.is_symlink() and p.is_dir() and matcher.fullmatch(p.name)]


def _level_matcher(segment: str) -> re.Pattern:
    parts, last = [], 0
    for match in _TOKEN_RE.finditer(segment):
        parts.append(re.escape(segment[last:match.start()]))
        parts.append(f"(?:{_TOKEN_PATTERNS[match.group(1)]})")
        last = match.end()
    parts.append(re.escape(segment[last:]))
    return re.compile("".join(parts))


def _level_name(rule: SortRule, level: int, path: Path) -> str:
    when = date_of(path, rule.date_sources)
    segment = rule.levels[level]
    if when is None and any(t in _DATE_TOKENS for t in _TOKEN_RE.findall(segment)):
        return ""
    return _TOKEN_RE.sub(lambda m: _format_token(m.group(1), when, path.stem), segment)


def _format_token(token: str, when: Optional[dt.datetime], stem: str) -> str:
    if token == "ABC":
        letter = (stem.strip()[:1] or "_").upper()
        return letter if "A" <= letter <= "Z" else "_"
    return {
        "YYYY": f"{when.year:04d}",
        "YY": f"{when.year % 100:02d}",
        "MM": f"{when.month:02d}",
        "MMMM": when.strftime("%B"),
        "DD": f"{when.day:02d}",
    }[token]


def _rule_and_level(folder: Path) -> Optional[Tuple[SortRule, int]]:
    """The rule sorting folder and the level folder stands at: the folder carrying the
    rule is level 0, its year folders level 1, and so on."""
    parts: List[str] = []
    current = folder
    while True:
        rule = read_rule(current)
        if rule is not None:
            levels = rule.levels
            if len(parts) > len(levels):
                return None
            for index, name in enumerate(reversed(parts)):
                if not _level_matcher(levels[index]).fullmatch(name):
                    return None
            return rule, len(parts)
        if current == current.parent or len(parts) > 8:
            return None
        parts.append(current.name)
        current = current.parent


def _free_name(destination: Path) -> Path:
    number = 2
    while True:
        candidate = destination.with_name(f"{destination.stem} ({number}){destination.suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def _sort_section(text: str) -> Dict[str, str]:
    """'key: value' lines of the '# Sort' section (lower-case keys; ' # notes' cut off)."""
    values: Dict[str, str] = {}
    inside = False
    for line in re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and ": " not in stripped:
            inside = stripped.lstrip("#").strip().lower() == "sort"
            continue
        key, sep, value = stripped.partition(":")
        if inside and sep and key.strip():
            values[key.strip().lower()] = re.split(r"\s#", value, maxsplit=1)[0].strip()
    return values


def _checked_pattern(pattern: str) -> Optional[str]:
    pattern = pattern.strip()
    # Security: folders are only created inside the sorted folder.
    if not pattern or pattern.startswith("/") or "\\" in pattern:
        return None
    segments = pattern.split("/")
    seen: List[str] = []
    for segment in segments:
        tokens = _TOKEN_RE.findall(segment)
        if not tokens or segment in (".", "..") or ".." in segment:
            return None
        for token in tokens:
            if token not in _TOKEN_PATTERNS or (token in _DATE_TOKENS and token in seen):
                return None
            seen.append(token)
    return pattern


def _filename_date(path: Path) -> Optional[dt.datetime]:
    for match in _FILENAME_DATE_RE.finditer(path.name):
        try:
            return dt.datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            continue
    return None


def _frontmatter_date(path: Path) -> Optional[dt.datetime]:
    if path.suffix.lower() not in (".md", ".markdown"):
        return None
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:40]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() in ("date", "created", "created_at"):
            text = value.strip().strip("'\"")
            try:
                return dt.datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                continue
    return None


def _exif_date(path: Path) -> Optional[dt.datetime]:
    """The recording date of a photo (EXIF DateTimeOriginal, else DateTime)."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            try:
                detail = exif.get_ifd(0x8769)  # the Exif IFD holds DateTimeOriginal
            except Exception:
                detail = {}
            raw = detail.get(0x9003) or exif.get(0x9003) or exif.get(0x0132)
    except Exception:  # not an image, or one Pillow cannot read
        return None
    try:
        return dt.datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S") if raw else None
    except ValueError:
        return None


def _modified_date(path: Path) -> Optional[dt.datetime]:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None
