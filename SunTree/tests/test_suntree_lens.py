"""SunTree at the lens session (SunTree/SunTree.py): it asks the session as Scope does and
builds no lens paths itself (Designdocument Perspective Resolver MVP.md, A6, E5)."""

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
    return {"root": root.resolve(), "studio": _project(root / "Musikstudio").resolve(),
            "reisen": _project(root / "Reisen").resolve()}


@pytest.fixture
def suntree(world):
    import SunTree.SunTree as T
    from core.scope_api import ScopeApi

    QGuiApplication.instance() or QGuiApplication([])
    backend = T.SunTreeBackend(T.MyOSBackendAdapter(ScopeApi(str(world["studio"]))), str(world["studio"]))
    yield backend
    backend.close()


def test_the_session_knows_where_suntree_stands(world, suntree):
    assert suntree.lens("state", {})["result"]["cwd"] == str(world["studio"])

    suntree.setCwd(str(world["reisen"]))
    assert suntree.lens("state", {})["result"]["cwd"] == str(world["reisen"])


def test_the_lens_through_suntree(world, suntree):
    on = suntree.lens("look_at", {"path": str(world["studio"] / "04_Finanz")})["result"]
    assert on["active"] and on["lens"] == ["04_Finanz"]
    assert on["project_dir"] == str(world["studio"])
    assert suntree.cwd() == str(world["studio"])  # the CWD stays (A3)

    assert suntree.lens("take_off", {})["result"]["active"] is False


def test_only_lens_requests(suntree):
    assert suntree.lens("shutdown", {})["ok"] is False


def test_the_projects_root(world, suntree):
    assert suntree.projectsRoot() == str(world["root"])


@pytest.fixture
def window(world, suntree):
    from PySide6.QtCore import QObject, QUrl, Signal
    from PySide6.QtQml import QQmlApplicationEngine

    class Hotkey(QObject):
        activated = Signal()

    app = QGuiApplication.instance()
    engine = QQmlApplicationEngine()
    hotkey = Hotkey()
    ctx = engine.rootContext()
    ctx.setContextProperty("sunTreeBackend", suntree)
    ctx.setContextProperty("sunTreeHotkey", hotkey)
    ctx.setContextProperty("sunTreeStartHidden", True)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parents[1] / "main.qml")))
    assert engine.rootObjects()
    win = engine.rootObjects()[0]
    app.processEvents()
    yield win
    engine.deleteLater()


def _call(win, name, *args):
    from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject

    value = QMetaObject.invokeMethod(win, name, Q_RETURN_ARG("QVariant"), *[Q_ARG("QVariant", a) for a in args])
    return value.toVariant() if hasattr(value, "toVariant") else value


def _left(win):
    return [row["label"] for row in _call(win, "leftEntries")]


def _lens(win):
    state = win.property("lensState")
    return state.toVariant() if hasattr(state, "toVariant") else state


def test_the_gestures_are_scopes(world, suntree, window):
    studio = world["studio"]
    # A double click on a MyOS folder puts on its lens; the CWD stays.
    _call(window, "applyLeftDoubleClick", _left(window).index("04_Finanz"))
    assert _lens(window)["target"] == str(studio / "04_Finanz")
    assert suntree.cwd() == str(studio)
    assert _left(window) == ["Ausgaben"]  # the lens' folder
    assert [row["label"] for row in _call(window, "frameEntries")] == ["04_Finanz"]

    _call(window, "applyLeftClick", 0)  # a single click only looks: the lens stays
    assert [row["label"] for row in _call(window, "frameEntries")] == ["04_Finanz"]
    _call(window, "applyLeftDoubleClick", 0)  # sharper: deliberately
    assert [row["label"] for row in _call(window, "frameEntries")] == ["04_Finanz", "Ausgaben"]

    _call(window, "lensRequest", "look_at", {"path": str(studio / "04_Finanz")})  # flatter (the frame)
    assert _lens(window)["target"] == str(studio / "04_Finanz")

    _call(window, "navigateTo", str(world["reisen"]))  # another project: the lens moves
    assert _lens(window)["target"] == str(world["reisen"] / "04_Finanz")
    assert suntree.cwd() == str(world["reisen"])

    _call(window, "takeOffLens")  # ✕: one stays - an embryo stays one, so the project
    assert not _lens(window)["active"]
    assert suntree.cwd() == str(world["reisen"])


def test_the_lens_stays_on_until_taken_off(world, suntree, window):
    # Job/Aufträge/Desertgreener -> Job/Aufträge -> Job: the lens stays (2026-10-25).
    studio, orders = world["studio"], world["studio"] / "Aufträge"
    orders.mkdir()
    _call(window, "applyLeftDoubleClick", _left(window).index("04_Finanz"))

    _call(window, "navigateTo", str(orders))  # no project: the lens stays in its project
    assert _lens(window)["active"] and _lens(window)["project_dir"] == str(studio)
    assert suntree.cwd() == str(orders)

    _call(window, "navigateTo", str(world["root"]))  # the projects root: the shelf
    assert _lens(window)["active"] and suntree.cwd() == str(world["root"])

    _call(window, "navigateTo", str(world["reisen"]))
    assert _lens(window)["target"] == str(world["reisen"] / "04_Finanz")

    _call(window, "navigateTo", str(world["root"].parent))  # outside the projects
    assert _lens(window)["active"]


def test_the_right_half_shows_no_myos_folders(world, suntree):
    (world["studio"] / "04_Finanz").mkdir()  # born: still a MyOS folder, left only
    (world["studio"] / "Noten").mkdir()

    assert [row["name"] for row in suntree.listFolders()] == ["Noten"]


def test_embryos_are_pale(window):
    rows = _call(window, "leftEntries")
    finance = [row["label"] for row in rows].index("04_Finanz")
    assert _call(window, "leftRowOpacity", finance) == window.property("embryoOpacity")


def test_the_folders_of_any_level(world, suntree):
    (world["reisen"] / "Fotos" / "2026").mkdir(parents=True)
    (world["reisen"] / "04_Finanz").mkdir()  # a MyOS folder: left only

    assert [row["name"] for row in suntree.listFoldersAt(str(world["reisen"]))] == ["Fotos"]
    assert [row["name"] for row in suntree.listFoldersAt(str(world["reisen"] / "Fotos"))] == ["2026"]


def test_the_pointer_is_put_where_the_crown_draws_it(suntree):
    suntree.pointerTo(120, 80)
    assert suntree.lastPointer() == {"x": 120, "y": 80}
