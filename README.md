# MyOS

A new OS paradigm for Linux: project-centric desktop and filesystem.

**MyOS** is an experimental Linux desktop concept that puts the user and their projects at the center. The goal is an intuitive, context-sensitive environment where everything revolves around your current project and its structure.

## Project Status

**Current phase:** MVP implementation — core API, Scope GUI, CLI tools, and blueprint layer are in place and iteratively hardened. Not a complete operating system; early experiments with FUSE, QML file browser, tagging, and workflow tools.

For a concise status snapshot and priorities, see [docs/STATUS.md](docs/STATUS.md). For the operational roadmap and open questions, see [ProjectLogbook.md](ProjectLogbook.md).

---

## What is MyOS?

- **Project-based desktop:** Multi-project environment for a single user. Each project can have its own desktop, launcher, and app configuration; open windows stay tied to their respective projects.

- **Standardized project structures:** Projects offer predefined but initially hidden folders (templates/embryos) that only materialize when used (e.g. first file moved in).

- **Deep Obsidian integration (vision):** Obsidian as the default note editor in a distraction-free mode; every project as an Obsidian Vault.

- **Permissions and localization:** Folder names and access rights can be customized per project and language.

---

## Vision

The building blocks exist but are fragmented. MyOS aims to unify them into one clean, intuitive environment with sensible defaults and a gentle learning curve.

---

## Repository Structure

| Path | Description |
|------|--------------|
| **core/** | API, FUSE/blueprint layer, project config, ACLs, tagging, design docs |
| **Scope/** | QML file browser (Templates + Projects rows, tags, CWD/CTD) |
| **PostFix/** | Markdown editor with tag sidebar, Obsidian-compatible |
| **cli/** | CLI tools (myls, myproject, mytag, myedit, myfilter, etc.) |
| **docs/** | Documentation index, development guide, conventions, security |
| **Vision/** | Concept and GUI notes (e.g. CWD/CWP/CTD) |
| **Learning MyOS/** | Tutorial and learning content (DE/EN) |
| **MyOS_Test/** | Test/demo project structure |

Design documents live under `core/Dokumentation/`. Entry points: [Designdokument.md](Designdokument.md), [docs/INDEX.md](docs/INDEX.md).

---

## Quick Start

**Run the Scope file browser (requires Qt/QML and Python backend):**
```bash
python3 Scope/Scope.py
```

**Run tests:**
```bash
python3 -m pytest core/tests/unit cli/tests PostFix/tests -v
```

**CLI examples:**
```bash
python3 cli/myls.py MyOS_Test/Projekte/ --extended
python3 PostFix/cli.py path/to/file.md
```

Setup, dependencies, and contribution guidelines: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
