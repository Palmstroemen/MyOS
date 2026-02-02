# Dokumentation: `myos_fuse.py`

## Zweck und Rolle der Library

Die `myos_fuse.py` Library ist die **Benutzeroberfläche und Brücke** zwischen dem MyOS-Konzept und der realen Welt. Sie implementiert ein **FUSE (Filesystem in Userspace)** Dateisystem, das alle virtuellen Konzepte von MyOS - Ghost-Folders, Blueprint-Verzeichnisse, Template-Projektionen - als echtes, navigierbares Dateisystem darstellt. Ohne diese Library wäre MyOS nur eine abstrakte Idee; mit ihr wird es zu einem konkreten Werkzeug, das jeder Benutzer sofort verstehen und verwenden kann.

Diese Datei ist die **größte und komplexeste** im MyOS-Ökosystem, weil sie:
1. Die komplette FUSE-API implementieren muss
2. Alle virtuellen Konzepte in Dateisystem-Operationen übersetzen muss
3. Zwischen physischer und virtueller Welt vermitteln muss
4. Fehler robust handhaben muss (Dateisystem-Fehler sind kritisch)

## Architektur und Aufbau

### **Globale Konfiguration und Konstanten**
- **`VIRTUAL_PROJECTS_ROOT` und `PHYSICAL_PROJECTS_ROOT`** (historisch, jetzt entfernt):  
  Diese Konstanten zeigten das **ursprüngliche Designproblem** - eine harte Kopplung zwischen virtuellem und physischem Layout. Ihre Entfernung markiert einen wichtigen Reifegrad des Systems.

### **1. MyOSFUSE Klasse - Das Herz des FUSE-Systems**

Die `MyOSFUSE` Klasse erbt von `Operations` (aus der `fuse` Bibliothek) und implementiert **alle benötigten Dateisystem-Operationen**. Jede Methode entspricht einem Systemaufruf, den das Betriebssystem an das Dateisystem stellt.

#### **Initialisierung und Dependency Injection**
- **`__init__(self, engine: LensEngine, projects_dir_name: str = "projects")`**:  
  Initialisiert das FUSE-System mit allen Abhängigkeiten. Der `LensEngine` wird injiziert, was die Klasse testbar und flexibel macht. Der `projects_dir_name` Parameter löst das Hardcoding-Problem - jetzt kann der Benutzer wählen, wie das Projekte-Verzeichnis heißt.

#### **Pfadverarbeitung und -auflösung**

##### **`_parse_virtual_path(virtual_path: str) -> Dict[str, Any]`**
Die **wichtigste Hilfsmethode** der gesamten Library. Sie analysiert jeden FUSE-Pfad und bestimmt:
- Ist dies der Root (`/`)?
- Ist dies das Projekte-Verzeichnis?
- Ist dies ein Pfad innerhalb eines Projekts?
- Enthält der Pfad `.blueprint` (virtuelles Blueprint-Verzeichnis)?
- Welches Projekt und welcher relative Pfad steckt dahinter?

**Beispiel-Transformationen:**
- `/` → `{'is_root': True, 'is_projects': False, ...}`
- `/Projekte` → `{'is_root': False, 'is_projects': True, 'project_name': None, ...}`
- `/Projekte/Haus/finance%` → `{'is_root': False, 'is_projects': True, 'project_name': 'Haus', 'relative_path': 'finance%', ...}`
- `/Projekte/Haus/.blueprint/finance` → `{'is_root': False, 'is_projects': True, 'project_name': 'Haus', 'is_blueprint': True, 'blueprint_relative': 'finance', ...}`

##### **`_resolve_to_physical(virtual_path: str, materialize: bool = False) -> Optional[Path]`**
Wandelt virtuelle Pfade in physische Pfade um. Der `materialize` Parameter ist kritisch:
- `False` (default): Nur auflösen, keine Verzeichnisse erstellen (für Leseoperationen)
- `True`: Verzeichnisse bei Bedarf erstellen (für Schreiboperationen)

**Besondere Logik für %-Pfade:**  
Wenn ein Pfad `%` enthält, prüft die Methode zuerst, ob der materialisierte Pfad bereits existiert. Falls ja, wird er zurückgegeben. Falls nein, wird `None` zurückgegeben (außer bei `materialize=True`). Diese Logik ermöglicht die "lazy materialization" - Ghost-Folders existieren virtuell, bis jemand tatsächlich etwas darin speichern will.

##### **`_get_blueprint_folders(project_name: str) -> List[str]`**
Ermittelt, welche Ghost-Folders für ein Projekt verfügbar sind, basierend auf dessen Template. Diese Methode ist die **Verbindung** zwischen Projektkonfiguration und Template-Struktur.

**Ablauf:**
1. Finde Projektverzeichnis
2. Lese `.project.cfg`
3. Extrahiere `template:` Wert
4. Scanne Template-Verzeichnis nach Unterordnern
5. Gib Liste der Ordnernamen zurück (ohne `%`)

#### **FUSE Kernoperationen - Die Dateisystem-API**

##### **`getattr(path: str, fh: Optional[Any] = None) -> Dict[str, Any]`**
**Die meistaufgerufene Methode.** Wird für **jeden** Dateisystemzugriff aufgerufen, um Dateiattribute zu ermitteln. Muss entscheiden:
- Ist dies ein virtuelles Verzeichnis (Root, Projekte, .blueprint, Ghost-Folder)?
- Ist dies ein physisches Objekt?
- Falls weder noch: `ENOENT` (Datei nicht gefunden) werfen

**Besondere Herausforderung:** Muss für **nicht-existierende Dateien in Ghost-Folders** `ENOENT` zurückgeben, damit `create()` aufgerufen werden kann. Aber für **existierende Dateien in materialisierten Ghost-Folders** muss die korrekte Statistik zurückgeben.

##### **`readdir(path: str, fh: Optional[Any] = None) -> List[str]`**
Listet Verzeichnisinhalte auf. Die **komplexeste Methode** nach `getattr`, weil sie virtuelle und physische Einträge kombinieren muss.

**Logik-Layers:**
1. **Basis:** Immer `["." , ".."]`
2. **Root:** Füge `projects_dir_name` hinzu
3. **Projekte-Verzeichnis:** Liste physische Projekte
4. **Normale Verzeichnisse:** Liste physische Dateien + virtuelle Einträge
5. **Projekt-Inhalte:** Füge `.blueprint` + Ghost-Folders (`folder%`) hinzu

**Ghost-Folder-Deduplizierung:**  
Prüft für jeden Ghost-Folder, ob er bereits materialisiert wurde. Falls ja: Zeige `folder` (ohne `%`). Falls nein: Zeige `folder%`. Verhindert Doppelauflistungen.

##### **Datei-IO Operationen**
- **`read(path: str, size: int, offset: int, fh: Any) -> bytes`**: Liest Dateiinhalt
- **`write(path: str, data: bytes, offset: int, fh: Any) -> int`**: Schreibt Dateiinhalt
- **`create(path: str, mode: int, fi: Optional[Any] = None) -> int`**: Erstellt neue Datei
- **`release(path: str, fh: Any)`**: Schließt Datei

**Besonderheit bei `create()`:** Ruft `materializer.materialize()` auf, was Ghost-Folders automatisch materialisiert. Dies ist der **kritische Punkt** wo virtuelle Konzepte physische Realität werden.

##### **Verzeichnisoperationen**
- **`mkdir(path: str, mode: int)`**: Erstellt Verzeichnis
- **`access(path: str, mode: int)`**: Prüft Zugriffsrechte

#### **Unterstützende Operationen**
- **`statfs(path: str) -> Dict[str, Any]`**: Gibt Dateisystem-Statistiken zurück (fest kodierte Werte)
- **`access(path: str, mode: int)`**: Prüft Zugriffsberechtigungen

### **2. mount_fuse() Funktion - Der System-Einstiegspunkt**

Eine bequeme Wrapper-Funktion, die alles für den Mount-Vorgang vorbereitet:

**Ablauf:**
1. Setze Default-Pfade (wenn nicht angegeben)
2. Erstelle benötigte Verzeichnisse
3. Initialisiere `PlateManager`, `LensEngine`, `MyOSFUSE`
4. Starte FUSE mit `FUSE(fuse, str(mount_point), ...)`

**CLI-Integration:** Wird von `argparse` aufgerufen, ermöglicht konfigurierbare Mount-Punkte, Template-Verzeichnisse, etc.

### **3. Kommandozeilen-Schnittstelle**

Die `if __name__ == "__main__"` Sektion verwandelt das Skript in ein ausführbares Programm mit Argumenten:
- `--plate`: Plate-Verzeichnis
- `--mount`: Mount-Punkt
- `--templates`: Template-Verzeichnis
- `--projects-dir`: Name des virtuellen Projekte-Verzeichnisses
- `--background`: Als Hintergrundprozess laufen

## Funktionsweise im Detail: Der virtuelle Dateisystem-Lebenszyklus

### **Beispiel: Benutzer erstellt Datei in Ghost-Folder**

1. **Benutzer:** `touch /mnt/Projekte/Haus/finance%/budget.txt`
2. **Kernel:** Ruft FUSE `getattr()` auf
3. **`getattr`:** Pfad enthält `%`, materialisierter Pfad existiert noch nicht → `ENOENT`
4. **Kernel:** Da `ENOENT`, ruft `create()` auf
5. **`create`:** Ruft `materializer.materialize("/Projekte/Haus/finance%/budget.txt")` auf
6. **`Materializer`:** Erstellt `/plate/Projekte/Haus/finance/` Verzeichnis
7. **`create`:** Erstellt Datei `/plate/Projekte/Haus/finance/budget.txt`
8. **Kernel:** Ruft `getattr()` erneut auf
9. **`getattr`:** Pfad enthält `%`, materialisierter Pfad existiert jetzt → gibt Stats zurück
10. **Benutzer:** Datei erscheint erfolgreich erstellt

### **Beispiel: Benutzer listet Projekt auf**

1. **Benutzer:** `ls -la /mnt/Projekte/Haus/`
2. **Kernel:** Ruft FUSE `readdir()` auf
3. **`readdir`:** 
   - Liest physische Dateien: `[".", "..", "existing.txt"]`
   - Fügt virtuelle Einträge hinzu: `[".blueprint", "finance%", "team%"]`
   - Prüft für `finance%`: Ist `/plate/Projekte/Haus/finance` materialisiert? Nein → Behalte `%`
4. **Benutzer:** Sieht Mischung aus physischen und virtuellen Einträgen

## Wichtige Hinweise und Kritische Design-Entscheidungen

### **1. Die Herausforderung der "gemischten Realität"**

**Problem:** Ein Dateisystem muss konsistent sein. Wenn wir sagen "diese Datei existiert", muss sie bei der nächsten Abfrage immer noch existieren. Aber wir haben **drei Arten von Existenz**:
1. **Physisch real:** Dateien auf dem Plate
2. **Virtuell permanent:** `.blueprint` Verzeichnisse
3. **Virtuell transient:** Ghost-Folders (können materialisiert werden)

**Lösung:** Jeder Pfadtyp hat spezifische Regeln:
- `.blueprint/`: Immer virtuell, nie physisch
- `folder%/`: Virtuell bis zur ersten Schreiboperation, dann physisch
- Alles andere: Rein physisch

### **2. Performance-Überlegungen bei `getattr()`**

**Herausforderung:** `getattr()` wird extrem häufig aufgerufen - für jeden `ls`, jeden Tab-Completion, jeden GUI-Filemanager-Aufruf.

**Optimierungen in unserem Code:**
- `_parse_virtual_path()`: Schnelle String-Operationen, kein Dateisystem-Zugriff
- `_resolve_to_physical()`: Verwendet gecachte `materializer.resolve()` für `%`-Pfade
- Frühzeitige Returns für spezielle Pfade (Root, Projekte, .blueprint)

**Potentielle Probleme:** `_get_blueprint_folders()` liest `.project.cfg` und scanned Template-Verzeichnis. Bei vielen Projekten/Templates könnte dies langsam sein.

### **3. Die %-Erkennungslogik ist fragil**

**Aktuelle Implementierung:** `if '%' in parsed['relative_path']:`

**Probleme:**
1. Was wenn jemand eine Datei `test%.txt` nennt? (Falsch-positiv)
2. Was wenn `%` in anderen Kontexten vorkommt?
3. Was mit Unicode/UTF-8?

**Verbesserungsmöglichkeit:** Striktere Prüfung: `if parts and parts[-1].endswith('%'):` (nur letzte Komponente)

### **4. Fehlerbehandlung und Robustheit**

**Philosophie:** FUSE-Operationen dürfen **niemals** Python-Exceptions nach außen werfen. Immer `FuseOSError` mit passendem errno.

**Implementierung:** Jede öffentliche Methode hat try/except Blöcke, die OSErrors in FuseOSErrors umwandeln.

**Besondere Herausforderung:** `getattr()` für nicht-existierende Dateien muss `ENOENT` werfen, aber Python's `os.lstat()` wirft bereits `OSError`. Wir fangen dies und konvertieren es.

### **5. Thread-Safety und parallele Zugriffe**

**Aktueller Status:** Nicht thread-safe dokumentiert.

**Problem:** Zwei Prozesse könnten gleichzeitig:
1. `getattr()` für `finance%/file.txt` aufrufen (beide erhalten `ENOENT`)
2. `create()` für denselben Pfad aufrufen
3. Beide versuchen, das Verzeichnis zu erstellen (Race Condition)

**Lösungsansatz:** Locking in `materializer.materialize()` oder atomare Operationen.

## Erweiterungsmöglichkeiten und Evolution

### **1. Dringend: Thread-Safety implementieren**

**Problem:** Wie oben beschrieben, Race Conditions bei parallelen Zugriffen.

**Lösungsvorschläge:**
1. **Einfach:** `threading.Lock()` in `Materializer._create_folder_if_needed()`
2. **Robust:** Dateisystem-level Locking mit `fcntl` oder `os.open()` mit exklusiven Flags
3. **Elegant:** Optimistisches Locking mit UUID-basierten temporären Dateien

**Empfehlung:** Beginnen mit einfachem Thread-Lock, später zu Dateisystem-Locks migrieren.

### **2. Dringend: Performance-Optimierung durch Caching**

**Problem:** `_get_blueprint_folders()` wird für jedes Projekt bei jedem `readdir()` neu aufgerufen.

**Caching-Strategien:**
1. **In-Memory Cache:** Dictionary `{project_name: blueprint_folders}` mit Timeout
2. **File Watcher:** Beobachten von `.project.cfg` Änderungen, Cache invalidierten
3. **Lazy + Cache:** Beim ersten Aufruf cachen, bei Änderungen neu laden

**Implementierung:** Decorator-Pattern um `_get_blueprint_folders()` mit `functools.lru_cache`

### **3. Dringend: Bessere %-Erkennung und -Handling**

**Probleme:** Wie oben beschrieben.

**Lösung:** Striktere, aber flexiblere Erkennung:
```python
def _is_ghost_component(self, component: str) -> bool:
    """Prüft ob eine Pfadkomponente ein Ghost-Folder ist."""
    # Nur komplette Komponenten die mit % enden
    if not component.endswith('%'):
        return False
    # Mindestens ein Zeichen vor dem %
    if len(component) < 2:
        return False
    # Kein % irgendwo sonst in der Komponente
    if component.count('%') != 1:
        return False
    return True
```

### **4. Mittelfristig: Erweiterte virtuelle Dateien**

**Aktuell:** Nur virtuelle Verzeichnisse.

**Erweiterung:** Virtuelle Dateien, z.B.:
- `.blueprint/README.md`: Automatisch generierte Dokumentation
- `%stats.json`: Projektstatistiken als virtuelle JSON-Datei
- `.myos/config`: Konfiguration als virtuelle Datei

**Implementierung:** Neue Methoden oder erweiterte `getattr()`/`read()` Logik.

### **5. Mittelfristig: Symbolische Links und Aliase**

**Feature:** Virtuelle symbolische Links zwischen Projekten oder Templates.

**Beispiele:**
- `Haus/finance%` → symbolischer Link zu `Garten/finance%` (gleiches Template)
- `.blueprint/standard` → Link zu tatsächlichem Template-Verzeichnis

**Herausforderung:** FUSE muss `readlink()` implementieren.

### **6. Langfristig: Transaktionale Operationen**

**Problem:** Wenn Materialisierung fehlschlägt (z.B. Disk voll), bleibt System in inkonsistentem Zustand.

**Feature:** Atomare Operationen mit Rollback.

**Beispiel:** `create()` in `finance%/budget.txt`:
1. Starte Transaktion
2. Erstelle `finance/` Verzeichnis
3. Erstelle `budget.txt` Datei
4. Commit Transaktion
5. Bei Fehler: Rollback (lösche alles)

**Implementierung:** Journaling oder Copy-on-Write mit finalem Move.

### **7. Langfristig: Erweiterte Dateisystem-Features**

- **Extended Attributes (xattr):** Speichern von MyOS-Metadaten in Dateien
- **Access Control Lists (ACL):** Fein-granulare Berechtigungen
- **File Watching (inotify):** Benachrichtigungen bei Änderungen in virtuellen Verzeichnissen

## Integration und Abhängigkeiten

```
Kernel / Userspace
        ↓
    FUSE Library
        ↓
    myos_fuse.py
        ↓
    myos_vlp.py (LensEngine)
    ↗          ↖
my_materializer.py  my_project.py
```

**Kritische Abhängigkeiten:**
1. **fuse-py:** Die Python FUSE-Bindung. Aktuell stabil, aber könnte veraltet sein.
2. **Kernel FUSE:** Muss auf dem System verfügbar und aktiviert sein.
3. **Python 3.7+:** Für type hints und pathlib Features.

## Wartungshinweise und Betrieb

### **1. Debugging ist schwierig aber möglich**

**Herausforderung:** FUSE läuft als Daemon, Fehler sind schwer zu sehen.

**Debugging-Strategien:**
1. **Foreground-Modus:** `--foreground` in FUSE-Optionen
2. **Ausführliches Logging:** Debug-Ausgaben wie in unserem Code
3. **Strace:** `strace -f -e trace=file python3 myos_fuse.py ...`
4. **FUSE Debug:** `-d` oder `--debug` Option an FUSE

### **2. Memory Leaks vermeiden**

**Risiko:** FUSE-Daemon läuft lange, kleine Leaks werden groß.

**Besondere Aufmerksamkeit:**
- `materialized` Cache in `Materializer` wächst unbegrenzt
- Keine großen Objekte in Instanzvariablen cachen
- Regelmäßige Cleanup-Routinen für temporäre Daten

### **3. Umount-Probleme**

**Häufiges Problem:** FUSE hängt bei `fusermount -u`.

**Ursachen:**
- Offene Dateihandles
- Aktive Operationen
- Deadlocks in unserem Code

**Lösungen:**
1. **Graceful Shutdown:** Signal-Handler für SIGTERM
2. **Timeout bei Operationen:** Lange blockierende Operationen vermeiden
3. **Resource Tracking:** Offene Handles zählen und schließen

### **4. Performance-Monitoring**

**Zu überwachende Metriken:**
- `getattr()` Aufrufe pro Sekunde
- `readdir()` Latenz
- Materialisierungs-Operationen
- Cache-Hit-Rates

**Tools:**
- `fuse-stats` oder `/proc/fs/fuse/`
- Custom Metrics in unserem Code

## Fazit

Die `myos_fuse.py` Library ist ein **beeindruckend komplexes Stück Software**, das abstrakte Konzepte in konkrete, nutzbare Funktionalität übersetzt. Sie zeigt mehrere fortgeschrittene Python-Techniken:

1. **Komplexe Pfadverarbeitung** mit Zustandsautomaten-ähnlicher Logik
2. **Bridge-Pattern** zwischen virtueller und physischer Welt
3. **Robuste Fehlerbehandlung** in einem kritischen System (Dateisystem)
4. **Dependency Injection** für Testbarkeit und Flexibilität

Die Hauptherausforderungen für die Zukunft sind:
1. **Thread-Safety** für Produktionseinsatz
2. **Performance-Optimierung** bei vielen Projekten/Ghost-Folders
3. **Erweiterte Dateisystem-Features** für professionellen Einsatz

Trotz ihrer Komplexität ist die Library **gut strukturiert und wartbar** - jede Methode hat eine klare Verantwortung, und die Hilfsmethoden trennen Concerns effektiv. Sie bildet eine solide Basis für die Weiterentwicklung von MyOS.