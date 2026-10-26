"""SunTree's UI strings are English in the code (qsTr); German comes from
i18n/suntree_de.ts/.qm, as in Scope.

Run scripts/update_translations.py suntree after changing strings, and translate new ones."""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QTranslator
from PySide6.QtGui import QGuiApplication

SUNTREE = Path(__file__).resolve().parents[1]
TS = SUNTREE / "i18n" / "suntree_de.ts"
QM = SUNTREE / "i18n" / "suntree_de.qm"
QSTR = re.compile(r"""\bqsTr\(\s*(["'])((?:\\.|(?!\1).)*)\1""")


def _messages():
    out = []
    for ctx in ET.parse(TS).getroot().iter("context"):
        name = ctx.find("name").text
        for msg in ctx.iter("message"):
            tr = msg.find("translation")
            out.append((name, msg.find("source").text, tr.text or "", tr.get("type") is None))
    return out


def test_every_string_in_the_code_has_a_german_translation():
    finished = {src for _, src, text, done in _messages() if done and text}
    in_code = set()
    for path in [*SUNTREE.glob("*.qml"), *(SUNTREE / "js").glob("*.js")]:
        in_code |= {m.group(2) for m in QSTR.finditer(path.read_text(encoding="utf-8"))}

    assert {"Undo", "Clipboard (%1)"} <= in_code  # the pattern still finds the strings
    missing = sorted(in_code - finished)
    assert not missing, f"untranslated (run scripts/update_translations.py suntree): {missing}"


def test_compiled_translations_match_the_ts():
    QGuiApplication.instance() or QGuiApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))
    stale = [(c, s) for c, s, t, done in _messages() if done and translator.translate(c, s) != t]
    assert not stale, f"suntree_de.qm is out of date (run scripts/update_translations.py suntree): {stale}"


def test_suntree_speaks_german():
    import SunTree.SunTree as T

    app = QGuiApplication.instance() or QGuiApplication([])
    translator = T.install_translator(app, "de")
    try:
        assert translator is not None
        assert QCoreApplication.translate("main", "Undo") == "Rückgängig"
        assert QCoreApplication.translate("main", "%1 files → %2") == "%1 Dateien → %2"
    finally:
        app.removeTranslator(translator)
    assert T.install_translator(app, "en") is None  # English is the code's own
