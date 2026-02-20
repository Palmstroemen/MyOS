#!/usr/bin/env python3
"""
perspective_fuse.py - FUSE adapter for flipped perspective runtime.
"""

from __future__ import annotations

import errno
import logging
import os
import stat
import time
from pathlib import Path
from typing import Dict, Iterable, Optional

try:
    from fuse import FUSE, FuseOSError, Operations
except ImportError:  # pragma: no cover - only used in systems without fusepy
    FUSE = None  # type: ignore

    class FuseOSError(OSError):  # type: ignore
        pass

    class Operations:  # type: ignore
        pass

from core.perspective_resolver import (
    PerspectiveContext,
    ResolverErrorCode,
    list_virtual_dir,
    perspective_open,
    prepare_create,
    prepare_rename,
    resolve_virtual_dir_for_read,
    resolve_virtual_path,
)

logger = logging.getLogger(__name__)


def resolver_error_to_errno(error_code: Optional[ResolverErrorCode]) -> int:
    mapping = {
        "not_found": errno.ENOENT,
        "denied": errno.EACCES,
        "invalid_path": errno.EINVAL,
        "ambiguous": errno.EINVAL,
        "conflict": errno.EEXIST,
        "unsupported": errno.ENOTSUP,
        "io_error": errno.EIO,
    }
    if not error_code:
        return errno.EIO
    return mapping.get(error_code, errno.EIO)


class PerspectiveFuseAdapter(Operations):
    """
    Thin adapter: FUSE operations delegate perspective semantics to resolver.
    """

    def __init__(
        self,
        *,
        project_root: str,
        start_real_path: str,
        perspective_id: str = "flipped",
        role: Optional[str] = None,
    ) -> None:
        self.ctx: PerspectiveContext = perspective_open(
            perspective_id=perspective_id,
            project_root=project_root,
            start_real_path=start_real_path,
            role=role,
        )
        self.mount_time = time.time()
        self._fd_table: Dict[int, int] = {}
        self._next_handle: int = 1000

    def _fail(self, error_code: Optional[ResolverErrorCode]) -> None:
        logger.debug("perspective_fuse.fail cpd=? error_code=%s", error_code)
        raise FuseOSError(resolver_error_to_errno(error_code))

    def _log_op(self, op: str, *, cpd: Optional[str] = None, real: Optional[str] = None, error_code: Optional[str] = None) -> None:
        logger.debug(
            "perspective_fuse.%s cpd=%s real=%s error_code=%s",
            op,
            cpd,
            real,
            error_code,
        )

    def _cpd(self, path: str) -> str:
        p = str(path or "/").strip()
        if not p.startswith("/"):
            p = "/" + p
        return p

    def _split_parent_name(self, path: str) -> tuple[str, str]:
        raw = self._cpd(path).rstrip("/")
        if raw == "":
            raw = "/"
        parent = str(Path(raw).parent)
        name = Path(raw).name
        if not name:
            return "/", ""
        return parent, name

    def _real_path(self, cpd: str, *, required: bool = True) -> Optional[str]:
        resolved = resolve_virtual_path(ctx=self.ctx, cpd=cpd)
        if not resolved.ok:
            self._fail(resolved.error_code)
        if required and not resolved.real_path:
            self._fail("unsupported")
        return resolved.real_path

    def _looks_like_directory_path(self, cpd: str) -> bool:
        if cpd.endswith("/"):
            return True
        name = Path(cpd).name
        return "." not in name

    # FUSE API ---------------------------------------------------------------
    def access(self, path: str, mode: int) -> int:
        cpd = self._cpd(path)
        resolved = resolve_virtual_path(ctx=self.ctx, cpd=cpd)
        if not resolved.ok:
            self._log_op("access", cpd=cpd, real=resolved.real_path, error_code=resolved.error_code)
            self._fail(resolved.error_code)
        self._log_op("access", cpd=cpd, real=resolved.real_path, error_code=None)
        return 0

    def getattr(self, path: str, fh=None):
        cpd = self._cpd(path)
        resolved = resolve_virtual_path(ctx=self.ctx, cpd=cpd)
        if not resolved.ok:
            # Apply parent fallback only for directory-like getattr requests.
            if self._looks_like_directory_path(cpd):
                dir_read = resolve_virtual_dir_for_read(ctx=self.ctx, cpd=cpd)
                if dir_read.ok and dir_read.node_type == "dir":
                    fallback_real = dir_read.effective_read_path
                    if fallback_real:
                        st = os.lstat(fallback_real)
                        self._log_op(
                            "getattr",
                            cpd=cpd,
                            real=fallback_real,
                            error_code=("fallback" if dir_read.fallback_applied else None),
                        )
                        return {
                            "st_mode": st.st_mode,
                            "st_nlink": st.st_nlink,
                            "st_size": st.st_size,
                            "st_ctime": st.st_ctime,
                            "st_mtime": st.st_mtime,
                            "st_atime": st.st_atime,
                            "st_uid": st.st_uid,
                            "st_gid": st.st_gid,
                        }
            self._log_op("getattr", cpd=cpd, real=resolved.real_path, error_code=resolved.error_code)
            self._fail(resolved.error_code)

        # Virtual anchor behaves like readonly directory.
        if resolved.node_type == "virtual_anchor":
            self._log_op("getattr", cpd=cpd, real=None, error_code=None)
            now = int(time.time())
            return {
                "st_mode": stat.S_IFDIR | 0o755,
                "st_nlink": 2,
                "st_size": 0,
                "st_ctime": now,
                "st_mtime": now,
                "st_atime": now,
            }

        assert resolved.real_path is not None
        self._log_op("getattr", cpd=cpd, real=resolved.real_path, error_code=None)
        st = os.lstat(resolved.real_path)
        return {
            "st_mode": st.st_mode,
            "st_nlink": st.st_nlink,
            "st_size": st.st_size,
            "st_ctime": st.st_ctime,
            "st_mtime": st.st_mtime,
            "st_atime": st.st_atime,
            "st_uid": st.st_uid,
            "st_gid": st.st_gid,
        }

    def readdir(self, path: str, fh) -> Iterable[str]:
        cpd = self._cpd(path)
        dir_read = resolve_virtual_dir_for_read(ctx=self.ctx, cpd=cpd)
        if not dir_read.ok:
            self._log_op("readdir", cpd=cpd, real=dir_read.real_path, error_code=dir_read.error_code)
            self._fail(dir_read.error_code)
        entries = [".", ".."]
        for item in list_virtual_dir(ctx=self.ctx, cpd=cpd):
            name = str(item.get("name") or "")
            if name:
                entries.append(name)
        self._log_op(
            "readdir",
            cpd=cpd,
            real=dir_read.effective_read_path,
            error_code=("fallback" if dir_read.fallback_applied else None),
        )
        return entries

    def open(self, path: str, flags: int) -> int:
        cpd = self._cpd(path)
        real_path = self._real_path(cpd, required=True)
        assert real_path is not None
        try:
            fd = os.open(real_path, flags)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        handle = self._next_handle
        self._next_handle += 1
        self._fd_table[handle] = fd
        self._log_op("open", cpd=cpd, real=real_path, error_code=None)
        return handle

    def create(self, path: str, mode: int, fi=None) -> int:
        parent_cpd, name = self._split_parent_name(path)
        prepared = prepare_create(ctx=self.ctx, cpd_parent=parent_cpd, name=name, node_type="file")
        if not prepared.ok or not prepared.real_path:
            self._log_op("create", cpd=path, real=prepared.real_path, error_code=prepared.error_code)
            self._fail(prepared.error_code)
        target = prepared.real_path
        os.makedirs(str(Path(target).parent), exist_ok=True)
        try:
            fd = os.open(target, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, mode)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        handle = self._next_handle
        self._next_handle += 1
        self._fd_table[handle] = fd
        self._log_op("create", cpd=path, real=target, error_code=None)
        return handle

    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        fd = self._fd_table.get(fh)
        if fd is None:
            raise FuseOSError(errno.EBADF)
        os.lseek(fd, offset, os.SEEK_SET)
        self._log_op("read", cpd=self._cpd(path), real=None, error_code=None)
        return os.read(fd, size)

    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        fd = self._fd_table.get(fh)
        if fd is None:
            raise FuseOSError(errno.EBADF)
        os.lseek(fd, offset, os.SEEK_SET)
        self._log_op("write", cpd=self._cpd(path), real=None, error_code=None)
        return int(os.write(fd, data))

    def release(self, path: str, fh: int) -> int:
        fd = self._fd_table.pop(fh, None)
        if fd is None:
            return 0
        os.close(fd)
        self._log_op("release", cpd=self._cpd(path), real=None, error_code=None)
        return 0

    def flush(self, path: str, fh: int) -> int:
        fd = self._fd_table.get(fh)
        if fd is None:
            return 0
        os.fsync(fd)
        return 0

    def truncate(self, path: str, length: int, fh=None):
        if fh is not None and fh in self._fd_table:
            os.ftruncate(self._fd_table[fh], length)
            return 0
        real_path = self._real_path(self._cpd(path), required=True)
        assert real_path is not None
        with open(real_path, "r+b") as fp:
            fp.truncate(length)
        return 0

    def mkdir(self, path: str, mode: int) -> int:
        parent_cpd, name = self._split_parent_name(path)
        prepared = prepare_create(ctx=self.ctx, cpd_parent=parent_cpd, name=name, node_type="dir")
        if not prepared.ok or not prepared.real_path:
            self._log_op("mkdir", cpd=path, real=prepared.real_path, error_code=prepared.error_code)
            self._fail(prepared.error_code)
        try:
            os.makedirs(prepared.real_path, mode=mode, exist_ok=False)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        self._log_op("mkdir", cpd=path, real=prepared.real_path, error_code=None)
        return 0

    def rename(self, old: str, new: str) -> int:
        target_parent, target_name = self._split_parent_name(new)
        source_resolved, target_prepared = prepare_rename(
            ctx=self.ctx,
            source_cpd=self._cpd(old),
            target_parent_cpd=target_parent,
            target_name=target_name,
        )
        if not source_resolved.ok:
            self._log_op("rename", cpd=self._cpd(old), real=source_resolved.real_path, error_code=source_resolved.error_code)
            self._fail(source_resolved.error_code)
        if not target_prepared.ok or not source_resolved.real_path or not target_prepared.real_path:
            self._log_op("rename", cpd=self._cpd(new), real=target_prepared.real_path, error_code=target_prepared.error_code)
            self._fail(target_prepared.error_code)
        try:
            os.rename(source_resolved.real_path, target_prepared.real_path)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        self._log_op("rename", cpd=f"{self._cpd(old)}->{self._cpd(new)}", real=target_prepared.real_path, error_code=None)
        return 0

    def unlink(self, path: str) -> int:
        resolved = resolve_virtual_path(ctx=self.ctx, cpd=self._cpd(path))
        if not resolved.ok:
            self._log_op("unlink", cpd=self._cpd(path), real=resolved.real_path, error_code=resolved.error_code)
            self._fail(resolved.error_code)
        if resolved.node_type == "virtual_anchor":
            self._log_op("unlink", cpd=self._cpd(path), real=None, error_code="unsupported")
            self._fail("unsupported")
        if not resolved.real_path:
            self._log_op("unlink", cpd=self._cpd(path), real=None, error_code="unsupported")
            self._fail("unsupported")
        try:
            os.unlink(resolved.real_path)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        self._log_op("unlink", cpd=self._cpd(path), real=resolved.real_path, error_code=None)
        return 0

    def rmdir(self, path: str) -> int:
        resolved = resolve_virtual_path(ctx=self.ctx, cpd=self._cpd(path))
        if not resolved.ok:
            self._log_op("rmdir", cpd=self._cpd(path), real=resolved.real_path, error_code=resolved.error_code)
            self._fail(resolved.error_code)
        if resolved.node_type == "virtual_anchor":
            self._log_op("rmdir", cpd=self._cpd(path), real=None, error_code="unsupported")
            self._fail("unsupported")
        if not resolved.real_path:
            self._log_op("rmdir", cpd=self._cpd(path), real=None, error_code="unsupported")
            self._fail("unsupported")
        try:
            os.rmdir(resolved.real_path)
        except OSError as exc:
            raise FuseOSError(exc.errno) from exc
        self._log_op("rmdir", cpd=self._cpd(path), real=resolved.real_path, error_code=None)
        return 0

    def statfs(self, path: str):
        root = Path(self.ctx.project_root)
        st = os.statvfs(root)
        return {
            "f_bsize": st.f_bsize,
            "f_frsize": st.f_frsize,
            "f_blocks": st.f_blocks,
            "f_bfree": st.f_bfree,
            "f_bavail": st.f_bavail,
            "f_files": st.f_files,
            "f_ffree": st.f_ffree,
            "f_favail": st.f_favail,
            "f_flag": st.f_flag,
            "f_namemax": st.f_namemax,
        }


def mount_perspective_fuse(
    *,
    project_root: str,
    start_real_path: str,
    mount_point: str,
    perspective_id: str = "flipped",
    role: Optional[str] = None,
    foreground: bool = True,
):
    if FUSE is None:
        raise RuntimeError("fusepy is not installed")
    adapter = PerspectiveFuseAdapter(
        project_root=project_root,
        start_real_path=start_real_path,
        perspective_id=perspective_id,
        role=role,
    )
    logger.info(
        "perspective_fuse.mount project_root=%s start_real=%s mount_point=%s perspective=%s",
        project_root,
        start_real_path,
        mount_point,
        perspective_id,
    )
    return FUSE(adapter, str(mount_point), foreground=foreground, allow_other=False)
