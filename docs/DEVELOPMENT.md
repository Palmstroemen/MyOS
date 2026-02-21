# MyOS Development Guide

## Design Docs

- [Designdocument Projects](../core/Dokumentation/Designdocument%20Projects.md)
- [Designdocument BlueprintLayer](../core/Dokumentation/Designdocument%20BlueprintLayer.md)
- [Designdocument ACLs](../core/Dokumentation/Designdocument%20ACLs.md)
- [Designdocument Tags](../core/Dokumentation/Designdocument%20Tags.md)
- [Designdocument Export-Import](../core/Dokumentation/Designdocument%20Export-Import.md)

## Repository Structure

```
MyOS/
├── core/                 # API, FUSE layer, project config, ACLs
├── Scope/                # QML GUI file browser
├── PostFix/              # Markdown editor
├── cli/                  # CLI tools (myls, myproject, mytag, etc.)
├── core/Dokumentation/   # Design documents
├── docs/                 # Consolidated documentation
├── MyOS_Test/            # Test/demo project structure
└── LICENSE
```

## Development Environment Setup

### Dependencies

```bash
sudo apt-get install fuse3 libfuse3-dev python3-pip
pip3 install -r core/requirements.txt
```

### Run Tests

```bash
# All tests
python3 -m pytest core/tests/unit cli/tests PostFix/tests -v

# Core only
python3 -m pytest core/tests/unit/

# CLI only
python3 -m pytest cli/tests/

# PostFix only
python3 -m pytest PostFix/tests/
```

### Launch Applications

```bash
python3 Scope/Scope.py
python3 PostFix/cli.py path/to/file.md
python3 cli/myls.py MyOS_Test/Projekte/ --recent=5
```

## Security

- Path traversal protection in embryo paths and API
- ACL system: `off` / `monitor` / `enforce` (see [ACL_ROLLOUT.md](../core/Dokumentation/ACL_ROLLOUT.md))
- Test in user space; do not run FUSE as root

## Contribution Guidelines

1. Discuss changes via GitHub issue first
2. Small, focused pull requests
3. Add tests for new features
4. Update documentation

---

*Last verified: 2026-02-17*
