# Dokumentation: `my_project.py`

## Zweck und Rolle der Library
Die Library `my_project.py` bildet das **Projektkonfigurations-Herzstück** von MyOS. Sie verwaltet die lebenswichtigen `.project.cfg` Dateien, die jedes MyOS-Projekt identifizieren und konfigurieren. Diese Dateien definieren die Verbindung zwischen einem konkreten Projekt und seinen übergeordneten Templates (Lenses), ermöglichen die Blueprint-Funktionalität und speichern projektspezifische Metadaten. Ohne diese Library wüsste MyOS nicht, welche Projekte existieren oder welche Templates sie verwenden sollen.

## Klassen und ihre Methoden im Detail

### **1. Projektkonfiguration (`ProjectConfig`-Klasse)**
Eine `ProjectConfig`-Instanz repräsentiert die komplette Konfiguration eines einzelnen MyOS-Projekts. Sie kapselt den Zugriff auf die `.project.cfg` Datei und bietet eine bequeme Python-Schnittstelle.

#### **Initialisierung und automatischer Ladevorgang**
- **`__init__(path: Path)`**:  
  Konstruiert eine neue Projektkonfiguration für das angegebene Verzeichnis. Der `path` Parameter sollte auf das Projekt-Stammverzeichnis zeigen. Die Methode prüft sofort, ob eine `.project.cfg` Datei existiert und lädt sie automatisch, falls vorhanden. Diese "auto-load" Funktionalität stellt sicher, dass das Objekt nach der Instanziierung immer den aktuellen Zustand repräsentiert.

#### **Konfigurations-Lesen und -Schreiben**
- **`load() -> None`**:  
  Lädt die Konfiguration neu aus der physischen `.project.cfg` Datei. Die Methode parst das einfache Textformat zeilenweise: Ignoriert Leerzeilen und Kommentare (beginnend mit `#`), erkennt die MyOS-Versionszeile (beginnt mit "MyOS"), und extrahiert alle `key: value` Paare. Besondere Bedeutung haben die Schlüssel `template:` (verbindet Projekt mit Template) und `version:` (MyOS-Version). Alle anderen Schlüssel werden im `metadata`-Dictionary gespeichert.
  
- **`save(template: Optional[str] = None, version: str = "MyOS v0.1") -> None`**:  
  Schreibt die aktuelle Konfiguration in die `.project.cfg` Datei. Falls angegeben, aktualisiert sie zuerst `template` und/oder `version`. Die Methode stellt sicher, dass das Elternverzeichnis existiert (erstellt es nötigenfalls), und schreibt dann alle Konfigurationszeilen in der richtigen Reihenfolge: zuerst die Versionszeile, dann das Template, dann alle Metadaten-Schlüssel.

#### **Validierung und Statusabfrage**
- **`is_valid() -> bool`**:  
  Überprüft, ob dies ein **gültiges** MyOS-Projekt ist. Ein Projekt gilt als gültig, wenn **sowohl** die `.project.cfg` Datei physisch existiert **als auch** eine Versionsinformation (`self.version`) vorhanden ist. Diese doppelte Prüfung verhindert, dass beschädigte oder unvollständige Konfigurationen als valide Projekte erkannt werden.

### **2. Projekterkennung (`ProjectFinder`-Klasse)**
Eine statische Hilfsklasse, die keine Instanzen erzeugt, sondern rein funktionale Methoden bietet. Sie hilft bei der Navigation in der Verzeichnishierarchie, um MyOS-Projekte zu finden.

#### **Hierarchische Navigation**
- **`find_nearest(start_path: Path) -> Optional[Path]`** *(statisch)*:  
  Beginnt beim `start_path`-Verzeichnis und wandert rekursiv im Dateisystem **nach oben** (zu den Elternverzeichnissen), bis sie entweder ein Verzeichnis mit `.project.cfg` Datei findet oder das Dateisystem-Root erreicht. Diese "Aufwärtsnavigation" ist essentiell für kontext-sensitive Operationen - z.B. um von einem tief verschachtelten Unterordner das übergeordnete MyOS-Projekt zu identifizieren.

- **`is_project(path: Path) -> bool`** *(statisch)*:  
  Eine einfache Prüfung: Gibt `True` zurück, wenn das angegebene Verzeichnis eine `.project.cfg` Datei direkt enthält. Diese Methode wird typischerweise verwendet, nachdem `find_nearest` einen Kandidaten gefunden hat, oder um ein Verzeichnis explizit als MyOS-Projekt zu klassifizieren.

## Dateiformat: `.project.cfg` im Detail
```
MyOS v0.1              # Obligatorisch: MyOS-Versionskennung
template: standard     # Obligatorisch: Verweis auf Lens-Template
author: Max Mustermann # Optional: Benutzerdefinierte Metadaten
created: 2024-01-26    # Optional: Weitere Metadaten
tags: haus, bau       # Optional: Kommaseparierte Werte möglich
```

## Funktionsweise und Architektur
1. **Konfigurationslebenszyklus:** `ProjectConfig`-Objekte folgen einem "load-on-init, save-explicitly" Muster: Sie laden automatisch beim Erstellen, müssen aber explizit gespeichert werden.
2. **Projektidentifikation:** Die Kombination aus `find_nearest()` (bottom-up Suche) und `is_project()` (direkte Prüfung) ermöglicht flexible Projekt-Erkennung in verschiedenen Kontexten.
3. **Template-Bindungskette:** Das `template:` Feld in `.project.cfg` erzeugt die kritische Verbindung zwischen einem konkreten Projekt und dem abstrakten Lens-Template, das dessen Blueprint-Struktur definiert.

## Wichtige Hinweise und Erkenntnisse aus der Entwicklung

### **1. Dateiformat-Design Entscheidungen**
- **Problem:** Anfänglich hatten wir über komplexere Formate (JSON, YAML, INI-Sektionen) nachgedacht.
- **Lösung:** Das gewählte `key: value` Format ist **menschenlesbar, einfach zu parsen, und erweiterbar**. Es kann mit jedem Texteditor bearbeitet werden, erfordert keine speziellen Parser, und erlaubt trotzdem strukturierte Daten.
- **Versionszeile vs. version:** Die erste Zeile `MyOS v0.1` und das `version:` Feld könnten redundant erscheinen, aber die erste Zeile dient als "Magic Number" zur schnellen Dateiidentifikation.

### **2. Pfadbehandlung und absolute Referenzen**
- **Kritisch:** Alle Pfade werden mit `expanduser().absolute()` normalisiert. Dies verhindert Probleme mit relativen Pfaden, Home-Verzeichnis-Tilde (~), und symbolischen Links.
- **Eltern-Navigation-Trick:** Die Bedingung `while current != current.parent` ist ein eleganter Weg, um sicher am Filesystem-Root zu stoppen, ohne betriebssystemspezifische Pfadprüfungen.

### **3. Template-Bindung als kritische Abhängigkeit**
- **Warnung:** Ohne `template:` Feld funktioniert die gesamte Blueprint-Funktionalität **nicht**. Das Projekt würde keine Ghost-Folders anzeigen.
- **Robustheit:** Die `load()` Methode ist fehlertolerant - wenn das Template-Feld fehlt, wird `self.template` einfach `None`, und der Caller muss damit umgehen.

### **4. Validierung vs. bloße Existenz**
- **Wichtiger Unterschied:** `(path / ".project.cfg").exists()` prüft nur die Datei-Existenz, während `is_valid()` auch den **Inhalt** validiert. Ein leeres oder korruptes `.project.cfg` würde somit nicht als valides Projekt durchgehen.

## Erweiterungsmöglichkeiten und Roadmap

### **1. Dringend: Erweiterte Metadatentypen**
- **Aktuelle Einschränkung:** Alle Werte werden als Strings gespeichert.
- **Erweiterung:** Typisierte Metadaten mit automatischer Konvertierung:
  - Listen: `tags: finance,haus,bau` → `["finance", "haus", "bau"]`
  - Booleans: `archived: true` → `True`
  - Zahlen: `priority: 5` → `5`
  - Daten: `deadline: 2024-12-31` → `datetime.date(2024, 12, 31)`
- **Implementierung:** Optionales Schema-Definition oder Typ-Inferenz beim Laden.

### **2. Dringend: Template-Existenz-Validierung**
- **Problem:** Ein Projekt kann auf ein nicht-existierendes Template verweisen.
- **Lösung:** `is_valid()` könnte optional prüfen, ob das referenzierte Template im `templates_dir` existiert (wenn ein `templates_dir` Parameter bereitgestellt wird).
- **Vorteil:** Frühe Fehlererkennung bei falschen Template-Namen.

### **3. Mittelfristig: Projekt-Abhängigkeiten und Verweise**
- **Feature:** `depends_on:` Feld, das andere MyOS-Projekte referenzieren kann.
- **Use-Cases:** 
  - Projekt-Hierarchien (Master-Projekt mit Sub-Projekten)
  - Template-Vererbung (Projekt erweitert Basis-Projekt)
  - Ressourcen-Sharing zwischen Projekten
- **Implementierung:** Relative oder absolute Projekt-Pfade, evtl. mit UUID-basierten Referenzen.

### **4. Mittelfristig: Konfigurations-History und Versionierung**
- **Feature:** Automatische Versionierung von `.project.cfg` Änderungen.
- **Implementierung:** Git-ähnliches Diff-System oder einfache Backup-Kopien vor Änderungen.
- **Vorteil:** Rückgängigmachen von Konfigurationsänderungen, Audit-Trail.

### **5. Langfristig: Dynamische Konfigurations-Templates**
- **Aktuell:** Statische `key: value` Paare.
- **Erweiterung:** Template-Variablen und Ausdrücke in Werten:
  ```ini
  author: ${USERNAME}
  created: ${CURRENT_DATE}
  project_id: ${RANDOM_UUID}
  path: ${PROJECT_ROOT}/docs
  ```
- **Komplexität:** Benötigt Evaluierungs-Engine und Sandboxing für Sicherheit.

### **6. Langfristig: Externe Konfigurations-Quellen**
- **Feature:** `.project.cfg` könnte auf externe Konfigurationsdateien verweisen.
- **Beispiel:** `include: ../company-policies.cfg` oder `import: https://config.myos.com/standard.cfg`
- **Use-Case:** Zentrale Verwaltung von Projekt-Standards in Organisationen.

## Integration in das MyOS-Ökosystem
- **Blueprint-Funktionalität:** `_get_blueprint_folders()` in `myos_fuse.py` ruft `ProjectConfig` um das Template des Projekts zu ermitteln.
- **Projektkontext:** Viele FUSE-Operationen benötigen den Projektkontext, den `ProjectFinder` bereitstellt.
- **Template-System:** Die `template:` Verbindung ist das Bindeglied zwischen dem konkreten Projekt und der abstrakten Lens-Definition in `myos_vlp.py`.

## Wartungshinweise und Best Practices
- **Backward Compatibility:** Das `.project.cfg` Format muss extrem stabil bleiben. Änderungen sollten nur additive neue Features sein, nie brechende Änderungen an bestehenden Feldern.
- **Fehlerbehandlung Philosophie:** `load()` soll **niemals** das Programm zum Absturz bringen. Bei Parse-Fehlern sollte eine leere/partielle Konfiguration mit Warnlog zurückgegeben werden.
- **Performance-Überlegungen:** `find_nearest()` könnte bei sehr tiefen Verzeichnisbäumen (z.B. 20+ Ebenen) ineffizient sein. Caching oder Limitierung der Suchtiefe wären Optimierungsmöglichkeiten.
- **Thread-Safety:** Aktuell nicht thread-safe. Bei parallelen Zugriffen könnten Race Conditions bei gleichzeitigen Lese-/Schreiboperationen auftreten.

## Beziehungen zu anderen MyOS-Komponenten
```
my_project.py (Projektkonfiguration)
    │
    ├──▶ myos_fuse.py (wird für Blueprint-Folders verwendet)
    │    └── Benötigt ProjectConfig um Template-Namen zu lesen
    │
    └──▶ myos_vlp.py (wird für Template-Referenzierung verwendet)
         └── ProjectConfig.template referenziert LensTemplate.name
```

Die Library löst **zwei grundlegende Probleme elegant**:
1. **Konfigurationsverwaltung:** Einfache, robuste Persistenz von Projektmetadaten
2. **Projektnavigation:** Hilfreiche Tools um in komplexen Verzeichnisstrukturen MyOS-Projekte zu identifizieren

Sie ist **schlank, fokussiert und gut testbar** - genau was eine Utility-Library sein sollte.