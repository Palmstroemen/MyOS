# MyOS: A Human-Centric Operating Environment

> **Organically growing, project-centric file management for the human workflow**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Status: Prototype](https://img.shields.io/badge/status-prototype-orange)](https://github.com/Palmstroemen/MyOS)

## 🎯 Vision

A new OS paradigm built on LINUX.

**MyOS** is an experimental Linux desktop concept that puts the user and their projects at the center — not the underlying technology.  
The goal is an intuitive, context-sensitive environment where everything revolves around your current project and its structure.

Modern operating systems are built around technical concepts (folders, files, paths), not how humans naturally work with **projects**. MyOS reimagines the desktop as a project-centric environment that grows organically with your work.

Traditional file managers show you *what is*. MyOS shows you **what could be** - and helps you get there.

## 🎯 What MyOS shall become?

[GitHub-Link](https://github.com/Palmstroemen/MyOS#-what-is-myos)

- **Project-Based Desktop:**
	Instead of a classic multi-user setup → a multi-project environment for a single user.  
    Each project has its own desktop, launcher, wallpaper, and app configuration. Open windows stay tied to their respective projects.
    
- **Deep Obsidian Integration:** 
	Obsidian becomes the default text and note editor — running in a clean, distraction-free "Zen mode".  
    Every project is automatically an Obsidian Vault.
    
- **Underlying GIT**
	An underlying simplyfied GIT-Layer for Versioning and Collaboration on everything.
	
- **Standardized Project Folder Structures:** Projects offer predefined but initially hidden folders (`finance`, `legal`, `docs`, etc.),  
    which only become visible when needed.
    
- **Permissions and Localization:** Folder names and access rights can be customized per project and language preference, without technical hurdles.

## 🚀 Vision

The tools for all this already exist — but they're overly complicated and fragmented.  
**MyOS** aims to unify these capabilities into one clean, intuitive environment with smart defaults and a gentle learning curve.
### Core Principles
- **Project-Centered**: Everything revolves around projects, not isolated files
- **Organically Growing**: Structure evolves with requirements
- **Unix-Compatible**: Builds on existing standards
- **Transparent & Safe**: No "magic" at the cost of control

## ✨ Core Features

### 1. Potential Folders (`%`-Magic)
```bash
# Folders ending with % are "potential" - they don't exist physically yet
ls mount/                  # Shows: project%, finance%, team%
touch mount/project%/test.txt  # Materializes project/ and creates test.txt

### 2. Intelligent Project View (`myls`)

bash

# Standard view (current level)
myls mirror/

# Recent files from anywhere in project
myls mirror/ --recent=5

# Intelligent flattening (1-level depth)
myls mirror/ --roentgen         # Shows: test.txt   (in project)

# Combined overview
myls mirror/ --all

# Show only blueprint folders
myls . --potential

### 3. Smart Uniqueness Rule

When multiple files share the same name, MyOS requires explicit paths - no guessing!

## 🚀 60-Second Quick Start

### 1. Install Dependencies

bash

# Ubuntu/Debian
sudo apt-get install fuse3 libfuse3-dev python3-pip
pip3 install fuse-py

# Or development-only (no sudo):
pip3 install --user fuse-py

### 2. Get the Code

bash

git clone https://github.com/Palmstroemen/MyOS.git
cd MyOS/prototype
chmod +x myos_core.py myls.py

### 3. Experience MyOS Magic

bash

# Terminal 1: Start MyOS
python3 myos_core.py ./mirror ./mount

# Terminal 2: Watch potential folders materialize!
ls mount/                         # Shows: project% finance% team%
touch mount/project%/hello.txt    # Folder materializes automatically!
ls mount/                         # Now shows: project/ (without %)

# Terminal 3: Intelligent project view
./myls.py mount/ --roentgen       # See files from subfolders

## 🏗️ Architecture

text

┌─────────────────────────────────────────┐
│          Applications (Nemo, CLI)       │
├─────────────────────────────────────────┤
│          MyOS Tools (myls, etc.)        │
├─────────────────────────────────────────┤
│   FUSE Layer (% materialization)        │
├─────────────────────────────────────────┤
│        Physical Filesystem              │
└─────────────────────────────────────────┘

### Components

- **`myos_core.py`**: FUSE filesystem with %-folder materialization
    
- **`myls.py`**: Intelligent file lister with multiple view modes
    
- **`.myproject`**: Project configuration (future feature)
    

## 📖 Command Reference

### `myls` - Intelligent File Lister

bash

myls [PATH]                    # Normal directory listing
myls [PATH] --recent[=N]       # N newest files (default: 10)
myls [PATH] --roentgen[=N]     # X-ray: small folders seen through while N lines suffice (default: terminal height)
myls [PATH] --flat             # Force flattening (1-level)
myls [PATH] --all              # Combined overview
myls [PATH] --potential        # Show potential folders only

### FUSE Operations

All standard Unix commands work transparently:

bash

touch mount/folder%/file.txt   # Materializes folder/ and creates file
cp file.txt mount/folder%/     # Materializes folder and copies
mkdir mount/client%/proposal   # Creates client/ and proposal/
rmdir mount/old_project%       # Removes blueprint (if empty)

## 📊 Project Status: v0.2.0

### ✅ **Phase 1: Core FUSE Implementation** - COMPLETE

- Blueprint folder materialization (`project%/` → `project/`)
    
- Intelligent file lister (`myls` with `--recent`, `--roentgen`, `--all`)
    
- Secure path handling and error management
    

### 🔄 **Phase 2: Template System** - IN DEVELOPMENT

- Project templates (`.myproject` configuration files)
    
- Template-specific blueprint folders
    
- Automatic project type detection
    

### 📅 **Phase 3: Rooms & Contexts** - PLANNED

- Virtual workspace management (`myrooms`)
    
- Context-sensitive desktop adaptation
    
- Spatial navigation between workspaces
    

## 🔒 Security & Limitations

**⚠️ PROTOTYPE - Not for production use**

### Current Features

- ✅ Blueprint folder materialization
    
- ✅ Intelligent file listing with multiple views
    
- ✅ Path traversal protection
    
- ✅ Safe error handling
    
- ✅ Clean architecture (FUSE + tools separated)
    

### Known Limitations

- Performance not optimized for large collections
    
- No GUI integration yet (CLI only)
    
- Blueprint folders are hardcoded (not configurable)
    
- Runs in userspace only
    

### Safe Usage Recommendations

- Start with test data in `mirror/` directory
    
- Don't run FUSE as root
    
- Regular backups of `mirror/` contents
    
- Report any unexpected behavior
    

## 🛣️ Roadmap

### Phase 1: Complete Prototype (Current)

- %-folder materialization
    
- Intelligent myls tool
    
- .myproject configuration files
    
- Basic GUI integration proof-of-concept
    

### Phase 2: Production Readiness

- Security audit and hardening
    
- Performance optimization
    
- Comprehensive test suite
    
- Packaging (Deb, RPM, AUR)
    

### Phase 3: Advanced Features

- Nemo/Dolphin plugin
    
- Team collaboration features
    
- Integrated version history
    
- Dynamic time/context structures
    

## 🤝 Contributing

MyOS is in active prototype development. We welcome:

- Bug reports (especially security issues)
    
- Use case feedback (how do you organize projects?)
    
- Documentation improvements
    
- Feature suggestions
    

Please open a GitHub issue to discuss changes or report problems.

## 📄 License

MIT License - see [LICENSE](https://license/) file for details.

## 🙏 Acknowledgments

- Built on FUSE for filesystem abstraction
    
- Inspired by human-centered design principles
    
- Thanks to all early testers and feedback providers
    
- Python's fuse-py bindings
    

_MyOS is not affiliated with any operating system vendor._