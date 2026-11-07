"""A project's embryos for a cloud: .MyOS/Embryos.json (the template tree and, per embryo,
what its birth copies) and those files, computed by MyOS as the one place that resolves
templates. The browser in Nextcloud only shows them and copies them on birth."""

import hashlib
import json
import os
from pathlib import Path

import pytest

from core.cloud_embryos import cloud_paths, compare, embryo_sets, send
from core.localBlueprintLayer import Blueprint


@pytest.fixture(autouse=True)
def _project_templates_only(monkeypatch):
    monkeypatch.delenv("MYOS_TEMPLATES_DIR", raising=False)
    monkeypatch.delenv("MYOS_ROLES", raising=False)


def _project(root: Path) -> Path:
    """Standard template: 04_Finanz (.MyOS/batch.svg, Liesmich.md) with sub-embryos Ausgaben/2026 and Einnahmen."""
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    finanz = root / "Templates" / "Standard" / "04_Finanz"
    (finanz / ".MyOS" / "icons").mkdir(parents=True)
    (finanz / ".MyOS" / "batch.svg").write_text("<svg/>")
    (finanz / ".MyOS" / "icons" / "euro.svg").write_text("<svg>€</svg>")
    (finanz / "Liesmich.md").write_text("Finanzen")
    (finanz / "Ausgaben" / "2026").mkdir(parents=True)
    (finanz / "Einnahmen").mkdir(parents=True)
    (root / "Templates" / "Standard" / "01_Info").mkdir(parents=True)
    return root


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def test_the_manifest_holds_the_template_tree(tmp_path):
    root = _project(tmp_path / "Projekt")

    (only,) = embryo_sets(root)

    assert only.path == "/"
    assert only.manifest["version"] == 1
    assert only.manifest["tree"] == {"04_Finanz": {"Ausgaben": {"2026": {}}, "Einnahmen": {}}, "01_Info": {}}


def test_a_birth_lists_its_files_with_their_hash_and_hidden_folders(tmp_path):
    root = _project(tmp_path / "Projekt")

    (only,) = embryo_sets(root)

    assert only.manifest["births"] == {
        "04_Finanz": {
            "dirs": [".MyOS", ".MyOS/icons"],
            "files": {".MyOS/batch.svg": _sha("<svg/>"), ".MyOS/icons/euro.svg": _sha("<svg>€</svg>"),
                      "Liesmich.md": _sha("Finanzen")},
        },
    }  # empty levels (Ausgaben, 01_Info, ...) copy nothing and are left out
    finanz = root / "Templates" / "Standard" / "04_Finanz"
    assert only.payload == {
        "04_Finanz/.MyOS/batch.svg": finanz / ".MyOS" / "batch.svg",
        "04_Finanz/.MyOS/icons/euro.svg": finanz / ".MyOS" / "icons" / "euro.svg",
        "04_Finanz/Liesmich.md": finanz / "Liesmich.md",
    }


def test_the_birth_list_is_what_a_birth_in_myos_copies(tmp_path):
    root = _project(tmp_path / "Projekt")
    (only,) = embryo_sets(root)

    Blueprint(root)._birth_path("/04_Finanz")

    born = root / "04_Finanz"
    found_dirs, found_files = set(), set()
    for folder, dirs, files in os.walk(born):
        rel = Path(folder).relative_to(born)
        found_dirs.update(str(rel / d) for d in dirs)
        found_files.update(str(rel / f) for f in files)
    birth = only.manifest["births"]["04_Finanz"]
    assert found_dirs == set(birth["dirs"])
    assert found_files == set(birth["files"])


def test_symlinks_in_a_template_are_not_copied(tmp_path):
    root = _project(tmp_path / "Projekt")
    secret = tmp_path / "geheim.txt"
    secret.write_text("x")
    (root / "Templates" / "Standard" / "04_Finanz" / "link.txt").symlink_to(secret)

    (only,) = embryo_sets(root)

    assert "link.txt" not in only.manifest["births"]["04_Finanz"]["files"]


def test_each_subproject_gets_its_own_manifest(tmp_path):
    root = _project(tmp_path / "Projekt")
    sub = _project(root / "Haus")
    (root / ".versteckt" / ".MyOS").mkdir(parents=True)
    (root / ".versteckt" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")

    sets = embryo_sets(root)

    assert [s.path for s in sets] == ["/", "/Haus"]
    assert sets[1].payload["04_Finanz/Liesmich.md"] == sub / "Templates" / "Standard" / "04_Finanz" / "Liesmich.md"


def test_a_project_without_templates_has_an_empty_manifest(tmp_path):
    root = tmp_path / "Leer"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")

    (only,) = embryo_sets(root)

    assert only.manifest == {"version": 1, "tree": {}, "births": {}}
    assert only.payload == {}


# --- bringing them into the cloud (myacl sync) ---


class FakeCloud:
    """Files of the cloud by path relative to the Team folder; records what is sent."""

    def __init__(self, files=None, folders=("/",)):
        self.files = dict(files or {})
        self.folders = set(folders)
        self.calls = []

    def get(self, path):
        return self.files.get(path)

    def mkcol(self, path):
        self.calls.append(("MKCOL", path))
        self.folders.add(path)

    def put(self, path, data):
        self.calls.append(("PUT", path))
        self.files[path] = data

    def delete(self, path):
        self.calls.append(("DELETE", path))
        self.files.pop(path, None)

    def exists(self, path):
        return path in self.folders or path in self.files


def test_an_empty_cloud_gets_the_manifest_and_every_file(tmp_path):
    (only,) = embryo_sets(_project(tmp_path / "Projekt"))

    (change,) = compare([only], FakeCloud())

    assert change.manifest_changed
    assert change.upload == ["04_Finanz/.MyOS/batch.svg", "04_Finanz/.MyOS/icons/euro.svg", "04_Finanz/Liesmich.md"]
    assert change.remove == []


def test_a_cloud_in_step_needs_nothing(tmp_path):
    (only,) = embryo_sets(_project(tmp_path / "Projekt"))
    cloud = FakeCloud({"/.MyOS/Embryos.json": json.dumps(only.manifest).encode()})

    (change,) = compare([only], cloud)

    assert not change.manifest_changed and change.upload == [] and change.remove == []


def test_only_changed_files_go_up_and_dropped_ones_go(tmp_path):
    root = _project(tmp_path / "Projekt")
    (old,) = embryo_sets(root)
    (root / "Templates" / "Standard" / "04_Finanz" / "Liesmich.md").write_text("Neu")
    (root / "Templates" / "Standard" / "04_Finanz" / ".MyOS" / "batch.svg").unlink()
    (new,) = embryo_sets(root)
    cloud = FakeCloud({"/.MyOS/Embryos.json": json.dumps(old.manifest).encode()})

    (change,) = compare([new], cloud)

    assert change.upload == ["04_Finanz/Liesmich.md"]
    assert change.remove == ["04_Finanz/.MyOS/batch.svg"]


def test_a_subproject_missing_in_the_cloud_is_left_out(tmp_path):
    root = _project(tmp_path / "Projekt")
    _project(root / "Haus")
    sets = embryo_sets(root)

    changes = compare(sets, FakeCloud())

    assert [(c.project, c.missing) for c in changes] == [("/", False), ("/Haus", True)]


def test_send_uploads_the_files_then_the_manifest_then_removes(tmp_path):
    root = _project(tmp_path / "Projekt")
    (old,) = embryo_sets(root)
    (root / "Templates" / "Standard" / "04_Finanz" / ".MyOS" / "batch.svg").unlink()
    (new,) = embryo_sets(root)
    cloud = FakeCloud({"/.MyOS/Embryos.json": json.dumps(old.manifest).encode(),
                       "/.MyOS/Embryos/04_Finanz/.MyOS/batch.svg": b"<svg/>"})
    (change,) = compare([new], cloud)
    change.upload.append("04_Finanz/Liesmich.md")  # as if it had changed too

    send(new, change, cloud)

    assert cloud.calls == [
        ("MKCOL", "/.MyOS"), ("MKCOL", "/.MyOS/Embryos"), ("MKCOL", "/.MyOS/Embryos/04_Finanz"),
        ("PUT", "/.MyOS/Embryos/04_Finanz/Liesmich.md"),
        ("PUT", "/.MyOS/Embryos.json"),
        ("DELETE", "/.MyOS/Embryos/04_Finanz/.MyOS/batch.svg"),
    ]
    assert json.loads(cloud.files["/.MyOS/Embryos.json"]) == new.manifest
    assert cloud.files["/.MyOS/Embryos/04_Finanz/Liesmich.md"] == b"Finanzen"


def test_send_puts_a_subprojects_files_below_it(tmp_path):
    root = _project(tmp_path / "Projekt")
    _project(root / "Haus")
    sub = embryo_sets(root)[1]
    cloud = FakeCloud(folders=("/", "/Haus"))
    (change,) = compare([sub], cloud)

    send(sub, change, cloud)

    assert ("PUT", "/Haus/.MyOS/Embryos/04_Finanz/.MyOS/icons/euro.svg") in cloud.calls
    assert ("MKCOL", "/Haus/.MyOS/Embryos/04_Finanz/.MyOS/icons") in cloud.calls


def test_a_project_without_templates_sends_nothing_to_an_empty_cloud(tmp_path):
    root = tmp_path / "Leer"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")

    (change,) = compare(embryo_sets(root), FakeCloud())

    assert not change.manifest_changed and change.upload == [] and change.remove == []


def test_cloud_paths_are_what_the_upload_creates(tmp_path):
    root = _project(tmp_path / "Projekt")
    _project(root / "Haus")

    paths = cloud_paths(embryo_sets(root)[1])

    assert paths[:3] == ["/Haus/.MyOS", "/Haus/.MyOS/Embryos.json", "/Haus/.MyOS/Embryos"]
    assert "/Haus/.MyOS/Embryos/04_Finanz/.MyOS/icons/euro.svg" in paths
    assert "/Haus/.MyOS/Embryos/04_Finanz/.MyOS/icons" in paths
