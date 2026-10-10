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
  const watch = (chunk) => {
    output += chunk.toString();
  };
  child.stdout.on("data", watch);
  child.stderr.on("data", watch);
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

async function waitForLogin(port) {
  let lastError = "";
  for (let attempt = 0; attempt < 50; attempt += 1) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/login`);
      if (response.status > 0) return;
    } catch (error) {
      lastError = error.message;
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`login page was not reachable: ${lastError}`);
}

async function calculate(page, fields) {
  await page.selectOption("#manufacturer_id", fields.manufacturer);
  await page.fill("#net_wall_area", fields.area);
  await page.fill("#corner_90", fields.corner90);
  await page.fill("#corner_45", fields.corner45);
  await page.getByRole("button", { name: "Calculate" }).click();
  await page.locator("[data-icf-result]").waitFor();
  return page.locator("[data-icf-result]").innerText();
}

test("the contractor ICF page uses the existing 8-inch quantities", async () => {
  const port = await freePort();
  const office = startOffice(port);
  const pageErrors = [];
  let browser;
  try {
    await office.ready;
    await waitForLogin(port);
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${port}/login?next=/calculators/wall-form`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/calculators/wall-form");
    await page.locator("#manufacturer_id").waitFor();

    const logix = await calculate(page, {
      manufacturer: "logix",
      area: "1523",
      corner90: "0",
      corner45: "0",
    });
    assert.match(logix, /Logix/);
    assert.match(logix, /8 inches/);
    assert.match(logix, /37\.623741/);
    assert.match(logix, /Concrete/);
    assert.match(logix, /These quantities are not on an estimate/);

    const fox = await calculate(page, {
      manufacturer: "fox_blocks",
      area: "5.33",
      corner90: "0",
      corner45: "0",
    });
    assert.match(fox, /Fox Blocks/);
    assert.match(fox, /0\.132/);
    assert.match(fox, /Standard forms/);

    const buildblock = await calculate(page, {
      manufacturer: "styrorail_buildblock",
      area: "5.33",
      corner90: "0",
      corner45: "0",
    });
    assert.match(buildblock, /StyroRail \/ BuildBlock/);
    assert.match(buildblock, /0\.131687/);

    const nudura = await calculate(page, {
      manufacturer: "nudura",
      area: "12",
      corner90: "0",
      corner45: "0",
    });
    assert.match(nudura, /Nudura/);
    assert.match(nudura, /0\.306/);

    const corner = await calculate(page, {
      manufacturer: "fox_blocks",
      area: "12.89",
      corner90: "1",
      corner45: "0",
    });
    assert.match(corner, /0\.277/);
    assert.match(corner, /90-degree corners/);

    const layout = await page.evaluate(() => {
      const form = document.querySelector("[data-icf-wall-calculator]");
      const result = document.querySelector("[data-icf-result]");
      const area = document.getElementById("net_wall_area");
      const box = (node) => {
        const rect = node.getBoundingClientRect();
        return { right: rect.right, width: rect.width };
      };
      return {
        innerWidth: window.innerWidth,
        form: box(form),
        result: box(result),
        area: box(area),
      };
    });
    assert.ok(layout.area.width > 40);
    assert.ok(layout.form.right <= layout.innerWidth + 1);
    assert.ok(layout.result.right <= layout.innerWidth + 1);
    await page.locator("[data-icf-result]").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "/tmp/icf-wall-mobile-result.png" });

    const missing = await calculate(page, {
      manufacturer: "styrorail_buildblock",
      area: "5.33",
      corner90: "0",
      corner45: "2",
    });
    assert.match(missing, /its coverage is not in the profile/);
    assert.match(missing, /not filled in here/);
    await page.screenshot({ path: "/tmp/icf-wall-mobile-missing.png" });

    await page.selectOption("#manufacturer_id", "logix");
    await page.fill("#net_wall_area", "abc");
    await page.fill("#corner_90", "0");
    await page.fill("#corner_45", "0");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator(".form-error").waitFor();
    const refused = await page.locator(".form-error").innerText();
    assert.match(refused, /decimal number/);
    assert.equal(await page.locator("[data-icf-result]").count(), 0);
    assert.deepEqual(pageErrors, []);
  } finally {
    if (browser) await browser.close();
    office.child.kill();
  }
});
