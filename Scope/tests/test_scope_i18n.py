"""Scope UI strings are English in the code (qsTr); German comes from i18n/scope_de.ts/.qm.

Run scripts/update_translations.py after changing strings, and translate new ones.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTranslator
from PySide6.QtGui import QGuiApplication

SCOPE = Path(__file__).resolve().parents[1]
TS = SCOPE / "i18n" / "scope_de.ts"
QM = SCOPE / "i18n" / "scope_de.qm"
QSTR = re.compile(r"""\bqsTr\(\s*(["'])((?:\\.|(?!\1).)*)\1""")


def _unescape(raw: str) -> str:
    """A QML/JS string literal's text, as lupdate stores it in the .ts."""
    return raw.encode("latin-1", "backslashreplace").decode("unicode_escape") if "\\" in raw else raw


def _messages():
    out = []
    for ctx in ET.parse(TS).getroot().iter("context"):
        name = ctx.find("name").text
        for msg in ctx.iter("message"):
            tr = msg.find("translation")
            out.append((name, msg.find("source").text, tr.text or "", tr.get("type") is None))
    return out


def _code_files():
    return [*SCOPE.glob("*.qml"), *(SCOPE / "Dialogs").glob("*.qml"), *(SCOPE / "js").glob("*.js")]


def test_every_string_in_the_code_has_a_german_translation():
    finished = {src for _, src, text, done in _messages() if done and text}
    in_code = set()
    for path in _code_files():
        in_code |= {_unescape(m.group(2)) for m in QSTR.finditer(path.read_text(encoding="utf-8"))}

    assert len(in_code) > 100  # the pattern still finds the strings
    missing = sorted(in_code - finished)
    assert not missing, f"untranslated (run scripts/update_translations.py scope): {missing}"


def test_compiled_translations_match_the_ts():
    QGuiApplication.instance() or QGuiApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))

    stale = [(c, s) for c, s, t, done in _messages() if done and translator.translate(c, s) != t]
    assert not stale, f"scope_de.qm is out of date (run scripts/update_translations.py scope): {stale}"


def test_examples_of_the_german_ui():
    QGuiApplication.instance() or QGuiApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))

    assert translator.translate("FilesPanel", "Size") == "Größe"
    assert translator.translate("FilesPanel", "Exceptions") == "Ausnahmen"
    assert translator.translate("SetupPage", "Projects") == "Projekte"  # the rows, on the back
