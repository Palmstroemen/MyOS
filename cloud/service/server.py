# server.py - the MyOS core service: the core's answers over HTTP
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 4, 6 and 8.1. Reached only from
# the platform's bridge (myos_acl for Nextcloud), never from a browser: the bridge sends the
# shared secret and the logged-in account. Read-only so far: GET /lens?path=.
#
# The shadow tree is a folder (MYOS_SHADOW_ROOT, for tests) or built from the Team folder with
# the service account and kept current (MYOS_NC_URL, _USER, _PASSWORD, _FOLDER; cloud/service/shadow.py):
#   MYOS_SHADOW_ROOT=/shadow MYOS_CORE_SECRET=... python3 -m cloud.service.server

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional, Union
from urllib.parse import parse_qs, urlsplit

from cloud.service.lens import lens
from cloud.service.shadow import ShadowKeeper
from core.acl_nextcloud import read_nextcloud_md
from core.nextcloud_dav import NextcloudDAV

logger = logging.getLogger(__name__)

MIN_SECRET_LENGTH = 24


def nextcloud_person(root: Union[str, Path], account: str) -> Optional[str]:
    """The person (lower-case key) whose Nextcloud account is account, by the project's
    .MyOS/Nextcloud.md "# Accounts" ("Lisa: lisa.m"); None for an account not listed."""
    _settings, accounts = read_nextcloud_md(Path(root) / ".MyOS" / "Nextcloud.md")
    people = [person for person, listed in accounts.items() if listed == account]
    return people[0] if account and len(people) == 1 else None


Root = Union[str, Path, Callable[[], Optional[Path]]]


def make_server(root: Root, secret: str, person_for: Callable[[str], Optional[str]],
                host: str = "127.0.0.1", port: int = 8080, place: str = "") -> ThreadingHTTPServer:
    """The service for the shadow tree at root (a folder, or a function naming the current
    one, None while there is none yet); person_for maps the account the bridge passes to a
    person of "# Users" (None: not one of them). place: where root lies in the platform's
    files ("/Projekte" for the Team folder), sent along with a real folder."""
    # Security: the secret is all that keeps others out; a short one is refused.
    if len(secret or "") < MIN_SECRET_LENGTH:
        raise ValueError(f"the shared secret needs at least {MIN_SECRET_LENGTH} characters")
    current = root if callable(root) else (lambda folder=Path(root).expanduser().resolve(): folder)
    expected = secret.encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if not hmac.compare_digest(self.headers.get("X-MyOS-Secret", "").encode(), expected):
                return self._answer(401, {"error": "unauthorized"})
            shadow = current()
            if shadow is None:
                return self._answer(503, {"error": "the shadow tree is being built"})
            person = person_for(self.headers.get("X-MyOS-Account", ""))
            if not person:
                return self._answer(403, {"error": "unknown account"})
            url = urlsplit(self.path)
            if url.path != "/lens":
                return self._answer(404, {"error": "not found"})
            path = parse_qs(url.query).get("path", ["/"])[0]
            try:
                answer = lens(shadow, person, path)
            except PermissionError:
                return self._answer(403, {"error": "denied"})
            if answer is None:
                return self._answer(404, {"error": "not found"})
            if answer["real"] is not None:
                answer["place"] = place
            self._answer(200, answer)

        def _answer(self, status: int, body: dict) -> None:
            data = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args) -> None:  # noqa: A002 - the base class's name
            logger.info("%s %s", self.address_string(), format % args)

    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    env = os.environ
    if env.get("MYOS_NC_URL"):
        keeper = ShadowKeeper(Path(env.get("MYOS_SHADOW_BASE", "/tmp/myos-shadow")), NextcloudDAV(
            env["MYOS_NC_URL"], env.get("MYOS_NC_USER", ""), env.get("MYOS_NC_PASSWORD", ""), env.get("MYOS_NC_FOLDER", "")))
        threading.Thread(target=_keep, args=(keeper, float(env.get("MYOS_SHADOW_POLL", "10"))), daemon=True).start()
        root: Root = lambda: keeper.root
        where = f"{env['MYOS_NC_URL']} {env.get('MYOS_NC_FOLDER', '')}"
    else:
        folder = env.get("MYOS_SHADOW_ROOT", "")
        if not folder or not Path(folder).is_dir():
            raise SystemExit("MYOS_SHADOW_ROOT must name the shadow tree (a folder), or MYOS_NC_URL a Nextcloud")
        root, where = Path(folder), folder

    def person_for(account: str) -> Optional[str]:
        shadow = root() if callable(root) else root
        return nextcloud_person(shadow, account) if shadow is not None else None

    server = make_server(root, env.get("MYOS_CORE_SECRET", ""), person_for,
                         host=env.get("MYOS_CORE_HOST", "127.0.0.1"), port=int(env.get("MYOS_CORE_PORT", "8080")),
                         place="/" + env.get("MYOS_NC_FOLDER", "").strip("/") if env.get("MYOS_NC_URL") else "")
    logger.info("MyOS core service on %s:%s for %s", *server.server_address[:2], where)
    server.serve_forever()


def _keep(keeper: ShadowKeeper, every: float) -> None:
    """Keep the shadow current: look at the Team folder's ETag every so many seconds."""
    while True:
        try:
            if keeper.refresh():
                logger.info("shadow tree built at %s", keeper.root)
        except Exception as error:  # the service stays up; the next round tries again
            logger.error("shadow tree not built: %s", error)
        time.sleep(every)


if __name__ == "__main__":
    main()
