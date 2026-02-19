from __future__ import annotations

from typing import Optional

from core.desktop_backends.base import DesktopBackend, NoopDesktopBackend


def build_backend(name: Optional[str]) -> DesktopBackend:
    backend_name = str(name or "").strip().lower()
    if backend_name == "kde":
        try:
            from core.desktop_backends.kde import KdeDesktopBackend

            return KdeDesktopBackend()
        except Exception:
            return NoopDesktopBackend()
    return NoopDesktopBackend()
