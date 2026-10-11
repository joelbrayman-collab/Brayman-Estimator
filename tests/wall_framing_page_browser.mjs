import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { chromium } from "../calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const python = path.join(repoRoot, "venv/bin/python");
const serverScript = path.join(repoRoot, "tests/concrete_page_server.py");

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

test("the contractor calculates a straight wall and sees the elevation", async () => {
  const port = await freePort();
  const office = startOffice(port);
  const pageErrors = [];
  let browser;
  try {
    await office.ready;
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${port}/login?next=/calculators/wall-framing`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/calculators/wall-framing");

    await page.fill("#length_ft", "10");
    await page.fill("#height_ft", "8");
    await page.fill("#spacing_in", "16");
    await page.fill("#stud_size", "2x4");
    await page.fill("#top_plate_count", "2");
    await page.fill("#bottom_plate_count", "1");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-stud-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "9 studs");
    assert.equal(await page.locator("[data-stud-lineal]").innerText(), "72 lineal feet of studs");
    assert.equal(await page.locator("[data-top-plate-lineal]").innerText(), "20 lineal feet of top plates");
    assert.equal(await page.locator("[data-bottom-plate-lineal]").innerText(), "10 lineal feet of bottom plates");
    assert.equal(await page.locator("[data-total-lineal]").innerText(), "102 total lineal feet");
    assert.equal(await page.locator("[data-gross-area]").innerText(), "80 square feet gross wall area");
    assert.match(await page.locator("[data-short-spacing]").innerText(), /8 in/);
    assert.equal(await page.locator(".stud").count(), 9);

    await page.fill("#stud_size", "2x6");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-stud-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "9 studs");
    assert.match(await page.locator("[data-wall-elevation]").innerText(), /2x6/);

    await page.fill("#spacing_in", "24");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-stud-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "6 studs");
    assert.equal(await page.locator("[data-short-spacing]").count(), 0);

    await page.fill("#length_ft", "abc");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[role='alert']").waitFor();
    assert.match(await page.locator("[role='alert']").innerText(), /greater than zero/);
    assert.equal(await page.locator("[data-wall-framing-result]").count(), 0);

    await page.fill("#length_ft", "10");
    await page.fill("#spacing_in", "16");
    await page.fill("#top_plate_count", "3");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-stud-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "9 studs");
    assert.equal(await page.locator("[data-top-plate-lineal]").innerText(), "30 lineal feet of top plates");

    const layout = await page.evaluate(() => {
      const elevation = document.querySelector("[data-wall-elevation]");
      const box = elevation.getBoundingClientRect();
      return {
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        elevationRight: box.right,
        elevationWidth: box.width,
      };
    });
    assert.equal(pageErrors.length, 0, pageErrors.join("\n"));
    assert.equal(layout.innerWidth, 390);
    assert.ok(layout.scrollWidth <= 390, JSON.stringify(layout));
    assert.ok(layout.elevationRight <= 390, JSON.stringify(layout));
    assert.ok(layout.elevationWidth > 200, JSON.stringify(layout));
    console.error(JSON.stringify(layout));
  } finally {
    if (browser) await browser.close();
    office.child.kill("SIGKILL");
    office.child.stdout.destroy();
    office.child.stderr.destroy();
  }
});
