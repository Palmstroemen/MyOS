"""The FUSE drive's mapping (see "Designdocument Perspective Resolver MVP.md", A6).

The drive always shows the whole turned tree of the projects root, independent of any
lens: /<department>/Projekte/<project>/... For LibreOffice "Save as" into
/04_Finanz/Projekte/Job the file lands in Projekte/Job/04_Finanz."""

from pathlib import Path

import pytest

from core.perspective_drive import PerspectiveDrive


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
    (template / "04_Finanz" / "Ausgangsrechnungen").mkdir(parents=True)
    (template / "04_Finanz" / ".MyOS").mkdir()
    (template / "04_Finanz" / ".MyOS" / "batch.md").write_text("€\n")
    (template / "07_Arbeit").mkdir()
    root = _project(tmp_path / "Projekte")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    studio = _project(root / "Musikstudio")
    (studio / "04_Finanz" / "Ausgangsrechnungen").mkdir(parents=True)
    (studio / "04_Finanz" / "Ausgangsrechnungen" / "r1.pdf").write_text("r1")
    reisen = _project(root / "Reisen")
    (reisen / "Fotos").mkdir()
    (reisen / "Fotos" / "bild.jpg").write_text("b")
    (reisen / "lose.pdf").write_text("l")
    _project(root / "Wohnen" / "Garten")
    (root / "Clipboard").mkdir()
    return {"root": root, "studio": studio, "reisen": reisen, "drive": PerspectiveDrive(root)}


def test_the_top_shows_the_departments_each_with_its_projects(world):
    drive = world["drive"]

    assert drive.listdir("/") == ["04_Finanz", "07_Arbeit"]
    assert drive.listdir("/04_Finanz") == ["Ausgangsrechnungen", "Projekte"]
    assert drive.listdir("/04_Finanz/Projekte") == ["Musikstudio", "Reisen", "Wohnen"]  # no Clipboard
    assert drive.listdir("/04_Finanz/Projekte/Wohnen") == ["Garten"]
    assert drive.node("/04_Finanz").real is None and drive.node("/04_Finanz").is_dir


def test_a_project_shows_its_department_folder(world):
    drive = world["drive"]

    assert drive.listdir("/04_Finanz/Projekte/Musikstudio") == ["Ausgangsrechnungen"]
    node = drive.node("/04_Finanz/Projekte/Musikstudio/Ausgangsrechnungen/r1.pdf")
    assert node.real == world["studio"] / "04_Finanz" / "Ausgangsrechnungen" / "r1.pdf" and not node.is_dir
    # a deeper lens: the department path before "Projekte"
    assert drive.listdir("/04_Finanz/Ausgangsrechnungen/Projekte/Musikstudio") == ["r1.pdf"]


def test_without_the_department_folder_the_project_itself_is_shown(world):
    drive = world["drive"]

    assert drive.listdir("/04_Finanz/Projekte/Reisen") == ["Fotos", "lose.pdf"]
    node = drive.node("/04_Finanz/Projekte/Reisen/Fotos/bild.jpg")
    assert node.real == world["reisen"] / "Fotos" / "bild.jpg"


def test_saving_into_a_project_lands_in_its_department_folder(world):
    drive = world["drive"]
    # into a folder the fallback shows: that real folder
    assert drive.target_for_create("/04_Finanz/Projekte/Reisen/Fotos/neu.jpg") == world["reisen"] / "Fotos" / "neu.jpg"

    target = drive.target_for_create("/04_Finanz/Projekte/Reisen/Rechnung.pdf")

    assert target == world["reisen"] / "04_Finanz" / "Rechnung.pdf"
    assert (world["reisen"] / "04_Finanz").is_dir()                       # born on the way,
    assert (world["reisen"] / "04_Finanz" / ".MyOS" / "batch.md").exists()  # with its template content
    assert drive.listdir("/04_Finanz/Projekte/Reisen") == []  # from now on the department folder is shown
    deep = drive.target_for_create("/04_Finanz/Ausgangsrechnungen/2026/Projekte/Musikstudio/r2.pdf")
    assert deep == world["studio"] / "04_Finanz" / "Ausgangsrechnungen" / "2026" / "r2.pdf"


@pytest.mark.parametrize("path", [
    "/Fotos", "/04_Finanz/Projekte/Clipboard", "/04_Finanz/Projekte/Gibtsnicht",
    "/04_Finanz/Projekte/Musikstudio/fehlt.pdf", "/04_Finanz/../Projekte",
])
def test_what_is_not_there(world, path):
    assert world["drive"].node(path) is None


@pytest.mark.parametrize("path", ["/neu.pdf", "/04_Finanz/neu.pdf", "/04_Finanz/Projekte/neu.pdf"])
def test_nothing_is_saved_into_the_virtual_levels(world, path):
    with pytest.raises(PermissionError):
        world["drive"].target_for_create(path)


def test_access_follows_the_acl_check_of_the_real_path(world):
    denied = world["studio"] / "04_Finanz"
    drive = PerspectiveDrive(world["root"], may=lambda path, action: denied not in [path, *path.parents])

    assert drive.listdir("/04_Finanz/Projekte") == ["Musikstudio", "Reisen", "Wohnen"]
    with pytest.raises(PermissionError):  # denied, not "missing" (resolver contract)
        drive.node("/04_Finanz/Projekte/Musikstudio/Ausgangsrechnungen/r1.pdf")
    with pytest.raises(PermissionError):
        drive.target_for_create("/04_Finanz/Projekte/Musikstudio/neu.pdf")
