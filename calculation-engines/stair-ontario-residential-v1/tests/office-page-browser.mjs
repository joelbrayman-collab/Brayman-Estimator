import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

import { createStairDiagramGeometry } from "../website-source/lib/useful-tools/stair-diagram-geometry.mjs";
import { selectRecommendedStair } from "../website-source/lib/useful-tools/stairs.mjs";
import profile from "../website-source/lib/useful-tools/profiles/ontario-residential-v1.json" with { type: "json" };

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const repoRoot = path.resolve(packageRoot, "../..");
const python = path.join(repoRoot, "venv/bin/python");
const serverScript = path.join(repoRoot, "tests/concrete_page_server.py");

function display(metres, system) {
  return system === "metric"
    ? `${(metres * 1000).toFixed(1)} mm`
    : `${(metres / 0.0254).toFixed(2)} in`;
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      server.close((error) => (error ? reject(error) : resolve(port)));
    });
  });
}

function startOffice(port) {
  const child = spawn(python, [serverScript], {
    cwd: repoRoot,
    env: { ...process.env, CONCRETE_PAGE_PORT: String(port) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  let output = "";
  child.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    output += chunk.toString();
  });
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`office page did not start\n${output}`)), 20000);
    const poll = () => {
      if (output.includes(`READY ${port}`)) {
        clearTimeout(timer);
        resolve();
        return;
      }
      if (child.exitCode !== null) {
        clearTimeout(timer);
        reject(new Error(`office page exited ${child.exitCode}\n${output}`));
        return;
      }
      setTimeout(poll, 50);
    };
    poll();
  });
  return { child, ready };
}

test("the contractor stair page uses the preserved engine and diagram", async () => {
  const port = await freePort();
  const office = startOffice(port);
  const pageErrors = [];
  let browser;
  try {
    await office.ready;
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${port}/login?next=/calculators/stairs`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/calculators/stairs");
    await page.locator(".tool-profile-badge strong").waitFor();

    await page.getByRole("button", { name: "Metric", exact: true }).click();
    await page.fill("#total-rise", "2800");
    await page.fill("#available-run", "4480");
    const metric = selectRecommendedStair(
      { totalRise: { value: 2800, unit: "mm" }, availableRun: { value: 4480, unit: "mm" } },
      profile,
    );
    const metricDiagram = createStairDiagramGeometry(metric);
    await page.locator(".tool-calculator-primary-result").getByText(`${metric.riserCount} risers`).waitFor();
    const metricText = await page.locator(".tool-calculator-results").innerText();
    assert.match(metricText, new RegExp(`Risers\\s+${metric.riserCount}`));
    assert.match(metricText, new RegExp(`Treads\\s+${metric.treadCount}`));
    assert.match(metricText, new RegExp(display(metric.riserHeightM, "metric").replace(".", "\\.")));
    assert.match(metricText, new RegExp(display(metric.treadRunM, "metric").replace(".", "\\.")));
    assert.match(metricText, /Within profile/);
    assert.equal(metric.overallStatus, "pass");
    const metricAngle = await page.locator(".stair-diagram").getAttribute("data-stair-angle");
    assert.equal(metricAngle, metricDiagram.angleDegrees.toFixed(6));
    const metricLabel = await page.locator(".stair-diagram").getAttribute("aria-label");
    assert.match(metricLabel, new RegExp(display(metric.riserHeightM, "metric").replace(".", "\\.")));
    assert.match(metricLabel, /Typical riser|Riser height/);

    await page.getByRole("button", { name: "Imperial", exact: true }).click();
    await page.fill("#total-rise", "38");
    await page.fill("#available-run", "44");
    const imperial = selectRecommendedStair(
      { totalRise: { value: 38, unit: "in" }, availableRun: { value: 44, unit: "in" } },
      profile,
    );
    const imperialDiagram = createStairDiagramGeometry(imperial);
    await page.locator(".tool-calculator-primary-result").getByText(`${imperial.riserCount} risers`).waitFor();
    const imperialAngle = await page.locator(".stair-diagram").getAttribute("data-stair-angle");
    assert.equal(imperialAngle, imperialDiagram.angleDegrees.toFixed(6));
    assert.notEqual(imperialAngle, metricAngle);
    const imperialText = await page.locator(".tool-calculator-results").innerText();
    assert.match(imperialText, new RegExp(display(imperial.riserHeightM, "imperial").replace(".", "\\.")));
    assert.equal(imperialDiagram.risers.length, imperial.riserCount);
    assert.equal(imperialDiagram.treads.length, imperial.treadCount);

    const layout = await page.evaluate(() => {
      const form = document.querySelector(".tool-calculator-form").getBoundingClientRect();
      const diagram = document.querySelector(".stair-diagram").getBoundingClientRect();
      const results = document.querySelector(".tool-calculator-results").getBoundingClientRect();
      return {
        innerWidth: window.innerWidth,
        formLeft: form.left,
        formRight: form.right,
        diagramLeft: diagram.left,
        diagramRight: diagram.right,
        diagramWidth: diagram.width,
        resultsRight: results.right,
        riseUsable: document.getElementById("total-rise").getBoundingClientRect().width > 40,
      };
    });
    assert.equal(layout.riseUsable, true);
    assert.ok(layout.formLeft >= 0 && layout.formRight <= layout.innerWidth + 1);
    assert.ok(layout.diagramLeft >= 0 && layout.diagramRight <= layout.innerWidth + 1);
    assert.ok(layout.diagramWidth > 200);
    assert.ok(layout.resultsRight <= layout.innerWidth + 1);
    await page.locator(".stair-diagram").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "/tmp/stair-page-mobile-diagram.png" });
    await page.locator("#total-rise").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "/tmp/stair-page-mobile-result.png" });

    await page.fill("#total-rise", "0");
    await page.locator(".tool-input-error").waitFor();
    assert.match(await page.locator(".tool-input-error").innerText(), /Total rise must be greater than zero/);
    assert.equal(await page.locator(".stair-diagram").count(), 0);
    await page.screenshot({ path: "/tmp/stair-page-mobile-error.png" });

    await page.fill("#total-rise", "38");
    await page.locator(".stair-diagram").waitFor();
    const recovered = await page.locator(".stair-diagram").getAttribute("data-stair-angle");
    assert.equal(recovered, imperialDiagram.angleDegrees.toFixed(6));
    assert.deepEqual(pageErrors, []);
  } finally {
    if (browser) await browser.close();
    office.child.kill("SIGTERM");
  }
});
