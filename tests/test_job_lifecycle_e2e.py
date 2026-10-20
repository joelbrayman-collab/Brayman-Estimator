"""V1 internal acceptance: one synthetic job through its whole life in a real browser (tests/e2e/job_lifecycle.mjs).

Office (desktop), customer and Field crew member (390 px phone) and supplier, against a local office built by
the real migrations. Proposal accepted → contract signed → work scheduled and crew assigned → concrete
request, PO and agreed delivery → Field time, observation and extra work → change order signed → walkthrough,
punch list → project closed. Synthetic data only; no hosted database is touched; mail is captured locally.
"""

import shutil
from pathlib import Path

from tests.browser_process import run_node_browser_test

ROOT = Path(__file__).resolve().parents[1]


def test_one_synthetic_job_from_estimate_to_a_closed_project():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    result = run_node_browser_test(
        [node, "--test", "--test-force-exit", str(ROOT / "tests" / "e2e" / "job_lifecycle.mjs")],
        cwd=ROOT,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout + result.stderr
