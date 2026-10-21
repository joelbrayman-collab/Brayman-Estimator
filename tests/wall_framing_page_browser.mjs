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
    // Updated deliberately (Joel, 21 Oct 2026 authorized): a stud is the wall height less the plates,
    // 96 − 3 × 1.5 = 91.5 in = 7.625 ft. Studs 9 × 7.625 = 68.625 lf (was 72); total 98.625 (was 102).
    assert.equal(await page.locator("[data-stud-length]").innerText(), "Stud length 91.5 in (8 ft wall less 3 plates at 1.5 in)");
    assert.equal(await page.locator("[data-stud-lineal]").innerText(), "68.625 lineal feet of studs");
    assert.equal(await page.locator("[data-top-plate-lineal]").innerText(), "20 lineal feet of top plates");
    assert.equal(await page.locator("[data-bottom-plate-lineal]").innerText(), "10 lineal feet of bottom plates");
    assert.equal(await page.locator("[data-total-lineal]").innerText(), "98.625 total lineal feet");
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

    await page.fill("#stud_size", "2x4");
    await page.fill("#top_plate_count", "2");
    await page.selectOption("#opening_type_1", "door");
    await page.fill("#opening_width_in_1", "32");
    await page.fill("#opening_height_ft_1", "7");
    await page.fill("#opening_position_in_1", "40");
    await page.fill("#opening_sill_ft_1", "");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-remaining-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "9 original layout studs");
    assert.equal(await page.locator("[data-remaining-count]").innerText(), "7 full-height studs");
    // Updated deliberately (Joel, 21 Oct 2026 authorized): 7 × 7.625 ft = 53.375 (was 56).
    assert.equal(await page.locator("[data-stud-lineal]").innerText(), "53.375 lineal feet of full-height studs");
    assert.equal(await page.locator("p[data-opening-positions]").innerText(), "Opening positions 48 in, 64 in");
    assert.equal(await page.locator("[data-top-plate-lineal]").innerText(), "20 lineal feet of top plates");
    assert.equal(await page.locator("[data-gross-area]").innerText(), "80 square feet gross wall area");
    // 53.375 + 30 plates = 83.375 (was 86).
    assert.equal(await page.locator("[data-total-lineal]").innerText(), "83.375 total lineal feet");
    const doorSvg = page.locator("[data-wall-elevation] svg");
    assert.equal(await doorSvg.getAttribute("data-stud-positions"), "0,16,32,48,64,80,96,112,120");
    assert.equal(await doorSvg.getAttribute("data-opening-positions"), "48,64");
    assert.equal(await doorSvg.getAttribute("data-full-height-positions"), "0,16,32,80,96,112,120");
    assert.equal(await page.locator("[data-opening-type='door']").getAttribute("data-sill"), "0");
    assert.equal(await page.locator(".stud").count(), 9);
    assert.equal(await page.locator(".opening-station").count(), 2);

    await page.selectOption("#opening_type_2", "window");
    await page.fill("#opening_width_in_2", "16");
    await page.fill("#opening_height_ft_2", "2");
    await page.fill("#opening_position_in_2", "48");
    await page.fill("#opening_sill_ft_2", "3");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[role='alert']").waitFor();
    assert.match(await page.locator("[role='alert']").innerText(), /overlap/);
    assert.equal(await page.locator("[data-wall-framing-result]").count(), 0);

    await page.fill("#opening_position_in_2", "72");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("p[data-opening-positions]").waitFor();
    assert.match(await page.locator("p[data-opening-positions]").innerText(), /48 in, 64 in, 80 in/);

    await page.selectOption("#opening_type_2", "");
    await page.fill("#opening_width_in_2", "");
    await page.fill("#opening_height_ft_2", "");
    await page.fill("#opening_position_in_2", "");
    await page.fill("#opening_sill_ft_2", "");
    await page.selectOption("#opening_type_1", "window");
    await page.fill("#opening_width_in_1", "32");
    await page.fill("#opening_height_ft_1", "3");
    await page.fill("#opening_position_in_1", "16");
    await page.fill("#opening_sill_ft_1", "3");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-remaining-count]").waitFor();
    assert.equal(await page.locator("[data-remaining-count]").innerText(), "8 full-height studs");
    assert.equal(await page.locator("p[data-opening-positions]").innerText(), "Opening positions 32 in");
    assert.equal(await page.locator("[data-opening-type='window']").getAttribute("data-sill"), "3");
    assert.match(await page.locator("[data-wall-framing-result]").innerText(), /unless you enter it/);

    await page.fill("#opening_height_ft_1", "5");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-opening-type='window']").waitFor();
    assert.equal(await page.locator("[data-opening-type='window']").getAttribute("data-height"), "5");
    assert.equal(await page.locator("[data-opening-type='window']").getAttribute("data-sill"), "3");

    await page.fill("#opening_height_ft_1", "6");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[role='alert']").waitFor();
    assert.match(await page.locator("[role='alert']").innerText(), /wall height/);
    assert.equal(await page.locator("[data-wall-framing-result]").count(), 0);

    await page.fill("#opening_height_ft_1", "3");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-remaining-count]").waitFor();
    assert.equal(await page.locator("[data-remaining-count]").innerText(), "8 full-height studs");

    await page.selectOption("#opening_type_1", "");
    await page.fill("#opening_width_in_1", "");
    await page.fill("#opening_height_ft_1", "");
    await page.fill("#opening_position_in_1", "");
    await page.fill("#opening_sill_ft_1", "");
    await page.selectOption("#corner_end_1", "left");
    await page.fill("#corner_count_1", "2");
    await page.fill("#corner_stud_size_1", "2x6");
    await page.fill("#corner_length_ft_1", "8");
    await page.selectOption("#member_kind_1", "king");
    await page.fill("#member_count_1", "2");
    await page.fill("#member_length_ft_1", "8");
    await page.selectOption("#member_kind_2", "header");
    await page.fill("#member_count_2", "1");
    await page.fill("#member_length_ft_2", "3");
    await page.getByRole("button", { name: "Calculate" }).click();
    await page.locator("[data-stud-count]").waitFor();
    assert.equal(await page.locator("[data-stud-count]").innerText(), "9 studs");
    // Updated deliberately (Joel, 21 Oct 2026 authorized): 68.625 studs + 30 plates + 16 corners
    // + 16 kings + 3 header = 133.625 (was 72 + 65 = 137).
    assert.equal(await page.locator("[data-stud-lineal]").innerText(), "68.625 lineal feet of studs");
    assert.equal(await page.locator("[data-total-lineal]").innerText(), "133.625 total lineal feet");
    assert.match(await page.locator("[data-corner]").innerText(), /Left corner/);
    assert.match(await page.locator("[data-corner]").innerText(), /16 ft/);
    assert.match(await page.locator("[data-extra-member]").first().innerText(), /King studs/);

    const extended = await page.evaluate(() => {
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
    assert.equal(extended.innerWidth, 390);
    assert.ok(extended.scrollWidth <= 390, JSON.stringify(extended));
    assert.ok(extended.elevationRight <= 390, JSON.stringify(extended));
    console.error(JSON.stringify(layout));
    console.error(JSON.stringify(extended));
  } finally {
    if (browser) await browser.close();
    office.child.kill("SIGKILL");
    office.child.stdout.destroy();
    office.child.stderr.destroy();
  }
});
