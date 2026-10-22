"""The lens (see "Designdocument Perspective Resolver MVP.md", Part A).

A lens looks at the projects from a department: /04_Finanz/Ausgangsrechnungen/2026 seen in
a project. It does not change the CWD (where one is). The left menu changes the CWD and
the lens follows; moving the lens to another project (the right menu, the CTD) leaves the
CWD; taking the lens off brings one back to the CWD."""

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


def test_the_right_menu_moves_only_the_lens_and_taking_it_off_returns_to_the_cwd(world):
    session = _session(world)
    session.put_on(LENS)

    session.move_to_project(("Reisen",))

    assert session.target == world["reisen"].resolve() / "04_Finanz" / "Ausgangsrechnungen" / "2026"
    assert session.cwd == world["studio"].resolve()
    assert session.take_off() == world["studio"].resolve()
    assert not session.active


def test_the_left_menu_changes_the_cwd_and_the_lens_follows(world):
    session = _session(world)
    session.put_on(LENS)
    session.move_to_project(("Reisen",))

    session.set_cwd(world["garten"])  # the left menu

    assert session.project == ("Wohnen", "Garten")  # the earlier right-menu choice is forgotten
    assert session.cpd == "/04_Finanz/Ausgangsrechnungen/2026/Projekte/Wohnen/Garten"
    assert session.take_off() == world["garten"].resolve()


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

    real = world["studio"] / "04_Finanz" / ".MyOS"
    real.mkdir()
    (real / "Desk.md").write_text("# Desk\nThemePreset: Eigen\n")
    assert session.desk_file() == real / "Desk.md"  # the nearest one wins

    session.put_on(("07_Arbeit",))
    assert session.desk_file() is None  # never the project's own Desk
