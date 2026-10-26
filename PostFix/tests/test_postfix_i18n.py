"""PostFix UI strings are English in the code; German comes from i18n/postfix_de.ts/.qm.

Run scripts/update_translations.py after changing strings, and translate new ones.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

POSTFIX = Path(__file__).resolve().parents[1]
TS = POSTFIX / "i18n" / "postfix_de.ts"
QM = POSTFIX / "i18n" / "postfix_de.qm"
TR_CALL = re.compile(r"""\btr\(\s*(["'])(.*?)\1\s*\)""")


def _messages():
    """(context, source, translation, finished) of every message in the .ts."""
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
    for path in POSTFIX.glob("*.py"):
        in_code |= {m.group(2) for m in TR_CALL.finditer(path.read_text(encoding="utf-8"))}

    assert len(in_code) > 40  # the pattern still finds the strings
    missing = sorted(in_code - finished)
    assert not missing, f"untranslated (run scripts/update_translations.py postfix): {missing}"


def test_compiled_translations_match_the_ts():
    QApplication.instance() or QApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))

    stale = [(c, s) for c, s, t, done in _messages() if done and translator.translate(c, s) != t]
    assert not stale, f"postfix_de.qm is out of date (run scripts/update_translations.py postfix): {stale}"


def test_german_ui_from_the_translation():
    app = QApplication.instance() or QApplication([])
    translator = QTranslator()
    assert translator.load(str(QM))
    app.installTranslator(translator)
    try:
        from PostFix.ui_panels import ACLRoleEditor

        editor = ACLRoleEditor("Buchhaltung", ["read"], own_rule=False)
        assert editor.meaning["read"].text() == "✓ darf lesen"
        assert editor.meaning["write"].text() == "✗ darf nicht schreiben"
        assert editor.apply_button.text() == "Übernehmen"
    finally:
        app.removeTranslator(translator)


def test_in_german_qts_own_buttons_are_german_too():
    # Dialogs PostFix opens (e.g. "Bin fertig") have Qt's own buttons: "Abbrechen", not "Cancel".
    import os
    from pathlib import Path

    from PySide6.QtCore import QCoreApplication, QObject
    from PySide6.QtWidgets import QApplication

    from PostFix.main import PostFixWindow

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    class _W(QObject):
        set_language = PostFixWindow.set_language

        def __init__(self):
            super().__init__()
            self._translator = None
            self._qt_translator = None
            self._i18n_dir = Path(__file__).resolve().parents[1] / "i18n"

        def retranslate_ui(self):
            pass

    w = _W()
    try:
        assert w.set_language("de")
        assert QCoreApplication.translate("QPlatformTheme", "Cancel") == "Abbrechen"
        w.set_language("en")
        assert QCoreApplication.translate("QPlatformTheme", "Cancel") == "Cancel"
    finally:
        for t in (w._translator, w._qt_translator):
            if t is not None:
                app.removeTranslator(t)
