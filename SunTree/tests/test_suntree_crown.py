"""The crown in SunTree (SunTree/main.qml with SunTree/js/Crown.js; Designdocument Krone.md):
moving outward a folder grows, beyond the line T it is drawn into the stem and the pointer
is pulled inward; a click goes into the folder under the pointer, a drop puts files there."""

from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("MYOS_SCOPE_START_DAEMON", "0")
    monkeypatch.setenv("MYOS_DESK_BACKEND", "none")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    (tmp_path / "Templates" / "Standard" / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio").resolve()
    (studio / "Noten" / "2025").mkdir(parents=True)
    (studio / "Noten" / "2026").mkdir()
    return {"root": root.resolve(), "studio": studio, "noten": studio / "Noten"}


@pytest.fixture
def suntree(world):
    import SunTree.SunTree as T
    from core.scope_api import ScopeApi

    QGuiApplication.instance() or QGuiApplication([])
    backend = T.SunTreeBackend(T.MyOSBackendAdapter(ScopeApi(str(world["studio"]))), str(world["studio"]))
    yield backend
    backend.close()


@pytest.fixture
def window(world, suntree):
    from PySide6.QtCore import QObject, QUrl, Signal
    from PySide6.QtQml import QQmlApplicationEngine

    class Hotkey(QObject):
        activated = Signal()

    engine, hotkey = QQmlApplicationEngine(), Hotkey()
    ctx = engine.rootContext()
    ctx.setContextProperty("sunTreeBackend", suntree)
    ctx.setContextProperty("sunTreeHotkey", hotkey)
    ctx.setContextProperty("sunTreeStartHidden", True)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / "main.qml")))
    win = engine.rootObjects()[0]
    QGuiApplication.instance().processEvents()
    yield win
    engine.deleteLater()


def _call(win, name, *args):
    from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject

    value = QMetaObject.invokeMethod(win, name, Q_RETURN_ARG("QVariant"), *[Q_ARG("QVariant", a) for a in args])
    return value.toVariant() if hasattr(value, "toVariant") else value


def _prop(win, name):
    value = win.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _dive(win, distance, step=5):
    """The hand moves outward on the right half's middle line (towards Noten), the crown
    settling after each move as its timer would."""
    geo = _call(win, "crownGeo", 1)
    _call(win, "handMoved", geo["cx"] + geo["ri"] + 1, geo["cy"])
    for _ in range(int(distance / step)):
        at = _prop(win, "crownPointer")
        _call(win, "handMoved", at["x"] + step, at["y"])
        for _ in range(3):
            _call(win, "crownTick", 0.2)
    return geo


def test_a_folder_grows_and_is_drawn_in(world, window):
    geo = _dive(window, 5)  # just taken: Noten under the pointer
    assert _call(window, "crownHit")["row"]["label"] == "Noten"

    _dive(window, 2 * (geo["T"] - geo["ri"]) + 20)  # through the line and beyond
    hit = _call(window, "crownHit")
    assert hit["row"]["label"] in ("2025", "2026")  # Noten is in the stem now
    stem = [e["label"] for e in _call(window, "stemEntries")]
    assert stem[0] == "Noten" and stem[1] == "Musikstudio"  # a preview above the CWD


def test_the_pointer_is_pulled_inward(world, suntree, window):
    geo = _call(window, "crownGeo", 1)
    _dive(window, geo["T"] - geo["ri"] + 30)  # 30 px beyond the line
    pointer = _prop(window, "crownPointer")
    r = _call(window, "crownPolar", 1, pointer["x"], pointer["y"])["r"]
    assert r < geo["T"] - 10  # pulled back inside the line, while the hand went beyond it
    put = suntree.lastPointer()
    assert put != {"x": 0, "y": 0}  # put there through the backend (QCursor.setPos)


def test_a_click_goes_into_the_folder_under_the_pointer(world, suntree, window):
    geo = _call(window, "crownGeo", 1)
    _dive(window, 2 * (geo["T"] - geo["ri"]) + 20)
    hit = _call(window, "crownHit")["row"]["path"]
    at = _prop(window, "crownPointer")
    _call(window, "crownClicked", at["x"], at["y"], False)
    assert suntree.cwd() == hit


def test_a_drop_lands_in_the_folder_under_the_pointer(world, window, tmp_path):
    invoice = tmp_path / "Rechnung.pdf"
    invoice.write_text("x")
    geo = _call(window, "crownGeo", 1)
    _dive(window, 2 * (geo["T"] - geo["ri"]) + 20)
    target = Path(_call(window, "crownHit")["row"]["path"])

    assert _call(window, "crownDropUrls", ["file://" + str(invoice)])
    assert (target / "Rechnung.pdf").exists()


def test_letting_go_runs_the_crown_back(world, window):
    geo = _call(window, "crownGeo", 1)
    _dive(window, geo["T"] - geo["ri"])
    _call(window, "crownRelease")
    for _ in range(40):
        _call(window, "crownTick", 0.2)
    assert _prop(window, "crownActive") == 0 and _call(window, "crownHit") is None
