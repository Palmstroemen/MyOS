## 📋 Test-Übersicht

MyOS verwendet **Test-Driven Development (TDD)** mit einem umfangreichen Test-Suite, der alle Komponenten abdeckt.

## 🏗️ Test-Architektur

text

tests/
├── unit/                          # Unit Tests
│   ├── core/                      # Core-Komponenten
│   │   ├── test_local_blueprint_layer.py    # Blueprint-Layer (FUSE)
│   │   └── test_project_config.py          # Projekt-Konfiguration
│   └── cli/                       # CLI-Tools
│       ├── test_myls.py           # myls erweiterte Features
│       └── test_cli_myls.py       # myls Basis-Features
└── integration/                   # Integration Tests (zukünftig)

## 🚀 Test-Ausführung

### **Alle Tests ausführen**

bash

python3 -m pytest

### **Nur bestimmte Test-Gruppen**

bash

# Nur Blueprint-Layer Tests
python3 -m pytest core/tests/unit/

# Nur CLI Tests
python3 -m pytest cli/tests/

# Nur myls Tests
python3 -m pytest cli/tests/test_myls.py

# Einzelner Test
python3 -m pytest cli/tests/test_myls.py::test_extended_view_with_mock_api

### **Mit Details**

bash

python3 -m pytest -v              # Ausführlich
python3 -m pytest -s              # Zeige stdout
python3 -m pytest --tb=short      # Kurze Tracebacks

## 🧪 Test-Kategorien

### **1. Blueprint-Layer Tests** (`core/tests/unit/test_local_blueprint_layer.py`)

**Was wird getestet:**

- Embryo-Erkennung ohne %-Marker
    
- Template-Loading und Merging
    
- FUSE-Operationen (readdir, getattr, mkdir, create)
    
- Materialisierung (Birth Process)
    
- Cache-Verhalten
    

**Beispiel-Tests:**

python

def test_is_embryo_method():
    """Prüft Embryo-Erkennung ohne %-Marker."""
    assert layer.is_embryo("admin") == True      # Embryo
    assert layer.is_embryo("finanz") == False    # Physisch existiert

def test_readdir_root_embryos_no_percent():
    """Embryos ohne %-Marker in readdir()."""
    entries = layer.readdir("/", None)
    assert "admin" in entries                    # Normaler Name
    assert not any(e.endswith("%") for e in entries)  # Keine %!

def test_birth_process_no_percent():
    """Embryo-Materialisierung bei create/mkdir."""
    layer.create("/admin/test.txt", 0o644, None)
    assert (root / "admin").exists()             # Jetzt physisch
    assert layer.is_embryo("admin") == False     # Kein Embryo mehr

### **2. Projekt-Konfiguration Tests** (`core/tests/unit/test_project_config.py`)

**Was wird getestet:**

- Projekt-Erkennung (`.MyOS/Project.md`)
    
- Template-Parsing
    
- Projekt-Root-Findung
    
- Verschachtelte Projekt-Strukturen
    

**Beispiel-Tests:**

python

def test_project_root_findung_multiple_levels():
    """Projekt-Root-Findung in tiefen Verzeichnissen."""
    # Start: /home/projects/haus/dach/kommunikation/extern/webseite
    # Erwartet: webseite/ (weil .MyOS/Project.md dort)
    layer = Blueprint(tiefes_verzeichnis)
    assert layer.project_root.name == "Webseite"

### **3. myls Basis-Tests** (`cli/tests/test_cli_myls.py`)

**Was wird getestet:**

- Grundlegende myls-Funktionalität
    
- Verschiedene Ansichten (normal, recent, roentgen)
    
- Kommandozeilen-Interface
    
- Fehlerbehandlung
    

**Beispiel-Tests:**

python

def test_list_normal(self):
    """Normale ls-ähnliche Ausgabe."""
    self.lister.list_normal()  # Sollte laufen ohne Exception

def test_recent_shows_modified_first(self):
    """Recent-Ansicht sortiert nach Modifikationszeit."""
    self.lister.list_recent(limit=2)

def test_roentgen_shows_paths(self):
    """Roentgen zeigt Dateien mit Pfaden."""
    self.lister.list_roentgen(limit=5)

### **4. myls Extended Tests** (`cli/tests/test_myls.py`)

**Was wird getestet:**

- `--extended` Flag Parsing
    
- Embryo-Anzeige in erweiterter Ansicht
    
- Farbige Ausgabe
    
- MyOS API Integration
    
- Mocking von Blueprint-Layer
    

**Beispiel-Tests:**

python

def test_extended_view_with_mock_api():
    """Extended view mit gemockter Blueprint API."""
    lister.api = MockAPI()  # Mock für Embryo-Erkennung
    lister.list_extended()
    assert "[embryo]" in output  # Embryo-Markierung

def test_extended_color_output():
    """Farbige extended Ausgabe."""
    lister.list_extended(color=True)
    # Embryos sollten farbig/kursiv erscheinen

## 🔧 Test-Fixtures

### **Blueprint-Layer Fixtures**

python

@pytest.fixture
def mount_haus(test_lab_structure):
    """Blueprint-Layer auf Haus-Projekt gemountet."""
    project_root = test_lab_structure / "Projekte" / "Haus"
    layer = Blueprint(project_root)
    yield layer, project_root  # (Blueprint, physischer Pfad)

### **Test-Lab Struktur**

python

@pytest.fixture(scope="session")
def test_lab_structure():
    """Komplette Test-Umgebung mit Templates und Projekten."""
    # Erstellt:
    # - Templates/Standard/ mit admin/, info/, kommunikation/
    # - Plate/Projekte/Haus/ mit .MyOS/Project.md
    # - Verschachtelte Projekt-Strukturen
    return PLATE_DIR

### **Temporäre Verzeichnisse**

python

def test_with_temp_dir():
    """Test mit temporärem Verzeichnis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "test.txt").touch()
        lister = MyOSLister(str(tmp))
        # Test-Logik hier

## 🧠 Test-Strategien

### **1. Mocking**

python

# Mock für Blueprint API
class MockAPI:
    def is_embryo(self, name):
        return name in ["admin", "finance"]
    
    @property
    def embryo_tree(self):
        return {"admin": {}, "finance": {}}

# In Test verwenden
lister.api = MockAPI()
lister.in_myos_project = True

### **2. State Isolation**

python

# Jeder Test bekommt frischen State
def test_embryo_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Eigenes Test-Verzeichnis
        # Keine Seiteneffekte auf andere Tests

### **3. Performance Testing**

python

def test_embryo_detection_performance():
    """Performance-Benchmark für Embryo-Erkennung."""
    start = time.perf_counter()
    for _ in range(1000):
        layer.is_embryo("admin")
    total_time = time.perf_counter() - start
    assert total_time < 0.1  # < 100ms für 1000 Operationen

### **4. Cache-Verhalten**

python

def test_cache_speedup():
    """Misst Cache-Geschwindigkeitsvorteil."""
    uncached_time = time_operation(lambda: layer.is_embryo("admin"))
    cached_time = time_operation(lambda: layer.is_embryo("admin"))
    assert cached_time < uncached_time  # Cache sollte schneller sein

## 📊 Test-Statistiken

**Aktuelle Coverage:**

- **Blueprint-Layer:** 31 Tests ✅
    
- **Projekt-Konfig:** 8 Tests ✅
    
- **myls Basis:** 9 Tests ✅
    
- **myls Extended:** 6 Tests ✅
    
- **Total:** 54 Tests ✅
    

**Performance:**

- Test-Suite läuft in ~0.3s
    
- Embryo-Erkennung: ~22μs pro Operation
    
- Cache-Lookup: ~11μs pro Operation
    

## 🐛 Debugging von Tests

### **Test-Ausgabe anzeigen**

bash

python3 -m pytest -v -s  # Zeigt print()-Ausgaben

### **Fehlgeschlagene Tests isolieren**

bash

# Nur fehlgeschlagene Tests
python3 -m pytest --lf

# Letzten Fehler anzeigen
python3 -m pytest --tb=long

### **Test-Coverage**

bash

# Coverage report (mit pytest-cov)
python3 -m pytest --cov=core --cov=cli --cov-report=html

## 🎯 Test-Guidelines

### **Für neue Features:**

1. **Tests zuerst schreiben** (TDD)
    
2. **Mocking verwenden** für externe Abhängigkeiten
    
3. **State isolieren** mit temp directories
    
4. **Performance prüfen** bei kritischen Pfaden
    

### **Für Bugfixes:**

1. **Reproduzierenden Test schreiben** der den Bug zeigt
    
2. **Fix implementieren**
    
3. **Test sollte jetzt grün sein**
    
4. **Bestehende Tests prüfen** (Regression)
    

### **Test-Naming Convention:**

python

def test_<unit>_<behavior>[_<condition>]:
    # Beispiel:
    test_is_embryo_method
    test_readdir_root_embryos_no_percent
    test_birth_process_no_percent
    test_embryo_detection_performance

## 🔍 Beispiel: Vollständiger Test-Cycle

### **1. Test für neues Feature schreiben**

python

# test_myls.py
def test_new_feature_x():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup
        tmp = Path(tmpdir)
        # Test-Logik
        result = some_function()
        # Assertion
        assert result == expected_value

### **2. Test ausführen (sollte rot sein)**

bash

python3 -m pytest cli/tests/test_myls.py::test_new_feature_x -v

### **3. Feature implementieren**

python

# myls.py
def some_function():
    # Implementation
    return expected_value

### **4. Test erneut ausführen (sollte grün sein)**

bash

python3 -m pytest cli/tests/test_myls.py::test_new_feature_x -v

### **5. Alle Tests prüfen (keine Regression)**

bash

python3 -m pytest

## 📈 Test-Metriken & CI

**IDEAL:** Alle Tests grün vor jedem Commit  
**REALITÄT:** >95% Test-Passing Rate  
**COVERAGE:** >80% Code-Coverage (Ziel)

**CI-Pipeline (zukünftig):**

yaml

# .github/workflows/test.yml
jobs:
  test:
    steps:
      - run: python3 -m pytest
      - run: python3 -m pytest --cov
      - run: python3 -m pytest core/tests/unit/test_performance_benchmark.py

## 🛠️ Hilfreiche Commands

### **Test-Datenbank**

bash

# Test-Umgebung aufbauen
cd core/tests/unit/
ls test_lab/  # Zeigt Test-Struktur

# Blueprint-Layer manuell testen
python3 -c "from test_local_blueprint_layer import *; test_is_embryo_method()"

### **Debug-Modus**

python

# In Tests Debug-Output aktivieren
print(f"[DEBUG] Cache size: {len(layer._embryo_cache)}")
# Oder mit pytest -s sehen

## 🎓 Best Practices

1. **Kleine, fokussierte Tests** (eine Assertion pro Test ideal)
    
2. **Deskriptive Test-Namen** (sagen was getestet wird)
    
3. **Keine Abhängigkeiten zwischen Tests**
    
4. **Mocking für externe Systeme**
    
5. **Performance-Tests für kritische Pfade**
    
6. **Regression-Tests für Bugs**
    

---

**Zusammenfassung:** MyOS hat eine umfangreiche Test-Suite, die alle Kern-Features abdeckt und TDD für neue Features erzwingt. Die Tests sind schnell (<0.5s), isoliert und geben gute Einblicke in das Systemverhalten.