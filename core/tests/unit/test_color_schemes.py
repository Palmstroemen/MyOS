"""The colour schemes (core/color_schemes.py; Scope/Designdocument Setup.md, step 2): each a file,
each naming the same colours."""

import re

from core.color_schemes import load_scheme


def test_both_schemes_name_the_same_colours():
    assert load_scheme("dark").keys() == load_scheme("light").keys()


def test_every_value_is_a_colour():
    for name in ("dark", "light"):
        for colour, value in load_scheme(name).items():
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), (name, colour, value)


def test_the_schemes_differ():
    assert load_scheme("dark")["bg"] != load_scheme("light")["bg"]
