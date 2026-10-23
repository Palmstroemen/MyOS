"""The lens (see "Designdocument Perspective Resolver MVP.md", Part A).

A lens looks at the projects from a department: /04_Finanz/Ausgangsrechnungen/2026 seen in
a project. Scope shows it framed in its one path line (A3): left of the frame the project
(or the shelf), inside the frame the department path. Taking the lens off (✕) removes only
the frame: one stays where the lens looked."""

from pathlib import Path

import pytest

from core.perspective_session import PerspectiveSession


def _project(path: Path) -> Path:
    (path / ".MyOS").mkdir(parents=True, exist_ok=True)
    (path / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)


@pytest.fixture
def world(tmp_path):
    template = tmp_path / "Templates" / "Standard"
    (template / "04_Finanz" / "Ausgangsrechnungen" / ".MyOS").mkdir(parents=True)
    (template / "04_Finanz" / ".MyOS").mkdir(parents=True, exist_ok=True)
    (template / "04_Finanz" / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Hell\n")
    (template / "07_Arbeit").mkdir(parents=True)
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    (studio / "04_Finanz" / "Ausgangsrechnungen" / "2026").mkdir(parents=True)
    (studio / "04_Finanz" / "Ausgangsrechnungen" / "2026" / "r1.pdf").write_text("r")
    (studio / ".MyOS" / "Desk.md").write_text("# Desk\nThemePreset: Dunkel\n")
    reisen = _project(root / "Reisen")
    (reisen / "Fotos").mkdir()
    (reisen / "lose Rechnung.pdf").write_text("x")
    _project(root / "Wohnen" / "Garten")
    (root / "Clipboard").mkdir()
    return {"root": root, "studio": studio, "reisen": reisen, "garten": root / "Wohnen" / "Garten",
            "template": template}


LENS = ("04_Finanz", "Ausgangsrechnungen", "2026")


def _session(world, cwd=None) -> PerspectiveSession:
    session = PerspectiveSession(world["root"])
    session.set_cwd(cwd or world["studio"])
    return session


def test_putting_on_a_lens_keeps_the_cwd(world):
    session = _session(world)
    assert not session.active

    session.put_on(LENS)

    assert session.active and session.cwd == world["studio"].resolve()
    assert session.project == ("Musikstudio",)
    assert session.cpd == "/04_Finanz/Ausgangsrechnungen/2026/Projekte/Musikstudio"
    assert session.target == world["studio"].resolve() / "04_Finanz" / "Ausgangsrechnungen" / "2026"


def test_left_of_the_frame_moves_the_lens_and_taking_it_off_stays_there(world):
    session = _session(world)
    session.put_on(LENS)

    session.move_to_project(("Reisen",))

    reisen_2026 = world["reisen"].resolve() / "04_Finanz" / "Ausgangsrechnungen" / "2026"
    assert session.target == reisen_2026
    assert session.take_off() == reisen_2026  # an embryo there: one stays in it
    assert session.cwd == reisen_2026 and not session.active


def test_left_of_the_frame_given_as_the_project_folder(world):
    # Scope's projects row names a project by its real path.
    session = _session(world)
    session.put_on(LENS)

    session.move_to(world["garten"])

    assert session.project == ("Wohnen", "Garten")
    assert session.cpd == "/04_Finanz/Ausgangsrechnungen/2026/Projekte/Wohnen/Garten"
    for not_a_project in (world["root"] / "Wohnen", world["studio"] / "04_Finanz", world["root"].parent):
        with pytest.raises(ValueError):
            session.move_to(not_a_project)
    assert session.project == ("Wohnen", "Garten")


def test_taking_the_lens_off_on_the_shelf_stays_on_the_shelf(world):
    session = _session(world)
    session.put_on(("04_Finanz",))
    session.to_shelf()

    assert session.take_off() == world["root"].resolve()


def test_changing_the_cwd_leaves_the_lens(world):
    session = _session(world)
    session.put_on(LENS)

    session.set_cwd(world["garten"])

    assert session.project == ("Musikstudio",) and session.cwd == world["garten"].resolve()


def test_what_the_lens_shows_and_the_fallback_to_the_project(world):
    session = _session(world)
    session.put_on(LENS)
    view = session.listing()
    assert [p.name for p in view.entries] == ["r1.pdf"] and not view.fallback

    session.move_to_project(("Reisen",))  # no 04_Finanz born there
    view = session.listing()

    assert view.fallback and view.shown == world["reisen"].resolve()
    assert [p.name for p in view.entries] == ["Fotos", "lose Rechnung.pdf"]  # folders too (A4)


def test_the_shelf_shows_projects_and_the_way_to_them(world):
    session = _session(world)
    session.put_on(("04_Finanz",))

    session.to_shelf()
    assert session.cpd == "/04_Finanz/Projekte"
    assert [p.name for p in session.listing().entries] == ["Musikstudio", "Reisen", "Wohnen"]  # no Clipboard

    session.into_shelf("Wohnen")
    assert [p.name for p in session.listing().entries] == ["Garten"]
    session.into_shelf("Garten")
    assert session.project == ("Wohnen", "Garten") and session.cpd == "/04_Finanz/Projekte/Wohnen/Garten"


def test_going_deeper_and_changing_the_lens(world):
    session = _session(world)
    session.put_on(("04_Finanz",))
    session.go_into("Ausgangsrechnungen")
    assert session.lens == ("04_Finanz", "Ausgangsrechnungen")

    session.move_to_project(("Reisen",))
    session.put_on(("07_Arbeit",))  # another department: stays in the project looked at
    assert session.project == ("Reisen",) and session.lens == ("07_Arbeit",)


@pytest.mark.parametrize("lens", [("Fotos",), ("04_Finanz", ".."), (), ("../x",)])
def test_only_departments_can_be_worn(world, lens):
    session = _session(world)

    with pytest.raises(ValueError):
        session.put_on(lens)
    assert not session.active


def test_no_lens_outside_the_projects(world, tmp_path):
    session = PerspectiveSession(world["root"])
    with pytest.raises(ValueError):
        session.put_on(("04_Finanz",))  # no CWD yet
    with pytest.raises(ValueError):
        session.set_cwd(tmp_path)        # outside the projects root
    session.set_cwd(world["studio"])
    session.put_on(("04_Finanz",))
    with pytest.raises(ValueError):
        session.move_to_project(("..", "elsewhere"))


def test_the_desk_of_the_department(world):
    session = _session(world)
    session.put_on(LENS)
    assert session.desk_file() == world["template"] / "04_Finanz" / ".MyOS" / "Desk.md"

    # Birth copies .MyOS: the copy in the project does not hide the template's Desk.
    copy = world["studio"] / "04_Finanz" / ".MyOS"
    copy.mkdir()
    (copy / "Desk.md").write_text("# Desk\nThemePreset: Alt\n")
    assert session.desk_file() == world["template"] / "04_Finanz" / ".MyOS" / "Desk.md"

    deeper = world["template"] / "04_Finanz" / "Ausgangsrechnungen" / ".MyOS" / "Desk.md"
    deeper.write_text("# Desk\nThemePreset: Rot\n")
    assert session.desk_file() == deeper  # the nearest one up the lens path

    session.put_on(("07_Arbeit",))
    assert session.desk_file() is None  # never the project's own Desk
    own = world["studio"] / "07_Arbeit" / ".MyOS"
    own.mkdir(parents=True)
    (own / "Desk.md").write_text("# Desk\nThemePreset: Eigen\n")
    assert session.desk_file() == own / "Desk.md"  # the template has none: the project's


def test_changes_to_the_lens_desk_are_saved_in_the_template(world):
    session = _session(world)
    assert session.desk_save_file() is None  # no lens: the project's rule (Desk.md, 12)
    session.put_on(LENS)
    assert session.desk_save_file() == world["template"] / "04_Finanz" / ".MyOS" / "Desk.md"

    deeper = world["template"] / "04_Finanz" / "Ausgangsrechnungen" / ".MyOS" / "Desk.md"
    deeper.write_text("# Desk\nThemePreset: Rot\n")
    assert session.desk_save_file() == deeper  # into the Desk that applies

    session.put_on(("07_Arbeit",))  # no Desk yet: born in the template on the first change
    assert session.desk_save_file() == world["template"] / "07_Arbeit" / ".MyOS" / "Desk.md"

    session.take_off()
    assert session.desk_save_file() is None


def test_bearing_the_target_where_the_department_folder_is_missing(world):
    # Dropping into the lens of a project without the department folder: the folder is
    # born on the way (with the template's content, as an embryo is) and the lens shows it.
    session = _session(world)
    session.put_on(LENS)
    session.move_to_project(("Reisen",))
    assert session.listing().fallback

    target = session.bear()

    assert target == world["reisen"].resolve() / "04_Finanz" / "Ausgangsrechnungen" / "2026"
    assert target.is_dir() and (target.parent / ".MyOS").is_dir()  # born from the template
    assert session.shown() == (target, False)


def test_nothing_to_bear_without_a_project(world):
    session = _session(world)
    with pytest.raises(ValueError):
        session.bear()  # no lens
    session.put_on(("04_Finanz",))
    session.to_shelf()
    with pytest.raises(ValueError):
        session.bear()  # on the shelf


def test_putting_on_the_lens_of_a_real_folder(world):
    # Scope's MyOS-folder row shows real folders of the project looked at; a double click
    # puts on the lens there. The session finds project and department path (nested too).
    session = _session(world)
    session.look_at(world["studio"] / "04_Finanz" / "Ausgangsrechnungen")
    assert session.lens == ("04_Finanz", "Ausgangsrechnungen") and session.project == ("Musikstudio",)
    assert session.cwd == world["studio"].resolve()  # the CWD stays

    session.look_at(world["garten"] / "04_Finanz")  # an embryo: not born, still a lens
    assert session.lens == ("04_Finanz",) and session.project == ("Wohnen", "Garten")

    for nowhere in (world["studio"], world["studio"] / "Eigenes", world["root"] / "Clipboard"):
        with pytest.raises(ValueError):
            session.look_at(nowhere)  # the project itself, no department, outside projects
