#!/usr/bin/env python3
"""
Update the UI translations of Scope, PostFix and SunTree.

Source strings in the code (qsTr / tr) are English; every other language is a
translation in <app>/i18n/<app>_<lang>.ts. This script extracts the strings from the code
into the .ts files (existing translations are kept, new strings come in as "unfinished")
and compiles the .qm files the apps load. Translate unfinished strings in the .ts
(e.g. with Qt Linguist) and run it again.

    python3 scripts/update_translations.py [scope|postfix|suntree ...]
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# app -> (source files relative to the repo, languages translated to)
APPS = {
    "scope": (["Scope/*.qml", "Scope/Dialogs/*.qml", "Scope/js/*.js"], ["de"]),
    "postfix": (["PostFix/*.py"], ["de"]),
    "suntree": (["SunTree/*.qml", "SunTree/js/*.js"], ["de"]),
}


def sources(patterns):
    files = []
    for pattern in patterns:
        files.extend(sorted(REPO_ROOT.glob(pattern)))
    return [str(f) for f in files]


def update(app: str) -> None:
    patterns, languages = APPS[app]
    i18n = REPO_ROOT / app_dir(app) / "i18n"
    for lang in languages:
        ts = i18n / f"{app}_{lang}.ts"
        qm = ts.with_suffix(".qm")
        subprocess.run(["pyside6-lupdate", *sources(patterns), "-no-obsolete", "-ts", str(ts)], check=True)
        subprocess.run(["pyside6-lrelease", str(ts), "-qm", str(qm)], check=True)


def app_dir(app: str) -> str:
    return {"scope": "Scope", "postfix": "PostFix", "suntree": "SunTree"}[app]


def main(argv) -> int:
    apps = argv[1:] or list(APPS)
    for app in apps:
        if app not in APPS:
            print(f"unknown app {app!r}; known: {', '.join(APPS)}", file=sys.stderr)
            return 2
        update(app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
