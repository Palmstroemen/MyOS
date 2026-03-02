"""
Daemon API: JSON request/response protocol over Unix socket.
One request = one line (JSON); one response = one line (JSON).
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def encode_request(method: str, params: Optional[Dict[str, Any]] = None) -> str:
    msg: Dict[str, Any] = {"method": method}
    if params is not None:
        msg["params"] = params
    return json.dumps(msg, ensure_ascii=False) + "\n"


def decode_request(line: str) -> Optional[Dict[str, Any]]:
    line = (line or "").strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def encode_response(ok: bool, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> str:
    msg: Dict[str, Any] = {"ok": ok}
    if result is not None:
        msg["result"] = result
    if error is not None:
        msg["error"] = error
    return json.dumps(msg, ensure_ascii=False) + "\n"


def decode_response(line: str) -> Optional[Dict[str, Any]]:
    line = (line or "").strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None
