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

## UI Language (i18n)

UI strings in the code are **English** (`qsTr("…")` in QML/JS, `self.tr("…")` in Python);
every other language is a translation:

- `Scope/i18n/scope_de.ts`, `PostFix/i18n/postfix_de.ts` — German translations
  (source), compiled to the `.qm` files the apps load.
- After adding or changing strings run `python3 scripts/update_translations.py`: it
  extracts the strings (new ones arrive as "unfinished"), keeps existing translations and
  rebuilds the `.qm`. Translate the unfinished entries (e.g. Qt Linguist) and run it again.
- Language: `MYOS_UI_LANG` (default `de`); English needs no file.
- `Scope/tests/test_scope_i18n.py` and `PostFix/tests/test_postfix_i18n.py` fail when a
  string has no German translation or a `.qm` is out of date.

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
