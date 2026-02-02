# MyOS: Projektleitfaden & Entwicklungspfad

## 📋 Projekt-Status: PROTOTYP FUNKTIONSFÄHIG

### Aktueller Stand (v0.1.0)
✅ **Funktionierende Kernfeatures:**
1. FUSE mit %-Materialisierung (`projekt%/` → `projekt/`)
2. Intelligenter Dateilister (`myls`) mit:
   - `--recent`: Neueste Dateien
   - `--roentgen`: Intelligente Flachansicht (1 Ebene → `/../`)
   - `--all`: Kombinierte Übersicht
3. Grundlegende Architektur (FUSE + Tools getrennt)

✅ **Testumgebung:**
- Verzeichnis: `~/Dokumente/MyOS/Prototyp/`
- Mirror: `mirror/` (physische Dateien)
- Mount: `mount/` (FUSE-Ansicht mit %-Magic)

## 🎯 Master-Prompt für KI/Chat-Assistenten
PROJEKT: MyOS - Human-Centric Operating Environment
STATUS: Funktionsfähiger Prototyp (v0.1.0)
ZIEL: Organisch wachsende, projektzentrierte Dateiverwaltung

KERNPRINZIPIEN:

Projektzentriert (nicht dateizentriert)

Organisches Wachstum (Struktur entwickelt sich mit)

Unix-kompatibel (erweitert, ersetzt nicht)

Transparent & sicher (keine "Magie" auf Kosten der Kontrolle)

AKTUELLER CODE:

myos_core.py: FUSE-Implementation mit %-Materialisierung

myls.py: Intelligenter Dateilister mit verschiedenen Ansichten

Testumgebung: mirror/ (physisch), mount/ (FUSE-Ansicht)

ENTWURFSENTSCHEIDUNGEN:

%-Syntax für potentielle Ordner (finanzen%)

/../ Syntax für geflattete Ansicht (nur Anzeige, intern %..%)

Nur 1-Ebene Flattening in myls (einfache Regel)

Trennung: FUSE (Grundfunktion) + Tools (Intelligenz)

WICHTIGE REGELN FÜR CODE:

Dokumentation: Docstrings für alle öffentlichen Funktionen

Sicherheit: Path traversal verhindern, realpath() verwenden

Fehlerbehandlung: Explizite Fehlermeldungen, keine silent fails

Performance: Für Prototyp okay, später C/Rust für Kern

Unix-Philosophy: Ein Tool, eine Aufgabe, gut kombinierbar

NÄCHSTE SCHRITTE: Siehe "Entwicklungspfad" unten

text

## 🛣️ Entwicklungspfad (Priorisierte ToDo-Liste)

### Phase 1a: Code-Qualität & Dokumentation (HOHE PRIORITÄT)
- [ ] **Code-Kommentare** hinzufügen (Docstrings + komplexe Logik)
- [ ] **Type Hints** für bessere IDE-Unterstützung
- [ ] **Logging** statt print() für Debug-Ausgaben
- [ ] **Konfigurationsdatei** für potentielle Ordner (`.myproject`)
- [ ] **Unit Tests** für kritische Funktionen

### Phase 1b: Sicherheit & Robustheit (HOHE PRIORITÄT)
- [ ] **Path Traversal Protection** in allen FUSE-Operationen
- [ ] **Symlink Safety** (realpath() für alle Pfadoperationen)
- [ ] **Permission Handling** (Unix permissions korrekt weitergeben)
- [ ] **Error Recovery** (FUSE bei Fehlern nicht abstürzen lassen)
- [ ] **Clean Shutdown** (Ressourcen freigeben, Dateihandles schließen)

### Phase 2: Erweiterte Features (MITTLERE PRIORITÄT)
- [ ] **Eindeutigkeitsprüfung** (wie im Design-Dokument)
  - Bei Namenskonflikten: Interaktive Abfrage oder Fehler
- [ ] **`.myproject` Konfiguration**
  - Vorlagen für Projekttypen (Software, Finanzen, etc.)
  - Automatische potentielle Ordner basierend auf Template
- [ ] **Weitere myls-Optionen**
  - `--tree`: Baumansicht mit intelligenter Tiefenbegrenzung
  - `--filter`: Dateityp-Filterung (z.B. nur PDFs, nur Bilder)
  - `--stats`: Projektstatistiken (Dateianzahl, Größe, Alter)

### Phase 3: Performance & Skalierung (NIEDRIGE PRIORITÄT)
- [ ] **Caching** für häufige Operationen (readdir, getattr)
- [ ] **Incremental Scanning** statt kompletter Rescans
- [ ] **Watchdog** für Dateiänderungen (inotify/fanotify)
- [ ] **Benchmarking** gegen reale Projekte (1000+ Dateien)

### Phase 4: GUI-Integration (ZUKUNFT)
- [ ] **Nemo/Dolphin Plugin** Proof-of-Concept
- [ ] **Drei-Zonen-Layout** (potentielle Ordner, aktuelle Ebene, recent)
- [ ] **Drag & Drop** für %-Ordner Materialisierung

## 🔧 Technische Schulden & Known Issues

### Dringende Fixes:
1. **FUSE Error Handling**: Uncaught exceptions führen zu Kernel-Panics
2. **Memory Leaks**: Dateihandles in open()/release() korrekt managen
3. **Thread Safety**: FUSE kann multi-threaded sein, unser Code nicht

### Wichtige Verbesserungen:
1. **Config File Parsing**: YAML für `.myproject` mit Schema-Validation
2. **Command Line Interface**: Besseres Argument-Parsing für myls
3. **Installation Script**: Einfache Installation für Testuser

### Langfristige Entscheidungen:
1. **Sprache**: Python für Prototyp → C/Rust für Production?
2. **FUSE Library**: fuse-py → libfuse direkt (C) oder rust-fuse?
3. **Distribution**: Standalone vs. System Package (deb, rpm, AUR)

## 🐛 Aktuelle Probleme & Workarounds

### Problem 1: FUSE mount permissions
**Symptom**: `fusermount: option allow_other only allowed if...`
**Workaround**: Ohne `allow_other` laufen lassen, nur für aktuellen User
**Lösung**: `/etc/fuse.conf` anpassen oder User-Namespace verwenden

### Problem 2: myls Argument-Parsing
**Symptom**: `./myls.py --recent mirror/` funktioniert nicht
**Workaround**: `./myls.py mirror/ --recent` (Pfad zuerst)
**Lösung**: Eigenes Argument-Parsing oder argparse Positionals fixen

### Problem 3: Keine .myproject Unterstützung
**Symptom**: `--potential` findet keine Ordner in mirror/
**Workaround**: Nur in mount/ verwenden (FUSE zeigt %-Ordner)
**Lösung**: `.myproject` Dateien lesen und parsen

## 📁 Projektstruktur (Empfohlen)
myos/
├── prototype/ # Aktueller Prototyp
│ ├── myos_core.py # FUSE-Implementation
│ ├── myls.py # Intelligenter Lister
│ ├── mirror/ # Physische Dateien (Test)
│ └── mount/ # FUSE-Mountpoint (Test)
├── docs/ # Dokumentation
│ ├── DESIGN.md # Ursprüngliches Designdokument
│ ├── ARCHITECTURE.md# Technische Architektur
│ └── API.md # Developer API
├── tests/ # Testsuite
│ ├── unit/ # Unit Tests
│ └── integration/ # Integration Tests
└── tools/ # Zusätzliche Tools
├── myfind.py # Intelligente Suche
└── mycp.py # Konflikt-sicheres Kopieren

text

## 🚨 Sicherheits-Checkliste

### Vor jeder Commit:
- [ ] Path traversal getestet? (`../../../etc/passwd`)
- [ ] Symlinks korrekt behandelt? (realpath() verwendet?)
- [ ] Permission checks vorhanden? (read/write/execute)
- [ ] Keine Passwörter/Keys im Code?
- [ ] Error messages enthalten keine internen Infos?

### Vor jedem Release:
- [ ] FUSE als nicht-root getestet?
- [ ] Boundary cases getestet? (sehr lange Pfade, Sonderzeichen)
- [ ] Memory usage unter Kontrolle? (keine leaks)
- [ ] Alle File Descriptors geschlossen?

## 🤝 Onboarding für neue Entwickler

### Erste Schritte:
1. `git clone https://github.com/yourusername/myos.git`
2. `cd myos/prototype`
3. `pip install fuse-py`
4. `python3 myos_core.py ./mirror ./mount` (in Terminal 1)
5. `./myls.py mount/ --roentgen` (in Terminal 2)

### Wichtige Code-Abschnitte verstehen:
1. **`myos_core.py:MyOSCore._materialize_path()`** - %-Magic
2. **`myos_core.py:MyOSCore.getattr()`** - FUSE Metadata
3. **`myls.py:MyOSLister._flatten_smart()`** - /../ Darstellung
4. **`myls.py:MyOSLister.list_recent()`** - Recent-Files Logik

### Debugging:
- FUSE Debug: `python3 myos_core.py -d ./mirror ./mount` (foreground)
- myls Debug: `./myls.py --recent=3 mirror/ 2>&1 | grep -i debug`
- System Debug: `strace -e trace=file python3 myos_core.py ...`

## 📈 Erfolgskriterien für v1.0

### Minimal Viable Product:
- [ ] Sicher (keine bekannten CVEs)
- [ ] Stabil (läuft 24/7 ohne Crash)
- [ ] Dokumentiert (Installation + Basic Usage)
- [ ] Testbar (CI Pipeline existiert)

### Nice-to-Have:
- [ ] GUI-Integration (Nemo/Dolphin Plugin)
- [ ] Performance (100k Dateien ohne spürbare Latenz)
- [ ] Community (5+ externe Contributor)

---

**Letzte Aktualisierung:** $(date)
**Nächste Review:** $(date -d "+2 weeks")
**Verantwortlich:** [Dein Name]
Wie du dieses Dokument nutzt:
Bei jedem neuen Chat/Coder: Den Master-Prompt kopieren

Für Planung: Den Entwicklungspfad durchgehen und Prioritäten setzen

Bei Problemen: In Aktuelle Probleme nach Workarounds suchen

Vor Releases: Die Checklisten durchgehen

Für neue Teammitglieder: Onboarding Abschnitt teilen


## **2. Aktualisierung nach Rooms:**

```markdown
# MyOS Development Roadmap

## Current Sprint: Template System Implementation
**Duration:** This week  
**Goal:** Basic template system with `.myproject` files

### Tasks (Priority Order):
1. [ ] **`.myproject` file format** (YAML/JSON)
   - Define blueprint folders per project type
   - Include metadata (project type, description)
   - Simple validation schema

2. [ ] **Template manager CLI** (`myos-template`)
   - `myos-template list` - Show available templates
   - `myos-template create <project> --template=<type>`
   - `myos-template detect <path>` - Auto-detect project type

3. [ ] **Update `myos_core.py`** to read `.myproject`
   - Load blueprint folders from config, not hardcoded
   - Fallback to default if no config exists
   - Cache template data for performance

4. [ ] **Update `myls.py`** for template awareness
   - `myls --template-info` - Show project type and structure
   - Color-code or mark template-specific folders
   - Suggest missing folders based on template

5. [ ] **Basic template library**
   - `software.yaml` - For development projects
   - `finance.yaml` - For financial projects  
   - `legal.yaml` - For legal/document projects
   - `creative.yaml` - For art/music/design

## Next Sprint: Template Intelligence & Rooms Foundation
**Estimated:** Next week

### Planned Features:
1. [ ] **Template inheritance** - Templates can extend others
2. [ ] **Automatic project classification** - Detect type from content
3. [ ] **Room system design** - Architecture for `myrooms`
4. [ ] **Basic desktop integration** - Wallpaper switching per project type

## Long-term Vision
- **Rooms/Workspaces** (`myrooms`) - Context-sensitive environments
- **3D/VR interfaces** - Spatial computing integration  
- **AI-assisted organization** - Smart suggestions and automation
- **Team collaboration features** - Shared workspaces and permissions

## Technical Debt & Improvements Needed
- [ ] Better error handling in FUSE layer
- [ ] Performance optimization for large directories
- [ ] Comprehensive test suite
- [ ] Security audit of path handling
