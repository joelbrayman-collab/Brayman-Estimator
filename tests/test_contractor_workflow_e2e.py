"""V1 internal acceptance: the contractor workflow end to end in Chrome (tests/e2e/contractor_workflow.mjs).

Runs with the repository's supported browser setup (locked Node Playwright, Google Chrome), against
a local office built by the real migrations. Synthetic data only; no hosted database is touched.
"""

import shutil
from pathlib import Path

from tests.browser_process import run_node_browser_test

ROOT = Path(__file__).resolve().parents[1]


def test_contractor_estimates_a_footing_job_from_sign_in_to_an_issued_proposal():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    result = run_node_browser_test(
        [node, "--test", "--test-force-exit", str(ROOT / "tests" / "e2e" / "contractor_workflow.mjs")],
        cwd=ROOT,
        timeout=600,
    )
    assert result.returncode == 0, result.stdout + result.stderr
