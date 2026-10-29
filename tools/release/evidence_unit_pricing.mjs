// Release evidence for Supplier Unit Pricing & Conversion (Joel, 29 Oct 2026), in a real browser — the office at
// 1280 x 900, the store on a 390 x 844 phone (touch) and at 1280 x 900 — against a local office and Supplier Hub
// built by the real migrations (tests/unit_pricing_page_server.py). Synthetic data only; everything through the
// normal pages.
//
// Takeoff measurements → the Hardie package from the template library (each component's requirement in SF, LF and
// pieces; Calibrayt's quantity only where the product's size is known; the nail boxes and sealant tubes "to confirm")
// → the store prices each item in its own POS unit on its phone (battens per lineal foot, the sealant tube with its
// own coverage, the soffit screws with its own box count) → Calibrayt converts, rounds up to whole units, extends and
// totals → the office sees the missing nail-box coverage block approval, records it with its source, takes one line
// out with a reason, approves → Sign & Send for E-Signature → the store's Sign & Confirm Order → Executed. Also: a
// store with no sign-in gets the approved PDF form (quantities only where known) and the office enters its prices.
// UNIT_SHOTS=<dir> saves the screens.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_unit_pricing.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const SHOTS = process.env.UNIT_SHOTS || "";
const DESK = { width: 1280, height: 900 };
const PHONE = { width: 390, height: 844 };
const MEASURED = { siding_sf: "1750", batten_lf: "1313", joint_lf: "200", trim_joint_lf: "600", soffit_sf: "400",
  fascia_lf: "315", corner_lf: "125", window_trim_lf: "205", door_trim_lf: "115", drip_lf: "70", freeze_lf: "125",
  jchannel_lf: "315" };
let browser, server, base, facts, shareId, screens = 0;
const serverErrors = [];
const pageErrors = [];
const sessions = {};
const W = {};

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/unit_pricing_page_server.py")], {
    cwd: REPO, env: { ...process.env, UNIT_PRICING_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("unit pricing office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("unit pricing office exited\n" + out)); }
      setTimeout(poll, 50);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`UNIT_PRICING_SCREENS=${screens} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});

async function session(key, viewport, [loginPath, [email, password]]) {
  if (sessions[key]) return sessions[key];
  const phone = viewport.width <= 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  await pg.goto(`${base}${loginPath}`);
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await Promise.all([pg.waitForNavigation(), pg.click("button[type=submit]")]);
  sessions[key] = { ctx, pg };
  return sessions[key];
}
const office = () => session("office", DESK, ["/login", facts.office]);
const storePhone = () => session("storePhone", PHONE, ["/supplier/login", facts.store]);
const storeDesk = () => session("storeDesk", DESK, ["/supplier/login", facts.store]);
const requests = () => `/projects/${facts.project_id}/supplier-requests`;
async function go(pg, url) { await pg.goto(`${base}${url}`); await pg.waitForLoadState(); }
async function press(pg, locator) { await Promise.all([pg.waitForNavigation(), locator.click()]); await pg.waitForLoadState(); }
async function flash(pg) { return (await pg.locator(".flash, .flash-stack .alert, .flash-stack").allInnerTexts()).join(" | "); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function screen(pg, name, locator = null) {
  screens += 1;
  if (!SHOTS) return;
  if (locator) await locator.first().scrollIntoViewIfNeeded().catch(() => {});
  await pg.waitForTimeout(200);
  await pg.screenshot({ path: path.join(SHOTS, `${String(screens).padStart(2, "0")}-${name}.png`), fullPage: !locator });
}
const line = (pg, key) => pg.locator(`[data-price-line="${key}"]`);
const priced = (pg, key) => pg.locator(`[data-priced-line="${key}"]`);

test("office: the Hardie package from the takeoff's measurements; Calibrayt's quantity only where the size is known", async () => {
  const { pg } = await office();
  await go(pg, requests());
  const form = pg.locator('[data-unit-template="hardie-vertical-aluminum-v2"]');
  for (const [k, v] of Object.entries(MEASURED)) await form.locator(`[name=m_${k}]`).fill(v);
  await form.locator("[name=contractor_supplier_account_id]").selectOption(String(facts.account_id));
  await screen(pg, "office-new-package", form);
  await press(pg, form.locator("[data-unit-create]"));
  assert.match(await flash(pg), /It is in their Supplier Hub now/);
  const card = pg.locator("[data-unit-pricing]").first();
  shareId = Number((await card.locator("xpath=ancestor::article").getAttribute("id")).replace("share-", ""));
  const table = card.locator("[data-unit-request]");
  assert.match(await table.locator('[data-unit-line="hpanel"]').innerText(), /1925 SF[\s\S]*61 PC[\s\S]*60\.16 rounded up/);
  assert.match(await table.locator('[data-unit-line="hbatten"]').innerText(), /1444\.3 LF[\s\S]*121 PC/);
  for (const key of ["hnails", "hcaulk", "anails", "screws"]) {
    assert.equal(await table.locator(`[data-unit-line="${key}"]`).getAttribute("data-conversion-missing"), "true", key);
    assert.match(await table.locator(`[data-unit-line="${key}"]`).innerText(), /To confirm[\s\S]*no verified product data/, key);
  }
  await noSideways(pg, "office request");
  await screen(pg, "office-request-sent", card);
});

test("store on its phone: prices each item in its own POS unit", async () => {
  const { pg } = await storePhone();
  await go(pg, `/supplier/${facts.supplier_id}/requests/${shareId}`);
  assert.match(await pg.locator("main").innerText(), /Pricing request: Hardie vertical siding/i);
  assert.doesNotMatch(await pg.locator("main").innerText(), /Elm Street|Sam Synthetic/, "no customer or job name");
  await noSideways(pg, "store phone request");
  await screen(pg, "store-phone-request", pg.locator("[data-unit-price-form]"));
  const form = pg.locator("[data-unit-price-form]");
  const keys = await form.locator("[data-price-line]").evaluateAll((rows) => rows.map((r) => r.getAttribute("data-price-line")));
  for (const key of keys) await line(pg, key).locator("[data-unit-price]").fill("10.00");
  await line(pg, "hpanel").locator("[data-unit-price]").fill("52.40");
  assert.equal(await line(pg, "hbatten").locator("[data-other-unit]").isVisible(), false, "other unit hidden until chosen");
  await line(pg, "hbatten").locator("[data-sell-unit]").selectOption("LF");
  await line(pg, "hbatten").locator("[data-unit-price]").fill("1.85");
  await line(pg, "hcaulk").locator("[data-supplier-per]").fill("30");
  await line(pg, "screws").locator("[data-supplier-qty]").fill("2");
  const valid = new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10);
  await form.locator("[name=valid_until]").fill(valid);
  await form.locator("[name=quote_number]").fill("LBS-SYN-77");
  await screen(pg, "store-phone-priced", line(pg, "hbatten"));
  await press(pg, form.locator("[data-unit-price-submit]"));
  assert.match(await flash(pg), /Quote returned to the contractor/);
  const view = pg.locator("[data-unit-priced]");
  assert.match(await priced(pg, "hbatten").innerText(), /1445 LF/);
  await noSideways(pg, "store phone returned");
  await screen(pg, "store-phone-returned", view);
});

test("office: conversion, rounding, extensions and totals; a missing conversion stops approval", async () => {
  const { pg } = await office();
  await go(pg, requests());
  const card = pg.locator(`#share-${shareId}`);
  assert.equal(await priced(pg, "hpanel").locator("[data-line-qty]").getAttribute("data-line-qty"), "61");
  assert.equal(await priced(pg, "hpanel").locator("[data-line-extension]").getAttribute("data-line-extension"), "3196.40");
  assert.equal(await priced(pg, "hbatten").locator("[data-line-qty]").getAttribute("data-line-qty"), "1445");
  assert.equal(await priced(pg, "hbatten").locator("[data-line-extension]").getAttribute("data-line-extension"), "2673.25");
  assert.match(await priced(pg, "hcaulk").innerText(), /1 TUBE = 30 LF[\s\S]*Stated by Lakeside[\s\S]*20 TUBE/);
  assert.equal(await priced(pg, "hnails").getAttribute("data-line-status"), "CONVERSION_MISSING");
  assert.equal(await priced(pg, "anails").getAttribute("data-line-status"), "CONVERSION_MISSING");
  assert.equal(await card.locator("[data-unit-approve]").count(), 0, "no Approve while a conversion is missing");
  assert.match(await card.locator("[data-unit-blockers]").innerText(), /Hardie siding nails/);
  await screen(pg, "office-priced-blocked", card.locator("[data-unit-priced]"));
  await screen(pg, "office-missing-conversion", card.locator('[data-resolve-line="hnails"]'));
  const conv = card.locator('[data-record-conversion="hnails"]');
  await conv.locator("[name=per]").fill("100");
  await conv.locator("[name=source]").fill("Synthetic manufacturer sheet (test)");
  await press(pg, conv.locator("button"));
  assert.match(await flash(pg), /Conversion recorded/);
  assert.match(await priced(pg, "hnails").innerText(), /1 BOX = 100 PC fastened[\s\S]*recorded by the contractor[\s\S]*2 BOX/);
  const out = pg.locator(`#share-${shareId} [data-exclude-line="anails"]`);
  await out.locator("[name=reason]").fill("Crew has a stock of them (synthetic)");
  await press(pg, out.locator("button"));
  assert.equal(await priced(pg, "anails").getAttribute("data-line-status"), "EXCLUDED");
  const subtotal = await pg.locator(`#share-${shareId} [data-unit-subtotal]`).getAttribute("data-unit-subtotal");
  const extensions = await pg.locator(`#share-${shareId} [data-priced-line][data-line-status=PRICED] [data-line-extension]`)
    .evaluateAll((cells) => cells.map((c) => Number(c.getAttribute("data-line-extension"))));
  assert.equal(Number(subtotal).toFixed(2), extensions.reduce((a, b) => a + b, 0).toFixed(2), "the package is the sum of its lines");
  const total = await pg.locator(`#share-${shareId} [data-unit-total]`).getAttribute("data-unit-total");
  assert.equal(Number(total).toFixed(2), (Number(subtotal) + Math.round(Number(subtotal) * 13) / 100).toFixed(2));
  await screen(pg, "office-resolved", pg.locator(`#share-${shareId} [data-unit-priced]`));
  W.subtotal = subtotal;
});

test("office: Approve, then the purchase order is signed with CaliSIGN", async () => {
  const { pg } = await office();
  await press(pg, pg.locator(`#share-${shareId} [data-unit-approve] button`));
  assert.match(await flash(pg), /Package approved/);
  assert.equal(await pg.locator(`#share-${shareId} [data-unit-approved]`).count(), 1);
  const order = pg.locator(`[data-place-order="${shareId}"]`);
  assert.match(await order.innerText(), new RegExp(`total \\$${Number(W.subtotal).toFixed(2)} before tax`));
  await order.locator("[name=delivery_window]").fill("8:00–10:00");
  await order.locator("[name=sign_consent]").check();
  await order.locator("[name=signer_name]").fill("Ben Synthetic Office");
  await screen(pg, "office-sign-and-send", order);
  await press(pg, order.locator("[data-calisign-po-send]"));
  assert.match(await flash(pg), /signed and sent to Lakeside Building Supply/);
});

test("store: Sign & Confirm Order; both sides Executed", async () => {
  const { pg } = await storeDesk();
  await go(pg, `/supplier/${facts.supplier_id}/requests/${shareId}`);
  const confirm = pg.locator("form[data-confirm-order]");
  await confirm.locator("[name=sign_consent]").check();
  await confirm.locator("[name=signer_name]").fill("Riley Synthetic");
  await press(pg, confirm.locator("[data-calisign-confirm]"));
  assert.match(await flash(pg), /signed and confirmed/);
  const { pg: o } = await office();
  await go(o, requests());
  assert.ok((await o.locator(`#share-${shareId} [data-calisign-status]`).allInnerTexts()).some((t) => /Executed/.test(t)));
  await screen(o, "office-executed", o.locator(`#share-${shareId} [data-po]`));
});

test("a store with no sign-in: the approved PDF form, then the office enters the returned prices", async () => {
  const { pg, ctx } = await office();
  await go(pg, requests());
  const form = pg.locator('[data-unit-template="hardie-vertical-aluminum-v2"]');
  for (const [k, v] of Object.entries(MEASURED)) await form.locator(`[name=m_${k}]`).fill(v);
  await form.locator("[name=contractor_supplier_account_id]").selectOption(String(facts.offline_account_id));
  await press(pg, form.locator("[data-unit-create]"));
  assert.match(await flash(pg), /has no Supplier Hub sign-in/);
  const card = pg.locator("[data-unit-pricing]").first();
  const href = await card.locator("[data-unit-form-pdf]").getAttribute("href");
  const pdf = await ctx.request.get(`${base}${href}`);
  assert.equal(pdf.status(), 200);
  assert.equal((await pdf.body()).subarray(0, 5).toString(), "%PDF-");
  const entry = card.locator("[data-unit-price-form]");
  for (const key of await entry.locator("[data-price-line]").evaluateAll((r) => r.map((x) => x.getAttribute("data-price-line")))) {
    await entry.locator(`[data-price-line="${key}"] [data-unit-price]`).fill("10.00");
  }
  for (const key of ["hnails", "hcaulk", "anails", "screws"]) await entry.locator(`[data-price-line="${key}"] [data-supplier-qty]`).fill("1");
  await entry.locator("[name=valid_until]").fill(new Date(Date.now() + 20 * 86400000).toISOString().slice(0, 10));
  await screen(pg, "office-offline-entry", entry);
  await press(pg, entry.locator("[data-unit-price-submit]"));
  assert.match(await flash(pg), /prices are recorded/);
  const newest = pg.locator("[data-unit-pricing]").first();
  assert.equal(await newest.locator("[data-unit-blockers]").count(), 0);
  assert.equal(await newest.locator("xpath=ancestor::article").locator("[data-unit-approve]").count(), 1);
  await screen(pg, "office-offline-priced", newest.locator("[data-unit-priced]"));
});

test("no server error and no page error anywhere", () => {
  assert.deepEqual(serverErrors, []);
  assert.deepEqual(pageErrors, []);
});
