"""The colour schemes (core/color_schemes.py; Scope/Designdocument Setup.md, step 2): each a file,
each naming the same colours."""

import re

from core.color_schemes import (
    SCHEMES_DIR,
    load_scheme,
    own_colors_path,
    reset_scheme_color,
    set_scheme_color,
    shipped_scheme,
)


def test_both_schemes_name_the_same_colours():
    assert load_scheme("dark").keys() == load_scheme("light").keys()


def test_every_value_is_a_colour():
    for name in ("dark", "light"):
        for colour, value in load_scheme(name).items():
            assert re.fullmatch(r"#([0-9a-fA-F]{2})?[0-9a-fA-F]{6}", value), (name, colour, value)


def test_the_schemes_differ():
    assert load_scheme("dark")["bg"] != load_scheme("light")["bg"]


# --- Colours of one's own: kept beside the shipped schemes, which stay as they are --------------


def test_a_colour_set_is_kept_for_its_scheme_alone():
    dark_before = load_scheme("dark")["filesPanelCenter"]
    assert set_scheme_color("light", "filesPanelCenter", "#112233") is True
    assert load_scheme("light")["filesPanelCenter"] == "#112233"
    assert load_scheme("dark")["filesPanelCenter"] == dark_before


def test_the_shipped_scheme_stays_as_it_is():
    before = (SCHEMES_DIR / "light.json").read_text(encoding="utf-8")
    set_scheme_color("light", "filesPanelCenter", "#112233")
    assert (SCHEMES_DIR / "light.json").read_text(encoding="utf-8") == before
    assert shipped_scheme("light")["filesPanelCenter"] != "#112233"
    assert own_colors_path("light").is_file()


def test_set_back_to_the_shipped_colour():
    shipped = shipped_scheme("light")["filesPanelCenter"]
    set_scheme_color("light", "filesPanelCenter", "#112233")
    reset_scheme_color("light", "filesPanelCenter")
    assert load_scheme("light")["filesPanelCenter"] == shipped


def test_what_is_no_colour_or_no_name_is_not_kept():
    assert set_scheme_color("light", "filesPanelCenter", "white-ish") is False
    assert set_scheme_color("light", "noSuchColour", "#112233") is False
    assert set_scheme_color("../evil", "filesPanelCenter", "#112233") is False
    assert not own_colors_path("light").exists()


def test_a_file_edited_by_hand_cannot_break_a_scheme():
    path = own_colors_path("light")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"filesPanelCenter": "nonsense", "noSuchColour": "#112233", "bg": "#010203"}', encoding="utf-8")
    scheme = load_scheme("light")
    assert scheme["filesPanelCenter"] == shipped_scheme("light")["filesPanelCenter"]
    assert "noSuchColour" not in scheme
    assert scheme["bg"] == "#010203"
    path.write_text("{ not json", encoding="utf-8")
    assert load_scheme("light") == shipped_scheme("light")
