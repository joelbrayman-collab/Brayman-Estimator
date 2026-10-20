// Release evidence for the Supplier PRO Desk (Joel, 20 Oct 2026): a walk-in quotation from sketch to an
// order-ready package, on desktop and phone, in Google Chrome. Local office on a temporary database
// (tests/pro_desk_page_server.py), synthetic store, customer and prices only.
// EVIDENCE_SHOTS=<folder> also saves screenshots of each step; the timed walk prints its duration.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const SKETCH = path.join(REPO, "tests/fixtures/pro_desk/synthetic-sketch.png");

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/pro_desk_page_server.py")], {
    cwd: REPO, env: { ...process.env, PRO_DESK_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("PRO Desk office did not start\n" + out)), 90000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("PRO Desk office exited\n" + out)); }
      setTimeout(poll, 50);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => { await browser?.close(); server?.kill(); });

async function session(width, height, [email, password], loginPath = "/supplier/login") {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  await pg.goto(`${base}${loginPath}`);
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await pg.click("button[type=submit]");
  await pg.waitForLoadState();
  return { ctx, pg, errors };
}
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function shot(pg, name, full = false) {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: full });
}
async function shotOf(pg, selector, name) {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.locator(selector).screenshot({ path: path.join(SHOTS, `${name}.png`) });
}

async function fillBuilding(pg, ref) {
  for (const [key, value] of Object.entries(ref)) {
    const field = pg.locator(`[name="${key}"]`);
    if (!(await field.count())) continue;
    const tag = await field.evaluate((el) => el.tagName);
    if (tag === "SELECT") await field.selectOption(value); else await field.fill(value);
  }
}

async function walk(width, height, label) {
  const started = Date.now();
  const { ctx, pg, errors } = await session(width, height, facts.store);
  const sid = facts.supplier_id;
  await pg.goto(`${base}/supplier/${sid}/pro-desk/`);
  await shot(pg, `${label}-01-pro-desk`);
  await pg.click("[data-new-walk-in]");
  await pg.fill("[name=customer_name]", `Synthetic Farmer ${label}`);
  await pg.fill("[name=customer_phone]", "613-555-0101");
  await pg.fill("[name=customer_email]", "joel.brayman@gmail.com");
  await pg.fill("[name=customer_town]", "Winchester");
  await pg.check("[name=consent_email]");
  await pg.check("[name=demo_synthetic]");
  await shot(pg, `${label}-02-customer`);
  await pg.click("button:has-text('Start the quotation')");
  await pg.waitForURL(/pro-desk\/\d+/);
  const quoteUrl = pg.url().split("#")[0];
  await pg.setInputFiles("[name=sketch]", SKETCH);
  await pg.click("button:has-text('Keep the sketch')");
  await pg.waitForLoadState();
  assert.equal(await pg.locator("[data-sketch]").count(), 1);
  await shotOf(pg, "#sketch", `${label}-03-sketch`);
  await fillBuilding(pg, facts.reference);
  await shotOf(pg, "#building", `${label}-04-building`);
  await pg.click("button:has-text('Confirm the building')");
  await pg.waitForLoadState();
  await pg.locator("[data-drawing-sheet='1']").evaluate((img) => img.complete || new Promise((r) => (img.onload = r)));
  await pg.locator("[data-drawing-sheet='2']").evaluate((img) => img.complete || new Promise((r) => (img.onload = r)));
  await shotOf(pg, "#drawing", `${label}-05-drawing`);
  await shotOf(pg, "#materials", `${label}-06-materials`);
  // Trusses: the store has no truss price; the truss manufacturer quotes them.
  const truss = pg.locator("[data-price-line^='CAL-OB-TRUSS']");
  await truss.locator("summary:has-text('Leave out')").click();
  await truss.locator("[name=exclude_reason]").fill("Truss quote to follow from the truss manufacturer");
  await truss.locator("button:has-text('Leave out')").click();
  await pg.waitForLoadState();
  await shotOf(pg, "#pricing", `${label}-07-pricing`);
  assert.equal(await pg.locator("[data-blockers]").count(), 0, "nothing left open before issue");
  await shotOf(pg, "#quotation", `${label}-08-totals`);
  await pg.click("[data-issue]");
  await pg.waitForLoadState();
  const total = await pg.locator("[data-total]").getAttribute("data-total");
  assert.ok(Number(total) > 0, total);
  const pdf = await ctx.request.get(`${quoteUrl}/quotation.pdf`);
  assert.equal(pdf.status(), 200);
  assert.ok((await pdf.body()).subarray(0, 5).toString() === "%PDF-");
  if (SHOTS) fs.writeFileSync(path.join(SHOTS, `${label}-quotation.pdf`), await pdf.body());
  await pg.click("button:has-text('Create approval link')");
  await pg.waitForLoadState();
  const link = (await pg.locator("[data-approval-link]").innerText()).trim();
  await shotOf(pg, "#approval", `${label}-09-approval-link`);
  // The customer, on their phone, opens the link and accepts.
  const phone = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const cp = await phone.newPage();
  await cp.goto(link);
  await shot(cp, `${label}-10-customer-link`, true);
  await noSideways(cp, `${label} customer`);
  await cp.fill("[name=customer_name]", `Synthetic Farmer ${label}`);
  await cp.check("[name=agree]");
  await cp.click("button[value=accept]");
  await cp.waitForLoadState();
  assert.ok((await cp.locator("h2").first().innerText()).includes("accepted"));
  await shot(cp, `${label}-11-customer-accepted`, true);
  await phone.close();
  await pg.goto(quoteUrl);
  await pg.click("[data-order-ready]");
  await pg.waitForURL(/\/order$/);
  assert.ok(await pg.locator("[data-order-line='SYN-PANEL']").count() >= 1);
  await shot(pg, `${label}-12-order`, true);
  const csv = await ctx.request.get(`${quoteUrl}/order.csv`);
  assert.ok((await csv.text()).includes(total));
  const seconds = (Date.now() - started) / 1000;
  await noSideways(pg, label);
  assert.deepEqual(errors, []);
  await ctx.close();
  return { seconds, total, quoteUrl };
}

test("desktop: walk-in quotation, sketch to order-ready package, timed", async () => {
  const { seconds, total } = await walk(1280, 900, "desktop");
  console.log(`PRO_DESK_DESKTOP_SECONDS=${seconds.toFixed(1)} TOTAL=${total}`);
  assert.ok(seconds < 300, `took ${seconds} s`);
});

test("phone: the same walk on a 390 px phone, no sideways scrolling", async () => {
  const { seconds } = await walk(390, 844, "phone");
  console.log(`PRO_DESK_PHONE_SECONDS=${seconds.toFixed(1)}`);
});

test("another supplier and the contractor office cannot open the quotation", async () => {
  const own = await session(1280, 900, facts.store);
  await own.pg.goto(`${base}/supplier/${facts.supplier_id}/pro-desk/`);
  const href = await own.pg.locator("[data-quote] a").first().getAttribute("href");
  await own.ctx.close();
  const rival = await session(1280, 900, facts.rival);
  assert.equal((await rival.ctx.request.get(`${base}${href}`)).status(), 404);
  assert.equal((await rival.ctx.request.get(`${base}${href.replace(`/supplier/${facts.supplier_id}/`, `/supplier/${facts.rival_id}/`)}`)).status(), 404);
  await rival.ctx.close();
  const office = await session(1280, 900, ["office@example.com", "office-test-password"], "/login");
  assert.equal((await office.ctx.request.get(`${base}${href}`)).status(), 403);
  await office.ctx.close();
});
