"""A note changed from outside while it is open in PostFix: the two versions are merged line by
line against the version both started from (three-way merge), so a moved window (PostFix keeps
the window's place in the note) and a paragraph added elsewhere both survive. Only where both
changed the same lines differently is it a conflict; then nothing is lost: the file keeps the
version from outside and PostFix's own lies beside it (conflict_copy_path).
"""

from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Tuple

Hunk = Tuple[int, int, List[str]]  # base lines [start, end) replaced by these lines


def _hunks(base: List[str], other: List[str]) -> List[Hunk]:
    matcher = SequenceMatcher(None, base, other, autojunk=False)
    return [(i1, i2, other[j1:j2]) for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]


def _overlap(a: Hunk, b: Hunk) -> bool:
    # Two changes touch the same lines, or both insert at the same place.
    return (a[0] < b[1] and b[0] < a[1]) or a[0] == b[0]


def _apply(base: List[str], start: int, end: int, hunks: List[Hunk]) -> List[str]:
    """base[start:end] with the hunks (all inside it, in order) applied."""
    out, pos = [], start
    for i1, i2, lines in hunks:
        out.extend(base[pos:i1])
        out.extend(lines)
        pos = i2
    out.extend(base[pos:end])
    return out


def merge3(base: str, mine: str, theirs: str) -> Tuple[str, bool]:
    """mine and theirs, both changed from base, as one text, and whether they conflict (both
    changed the same lines differently; the text then holds theirs there)."""
    if mine == theirs or theirs == base:
        return mine, False
    if mine == base:
        return theirs, False
    base_lines = base.splitlines(keepends=True)
    tagged = sorted([(h, "mine") for h in _hunks(base_lines, mine.splitlines(keepends=True))]
                    + [(h, "theirs") for h in _hunks(base_lines, theirs.splitlines(keepends=True))],
                    key=lambda item: (item[0][0], item[0][1]))
    # Changes that touch each other form one cluster; clusters are merged one by one.
    clusters: List[List[Tuple[Hunk, str]]] = []
    for item in tagged:
        if clusters and any(_overlap(item[0], other[0]) for other in clusters[-1]):
            clusters[-1].append(item)
        else:
            clusters.append([item])
    out: List[str] = []
    pos, conflict = 0, False
    for cluster in clusters:
        start = min(h[0] for h, _ in cluster)
        end = max(h[1] for h, _ in cluster)
        out.extend(base_lines[pos:start])
        mine_part = _apply(base_lines, start, end, [h for h, side in cluster if side == "mine"])
        theirs_part = _apply(base_lines, start, end, [h for h, side in cluster if side == "theirs"])
        sides = {side for _h, side in cluster}
        if sides == {"mine"}:
            out.extend(mine_part)
        elif sides == {"theirs"} or mine_part == theirs_part:
            out.extend(theirs_part)
        else:
            conflict = True
            out.extend(theirs_part)
        pos = end
    out.extend(base_lines[pos:])
    return "".join(out), conflict


def conflict_copy_path(note: Path) -> Path:
    """Where PostFix's own version goes in a conflict: beside the note, never over a file."""
    note = Path(note)
    candidate = note.with_name(f"{note.stem} (Konflikt){note.suffix}")
    number = 2
    while candidate.exists():
        candidate = note.with_name(f"{note.stem} (Konflikt {number}){note.suffix}")
        number += 1
    return candidate
