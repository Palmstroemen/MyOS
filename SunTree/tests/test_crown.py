"""The crown's arithmetic (SunTree/js/Crown.js), run in Qt's JS engine.

SunTree/Designdocument Krone.md: moving outward a folder's field grows until it fills the half
at the line T; beyond it the field is drawn into the stem while the pointer is pulled inward,
and the next level starts again at the inner radius."""

import os
from pathlib import Path

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QJSEngine

CROWN_JS = Path(__file__).resolve().parents[1] / "js" / "Crown.js"

# ri = 0.2 R, T = 0.7 R with R = 300: D = T - ri = 150, one level = 2 D = 300.
GEO = {"ri": 60, "T": 210, "R": 300, "lens": 2.2, "speed": 1}

# Job: Aufträge has 3 subfolders (Desertgreener has 2), Belege has 12, Rechnungen none.
TREE = {"": ["Aufträge", "Belege", "Rechnungen"],
        "Aufträge": ["Desertgreener", "Gartenhof", "TestKunde"],
        "Aufträge/Desertgreener": ["Angebote", "Fotos"],
        "Belege": [str(m) for m in range(1, 13)]}


@pytest.fixture(scope="module")
def js():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    engine = QJSEngine()
    result = engine.evaluate(CROWN_JS.read_text(encoding="utf-8").replace(".pragma library", ""))
    assert not result.isError(), result.toString()
    engine.evaluate("var TREE = " + repr(TREE).replace("'", '"') + ";"
                    "function count(path) { var k = TREE[path.join('/')]; return k ? k.length : 0; }"
                    "function nameAt(path, i) { return TREE[path.join('/')][i]; }"
                    "function childCount(path) { var names = []; for (var i = 0; i < path.length; i++) {"
                    "  names.push(nameAt(names, path[i])); } return count(names); }")

    def call(name, *args):
        fn = engine.globalObject().property(name)
        value = fn.call([engine.toScriptValue(a) for a in args])
        assert not value.isError(), value.toString()
        return value.toVariant()

    def walk(state, moves):
        """Moves (dr, dt) through Crown.move with the test tree; returns the state."""
        engine.globalObject().setProperty("st", engine.toScriptValue(state))
        engine.globalObject().setProperty("moves", engine.toScriptValue(moves))
        engine.globalObject().setProperty("geo", engine.toScriptValue(GEO))
        value = engine.evaluate("for (var i = 0; i < moves.length; i++) st = move(st, moves[i][0], moves[i][1], geo, childCount); st")
        assert not value.isError(), value.toString()
        return value.toVariant()

    def evaluate(code):
        engine.globalObject().setProperty("geo", engine.toScriptValue(GEO))
        value = engine.evaluate(code)
        assert not value.isError(), value.toString()
        return value.toVariant()

    call.walk = walk
    call.evaluate = evaluate
    yield call


def test_one_coordinate_runs_through_the_levels(js):
    assert js("phase", 59, 60, 210)["ph"] == 0  # the stem's hollow
    grow = js("phase", 135, 60, 210)
    assert (grow["L"], grow["ph"], grow["p"]) == (0, 1, 0.5)
    suck = js("phase", 285, 60, 210)
    assert (suck["L"], suck["ph"], suck["q"]) == (0, 2, 0.5)
    nxt = js("phase", 360, 60, 210)
    assert (nxt["L"], nxt["ph"], nxt["p"]) == (1, 1, 0)


def test_the_pointer_is_pulled_inward_beyond_the_line(js):
    # Growing it follows the hand; beyond T it goes back to ri while the hand goes on.
    radii = [js("pointerRadius", s, 60, 210) for s in (60, 150, 209.9, 210, 285, 359.9, 360, 400)]
    assert radii[0] == 60 and radii[1] == 150
    assert abs(radii[2] - 210) < 0.2 and radii[3] == 210
    assert 60 < radii[4] < 210
    assert abs(radii[5] - 60) < 0.2 and radii[6] == 60 and radii[7] == 100


def test_the_field_grows_to_the_whole_half(js):
    sp = js("spans", 5, 2.5, 0, 2.2)
    assert abs(sum(sp) - 180) < 1e-6 and sp[2] == max(sp)  # a fish-eye around u
    full = js("spans", 5, 2.5, 1, 2.2)
    assert full[2] > 179.9
    assert js("fieldRadius", 0, 300, 210) == 300 and js("fieldRadius", 1, 300, 210) == 210


def test_the_angle_and_its_inverse(js):
    for th in (-80, -30, 0, 45, 85):
        u = js("uAtAngle", 7, th, 2.2)
        assert abs(js("angleAt", js("spans", 7, u, 0, 2.2), u) - th) < 0.01


def test_scrolling_through_a_full_field_moves_the_pointer_calmly(js):
    angles = []
    for i in range(0, 401):
        u = 2 + i / 200  # through two folders
        angles.append(js("pointerAngle", js("spans", 7, u, 1, 2.2), u, 1))
    assert max(abs(b - a) for a, b in zip(angles, angles[1:])) < 0.5


def test_outward_through_the_line_goes_a_level_deeper(js):
    start = js("start", 60, 0, 3)  # at ri, pointing at the middle: Belege
    deeper = js.walk(start, [[5, 0]] * 61)  # 305 px outward
    assert js("phase", deeper["s"], 60, 210)["L"] == 1
    assert deeper["lock"] == [1]  # Belege was drawn into the stem
    back = js.walk(deeper, [[-5, 0]] * 12)  # inward again: Belege comes back out
    assert js("phase", back["s"], 60, 210)["L"] == 0


def test_a_folder_without_subfolders_is_not_drawn_in(js):
    start = js("start", 60, 80, 3)  # pointing low: Rechnungen
    stopped = js.walk(start, [[5, 0]] * 80)
    st = js("phase", stopped["s"], 60, 210)
    assert (st["L"], st["ph"]) == (0, 1) and st["p"] > 0.99


def test_up_and_down_scrolls_a_level(js):
    start = js("start", 100, 0, 3)
    down = js.walk(start, [[0, 10]] * 10)
    assert down["u"][0] > start["u"][0]


def test_back_into_the_hollow_lets_go(js):
    start = js("start", 70, 0, 3)
    out = js.walk(start, [[-5, 0]] * 4)
    assert out["released"]


def _layout(js, state):
    engine_tree = "function kids(way) { var names = []; for (var i = 0; i < way.length; i++) names.push(nameAt(names, way[i]));" \
                  " return (TREE[names.join('/')] || []).slice(); }"
    return js.evaluate(engine_tree + "layout(" + repr(state).replace("'", '"').replace("True", "true").replace("False", "false")
                       + ", geo, kids)")


def test_the_rings_of_a_growing_field(js):
    rings = _layout(js, {"s": 135, "u": [1.5], "lock": [], "released": False})  # Belege, half grown
    field, kids = rings[0], [r for r in rings[1:] if r["under"]]
    assert field["kind"] == "field" and field["r0"] == 60 and 210 < field["r1"] < 300
    assert len(field["items"]) == 3 and abs(sum(field["sp"]) - 180) < 1e-6
    assert kids[0]["r0"] == field["r1"] and kids[0]["r1"] == 300
    assert kids[0]["way"] == [1] and len(kids[0]["items"]) == 12  # Belege's months in its slice


def test_the_rings_while_drawn_in(js):
    rings = _layout(js, {"s": 285, "u": [1.5, 6], "lock": [1], "released": False})
    field, kids = rings
    assert field["r1"] == kids["r0"] and 60 < field["r1"] < 210  # shrinking into the stem
    assert kids["r1"] == 300 and abs(sum(kids["sp"]) - 180) < 1e-6 and len(kids["items"]) == 12


def test_a_deeper_level_lists_the_way_down(js):
    rings = _layout(js, {"s": 400, "u": [0.5, 0.5], "lock": [0], "released": False})
    assert rings[0]["way"] == [0] and [len(r["items"]) for r in rings][0] == 3  # Aufträge's folders


def test_over_the_end_of_a_level_lets_go_on_every_level(js):
    # Aufträge drawn in, its 3 folders fill the half: pushing on past the first one, towards
    # the stem, in many small steps lets go (the push adds up), not one small nudge.
    deep = js.walk(js("start", 60, -60, 3), [[5, 0]] * 61)
    assert deep["lock"] == [0] and not deep["released"]
    top = dict(deep, u=[deep["u"][0], 0.01])  # at the first folder
    nudge = js.walk(top, [[0, -2]] * 3)
    assert not nudge["released"]
    pushed = js.walk(top, [[0, -2]] * 15)
    assert pushed["released"]


def test_moving_back_from_the_end_starts_the_push_again(js):
    deep = js.walk(js("start", 60, -60, 3), [[5, 0]] * 61)
    top = js.walk(dict(deep, u=[deep["u"][0], 0.01]), [[0, -2]] * 8)  # half way to letting go
    assert not top["released"]
    back = js.walk(top, [[0, 4]] + [[0, -2]] * 8)
    assert not back["released"]
