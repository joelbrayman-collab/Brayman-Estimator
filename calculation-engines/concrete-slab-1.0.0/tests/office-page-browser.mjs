import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const repoRoot = path.resolve(packageRoot, "../..");
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
    const timer = setTimeout(() => {
      reject(new Error(`office page did not start\n${output}`));
    }, 20000);
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
  return {
    child,
    ready,
    output: () => output,
  };
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

async function shownResult(page) {
  const result = page.locator("[data-concrete-result]");
  await result.waitFor({ state: "visible" });
  return result.innerText();
}

test("the contractor page Calculate button matches the original fixtures", async () => {
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
    await page.goto(`http://127.0.0.1:${port}/login?next=/calculators/concrete`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL(`**/calculators/concrete`);

    const collision = await page.evaluate(() => ({
      controlCount: typeof document.querySelector("[data-concrete-calculator]").elements.length,
      lengthField: document.getElementById("length").tagName,
    }));
    assert.equal(collision.controlCount, "number");
    assert.equal(collision.lengthField, "INPUT");

    // Metric thickness and edge values are the fixture metre inputs in the
    // page's millimetre fields. 0.1524 m is 152.4 mm. The formula is unchanged.
    const cases = [
      {
        name: "standard imperial",
        variant: "standard",
        system: "imperial",
        length: "40",
        width: "20",
        thickness: "6",
        waste: "0",
        total: "14.815",
        unit: "yd3",
      },
      {
        name: "standard metric",
        variant: "standard",
        system: "metric",
        length: "12.192",
        width: "6.096",
        thickness: "152.4",
        waste: "0",
        total: "11.327",
        unit: "m3",
      },
      {
        name: "thickened edge imperial",
        variant: "thickened_edge",
        system: "imperial",
        length: "40",
        width: "20",
        thickness: "6",
        edgeWidth: "2",
        edgeDepth: "12",
        waste: "5",
        total: "24.267",
        unit: "yd3",
      },
      {
        name: "thickened edge metric",
        variant: "thickened_edge",
        system: "metric",
        length: "12.192",
        width: "6.096",
        thickness: "152.4",
        edgeWidth: "609.6",
        edgeDepth: "304.8",
        waste: "5",
        total: "18.553",
        unit: "m3",
      },
    ];

    for (const item of cases) {
      await page.selectOption("#variant", item.variant);
      await page.selectOption("#measurement_system", item.system);
      if (item.variant === "thickened_edge") {
        await page.locator("[data-concrete-edge]").waitFor({ state: "visible" });
        await page.fill("#edge_width", item.edgeWidth);
        await page.fill("#edge_depth", item.edgeDepth);
      }
      await page.fill("#length", item.length);
      await page.fill("#width", item.width);
      await page.fill("#slab_thickness", item.thickness);
      await page.fill("#waste_percent", item.waste);
      await page.getByRole("button", { name: "Calculate" }).click();
      const text = await shownResult(page);
      assert.match(text, new RegExp(`Total concrete\\s+${item.total}\\s+${item.unit}`), item.name);
      assert.match(text, new RegExp(item.variant), item.name);
      assert.match(text, new RegExp(item.system), item.name);
      const layout = await page.evaluate(() => {
        const table = document.querySelector("[data-concrete-result] table");
        const box = table.getBoundingClientRect();
        const form = document.querySelector("[data-concrete-calculator]").getBoundingClientRect();
        let widest = "";
        let widestRight = 0;
        document.querySelectorAll("body *").forEach((node) => {
          const rect = node.getBoundingClientRect();
          if (rect.width > 0 && rect.right > widestRight) {
            widestRight = rect.right;
            widest = `${node.tagName}.${node.className}`;
          }
        });
        return {
          scrollWidth: document.documentElement.scrollWidth,
          innerWidth: window.innerWidth,
          tableRight: box.right,
          tableLeft: box.left,
          formRight: form.right,
          formLeft: form.left,
          widest,
          widestRight,
          lengthUsable: document.getElementById("length").getBoundingClientRect().width > 40,
        };
      });
      assert.ok(layout.formLeft >= 0 && layout.formRight <= layout.innerWidth + 1, item.name);
      assert.ok(layout.tableLeft >= 0 && layout.tableRight <= layout.innerWidth + 1, item.name);
      assert.equal(layout.lengthUsable, true, item.name);
    }

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: "/tmp/concrete-page-mobile-top.png" });
    await page.locator("[data-concrete-result]").scrollIntoViewIfNeeded();
    await page.screenshot({ path: "/tmp/concrete-page-mobile-result-view.png" });
    await page.screenshot({ path: "/tmp/concrete-page-mobile-result.png", fullPage: true });

    await page.fill("#length", "abc");
    await page.getByRole("button", { name: "Calculate" }).click();
    const error = page.locator("[data-concrete-error]");
    await error.waitFor({ state: "visible" });
    assert.equal(await error.innerText(), "length must be a decimal number.");
    assert.equal(await page.locator("[data-concrete-result]").isHidden(), true);
    await page.screenshot({ path: "/tmp/concrete-page-mobile-error.png", fullPage: true });

    await page.fill("#length", "40");
    await page.selectOption("#variant", "standard");
    await page.selectOption("#measurement_system", "imperial");
    await page.fill("#width", "20");
    await page.fill("#slab_thickness", "6");
    await page.fill("#waste_percent", "0");
    await page.getByRole("button", { name: "Calculate" }).click();
    const recovered = await shownResult(page);
    assert.match(recovered, /Total concrete\s+14\.815\s+yd3/);
    assert.deepEqual(pageErrors, []);
  } finally {
    if (browser) await browser.close();
    office.child.kill("SIGTERM");
  }
});
