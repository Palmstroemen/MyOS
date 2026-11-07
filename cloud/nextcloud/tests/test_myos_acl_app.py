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
