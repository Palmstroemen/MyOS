"""The colour schemes of MyOS's programs (Scope/Designdocument Setup.md, step 2).

A scheme is a file in core/schemes, one colour per name; the programs say where each name is used.
"""

import json
from pathlib import Path
from typing import Dict

SCHEMES_DIR = Path(__file__).with_name("schemes")


def load_scheme(name: str) -> Dict[str, str]:
    return json.loads((SCHEMES_DIR / f"{name}.json").read_text(encoding="utf-8"))
