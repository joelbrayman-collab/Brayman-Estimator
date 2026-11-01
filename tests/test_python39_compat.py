"""Production and the office Mac release gate run Python 3.9.6 (1 Nov 2026).

The tf1 release gate stopped because a test used sys.stdlib_module_names, which only exists from Python 3.10;
the development container runs a newer Python, so it passed there and failed on the Mac. This guard scans every
Python file under app/, tests/, tools/ and migrations/ for syntax and standard-library APIs that need 3.10 or later,
so the next one is caught in the container too.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOTS = ("app", "tests", "tools", "migrations")

# Attribute access that only exists from Python 3.10 (module, attribute).
NEW_ATTRS = {("sys", "stdlib_module_names"), ("sys", "orig_argv"), ("itertools", "pairwise")}
# Keyword arguments that only exist from Python 3.10, keyed by the called name.
NEW_KWARGS = {"zip": {"strict"}, "dataclass": {"slots", "kw_only", "match_args"}, "bisect": {"key"},
              "bisect_left": {"key"}, "bisect_right": {"key"}, "insort": {"key"}}


def _files():
    for root in ROOTS:
        for path in sorted((REPO / root).rglob("*.py")):
            if "__pycache__" not in path.parts and "node_modules" not in path.parts:
                yield path


def _guarded_names(tree):
    """sys.stdlib_module_names read through getattr(...) or behind hasattr(...) is fine on 3.9."""
    ok = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("hasattr", "getattr"):
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                ok.add(node.args[1].value)
    return ok


def test_every_python_file_parses_with_python_39_grammar():
    bad = []
    for path in _files():
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))
        except SyntaxError as exc:
            bad.append(f"{path.relative_to(REPO)}:{exc.lineno}: {exc.msg}")
    assert bad == []


def test_no_standard_library_api_that_needs_python_310():
    bad = []
    for path in _files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        guarded = _guarded_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if (node.value.id, node.attr) in NEW_ATTRS and node.attr not in guarded:
                    bad.append(f"{path.relative_to(REPO)}:{node.lineno}: {node.value.id}.{node.attr}")
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
                for kw in node.keywords:
                    if kw.arg in NEW_KWARGS.get(name, ()):
                        bad.append(f"{path.relative_to(REPO)}:{node.lineno}: {name}({kw.arg}=...)")
    assert bad == []


def test_the_guard_catches_the_tf1_case():
    tree = ast.parse("import sys\nok = 'json' in sys.stdlib_module_names\n")
    hits = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and (getattr(n.value, "id", None), n.attr) in NEW_ATTRS]
    assert len(hits) == 1
    guarded = ast.parse("import sys\nok = getattr(sys, 'stdlib_module_names', None)\n")
    assert "stdlib_module_names" in _guarded_names(guarded)
