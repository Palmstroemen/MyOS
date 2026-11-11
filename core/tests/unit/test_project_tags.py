"""The tags a project suggests: the lines "#Tag" of the .MyOS/Tags.md of the nearest project
up the path that has one (Scope's tag bar, the MyOS core in the cloud)."""

from core.tags import hash_line_tags, project_tags


def test_tags_are_the_hash_lines_not_the_headings():
    assert hash_line_tags("# Tags\n#Wichtig\n#in Arbeit\n  #Rechnung  \nText\n## Mehr\n#Wichtig\n") == [
        "in Arbeit", "Rechnung", "Wichtig"]


def _project(folder, tags):
    (folder / ".MyOS").mkdir(parents=True)
    (folder / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (folder / ".MyOS" / "Tags.md").write_text(tags)


def test_a_folder_takes_the_tags_of_the_nearest_project_s_tags_md(tmp_path):
    _project(tmp_path, "# Tags\n#Familie\n")
    _project(tmp_path / "Job", "# Tags\n#Kunde\n")
    (tmp_path / "Job" / "Kunden").mkdir()
    (tmp_path / "Urlaub").mkdir()

    assert project_tags(tmp_path / "Job" / "Kunden") == ["Kunde"]
    assert project_tags(tmp_path / "Urlaub") == ["Familie"]


def test_without_tags_md_there_are_none(tmp_path):
    assert project_tags(tmp_path) == []
