# Dokumentation: `myos_vlp.py`

## Zweck und Rolle der Library

Die Library `myos_vlp.py` implementiert das **kernarchitektonische Konzept** von MyOS: das **View/Lens/Plate (VLP) Modell**. Diese Architektur trennt die drei fundamentalen Aspekte des Systems sauber voneinander:

1. **View:** Was der Benutzer sieht (virtuelle Struktur, Ghost-Folders, Blueprints) - implementiert in `myos_fuse.py`
2. **Lens:** Wie der Benutzer es sieht (Templates, Transformationsregeln, Projektionen) - implementiert hier als `LensTemplate`
3. **Plate:** Wo die Daten physisch gespeichert sind (Dateisystem, Speicherhierarchie) - implementiert hier als `PlateManager`

Diese Library ist somit das **technische Herzstück**, das die abstrakten Konzepte in konkrete, arbeitende Python-Klassen übersetzt. Sie definiert die Datenmodelle und deren Beziehungen, auf denen das gesamte MyOS-System aufbaut.

## Klassen und ihre Methoden im Detail

### **1. PlateManager - Die physische Speicherschicht**

Der `PlateManager` ist verantwortlich für alles, was mit **physischer Datenspeicherung** zu tun hat. Er abstrahiert das zugrunde liegende Dateisystem und bietet eine einheitliche Schnittstelle für Dateioperationen, unabhängig davon, wo die Daten tatsächlich gespeichert sind.

#### **Initialisierung und Pfadverwaltung**
- **`__init__(root=None)`**:  
  Erstellt einen neuen PlateManager mit einem gegebenen Root-Verzeichnis. Akzeptiert `None` (Standard: `~/myos_plates`), `str`, oder `Path`. Die Methode stellt sicher, dass das Root-Verzeichnis existiert (erstellt es nötigenfalls mit `mkdir(parents=True, exist_ok=True)`). Dieser "auto-create" Ansatz folgt dem Prinzip "fail early, create if missing".

#### **Pfadkonvertierung und -auflösung**
- **`physical_path(virtual_path: str = "") -> Path`**:  
  Die **zentrale Methode** des PlateManagers. Konvertiert einen virtuellen Pfad (wie ihn FUSE sieht) in einen physischen Pfad (wie er auf dem Dateisystem existiert). Handelt spezielle Fälle: Leerer String oder "." gibt das Root zurück, führende Schrägstriche werden entfernt. Diese Normalisierung ist entscheidend für konsistente Pfadbehandlung.

- **`exists(virtual_path: str = "") -> bool`**:  
  Prüft, ob ein virtueller Pfad physisch existiert. Ein einfacher Wrapper um `physical_path().exists()`, der aber die semantische Trennung zwischen virtueller und physischer Existenz klar macht.

#### **Dateisystemoperationen**
- **`materialize(virtual_path: str) -> Path`**:  
  Erstellt die physische Struktur für einen virtuellen Pfad. Bei Dateien (mit Extension) wird eine leere Datei erstellt (`touch()`), bei Verzeichnissen wird die Verzeichnisstruktur angelegt. Der Name "materialize" ist bewusst gewählt - er spiegelt den Übergang von virtueller zu physischer Existenz wider.

- **`list_dir(virtual_path: str = "") -> List[str]`**:  
  Listet den Inhalt eines virtuellen Verzeichnisses auf. Gibt eine einfache Liste von Datei- und Verzeichnisnamen zurück (ohne volle Pfade). Diese Reduktion auf Namen ist intentional - sie zwingt den Aufrufer, bei Bedarf `physical_path()` für vollständige Pfade aufzurufen.

### **2. LensTemplate - Die Transformationsschicht**

Ein `LensTemplate` definiert, **wie** ein Projekt "aussieht" - welche virtuellen Ordnerstrukturen (Ghost-Folders) es anbietet, bevor sie materialisiert werden. Es ist im Wesentlichen eine strukturierte Beschreibung der möglichen Projektorganisation.

#### **Initialisierung und automatisches Scanning**
- **`__init__(name: str, path: Path, ghost_tree: Dict[str, List[str]] = field(default_factory=dict))`**:  
  Erstellt ein neues LensTemplate. Der `ghost_tree` Parameter ist optional - wenn nicht angegeben, wird automatisch das Template-Verzeichnis gescannt (`_scan_template()`). Diese Lazy-Initialisierung ermöglicht sowohl manuelle Definition von Templates als auch automatische Generierung aus Verzeichnisstrukturen.

- **`_scan_template() -> Dict[str, List[str]]`** *(private)*:  
  Scannt das Template-Verzeichnis **rekursiv** und erstellt eine Baumstruktur aller Unterverzeichnisse (ignoriert versteckte Ordner die mit '.' beginnen). Die rekursive Natur dieser Methode ermöglicht beliebig tief verschachtelte Template-Strukturen.

#### **Ghost-Folder-Abfrage**
- **`ghosts_at(current_path: str = "") -> List[str]`**:  
  Gibt die Ghost-Folders für einen gegebenen Pfad innerhalb des Templates zurück. Navigiert durch die `ghost_tree`-Struktur basierend auf `current_path` und gibt alle Kindelemente mit `%`-Suffix zurück. Diese Methode ist essentiell für die dynamische Generierung von Ghost-Folders in Abhängigkeit der aktuellen Position im Verzeichnisbaum.

### **3. ProjectConfig - Die Projektkonfiguration (Wiederverwendung)**

Diese Klasse wird auch in `my_project.py` definiert (duplikativer Code). Sie repräsentiert die `.project.cfg` Datei und deren Inhalt. Die Duplizierung ist ein Design-Problem, das gelöst werden sollte (siehe Erweiterungsmöglichkeiten).

### **4. LensEngine - Die zentrale Steuerungseinheit**

Der `LensEngine` ist der **Orchestrator**, der Plate, Templates und ProjectConfig zusammenbringt. Er initialisiert alle Komponenten, verwaltet den Template-Cache, und bietet High-Level-APIs für das Gesamtsystem.

#### **Initialisierung und Template-Loading**
- **`__init__(plate: PlateManager, templates_dir=None)`**:  
  Erstellt einen neuen LensEngine mit einem gegebenen PlateManager. Lädt automatisch alle verfügbaren Templates aus `templates_dir` (Standard: `~/.myos/lenses`). Die Abhängigkeitsinjektion (`plate` als Parameter) macht den Engine testbar und flexibel.

- **`_load_templates()`**:  
  Scant das Templates-Verzeichnis und lädt jedes Unterverzeichnis als `LensTemplate`. Fehler beim Laden eines einzelnen Templates werden abgefangen und gewarnt, aber stoppen nicht den gesamten Prozess. Diese Robustheit ist wichtig für Systeme mit gemischten/malformierten Templates.

#### **Projektvalidierung**
- **`is_project(project_name: str) -> bool`**:  
  Prüft, ob ein Verzeichnis ein gültiges MyOS-Projekt ist, indem es nach der `.project.cfg` Datei sucht. Diese Methode delegiert im Wesentlichen an `ProjectConfig.is_valid()`, bietet aber eine bequemere API auf Engine-Level.

## Architektur und Datenfluss

```
Benutzeraktion (FUSE)
    ↓
myos_fuse.py (View)
    ↓ Fragt ab / transformiert
myos_vlp.py (LensEngine)
    ├── PlateManager (physischer Zugriff)
    ├── LensTemplate (strukturelle Information)
    └── ProjectConfig (Projektmetadaten)
    ↓
Dateisystem (Plate)
```

Der kritische Datenfluss bei der Blueprint-Erstellung:
1. FUSE erhält Pfad `/projects/Haus/finance%`
2. Ruft `_get_blueprint_folders("Haus")` in `myos_fuse.py`
3. Diese Methode verwendet `ProjectConfig` um Template-Name zu lesen
4. Fragt `LensEngine` nach dem `LensTemplate` "standard"
5. `LensTemplate.ghosts_at()` gibt verfügbare Ghost-Folders zurück
6. FUSE zeigt `finance%` als virtuellen Ordner an

## Wichtige Hinweise und Design-Entscheidungen

### **1. Architekturtrennung als oberstes Prinzip**
- **Entscheidung:** Strikte Trennung von View, Lens und Plate auch im Code
- **Vorteil:** Jede Schicht kann unabhängig getestet, erweitert oder ausgetauscht werden
- **Beispiel:** Man könnte den `PlateManager` durch eine Cloud-Speicher-Implementierung ersetzen, ohne `LensTemplate` oder FUSE-Layer zu ändern

### **2. Das Duplizierungsproblem von ProjectConfig**
- **Problem:** `ProjectConfig` existiert sowohl hier als auch in `my_project.py`
- **Ursache:** Vermutlich evolutionäres Wachstum - beide Module brauchten die Funktionalität
- **Lösungsrichtung:** `ProjectConfig` in ein eigenes Modul auslagern und von beiden importieren

### **3. Rekursive vs. flache Template-Strukturen**
- **Implementierung:** `_scan_template()` ist rekursiv, ermöglicht beliebig tiefe Strukturen
- **Use-Case:** Komplexe Projektvorlagen mit Sub-Sub-Verzeichnissen
- **Performance:** Rekursion könnte bei sehr tiefen Bäumen problematisch sein (Stack-Tiefe)

### **4. Fehlertoleranz im Template-Loading**
- **Entscheidung:** Einzelne fehlerhafte Templates verhindern nicht das Laden anderer
- **Implementierung:** Try/Except um jedes Template, Warnung bei Fehlern
- **Trade-off:** System startet auch mit teilweise kaputten Templates, aber Benutzer muss Fehler selbst entdecken

### **5. Pfadnormalisierungskonsistenz**
- **Pattern:** Alle öffentlichen Methoden akzeptieren `virtual_path` als String
- **Normalisierung:** Immer absolute Pfade zurückgeben, relative Pfade relativ zum Root
- **Konsistenz:** `physical_path("") == physical_path(".") == root` - vermeidet Mehrdeutigkeiten

## Erweiterungsmöglichkeiten und Evolution

### **1. Dringend: ProjectConfig-Duplizierung beheben**
- **Problem:** Code-Duplikation zwischen `myos_vlp.py` und `my_project.py`
- **Lösung:** Gemeinsame Basisklasse in eigenem Modul (`myos_project_config.py`)
- **Implementierung:**
  ```python
  # myos_project_config.py
  class BaseProjectConfig:
      # gemeinsame Logik hier
  
  # my_project.py und myos_vlp.py
  from myos_project_config import BaseProjectConfig
  
  class ProjectConfig(BaseProjectConfig):
      # modulspezifische Erweiterungen
  ```

### **2. Dringend: Template-Caching mit Invalidation**
- **Aktuell:** Templates werden beim Start geladen, dann statisch gehalten
- **Problem:** Änderungen an Templates erfordern Neustart von MyOS
- **Lösung:** File-Watcher der Template-Änderungen erkennt und Cache invalidiert
- **Implementierung:** `watchdog` Bibliothek oder periodisches Re-Scanning

### **3. Mittelfristig: Template-Vererbung und Komposition**
- **Feature:** Templates können von anderen Templates erben oder kombinieren
- **Use-Case:** `standard` Template erbt von `base`, `finance-project` kombiniert `standard` mit `finance-specific`
- **Syntax in .project.cfg:** `template: standard+finance` oder `inherits: base`
- **Komplexität:** Auflösung von Konflikten bei überschneidenden Ordnerstrukturen

### **4. Mittelfristig: Dynamische Template-Generierung**
- **Aktuell:** Statische Verzeichnisstrukturen als Templates
- **Erweiterung:** Templates können durch Skripte/Plugins generiert werden
- **Beispiel:** `dynamic_project` Template das Ordner basierend auf aktuellen Dateien im Projekt erzeugt
- **Architektur:** Plugin-System mit `TemplateGenerator` Interface

### **5. Langfristig: Multi-Plate-Unterstützung**
- **Feature:** Ein MyOS kann auf mehrere Plates zugreifen (lokale + Cloud + Netzwerk)
- **Implementierung:** `PlateManager` wird zu abstrakter Klasse, konkrete Implementierungen für verschiedene Backends
- **Use-Case:** Projekte können über Storage-Grenzen hinweg organisiert werden

### **6. Langfristig: Template-Versionierung und Migration**
- **Problem:** Templates entwickeln sich weiter, bestehende Projekte müssen migriert werden
- **Feature:** Jedes Template hat eine Version, Migrationsskripte für Upgrades
- **Beispiel:** Projekt mit Template `standard:v1` kann zu `standard:v2` migriert werden
- **Komplexität:** Automatische oder manuelle Migration von existierenden Dateistrukturen

### **7. Langfristig: Template-Parametrisierung**
- **Feature:** Templates mit Parametern, die bei Projekt-Erstellung angegeben werden
- **Beispiel:** `web-project` Template mit Parametern `framework: django|flask|fastapi`, `db: postgres|mysql`
- **Implementierung:** Template-Definition in strukturierter Datei (YAML/JSON) statt reinem Verzeichnis

## Integration und Abhängigkeiten

Die `myos_vlp.py` Library hat eine **zentrale Position** im MyOS-Ökosystem:

```
       myos_fuse.py (Consumer)
             ↑
       myos_vlp.py (Provider)
        ↗    ↑    ↖
my_materializer.py  my_project.py (Collaborators)
```

- **Primärer Consumer:** `myos_fuse.py` verwendet `LensEngine` für alle Template-bezogenen Operationen
- **Kollaboratoren:** `my_materializer.py` und `my_project.py` ergänzen die Funktionalität, sind aber technisch unabhängig
- **Externe Abhängigkeiten:** Nur Standard-Python-Bibliotheken (`pathlib`, `os`, `dataclasses`)

## Wartungshinweise und Kritische Aspekte

### **1. Die "doppelte" ProjectConfig ist ein Architekturfehler**
- **Priorität:** Hoch - technische Schuld die bezahlt werden sollte
- **Risiko:** Inkonsistenzen zwischen den beiden Implementierungen
- **Migrationsplan:** 1. Gemeinsame Basis extrahieren, 2. Alte Klassen als Wrapper, 3. Deprecate, 4. Entfernen

### **2. Template-Scanning ist potentiell langsam**
- **Bei:** Sehr großen Template-Verzeichnissen (1000+ Dateien/Ordner)
- **Monitoring:** Ladezeiten beim Start messen
- **Optimierung:** Lazy-Loading (nur bei erstem Zugriff scannen), Caching der Scan-Ergebnisse

### **3. Fehlerbehandlung ist zu tolerant**
- **Problem:** Fehler in einzelnen Templates werden nur gewarnt, nicht verhindert
- **Risiko:** Benutzer merkt nicht, dass ein Template nicht richtig geladen wurde
- **Balance:** Zwischen Robustheit (System startet immer) und Korrektheit (Fehler sofort erkennen)

### **4. Thread-Safety nicht garantiert**
- **Aktuell:** Keine Synchronisation bei gleichzeitigen Zugriffen
- **Risiko:** Bei parallelen FUSE-Operationen könnten Race Conditions auftreten
- **Lösung:** `threading.RLock()` für Template-Cache oder immutable Datenstrukturen

### **5. Testbarkeit gut, aber Verbesserungspotential**
- **Stärke:** `PlateManager` kann mit Temp-Verzeichnissen getestet werden
- **Schwäche:** `LensEngine` hat reale Dateisystem-Abhängigkeiten
- **Verbesserung:** Mehr Dependency Injection, Dateisystem-Interface abstrahieren

## Fazit

Die `myos_vlp.py` Library ist **gut strukturiert** und implementiert die Kernarchitektur von MyOS effektiv. Sie zeigt eine klare Trennung der Verantwortlichkeiten und bietet flexible Erweiterungspunkte. Die Hauptprobleme (ProjectConfig-Duplizierung, fehlende Template-Cache-Invalidation) sind bekannt und lösbar.

Die Architektur ermöglicht es, dass MyOS von einem einfachen "Ghost-Folder mit Templates" System zu einem komplexen "Projektverwaltungsframework" wachsen kann, ohne fundamentale Änderungen am Kerncode.