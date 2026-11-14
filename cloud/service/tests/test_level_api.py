"""The MyOS folders of a level and what a birth does, as the core service answers them for the
row in Files ("Designdocument MyOS Core Service.md", 8, step 2). As Scope with ACLs enforced:
born MyOS folders for who may read them, embryos only for who may create them there. A birth
copies from the project's .MyOS/Embryos/ (kept by the core): the files and hidden folders of
that template level; visible subfolders stay embryos."""

import pytest

from cloud.service.level import bear, birth, level, tags
from core.brand import META_DIR


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


@pytest.mark.parametrize("path", ["/Nichts", "/Familie/../Job", f"/Familie/{META_DIR}"])
def test_no_level_where_there_is_no_folder(shadow, path):
    assert level(shadow, "oliver", path) is None


def test_a_birth_creates_the_folder_and_its_hidden_folders_and_copies_the_files(shadow):
    assert birth(shadow, "lisa", "/Familie/07_Arbeit") == {
        "create": ["/Familie/07_Arbeit", f"/Familie/07_Arbeit/{META_DIR}"],
        "copy": [
            {"from": f"/Familie/{META_DIR}/Embryos/07_Arbeit/{META_DIR}/Desk.md", "to": f"/Familie/07_Arbeit/{META_DIR}/Desk.md"},
            {"from": f"/Familie/{META_DIR}/Embryos/07_Arbeit/Liesmich.md", "to": "/Familie/07_Arbeit/Liesmich.md"},
        ],
    }


def test_a_birth_needs_the_right_to_create_there(shadow):
    with pytest.raises(PermissionError):
        birth(shadow, "lisa", "/Job/07_Arbeit")


@pytest.mark.parametrize("path", ["/Familie/04_Finanz", "/Familie/Fremd", "/Familie/07_Arbeit/Aufgaben", "/"])
def test_only_an_embryo_whose_parent_is_born_can_be_born(shadow, path):
    assert birth(shadow, "oliver", path) is None


def test_saving_through_a_lens_bears_the_department_folder_on_the_way(shadow):
    # As Blueprint.materialize_dir on the desktop: embryos on the way born with their content.
    assert bear(shadow, "karl", "/07_Arbeit/Projekte/Job") == {
        "real": "/Job/07_Arbeit",
        "create": ["/Job/07_Arbeit", f"/Job/07_Arbeit/{META_DIR}"],
        "copy": [
            {"from": f"/Job/{META_DIR}/Embryos/07_Arbeit/{META_DIR}/Desk.md", "to": f"/Job/07_Arbeit/{META_DIR}/Desk.md"},
            {"from": f"/Job/{META_DIR}/Embryos/07_Arbeit/Liesmich.md", "to": "/Job/07_Arbeit/Liesmich.md"},
        ],
    }
    assert bear(shadow, "karl", "/04_Finanz/Ausgaben/Projekte/Job") == {
        "real": "/Job/04_Finanz/Ausgaben", "create": ["/Job/04_Finanz", "/Job/04_Finanz/Ausgaben"], "copy": []}


def test_only_what_is_missing_is_born(shadow):
    (shadow / "Job" / "04_Finanz").mkdir()

    assert bear(shadow, "karl", "/04_Finanz/Ausgaben/Projekte/Job")["create"] == ["/Job/04_Finanz/Ausgaben"]


def test_bearing_needs_the_right_to_create_there(shadow):
    with pytest.raises(PermissionError):
        bear(shadow, "lisa", "/07_Arbeit/Projekte/Job")


@pytest.mark.parametrize("path", ["/04_Finanz/Projekte/Familie",  # born: nothing to bear
                                  "/04_Finanz/Projekte/Job/Kunden",  # a real folder of the project
                                  "/04_Finanz/Projekte", "/04_Finanz", "/Nichts"])
def test_nothing_to_bear_where_the_lens_shows_no_unborn_folder(shadow, path):
    assert bear(shadow, "oliver", path) is None


def test_the_tags_of_a_folder_are_those_of_its_project(shadow):
    (shadow / META_DIR / "Tags.md").write_text("# Tags\n#Wichtig\n#Rechnung\n")
    (shadow / "Job" / META_DIR / "Tags.md").write_text("# Tags\n#Kunde\n")

    assert tags(shadow, "lisa", "/Familie/04_Finanz") == {"tags": ["Rechnung", "Wichtig"]}  # Familie inherits
    assert tags(shadow, "karl", "/Job/Kunden") == {"tags": ["Kunde"]}


def test_no_tags_where_one_may_not_read(shadow):
    (shadow / META_DIR / "Tags.md").write_text("# Tags\n#Wichtig\n")

    assert tags(shadow, "karl", "/Familie") == {"tags": []}
    assert tags(shadow, "lisa", f"/Familie/{META_DIR}") is None
