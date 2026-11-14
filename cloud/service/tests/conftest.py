"""The shadow tree the core service reads in these tests: folders and .MyOS files."""

from pathlib import Path

import pytest
from core.brand import META_DIR, env_name

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, delete, change\n\n"
    "## Familie\n- /Familie/: read, write\n\n"
    "## Team\n- /Job/: read, write\n\n"
    "# Users\nOliver: Admin\nLisa: Familie\nKarl: Team\n"
)


def _project(path: Path) -> Path:
    (path / META_DIR).mkdir(parents=True, exist_ok=True)
    (path / META_DIR / "Project.md").write_text("# MyOS Project\n")
    return path


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.delenv(env_name("TEMPLATES_DIR"), raising=False)
    monkeypatch.delenv(env_name("ACL_USER"), raising=False)


@pytest.fixture
def shadow(tmp_path):
    root = _project(tmp_path / "Projekte")
    (root / META_DIR / "ACLs.md").write_text(ACLS)
    (root / META_DIR / "Templates.md").write_text("# Templates\nStandard\n")
    template = root / META_DIR / "Templates" / "Standard"
    (template / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (template / "07_Arbeit" / META_DIR).mkdir(parents=True)  # what a birth of 07_Arbeit copies:
    (template / "07_Arbeit" / META_DIR / "Desk.md").write_text("theme: dark\n")  # its hidden folders
    (template / "07_Arbeit" / "Liesmich.md").write_text("Arbeit\n")  # and files
    (template / "07_Arbeit" / "Aufgaben").mkdir()  # a deeper embryo, not copied
    (_project(root / "Familie") / "04_Finanz" / "Ausgaben").mkdir(parents=True)
    (_project(root / "Job") / "Kunden").mkdir()  # no 04_Finanz: the project itself is shown
    _project(root / "Wohnen" / "Garten")  # Wohnen holds a project, it is none itself
    (root / "Clipboard").mkdir()
    return root
