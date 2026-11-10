"""The MyOS folders of a level and what a birth does, as the core service answers them for the
row in Files ("Designdocument MyOS Core Service.md", 8, step 2). As Scope with ACLs enforced:
born MyOS folders for who may read them, embryos only for who may create them there. A birth
copies from the project's .MyOS/Embryos/ (kept by the core): the files and hidden folders of
that template level; visible subfolders stay embryos."""

import pytest

from cloud.service.level import birth, level


def test_a_level_lists_born_ones_and_the_embryos_one_may_create(shadow):
    assert level(shadow, "lisa", "/Familie") == {"folders": [
        {"name": "04_Finanz", "born": True}, {"name": "07_Arbeit", "born": False}]}
    assert level(shadow, "lisa", "/Familie/04_Finanz") == {"folders": [{"name": "Ausgaben", "born": True}]}
    assert level(shadow, "lisa", "/Familie/04_Finanz/Ausgaben") == {"folders": []}


def test_who_may_not_create_there_sees_no_embryos(shadow):
    assert level(shadow, "lisa", "/") == {"folders": []}  # the root's 04_Finanz, 07_Arbeit: not hers
    assert [f["name"] for f in level(shadow, "oliver", "/")["folders"]] == ["04_Finanz", "07_Arbeit"]
    assert level(shadow, "karl", "/Job") == {"folders": [
        {"name": "04_Finanz", "born": False}, {"name": "07_Arbeit", "born": False}]}


def test_who_may_not_read_there_sees_nothing_of_it(shadow):
    # Nextcloud decides who comes into a folder; here nothing shows one may not read or create.
    assert level(shadow, "karl", "/Familie") == {"folders": []}


@pytest.mark.parametrize("path", ["/Nichts", "/Familie/../Job", "/Familie/.MyOS"])
def test_no_level_where_there_is_no_folder(shadow, path):
    assert level(shadow, "oliver", path) is None


def test_a_birth_creates_the_folder_and_its_hidden_folders_and_copies_the_files(shadow):
    assert birth(shadow, "lisa", "/Familie/07_Arbeit") == {
        "create": ["/Familie/07_Arbeit", "/Familie/07_Arbeit/.MyOS"],
        "copy": [
            {"from": "/Familie/.MyOS/Embryos/07_Arbeit/.MyOS/Desk.md", "to": "/Familie/07_Arbeit/.MyOS/Desk.md"},
            {"from": "/Familie/.MyOS/Embryos/07_Arbeit/Liesmich.md", "to": "/Familie/07_Arbeit/Liesmich.md"},
        ],
    }


def test_a_birth_needs_the_right_to_create_there(shadow):
    with pytest.raises(PermissionError):
        birth(shadow, "lisa", "/Job/07_Arbeit")


@pytest.mark.parametrize("path", ["/Familie/04_Finanz", "/Familie/Fremd", "/Familie/07_Arbeit/Aufgaben", "/"])
def test_only_an_embryo_whose_parent_is_born_can_be_born(shadow, path):
    assert birth(shadow, "oliver", path) is None
