"""Against a real Nextcloud test instance with the app myos_acl: myacl sync, then entries
created, moved or copied on the way stay hidden from who may only pass there.

Runs only when asked for (not part of the suite):
  MYOS_NC_TEST_URL=http://localhost:8081 MYOS_NC_TEST_PASSWORDS=<file with "user password" lines> \\
      python3 -m pytest cloud/nextcloud/tests
The instance needs the Team folder "Projekte" (advanced permissions on, "oliver" may manage
them) given to the groups below, with the folders Familie/{Finanz,Fotos,Kind} and Job.
Security: it changes that Team folder's rules - never point it at a real one.
"""

import base64
import functools
import os
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest

URL = os.environ.get("MYOS_NC_TEST_URL", "")
pytestmark = pytest.mark.skipif(not URL, reason="needs MYOS_NC_TEST_URL (a Nextcloud test instance)")

ACLS = (
    "# Permissions\n\n"
    "## Admin\n- /*: read, write, delete, change\n\n"
    "## Familie\n- /Familie/: read, write, delete\n- /Familie/Finanz/: read\n\n"
    "## Kinder\n- /Familie/Kind/: read, write\n\n"
    "## Buchhaltung\n- /Familie/Finanz/: read, write\n\n"
    "## Team\n- /Job/: read, write\n\n"
    "# Users\nOliver: Admin\nLisa: Familie\nTom: Kinder\nAnna: Buchhaltung, Team\nKarl: Team\n"
)
NEXTCLOUD_MD = (
    f"# Nextcloud\nurl: {URL}\nfolder: Projekte\ngroup: Admin, Familie, Kinder, Buchhaltung, Team\n\n"
    "# Accounts\nOliver: oliver\nLisa: lisa\nTom: tom\nAnna: anna\nKarl: karl\n"
)


@functools.lru_cache(maxsize=None)
def _passwords():
    # Read once: the file may be a pipe (MYOS_NC_TEST_PASSWORDS=<(ssh host cat users.txt)).
    lines = Path(os.environ["MYOS_NC_TEST_PASSWORDS"]).read_text().split("\n")
    return dict(line.split(None, 1) for line in lines if line.strip())


def _dav(user, method, path, headers=None, body=None):
    token = base64.b64encode(f"{user}:{_passwords()[user]}".encode()).decode()
    url = f"{URL}/remote.php/dav/files/{user}/Projekte/{path}"
    request = urllib.request.Request(url, data=body, method=method,
                                     headers={"Authorization": f"Basic {token}", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, ""


def _sees(user, folder, name):
    status, body = _dav(user, "PROPFIND", folder, {"Depth": "1"})
    return status == 207 and f"/{name}" in body


def _sync(tmp_path):
    root = tmp_path / "Projekte"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    (root / ".MyOS" / "Nextcloud.md").write_text(NEXTCLOUD_MD)
    # A template: Familie (there) with the embryo Neu, whose birth copies Liesmich.md and .MyOS.
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    neu = root / "Templates" / "Standard" / "Familie" / "Neu"
    (neu / ".MyOS").mkdir(parents=True)
    (neu / ".MyOS" / "Tags.md").write_text("# Tags\n")
    (neu / "Liesmich.md").write_text("Neu in Familie")
    # Familie a subproject: myacl sync puts its embryos into Familie/.MyOS.
    (root / "Familie" / ".MyOS").mkdir(parents=True)
    (root / "Familie" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    script = Path(__file__).resolve().parents[3] / "cli" / "myacl.py"
    env = {k: v for k, v in os.environ.items() if not k.startswith("MYOS_ACL")}
    env.update(MYOS_NEXTCLOUD_USER="oliver", MYOS_NEXTCLOUD_PASSWORD=_passwords()["oliver"],
               XDG_CONFIG_HOME=str(tmp_path / "config"))
    result = subprocess.run([sys.executable, str(script), "sync", "--yes", str(root)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    return root, script, env


@pytest.fixture
def synced(tmp_path):
    root, script, env = _sync(tmp_path)
    made = []
    yield made
    for path in reversed(made):
        _dav("oliver", "DELETE", path)
    check = subprocess.run([sys.executable, str(script), "sync", "--dry-run", str(root)],
                           capture_output=True, text=True, env=env)
    assert " 0 change(s)" in check.stdout, check.stdout + check.stderr


def test_a_new_folder_on_the_way_stays_hidden(synced):
    name = f"neu-{uuid.uuid4().hex[:6]}"
    assert _dav("oliver", "MKCOL", f"Familie/{name}")[0] == 201
    synced.append(f"Familie/{name}")

    assert not _sees("tom", "Familie/", name)  # Tom only passes through Familie
    assert not _sees("anna", "Familie/", name)
    assert _sees("lisa", "Familie/", name)  # Lisa may read Familie by ACLs.md
    assert _sees("tom", "Familie/", "Kind")


def test_a_new_file_at_the_root_stays_hidden(synced):
    name = f"neu-{uuid.uuid4().hex[:6]}.txt"
    assert _dav("oliver", "PUT", name, body=b"x")[0] in (201, 204)
    synced.append(name)

    assert not any(_sees(user, "", name) for user in ("tom", "lisa", "anna", "karl"))
    assert _sees("oliver", "", name)


def test_moved_and_copied_entries_stay_hidden(synced):
    moved, copied = f"weg-{uuid.uuid4().hex[:6]}.txt", f"kopie-{uuid.uuid4().hex[:6]}.txt"
    assert _dav("anna", "PUT", f"Job/{moved}", body=b"x")[0] in (201, 204)
    destination = f"{URL}/remote.php/dav/files/oliver/Projekte/Familie/"
    assert _dav("oliver", "MOVE", f"Job/{moved}", {"Destination": destination + moved})[0] in (201, 204)
    synced.append(f"Familie/{moved}")
    assert _dav("oliver", "COPY", f"Familie/{moved}", {"Destination": destination + copied})[0] in (201, 204)
    synced.append(f"Familie/{copied}")

    for user in ("tom", "anna"):
        assert not _sees(user, "Familie/", moved) and not _sees(user, "Familie/", copied)
    assert _sees("lisa", "Familie/", moved)


def test_the_embryos_are_readable_for_who_only_passes_but_the_rest_of_myos_is_not(synced):
    status, body = _dav("tom", "GET", ".MyOS/Embryos.json")
    assert status == 200 and '"Neu"' in body
    assert _dav("tom", "GET", ".MyOS/Embryos/Familie/Neu/Liesmich.md")[0] == 200
    for secret in (".MyOS/ACLs.md", ".MyOS/Nextcloud.md", ".MyOS/Project.md"):
        assert _dav("tom", "GET", secret)[0] == 404, secret
    assert _dav("karl", "GET", ".MyOS/Embryos.json")[0] == 200


def test_a_birth_as_the_browser_does_it_copies_the_template_and_stays_hidden_on_the_way(synced):
    # What src/main.js does: MKCOL the folder and its hidden folders, COPY the files.
    name = f"Neu-{uuid.uuid4().hex[:6]}"  # a fresh name; the copy is what counts
    assert _dav("lisa", "MKCOL", f"Familie/{name}")[0] == 201
    synced.append(f"Familie/{name}")
    assert _dav("lisa", "MKCOL", f"Familie/{name}/.MyOS")[0] == 201
    destination = f"{URL}/remote.php/dav/files/lisa/Projekte/Familie/{name}/"
    for rel in ("Liesmich.md", ".MyOS/Tags.md"):
        status = _dav("lisa", "COPY", f".MyOS/Embryos/Familie/Neu/{rel}", {"Destination": destination + rel})[0]
        assert status in (201, 204), rel

    status, body = _dav("lisa", "GET", f"Familie/{name}/Liesmich.md")
    assert status == 200 and body == "Neu in Familie"
    assert not _sees("tom", "Familie/", name)


def test_who_may_write_a_project_may_not_write_its_rights_and_sync_files(synced):
    # Lisa may write in Familie (ACLs.md), but only who may change the rights may write
    # Familie/.MyOS/Embryos.json - else her file would be copied into other people's births.
    status, body = _dav("lisa", "GET", "Familie/.MyOS/Embryos.json")
    assert status == 200
    assert _dav("lisa", "PUT", "Familie/.MyOS/Embryos.json", body=b"{}")[0] == 403
    assert _dav("lisa", "GET", "Familie/.MyOS/Embryos.json")[1] == body
    assert _dav("lisa", "DELETE", "Familie/.MyOS/Embryos.json")[0] == 403
    name = f"Desk-{uuid.uuid4().hex[:6]}.md"  # the rest of .MyOS as in MyOS: her rights
    assert _dav("lisa", "PUT", f"Familie/.MyOS/{name}", body=b"x")[0] in (201, 204)
    synced.append(f"Familie/.MyOS/{name}")
