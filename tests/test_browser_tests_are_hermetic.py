"""Browser tests must not depend on the public internet (17 Nov 2026).

Every page links Google Fonts and jsDelivr CSS and the walks wait for the page "load" event. On 17 Nov the same
commit passed gate run ai4-160327 and then stopped gate run ai5-172241 (and earlier ai4-105304): the walks stalled about
300 s, or ran to their 600/900 s limit, while the Mac's network was slow. Every browser the tests launch now fails
outside hosts at once, so the result no longer depends on the network."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from tests.browser_process import HERMETIC_CHROME_ARGS, HERMETIC_PRELOAD, run_node_browser_test

ROOT = Path(__file__).resolve().parents[1]

PROBE = r"""
import path from "node:path";
import { pathToFileURL } from "node:url";
const { chromium } = await import(pathToFileURL(path.join(process.env.PROBE_REPO,
  "calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs")).href);
const exe = process.env.EVIDENCE_EXECUTABLE;
const browser = await chromium.launch(exe ? { executablePath: exe, headless: true } : { channel: "chrome", headless: true });
const page = await browser.newPage();
const failures = [];
page.on("requestfailed", (r) => failures.push({ url: r.url(), error: r.failure() && r.failure().errorText }));
const started = Date.now();
await page.setContent('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans">'
  + '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"><p>x</p>');
await page.waitForLoadState("load");
console.log("PROBE " + JSON.stringify({ ms: Date.now() - started, failures }));
await browser.close();
"""


def test_every_python_launched_browser_is_hermetic():
    offenders = []
    for path in sorted((ROOT / "tests").glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        for number, line in enumerate(path.read_text(encoding="utf8").splitlines(), 1):
            if re.search(r"chromium\.launch\(", line) and "HERMETIC_CHROME_ARGS" not in line:
                offenders.append(f"{path.name}:{number}")
    assert not offenders, offenders


def test_the_node_browser_harness_preloads_the_hermetic_network_rule():
    text = (ROOT / "tests" / "browser_process.py").read_text(encoding="utf8")
    assert '"--import", HERMETIC_PRELOAD' in text
    assert os.path.isfile(HERMETIC_PRELOAD)
    assert "--no-proxy-server" in HERMETIC_CHROME_ARGS
    assert any("MAP * ~NOTFOUND, EXCLUDE 127.0.0.1" in a for a in HERMETIC_CHROME_ARGS)
    for arg in HERMETIC_CHROME_ARGS:
        assert arg in Path(HERMETIC_PRELOAD).read_text(encoding="utf8")


def test_a_node_browser_cannot_reach_the_public_internet_and_the_page_still_loads_at_once():
    node = shutil.which("node") or "/opt/homebrew/bin/node"
    result = run_node_browser_test(
        [node, "--input-type=module", "-e", PROBE],
        cwd=ROOT, timeout=120, env=dict(os.environ, PROBE_REPO=str(ROOT)),
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    probe = json.loads(next(line for line in result.stdout.splitlines() if line.startswith("PROBE "))[6:])
    hosts = {re.sub(r"^https://([^/]+)/.*", r"\1", f["url"]): f["error"] for f in probe["failures"]}
    assert set(hosts) == {"fonts.googleapis.com", "cdn.jsdelivr.net"}, probe
    assert all("ERR_NAME_NOT_RESOLVED" in (e or "") for e in hosts.values()), probe
    assert probe["ms"] < 15000, probe


def test_a_node_browser_timeout_reports_what_the_machine_and_playwright_were_doing(capsys):
    """18 Nov 2026: three walks timed out with nothing to show which step hung. A timeout now reports the busiest
    processes, the load, the process tree and the last Playwright calls."""
    import pytest

    node = shutil.which("node") or "/opt/homebrew/bin/node"
    code = "console.error('pw:api    waiting for locator(#never)'); setInterval(() => {}, 1000);"
    with pytest.raises(subprocess.TimeoutExpired):
        run_node_browser_test([node, "-e", code], cwd=ROOT, timeout=4)
    report = capsys.readouterr().err
    assert "BROWSER TEST TIMED OUT after 4s" in report
    assert "--- busiest processes ---" in report and "uptime:" in report
    assert "--- last 60 Playwright/Node stderr lines ---" in report
    assert "waiting for locator(#never)" in report
