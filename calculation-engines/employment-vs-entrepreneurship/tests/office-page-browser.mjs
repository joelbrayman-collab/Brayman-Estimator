import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { chromium } from "../../concrete-slab-1.0.0/node_modules/playwright/index.mjs";

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const repoRoot = path.resolve(packageRoot, "../..");
const python = path.join(repoRoot, "venv/bin/python");
const serverScript = path.join(repoRoot, "tests/concrete_page_server.py");

function dollars(value) {
  return Number(String(value).replace(/[^0-9.-]/g, ""));
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

test("the contractor page runs the preserved comparison", async () => {
  const port = await freePort();
  const office = startOffice(port);
  const pageErrors = [];
  let browser;
  try {
    await office.ready;
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    await page.goto(`http://127.0.0.1:${port}/login?next=/calculators/employment-vs-entrepreneurship`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/calculators/employment-vs-entrepreneurship");
    await page.locator("#wage").waitFor();

    const employment = await page.locator("#cur").innerText();
    const business = await page.locator("#biz").innerText();
    assert.equal(await page.locator("#wage").inputValue(), "45");
    assert.match(await page.getByRole("heading", { name: "Employment", exact: true }).innerText(), /Employment/);

    await page.fill("#wage", "55");
    const higherWage = await page.locator("#cur").innerText();
    assert.ok(dollars(higherWage) > dollars(employment));

    await page.locator("[data-p='business']").click();
    await page.locator("#weeks").waitFor({ state: "visible" });
    await page.fill("#weeks", "45");
    const moreWeeks = await page.locator("#biz").innerText();
    assert.ok(dollars(moreWeeks) > dollars(business));
    await page.fill("#weeks", "40");

    await page.locator("[data-p='costs']").click();
    await page.locator("#winterCost").waitFor({ state: "visible" });
    const truck = page.locator("[data-cost]").nth(0);
    const fuel = page.locator("[data-cost]").nth(1);
    const beforeTruck = dollars(await page.locator("#biz").innerText());
    await truck.fill(String(Number(await truck.inputValue()) + 100));
    assert.equal(dollars(await page.locator("#biz").innerText()), beforeTruck - 100);
    await truck.fill(String(Number(await truck.inputValue()) - 100));

    const beforeFuel = dollars(await page.locator("#biz").innerText());
    await fuel.fill(String(Number(await fuel.inputValue()) + 100));
    assert.equal(dollars(await page.locator("#biz").innerText()), beforeFuel - 100);
    await fuel.fill(String(Number(await fuel.inputValue()) - 100));

    const beforeWinter = dollars(await page.locator("#biz").innerText());
    await page.fill("#winterCost", "100");
    assert.equal(dollars(await page.locator("#biz").innerText()), beforeWinter - 100);
    await page.fill("#winterCost", "0");

    const tools = page.locator("#tools");
    const beforeTools = dollars(await page.locator("#biz").innerText());
    await tools.fill(String(Number(await tools.inputValue()) + 100));
    assert.equal(dollars(await page.locator("#biz").innerText()), beforeTools - 100);
    await tools.fill(String(Number(await tools.inputValue()) - 100));

    await page.locator("[data-p='market']").click();
    await page.locator("#helper").waitFor({ state: "visible" });
    const solo = await page.locator("#biz").innerText();
    await page.selectOption("#helper", "yes");
    const withHelper = await page.locator("#biz").innerText();
    assert.notEqual(withHelper, solo);
    await page.fill("#hw", "30");
    assert.ok(dollars(await page.locator("#biz").innerText()) < dollars(withHelper));
    await page.selectOption("#helper", "no");

    await page.locator("[data-p='today']").click();
    await page.locator("#wage").waitFor({ state: "visible" });
    await page.locator("#wage").evaluate((field) => {
      field.value = "abc";
      field.dispatchEvent(new Event("input", { bubbles: true }));
    });
    const refused = await page.locator("#cur").innerText();
    await page.fill("#wage", "0");
    assert.equal(await page.locator("#cur").innerText(), refused);
    await page.fill("#wage", "45");
    assert.equal(await page.locator("#cur").innerText(), employment);

    const formLayout = await page.evaluate(() => {
      const wage = document.getElementById("wage").getBoundingClientRect();
      return {
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        wageWidth: wage.width,
        wageRight: wage.right,
      };
    });
    assert.equal(formLayout.innerWidth, 390);
    assert.ok(formLayout.scrollWidth <= formLayout.innerWidth + 1);
    assert.ok(formLayout.wageWidth > 40);
    assert.ok(formLayout.wageRight <= formLayout.innerWidth + 1);

    await page.getByRole("button", { name: "RESULTS" }).click();
    await page.locator("#results.on").waitFor();
    const results = await page.locator("#results").innerText();
    assert.match(results, /break-even|employment economic value/i);
    const resultLayout = await page.evaluate(() => {
      const resultsBox = document.getElementById("results").getBoundingClientRect();
      const bar = document.getElementById("prog").getBoundingClientRect();
      return {
        innerWidth: window.innerWidth,
        scrollWidth: document.documentElement.scrollWidth,
        resultsRight: resultsBox.right,
        barWidth: bar.width,
      };
    });
    process.stderr.write(`${JSON.stringify({ formLayout, resultLayout })}\n`);
    assert.ok(resultLayout.scrollWidth <= resultLayout.innerWidth + 1);
    assert.ok(resultLayout.resultsRight <= resultLayout.innerWidth + 1);
    assert.ok(resultLayout.barWidth > 100);
    assert.deepEqual(pageErrors, []);
  } finally {
    if (browser) await browser.close();
    office.child.kill("SIGKILL");
    office.child.stdout.destroy();
    office.child.stderr.destroy();
  }
});
