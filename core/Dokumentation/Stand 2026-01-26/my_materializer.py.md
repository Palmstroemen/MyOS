# Dokumentation: `my_materializer.py`

## Zweck der Library
Die Library `my_materializer.py` implementiert die **Materialisierung** von virtuellen Ordnern mit `%`-Suffix in reale physische Ordner.

## Klassen und ihre Methoden

### **Materializer** (Hauptklasse)

#### **1. Initialisierung und Konfiguration**
- **`__init__(plate_root: Path, projects_dir_name: str = "projects")`**

#### **2. Pfadauflösung (Ohne Erstellung)**
- **`resolve(virtual_path: str) -> Path`**

#### **3. Materialisierung (Mit Erstellung)**
- **`materialize(virtual_path: str) -> Path`**

#### **4. Hilfsmethoden**
- **`_create_folder_if_needed(parent_parts: List[str], folder: str) -> None`**
- **`is_materialized(folder_path: Path) -> bool`**

## Wichtige Hinweise

### **1. Projekte-Verzeichnis-Handling**
- `projects_dir_name` muss konsistent mit FUSE verwendet werden

### **2. `resolve()` vs `materialize()`**
- `resolve()` für read-only, `materialize()` für write operations

### **3. Cache-Strategie**
- `self.materialized` verfolgt in dieser Session erstellte Ordner

## Erweiterungsmöglichkeiten

### **1. Dringend: Fehlerbehandlung verbessern**
Integration von Python's `logging`-Modul

### **2. Dringend: Thread-Sicherheit**
`threading.Lock()` für `_create_folder_if_needed()`

### **3. Mittelfristig: Persistenter Cache**
Persistente Speicherung materialisierter Ordner

### **4. Langfristig: Reverse-Materialization**
Automatische Konvertierung leerer Ordner zurück zu Ghost-Folders