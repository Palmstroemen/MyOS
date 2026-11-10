"""The core service over HTTP ("Designdocument MyOS Core Service.md", 4 and 6): only who
knows the shared secret is answered (myos_acl, which passes the logged-in account along);
an account without a person in the project's "# Accounts" sees nothing."""

import json
import threading
import urllib.error
import urllib.request

import pytest

from cloud.service.server import make_server, nextcloud_person

SECRET = "s3cret-for-tests-only-0123456789"


@pytest.fixture
def service(shadow):
    (shadow / ".MyOS" / "Nextcloud.md").write_text(
        "# Nextcloud\nfolder: Projekte\n\n# Accounts\nOliver: oliver\nLisa: lisa.m\nKarl: karl\n")
    server = make_server(shadow, SECRET, lambda account: nextcloud_person(shadow, account), port=0, place="/Projekte")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


def _get(url, secret=SECRET, account="lisa.m"):
    headers = {"X-MyOS-Account": account}
    if secret is not None:
        headers["X-MyOS-Secret"] = secret
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=10) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read() or b"null")


def test_a_lens_is_answered_for_the_account_s_person(service):
    status, body = _get(service + "/lens?path=/04_Finanz/Projekte")

    assert status == 200 and [entry["name"] for entry in body["entries"]] == ["Familie"]
    assert _get(service + "/lens?path=/04_Finanz/Projekte/Familie")[1] == {
        "path": "/04_Finanz/Projekte/Familie", "real": "/Familie/04_Finanz", "fallback": False,
        "place": "/Projekte"}  # where the real folder lies in the user's files: place + real
    assert "place" not in body


@pytest.mark.parametrize("secret", [None, "", "wrong"])
def test_without_the_secret_nothing_is_answered(service, secret):
    assert _get(service + "/lens?path=/", secret=secret)[0] == 401


@pytest.mark.parametrize("account", ["", "tom", "Lisa"])
def test_an_account_without_a_person_sees_nothing(service, account):
    assert _get(service + "/lens?path=/", account=account)[0] == 403


def test_denied_missing_and_unknown(service):
    assert _get(service + "/lens?path=/04_Finanz/Projekte/Job")[0] == 403
    assert _get(service + "/lens?path=/09_Nichts")[0] == 404
    assert _get(service + "/nichts")[0] == 404


def test_a_short_secret_is_refused(shadow):
    with pytest.raises(ValueError):
        make_server(shadow, "kurz", lambda account: None, port=0)


def test_while_there_is_no_shadow_yet_the_service_says_so(shadow):
    server = make_server(lambda: None, SECRET, lambda account: "lisa", port=0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert _get(f"http://127.0.0.1:{server.server_address[1]}/lens?path=/")[0] == 503
    finally:
        server.shutdown()
        server.server_close()
