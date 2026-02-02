# localBlueprintLayer.py - Blueprint class (FUSE-only embryos)

import os
import stat
import time
import errno
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from fuse import FUSE, FuseOSError, Operations
from core.project import ProjectConfig
from core.acl import ACLPolicy

import shutil
import getpass

class BirthClinic:
    """Handles the birth process from embryos to physical folders."""
    
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.templates_dir = blueprint.templates_dir
    
    def give_birth(self, embryo_path: str) -> Path:
        """
        Complete birth process for a SINGLE embryo path.
        Now embryo_path uses normal names (no % suffix).
        Example: embryo_path = "admin" or "kommunikation/extern"
        
        Returns: Path to the newborn physical folder
        """
        # 1. Find template source for this specific embryo
        template_source = self.find_template_source(embryo_path)
        
        # Security: validate template before copying
        self._validate_template_security(template_source)
        
        # 3. Convert embryo path to physical path
        target_path = self._embryo_to_physical_path(embryo_path)
        
        # 4. Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Security: copy template without symlinks
        self._copy_template_safely(template_source, target_path)
        
        print(f"BirthClinic: Embryo '{embryo_path}' → {target_path} (from {template_source})")
        return target_path
    
    def _validate_template_security(self, template_source: Path) -> None:
        """
        Validates template for security issues.
        Currently only checks for symlinks.
        """
        issues = []
        
        # Security: check for symlinks (forbidden in templates)
        try:
            for root, dirs, files in os.walk(template_source, followlinks=False):
                # Check directories
                for name in dirs:
                    path = Path(root) / name
                    if path.is_symlink():
                        issues.append(f"Symlink directory: {path.relative_to(template_source)}")
                
                # Check files
                for name in files:
                    path = Path(root) / name
                    if path.is_symlink():
                        issues.append(f"Symlink file: {path.relative_to(template_source)}")
        except Exception as e:
            issues.append(f"Error scanning template: {e}")
        
        if issues:
            error_msg = "Template security validation failed:\n" + "\n".join(f"  - {issue}" for issue in issues)
            raise ValueError(error_msg)
    
    def _copy_template_safely(self, source: Path, target: Path):
        """Copy template directory without symlinks."""
        if source.is_dir():
            # Security: symlinks=False prevents copying symlinks
            shutil.copytree(
                source, 
                target, 
                dirs_exist_ok=True,
                symlinks=False,  # Security: do not copy symlinks
                ignore_dangling_symlinks=True,  # Security: ignore dangling symlinks
                ignore=None
            )
            shutil.copystat(source, target)
        else:
            # Security: copy2 does not follow symlinks for files
            shutil.copy2(source, target)
    
    def find_template_source(self, embryo_path: str) -> Path:
        """Find the template source directory for an embryo path."""
        
        # 1. Empty path check
        if not embryo_path:
            raise ValueError("Empty embryo path")
        
        # Security: URL-decode first (attackers can send encoded paths)
        import urllib.parse
        try:
            # Security: allow only key path characters to be decoded explicitly
            decoded = embryo_path
            decoded = decoded.replace('%2f', '/').replace('%2F', '/')
            decoded = decoded.replace('%5c', '\\').replace('%5C', '\\')
            decoded = decoded.replace('%2e', '.').replace('%2E', '.')
            decoded = urllib.parse.unquote(decoded)  # Remaining decoding
        except:
            decoded = embryo_path
        
        # Normalize path separators (Unix/Windows)
        # Security: replace Windows backslashes with forward slashes
        normalized = decoded.replace('\\', '/')
        
        # Security: block ".." anywhere (embryo paths must stay relative)
        if ".." in normalized:
            raise ValueError(
                f"Path traversal blocked (CWE-22): {embryo_path} "
                f"(decoded: {decoded})"
            )
        
        # Security: block absolute paths (Unix, Windows, Network)
        # Unix: /path, Windows: C:\path oder C:/path, Network: //server/path
        if (
            normalized.startswith('/') or  # Unix absolute
            (len(normalized) > 2 and normalized[1] == ':' and normalized[2] == '/') or  # Windows C:/ 
            (len(normalized) > 1 and normalized[0] == '/' and normalized[1] == '/')  # Network //server
        ):
            raise ValueError(
                f"Absolute path not allowed: {embryo_path}"
            )
        
        # Security: block hidden paths (e.g., .ssh, .config)
        parts = normalized.split('/')
        for part in parts:
            if part and part.startswith('.'):
                raise ValueError(
                    f"Hidden paths not allowed in embryo context: {embryo_path}"
                )
        
        # Only now: template search
        parts = normalized.strip('/').split('/')
        
        for template_name in self.blueprint.template_names:
            # Security: validate template names
            if not template_name or '..' in template_name or '/' in template_name:
                print(f"WARNING: Skipping invalid template name: {template_name}")
                continue

            template_dir = self.templates_dir / template_name
            current = template_dir
            
            for part in parts:
                current = current / part
                if not current.exists():
                    break  # This template doesn't have this path
            else:
                # All parts found in this template!
                if current.exists():
                    return current
        
        raise ValueError(f"No template found for embryo path: {embryo_path}")
    
    def _embryo_to_physical_path(self, embryo_path: str) -> Path:
        """Convert embryo path to physical path."""
        parts = embryo_path.strip('/').split('/')
        
        # Start from project root
        current = self.blueprint.project_root
        for part in parts:
            current = current / part
        
        return current
    
    def _copy_template(self, source: Path, target: Path):
        """Copy template directory with ALL contents."""
        if source.is_dir():
            shutil.copytree(
                source, 
                target, 
                dirs_exist_ok=True,
                symlinks=True,
                ignore=None
            )
            shutil.copystat(source, target)
        else:
            shutil.copy2(source, target)


class Blueprint(Operations):
    DEFAULT_TEMPLATES_DIR = Path("~/.myos/templates").expanduser()

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            project_root = Path.cwd()
        
        self.project_root = self._find_project_root(Path(project_root).resolve())
        self.config = ProjectConfig(self.project_root)
        
        if not self.config.is_valid():
            raise ValueError(f"Not a valid MyOS project: {self.project_root}")
        
        self.templates_dir = Path(
            os.environ.get("MYOS_TEMPLATES_DIR", 
                          self.project_root / "Templates")
        )
        
        self.birth_clinic = BirthClinic(self)
        
        self.template_names = self.config.templates if self.config.templates else []
        self.embryo_tree = self._load_embryo_tree()
        self.mount_time = time.time()
        
        # Cache for embryo status (path -> True/False)
        self._embryo_cache: Dict[str, bool] = {}

        # ACL policy and role resolution
        self.acl_policy = ACLPolicy.from_project(self.project_root)
        self.acl_enabled = (self.project_root / ".MyOS" / "ACLs.md").exists()
        self.acl_roles = self._resolve_acl_roles()
        
        print(f"Blueprint: Mounted on {self.project_root}")
        print(f"Blueprint: Using templates from {self.templates_dir}")
        print(f"Blueprint: Active templates: {self.template_names}")

    def _find_project_root(self, start_path: Path) -> Path:
        """Find the nearest project root by searching for .MyOS/Project.md upwards."""
        current = start_path
        while current != current.parent:
            if (current / ".MyOS" / "Project.md").exists():
                return current
            current = current.parent
        raise ValueError(f"No project root found from {start_path}")

    def _resolve_acl_roles(self) -> Set[str]:
        """
        Resolve roles for the current user.
        Priority:
        1) MYOS_ROLES env var (comma-separated)
        2) Users section in ACLs.md
        If Users section exists but user is not listed, returns empty set.
        If no Users section exists, returns empty set (no enforcement).
        """
        env_roles = os.environ.get("MYOS_ROLES")
        if env_roles:
            return {r.strip().lower() for r in env_roles.split(",") if r.strip()}

        if not self.acl_policy.users:
            return set()

        user = getpass.getuser()
        return self.acl_policy.roles_for_user(user)

    def _can_write_embryo(self, rel_path: str) -> bool:
        """
        Return True if the current roles allow write access to this embryo path.
        If no roles are resolved, do not enforce ACLs.
        """
        if not self.acl_enabled:
            return True
        if not self.acl_roles:
            return False
        path = f"/{rel_path.strip('/')}"
        return any(self.acl_policy.can_access(role, path, "write") for role in self.acl_roles)

    def _load_embryo_tree(self) -> Dict[str, Any]:
        """Load recursive embryo tree from ALL configured templates."""
        combined_tree = {}
        
        for template_name in self.template_names:
            template_dir = self.templates_dir / template_name
            if not template_dir.exists():
                print(f"[Blueprint] Warning: Template directory {template_dir} not found")
                continue
            
            template_tree = self._load_template_tree(template_dir)
            self._merge_trees(combined_tree, template_tree)
        
        return combined_tree

    def _load_template_tree(self, template_dir: Path) -> Dict[str, Any]:
        """Load recursive tree from a single template directory."""
        tree = {}
        for item in template_dir.iterdir():
            if item.is_dir():
                # Kein %-Suffix mehr - nur der reine Name
                name = item.name
                tree[name] = self._load_embryo_tree_sub(item)
        return tree

    def _load_embryo_tree_sub(self, dir_path: Path) -> Dict[str, Any]:
        sub_tree = {}
        for item in dir_path.iterdir():
            if item.is_dir():
                name = item.name
                sub_tree[name] = self._load_embryo_tree_sub(item)
        return sub_tree

    def _merge_trees(self, combined: Dict[str, Any], new: Dict[str, Any]) -> None:
        """Merge new tree into combined tree."""
        for key, value in new.items():
            if key in combined:
                self._merge_trees(combined[key], value)
            else:
                combined[key] = value

    def _physical_path(self, fuse_path: str) -> Path:
        rel = fuse_path.lstrip('/')
        return self.project_root / rel if rel else self.project_root

    def is_embryo(self, path: str) -> bool:
        """
        Check if a path is an embryo.
        """
        if not path:
            return False
        
        # Check physical existence first (takes precedence)
        physical = self._physical_path(path)
        exists_physically = physical.exists()
        
        # If it exists physically, it is not an embryo
        if exists_physically:
            self._embryo_cache[path] = False
            return False
        
        # Check cache (only if not physically present)
        if path in self._embryo_cache:
            return self._embryo_cache[path]
        
        # Check if path exists in embryo tree
        parts = path.split('/')
        node = self.embryo_tree
        
        for part in parts:
            if part in node:
                node = node[part]
            else:
                # Not found -> not an embryo
                node = None
                break
        
        result = node is not None
        self._embryo_cache[path] = result
        
        return result

    def contains_embryos(self, path: str) -> bool:
        """Check if any part of a path is an embryo."""
        parts = path.strip('/').split('/') if path else []
        
        # Check every subpath
        current_path = ""
        for part in parts:
            if current_path:
                current_path = f"{current_path}/{part}"
            else:
                current_path = part
            
            if self.is_embryo(current_path):
                return True
        
        return False

    def get_embryos_at(self, rel_path: str) -> List[str]:
        """
        Get all embryo folders that should be displayed at the given relative path.
        Returns names without any special markers.
        """
        embryos = []
        
        if not rel_path:
            # Root level: embryos directly under project root
            node = self.embryo_tree
        else:
            # Navigate to the requested node
            node = self.embryo_tree
            parts = rel_path.split('/')
            for i, part in enumerate(parts):
                if part in node:
                    node = node[part]
                else:
                    # Not found -> no embryos here
                    return []
        
        # Include children that are embryos
        for name in node.keys():
            # Build the full path
            if rel_path:
                full_path = f"{rel_path}/{name}"
            else:
                full_path = name
            
            # Only when it is an embryo (not physically present)
            if self.is_embryo(full_path) and self._can_write_embryo(full_path):
                embryos.append(name)
        
        return embryos

    def _birth_path(self, fuse_path: str) -> Path:
        """
        Handle birth process for a path containing embryos.
        Now works with normal paths (no % markers).
        """
        parts = fuse_path.strip('/').split('/')
        
        # Find the LAST embryo in the path
        embryo_parts = []
        current_path = ""
        
        for part in parts:
            if current_path:
                test_path = f"{current_path}/{part}"
            else:
                test_path = part
            
            if self.is_embryo(test_path):
                embryo_parts.append(part)
                current_path = test_path
            else:
                # Stop once a non-embryo segment is reached
                break
        
        if not embryo_parts:
            raise ValueError(f"No embryo found in path: {fuse_path}")
        
        # Embryo path (only embryo segments)
        embryo_path = '/'.join(embryo_parts)

        # Enforce ACLs for birth
        if not self._can_write_embryo(embryo_path):
            raise FuseOSError(errno.EACCES)
        
        # Remaining path after the embryo
        remaining_parts = parts[len(embryo_parts):]
        
        # Trigger birth for the embryo
        newborn = self.birth_clinic.give_birth(embryo_path)
        
        # Create remaining path parts
        for part in remaining_parts:
            newborn = newborn / part
        
        return newborn

    def _has_write_permission_for_embryo(self, embryo_name: str) -> bool:
        """Placeholder for permission check."""
        return True

    # ------------------------------------------------------------
    # FUSE Operations (FUSE-only embryos)
    # ------------------------------------------------------------

    def getattr(self, path: str, fh=None) -> Dict[str, Any]:
        # Security: warn about symlinks in the project path
        physical = self._physical_path(path)
        if physical.exists() and physical.is_symlink():
            print(f"SECURITY NOTICE: Symlink detected at {path}")

        # 1. Check if this exact path is an embryo directory
        rel_path = path.lstrip('/')
        
        if self.is_embryo(rel_path):
            # Embryo directory; use template source for metadata
            try:
                template_source = self.birth_clinic.find_template_source(rel_path)
                st = os.lstat(template_source)
                return {
                    'st_mode': stat.S_IFDIR | 0o555,  # Read-only for embryos
                    'st_nlink': 2,
                    'st_size': 4096,
                    'st_ctime': self.mount_time,
                    'st_mtime': self.mount_time,
                    'st_atime': self.mount_time,
                    'st_uid': os.getuid(),
                    'st_gid': os.getgid(),
                }
            except (ValueError, OSError):
                # Template not found: fall back to default values
                pass
        
        # 2. Check physical paths
        physical = self._physical_path(path)
        if physical.exists():
            st = os.lstat(physical)
            return dict((key, getattr(st, key)) for key in 
                       ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 
                        'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        
        # 3. Check if parent directory has embryos with this name
        if rel_path:
            dir_path = '/'.join(rel_path.split('/')[:-1]) if '/' in rel_path else ""
            name = rel_path.split('/')[-1]
            
            embryos_in_parent = self.get_embryos_at(dir_path)
            if name in embryos_in_parent:
                # This is an embryo directory
                return dict(
                    st_mode=stat.S_IFDIR | 0o555,
                    st_nlink=2,
                    st_size=4096,
                    st_ctime=self.mount_time,
                    st_mtime=self.mount_time,
                    st_atime=self.mount_time,
                    st_uid=os.getuid(),
                    st_gid=os.getgid(),
                )
        
        raise FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh) -> List[str]:
        rel_path = path.lstrip('/')
        physical = self._physical_path(path)
        
        if not physical.exists() or not physical.is_dir():
            raise FuseOSError(errno.ENOTDIR)

        entries = ['.', '..']

        # Physical entries (take precedence)
        for item in os.listdir(physical):
            if not item.startswith('.'):
                entries.append(item)

        # Embryos at this level (only if not already physical)
        embryos_here = self.get_embryos_at(rel_path)
        for embryo in embryos_here:
            # Ensure it does not already exist physically
            if embryo not in entries and self._has_write_permission_for_embryo(embryo):
                entries.append(embryo)

        return entries

    def mkdir(self, path: str, mode) -> None:
        # Birth on mkdir if path contains embryos
        rel_path = path.lstrip('/')
        if self.is_embryo(rel_path) or self.contains_embryos(path):
            self._birth_path(path)
        
        physical = self._physical_path(path)
        physical.mkdir(mode=mode, parents=True, exist_ok=True)

    def create(self, path: str, mode, fi=None) -> int:
        # Birth on create if path contains embryos
        rel_path = path.lstrip('/')
        if self.is_embryo(rel_path) or self.contains_embryos(path):
            self._birth_path(path)
        
        physical = self._physical_path(path)
        return os.open(physical, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)

    def write(self, path: str, data: bytes, offset: int, fh: Any) -> int:
        return os.pwrite(fh, data, offset)

    def release(self, path: str, fh: Any) -> None:
        os.close(fh)

    # ------------------------------------------------------------
    # Mount Function
    # ------------------------------------------------------------

    @staticmethod
    def mount(project_path: str | Path = Path.cwd(), foreground: bool = True):
        fuse = Blueprint(project_path)
        FUSE(fuse, str(fuse.project_root), foreground=foreground, allow_other=False)




if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        Blueprint.mount(sys.argv[1])
    else:
        print("Usage: python localBlueprintLayer.py /path/to/project")
