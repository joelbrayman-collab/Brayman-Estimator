"""The confidential Family 05 master stays outside the repository, and missing-master failures are named as such.

Joel, 20 Oct 2026: report the dependency clearly; do not skip, disable or weaken the contract tests.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.conftest import FAMILY_05_DEPENDENT_FILES

ROOT = Path(__file__).resolve().parents[1]
MASTER_NAME = "05_Brayman_Ontario_Construction_Contract_COMMERCIAL_DRAFT_MASTER_V1.docx"


def test_every_listed_dependent_file_exists():
    missing = sorted(name for name in FAMILY_05_DEPENDENT_FILES if not (ROOT / "tests" / name).is_file())
    assert not missing, missing


def test_files_that_read_the_master_directly_are_listed():
    readers = {p.name for p in (ROOT / "tests").glob("test_*.py") if p.name != Path(__file__).name and (
               "DEFAULT_FAMILY_05_MASTER_PATH.read_bytes" in p.read_text(encoding="utf-8")
               or "DEFAULT_FAMILY_05_MASTER_PATH.is_file" in p.read_text(encoding="utf-8"))}
    assert readers <= FAMILY_05_DEPENDENT_FILES, sorted(readers - FAMILY_05_DEPENDENT_FILES)


def test_the_master_is_never_in_the_repository():
    if not (ROOT / ".git").exists():
        tracked = [p for p in ROOT.rglob("*.docx") if p.name == MASTER_NAME]
    else:
        out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        tracked = [line for line in out.splitlines() if line.endswith(MASTER_NAME)]
    assert tracked == []


def test_the_contract_tests_are_not_skipped_when_the_master_is_missing():
    for name in FAMILY_05_DEPENDENT_FILES:
        source = (ROOT / "tests" / name).read_text(encoding="utf-8")
        assert "skipif" not in source and "importorskip" not in source and "pytest.skip(" not in source, name
