"""The crown in SunTree (SunTree/main.qml with SunTree/js/Crown.js; Designdocument Krone.md):
moving outward a folder grows, beyond the line T it is drawn into the stem and the pointer
is pulled inward; a click goes into the folder under the pointer, a drop puts files there."""

import math
from pathlib import Path

import pytest
from PySide6.QtGui import QCursor, QGuiApplication


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


def _gone(win):
    """SunTree went away: it fades out first (Designdocument Krone.md), then its window hides."""
    from PySide6.QtTest import QTest

    QTest.qWait(450)
    return not win.isVisible()


def _prop(win, name):
    value = win.property(name)
    return value.toVariant() if hasattr(value, "toVariant") else value


def _tick(win, dt):
    """A frame of the crown and, as X does after the crown has put the pointer, the motion
    event at the put place (which ends the time of motion events from before the put)."""
    _call(win, "crownTick", dt)
    if _prop(win, "putsPending"):
        at = _prop(win, "crownPointer")
        _call(win, "handMoved", at["x"], at["y"])


def _dive(win, distance, step=5):
    """The hand moves outward on the right half's middle line (towards Noten), the crown
    settling after each move as its timer would."""
    geo = _call(win, "crownGeo", 1)
    _call(win, "handMoved", geo["cx"] + geo["ri"] + 1, geo["cy"])
    for _ in range(int(distance / step)):
        at = _prop(win, "crownPointer")
        _call(win, "handMoved", at["x"] + step, at["y"])
        for _ in range(3):
            _tick(win, 0.2)
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
    _dive(window, geo["T"] - geo["ri"] + 60)  # 60 px beyond the line
    pointer = _prop(window, "crownPointer")
    r = _call(window, "crownPolar", 1, pointer["x"], pointer["y"])["r"]
    assert r < geo["T"] - 20  # pulled back inside the line, while the hand went beyond it
    put = suntree.lastPointer()
    assert put != {"x": 0, "y": 0}  # put there through the backend (QCursor.setPos)


def test_a_click_shows_the_folder_under_the_pointer(world, suntree, window):
    # A single click only looks: the folder becomes the CTD (what SunTree shows in its middle);
    # the CWD - Scope's place - stays.
    geo = _call(window, "crownGeo", 1)
    _dive(window, 2 * (geo["T"] - geo["ri"]) + 20)
    hit = _call(window, "crownHit")["row"]["path"]
    at = _prop(window, "crownPointer")
    _call(window, "crownClicked", at["x"], at["y"], False)
    assert suntree.ctd() == hit and suntree.cwd() == str(world["studio"])


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
    _call(window, "crownRelease", False)
    for _ in range(40):
        _tick(window, 0.2)
    assert _prop(window, "crownActive") == 0 and _call(window, "crownHit") is None


def _texts(window):
    from PySide6.QtQuick import QQuickItem

    return [str(item.property("text")) for item in window.findChildren(QQuickItem)
            if isinstance(item.property("text"), str)]


def test_no_top_band_only_the_stem(world, window):
    # The development helpers (filter buttons, "Dummy Ablage") are gone; SunTree is the crown
    # and its stem.
    filters = world["studio"] / ".MyOS" / "Filters"
    filters.mkdir()
    (filters / "Ausgaben.md").write_text("## Perspective 04_Finanz/Ausgaben\n")
    _call(window, "refreshModels")
    texts = _texts(window)
    assert "Dummy Ablage" not in texts and "Ausgaben" not in texts


def test_no_exit_button_the_clipboard_spans_the_stem(world, window):
    # SunTree stays, ready for the shortcut: no red X; Ctrl+Q ends it (test_suntree_once).
    from PySide6.QtQuick import QQuickItem

    window.show()
    QGuiApplication.instance().processEvents()
    assert window.findChild(QQuickItem, "emergencyExit") is None
    clipboard = next(h for h in _prop(window, "stemHits") if h["kind"] == "clipboard")
    left, right = _call(window, "crownGeo", -1), _call(window, "crownGeo", 1)
    assert clipboard["w"] == right["cx"] - left["cx"]


def test_past_the_last_folder_into_the_stem(world, window):
    # Noten fills the right half and is drawn in; its folders 2025 and 2026 fill it. Moving on
    # sideways past the first folder, towards the stem, lets go; the half does not take the
    # pointer again until the hand has left it.
    geo = _dive(window, 2 * (_call(window, "crownGeo", 1)["T"] - _call(window, "crownGeo", 1)["ri"]) + 20)

    def polar():
        at = _prop(window, "crownPointer")
        return _call(window, "crownPolar", 1, at["x"], at["y"])

    while polar()["th"] > -80:  # up the half to the first folder, 2025
        at = _prop(window, "crownPointer")
        p = polar()
        a = math.radians(p["th"])
        _call(window, "handMoved", at["x"] + 3 * math.sin(a), at["y"] - 3 * math.cos(a))
        for _ in range(3):
            _tick(window, 0.2)
    assert _prop(window, "crownActive") == 1 and _call(window, "crownHit")["row"]["label"] == "2025"
    for _ in range(60):
        at = _prop(window, "crownPointer")
        _call(window, "handMoved", at["x"] - 4, at["y"])  # sideways to the stem
        for _ in range(3):
            _tick(window, 0.2)
        if _prop(window, "crownActive") == 0:
            break
    assert _prop(window, "crownActive") == 0
    at = _prop(window, "crownPointer")
    _call(window, "handMoved", at["x"] + 1, at["y"] + 1)  # still on the half's edge
    assert _prop(window, "crownActive") == 0
    _call(window, "handMoved", geo["cx"] - 40, geo["cy"])  # in the stem
    _call(window, "handMoved", geo["cx"] + geo["ri"] + 5, geo["cy"])  # and back into the half
    assert _prop(window, "crownActive") == 1


def _stem_hit(win, kind, path):
    return next(h for h in _prop(win, "stemHits") if h["kind"] == kind and h["path"] == path)


def test_up_the_stem_the_folders_are_spat_out(world, suntree, window):
    # Standing in Noten/2025, a click on Musikstudio lower in the stem: Noten and 2025 do not
    # vanish, they are pushed up the stem and spat out into the crown, which runs back to rest.
    from PySide6.QtTest import QTest

    QCursor.setPos(-200, -200)
    suntree.setCwd(str(world["noten"] / "2025"))
    window.show()
    QTest.qWait(100)
    studio = str(world["studio"])
    hit = _stem_hit(window, "parent", studio)
    was = _prop(window, "stemGlide")["parent:" + studio]

    _call(window, "crownClicked", hit["x"] + hit["w"] / 2, hit["y"] + hit["h"] / 2, False)

    assert suntree.ctd() == studio and suntree.cwd() == str(world["noten"] / "2025")  # only looking up
    assert _prop(window, "stemGlide")[studio] == was  # Musikstudio glides from where it was
    stem = [(e["kind"], e["label"]) for e in _call(window, "stemEntries")]
    assert stem[:3] == [("preview", "2025"), ("preview", "Noten"), ("ctd", "Musikstudio")]
    noten = [e["label"] for e in _call(window, "rightEntries")].index("Noten")
    assert _prop(window, "crownHalves")["1"]["shown"]["lock"] == [noten, 0]  # 2025: first of Noten's

    for _ in range(60):
        _tick(window, 0.1)
    assert [e["kind"] for e in _call(window, "stemEntries")][0] == "ctd"  # all spat out
    assert _prop(window, "crownHalves")["1"]["shown"] is None  # the crown at rest


def test_the_halves_share_the_centres_of_the_cwd_ovals_ends(window):
    # The crown's half circles are centred where the CWD oval's round ends are (radius: half
    # its height), so the hollow lies around them; the stem is as wide as the space between.
    left, right = _call(window, "crownGeo", -1), _call(window, "crownGeo", 1)
    width, height = _call(window, "cwdOval")["w"], _call(window, "cwdOval")["h"]
    assert right["cx"] - left["cx"] == width - height
    assert _call(window, "cwdOval")["cx"] == (left["cx"] + right["cx"]) / 2
    assert right["cy"] == _call(window, "cwdOval")["cy"]


def test_drawing_in_the_stem_entries_never_overlap(world, window):
    # Halfway through drawing Noten in: the preview comes down from above into the middle
    # while the CTD slides down - one slot apart at every moment, not piled up in the oval.
    geo = _call(window, "crownGeo", 1)
    D = geo["T"] - geo["ri"]
    _dive(window, 1.5 * D)  # s about T + D/2: q about 0.5
    for _ in range(30):
        _tick(window, 0.2)
    places = _call(window, "stemPlaces")
    kinds = [p["kind"] for p in places]
    assert kinds[:2] == ["preview", "ctd"] and 0.2 < places[0]["weight"] < 0.8
    for upper, lower in zip(places, places[1:]):
        assert upper["y"] + upper["h"] / 2 <= lower["y"] - lower["h"] / 2 + 0.01, (upper, lower)


def test_a_motion_from_before_the_pull_does_not_throw_the_crown(world, window):
    # While drawing in, the crown puts the pointer inward each frame. A motion event the hand
    # made before that put, arriving after it, reports the old place further out: it must
    # count as the small step it was, not as a jump from where the pointer was put.
    geo = _call(window, "crownGeo", 1)
    _dive(window, geo["T"] - geo["ri"] + 40)  # drawing in: the crown pulls the pointer
    hand = _prop(window, "crownPointer")
    _call(window, "handMoved", hand["x"] + 4, hand["y"])  # the hand moves on
    before = _prop(window, "crownHalves")["1"]["target"]["s"]
    _call(window, "crownTick", 0.2)  # the crown puts the pointer inward
    put = _prop(window, "crownPointer")
    assert put["x"] < hand["x"]  # pulled in

    _call(window, "handMoved", hand["x"] + 6, hand["y"])  # stale: from before the put, 2 px on
    after = _prop(window, "crownHalves")["1"]["target"]["s"]
    assert after - before < 5  # a small step, not the gap to the put pointer


def test_the_crown_takes_its_values_from_the_settings_on_appearing(world, window, tmp_path):
    # Set on the back of Scope (Scope/Designdocument Setup.md), read when SunTree appears.
    from core.settings import Settings

    geo = _call(window, "crownGeo", 1)
    assert abs(geo["T"] - 0.7 * geo["R"]) < 1e-6 and geo["enter"] == 0.75  # the defaults
    settings = Settings()
    settings.set("SunTree/lineT", 0.6)
    settings.set("SunTree/enter", 0.8)
    settings.set("SunTree/leave", 0.3)

    _call(window, "turnedTo")
    geo = _call(window, "crownGeo", 1)
    assert abs(geo["T"] - 0.6 * geo["R"]) < 1e-6
    assert geo["enter"] == 0.8 and geo["leave"] == 0.3


def test_suntree_takes_the_embryo_setting_on_appearing(world, window):
    from core.settings import Settings

    Settings().set("General/embryoOpacity", 0.6)
    _call(window, "turnedTo")
    assert abs(_prop(window, "embryoOpacity") - 0.6) < 1e-6
