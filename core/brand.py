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

NAME = "MyOS"
META_DIR = ".MyOS"  # a project's (or a template's) own settings, inside the folder
CONFIG_DIR = "MyOS"  # the user's settings, below XDG_CONFIG_HOME
ENV_PREFIX = "MYOS_"
XATTR_PREFIX = "user.myos."

# Prefixes of former names, read when the current one is not set (newest first).
LEGACY_ENV_PREFIXES: tuple = ()


def meta_dir(folder: Union[str, Path]) -> Path:
    """The folder's own settings folder (folder/.MyOS); it need not exist."""
    return Path(folder) / META_DIR


def config_dir(env: Optional[Mapping[str, str]] = None) -> Path:
    """The user's settings folder (~/.config/MyOS, or below XDG_CONFIG_HOME)."""
    env = os.environ if env is None else env
    return Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config") / CONFIG_DIR


def env_name(key: str) -> str:
    """The environment variable for key under the current name (ACL_MODE -> MYOS_ACL_MODE)."""
    return ENV_PREFIX + key


def getenv(key: str, default: Optional[str] = None, env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The environment variable for key (ACL_MODE: MYOS_ACL_MODE); under a former name when
    the current one is not set, else default. An empty value counts as set."""
    env = os.environ if env is None else env
    for prefix in (ENV_PREFIX, *LEGACY_ENV_PREFIXES):
        value = env.get(prefix + key)
        if value is not None:
            return value
    return default
