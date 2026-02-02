# fuse.py
"""
MyOS FUSE Layer - Virtual filesystem with .blueprint feature.
"""

import os
import errno
import stat
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from fuse import FUSE, FuseOSError, Operations
from .vlp import LensEngine, PlateManager


class MyOSFUSE(Operations):
    """
    FUSE filesystem for MyOS.
    Presents virtual view with .blueprint directories in projects.
    """
        
    def __init__(self, engine: LensEngine, *, projects_dir_name: str | None = None):
        """
        : projects_dir_name: Name of the physical 
        """
        self.engine = engine
        self.mount_time = time.time()
        self.projects_dir_name = projects_dir_name
        
        # Add materializer
        from .materializer import Materializer
        self.materializer = Materializer(engine.plate.root, projects_dir_name)        

    # --- Path resolution helpers ---
    
    def _parse_virtual_path(self, virtual_path: str) -> Dict[str, Any]:
        parts = [p for p in virtual_path.strip('/').split('/') if p]
        
        # --- Case 1: Root directory '/' ---
        if not parts:
            return {
                'is_root': True,
                'is_projects': False,
                'project_name': None,
                'relative_path': '',
                'is_blueprint': False,
                'blueprint_relative': None
            }
        
        # --- Case 2: Paths not starting with self.projects_dir_name ---
        if parts[0] != self.projects_dir_name:
            return {
                'is_root': False,
                'is_projects': False,
                'project_name': None,
                'relative_path': virtual_path.strip('/'),
                'is_blueprint': False,
                'blueprint_relative': None
            }
        
        # --- Case 3: Inside self.projects_dir_name ---
        
        # 3a: Just self.projects_dir_name itself
        if len(parts) == 1:
            return {
                'is_root': False,
                'is_projects': True,
                'project_name': None,
                'relative_path': '',
                'is_blueprint': False,
                'blueprint_relative': None
            }
        
        # 3b: Path contains '.blueprint' virtual directory
        if '.blueprint' in parts:
            blueprint_index = parts.index('.blueprint')
            
            # Project name is the part right after self.projects_dir_name
            project_name = parts[1] if len(parts) > 1 else None
            
            # Path after .blueprint (if any)
            blueprint_relative = '/'.join(parts[blueprint_index + 1:]) if blueprint_index + 1 < len(parts) else ''
            
            return {
                'is_root': False,
                'is_projects': True,
                'project_name': project_name,
                'relative_path': '',  # Original path is virtual
                'is_blueprint': True,
                'blueprint_relative': blueprint_relative
            }
        
        # 3c: Normal project path (no .blueprint)
        project_name = parts[1] if len(parts) > 1 else None
        relative_path = '/'.join(parts[2:]) if len(parts) > 2 else ''
        
        return {
            'is_root': False,
            'is_projects': True,
            'project_name': project_name,
            'relative_path': relative_path,
            'is_blueprint': False,
            'blueprint_relative': None
        }
    
    def _resolve_to_physical(self, virtual_path: str, materialize: bool = False) -> Optional[Path]:
        """
        Resolve FUSE path to physical path.
        """
        print(f"DEBUG _resolve_to_physical: virtual_path='{virtual_path}', materialize={materialize}")
        
        if materialize:
            return self.materializer.materialize(virtual_path)
        
        parsed = self._parse_virtual_path(virtual_path)
        print(f"DEBUG _resolve_to_physical: parsed={parsed}")
        
        # Root and projects directory have no physical path
        if parsed['is_root'] or (parsed['is_projects'] and not parsed['project_name']):
            print(f"DEBUG _resolve_to_physical: is_root or is_projects without project_name -> None")
            return None
        
        # .blueprint virtual paths have no physical path
        if parsed['is_blueprint']:
            print(f"DEBUG _resolve_to_physical: is_blueprint -> None")
            return None
        
        # For paths with %, we need to check if they exist physically (already materialized)
        if '%' in parsed['relative_path']:
            # Try to resolve without the % suffix
            # Convert virtual path with % to physical path using materializer's resolve
            physical_path = self.materializer.resolve(virtual_path)
            print(f"DEBUG _resolve_to_physical: path with % -> trying {physical_path}")
            
            # Check if the physical path exists
            if physical_path.exists():
                print(f"DEBUG _resolve_to_physical: materialized path exists, returning {physical_path}")
                return physical_path
            else:
                print(f"DEBUG _resolve_to_physical: materialized path doesn't exist -> None")
                return None
        
        # Normal project path: convert to physical
        if parsed['is_projects'] and parsed['project_name']:
            # Build path: plate_root/projects_dir_name/project_name/relative_path
            project_root = self.engine.plate.root / self.projects_dir_name / parsed['project_name']
            result = project_root / parsed['relative_path']
            print(f"DEBUG _resolve_to_physical: project path -> {result}")
            return result
        
        # Fallback (should not reach here)
        print(f"DEBUG _resolve_to_physical: fallback -> None")
        return None
   
    def _is_in_project(self, virtual_path: str) -> bool:
        """Check if path is inside a MyOS project"""
        parsed = self._parse_virtual_path(virtual_path)
        if not parsed['is_projects'] or not parsed['project_name']:
            return False
        
        # Check if project exists
        return self.engine.is_project(parsed['project_name'])
    
    def _get_project_root_path(self, virtual_path: str) -> Optional[Path]:
        """Get physical project root path"""
        parsed = self._parse_virtual_path(virtual_path)
        if not parsed['is_projects'] or not parsed['project_name']:
            return None
        
        # Build path: plate_root/projects_dir_name/project_name
        return self.engine.plate.root / self.projects_dir_name / parsed['project_name']
    
    # --- FUSE operations ---
    
    def getattr(self, path: str, fh: Optional[Any] = None) -> Dict[str, Any]:
        """Get file attributes"""
        print(f"DEBUG getattr called for path: '{path}'")
        
        now = time.time()
        mount_time = self.mount_time
        uid = os.getuid()
        gid = os.getgid()
        
        # === Handle special paths ===
        if path == '/':
            print(f"DEBUG getattr: root path")
            return {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 4096,
                'st_atime': now,
                'st_mtime': now,
                'st_ctime': mount_time,
                'st_uid': uid,
                'st_gid': gid,
            }
        
        if path == f'/{self.projects_dir_name}':
            print(f"DEBUG getattr: /{self.projects_dir_name}")
            return {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 4096,
                'st_atime': now,
                'st_mtime': now,
                'st_ctime': mount_time,
                'st_uid': uid,
                'st_gid': gid,
            }
        
        # Handle .blueprint virtual directory
        if path.endswith('/.blueprint') or path == '/.blueprint' or '.blueprint/' in path:
            print(f"DEBUG getattr: .blueprint path: {path}")
            return {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 4096,
                'st_atime': now,
                'st_mtime': now,
                'st_ctime': mount_time,
                'st_uid': uid,
                'st_gid': gid,
            }

        # Parse the path to understand its structure
        parsed = self._parse_virtual_path(path)
        
        # === Handle project directories (e.g., /projects/Haus) ===
        # A project directory is a path inside projects with no further relative path
        if parsed['is_projects'] and parsed['project_name'] and not parsed['relative_path']:
            print(f"DEBUG getattr: checking project directory: {parsed['project_name']}")
            
            # Check if project exists physically
            project_physical_path = self.engine.plate.root / self.projects_dir_name / parsed['project_name']
            print(f"DEBUG getattr: project_physical_path = {project_physical_path}")
            
            if project_physical_path.exists():
                # Project exists - return physical stats
                try:
                    st = os.lstat(project_physical_path)
                    print(f"DEBUG getattr: project exists, returning physical stats")
                    return {
                        'st_mode': st.st_mode,
                        'st_nlink': st.st_nlink,
                        'st_size': st.st_size,
                        'st_atime': st.st_atime,
                        'st_mtime': st.st_mtime,
                        'st_ctime': st.st_ctime,
                        'st_uid': st.st_uid,
                        'st_gid': st.st_gid,
                    }
                except OSError as e:
                    print(f"DEBUG getattr: error accessing project: {e}")
                    # Fall through to virtual directory
            else:
                print(f"DEBUG getattr: project doesn't exist physically")
            
            # If project doesn't exist or error: return virtual directory attributes
            # This allows ls to display project entries from readdir
            print(f"DEBUG getattr: returning virtual directory attributes for project")
            return {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 4096,
                'st_atime': now,
                'st_mtime': now,
                'st_ctime': mount_time,
                'st_uid': uid,
                'st_gid': gid,
            }

        # === Handle % embryo folders ===
        parts = path.strip('/').split('/')
        if parts and parts[-1].endswith('%'):
            # Extract folder name without %
            folder_name = parts[-1][:-1]
            print(f"DEBUG getattr: checking embryo folder: {folder_name} in {path}")
            
            # Get project context
            parsed = self._parse_virtual_path(path)
            print(f"DEBUG getattr: parsed = {parsed}")
            
            if parsed['is_projects'] and parsed['project_name']:
                # Check if this folder exists in blueprint
                blueprint_folders = self._get_blueprint_folders(parsed['project_name'])
                print(f"DEBUG getattr: blueprint_folders = {blueprint_folders}")
                
                if folder_name in blueprint_folders:
                    # Valid embryo folder - return virtual directory attributes
                    print(f"DEBUG getattr: valid embryo folder, returning virtual dir")
                    return {
                        'st_mode': stat.S_IFDIR | 0o755,
                        'st_nlink': 2,
                        'st_size': 4096,
                        'st_atime': now,
                        'st_mtime': now,
                        'st_ctime': mount_time,
                        'st_uid': uid,
                        'st_gid': gid,
                    }
        
        print(f"DEBUG getattr: trying to resolve physical path: {path}")
        # Resolve to physical path for normal files/directories
        physical_path = self._resolve_to_physical(path)
        print(f"DEBUG getattr: physical_path = {physical_path}")
        
        if not physical_path or not physical_path.exists():
            print(f"DEBUG getattr: physical path not found or doesn't exist")
            raise FuseOSError(errno.ENOENT)
        
        # Get stats from physical file
        try:
            st = os.lstat(physical_path)
            print(f"DEBUG getattr: returning stats for {physical_path}")
            return {
                'st_mode': st.st_mode,
                'st_nlink': st.st_nlink,
                'st_size': st.st_size,
                'st_atime': st.st_atime,
                'st_mtime': st.st_mtime,
                'st_ctime': st.st_ctime,
                'st_uid': st.st_uid,
                'st_gid': st.st_gid,
            }
        except OSError as e:
            print(f"DEBUG getattr: OSError: {e}")
            raise FuseOSError(e.errno)
    
    def _get_blueprint_folders(self, project_name: str) -> List[str]:
        """
        Get blueprint folders for a project based on its template.
        
        Reads .project.cfg to find template name, then scans template directory
        for folders to use as blueprint.
        
        Returns:
            List of folder names (without % suffix)
        """
        if not project_name:
            return []
        
        try:
            # Get project directory - use projects_dir_name
            project_path = self.engine.plate.root / self.projects_dir_name / project_name
            if not project_path.exists():
                return []
            
            # Read .project.cfg
            config_file = project_path / ".project.cfg"
            if not config_file.exists():
                return []
            
            # Find template name
            template_name = None
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('template:'):
                        template_name = line.split(':', 1)[1].strip()
                        break
            
            if not template_name:
                return []
            
            # Get template directory
            template_dir = self.engine.templates_dir / template_name
            if not template_dir.exists():
                return []
            
            # Scan for directories in template (non-hidden)
            folders = []
            for item in template_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item.name)
            
            return folders
            
        except Exception as e:
            print(f"MyOS Error getting blueprint folders for {project_name}: {e}")
            return []

    def readdir(self, path: str, fh: Optional[Any] = None) -> List[str]:
        """Read directory contents with virtual entries"""
        entries = ['.', '..']
        
        parsed = self._parse_virtual_path(path)
        
        # --- Root directory '/' ---
        if parsed['is_root']:
            entries.append(self.projects_dir_name)
            return entries
        
        # --- Inside self.projects_dir_name directory ---
        if path == f'/{self.projects_dir_name}':
            # List all projects in physical directory
            projects_dir = self.engine.plate.root / self.projects_dir_name
            if projects_dir.exists():
                for item in projects_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        entries.append(item.name)
            return entries
        
        # --- Inside .blueprint virtual directory ---
        if parsed.get('is_blueprint'):
            # Show template folders as blueprint
            folders = self._get_blueprint_folders(parsed['project_name'])
            entries.extend(folders)
            return entries
        
        # --- Normal directory listing ---
        physical_path = self._resolve_to_physical(path)
        
        if physical_path and physical_path.exists():
            # Add physical files (filter hidden)
            for item in os.listdir(physical_path):
                if not item.startswith('.'):
                    entries.append(item)
        
        # --- Add virtual entries for projects ---
        if parsed['is_projects'] and parsed['project_name']:
            # 1. .blueprint virtual directory
            entries.append('.blueprint')
            
            # 2. embryo folders (%)
            blueprint_folders = self._get_blueprint_folders(parsed['project_name'])
            for folder in blueprint_folders:
                embryo_name = f"{folder}%"
                
                # Check if already materialized
                materialized_path = self._resolve_to_physical(
                    f"/{self.projects_dir_name}/{parsed['project_name']}/{folder}"
                )
                
                if materialized_path and not materialized_path.exists():
                    entries.append(embryo_name)
                else:
                    # Show materialized folder without %
                    entries.append(folder)
        
        return entries
    
    def read(self, path: str, size: int, offset: int, fh: Any) -> bytes:
        """Read file content"""
        physical_path = self._resolve_to_physical(path)
        if not physical_path or not physical_path.exists():
            raise FuseOSError(errno.ENOENT)
        
        with open(physical_path, 'rb') as f:
            f.seek(offset)
            return f.read(size)
        
    def mkdir(self, path: str, mode: int):
        """Create directory - materialize % folders"""
        print(f"DEBUG mkdir: path={path}, mode={mode}")
        physical_path = self.materializer.materialize(path)
        print(f"DEBUG mkdir: physical_path={physical_path}")
        
        if not physical_path:
            raise FuseOSError(errno.EINVAL)
        
        os.mkdir(physical_path, mode)

    def create(self, path: str, mode: int, fi: Optional[Any] = None) -> int:
        """Create file - materialize % folders"""
        print(f"DEBUG create: path={path}, mode={mode}")
        # Convert virtual FUSE path to plate-relative path
        plate_path = path
        
        physical_path = self.materializer.materialize(plate_path)
        print(f"DEBUG create: physical_path={physical_path}")
        
        if not physical_path:
            raise FuseOSError(errno.EINVAL)
        
        # Ensure parent directory exists
        physical_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file
        fd = os.open(physical_path, os.O_WRONLY | os.O_CREAT, mode)
        print(f"DEBUG create: file created, fd={fd}")
        return fd
    
    def write(self, path: str, data: bytes, offset: int, fh: Any) -> int:
        """Write to file"""
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, data)
    
    def release(self, path: str, fh: Any):
        """Close file"""
        return os.close(fh)
    
    # --- Simple implementations for other required methods ---
    
    def access(self, path: str, mode: int):
        """Check access permissions"""
        physical_path = self._resolve_to_physical(path)
        if not physical_path or not physical_path.exists():
            raise FuseOSError(errno.ENOENT)
        
        if not os.access(physical_path, mode):
            raise FuseOSError(errno.EACCES)
    
    def statfs(self, path: str) -> Dict[str, Any]:
        """Get filesystem statistics"""
        return {
            'f_bsize': 4096,
            'f_frsize': 4096,
            'f_blocks': 1000000,
            'f_bfree': 500000,
            'f_bavail': 500000,
            'f_files': 100000,
            'f_ffree': 50000,
            'f_favail': 50000,
            'f_flag': 0,
            'f_namemax': 255,
        }

def mount_fuse(plate_root: Path = None, mount_point: Path = None, 
               templates_dir: Path = None, projects_dir: str = "projects",
               foreground: bool = True):
    """
    Convenience function to mount MyOS FUSE.
    
    Args:
        plate_root: Plate directory (default: ~/plates)
        mount_point: Where to mount (default: ~/projects)
        templates_dir: Templates directory (default: ~/.myos/lenses)
        projects_dir: Name of projects directory in plate (default: "projects")
        foreground: Run in foreground
    """
    if plate_root is None:
        plate_root = Path.home() / "plates"
    if mount_point is None:
        mount_point = Path.home() / "projects"  # Default Englisch
    if templates_dir is None:
        templates_dir = Path.home() / ".myos" / "lenses"
    
    # Create directories if needed
    plate_root.mkdir(parents=True, exist_ok=True)
    mount_point.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    plate = PlateManager(plate_root)
    engine = LensEngine(plate, templates_dir=templates_dir)
    fuse = MyOSFUSE(engine, projects_dir_name=projects_dir)
    
    print(f"Mounting MyOS FUSE:")
    print(f"  Plate:   {plate_root}")
    print(f"  Mount:   {mount_point} (showing as /{projects_dir})")
    print(f"  Templates: {templates_dir}")
    print("Press Ctrl+C to unmount")
    
    # Mount
    FUSE(fuse, str(mount_point), foreground=foreground, allow_other=False, ro=False)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Mount MyOS FUSE filesystem")
    parser.add_argument("--plate", default="~/plates", help="Plate directory")
    parser.add_argument("--mount", default="~/Projekte", help="Mount point")
    parser.add_argument("--templates", default="~/.myos/lenses", help="Templates directory")
    parser.add_argument("--projects-dir", default="projects", help="Projects directory name in plate")  # <-- NEU
    parser.add_argument("--background", action="store_true", help="Run in background")
    
    args = parser.parse_args()
    
    mount_fuse(
        plate_root=Path(args.plate).expanduser(),
        mount_point=Path(args.mount).expanduser(),
        templates_dir=Path(args.templates).expanduser(),
        projects_dir=args.projects_dir,  # <-- NEU
        foreground=not args.background
    )
