#!/usr/bin/env python3
"""
materializer.py - % folder materialization logic for MyOS
Handles conversion of virtual paths (with %) to physical paths.
"""

import os
from pathlib import Path
from typing import Dict, List


class Materializer:
    """
    Materializes % folders in virtual paths to physical folders.
    
    Converts virtual paths with % to physical paths and creates directories as needed.
    
    Examples:
        /projects/finance%/budget.xls → /physical/root/projects/finance/budget.xls
        The 'finance%' folder is automatically created as 'finance/'.
    """
    
    def __init__(self, plate_root: Path, projects_dir_name: str = "projects"):
        """
        Initialize materializer with plate root and projects directory name.
        
        Args:
            plate_root: Physical root directory where files are stored (plate root)
            projects_dir_name: Name of the projects directory inside plate root
        """
        self.root = Path(plate_root).expanduser().absolute()
        self.projects_dir_name = projects_dir_name
        self.materialized: Dict[str, bool] = {}  # Cache of materialized folders
        
        # Ensure root exists
        self.root.mkdir(parents=True, exist_ok=True)
        print(f"MyOS Materializer: Root is {self.root}, projects dir: {self.projects_dir_name}")
            
    def resolve(self, virtual_path: str) -> Path:
        """
        Convert virtual path to physical path without creating directories.
        
        This method only converts the path format but doesn't create any directories.
        Use for read-only operations.
        
        Args:
            virtual_path: Virtual path from FUSE (e.g., '/projects/finance%/file.txt')
        
        Returns:
            Physical Path object where file would be stored
        """
        # Handle root directory
        if virtual_path == '/':
            return self.root
        
        # Split path into components
        parts = virtual_path.strip('/').split('/')
        
        # Process each component, removing % suffix if present
        processed_parts = []
        for part in parts:
            if part.endswith('%'):
                processed_parts.append(part[:-1])  # Remove % suffix
            else:
                processed_parts.append(part)
        
        # Build and return physical path
        return self.root.joinpath(*processed_parts)
    
    def materialize(self, virtual_path: str) -> Path:
        """
        Convert virtual path to physical path, creating directories as needed.
        
        This method creates directories for any % folders in the path.
        Use for write operations.
        
        Args:
            virtual_path: Virtual path from FUSE (e.g., '/projects/finance%/file.txt')
        
        Returns:
            Physical Path object where file should be stored
        """
        # Handle root directory
        if virtual_path == '/':
            return self.root
        
        # Split path into components
        parts = virtual_path.strip('/').split('/')
        
        # Process each component
        processed_parts = []
        for part in parts:
            if part.endswith('%'):
                # Remove % and create directory if needed
                folder_name = part[:-1]
                self._create_folder_if_needed(processed_parts, folder_name)
                processed_parts.append(folder_name)
            else:
                processed_parts.append(part)
        
        # Build and return physical path
        return self.root.joinpath(*processed_parts)
    
    def _create_folder_if_needed(self, parent_parts: List[str], folder: str) -> None:
        """
        Create physical folder if it doesn't exist yet.
        
        Args:
            parent_parts: List of parent directory names already processed
            folder: Folder name to create (without % suffix)
        """
        # Build parent path
        if parent_parts:
            parent_path = self.root.joinpath(*parent_parts)
        else:
            parent_path = self.root
        
        # Create folder if it doesn't exist
        folder_path = parent_path / folder
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            self.materialized[str(folder_path)] = True
            print(f"MyOS Materializer: Created folder {folder_path.relative_to(self.root)}")
    
    def is_materialized(self, folder_path: Path) -> bool:
        """
        Check if a folder has been materialized by this instance.
        
        Args:
            folder_path: Path to check
        
        Returns:
            True if folder was materialized during this session
        """
        return str(folder_path.absolute()) in self.materialized
