"""What the core service answers for a turned path ("Designdocument MyOS Core Service.md", 8.1).

The service reads a shadow tree: folders and .MyOS files, no documents. For a virtual level
(departments, a department path, the shelf) it lists the entries; for a path inside a project
it names the real folder, which the browser lists itself with the user's rights. The shelf
shows only projects the person may read there."""

import pytest

from cloud.service.lens import lens


def test_the_top_lists_the_departments(shadow):
    assert lens(shadow, "lisa", "/") == {
        "path": "/", "real": None,
        "entries": [{"name": "04_Finanz", "kind": "department"}, {"name": "07_Arbeit", "kind": "department"}],
    }


def test_a_department_lists_its_folders_and_the_shelf(shadow):
    assert lens(shadow, "lisa", "/04_Finanz")["entries"] == [
        {"name": "Ausgaben", "kind": "folder"}, {"name": "Projekte", "kind": "shelf"}]


def test_the_shelf_shows_only_the_projects_one_may_read_there(shadow):
    def names(person):
        return [entry["name"] for entry in lens(shadow, person, "/04_Finanz/Projekte")["entries"]]

    assert names("lisa") == ["Familie"]
    assert names("karl") == ["Job"]
    assert lens(shadow, "oliver", "/04_Finanz/Projekte")["entries"] == [
        {"name": "Familie", "kind": "project", "real": "/Familie/04_Finanz"},
        {"name": "Job", "kind": "project"},  # 04_Finanz not born there: nothing real to carry
        {"name": "Wohnen", "kind": "way"}]  # no Clipboard
    assert names("tom") == []  # not listed: may read nothing


def test_a_way_is_shown_only_when_it_leads_to_a_readable_project(shadow):
    assert lens(shadow, "oliver", "/04_Finanz/Projekte/Wohnen")["entries"] == [{"name": "Garten", "kind": "project"}]
    assert lens(shadow, "oliver", "/04_Finanz/Ausgaben/Projekte")["entries"][0] == {
        "name": "Familie", "kind": "project", "real": "/Familie/04_Finanz/Ausgaben"}
    with pytest.raises(PermissionError):
        lens(shadow, "lisa", "/04_Finanz/Projekte/Wohnen")


def test_inside_a_project_the_real_folder_is_named(shadow):
    assert lens(shadow, "lisa", "/04_Finanz/Projekte/Familie") == {
        "path": "/04_Finanz/Projekte/Familie", "real": "/Familie/04_Finanz", "fallback": False}
    assert lens(shadow, "lisa", "/04_Finanz/Ausgaben/Projekte/Familie")["real"] == "/Familie/04_Finanz/Ausgaben"


def test_without_the_department_folder_the_project_itself_is_shown(shadow):
    assert lens(shadow, "karl", "/04_Finanz/Projekte/Job") == {
        "path": "/04_Finanz/Projekte/Job", "real": "/Job", "fallback": True}
    assert lens(shadow, "karl", "/04_Finanz/Projekte/Job/Kunden")["real"] == "/Job/Kunden"


def test_a_project_one_may_not_read_is_denied_not_missing(shadow):
    with pytest.raises(PermissionError):
        lens(shadow, "lisa", "/04_Finanz/Projekte/Job")


@pytest.mark.parametrize("path", ["/09_Nichts", "/04_Finanz/Projekte/Nichts", "/04_Finanz/../Familie",
                                  "/04_Finanz/Projekte/Familie/.MyOS", "/04_Finanz/Projekte/Clipboard"])
def test_nothing_there_or_not_allowed_is_none(shadow, path):
    assert lens(shadow, "oliver", path) is None


def test_a_broken_acls_md_hides_everything(shadow):
    (shadow / ".MyOS" / "ACLs.md").write_bytes(b"\xff\xfe broken")

    assert lens(shadow, "oliver", "/04_Finanz/Projekte")["entries"] == []
