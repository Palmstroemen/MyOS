# brand.py - the product's name in one place
#
# Everything that carries the name where it lasts - the folder of a project's own settings, the
# user's settings folder, the environment variables, the extended attributes - takes it from
# here. A new name is a change in this file; what exists under the old one is still read
# (LEGACY_ENV_PREFIXES) or moved over by a migration.
#
# QML has its copy in Scope/js/Brand.js (core/tests/unit/test_brand.py compares them).
#
# Not reachable from here, and to be changed by hand with a new name: the Nextcloud app
# (cloud/nextcloud/myos_acl: its id cannot change, a new id is a new app), the Dockerfile's
# ENV lines, ClipboardTool (stands alone, started by CopyQ), shell scripts, the documentation
# and translations. core/tests/unit/test_brand.py keeps new literals out of the Python code.

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping, Optional, Union

NAME = "Seiton"
META_DIR = ".seiton"  # a project's (or a template's) own settings, inside the folder
CONFIG_DIR = "seiton"  # the user's settings, below XDG_CONFIG_HOME
ENV_PREFIX = "SEITON_"
XATTR_PREFIX = "user.seiton."
HTTP_HEADER_PREFIX = "X-Seiton-"  # between the platform's bridge and the core service
URL_SCHEME = "seiton"  # links in notes: seiton:open?scope=... (PostFix/exercise_links.py)

# Former names, newest first (MyOS until 2026-11-14): environment variables under them are
# still read; settings folders, the user's settings and extended attributes under them are
# moved over by core/name_migration.py (python3 cli/migrate_name.py).
LEGACY_ENV_PREFIXES: tuple = ("MYOS_",)
LEGACY_META_DIRS: tuple = (".MyOS",)
LEGACY_CONFIG_DIRS: tuple = ("MyOS",)
LEGACY_XATTR_PREFIXES: tuple = ("user.myos.",)
LEGACY_URL_SCHEMES: tuple = ("myos",)  # still followed: notes keep their links


def meta_dir(folder: Union[str, Path]) -> Path:
    """The folder's own settings folder (folder/.seiton); it need not exist."""
    return Path(folder) / META_DIR


def config_dir(env: Optional[Mapping[str, str]] = None) -> Path:
    """The user's settings folder (~/.config/seiton, or below XDG_CONFIG_HOME)."""
    env = os.environ if env is None else env
    return Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config") / CONFIG_DIR


def env_name(key: str) -> str:
    """The environment variable for key under the current name (ACL_MODE -> SEITON_ACL_MODE)."""
    return ENV_PREFIX + key


def getenv(key: str, default: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The environment variable for key (ACL_MODE: SEITON_ACL_MODE); under a former name when
    the current one is not set, else default. An empty value counts as set."""
    env = os.environ if env is None else env
    for prefix in (ENV_PREFIX, *LEGACY_ENV_PREFIXES):
        value = env.get(prefix + key)
        if value is not None:
            return value
    return default


def file_name(kind: str) -> str:
    """The name of a file of ours outside a project (desktop entry, socket, thumbnailer):
    file_name("suntree.desktop") -> "seiton-suntree.desktop"."""
    return f"{CONFIG_DIR.lower()}-{kind}"


def legacy_file_names(kind: str) -> tuple:
    """The same file under the former names ("myos-suntree.desktop"): replaced when installing."""
    return tuple(f"{name.lower()}-{kind}" for name in LEGACY_CONFIG_DIRS)


def marker(kind: str) -> str:
    """The name of a marker file of ours: marker("demo") -> ".seiton-demo"."""
    return "." + file_name(kind)


def legacy_markers(kind: str) -> tuple:
    """The same marker under the former names (".myos-demo"): still recognised."""
    return tuple("." + name for name in legacy_file_names(kind))
