// Screenshots for the Field Crew lesson "Installing and Using Useful Calculators" (Joel, 22 Oct 2026;
// app/training/useful_calculators_lesson.py).
//
// Starts the local training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on, the
// synthetic training company). Kevin (Field-only crew) does what the lesson teaches on an iPhone-sized screen
// (390 x 844, touch): the dashboard in Safari signed out, the Useful Calculators sign-in, the dashboard signed in
// with the Office only cards, the Footing calculator with its result, and the way back to the list. The Share
// sheet and the Home Screen are the iPhone's own screens and are not pictured. Each picture is saved to
// app/static/training/shots/f01-uc-<name>.png. Any response of 500 or more, a page JavaScript error, sideways
// scrolling, or money on a picture fails it. Synthetic data only.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium \
//      node --test --test-concurrency=1 tools/training/capture_useful_calculators_shots.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "../release/evidence_common.mjs";

const SHOTS = path.join(REPO, "app/static/training/shots");
const PHONE = { width: 390, height: 844 };
const PY = path.join(REPO, "venv/bin/python");
// Money words. ("estimate" is not checked here: the existing calculator pages say "These quantities are not on
// an estimate", which tells the crew nothing confidential.)
const MONEY = [/\$\s?\d/, /\bprice/i, /\bcost/i, /margin/i, /markup/i, /invoice/i, /labour rate/i];
let browser, server, base, facts, ctx, pg;
const serverErrors = [];
const pageErrors = [];
const saved = [];

before(async () => {
  const port = await freePort();
  server = spawn(PY, [path.join(REPO, "tests/training_page_server.py")], {
    cwd: REPO, env: { ...process.env, TRAINING_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("training site did not start\n" + out)), 240000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("training site exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
  ctx = await browser.newContext({ viewport: PHONE, isMobile: true, hasTouch: true, deviceScaleFactor: 1 });
  ctx.setDefaultTimeout(15000);
  pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
});
after(async () => {
  await ctx?.close().catch(() => {});
  await browser?.close();
  server?.kill();
  console.log(`USEFUL_CALCULATORS_SHOTS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
  for (const name of saved) console.log(`SHOT ${name}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

async function go(url) {
  await pg.goto(`${base}${url}`);
  await pg.waitForLoadState();
}
async function submit(locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
async function shot(name, focus) {
  assert.match(name, /^f01-uc-[a-z-]+$/);
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${name}: page scrolls sideways by ${over}px`);
  const text = await pg.locator("body").innerText();
  for (const m of MONEY) assert.doesNotMatch(text, m, `${name}: shows ${m}`);
  if (focus) await focus.first().evaluate((e) => e.scrollIntoView({ block: "center" }));
  else await pg.evaluate(() => window.scrollTo(0, 0));
  await pg.waitForTimeout(200);
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`) });
  saved.push(`${name}.png`);
}

test("Safari: the dashboard signed out", async () => {
  await go("/useful-calculators/");
  assert.equal(await pg.locator('[data-uc-dashboard="signed_out"]').count(), 1);
  assert.equal(await pg.locator('link[rel="manifest"]').getAttribute("href"), "/static/useful-calculators/manifest.webmanifest");
  await shot("f01-uc-safari");
});

test("Sign in, back to the dashboard", async () => {
  await submit(pg.locator("[data-uc-sign-in]"));
  assert.match(new URL(pg.url()).pathname, /^\/useful-calculators\/sign-in$/);
  await pg.fill("input[name=email]", facts.people.kevin.email);
  await pg.fill("input[name=password]", "Synthetic-kevin-training-1");
  await shot("f01-uc-sign-in");
  await submit(pg.locator("[data-uc-sign-in-form] button[type=submit]"));
  assert.equal(new URL(pg.url()).pathname, "/useful-calculators/");
  assert.equal(await pg.locator('[data-uc-dashboard="field_only"]').count(), 1);
  assert.equal(await pg.locator('[data-uc-state="open"]').count(), 9);
  await shot("f01-uc-dashboard", pg.locator('[data-uc-calc="employment"]'));
});

test("Footing calculator with a result", async () => {
  await submit(pg.locator('[data-uc-calc="footing"]'));
  assert.equal(new URL(pg.url()).pathname, "/useful-calculators/footing");
  await pg.fill("#footing_length_1", "20");
  await pg.fill("#footing_width_1", "2");
  await pg.fill("#footing_thickness_1", "8");
  await pg.fill("#waste_percent", "0");
  await submit(pg.locator('[data-trade-form] button[value="calculate"]'));
  const result = await pg.locator('[data-trade-result="footing"]').innerText();
  assert.match(result, /Concrete 0\.988 yd³/);
  assert.match(result, /26\.67 ft³/);
  await shot("f01-uc-calculator", pg.locator('[data-trade-result="footing"]'));
});

test("Return to the dashboard", async () => {
  await shot("f01-uc-return");
  await submit(pg.locator("[data-uc-back]"));
  assert.equal(new URL(pg.url()).pathname, "/useful-calculators/");
});
