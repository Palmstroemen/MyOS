# server.py - the MyOS core service: the core's answers over HTTP
#
# See "cloud/nextcloud/Designdocument MyOS Core Service.md", 4, 6 and 8.1. Reached only from
# the platform's bridge (myos_acl for Nextcloud), never from a browser: the bridge sends the
# shared secret and the logged-in account. Read-only so far: GET /lens?path=.
#
#   MYOS_SHADOW_ROOT=/shadow MYOS_CORE_SECRET=... python3 -m cloud.service.server

from __future__ import annotations

import hmac
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Optional, Union
from urllib.parse import parse_qs, urlsplit

from cloud.service.lens import lens
from core.acl_nextcloud import read_nextcloud_md

logger = logging.getLogger(__name__)

MIN_SECRET_LENGTH = 24


def nextcloud_person(root: Union[str, Path], account: str) -> Optional[str]:
    """The person (lower-case key) whose Nextcloud account is account, by the project's
    .MyOS/Nextcloud.md "# Accounts" ("Lisa: lisa.m"); None for an account not listed."""
    _settings, accounts = read_nextcloud_md(Path(root) / ".MyOS" / "Nextcloud.md")
    people = [person for person, listed in accounts.items() if listed == account]
    return people[0] if account and len(people) == 1 else None


def make_server(root: Union[str, Path], secret: str, person_for: Callable[[str], Optional[str]],
                host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """The service for the shadow tree at root; person_for maps the account the bridge
    passes to a person of "# Users" (None: not one of them)."""
    # Security: the secret is all that keeps others out; a short one is refused.
    if len(secret or "") < MIN_SECRET_LENGTH:
        raise ValueError(f"the shared secret needs at least {MIN_SECRET_LENGTH} characters")
    root = Path(root).expanduser().resolve()
    expected = secret.encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if not hmac.compare_digest(self.headers.get("X-MyOS-Secret", "").encode(), expected):
                return self._answer(401, {"error": "unauthorized"})
            person = person_for(self.headers.get("X-MyOS-Account", ""))
            if not person:
                return self._answer(403, {"error": "unknown account"})
            url = urlsplit(self.path)
            if url.path != "/lens":
                return self._answer(404, {"error": "not found"})
            path = parse_qs(url.query).get("path", ["/"])[0]
            try:
                answer = lens(root, person, path)
            except PermissionError:
                return self._answer(403, {"error": "denied"})
            if answer is None:
                return self._answer(404, {"error": "not found"})
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
    root = os.environ.get("MYOS_SHADOW_ROOT", "")
    if not root or not Path(root).is_dir():
        raise SystemExit("MYOS_SHADOW_ROOT must name the shadow tree (a folder)")
    server = make_server(root, os.environ.get("MYOS_CORE_SECRET", ""),
                         lambda account: nextcloud_person(root, account),
                         host=os.environ.get("MYOS_CORE_HOST", "127.0.0.1"),
                         port=int(os.environ.get("MYOS_CORE_PORT", "8080")))
    logger.info("MyOS core service on %s:%s for %s", *server.server_address[:2], root)
    server.serve_forever()


if __name__ == "__main__":
    main()
