#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
myos_core.py - MyOS FUSE Filesystem Core

Implements a FUSE filesystem with project-centric features:
- Potential folder materialization (folders ending with %)
- Intelligent file access and directory listing
- Secure path handling and error management

Usage:
    python3 myos_core.py <mirror_dir> <mount_point>
    python3 myos_core.py ./mirror ./mount

Security Features:
- Path traversal protection
- Symlink resolution with realpath()
- Permission preservation
- Safe error handling
"""

import os
import sys
import errno
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from fuse import FUSE, Operations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('myos.core')

class MyOSCore(Operations):
    """
    MyOS FUSE Filesystem Implementation.
    
    Provides virtual filesystem operations with project-centric features:
    1. Potential folders (ending with %) that materialize on first access
    2. Virtual file entries for flattened project views
    3. Secure path handling and permission management
    """
    
    def __init__(self, root: str) -> None:
        """
        Initialize the MyOS filesystem.
        
        Args:
            root: Path to the mirror directory (physical files)
        """
        self.root = os.path.abspath(root)
        logger.info(f"MyOS: Mirror root is {self.root}")
        
        # Track materialized folders (those where % was removed)
        self.materialized: Dict[str, bool] = {}
        
        # Security: Store real root path after symlink resolution
        self.real_root = os.path.realpath(self.root)
        
        # Default potential folders (should be loaded from .myproject later)
        self.potential_folders = ['projekt%', 'finanzen%', 'team%', 'notizen%']
    
    def _safe_path(self, requested_path: str) -> str:
        """
        Convert virtual path to safe physical path with security checks.
        
        Args:
            requested_path: Virtual path from FUSE
        
        Returns:
            Safe physical path in mirror directory
        
        Raises:
            PermissionError: If path traversal outside mirror is detected
        """
        # Handle root path
        if requested_path == '/':
            return self.real_root
        
        # Remove leading slash and split
        parts = []
        for part in requested_path.strip('/').split('/'):
            # Materialize % folders
            if part.endswith('%'):
                part = part[:-1]
                self.materialized[part] = True
            
            # Skip empty parts but validate non-empty ones
            if part:
                # Security: Prevent path traversal components
                if part in ('..', '.'):
                    raise PermissionError(
                        f"Path traversal detected in: {requested_path}"
                    )
                parts.append(part)
        
        # Construct physical path
        physical_path = os.path.join(self.real_root, *parts) if parts else self.real_root
        
        # Security: Verify path is within mirror directory
        real_physical = os.path.realpath(physical_path)
        if not real_physical.startswith(self.real_root):
            raise PermissionError(
                f"Path escapes mirror directory: {requested_path} -> {real_physical}"
            )
        
        return real_physical
    
    def _materialize_path(self, path: str) -> str:
        """
        Materialize a path by converting % folders to real folders.
        
        Note: This is a convenience method that calls _safe_path but
        is kept for backward compatibility.
        
        Args:
            path: Virtual path with potential % folders
        
        Returns:
            Materialized physical path
        """
        return self._safe_path(path)
    
    def _is_potential_folder(self, path: str) -> bool:
        """
        Check if a path refers to a potential (not yet materialized) folder.
        
        Args:
            path: Virtual path to check
        
        Returns:
            True if path is a potential folder, False otherwise
        """
        if not path.endswith('%'):
            return False
        
        clean_name = path.rstrip('/').rstrip('%')
        return f"{clean_name}%" in self.potential_folders
    
    def _find_flat_entries(self) -> List[str]:
        """
        Find files for flattened directory view.
        
        Creates virtual entries for files in subdirectories using
        the %..% syntax for unique files in direct subdirectories.
        
        Returns:
            List of virtual file names for flattened view
        """
        flat_entries = []
        name_count: Dict[str, int] = {}  # For uniqueness checking
        
        try:
            for item in os.listdir(self.real_root):
                item_path = os.path.join(self.real_root, item)
                if os.path.isdir(item_path):
                    for root_dir, dirs, files in os.walk(item_path):
                        for file in files:
                            rel_path = os.path.relpath(
                                os.path.join(root_dir, file), 
                                self.real_root
                            )
                            
                            # Only files in subdirectories (not in root)
                            if '/' in rel_path:
                                parts = rel_path.split('/')
                                base_name = parts[0]
                                filename = parts[-1]
                                
                                # Create flat name: folder%..%file
                                flat_name = f"{base_name}%..%{filename}"
                                
                                # Check uniqueness
                                name_count[flat_name] = name_count.get(flat_name, 0) + 1
                                
                                # For non-unique names, use full path
                                if name_count[flat_name] > 1:
                                    flat_name = rel_path.replace('/', '%..%')
                                
                                flat_entries.append(flat_name)
                                logger.debug(f"Flat entry: {flat_name} -> {rel_path}")
        
        except PermissionError as e:
            logger.warning(f"Permission error scanning for flat entries: {e}")
        except OSError as e:
            logger.error(f"OS error scanning for flat entries: {e}")
        
        return flat_entries
    
    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, Any]:
        """
        Get file attributes (stat information).
        
        Implements FUSE getattr operation for:
        - Normal files and directories
        - Potential folders (% suffix)
        - Virtual flat files (%..% syntax)
        
        Args:
            path: Virtual path
            fh: Optional file handle (unused in this implementation)
        
        Returns:
            Dictionary with stat attributes
        
        Raises:
            FileNotFoundError: If path doesn't exist
        """
        try:
            logger.debug(f"getattr: {path}")
            
            # Handle virtual flat files (%..% syntax)
            if '%..%' in path:
                logger.debug(f"Processing flat file: {path}")
                
                # Extract folder and filename from flat syntax
                flat_path = path.lstrip('/')
                parts = flat_path.split('%..%')
                
                if len(parts) >= 2:
                    search_root_name = parts[0]
                    filename = parts[-1]
                    
                    # Security: Validate folder name
                    if not search_root_name or '..' in search_root_name:
                        raise FileNotFoundError(
                            errno.ENOENT, 
                            f"Invalid flat path: {path}"
                        )
                    
                    search_root = os.path.join(self.real_root, search_root_name)
                    
                    if os.path.exists(search_root):
                        # Recursively search for the file
                        for root_dir, dirs, files in os.walk(search_root):
                            if filename in files:
                                real_path = os.path.join(root_dir, filename)
                                logger.debug(f"Found flat file: {real_path}")
                                
                                st = os.stat(real_path)
                                return {
                                    'st_mode': st.st_mode,
                                    'st_ino': st.st_ino,
                                    'st_dev': st.st_dev,
                                    'st_nlink': st.st_nlink,
                                    'st_uid': st.st_uid,
                                    'st_gid': st.st_gid,
                                    'st_size': st.st_size,
                                    'st_atime': st.st_atime,
                                    'st_mtime': st.st_mtime,
                                    'st_ctime': st.st_ctime
                                }
                
                raise FileNotFoundError(
                    errno.ENOENT, 
                    f"Flat file not found: {path}"
                )
            
            # Handle potential folders
            if self._is_potential_folder(path):
                clean_name = path.rstrip('/').rstrip('%')
                real_check_path = os.path.join(self.real_root, clean_name)
                
                # If not yet materialized, return virtual directory attributes
                if not os.path.exists(real_check_path):
                    return {
                        'st_mode': 0o40755,  # drwxr-xr-x
                        'st_ino': 0,
                        'st_dev': 0,
                        'st_nlink': 2,
                        'st_uid': os.getuid(),
                        'st_gid': os.getgid(),
                        'st_size': 4096,
                        'st_atime': time.time(),
                        'st_mtime': time.time(),
                        'st_ctime': time.time()
                    }
            
            # Handle normal files and directories
            real_path = self._safe_path(path)
            
            if not os.path.exists(real_path):
                raise FileNotFoundError(errno.ENOENT, f"Path not found: {path}")
            
            st = os.stat(real_path)
            
            return {
                'st_mode': st.st_mode,
                'st_ino': st.st_ino,
                'st_dev': st.st_dev,
                'st_nlink': st.st_nlink,
                'st_uid': st.st_uid,
                'st_gid': st.st_gid,
                'st_size': st.st_size,
                'st_atime': st.st_atime,
                'st_mtime': st.st_mtime,
                'st_ctime': st.st_ctime
            }
            
        except PermissionError as e:
            raise PermissionError(errno.EACCES, str(e))
        except FileNotFoundError:
            raise  # Re-raise unchanged
        except Exception as e:
            logger.error(f"getattr error for {path}: {e}")
            raise FileNotFoundError(errno.ENOENT, f"Internal error: {e}")
    
    def readdir(self, path: str, fh: Optional[int] = None) -> List[str]:
        """
        Read directory contents.
        
        Implements FUSE readdir operation with virtual entries for:
        - Potential folders (% suffix)
        - Flat file entries (%..% syntax)
        
        Args:
            path: Directory path
            fh: Optional file handle (unused)
        
        Returns:
            List of directory entries
        """
        items = ['.', '..']
        
        try:
            logger.debug(f"readdir: {path}")
            
            # Get safe physical path
            real_dir = self._safe_path(path)
            
            # Add existing files and directories
            if os.path.exists(real_dir):
                try:
                    for item in os.listdir(real_dir):
                        items.append(item)
                except PermissionError:
                    logger.warning(f"No permission to list: {real_dir}")
            
            # In root directory, add virtual entries
            if path == '/':
                # Add potential folders (if not materialized)
                for folder in self.potential_folders:
                    base_name = folder[:-1]
                    real_folder_path = os.path.join(self.real_root, base_name)
                    
                    if not os.path.exists(real_folder_path):
                        items.append(folder)
                
                # Add flat file entries
                logger.info("Scanning for flat files...")
                flat_entries = self._find_flat_entries()
                for flat_name in flat_entries:
                    if flat_name not in items:  # Avoid duplicates
                        items.append(flat_name)
                
                logger.info(f"Total items in root: {len(items)}")
            
            return items
            
        except PermissionError as e:
            logger.error(f"Permission error in readdir: {e}")
            return ['.', '..']
        except Exception as e:
            logger.error(f"Error in readdir for {path}: {e}")
            return ['.', '..']
    
    def create(self, path: str, mode: int, fi: Optional[Any] = None) -> int:
        """
        Create and open a file.
        
        Materializes % folders in the path automatically.
        
        Args:
            path: File path (may contain % folders)
            mode: File mode (permissions)
            fi: Optional fuse_file_info structure
        
        Returns:
            File descriptor
        """
        try:
            logger.info(f"create: {path}")
            
            real_path = self._safe_path(path)
            logger.debug(f"  -> real path: {real_path}")
            
            # Ensure parent directory exists
            parent_dir = os.path.dirname(real_path)
            if not os.path.exists(parent_dir):
                logger.debug(f"  -> creating parent: {parent_dir}")
                os.makedirs(parent_dir, mode=0o755, exist_ok=True)
            
            logger.debug(f"  -> creating file: {real_path}")
            return os.open(real_path, os.O_CREAT | os.O_WRONLY, mode)
            
        except PermissionError as e:
            logger.error(f"Permission error creating {path}: {e}")
            raise PermissionError(errno.EACCES, str(e))
        except Exception as e:
            logger.error(f"Error creating {path}: {e}")
            raise OSError(errno.EIO, f"Create failed: {e}")
    
    def open(self, path: str, flags: int) -> int:
        """
        Open a file.
        
        Handles both normal files and virtual flat files (%..% syntax).
        
        Args:
            path: File path
            flags: Open flags
        
        Returns:
            File descriptor
        
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        try:
            # Handle virtual flat files
            if '%..%' in path:
                logger.info(f"open flat file: {path}")
                
                flat_path = path.lstrip('/')
                parts = flat_path.split('%..%')
                
                if len(parts) >= 2:
                    search_root_name = parts[0]
                    filename = parts[-1]
                    
                    # Security: Validate folder name
                    if not search_root_name or '..' in search_root_name:
                        raise FileNotFoundError(
                            errno.ENOENT, 
                            f"Invalid flat path: {path}"
                        )
                    
                    search_root = os.path.join(self.real_root, search_root_name)
                    
                    if os.path.exists(search_root):
                        # Search recursively
                        for root_dir, dirs, files in os.walk(search_root):
                            if filename in files:
                                real_path = os.path.join(root_dir, filename)
                                logger.debug(f"  Opening: {real_path}")
                                return os.open(real_path, flags)
                
                raise FileNotFoundError(
                    errno.ENOENT, 
                    f"Flat file not found: {path}"
                )
            
            # Handle normal files
            real_path = self._safe_path(path)
            return os.open(real_path, flags)
            
        except FileNotFoundError:
            raise  # Re-raise unchanged
        except PermissionError as e:
            logger.error(f"Permission error opening {path}: {e}")
            raise PermissionError(errno.EACCES, str(e))
        except Exception as e:
            logger.error(f"Error opening {path}: {e}")
            raise OSError(errno.EIO, f"Open failed: {e}")
    
    def mkdir(self, path: str, mode: int) -> int:
        """
        Create a directory.
        
        Materializes % folders automatically.
        
        Args:
            path: Directory path
            mode: Directory mode (permissions)
        
        Returns:
            0 on success
        """
        try:
            real_path = self._safe_path(path)
            os.makedirs(real_path, mode=mode, exist_ok=True)
            return 0
        except PermissionError as e:
            logger.error(f"Permission error creating directory {path}: {e}")
            raise PermissionError(errno.EACCES, str(e))
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
            raise OSError(errno.EIO, f"Mkdir failed: {e}")
    
    def read(self, path: str, size: int, offset: int, fh: int) -> bytes:
        """
        Read data from a file.
        
        Args:
            path: File path (unused, file handle determines file)
            size: Number of bytes to read
            offset: Offset to read from
            fh: File handle from open()
        
        Returns:
            Bytes read
        """
        try:
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, size)
        except Exception as e:
            logger.error(f"Error reading file (handle {fh}): {e}")
            raise OSError(errno.EIO, f"Read failed: {e}")
    
    def write(self, path: str, data: bytes, offset: int, fh: int) -> int:
        """
        Write data to a file.
        
        Args:
            path: File path (unused)
            data: Data to write
            offset: Offset to write at
            fh: File handle from open()
        
        Returns:
            Number of bytes written
        """
        try:
            os.lseek(fh, offset, os.SEEK_SET)
            return os.write(fh, data)
        except Exception as e:
            logger.error(f"Error writing file (handle {fh}): {e}")
            raise OSError(errno.EIO, f"Write failed: {e}")
    
    def release(self, path: str, fh: int) -> int:
        """
        Close a file.
        
        Args:
            path: File path (unused)
            fh: File handle to close
        
        Returns:
            0 on success
        """
        try:
            os.close(fh)
            return 0
        except Exception as e:
            logger.error(f"Error closing file (handle {fh}): {e}")
            # Don't raise - closing should not fail the operation
            return 0
    
    # Optional but recommended methods for completeness
    
    def unlink(self, path: str) -> int:
        """Remove a file."""
        try:
            real_path = self._safe_path(path)
            os.unlink(real_path)
            return 0
        except Exception as e:
            logger.error(f"Error removing file {path}: {e}")
            raise
    
    def rmdir(self, path: str) -> int:
        """Remove a directory."""
        try:
            real_path = self._safe_path(path)
            os.rmdir(real_path)
            return 0
        except Exception as e:
            logger.error(f"Error removing directory {path}: {e}")
            raise
    
    def rename(self, old: str, new: str) -> int:
        """Rename a file or directory."""
        try:
            old_path = self._safe_path(old)
            new_path = self._safe_path(new)
            os.rename(old_path, new_path)
            return 0
        except Exception as e:
            logger.error(f"Error renaming {old} to {new}: {e}")
            raise

def main() -> None:
    """
    Main entry point for MyOS FUSE filesystem.
    
    Usage: python3 myos_core.py <mirror_dir> <mount_point>
    """
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <mirror_dir> <mount_point>")
        print(f"Example: {sys.argv[0]} ./mirror ./mount")
        sys.exit(1)
    
    mirror_dir = sys.argv[1]
    mount_point = sys.argv[2]
    
    # Create directories if they don't exist
    try:
        os.makedirs(mirror_dir, exist_ok=True)
        os.makedirs(mount_point, exist_ok=True)
    except PermissionError as e:
        print(f"Error: Cannot create directories: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("MyOS Core - Project-Centric FUSE Filesystem")
    print("=" * 60)
    print(f"Mirror directory: {os.path.abspath(mirror_dir)}")
    print(f"Mount point: {os.path.abspath(mount_point)}")
    print()
    print("Features:")
    print("  - Potential folders (projekt%, finanzen%, etc.)")
    print("  - Automatic materialization on access")
    print("  - Virtual flat file entries")
    print("  - Secure path handling")
    print()
    print("Test commands:")
    print("  ls mount/                         # Shows potential folders")
    print("  touch mount/projekt%/test.txt     # Materializes projekt/")
    print("  myls mount/ --roentgen            # Intelligent view")
    print("=" * 60)
    print()
    
    try:
        # Mount the filesystem
        FUSE(
            MyOSCore(mirror_dir), 
            mount_point, 
            foreground=True, 
            nothreads=True,
            ro=False  # Read/write mode
        )
    except KeyboardInterrupt:
        print("\nMyOS stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError mounting filesystem: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
