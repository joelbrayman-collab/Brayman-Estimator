"""Guided Estimating in a real browser, desktop and iPhone size (tools/release/evidence_guided_estimating.mjs).

The same walk the release gate runs: New Project → scope (the 14 New Home choices) → workflow → an internal stage
through its calculator and the estimate review → subcontracted stages with quotes → missing costs → Save & Exit
and Resume → the internal cost estimate → pricing gate → the three calculator choices with Cancel → phone
layouts → Field-only crew and another company kept out. Synthetic data only.
"""

import os
import shutil
from pathlib import Path

from tests.browser_process import run_node_browser_test

ROOT = Path(__file__).resolve().parents[1]


def test_guided_estimating_browser_walk():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    env = dict(os.environ, EVIDENCE_REPO=str(ROOT))
    result = run_node_browser_test(
        [node, "--test", "--test-force-exit", "--test-concurrency=1",
         str(ROOT / "tools" / "release" / "evidence_guided_estimating.mjs")],
        cwd=ROOT / "tools" / "release", timeout=900, env=env,
    )
    assert result.returncode == 0, result.stdout[-6000:] + result.stderr[-3000:]
    assert "# fail 0" in result.stdout or "ℹ fail 0" in result.stdout
