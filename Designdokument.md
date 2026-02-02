# **MyOS:

## **1. Einführung und Vision**

### 1.1 Das Problem

Aktuelle Betriebssysteme und Dateimanager sind auf technische Konzepte ausgerichtet (Ordner, Dateien, Pfade), nicht auf die natürliche Arbeitsweise von Menschen mit ihren **Projekten**. Nutzer müssen ständig zwischen verschiedenen Programmen wechseln und komplexe Ordnerstrukturen von Hand pflegen.

### 1.2 Die Vision

MyOS ist ein neuartiger Ansatz für den Desktop, bei dem **Projekte und deren Inhalte im Mittelpunkt** stehen. Es stellt eine intelligente, mitwachsende Arbeitsumgebung bereit, die sich automatisch an den Nutzer und seine Daten anpasst.

### 1.3 Grundprinzipien

- **Projektzentriert**: Alles dreht sich um Projekte, nicht um isolierte Dateien.
    
- **Organisch wachsend**: Die Struktur entwickelt sich mit den Anforderungen.
    
- **Unix-kompatibel**: Baut auf bestehenden Standards auf und erweitert sie sinnvoll.
    
- **Transparent und sicher**: Keine "Magie" auf Kosten der Kontrolle oder Datensicherheit.
    

---

## **2. Grundlegende Konzepte und neue Begriffe**

### 2.1 Projektordner (Project Folder)

Ein ganz normaler Ordner im Dateisystem, der durch eine versteckte Konfigurationsdatei (`.myproject`) als "MyOS-Projekt" gekennzeichnet ist. Darin gelten besondere Regeln für die Darstellung und Verwaltung von Inhalten.

### 2.2 Potenzielle Ordner (Potential Folders)

Ordnernamen, die mit einem `%`-Zeichen enden (z.B. `finanzen%`). Sie stellen eine **Absichtserklärung** dar: "Hier könnte einmal der Ordner `finanzen/` entstehen." Sie werden im Dateimanager angezeigt, existieren physisch aber noch nicht.

**Verhalten**:

- **Lesen** (`ls`, `test -d`): Ein potentieller Ordner `finanzen%` verhält sich, als ob er nicht existiert.
    
- **Schreiben** (`cp file.txt finanzen%/`, `touch finanzen%/neuedatei.txt`): Der Befehl wird ausgeführt und der Ordner `finanzen/` dabei **automatisch physisch erstellt** (materialisiert).
    

### 2.3 Flache Projektansicht (Flat Project View)

Die Standardansicht eines Projektordners. Um die Übersicht zu wahren, werden darin nicht alle verschachtelten Unterordner gezeigt. Stattdessen werden wichtige Dateien und Unterordner aus der Tiefe **flach im Projektstamm** angezeigt.

**Darstellung**:

- `ordner/../datei.txt`: Eine Datei, die sich eigentlich im (Unter-)Ordner `ordner/` befindet.
    
- `wichtiger/unterordner/`: Ein besonders relevanter oder inhaltsreicher Unterordner.
    

**Zugriff**:  
Nutzer können sowohl mit dem flachen Namen (`datei.txt`) als auch mit expliziten Pfaden (`ordner/../datei.txt` oder `ordner/unterordner/datei.txt`) auf ihre Daten zugreifen.

### 2.4 Intelligente Sichtbarkeit (Intelligent Visibility)

Das System entscheidet automatisch, was in der flachen Ansicht angezeigt wird, basierend auf Faktoren wie:

- **Anzahl der Dateien** in einer Struktur
    
- **Aktualität** und Zugriffshäufigkeit
    
- **Dateityp** (z.B. werden `.xls`-Dateien priorisiert)
    
- Vom Nutzer definierte **Wichtigkeit**
    

Ziel: Anfangs eine einfache, flache Liste; mit wachsendem Projekt eine klare, tiefere Ordnerstruktur.

### 2.5 Eindeutigkeitsregel (Uniqueness Rule)

Ein Kernprinzip für Sicherheit und Vorhersehbarkeit: **Mehrdeutige Befehle führen zu einem klaren Fehler.**

**Beispiel**:

bash

# Angenommen, 'bericht.pdf' existiert an zwei Stellen im Projekt.
$ cp bericht.pdf ~/Backup/
# FEHLER (nicht: raten und kopieren)
MyOS: Mehrdeutig! 'bericht.pdf' wurde an 2 Stellen gefunden:
[1] finanzen/quartalsberichte/bericht.pdf
[2] marketing/präsentationen/bericht.pdf
Bitte wählen Sie [1/2] oder einen expliziten Pfad verwenden.

---

## **3. Entwicklungspfad eines Projekts**

### Phase 1: Projektinitialisierung

Ein neuer Ordner wird erstellt und als MyOS-Projekt markiert. Basierend auf einer Vorlage (Template) werden **potenzielle Ordner** angelegt (z.B. `finanzen%`, `team%`, `notizen%`).

### Phase 2: Erste Inhalte und Materialisierung

Der Nutzer beginnt, Dateien abzulegen. Beim ersten Speichern in einen potentiellen Ordner (z.B. `cp rechnung.pdf finanzen%/`) wird dieser **materialisiert** (das `%`-Zeichen verschwindet, der physische Ordner `finanzen/` entsteht). Dateien in materialisierten, aber noch "dünnen" Ordnern werden in der flachen Projektansicht als `ordner/../datei` angezeigt.

### Phase 3: Organisches Wachstum und Strukturierung

Je mehr Inhalte ein Projekt bekommt, desto mehr verschiebt sich die Ansicht von einer flachen Liste hin zu einer klaren Baumstruktur. Sehr aktive oder volle Unterordner (z.B. `finanzen/rechnungen/`) werden selbst in der flachen Stammansicht sichtbar.

### Phase 4: Reifes Projekt mit stabiler Struktur

Das Projekt hat eine klare, tiefe Ordnerhierarchie entwickelt, die den Arbeitsabläufen entspricht (z.B. `/projekt/entwicklung/`, `/projekt/ dokumentation/`, `/projekt/design/assets/`). Die flache Ansicht zeigt primär diese Hauptordner.

---

## **4. Technische Architektur (Übersicht)**

MyOS besteht aus zwei Hauptkomponenten:

### 4.1 Intelligenter Dateisystem-Layer (FUSE)

Ein virtuelles Dateisystem, das zwischen dem Nutzer und seinen physischen Daten liegt. Dieser Layer:

- **Erzeugt dynamisch Einträge** für potenzielle Ordner (`%`) und flache Datei-Links (`ordner/../datei`).
    
- **Übersetzt Aktionen**: Wandelt Operationen auf virtuelle Pfade in Operationen auf echte Pfade um (z.B. Materialisierung).
    
- **Erzwingt Regeln**: Implementiert die Eindeutigkeitsregel und intelligente Sichtbarkeit.
    

### 4.2 Dateibasierte Konfiguration und Metadaten

Alle Informationen über Projekte, Vorlagen und intelligente Regeln werden in einfachen, lesbaren Textdateien (YAML, Markdown) gespeichert, nicht in einer Datenbank.

- **Projektkonfiguration** (`.myproject`): Definiert Typ, Vorlage und Regeln eines Projekts.
    
- **Vorlagendateien**: Enthalten standardisierte Satzpotenzieller Ordner und Regeln (z.B. für "Softwareentwicklung", "Familie", "Rechtsanwalt").
    
- **Metadatendateien**: Verwalten Informationen wie Zugriffsrechte (ACLs), Verknüpfungen zwischen Dateien und Kontaktdaten.
    

---

## **5. Erste Umsetzungsschritte (Prototyp)**

Das Ziel des ersten Prototyps ist es, die **Kernmagie** erlebbar zu machen.

### Schritt 1: Grundlegendes FUSE-Dateisystem

Ein minimales Programm, das ein Verzeichnis (z.B. `~/.myos_mirror/`) als virtuelles Laufwerk einhängt. Zunächst werden alle Dateien und Ordner einfach 1:1 gespiegelt.

### Schritt 2: Potenzielle Ordner (`%`)

Erweiterung des FUSE-Layers, um Ordnernamen, die mit `%` enden, in `ls`-Auflistungen anzuzeigen. Zugriffe auf diese Ordner (z.B. `touch test%/datei.txt`) führen zur automatischen Erstellung des entsprechenden physischen Ordners (ohne `%`).

### Schritt 3: Flache Dateiansicht (`ordner/../datei`)

Erweiterung, um Dateien aus Unterordnern im Projektstamm als `ordner/../datei` anzuzeigen. Zugriffe auf diese Pfade müssen auf die echte, tiefer liegende Datei umgeleitet werden.

### Schritt 4: Eindeutigkeitsprüfung und interaktive Abfrage

Implementierung der Regel, dass der Versuch, eine mehrdeutige Datei (gleicher Name an mehreren Orten) nur mit ihrem Namen anzusprechen, zu einer **klaren Fehlermeldung mit Auswahloption** führt.

---

## **6. Langfristige Vision und Roadmap**

Nach dem funktionierenden Prototyp folgen komplexere Themen:

- **Intelligente Vorlagen**: Baukastensystem für Projektstrukturen.
    
- **Team- und Berechtigungsverwaltung**: Einfache Vergabe von Zugriffsrechten basierend auf Rollen.
    
- **Projektübergreifende Werkzeuge**: Konsistente Verwaltung von Kontakten und Ressourcen.
    
- **Kontextsensitive Desktop-Umgebung**: Fenster und Anwendungen, die an Projekte gebunden sind.
    
- **Robuste Sicherungs- und Synchronisationsstrategien**: Projektweise Backups in Clouds oder auf Server.

## **7. Erweiterte Konzepte**

### 7.1 Integrierte Versionsgeschichte (Integrated Version History)

MyOS bietet eine grundlegende, intuitive Versionskontrolle, die mit der Komplexität des Projekts wachsen kann.

**Stufe 1: Ewiges UNDO (Prototyp)**  
Jede Änderung an einer Datei oder Ordnerstruktur wird automatisch protokolliert. Der Nutzer kann über eine einfache Timeline (`myos history datei.pdf`) sehen, was sich wann geändert hat, und zu jedem früheren Zustand zurückkehren.

**Stufe 2: Manuelle Markierungen (Snapshots)**  
Der Nutzer kann bewusst wichtige Projektzustände als **Snapshot** markieren (z.B. "Version vor Kundenpräsentation"). Diese Snapshots sind benannt und leicht wiederherstellbar.

**Stufe 3: Kollaboration und Branches (Erweitert)**  
Für Teamarbeit können Änderungen verschiedener Personen abgeglichen und alternative Entwicklungszweige (Branches) verwaltet werden – ähnlich wie bei Git, jedoch stark vereinfacht und in die MyOS-Oberfläche integriert.

**Philosophie**: Die Versionskontrolle ist kein separates, komplexes Werkzeug, sondern ein natürlicher Teil des Dateisystems. Sie fängt einfach an ("Was habe ich gestern geändert?") und kann bei Bedarf mächtiger werden.

---

### 7.2 Dynamische Zeit- und Kontextstrukturen (Dynamic Time & Context Structures)

MyOS erlaubt es, Ordnerstrukturen flexibel nach verschiedenen Schemata zu organisieren und diese Schemata später zu ändern.

#### 7.2.1 Platzhalter für dynamische Strukturen

In Projektvorlagen oder Pfaden können **dynamische Platzhalter** definiert werden, die zur Laufzeit aufgelöst werden.

**Beispiele für Platzhalter**:

- `%YEAR%` → aktuelles Jahr (z.B. `2025`)
    
- `%MONTH%` → aktueller Monat (z.B. `01` für Januar)
    
- `%PROJECT_NAME%` → Name des Projekts
    
- `%USER%` → Name des aktuellen Nutzers
    

#### 7.2.2 Flexibles Einfügen von Strukturebenen

Ein Nutzer kann entscheiden, wie er seine Daten gliedern möchte. Das System hilft bei der Umorganisation.

**Beispiel: Entwicklung einer Finanzablage**

bash

# Anfang: Flache Ablage
/finanzen/rechnung_xyz.pdf

# Nutzer fügt Jahresstruktur ein:
/finanzen/%YEAR%/rechnung_xyz.pdf
# Wird bei Zugriff zu:
/finanzen/2025/rechnung_xyz.pdf

# Später möchte der Nutzer nach Monaten unterteilen:
/finanzen/%YEAR%/%MONTH%/rechnung_xyz.pdf
# Wird zu:
/finanzen/2025/01/rechnung_xyz.pdf

# Die ursprüngliche, flache Struktur bleibt im Hintergrund erhalten
# und kann als alternative "Sicht" auf die Daten genutzt werden.

#### 7.2.3 Manifestieren und Umorganisieren

Dynamische Strukturen beginnen als **potenzielle Pfadsegmente** (`%YEAR%`), die bei Bedarf **materialisiert** (also in echte, feste Ordner wie `2025/` umgewandelt) werden können.

**Umorganisieren**:  
Eine einmal erstellte Struktur (z.B. `/finanzen/2025/rechnungen/`) kann später in eine andere Struktur **überführt** werden (z.B. `/rechnungen/2025/finanzen/`). MyOS hilft dabei, alle betroffenen Dateien und Verweise konsistent zu verschieben, ohne dass Daten verloren gehen oder Pfade brechen.

**Wichtige Regel: Eindeutigkeit**  
Ein bestimmter Platzhalter (wie `%YEAR%`) darf nur **einmal pro Pfad** vorkommen, um Verwirrung zu vermeiden. `/finanzen/%YEAR%/%YEAR%_backup/` ist nicht erlaubt.

---

### 7.3 Kontextverschiebung und Projektwachstum (Context Shifting)

Wenn Projekte wachsen, entstehen oft neue logische Gruppierungen (Teams, Kunden, Produktlinien). MyOS unterstützt das **"Einschieben"** neuer Kontextebenen in bestehende Pfade.

**Beispiel: Vom einfachen zum Team-basierten Projekt**

bash

# Ursprüngliche Struktur (kleines Projekt):
/projekt/
├── finanzen/
│   └── rechnungen/
├── entwicklung/
│   └── quellcode/
└── dokumente/

# Das Projekt wächst, Teams entstehen.
# Der Nutzer entscheidet: "Ich möchte die 'Team'-Ebene einfügen."
# MyOS bietet an, bestehende Ordner unter Team-Namen zu gruppieren.

# Neue, erweiterte Sicht:
/projekt/
├── team_alpha/
│   ├── finanzen/
│   └── entwicklung/
├── team_bravo/
│   ├── finanzen/
│   └── dokumente/
└── shared/
    ├── infrastruktur/
    └── richtlinien/

# Die alten Pfade (`/projekt/finanzen/`) bleiben als "Verknüpfungen" oder
# alternative Sichten erhalten, um Abwärtskompatibilität zu gewährleisten.

**Mechanismus**:

1. **Vorschlag**: MyOS analysiert die Nutzung (welche Personen arbeiten oft mit welchen Ordnern?) und schlägt sinnvolle neue Gruppierungen vor.
    
2. **Simulation**: Der Nutzer kann die geplante Umstrukturierung in einer Vorschau betrachten.
    
3. **Umsetzung**: MyOS führt die Änderung durch, aktualisiert alle Metadaten, Verweise und Zugriffsrechte und behält dabei eine Wiederherstellungsoption (siehe 7.1).
    

---

## **8. Zusammenfassung der neuen Prinzipien**

1. **Wachsende Werkzeuge**: Funktionen wie Versionskontrolle starten einfach und werden nur so komplex, wie der Nutzer es benötigt.
    
2. **Flexible, dynamische Ordnung**: Daten können nach verschiedenen, veränderlichen Schemata (Zeit, Kontext, Team) organisiert werden. Die Struktur dient dem Nutzer, nicht umgekehrt.
    
3. **Organische Evolution**: Projekte können umstrukturiert werden, wenn sie wachsen. Das System unterstützt diese Evolution, anstatt sie zu behindern.
    

Diese Erweiterungen verstärken den Kerngedanken von MyOS: eine **mitwachsende, anpassbare und intuitive** Umgebung zu schaffen, die sich dem Menschen anpasst – nicht umgekehrt.



# MyOS Design Vision nach Rooms

## Core Philosophy
**"Organically growing systems for organically growing projects."**

MyOS doesn't force structure - it suggests and adapts based on how you actually work.

## Three-Layer Architecture

### Layer 1: Intelligent Foundation (Current Focus)

FUSE Layer → Template System → Smart Tools

text

- **Blueprint Folders**: `%` suffix for "could exist" folders
- **Project Templates**: Type-specific structures (software, finance, etc.)
- **Adaptive Views**: `myls` shows what's relevant now

### Layer 2: Contextual Workspaces (Next Phase)

Rooms → Doors → Perspectives

text

- **Rooms**: Virtual workspaces (Workshop, Studio, Office)
- **Doors**: Transitions between workspaces  
- **Perspectives**: Cross-cutting views (Finance, Legal, Documentation)

### Layer 3: Spatial Computing (Future Vision)

3D Rooms → AR Overlays → Neural Interfaces

text

- **3D Workspaces**: Navigate virtual environments
- **AR Integration**: Overlay information on physical world
- **Ambient Computing**: Environment adapts to work context

## User Journey Examples

### Example 1: Software Developer

# 1. Create project with template
myos-template create ~/projects/myapp --template=software

# 2. Work in development "room"
myrooms enter dev-lab

# 3. Focus on recent changes
myls --recent --template=software

### Example 2: Freelancer with Multiple Roles

bash

# Morning: Client work (legal perspective)
myrooms enter office
myrooms go legal
# Sees all contracts across all client projects

# Afternoon: Creative work  
myrooms enter studio
# Music tools appear, legal tools fade

# Evening: Financial review
myrooms go finance
# All invoices and payments across all projects

## Design Principles

1. **Progressive Disclosure**: Start simple, reveal complexity as needed
    
2. **Context Preservation**: Environment remembers where you left off
    
3. **Spatial Metaphors**: Rooms, doors, windows - not just folders
    
4. **Template-Driven**: Structure emerges from intention, not enforcement
    
5. **Unix-Compatible**: Enhances, doesn't replace, existing tools
    

text

## **4. Entwickler-Notizen (DEV_NOTES.md für schnelle Referenz):**


# MyOS Developer Notes

## Current Code Structure

prototype/  
├── myos_core.py # FUSE layer (needs template support)  
├── myls.py # File lister (needs template awareness)  
├── myos_template.py # NEW: Template management  
├── mirror/ # Physical files  
└── mount/ # FUSE mount point


## Key Design Decisions
1. **Blueprint Syntax**: `%` suffix for potential folders
2. **Flat View Syntax**: `/../` in display, `%..%` internally
3. **Template Format**: YAML for `.myproject` files
4. **Room Metaphor**: Workspaces with spatial relationships

## Immediate Next Steps
1. Implement `.myproject` YAML parser
2. Update `MyOSCore.__init__()` to read template
3. Create basic template CLI
4. Test template switching

## Testing Commands

# Test current implementation
python3 myos_core.py ./mirror ./mount
./myls.py mount/ --roentgen

# Test templates (after implementation)
./myos_template.py create ./test_project --template=software
ls -la ./test_project/.myproject

## Known Issues & Limitations

- Hardcoded blueprint folders in `myos_core.py`
    
- No project type detection
    
- Limited error recovery in FUSE
    
- Performance not optimized for >1000 files
  
  
# **Architectural Perspective: MyOS as MVC-for-the-Filesystem**

## **The MVC Analogy**

MyOS can be understood through the lens of the classic Model-View-Controller pattern, but applied at the operating system level:

- **Model**: The physical storage (`Plate`) and project metadata (`ProjectConfig`, `LensTemplate`) – the "what" of your data.
    
- **View**: What users see and interact with – virtual directories, ghost folders, project decorators in `~/Projekte/`.
    
- **Controller**: The `LensEngine` and FUSE layer that translate filesystem operations into MyOS logic – the "how" of interaction.
    

## **Key Differences from Traditional MVC**

Unlike application-focused MVC, MyOS operates **system-wide**:

1. **Filesystem as UI**: Every application becomes a "MyOS app" because they all interact with the virtual filesystem. There's no separate GUI – the directory structure _is_ the interface.
    
2. **Reactive, Not Active**: The controller doesn't initiate actions; it **reacts** to filesystem calls (`readdir`, `mkdir`, `open`) from any source (command line, file manager, IDE, etc.).
    
3. **State is the Filesystem**: Project state isn't stored in memory but manifested through materialized directories and persistent ghost markers.
    
4. **Layered Abstraction**: MyOS uses a **Decorator Pattern** over the existing filesystem, adding intelligence without replacing underlying infrastructure.
    

## **Practical Implications**

This architecture means:

- **No app integration needed**: Any tool that works with files automatically works with MyOS.
    
- **Progressive disclosure**: Complexity emerges only when needed (ghosts → materialization → templates).
    
- **Unix philosophy extended**: "Everything is a file" becomes "Every project is a filesystem-with-intent."
    

MyOS isn't just another file manager – it's a **context-aware filesystem** that understands projects, not just folders.


# Anhang: MyOS Designdokument - Embryo-Folder Konzept und Evolution

## 1. Das Grundkonzept: Embryo vs. Ghost

### **Das Problem mit "Ghost-Folders"**
Im aktuellen MyOS Prototyp verwenden wir das Konzept von "Ghost-Folders" - virtuelle Ordner mit einem `%`-Suffix (z.B. `finance%`), die automatisch materialisiert werden, wenn jemand etwas darin speichert. Dieser Begriff ist jedoch **irreführend**:

- **Ghost:** Etwas, das **nach dem Tod** erscheint (Vergangenheitsbezug)
- **Embryo:** Etwas, das **noch nicht geboren** ist, aber das Potenzial hat zu wachsen (Zukunftsbezug)

Unsere virtuellen Ordner sind **Embryos** - sie existieren als Potential in Templates und werden bei Bedarf zu realen Verzeichnissen.

## 2. Die drei Ebenen der Marker-Implementierung

### **Ebene 1: Aktueller Zustand (`%`-Suffix)**
```
/projects/Haus/finance%/   ← Sichtbarer Marker
```

**Vorteile:**
- Einfach zu implementieren und zu debuggen
- Sofort erkennbar für Benutzer
- Keine Dateisystem-Abhängigkeiten

**Nachteile:**
- Sieht "hacky" aus
- Kollidiert mit Namenskonventionen
- Begrenzte Metadaten-Speicherung

### **Ebene 2: Extended Attributes (xattr)**
```python
# Unsichtbarer Marker
os.setxattr("/projects/Haus/finance", 
            "user.myos.embryo", 
            b"template=standard;created=2024-01-26")
```

**Vorteile:**
- Unsichtbar im normalen `ls`
- Kann strukturierte Metadaten speichern
- Native Dateisystem-Funktionalität
- Trennung von Permission-Bits

**Nachteile:**
- Nicht alle Dateisysteme unterstützen xattr (FAT, exFAT)
- Backup-Tools könnten xattr verlieren
- Schwieriger zu debuggen

### **Ebene 3: Permission-Bits (Sticky Bit & Co.)**
```python
# Sticky Bit als Marker
os.chmod("/projects/Haus/finance", 0o1700)  # rwx------ + sticky bit
```

**Vorteile:**
- Extrem schnell zu prüfen
- Universell unterstützt
- Einfach zu migrieren

**Nachteile:**
- Begrenzte Anzahl verfügbarer Bits
- Könnte legitime Nutzung stören
- Wenig erweiterbar

## 3. Die Projekt-Lebenszyklus-Erweiterung

### **Die Erkenntnis:**
Projekte haben einen natürlichen Lebenszyklus, dessen **Endphase oft vernachlässigt wird**. Nach Abschluss stellt sich die Frage: "Was ist wichtig, was kann weg?"

### **Die Lösung:**
Wir können die gleichen Marker-Technologien für **Projekt-Lebenszyklus-Management** verwenden:

```python
# Dateien markieren als...
os.setxattr(file, "user.myos.essential", b"true")    # Unbedingt behalten
os.setxattr(file, "user.myos.disposable", b"true")   # Kann gelöscht werden

# ODER mit Permission-Bits:
os.chmod(essential_file, mode | stat.S_ISVTX)   # Sticky Bit = essential
os.chmod(disposable_file, mode & ~stat.S_ISVTX) # Kein Sticky = disposable
```

### **Workflow:**
1. **Entwicklungsphase:** Alle Dateien sind "essential" (Sticky Bit gesetzt)
2. **Review-Phase:** Manuelles Markieren von "disposable" Dateien
3. **Cleanup-Phase:** Automatisches Löschen oder Archivieren

## 4. Hybrid-Ansatz für maximale Kompatibilität

### **Die Strategie:**
1. **Primär-Marker:** Extended Attributes (wenn verfügbar)
2. **Sekundär-Marker:** Permission Bits (Sticky Bit)
3. **Legacy-Marker:** `%`-Suffix (für Migration/Backwards Compatibility)

### **Implementierungs-Priorität:**
```python
class EmbryoDetector:
    def is_embryo(self, path: Path) -> bool:
        # 1. Prüfe xattr (modernste Technologie)
        try:
            if os.getxattr(path, "user.myos.embryo"):
                return True
        except OSError:
            pass  # xattr nicht unterstützt
        
        # 2. Prüfe Permission Bits (breite Kompatibilität)
        if os.stat(path).st_mode & stat.S_ISVTX:
            return True
        
        # 3. Prüfe Legacy %-Suffix (für Migration)
        if path.name.endswith("%"):
            return True
        
        return False
```

## 5. Migrationspfad

### **Phase 1 (v1.0):** `%`-Suffix
- Einfach, funktioniert überall
- Gute Basis für Testing und Feedback

### **Phase 2 (v1.5):** Hybrid-Ansatz
- Neue Projekte: xattr + Sticky Bit
- Alte Projekte: Automatische Migration von `%` → xattr
- Rückwärtskompatibel

### **Phase 3 (v2.0):** Nur xattr
- Saubere, standardkonforme Implementierung
- Erweiterte Metadaten-Speicherung
- Projekt-Lebenszyklus-Features

## 6. Konsistenzregeln und -Herausforderungen

### **Das Konsistenz-Problem:**
Was passiert, wenn jemand manuell einen Embryo-Ordner manipuliert?
```
/projects/Haus/finance%/subdir/file.txt  ← Inkonsistenter Zustand!
```

### **Lösungsstrategien:**

#### **Option A: Strikte Validierung**
- Embryo-Ordner dürfen **nie** Inhalte haben
- Bei Erkennung: Sofortige Materialisierung oder Warnung

#### **Option B: Lazy Materialisierung**
- Embryo mit Inhalt wird bei nächstem Zugriff materialisiert
- Automatische Bereinigung von inkonsistenten Zuständen

#### **Option C: Benutzer-Intervention**
- Warnung und manuelle Entscheidung
- Dokumentation des Vorfalls

### **Empfehlung:**
Implementiere **Option B** mit Logging:
- Automatische Materialisierung bei inkonsistenten Zuständen
- Ausführliche Logs für Administratoren
- Optional: Benachrichtigung an Benutzer

## 7. Technische Entscheidungsmatrix

| Kriterium | `%`-Suffix | Extended Attributes | Permission Bits |
|-----------|------------|---------------------|-----------------|
| **Sichtbarkeit** | Hoch | Niedrig | Mittel |
| **Metadaten** | Keine | Strukturiert | Begrenzt |
| **Kompatibilität** | Sehr hoch | Mittel | Hoch |
| **Performance** | Mittel | Mittel | Sehr hoch |
| **Erweiterbarkeit** | Niedrig | Hoch | Niedrig |
| **Debugging** | Einfach | Schwierig | Mittel |

## 8. Empfohlene Vorgehensweise für neue Entwickler

1. **Verstehe das Konzept:** Embryo = potentieller Ordner, noch nicht real
2. **Beginne einfach:** Implementiere mit `%`-Suffix für Prototypen
3. **Plan für Evolution:** Architekturiere für spätere Migration zu xattr
4. **Denke an Lebenszyklen:** Marker können für mehr verwendet werden (essential/disposable)
5. **Handle Inkonsistenzen:** Entscheide, wie mit manuellen Manipulationen umgehen

## 9. Wichtige Code-Snippets für die Implementierung

### **Embryo-Erkennung:**
```python
import os
import stat
from pathlib import Path

def is_embryo_folder(path: Path) -> bool:
    """Erkennt einen Embryo-Ordner mit fallback-Mechanismus."""
    # 1. Extended Attribute (modern)
    try:
        if os.getxattr(path, "user.myos.embryo"):
            return True
    except (OSError, AttributeError):
        pass
    
    # 2. Sticky Bit (kompatibel)
    try:
        if os.stat(path).st_mode & stat.S_ISVTX:
            return True
    except OSError:
        pass
    
    # 3. Legacy %-Suffix (migration)
    if path.name.endswith("%"):
        return True
    
    return False
```

### **Materialisierung:**
```python
def materialize_embryo(path: Path) -> None:
    """Macht einen Embryo-Ordner zu einem echten Verzeichnis."""
    # Entferne alle Marker
    try:
        os.removexattr(path, "user.myos.embryo")
    except OSError:
        pass
    
    # Entferne Sticky Bit
    try:
        mode = os.stat(path).st_mode
        os.chmod(path, mode & ~stat.S_ISVTX)
    except OSError:
        pass
    
    # Logge die Materialisierung
    print(f"Materialized: {path}")
```

## 10. FAQ für neue Teammitglieder

### **Q: Warum nicht einfach bei `%` bleiben?**
A: `%` ist ein guter Start, aber limitiert. xattr erlaubt strukturierte Metadaten und ist unsichtbar für normale Benutzer.

### **Q: Was ist mit Windows?**
A: Extended Attributes funktionieren auf NTFS (via `win32api`), aber für maximale Kompatibilität benötigen wir einen Hybrid-Ansatz.

### **Q: Wie migrieren wir existierende Projekte?**
A: Automatisches Skript: Finde `%`-Ordner, entferne `%`, setze xattr/Sticky Bit.

### **Q: Was passiert bei Backup/Restore?**
A: Mit xattr: Prüfe ob Backup-Tool xattr erhält. Mit `%`: Funktioniert immer, aber Migration nach Restore nötig.

### **Q: Können Benutzer die Marker versehentlich löschen?**
A: Ja, deshalb: 1) Logge solche Ereignisse, 2) Stelle automatisch wieder her wenn möglich, 3) Dokumentiere klar.

---

**Letzte Aktualisierung:** 26. Januar 2024  
**Status:** Konzeptphase - wartet auf Implementierungsentscheidung  
**Entscheidungsträger:** Oliver & AI-Assistent  
**Nächster Schritt:** Pilot-Implementierung in Test-Umgebung