"""Reading a Nextcloud Team folder over WebDAV (tree and "advanced permissions" rules) and
comparing its rules with the planned ones (myacl sync --dry-run). No network: a fake
transport answers like Nextcloud 32 does."""

import json
import re
from urllib.parse import quote

import pytest

from core.acl_nextcloud import PlannedRule, diff, updates
from core.nextcloud_dav import ExistingRule, NextcloudDAV, NextcloudError, tree_functions

BASE = "/remote.php/dav/files/oliver/Projekte"


def _response(href, is_dir, rules=(), enabled=True, manage=True):
    acl = "".join(
        f"<nc:acl><nc:acl-mapping-type>{kind}</nc:acl-mapping-type><nc:acl-mapping-id>{who}</nc:acl-mapping-id>"
        f"<nc:acl-mapping-display-name>{who}</nc:acl-mapping-display-name><nc:acl-mask>{mask}</nc:acl-mask>"
        f"<nc:acl-permissions>{perms}</nc:acl-permissions></nc:acl>"
        for kind, who, mask, perms in rules
    )
    kind = "<d:collection/>" if is_dir else ""
    return (
        f"<d:response><d:href>{href}</d:href><d:propstat><d:prop><d:resourcetype>{kind}</d:resourcetype>"
        f"<nc:acl-enabled>{int(enabled)}</nc:acl-enabled><nc:acl-can-manage>{int(manage)}</nc:acl-can-manage>"
        f"<nc:acl-list>{acl}</nc:acl-list></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>"
    )


def _multistatus(*responses):
    return (
        '<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" '
        'xmlns:nc="http://nextcloud.org/ns">' + "".join(responses) + "</d:multistatus>"
    ).encode()


# A folder's listing: the folder itself, then its entries (Depth: 1), keyed by DAV path.
SERVER = {
    BASE + "/": _multistatus(
        _response(BASE + "/", True, [("group", "Projekte", 31, 0), ("user", "oliver", 31, 7)]),
        _response(BASE + "/Familie/", True),
        _response(BASE + "/Job/", True, [("group", "Kinder", 1, 0)]),
    ),
    BASE + "/Familie/": _multistatus(
        _response(BASE + "/Familie/", True),
        _response(BASE + "/Familie/Kind/", True, [("user", "tom", 31, 7)]),
        _response(BASE + "/Familie/" + quote("Notiz für Tom.md"), False),
    ),
    BASE + "/Familie/Kind/": _multistatus(_response(BASE + "/Familie/Kind/", True)),
    BASE + "/Job/": _multistatus(_response(BASE + "/Job/", True)),
}


def _transport(server, calls=None, patched=None, refuse=None, infinity=False):
    def request(method, url, body, headers, auth):
        path = url.split("8081", 1)[1]
        if calls is not None:
            calls.append((method, path, headers.get("Depth")))
        if headers.get("Depth") == "infinity":
            if not infinity:  # as with dav.propfind.depth_infinity switched off
                return 403, b""
            # Each entry once, as a server answers (the fake's listings repeat a folder).
            seen, responses = set(), []
            for key in sorted(server):
                if key.startswith(path):
                    for response in re.findall(r"<d:response>.*?</d:response>", server[key].decode(), re.S):
                        href = re.search(r"<d:href>(.*?)</d:href>", response).group(1)
                        if href not in seen:
                            seen.add(href)
                            responses.append(response)
            return 207, _multistatus(*responses)
        if method == "PROPPATCH":
            if patched is not None:
                patched.append((path, body))
            status = refuse or "HTTP/1.1 200 OK"
            return 207, _multistatus(
                f"<d:response><d:href>{path}</d:href><d:propstat><d:prop><nc:acl-list/></d:prop>"
                f"<d:status>{status}</d:status></d:propstat>"
                + ("<d:responsedescription>You cannot remove your own read permission.</d:responsedescription>" if refuse else "")
                + "</d:response>"
            )
        if path not in server:
            return 404, b""
        return 207, server[path]

    return request


def _dav(server=SERVER, calls=None, patched=None, refuse=None, infinity=False):
    return NextcloudDAV("http://localhost:8081", "oliver", "secret", "Projekte",
                        transport=_transport(server, calls, patched, refuse, infinity))


def test_the_tree_holds_every_entry_with_its_rules():
    tree = _dav().tree()

    assert set(tree) == {"/", "/Familie", "/Job", "/Familie/Kind", "/Familie/Notiz für Tom.md"}
    assert tree["/"].rules == [ExistingRule("group", "Projekte", 31, 0), ExistingRule("user", "oliver", 31, 7)]
    assert tree["/Familie/Kind"].rules == [ExistingRule("user", "tom", 31, 7)]
    assert not tree["/Familie/Notiz für Tom.md"].is_dir


def test_without_infinite_depth_only_folders_are_listed_one_level_at_a_time():
    calls = []
    _dav(calls=calls).tree()

    assert calls[0] == ("PROPFIND", BASE + "/", "infinity")  # refused: then folder by folder
    assert all(method == "PROPFIND" and depth == "1" for method, _path, depth in calls[1:])
    assert sorted(path for _m, path, _d in calls[1:]) == sorted(SERVER)


def test_with_infinite_depth_one_request_gives_the_whole_tree():
    # One PROPFIND instead of one per folder: seconds less for every round of the core service.
    calls = []
    tree = _dav(calls=calls, infinity=True).tree()

    assert calls == [("PROPFIND", BASE + "/", "infinity")]
    assert tree == _dav().tree()


def test_exists_and_children_follow_the_cloud():
    exists, children = tree_functions(_dav().tree())

    assert exists("/Familie/Kind") and not exists("/Familie/Fotos")
    assert children("/Familie") == ["Kind", "Notiz für Tom.md"]


def test_a_folder_without_advanced_permissions_is_refused():
    server = {BASE + "/": _multistatus(_response(BASE + "/", True, enabled=False))}

    with pytest.raises(NextcloudError, match="advanced permissions"):
        _dav(server).tree()


def test_an_account_that_may_not_manage_the_rules_is_refused():
    server = {BASE + "/": _multistatus(_response(BASE + "/", True, manage=False))}

    with pytest.raises(NextcloudError, match="manage"):
        _dav(server).tree()


def test_a_missing_folder_is_refused():
    with pytest.raises(NextcloudError, match="Projekte"):
        _dav({}).tree()


def test_diff_adds_changes_keeps_and_removes():
    tree = _dav().tree()
    planned = [
        PlannedRule("/", "group", "Projekte", frozenset()),  # as it is
        PlannedRule("/", "user", "oliver", frozenset({"read", "write", "create", "delete"})),  # 7 -> 15
        PlannedRule("/Familie", "user", "tom", frozenset({"read"})),  # new
    ]

    changes = {(c.path, c.kind, c.account): c for c in diff(planned, tree)}

    assert ("/", "group", "Projekte") not in changes
    assert changes[("/", "user", "oliver")].before == ExistingRule("user", "oliver", 31, 7)
    assert changes[("/", "user", "oliver")].after == {"read", "write", "create", "delete"}
    assert changes[("/Familie", "user", "tom")].before is None
    assert changes[("/Job", "group", "Kinder")].after is None  # not from ACLs.md: would go
    assert changes[("/Familie/Kind", "user", "tom")].after is None


PLANNED = [
    PlannedRule("/", "group", "Projekte", frozenset()),
    PlannedRule("/", "user", "oliver", frozenset({"read", "write", "create", "delete"})),
    PlannedRule("/Familie", "user", "tom", frozenset({"read"})),
    PlannedRule("/Familie/Kind", "user", "tom", frozenset({"read", "write", "create"})),
]


def test_updates_send_the_whole_list_of_each_changed_path_deepest_first():
    tree = _dav().tree()
    planned = PLANNED[:2] + PLANNED[2:3]  # /Familie/Kind loses tom's rule, /Job loses Kinder's

    result = updates(planned, diff(planned, tree))

    assert [path for path, _rules in result] == ["/Familie/Kind", "/Familie", "/Job", "/"]
    assert dict(result)["/"] == [PLANNED[0], PLANNED[1]]  # the unchanged group rule is sent again
    assert dict(result)["/Familie/Kind"] == [] and dict(result)["/Job"] == []


def test_set_rules_sends_the_rules_as_nextcloud_reads_them():
    patched = []

    _dav(patched=patched).set_rules("/Familie/Kind", [PLANNED[3]])

    (path, body), = patched
    assert path == BASE + "/Familie/Kind"
    text = body.decode()
    assert "<nc:acl-mapping-type>user</nc:acl-mapping-type>" in text
    assert "<nc:acl-mapping-id>tom</nc:acl-mapping-id>" in text
    assert "<nc:acl-mask>31</nc:acl-mask>" in text and "<nc:acl-permissions>7</nc:acl-permissions>" in text


def test_a_refused_update_says_why():
    with pytest.raises(NextcloudError, match="own read permission"):
        _dav(refuse="HTTP/1.1 403 Forbidden").set_rules("/", [])


def test_a_way_rule_is_sent_with_its_mask():
    patched = []

    _dav(patched=patched).set_rules("/Familie", [PlannedRule("/Familie", "user", "tom", frozenset({"read"}), traverse=True)])

    assert "<nc:acl-mask>15</nc:acl-mask><nc:acl-permissions>1</nc:acl-permissions>" in patched[0][1].decode()


def test_a_rule_with_the_wrong_mask_is_a_change():
    tree = _dav().tree()  # tom holds 31/7 on /Familie/Kind
    planned = [PlannedRule("/Familie/Kind", "user", "tom", frozenset({"read", "write", "create"}), traverse=True)]

    assert ("/Familie/Kind", "user", "tom") in {(c.path, c.kind, c.account) for c in diff(planned, tree)}


# --- files (the embryos of myacl sync) ---

def _files_transport(answers, calls):
    def request(method, url, body, headers, auth):
        path = url.split("8081", 1)[1]
        calls.append((method, path, body, headers.get("Overwrite")))
        return answers.get((method, path), (404, b""))

    return request


def _files_dav(answers, calls):
    return NextcloudDAV("http://localhost:8081", "oliver", "secret", "Projekte",
                        transport=_files_transport(answers, calls))


def test_get_returns_the_content_or_none():
    calls = []
    dav = _files_dav({("GET", BASE + "/.MyOS/Embryos.json"): (200, b"{}")}, calls)

    assert dav.get("/.MyOS/Embryos.json") == b"{}"
    assert dav.get("/.MyOS/fehlt.json") is None


def test_put_mkcol_and_delete_accept_what_nextcloud_answers():
    calls = []
    dav = _files_dav({
        ("PUT", BASE + "/" + quote("Für Tom.md")): (201, b""),
        ("MKCOL", BASE + "/.MyOS"): (405, b""),  # already there
        ("DELETE", BASE + "/alt.md"): (204, b""),
    }, calls)

    dav.put("/Für Tom.md", b"x")
    dav.mkcol("/.MyOS")
    dav.delete("/alt.md")
    dav.delete("/schon-weg.md")  # 404: gone already

    assert calls[0] == ("PUT", BASE + "/" + quote("Für Tom.md"), b"x", None)


def test_a_refused_put_says_so():
    dav = _files_dav({("PUT", BASE + "/x.md"): (403, b"")}, [])

    with pytest.raises(NextcloudError, match="403"):
        dav.put("/x.md", b"x")


def test_exists_asks_the_cloud_for_the_entry():
    dav = _files_dav({("PROPFIND", BASE + "/Haus"): (207, _multistatus(_response(BASE + "/Haus/", True)))}, [])

    assert dav.exists("/Haus")
    assert not dav.exists("/Garten")


def test_the_etag_of_the_team_folder_tells_whether_anything_below_changed():
    # Nextcloud changes a folder's ETag when anything below it changes: one cheap request
    # tells the core service whether its shadow tree is still current.
    calls = []
    server = {BASE + "/": _multistatus(_response(BASE + "/", True).replace(
        "<d:resourcetype>", '<d:getetag>"6911a2"</d:getetag><d:resourcetype>'))}

    assert _dav(server, calls=calls).etag() == '"6911a2"'
    assert calls == [("PROPFIND", BASE + "/", "0")]
    with pytest.raises(NextcloudError, match="Projekte"):
        _dav({}).etag()


TAGS_URL = "/remote.php/dav/systemtags/"


def _tag(tag_id, name):
    return (f"<d:response><d:href>{TAGS_URL}{tag_id}</d:href><d:propstat><d:prop><oc:id>{tag_id}</oc:id>"
            f"<oc:display-name>{name}</oc:display-name></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>")


def test_the_instance_s_tags_are_read_by_name():
    tags = _multistatus(f"<d:response><d:href>{TAGS_URL}</d:href></d:response>", _tag(1, "Wichtig"), _tag(4, "in Arbeit"))
    calls = []

    def transport(method, url, body, headers, auth):
        calls.append((method, url.split("8081", 1)[1]))
        return 207, tags

    dav = NextcloudDAV("http://localhost:8081", "oliver", "secret", "Projekte", transport=transport)

    assert dav.system_tags() == {"Wichtig": "1", "in Arbeit": "4"}
    assert calls == [("PROPFIND", TAGS_URL)]


@pytest.mark.parametrize("status", [201, 409])  # 409: someone made it meanwhile
def test_a_tag_is_made_for_all_to_see_and_assign(status):
    sent = []

    def transport(method, url, body, headers, auth):
        sent.append((method, url.split("8081", 1)[1], json.loads(body), headers.get("Content-Type")))
        return status, b""

    NextcloudDAV("http://localhost:8081", "oliver", "secret", "Projekte", transport=transport).create_system_tag("in Arbeit")

    assert sent == [("POST", TAGS_URL, {"name": "in Arbeit", "userVisible": True, "userAssignable": True}, "application/json")]


def test_a_tag_the_server_refuses_says_why():
    dav = NextcloudDAV("http://localhost:8081", "oliver", "secret", "Projekte", transport=lambda *a: (403, b""))

    with pytest.raises(NextcloudError, match="403"):
        dav.create_system_tag("Wichtig")
