"""The name in one place (core/brand.py): helpers and a guard against new literals."""

import ast
import re
from pathlib import Path

import pytest

from core import brand

REPO = Path(__file__).resolve().parents[3]


def test_meta_dir_is_inside_the_folder(tmp_path):
    assert brand.meta_dir(tmp_path) == tmp_path / brand.META_DIR
    assert brand.meta_dir(str(tmp_path)) == tmp_path / brand.META_DIR


def test_config_dir_follows_xdg_config_home(tmp_path):
    assert brand.config_dir({"XDG_CONFIG_HOME": str(tmp_path)}) == tmp_path / brand.CONFIG_DIR


def test_config_dir_falls_back_to_dot_config():
    assert brand.config_dir({}) == Path.home() / ".config" / brand.CONFIG_DIR


def test_getenv_reads_the_current_name():
    env = {brand.env_name("ACL_MODE"): "enforce"}
    assert brand.getenv("ACL_MODE", env=env) == "enforce"
    assert brand.getenv("ACL_USER", "nobody", env=env) == "nobody"


def test_getenv_keeps_an_empty_value():
    assert brand.getenv("X", "default", env={brand.env_name("X"): ""}) == ""


def test_getenv_falls_back_to_former_names(monkeypatch):
    monkeypatch.setattr(brand, "LEGACY_ENV_PREFIXES", ("OLDNAME_",))
    assert brand.getenv("ACL_MODE", env={"OLDNAME_ACL_MODE": "monitor"}) == "monitor"
    both = {"OLDNAME_ACL_MODE": "monitor", brand.env_name("ACL_MODE"): "enforce"}
    assert brand.getenv("ACL_MODE", env=both) == "enforce"


def test_getenv_reads_os_environ_by_default(monkeypatch):
    monkeypatch.setenv(brand.env_name("BRAND_PROBE"), "1")
    assert brand.getenv("BRAND_PROBE") == "1"


def test_qml_has_the_same_name():
    """Scope/js/Brand.js mirrors core/brand.py for QML."""
    js = (REPO / "Scope" / "js" / "Brand.js").read_text(encoding="utf-8")
    values = dict(re.findall(r'^var (\w+) = "([^"]*)"$', js, re.M))
    assert values == {"NAME": brand.NAME, "META_DIR": brand.META_DIR}


def test_qml_takes_the_name_from_brand_js():
    for name in ("main.qml", "FolderBrowser.qml"):
        qml = (REPO / "Scope" / name).read_text(encoding="utf-8")
        code = "\n".join(line.split("//", 1)[0] for line in qml.splitlines())
        for value in (brand.NAME, brand.META_DIR, "MyOS", ".MyOS"):
            assert f'"{value}"' not in code, (name, value)


# Security: To avoid a rename that leaves parts behind, code outside core/brand.py must not
# spell the settings folder or an environment variable itself (comments and docstrings may).
# ClipboardTool stands alone (started by CopyQ, see core/brand.py).
_CODE_DIRS = ("core", "cli", "cloud/service", "Scope", "PostFix", "SunTree", "daemon", "scripts")
_DIRS = (brand.META_DIR, *brand.LEGACY_META_DIRS)
_PREFIXES = (brand.ENV_PREFIX, *brand.LEGACY_ENV_PREFIXES)
_LITERAL = re.compile(
    r"\bX-(MyOS|Seiton)-|(^|[^A-Za-z0-9])(" + "|".join(re.escape(d) for d in _DIRS) + r")($|[^A-Za-z0-9_])"
    r"|\b(" + "|".join(re.escape(p) for p in _PREFIXES) + r")[A-Z]"
    r"|^(" + "|".join(re.escape(n) for n in {brand.NAME, brand.CONFIG_DIR, "MyOS"}) + r")$")


def _strings(tree: ast.AST):
    """The string constants of tree with their line, docstrings left out."""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node.lineno, node.value
        elif isinstance(node, ast.keyword) and node.arg:  # dict(os.environ, MYOS_X="0")
            yield node.lineno, node.arg


@pytest.mark.parametrize("folder", _CODE_DIRS)
def test_no_name_literals_outside_brand(folder):
    found = []
    for path in sorted((REPO / folder).rglob("*.py")):
        rel = path.relative_to(REPO)
        if "tests" in rel.parts or "archive" in rel.parts or path.name == "brand.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for line, text in _strings(tree):
            if _LITERAL.search(text):
                found.append(f"{rel}:{line}: {text[:80]!r}")
    assert not found, "use core.brand:\n" + "\n".join(found)
