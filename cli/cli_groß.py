# cli/myos_cli.py

import argparse
from rich.console import Console
from rich.table import Table
from core.api import MyOSAPI

console = Console()

def main():
    parser = argparse.ArgumentParser(description="MyOS CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # ls
    ls_parser = subparsers.add_parser("ls", help="List directory")
    ls_parser.add_argument("path", nargs="?", default=".", help="Path to list")
    
    # cd
    cd_parser = subparsers.add_parser("cd", help="Change directory")
    cd_parser.add_argument("path", help="Path to change to")
    
    # embryo create
    embryo_parser = subparsers.add_parser("embryo", help="Embryo operations")
    embryo_sub = embryo_parser.add_subparsers(dest="embryo_cmd")
    
    create_parser = embryo_sub.add_parser("create", help="Create embryo")
    create_parser.add_argument("name", help="Embryo name")
    create_parser.add_argument("-t", "--template", help="Template name")
    
    birth_parser = embryo_sub.add_parser("birth", help="Birth embryo")
    birth_parser.add_argument("name", help="Embryo name")
    
    list_parser = embryo_sub.add_parser("list", help="List embryos")
    
    # project
    project_parser = subparsers.add_parser("project", help="Project operations")
    project_sub = project_parser.add_subparsers(dest="project_cmd")
    
    project_sub.add_parser("info", help="Show project info")
    
    create_proj_parser = project_sub.add_parser("create", help="Create project")
    create_proj_parser.add_argument("name", help="Project name")
    create_proj_parser.add_argument("-t", "--template", default="Standard")
    
    args = parser.parse_args()
    
    # API initialisieren
    api = MyOSAPI()
    
    # Commands ausführen
    if args.command == "ls":
        print_ls(api, args.path)
    elif args.command == "cd":
        api.cd(args.path)
        console.print(f"Changed to: {api.get_cwd()}")
    elif args.command == "embryo":
        handle_embryo(api, args)
    elif args.command == "project":
        handle_project(api, args)
    else:
        parser.print_help()

def print_ls(api, path):
    """Formatiertes ls mit Embryo-Markierung"""
    entries = api.ls(path)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Type", width=6)
    table.add_column("Name", width=40)
    table.add_column("Size", width=10)
    table.add_column("Modified", width=20)
    
    for entry in entries:
        # Type-Icon
        if entry["type"] == "embryo":
            type_icon = "🥚"
            name = f"{entry['name']}%"
            style = "dim"
        elif entry["type"] == "directory":
            type_icon = "📁"
            name = entry["name"]
            style = "blue"
        else:
            type_icon = "📄"
            name = entry["name"]
            style = None
        
        # Size formatieren
        if entry["size"] < 1024:
            size = f"{entry['size']} B"
        elif entry["size"] < 1024*1024:
            size = f"{entry['size']/1024:.1f} KB"
        else:
            size = f"{entry['size']/(1024*1024):.1f} MB"
        
        table.add_row(
            type_icon,
            f"[{style}]{name}[/{style}]" if style else name,
            size,
            entry["modified"].strftime("%Y-%m-%d %H:%M")
        )
    
    console.print(table)

def handle_embryo(api, args):
    """Embryo-Commands"""
    if args.embryo_cmd == "create":
        api.create_embryo(args.name, args.template)
        console.print(f"[green]✓ Embryo '{args.name}' created[/green]")
    elif args.embryo_cmd == "birth":
        api.birth_embryo(args.name)
        console.print(f"[green]✓ Embryo '{args.name}' born[/green]")
    elif args.embryo_cmd == "list":
        embryos = api.list_embryos()
        if embryos:
            console.print("Embryos:")
            for embryo in embryos:
                console.print(f"  🥚 {embryo}%")
        else:
            console.print("[dim]No embryos found[/dim]")

def handle_project(api, args):
    """Project-Commands"""
    if args.project_cmd == "info":
        project = api.get_current_project()
        if project:
            console.print(f"Project: [bold]{project['name']}[/bold]")
            console.print(f"Path: {project['path']}")
            console.print(f"Templates: {', '.join(project['templates'])}")
        else:
            console.print("[yellow]Not in a project[/yellow]")
    elif args.project_cmd == "create":
        api.create_project(args.name, args.template)
        console.print(f"[green]✓ Project '{args.name}' created[/green]")

if __name__ == "__main__":
    main()
