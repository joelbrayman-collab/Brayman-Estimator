"""Production dependencies are pinned to the verified working set (Joel, 18 Oct 2026).

requirements.txt pins every top-level package exactly and constrains everything they pull in
with requirements-lock.txt (the set Render installed for 0e2c917), so every build is the same.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _lines(name):
    return [
        line.split("#", 1)[0].strip()
        for line in (ROOT / name).read_text().splitlines()
        if line.split("#", 1)[0].strip()
    ]


def _pins(name):
    pins = {}
    for line in _lines(name):
        if line.startswith("-"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.\-]+)", line)
        assert match, f"{name}: not an exact pin: {line!r}"
        pins[match.group(1).lower().replace("_", "-")] = match.group(2)
    return pins


def test_requirements_pin_every_package_exactly_and_use_the_lock():
    assert "-c requirements-lock.txt" in _lines("requirements.txt")
    top = _pins("requirements.txt")
    lock = _pins("requirements-lock.txt")
    assert len(top) == 17
    for name, version in top.items():
        assert lock.get(name) == version, name


def test_the_lock_is_complete_and_exact():
    lock = _pins("requirements-lock.txt")
    assert len(lock) == 62
    for name in ("flask", "werkzeug", "sqlalchemy", "jinja2", "numpy", "pypdf", "reportlab"):
        assert name in lock


def test_dev_requirements_are_test_only_and_exact():
    dev = _pins("requirements-dev.txt")
    # icalendar 6.3.2 (21 Oct 2026): an independent RFC 5545 parser for tests/test_calendar_connect.py.
    assert dev == {"playwright": "1.56.0", "icalendar": "6.3.2"}
    assert "playwright" not in _pins("requirements.txt")
    assert "icalendar" not in _pins("requirements.txt")


def test_python_and_node_packages_are_pinned():
    assert (ROOT / ".python-version").read_text().strip() == "3.9.6"
    for package in ("concrete-slab-1.0.0", "stair-ontario-residential-v1"):
        folder = ROOT / "calculation-engines" / package
        manifest = json.loads((folder / "package.json").read_text())
        lock = json.loads((folder / "package-lock.json").read_text())
        assert manifest["devDependencies"]["playwright"] == "1.56.1"
        assert lock["packages"]["node_modules/playwright"]["version"] == "1.56.1"
        for spec in manifest.get("devDependencies", {}).values():
            assert re.fullmatch(r"\d+\.\d+\.\d+", spec), spec
