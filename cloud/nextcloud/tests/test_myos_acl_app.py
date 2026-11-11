"""Against a real Nextcloud test instance with the app myos_acl: myacl sync, then entries
created, moved or copied on the way stay hidden from who may only pass there.

Runs only when asked for (not part of the suite):
  MYOS_NC_TEST_URL=http://localhost:8081 MYOS_NC_TEST_PASSWORDS=<file with "user password" lines> \\
      python3 -m pytest cloud/nextcloud/tests
The instance needs the Team folder "Projekte" (advanced permissions on, "oliver" may manage
them) given to the groups below, with the folders Familie/{Finanz,Fotos,Kind} and Job.
Security: it changes that Team folder's rules - never point it at a real one.
The MyOS core service runs next to the instance, set up in myos_acl (core_url, core_secret;
cloud/service/server.py) and keeping the Team folder "Projekte" in step with its ACLs.md - the
tests wait until it is (_settled), and some test it.
"""

import base64
import functools
import json
import re
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
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
    "## Buchhaltung\n- /Familie/Finanz/: read, write\n- /Familie/Steuer/: read, write\n\n"
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


def _core(user, question, path):
    """The MyOS core's answer through myos_acl (OCS), as the browser asks for it."""
    token = base64.b64encode(f"{user}:{_passwords()[user]}".encode()).decode()
    url = f"{URL}/ocs/v2.php/apps/myos_acl/api/v1/{question}?format=json&path={urllib.parse.quote(path)}"
    request = urllib.request.Request(url, headers={"Authorization": f"Basic {token}", "OCS-APIRequest": "true"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())["ocs"]["data"]
    except urllib.error.HTTPError as error:
        return error.code, None


def _lens(user, path):
    return _core(user, "lens", path)


def _sees(user, folder, name):
    status, body = _dav(user, "PROPFIND", folder, {"Depth": "1"})
    return status == 207 and f"/{name}" in body


def _sync(tmp_path):
    root = tmp_path / "Projekte"
    (root / ".MyOS").mkdir(parents=True)
    (root / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    (root / ".MyOS" / "ACLs.md").write_text(ACLS)
    (root / ".MyOS" / "Nextcloud.md").write_text(NEXTCLOUD_MD)
    (root / ".MyOS" / "Tags.md").write_text("# Tags\n#Rechnung\n#Wichtig\n")
    # A template: Familie (there) with the embryo Neu, whose birth copies Liesmich.md and .MyOS.
    (root / ".MyOS" / "Templates.md").write_text("# Templates\nStandard\n")
    neu = root / ".MyOS" / "Templates" / "Standard" / "Familie" / "Neu"
    (neu / ".MyOS").mkdir(parents=True)
    (neu / ".MyOS" / "Tags.md").write_text("# Tags\n")
    (neu / "Liesmich.md").write_text("Neu in Familie")
    # And 00_Admin, which only the role Admin may read: nobody else sees it or its template.
    admin = root / ".MyOS" / "Templates" / "Standard" / "00_Admin"
    admin.mkdir(parents=True)
    (admin / "Liesmich.md").write_text("Nur für Admins")
    # And the department 04_Finanz, empty: for the lenses (/04_Finanz/Projekte).
    (root / ".MyOS" / "Templates" / "Standard" / "04_Finanz").mkdir()
    # Familie a subproject: myacl sync puts its embryos into Familie/.MyOS.
    (root / "Familie" / ".MyOS").mkdir(parents=True)
    (root / "Familie" / ".MyOS" / "Project.md").write_text("# MyOS Project\n")
    # The .MyOS files come into the Team folder as with a sync client (the core reads them
    # there), before the sync, so it sets their rules as well.
    _upload_myos(root, root)
    _upload_myos(root, root / "Familie")
    script = Path(__file__).resolve().parents[3] / "cli" / "myacl.py"
    env = {k: v for k, v in os.environ.items() if not k.startswith("MYOS_ACL")}
    env.update(MYOS_NEXTCLOUD_USER="oliver", MYOS_NEXTCLOUD_PASSWORD=_passwords()["oliver"],
               XDG_CONFIG_HOME=str(tmp_path / "config"))
    result = subprocess.run([sys.executable, str(script), "sync", "--yes", str(root)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stdout + result.stderr
    _settled(script, root, env)
    return root, script, env


def _settled(script, root, env, timeout=120):
    """Wait until the Team folder holds what ACLs.md says and stays so - the core service
    may still be bringing it in step - checked twice, a round of the core apart."""
    deadline, quiet = time.time() + timeout, 0
    while quiet < 2:
        check = subprocess.run([sys.executable, str(script), "sync", "--dry-run", str(root)],
                               capture_output=True, text=True, env=env)
        quiet = quiet + 1 if " 0 change(s)" in check.stdout else 0
        assert time.time() < deadline, check.stdout + check.stderr
        time.sleep(8)


def _upload_myos(root, project):
    myos = project / ".MyOS"
    for path in sorted([myos, *myos.rglob("*")]):
        rel = path.relative_to(root).as_posix()
        if path.is_dir():
            assert _dav("oliver", "MKCOL", rel)[0] in (201, 405), rel
        else:
            assert _dav("oliver", "PUT", rel, body=path.read_bytes())[0] in (201, 204), rel


@pytest.fixture
def synced(tmp_path):
    root, script, env = _sync(tmp_path)
    made = []
    yield made
    for path in reversed(made):
        _dav("oliver", "DELETE", path)
    _settled(script, root, env)


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


def test_an_embryo_is_readable_for_who_may_read_where_it_is_born(synced):
    # As Scope shows an embryo: Lisa may read /Familie/Neu, not /00_Admin; Tom only /Familie/Kind.
    assert _dav("lisa", "GET", ".MyOS/Embryos/Familie/Neu/Liesmich.md")[0] == 200
    assert _dav("lisa", "GET", ".MyOS/Embryos/00_Admin/Liesmich.md")[0] == 404
    assert _sees("lisa", ".MyOS/Embryos/", "Familie") and not _sees("lisa", ".MyOS/Embryos/", "00_Admin")
    assert _dav("oliver", "GET", ".MyOS/Embryos/00_Admin/Liesmich.md")[0] == 200
    assert _dav("tom", "PROPFIND", ".MyOS/Embryos", {"Depth": "0"})[0] == 207  # the list, for all in the project
    assert not _sees("tom", ".MyOS/Embryos/", "Familie")
    assert _dav("tom", "GET", ".MyOS/Embryos/Familie/Neu/Liesmich.md")[0] == 404
    for secret in (".MyOS/Embryos.json", ".MyOS/ACLs.md", ".MyOS/Nextcloud.md", ".MyOS/Project.md"):
        assert _dav("tom", "GET", secret)[0] == 404, secret
        assert _dav("lisa", "GET", secret)[0] == 404, secret


def test_a_birth_as_the_browser_does_it_copies_the_template_and_stays_hidden_on_the_way(synced):
    # What src/main.js does: ask the core what the level holds and what the birth does, then
    # create and copy with the user's own rights.
    status, body = _core("lisa", "level", "/Projekte/Familie")
    assert status == 200 and {"name": "00_Admin", "born": False} in body["folders"]
    assert _core("tom", "level", "/Projekte/Familie")[1]["folders"] == []  # Tom may create nothing there
    status, todo = _core("lisa", "birth", "/Projekte/Familie/00_Admin")
    assert status == 200 and todo["create"] == ["/Projekte/Familie/00_Admin"]
    synced.append("Familie/00_Admin")
    destination = f"{URL}/remote.php/dav/files/lisa"
    for folder in todo["create"]:
        assert _dav("lisa", "MKCOL", folder.removeprefix("/Projekte/"))[0] == 201, folder
    for copy in todo["copy"]:
        status = _dav("lisa", "COPY", copy["from"].removeprefix("/Projekte/"), {"Destination": destination + copy["to"]})[0]
        assert status in (201, 204), copy

    status, text = _dav("lisa", "GET", "Familie/00_Admin/Liesmich.md")
    assert status == 200 and text == "Nur für Admins"
    assert not _sees("tom", "Familie/", "00_Admin")
    _within(90, lambda: {"name": "00_Admin", "born": True} in _core("lisa", "level", "/Projekte/Familie")[1]["folders"],
            "the core does not see 00_Admin born")
    assert _core("lisa", "birth", "/Projekte/Familie/00_Admin")[0] == 404  # born already
    assert _core("tom", "birth", "/Projekte/Familie/04_Finanz")[0] == 403


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


def test_a_lens_shows_on_the_shelf_only_the_projects_one_may_read(synced):
    # The core sees the sync once its shadow tree is rebuilt (it watches the Team folder's ETag).
    deadline = time.time() + 60
    while _lens("lisa", "/04_Finanz/Projekte")[0] != 200 or not _lens("lisa", "/04_Finanz/Projekte")[1]["entries"]:
        assert time.time() < deadline, _lens("lisa", "/04_Finanz/Projekte")
        time.sleep(2)

    assert _lens("lisa", "/04_Finanz/Projekte")[1]["entries"] == [{"name": "Familie", "kind": "project"}]
    assert _lens("tom", "/04_Finanz/Projekte")[1]["entries"] == []  # Tom only passes through Familie
    status, body = _lens("lisa", "/04_Finanz/Projekte/Familie")
    assert status == 200 and body["real"] == "/Familie" and body["fallback"]  # 04_Finanz not born there
    assert _lens("tom", "/04_Finanz/Projekte/Familie")[0] == 403
    assert _lens("mia", "/")[0] == 403  # an account without a person in # Accounts


def _within(seconds, check, what):
    deadline = time.time() + seconds
    while not check():
        assert time.time() < deadline, what
        time.sleep(2)


def test_a_folder_made_later_gets_its_rights_from_acls_md_without_a_sync(synced):
    # Anna (Buchhaltung) may work in /Familie/Steuer/, which is not there yet. Lisa makes it;
    # on the way through Familie it is locked for Anna at once (myos_acl), then the core gives
    # her what ACLs.md says - no myacl sync.
    assert _dav("lisa", "MKCOL", "Familie/Steuer")[0] == 201
    synced.append("Familie/Steuer")

    _within(90, lambda: _sees("anna", "Familie/", "Steuer"), "Anna does not see Familie/Steuer")
    assert _dav("anna", "PUT", "Familie/Steuer/Beleg.txt", body=b"x")[0] in (201, 204)
    assert not _sees("tom", "Familie/", "Steuer")


def test_acls_md_edited_in_the_cloud_changes_the_rules(synced):
    # Oliver (change) gives the Team read on /Familie/Fotos/ in the cloud; Karl sees it. Back
    # as it was, he does not.
    original = _dav("oliver", "GET", ".MyOS/ACLs.md")[1].encode()
    edited = original.replace(b"## Team\n- /Job/: read, write\n", b"## Team\n- /Job/: read, write\n- /Familie/Fotos/: read\n")
    assert edited != original
    assert not _sees("karl", "Familie/", "Fotos")
    try:
        assert _dav("oliver", "PUT", ".MyOS/ACLs.md", body=edited)[0] in (201, 204)
        _within(90, lambda: _sees("karl", "Familie/", "Fotos"), "Karl does not see Familie/Fotos")
    finally:
        assert _dav("oliver", "PUT", ".MyOS/ACLs.md", body=original)[0] in (201, 204)
    _within(90, lambda: not _sees("karl", "Familie/", "Fotos"), "Karl still sees Familie/Fotos")


def test_an_acls_md_that_leaves_no_one_to_change_the_rights_changes_nothing(synced):
    original = _dav("oliver", "GET", ".MyOS/ACLs.md")[1].encode()
    try:
        assert _dav("oliver", "PUT", ".MyOS/ACLs.md", body=b"kaputt\n")[0] in (201, 204)
        time.sleep(30)  # a few rounds of the core
        assert _sees("lisa", "Familie/", "Fotos") and _sees("karl", "", "Job")
    finally:
        assert _dav("oliver", "PUT", ".MyOS/ACLs.md", body=original)[0] in (201, 204)


def test_saving_through_a_lens_bears_the_department_folder(synced):
    # What src/lens.js does when files are dropped on the unborn department folder: ask the
    # core what to bear, do it with the user's rights, put the files in. Lisa, in the finance
    # lens of Familie, where 04_Finanz is not born.
    status, here = _lens("lisa", "/04_Finanz/Projekte/Familie")
    assert status == 200 and here["fallback"] and here["unborn"] == "/Familie/04_Finanz"
    assert _core("tom", "bear", "/04_Finanz/Projekte/Familie")[0] == 403
    status, todo = _core("lisa", "bear", "/04_Finanz/Projekte/Familie")
    assert status == 200 and todo["real"] == "/Projekte/Familie/04_Finanz"
    synced.append("Familie/04_Finanz")
    destination = f"{URL}/remote.php/dav/files/lisa"
    for folder in todo["create"]:
        assert _dav("lisa", "MKCOL", folder.removeprefix("/Projekte/"))[0] == 201, folder
    for copy in todo["copy"]:
        assert _dav("lisa", "COPY", copy["from"].removeprefix("/Projekte/"), {"Destination": destination + copy["to"]})[0] in (201, 204)
    assert _dav("lisa", "PUT", "Familie/04_Finanz/Rechnung.txt", body=b"42")[0] in (201, 204)

    _within(60, lambda: not _lens("lisa", "/04_Finanz/Projekte/Familie")[1]["fallback"], "the lens still shows the project")
    assert _lens("lisa", "/04_Finanz/Projekte/Familie")[1]["real"] == "/Familie/04_Finanz"
    assert _dav("lisa", "GET", "Familie/04_Finanz/Rechnung.txt")[1] == "42"
    assert _dav("tom", "GET", "Familie/04_Finanz/Rechnung.txt")[0] == 404


def _system_tags(user):
    token = base64.b64encode(f"{user}:{_passwords()[user]}".encode()).decode()
    body = (b'<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop>'
            b"<oc:display-name/></d:prop></d:propfind>")
    request = urllib.request.Request(f"{URL}/remote.php/dav/systemtags/", data=body, method="PROPFIND",
                                     headers={"Authorization": f"Basic {token}", "Depth": "1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return set(re.findall(r"<oc:display-name>([^<]*)</oc:display-name>", response.read().decode()))


def test_the_tags_of_tags_md_are_nextcloud_s_tags_and_the_row_s(synced):
    # The core makes the tags of the projects' Tags.md as collaborative tags; the row asks
    # for those of a folder - none where one may not read it.
    assert {"Rechnung", "Wichtig"} <= _system_tags("lisa")
    assert _core("lisa", "tags", "/Projekte/Familie") == (200, {"tags": ["Rechnung", "Wichtig"]})
    assert _core("tom", "tags", "/Projekte/Familie") == (200, {"tags": []})
