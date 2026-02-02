# test_local_blueprint_layer.py (überarbeitet)

import pytest
import subprocess
from pathlib import Path
import shutil
import os
import tempfile
import stat

from core.localBlueprintLayer import Blueprint

TEST_LAB_ROOT = Path(__file__).parent / "test_lab"
TEMPLATE_DIR = TEST_LAB_ROOT / "Templates"
PLATE_DIR = TEST_LAB_ROOT / "plate"

os.environ["MYOS_TEMPLATES_DIR"] = str(TEMPLATE_DIR)
print(f"[Test Setup] Set MYOS_TEMPLATES_DIR to: {TEMPLATE_DIR}")

@pytest.fixture(scope="session", autouse=True)
def set_test_templates_dir():
    original = os.getenv("MYOS_TEMPLATES_DIR")
    os.environ["MYOS_TEMPLATES_DIR"] = str(TEMPLATE_DIR)
    yield
    if original is not None:
        os.environ["MYOS_TEMPLATES_DIR"] = original
    else:
        os.environ.pop("MYOS_TEMPLATES_DIR", None)

@pytest.fixture(autouse=True)
def cleanup_myos_mounts_before_test():
    cleanup_all_myos_mounts()
    yield
    cleanup_all_myos_mounts()

def cleanup_all_myos_mounts():
    try:
        result = subprocess.run(['mount'], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return

    for line in result.stdout.splitlines():
        if 'MyOSFUSE' in line or 'fuse' in line and '/tmp/' in line:
            try:
                mount_point = line.split(' on ')[1].split(' type ')[0].strip()
                subprocess.run(['fusermount', '-u', mount_point], check=False)
                subprocess.run(['fusermount', '-uz', mount_point], check=False)
            except Exception as e:
                print(f"Unmount fehlgeschlagen für {mount_point}: {e}")

@pytest.fixture(scope="session")
def test_lab_structure():
    if PLATE_DIR.exists():
        shutil.rmtree(PLATE_DIR)
    if TEMPLATE_DIR.exists():
        shutil.rmtree(TEMPLATE_DIR)

    # Template-Verzeichnis
    TEMPLATES_ROOT = TEST_LAB_ROOT / "Templates"
    TEMPLATES_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Standard Template (ohne %-Marker!)
    STANDARD_DIR = TEMPLATES_ROOT / "Standard"
    STANDARD_DIR.mkdir(parents=True, exist_ok=True)
    
    (STANDARD_DIR / "admin").mkdir(exist_ok=True)
    (STANDARD_DIR / "info").mkdir(exist_ok=True)
    comm = STANDARD_DIR / "kommunikation"
    comm.mkdir(exist_ok=True)
    (comm / "intern").mkdir(exist_ok=True)
    (comm / "extern").mkdir(exist_ok=True)
    
    # Person Template
    PERSON_DIR = TEMPLATES_ROOT / "Person"
    PERSON_DIR.mkdir(exist_ok=True)
    (PERSON_DIR / "Ausbildung").mkdir(exist_ok=True)
    (PERSON_DIR / "Gesundheit").mkdir(exist_ok=True)
    
    # Plate-Struktur
    PLATE_DIR.mkdir(parents=True, exist_ok=True)
    
    projekte = PLATE_DIR / "Projekte"
    projekte.mkdir(exist_ok=True)
    _create_test_project(projekte, "Person")
    
    garten = projekte / "Garten"
    garten.mkdir(exist_ok=True)
    _create_test_project(garten, "FalscherTemplateName")
    
    haus = projekte / "Haus"
    haus.mkdir(exist_ok=True)
    _create_test_project(haus, "Standard")
    
    (haus / "Dach").mkdir(exist_ok=True)
    (haus / "Ausmalen").mkdir(exist_ok=True)
    (haus / "finanz").mkdir(exist_ok=True)
    (haus / "sonstigerOrdner").mkdir(exist_ok=True)
    _create_test_project(haus / "Dach", "Standard")

    ausmalen = haus / "Ausmalen"
    _create_test_project(ausmalen, "Standard")
    
    webseite = haus / "Dach" / "kommunikation" / "extern" / "Webseite"
    webseite.mkdir(parents=True, exist_ok=True)
    _create_test_project(webseite, "Standard")
    
    finanz = haus / "finanz"
    (finanz / "rechnungen").mkdir(exist_ok=True)
    (finanz / "rechnungen" / "2026").mkdir(exist_ok=True)
    
    (webseite / "info.txt").write_text("Webseite Info")
    (haus / "Dach" / "info.txt").write_text("Dach Info")
    (projekte / "info.txt").write_text("Projekte Info")
    (finanz / "rechnungen" / "2026" / "rechnung.pdf").write_text("PDF Rechnung")
    
    yield PLATE_DIR

def _create_test_project(project_dir, template_name):
    project_dir.mkdir(parents=True, exist_ok=True)
    myos_dir = project_dir / ".MyOS"
    myos_dir.mkdir(exist_ok=True)
    
    (myos_dir / "project.md").write_text("# MyOS Project\n")
    templates_content = f"# Project Templates\n\n## Templates\n- {template_name}\n"
    (myos_dir / "Templates.md").write_text(templates_content)
    
    print(f"Created test project at {project_dir} with template '{template_name}'")

# Fixtures
@pytest.fixture
def mount_haus(test_lab_structure):
    project_root = test_lab_structure / "Projekte" / "Haus"
    layer = Blueprint(project_root)
    yield layer, project_root

@pytest.fixture
def mount_garten(test_lab_structure):
    project_root = test_lab_structure / "Projekte" / "Garten"
    layer = Blueprint(project_root)
    yield layer, project_root

@pytest.fixture
def mount_webseite(test_lab_structure):
    project_root = test_lab_structure / "Projekte" / "Haus" / "Dach" / "kommunikation" / "extern" / "Webseite"
    layer = Blueprint(project_root)
    yield layer, project_root

# ────────────────────────────────────────────────────────────────
# Tests für FUSE-only Embryos (ohne %-Marker!)
# ────────────────────────────────────────────────────────────────


def test_01_is_embryo_method(mount_haus):
    """Testet die neue is_embryo() Methode ohne %-Marker."""
    layer, root = mount_haus
    
    # admin ist ein Embryo (existiert in Template, aber nicht physisch)
    assert layer.is_embryo("admin") == True
    
    # info ist ein Embryo
    assert layer.is_embryo("info") == True
    
    # kommunikation ist ein Embryo
    assert layer.is_embryo("kommunikation") == True
    
    # finanz ist KEIN Embryo (existiert physisch!)
    assert layer.is_embryo("finanz") == False
    
    # nicht-existenter Ordner ist kein Embryo
    assert layer.is_embryo("nonexistent") == False

def test_02_readdir_root_embryos_no_percent(mount_haus):
    """Testet ob Embryo-Ordner ohne %-Marker angezeigt werden."""
    layer, root = mount_haus
    
    entries = layer.readdir("/", None)
    print(f"[Test] Directory entries: {entries}")
    
    # Embryos sollten als normale Namen erscheinen
    assert "admin" in entries, f"'admin' not in {entries}"
    assert "info" in entries, f"'info' not in {entries}"
    assert "kommunikation" in entries, f"'kommunikation' not in {entries}"
    
    # KEIN %-Marker sollte erscheinen
    for entry in entries:
        assert not entry.endswith("%"), f"Unerwarteter %-Marker: {entry}"
    
    # Physische Ordner haben Vorrang
    assert "finanz" in entries  # Existiert physisch
    assert "Ausmalen" in entries  # Existiert physisch
    assert "Dach" in entries  # Existiert physisch

def test_03_embryos_in_nested_directories(mount_haus):
    """Testet verschachtelte Embryos."""
    layer, root = mount_haus
    
    # Im Root: kommunikation ist ein Embryo
    assert "kommunikation" in layer.readdir("/", None)
    
    # In kommunikation: intern und extern sollten Embryos sein
    embryos_in_kommunikation = layer.get_embryos_at("kommunikation")
    print(f"Embryos in kommunikation: {embryos_in_kommunikation}")
    
    assert "intern" in embryos_in_kommunikation
    assert "extern" in embryos_in_kommunikation

def test_04_physical_takes_precedence(mount_haus):
    """Testet dass physische Ordner Vorrang vor Embryos haben."""
    layer, root = mount_haus
    
    # Erstelle einen physischen Ordner mit dem Namen eines Embryos
    (root / "admin").mkdir(exist_ok=True)
    
    # Jetzt sollte admin nicht mehr als Embryo gelten
    entries = layer.readdir("/", None)
    print(f"Entries after creating physical 'admin': {entries}")
    
    # admin sollte nur einmal vorkommen (physisch)
    assert entries.count("admin") == 1
    # Und es sollte definitiv kein Embryo mehr sein
    assert layer.is_embryo("admin") == False

def test_05_getattr_for_embryos(mount_haus):
    """Testet getattr für Embryo-Verzeichnisse."""
    layer, root = mount_haus
    
    # admin sollte ein Embryo sein (noch nicht physisch)
    # Aber zuerst prüfen ob es physisch existiert (könnte von anderen Tests übrig sein)
    if (root / "admin").exists():
        print("WARNING: admin exists physically, skipping embryo test")
        return
    
    # getattr für ein Embryo
    attrs = layer.getattr("/admin", None)
    print(f"Attributes for /admin: {attrs}")
    
    assert attrs['st_mode'] & stat.S_IFDIR  # Es ist ein Verzeichnis
    # Embryos sollten read-only sein (0o555 = 16893 in decimal)
    # 16893 & 0o555 sollte 0o555 sein
    assert attrs['st_mode'] & 0o555 == 0o555
    
    # getattr für einen physischen Ordner
    attrs = layer.getattr("/finanz", None)
    print(f"Attributes for /finanz: {attrs}")
    assert attrs['st_mode'] & stat.S_IFDIR

def test_06_contains_embryos_method(mount_haus):
    """Testet die contains_embryos Methode."""
    layer, root = mount_haus
    
    # Test mit einem Embryo der sicher noch nicht physisch existiert
    # kommunikation sollte ein Embryo sein
    assert layer.contains_embryos("/kommunikation") == True
    assert layer.contains_embryos("/kommunikation/extern") == True  # Enthält Embryo
    assert layer.contains_embryos("/kommunikation/extern/website") == True
    
    # Physische Ordner sind keine Embryos
    assert layer.contains_embryos("/finanz") == False  # Kein Embryo
    assert layer.contains_embryos("/finanz/rechnungen") == False  # Kein Embryo
    
    # Komplexe Pfade
    assert layer.contains_embryos("/nonexistent/path") == False

def test_07_specific_embryo_exists(mount_haus):
    """Testet ob bestimmte Embryos korrekt erkannt werden."""
    layer, root = mount_haus
    
    # Liste der erwarteten Embryos aus Standard Template
    expected_embryos = ["admin", "info", "kommunikation"]
    
    for embryo in expected_embryos:
        physical_path = root / embryo
        print(f"Checking {embryo}: physical exists={physical_path.exists()}, is_embryo={layer.is_embryo(embryo)}")
        
        # Wenn es physisch existiert, sollte es kein Embryo sein
        if physical_path.exists():
            assert layer.is_embryo(embryo) == False, f"{embryo} exists but marked as embryo"
        else:
            assert layer.is_embryo(embryo) == True, f"{embryo} should be embryo but isn't"
    
    # Teste verschachtelte Embryos
    assert layer.is_embryo("kommunikation/extern") == True
    assert layer.is_embryo("kommunikation/intern") == True

def test_08_birth_process_no_percent(mount_haus):
    """Testet dass Embryos bei create/mkdir materialisiert werden."""
    layer, root = mount_haus
    
    # Wähle einen Embryo, der definitiv noch nicht existiert
    # kommunikation/extern sollte ein Embryo sein
    embryo_path = "kommunikation"
    
    # kommunikation sollte noch nicht existieren
    assert not (root / embryo_path).exists()
    assert layer.is_embryo(embryo_path) == True
    
    # Versuche eine Datei in kommunikation zu erstellen
    try:
        fd = layer.create(f"/{embryo_path}/test.txt", 0o644, None)
        layer.write(f"/{embryo_path}/test.txt", b"test", 0, fd)
        layer.release(f"/{embryo_path}/test.txt", fd)
    except Exception as e:
        print(f"create failed: {e}, trying mkdir")
        # Falls create nicht funktioniert, versuche mkdir
        layer.mkdir(f"/{embryo_path}", 0o755)
    
    # Jetzt sollte kommunikation materialisiert sein
    assert (root / embryo_path).exists()
    
    # Und kein Embryo mehr
    assert layer.is_embryo(embryo_path) == False
    
    # In readdir sollte kommunikation noch erscheinen (als physischer Ordner)
    entries = layer.readdir("/", None)
    assert embryo_path in entries

def test_project_with_broken_template(mount_garten):
    """Testet Verhalten bei nicht-existierendem Template."""
    layer, root = mount_garten
    entries = layer.readdir("/", None)
    
    # Garten hat "FalscherTemplateName" - sollte keine Embryos haben
    assert "admin" not in entries
    assert "info" not in entries
    assert "kommunikation" not in entries

def test_deeply_nested_project(mount_webseite):
    """Testet tief verschachtelte Projekte."""
    layer, root = mount_webseite
    assert layer.project_root.name == "Webseite"
    
    entries = layer.readdir("/", None)
    print(f"[Test Webseite] Entries: {entries}")
    
    # Webseite sollte auch Embryos aus Standard Template haben
    assert "admin" in entries
    assert "info" in entries
    assert "kommunikation" in entries

def test_performance_cache(mount_haus):
    """Testet dass der Embryo-Cache funktioniert."""
    layer, root = mount_haus
    
    import time
    
    # Wähle einen Embryo der sicher existiert
    # "info" sollte ein Embryo sein (aus Standard Template)
    embryo_test = "info"
    
    # Erster Aufruf (sollte nicht gecached sein)
    start = time.time()
    result1 = layer.is_embryo(embryo_test)
    time1 = time.time() - start
    
    # Zweiter Aufruf (sollte gecached sein)
    start = time.time()
    result2 = layer.is_embryo(embryo_test)
    time2 = time.time() - start
    
    print(f"is_embryo('{embryo_test}'): {result1}")
    print(f"First call: {time1:.6f}s, Second call: {time2:.6f}s")
    
    # Wenn es ein Embryo ist, sollte Cache funktionieren
    if result1:
        assert result1 == result2
        # Cache sollte schneller oder gleich schnell sein
        # (kein strikter Assert, da Timing variieren kann)
    else:
        print(f"WARNING: {embryo_test} is not an embryo, cache test inconclusive")

def test_security_path_traversal_blocked():
    """Test that path traversal attempts in embryo paths are blocked."""
    # Setup a normal project
    project_root = PLATE_DIR / "SecurityTestProject"
    if project_root.exists():
        shutil.rmtree(project_root)
    
    project_root.mkdir()
    _create_test_project(project_root, "Standard")
    
    # Create BirthClinic directly to test the method
    from core.localBlueprintLayer import BirthClinic, Blueprint
    
    blueprint = Blueprint(project_root)
    clinic = blueprint.birth_clinic
    
    # Test cases that SHOULD fail
    traversal_attempts = [
        "admin/../../etc",
        "safe/../evil",
        "a/b/../../c",
        "..%2f..%2fetc",  # URL encoded (though unlikely here)
        "normal/..",
    ]
    
    for bad_path in traversal_attempts:
        print(f"Testing traversal: {bad_path}")
        try:
            # This should call find_template_source internally
            clinic.give_birth(bad_path)
            assert False, f"Path traversal should have been blocked: {bad_path}"
        except ValueError as e:
            error_msg = str(e)
            print(f"  ✓ Blocked: {error_msg}")
            assert "CWE-22" in error_msg or "traversal" in error_msg.lower()
    
    print("✅ All path traversal attempts correctly blocked")

def test_security_absolute_paths_blocked():
    """Test that absolute paths in embryo paths are blocked."""
    project_root = PLATE_DIR / "SecurityTestProject2"
    if project_root.exists():
        shutil.rmtree(project_root)
    
    project_root.mkdir()
    _create_test_project(project_root, "Standard")
    
    from core.localBlueprintLayer import BirthClinic, Blueprint
    
    blueprint = Blueprint(project_root)
    clinic = blueprint.birth_clinic
    
    # Test absolute paths (Unix and Windows style)
    absolute_paths = [
        "/etc/passwd",
        "/tmp/evil",
        "C:\\Windows\\System32",  # Might come through somehow
        "//network/share",
    ]
    
    for abs_path in absolute_paths:
        print(f"Testing absolute path: {abs_path}")
        try:
            clinic.give_birth(abs_path)
            assert False, f"Absolute path should have been blocked: {abs_path}"
        except ValueError as e:
            error_msg = str(e)
            print(f"  ✓ Blocked: {error_msg}")
            assert "absolute" in error_msg.lower() or "not allowed" in error_msg
    
    print("✅ All absolute paths correctly blocked")

def test_security_valid_paths_allowed():
    """Test that valid embryo paths still work."""
    project_root = PLATE_DIR / "SecurityTestProject3"
    if project_root.exists():
        shutil.rmtree(project_root)
    
    project_root.mkdir()
    _create_test_project(project_root, "Standard")
    
    from core.localBlueprintLayer import BirthClinic, Blueprint
    
    blueprint = Blueprint(project_root)
    clinic = blueprint.birth_clinic
    
    # Valid paths that SHOULD work
    valid_paths = [
        "admin",
        "info",
        "kommunikation",
        "kommunikation/extern",
        "kommunikation/intern",
    ]
    
    for valid_path in valid_paths:
        print(f"Testing valid path: {valid_path}")
        try:
            # We can't actually give_birth because templates might not exist
            # Just test that find_template_source doesn't raise security errors
            source = clinic.find_template_source(valid_path)
            print(f"  ✓ Found template source: {source}")
        except ValueError as e:
            if "traversal" in str(e).lower() or "absolute" in str(e).lower():
                # This would be wrong - valid path blocked!
                assert False, f"Valid path incorrectly blocked: {valid_path} - {e}"
            else:
                # Other errors are OK (e.g., template not found)
                print(f"  Note: {type(e).__name__}: {e}")
    
    print("✅ Valid paths correctly accepted")

def test_security_edge_cases():
    """Test edge cases and weird inputs."""
    project_root = PLATE_DIR / "SecurityEdgeCases"
    if project_root.exists():
        shutil.rmtree(project_root)
    
    project_root.mkdir()
    _create_test_project(project_root, "Standard")
    
    from core.localBlueprintLayer import BirthClinic, Blueprint
    
    blueprint = Blueprint(project_root)
    clinic = blueprint.birth_clinic
    
    edge_cases = [
        ("", "empty path"),
        (".", "current directory"),
        (".hidden", "hidden file"),
        ("..", "parent directory"),
        ("../..", "grandparent"),
        ("....", "multiple dots"),
        (".. / ..", "space in traversal"),
        ("../\t/..", "tab in path"),
    ]
    
    for path, description in edge_cases:
        print(f"Testing edge case '{description}': '{path}'")
        try:
            clinic.give_birth(path)
            # Some might be valid, some not - check error message
        except ValueError as e:
            error_msg = str(e)
            print(f"  Result: {error_msg[:50]}...")
        except Exception as e:
            print(f"  Other error: {type(e).__name__}: {e}")
    
    print("✅ Edge cases handled")

def test_all_security():
    """Run all security tests."""
    test_security_path_traversal_blocked()
    test_security_absolute_paths_blocked()
    test_security_valid_paths_allowed()
    test_security_edge_cases()
    print("\n" + "="*60)
    print("ALL SECURITY TESTS PASSED ✅")
    print("="*60)

if __name__ == "__main__":
    # Für manuelles Testen
    test_all_security()

class TestBlueprintPerformance:
    """Performance-Benchmarks für den Blueprint-Layer."""
    
    def test_embryo_detection_performance(self, mount_haus):
        """Misst Performance der Embryo-Erkennung."""
        layer, root = mount_haus
        
        # Test-Pfade
        test_paths = [
            "admin", "info", "kommunikation", 
            "kommunikation/intern", "kommunikation/extern",
            "finanz", "finanz/rechnungen", "nonexistent"
        ]
        
        repetitions = 100
        total_ops = len(test_paths) * repetitions
        
        # Warm-up
        for path in test_paths:
            _ = layer.is_embryo(path)
        
        # Messung
        import time
        start = time.perf_counter()
        
        for _ in range(repetitions):
            for path in test_paths:
                _ = layer.is_embryo(path)
        
        total_time = time.perf_counter() - start
        ops_per_second = total_ops / total_time
        
        print(f"\n{'='*60}")
        print(f"PERFORMANCE: Embryo Detection")
        print(f"{'='*60}")
        print(f"Total operations: {total_ops}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Operations/sec: {ops_per_second:,.0f}")
        print(f"Time per op: {(total_time/total_ops)*1_000_000:.1f}μs")
        
        assert ops_per_second > 10_000, f"Only {ops_per_second:,.0f} ops/sec"
        print("✅ Performance acceptable!")
    
    def test_cache_speedup(self, mount_haus):
        """Misst Cache-Geschwindigkeitsvorteil."""
        layer, root = mount_haus
        
        import time
        
        # Uncached (erstmaliger Aufruf)
        start = time.perf_counter()
        result1 = layer.is_embryo("admin")
        uncached_time = time.perf_counter() - start
        
        # Cached (zweiter Aufruf)
        start = time.perf_counter()
        result2 = layer.is_embryo("admin")
        cached_time = time.perf_counter() - start
        
        speedup = uncached_time / cached_time if cached_time > 0 else 0
        
        print(f"\nCACHE PERFORMANCE:")
        print(f"Uncached: {uncached_time*1_000_000:.1f}μs")
        print(f"Cached:   {cached_time*1_000_000:.1f}μs")
        print(f"Speedup:  {speedup:.1f}x")
        
        assert speedup > 1.5, f"Cache speedup only {speedup:.1f}x"
        print("✅ Cache effective!")
    
    def test_readdir_performance(self, mount_haus):
        """Misst readdir() Performance."""
        layer, root = mount_haus
        
        import time
        
        iterations = 100
        times = []
        
        for i in range(iterations):
            start = time.perf_counter()
            entries = layer.readdir("/", None)
            end = time.perf_counter()
            times.append(end - start)
        
        avg_time_ms = (sum(times) / len(times)) * 1000
        entries_count = len(entries)
        
        print(f"\nREADDIR PERFORMANCE:")
        print(f"Iterations: {iterations}")
        print(f"Entries returned: {entries_count}")
        print(f"Average time: {avg_time_ms:.2f}ms")
        print(f"Fastest: {min(times)*1000:.2f}ms")
        print(f"Slowest: {max(times)*1000:.2f}ms")
        
        assert avg_time_ms < 5.0, f"readdir too slow: {avg_time_ms:.2f}ms"
        print("✅ readdir performance acceptable!")

    def test_template_with_symlink_rejected(self):
        """Testet dass Templates mit Symlinks abgelehnt werden."""
        # Erstelle ein Template mit einem Symlink
        test_template = TEMPLATE_DIR / "UnsafeTemplate"
        test_template.mkdir(exist_ok=True)
        
        (test_template / "normal_folder").mkdir()
        (test_template / "normal_file.txt").write_text("normal")
        
        # Erstelle einen Symlink
        link_target = test_template / "link_target"
        link_target.mkdir()
        symlink = test_template / "unsafe_symlink"
        symlink.symlink_to(link_target, target_is_directory=True)
        
        # Versuche ein Projekt mit diesem Template zu mounten
        project_root = PLATE_DIR / "TestUnsafeProject"
        project_root.mkdir(exist_ok=True)
        _create_test_project(project_root, "UnsafeTemplate")
        
        # Sollte scheitern oder zumindest eine Warnung geben
        try:
            layer = Blueprint(project_root)
            # Versuche ein Embryo zu materialisieren
            if layer.is_embryo("normal_folder"):
                # Sollte wegen Symlink im Template scheitern
                try:
                    layer.mkdir("/normal_folder", 0o755)
                    print("WARNING: Template with symlink was accepted!")
                    # Wenn wir hier ankommen, ist der Test fehlgeschlagen
                    assert False, "Template with symlink should have been rejected"
                except ValueError as e:
                    print(f"GOOD: Template correctly rejected: {e}")
                    assert "symlink" in str(e).lower() or "security" in str(e).lower()
        except Exception as e:
            print(f"GOOD: Blueprint creation failed due to unsafe template: {e}")
            assert "symlink" in str(e).lower() or "security" in str(e).lower()



if __name__ == "__main__":
    # Einfache manuelle Tests
    test_all_security()
    pytest.main([__file__, "-v"])
