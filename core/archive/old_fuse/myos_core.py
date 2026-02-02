#!/usr/bin/env python3
import os
import sys
import errno
import time
from fuse import FUSE, Operations

class MyOSCore(Operations):
    def __init__(self, root):
        self.root = os.path.abspath(root)
        print(f"MyOS: Mirror root is {self.root}")
        
        # Hier lesen wir später aus .myproject
        self.potential_folders = ['projekt%', 'finanzen%', 'team%', 'notizen%']
        
        # Cache für materialisierte Pfade
        self.materialized = {}
    
    def _materialize_path(self, path):
        """Wandelt % in echte Pfade um"""
        if path == '/':
            return self.root
        
        parts = []
        for part in path.strip('/').split('/'):
            if part.endswith('%'):
                part = part[:-1]  # % entfernen
                # Markiere als materialisiert
                self.materialized[part] = True
            if part:
                parts.append(part)
        
        return os.path.join(self.root, *parts) if parts else self.root
    
    def _get_potential_name(self, path):
        """Extrahiert den Basisnamen ohne % für Checks"""
        name = os.path.basename(path.rstrip('/'))
        if name.endswith('%'):
            return name[:-1]
        return name
    
    # ===== FUSE Methoden =====
    
    def getattr(self, path, fh=None):
        try:
            # Prüfe ob es ein potentieller Ordner ist
            base_name = self._get_potential_name(path)
            
            # Wenn der Name in unserer Liste ist (mit %) und noch nicht existiert
            if f"{base_name}%" in self.potential_folders:
                real_check_path = os.path.join(self.root, base_name)
                if not os.path.exists(real_check_path):
                    # Potentieller Ordner - existiert virtuell
                    return {
                        'st_mode': 0o40755,
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
            
            # Normale Datei/Ordner
            if path == '/':
                real_path = self.root
            else:
                real_path = os.path.join(self.root, path.lstrip('/').replace('%/', '/'))
            
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
            
        except FileNotFoundError:
            raise FileNotFoundError(errno.ENOENT, f"Path not found: {path}")
    
    def readdir(self, path, fh=None):
        items = ['.', '..']
        
        try:
            # Pfad für reale Dateien
            if path == '/':
                real_dir = self.root
            else:
                real_dir = os.path.join(self.root, path.lstrip('/').replace('%/', '/'))
            
            # Existierende Dateien/Ordner
            if os.path.exists(real_dir):
                for item in os.listdir(real_dir):
                    items.append(item)
            
            # Im Root-Verzeichnis: Potentielle Ordner hinzufügen
            if path == '/':
                for folder in self.potential_folders:
                    base_name = folder[:-1]  # Ohne %
                    real_folder_path = os.path.join(self.root, base_name)
                    
                    # Nur zeigen, wenn noch nicht materialisiert
                    if not os.path.exists(real_folder_path):
                        items.append(folder)
            
            return items
            
        except Exception as e:
            print(f"readdir error: {e}")
            return ['.', '..']
    
    def mkdir(self, path, mode):
        """Erstellt Ordner - materialisiert %"""
        print(f"mkdir called: {path}")
        
        # Materialisiere den Pfad
        real_path = self._materialize_path(path)
        print(f"  -> real path: {real_path}")
        
        os.makedirs(real_path, mode=mode, exist_ok=True)
        return 0
    
    def create(self, path, mode, fi=None):
        """Erstellt Datei - materialisiert % im Pfad"""
        print(f"create called: {path}")
        
        # Materialisiere den Pfad
        real_path = self._materialize_path(path)
        print(f"  -> real path: {real_path}")
        
        # Stelle sicher, dass Elternverzeichnis existiert
        parent_dir = os.path.dirname(real_path)
        if not os.path.exists(parent_dir):
            print(f"  -> creating parent: {parent_dir}")
            os.makedirs(parent_dir, exist_ok=True)
        
        # Datei erstellen
        print(f"  -> creating file: {real_path}")
        return os.open(real_path, os.O_CREAT | os.O_WRONLY, mode)
    
    # Minimal notwendige Methoden
    def open(self, path, flags):
        real_path = self._materialize_path(path)
        return os.open(real_path, flags)
    
    def read(self, path, size, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, size)
    
    def write(self, path, data, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, data)
    
    def release(self, path, fh):
        return os.close(fh)
    
    def unlink(self, path):
        real_path = self._materialize_path(path)
        os.unlink(real_path)
        return 0
    
    def rmdir(self, path):
        real_path = self._materialize_path(path)
        os.rmdir(real_path)
        return 0

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <mirror_dir> <mount_point>")
        print(f"Example: {sys.argv[0]} ./mirror ./mount")
        sys.exit(1)
    
    mirror_dir = sys.argv[1]
    mount_point = sys.argv[2]
    
    os.makedirs(mirror_dir, exist_ok=True)
    os.makedirs(mount_point, exist_ok=True)
    
    print("=" * 50)
    print("MyOS Core - MIT %-MATERIALISIERUNG")
    print("=" * 50)
    print(f"Root: {os.path.abspath(mirror_dir)}")
    print(f"Mount: {os.path.abspath(mount_point)}")
    print("")
    print("Testsequenz in neuem Terminal:")
    print("1. ls mount/                         # Zeigt %-Ordner")
    print("2. touch mount/projekt%/test.txt     # Materialisiert")
    print("3. ls mount/                         # % weg, projekt/ da")
    print("4. ls mirror/                        # Realer Ordner")
    print("=" * 50)
    
    try:
        # OHNE allow_other - das brauchen wir nicht
        FUSE(MyOSCore(mirror_dir), mount_point, 
             foreground=True, 
             nothreads=True,
             ro=False)  # read/write mode
    except KeyboardInterrupt:
        print("\nMyOS stopped by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
