# template_place.py - where a project's templates live
#
# Templates are system settings like ACLs.md: they live in <project>/.MyOS/Templates/<name>/.
# The nearest .MyOS/Templates above a path wins as a whole (a subproject with templates of
# its own does not mix them with its parent's). A plain Templates/ folder is never taken:
# ~/Templates (XDG), a cloud's own Templates folder and the like are not MyOS'.
# MYOS_TEMPLATES_DIR overrides the search (one set for all projects).

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

TEMPLATES_REL = Path(".MyOS") / "Templates"


def find_templates_dir(start) -> Optional[Path]:
    """The templates folder that serves start (a project or anything in it), or None."""
    env_dir = os.environ.get("MYOS_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    current = Path(start).expanduser().resolve()
    for folder in (current, *current.parents):
        candidate = folder / TEMPLATES_REL
        if candidate.is_dir():
            return candidate
    return None
