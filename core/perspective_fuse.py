#!/usr/bin/env python3
"""
perspective_fuse.py - the "Perspektiven" FUSE drive over the turned tree.

See "Designdocument Perspective Resolver MVP.md", A6. A thin adapter: what a path means
comes from core/perspective_drive.py; here it is only turned into file operations on the
real paths. Third-party programs (LibreOffice "Save as") write into
/04_Finanz/Projekte/Job and the file lands in Projekte/Job/04_Finanz.
"""

from __future__ import annotations

import errno
import logging
import os
import stat
import threading
import time
from pathlib import Path
from typing import Callable, Dict, Iterable, Optional

try:
    from fuse import FUSE, FuseOSError, Operations
except ImportError:  # pragma: no cover - only used in systems without fusepy
    FUSE = None  # type: ignore

    class FuseOSError(OSError):  # type: ignore
        def __init__(self, code: int) -> None:
            super().__init__(code, os.strerror(code))

    class Operations:  # type: ignore
        pass

from core.perspective_drive import DriveNode, PerspectiveDrive

logger = logging.getLogger(__name__)

_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_TRUNC


class PerspectiveDriveFuse(Operations):
    def __init__(self, drive: PerspectiveDrive) -> None:
        self.drive = drive
        self._fds: Dict[int, int] = {}
        self._next_handle = 1000
        self._lock = threading.Lock()
        self._mounted_at = time.time()

    # --- helpers ---------------------------------------------------------------------

    def _node(self, path: str) -> DriveNode:
        try:
            node = self.drive.node(path)
        except PermissionError:
            raise FuseOSError(errno.EACCES)
        if node is None:
            raise FuseOSError(errno.ENOENT)
        return node

    def _real(self, path: str, action: str) -> Path:
        """The real path behind path; the virtual levels cannot be changed."""
        node = self._node(path)
        if node.real is None:
            raise FuseOSError(errno.EACCES)
        if action == "write":
            # Security: where the lens enters a project (its department folder, or the
            # project folder standing in for it) is not removed, renamed or changed here.
            if node.project is not None and not node.rest:
                raise FuseOSError(errno.EACCES)
            if not self.drive.may(node.real, "write"):
                raise FuseOSError(errno.EACCES)
        return node.real

    def _target(self, path: str) -> Path:
        try:
            return self.drive.target_for_create(path)
        except PermissionError:
            raise FuseOSError(errno.EACCES)
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)

    def _keep(self, fd: int) -> int:
        with self._lock:
            handle = self._next_handle
            self._next_handle += 1
            self._fds[handle] = fd
        return handle

    def _fd(self, handle: int) -> int:
        fd = self._fds.get(handle)
        if fd is None:
            raise FuseOSError(errno.EBADF)
        return fd

    @staticmethod
    def _call(action: Callable[[], object]):
        try:
            return action()
        except OSError as exc:
            raise FuseOSError(exc.errno or errno.EIO)

    # --- reading ---------------------------------------------------------------------

    def getattr(self, path: str, fh=None):
        node = self._node(path)
        if node.real is None:  # a virtual level: a read-only folder
            return {"st_mode": stat.S_IFDIR | 0o555, "st_nlink": 2, "st_size": 0,
                    "st_ctime": self._mounted_at, "st_mtime": self._mounted_at, "st_atime": self._mounted_at,
                    "st_uid": os.getuid(), "st_gid": os.getgid()}
        info = self._call(lambda: os.lstat(node.real))
        return {key: getattr(info, key) for key in (
            "st_mode", "st_nlink", "st_size", "st_ctime", "st_mtime", "st_atime", "st_uid", "st_gid")}

    def readdir(self, path: str, fh) -> Iterable[str]:
        try:
            names = self.drive.listdir(path)
        except PermissionError:
            raise FuseOSError(errno.EACCES)
        except FileNotFoundError:
            raise FuseOSError(errno.ENOENT)
        return [".", "..", *names]

    def access(self, path: str, mode: int) -> int:
        node = self._node(path)
        if mode & os.W_OK and (node.real is None or not self.drive.may(node.real, "write")):
            raise FuseOSError(errno.EACCES)
        return 0

    def open(self, path: str, flags: int) -> int:
        real = self._real(path, "write" if flags & _WRITE_FLAGS else "read")
        return self._keep(self._call(lambda: os.open(real, flags)))

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        return self._call(lambda: os.pread(self._fd(fh), size, offset))

    def statfs(self, path: str):
        info = os.statvfs(self.drive.projects_root)
        return {key: getattr(info, key) for key in (
            "f_bavail", "f_bfree", "f_blocks", "f_bsize", "f_favail", "f_ffree", "f_files",
            "f_flag", "f_frsize", "f_namemax")}

    # --- writing ---------------------------------------------------------------------

    def create(self, path: str, mode: int, fi=None) -> int:
        # fusepy does not pass the caller's open flags here; the kernel keeps the caller's
        # access mode, so the handle is opened for reading too (LibreOffice reads its lock
        # file right after creating it).
        target = self._target(path)
        return self._keep(self._call(lambda: os.open(target, os.O_CREAT | os.O_RDWR | os.O_TRUNC, mode)))

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        return self._call(lambda: os.pwrite(self._fd(fh), data, offset))

    def truncate(self, path: str, length: int, fh=None) -> int:
        if fh is not None and fh in self._fds:
            self._call(lambda: os.ftruncate(self._fds[fh], length))
        else:
            real = self._real(path, "write")
            self._call(lambda: os.truncate(real, length))
        return 0

    def flush(self, path: str, fh: int) -> int:
        return 0

    def fsync(self, path: str, datasync: bool, fh: int) -> int:
        self._call(lambda: os.fsync(self._fd(fh)))
        return 0

    def release(self, path: str, fh: int) -> int:
        with self._lock:
            fd = self._fds.pop(fh, None)
        if fd is not None:
            os.close(fd)
        return 0

    def mkdir(self, path: str, mode: int) -> int:
        target = self._target(path)
        self._call(lambda: os.mkdir(target, mode))
        return 0

    def unlink(self, path: str) -> int:
        real = self._real(path, "write")
        self._call(lambda: os.unlink(real))
        return 0

    def rmdir(self, path: str) -> int:
        real = self._real(path, "write")
        self._call(lambda: os.rmdir(real))
        return 0

    def rename(self, old: str, new: str) -> int:
        source = self._real(old, "write")
        target = self._target(new)
        self._call(lambda: os.rename(source, target))
        return 0

    def chmod(self, path: str, mode: int) -> int:
        real = self._real(path, "write")
        self._call(lambda: os.chmod(real, mode))
        return 0

    def utimens(self, path: str, times=None) -> int:
        real = self._real(path, "write")
        self._call(lambda: os.utime(real, times))
        return 0


def mount_perspective_drive(
    *,
    projects_root: str,
    mount_point: str,
    may: Optional[Callable[[Path, str], bool]] = None,
    foreground: bool = True,
):
    """Mount the turned tree of projects_root at mount_point (blocks while foreground)."""
    if FUSE is None:
        raise RuntimeError("fusepy is not installed")
    logger.info("perspective_fuse.mount projects_root=%s mount_point=%s", projects_root, mount_point)
    fs = PerspectiveDriveFuse(PerspectiveDrive(projects_root, may=may))
    return FUSE(fs, str(mount_point), foreground=foreground, allow_other=False, nothreads=False)
