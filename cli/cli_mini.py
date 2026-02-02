# cli/myos_cli.py
import sys
from pathlib import Path
from core.api import MyOSAPI

def main():
    api = MyOSAPI()
    
    if len(sys.argv) < 2:
        # Einfaches ls
        for entry in api.ls():
            name = entry.get("name_display", entry["name"])
            print(f"{'🥚' if entry['is_embryo'] else '📁'} {name}")
        return
    
    cmd = sys.argv[1]
    if cmd == "project":
        project = api.get_project()
        print(f"Project: {project.name if project else 'None'}")
    
    # Weitere Commands...

if __name__ == "__main__":
    main()
