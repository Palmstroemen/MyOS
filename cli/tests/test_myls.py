# cli/tests/test_myls.py
import pytest
from pathlib import Path
import sys
import os
import tempfile
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from cli.myls import MyOSLister, parse_arguments, main

def test_extended_flag_parsing(monkeypatch):
    """Teste dass --extended Flag korrekt geparst wird."""
    monkeypatch.setattr(sys, 'argv', ['myls.py', '--extended'])
    args = parse_arguments()
    assert args.extended == True
    assert args.path == "."
    
    monkeypatch.setattr(sys, 'argv', ['myls.py', '/some/path', '--extended'])
    args = parse_arguments()
    assert args.extended == True
    assert args.path == "/some/path"
    
    monkeypatch.setattr(sys, 'argv', ['myls.py'])
    args = parse_arguments()
    assert args.extended == False

def test_extended_view_without_api(capsys):
    """Teste extended view ohne MyOS API."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "file1.txt").touch()
        (tmp / "folder1").mkdir()
        
        lister = MyOSLister(str(tmp))
        lister.list_extended()
        
        captured = capsys.readouterr()
        assert "file1.txt" in captured.out
        assert "folder1" in captured.out

class MockAPI:
    def __init__(self, project_root=None):
        self.embryo_tree = {"admin": {}, "finance": {}}
        self._project_root = project_root or Path("/mock/project")
        self.template_names = ["Standard"]
    
    @property
    def project_root(self):
        return self._project_root
    
    def is_embryo(self, name):
        return name in ["admin", "finance"]
    
    def get_embryos_at(self, path):
        return ["admin", "finance"] if path == "" else []
    
    def count_embryos(self):
        return 2
    
    def get_template_name(self):
        return "Standard"

def test_extended_view_with_mock_api(capsys, monkeypatch):
    """Teste extended view mit mock API für Embryos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "admin").mkdir()
        (tmp / "src").mkdir()
        (tmp / "file.txt").touch()
        
        lister = MyOSLister(str(tmp))
        
        # Mock API mit korrektem project_root
        mock_api = MockAPI(project_root=tmp)
        lister.api = mock_api
        lister.in_myos_project = True
        
        lister.list_extended()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "admin" in output
        assert "src" in output  
        assert "file.txt" in output
        assert "[embryo]" in output or "Template:" in output

def test_extended_color_output(capsys, monkeypatch):
    """Teste farbige extended Ausgabe."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "embryo_dir").mkdir()
        
        class SimpleMockAPI:
            def __init__(self):
                self.embryo_tree = {"embryo_dir": {}}
                self.project_root = tmp
                self.template_names = ["Test"]
            
            def is_embryo(self, name):
                return name == "embryo_dir"
            
            def get_embryos_at(self, path):
                return ["embryo_dir"] if path == "" else []
            
            def count_embryos(self):
                return 1
            
            def get_template_name(self):
                return "Test"
        
        lister = MyOSLister(str(tmp))
        lister.api = SimpleMockAPI()
        lister.in_myos_project = True
        
        lister.list_extended(color=True)
        
        captured = capsys.readouterr()
        assert "embryo_dir" in captured.out

def test_command_line_integration(monkeypatch):
    """Teste myls.py mit --extended."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "testfile.txt").touch()
        
        monkeypatch.setattr(sys, 'argv', ['myls.py', '--extended', str(tmp)])
        
        import io
        from contextlib import redirect_stdout, redirect_stderr
        
        f = io.StringIO()
        with redirect_stdout(f), redirect_stderr(io.StringIO()):
            try:
                main()
            except SystemExit as e:
                if e.code != 0:
                    raise
        
        output = f.getvalue()
        assert "testfile.txt" in output

def test_basic_extended():
    """Einfacher Test für extended view."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "normal_dir").mkdir()
        (tmp / "normal_file.txt").touch()
        
        lister = MyOSLister(str(tmp))
        # Sollte ohne Fehler laufen
        lister.list_extended()
        lister.list_extended(color=True)
