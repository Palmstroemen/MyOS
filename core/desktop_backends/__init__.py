from __future__ import annotations

import os
from typing import Optional

from core.desktop_backends.base import DesktopBackend, NoopDesktopBackend


def detect_backend_name() -> str:
    """Backend for the running desktop session (XDG_CURRENT_DESKTOP), "none" if unknown."""
    desktops = [part.strip().lower() for part in str(os.environ.get("XDG_CURRENT_DESKTOP") or "").split(":")]
    if any("cinnamon" in name for name in desktops):
        return "cinnamon"
    if "gnome" in desktops:
        return "gnome"
    if "kde" in desktops:
        return "kde"
    return "none"


def build_backend(name: Optional[str]) -> DesktopBackend:
    backend_name = str(name or "").strip().lower()
    if backend_name == "auto":
        backend_name = detect_backend_name()
    try:
        if backend_name == "kde":
            from core.desktop_backends.kde import KdeDesktopBackend

            return KdeDesktopBackend()
        if backend_name in {"cinnamon", "gnome"}:
            from core.desktop_backends.gnome import GnomeFamilyDesktopBackend

            return GnomeFamilyDesktopBackend(backend_name)
    except Exception:
        return NoopDesktopBackend()
    return NoopDesktopBackend()
