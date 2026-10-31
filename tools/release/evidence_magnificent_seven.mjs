// Release evidence for the Magnificent Seven everyday operations (Joel, 25 Oct 2026), in a real browser at desktop
// (1280 x 900) and iPhone size (390 x 844, touch), against a local office built by the real migrations
// (tests/magnificent_seven_server.py: owner Ben, office Suzanne, Field-only crew Kevin and Liam, another company's
// owner, the Harbour Lane job with Kevin booked today, Shop / Company Work, BMR Winchester with Darcy's Supplier Hub
// sign-in, a confirmed order due today, and a TEST QuickBooks Online company in memory — nothing reaches Intuit).
//
// Checks: Home shows WHAT NEEDS MY ATTENTION? first and compact with the wizards' Start buttons still above the fold;
// Field Today's seven quick actions on the phone; Add Receipt with the upload interrupted twice (the photo, then the
// receipt's registration) and recovered from the phone without a second receipt; Suzanne's Receipts Inbox, review,
// approve → confirmed by QuickBooks with the image attached → reconciliation; a company receipt matching an expense
// already in QuickBooks attached, not entered again; Needs Attention lifecycle (a real request appears, one click opens
// its working screen, resolved, gone); Need Materials → approval → the existing supplier request → Darcy's price in the
// Supplier Hub → cost recorded and approved → purchase order → the worker sees Ordered; Extra Work with a photo →
// question and answer → the existing change-order form → customer approval → outcome; Confirm Delivery Short with a
// photo → exception → resolved → the rest Received → Delivered; Job Update prefilled from records → project history →
// the problem on Ben's list → handled; end-of-day reminders made once (a second press makes none) and shown on Field
// Today with "Texts not switched on"; Kevin kept out of the office and accounting, Liam out of Kevin's receipt; another
// company sees nothing; no price or cost on any Field page; every page on a phone without sideways scrolling; no page
// error and no server error. MAG7_SHOTS=<dir> saves the screens (desktop and phone) for the Training Centre.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium node --test tools/release/evidence_magnificent_seven.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const SHOTS = process.env.MAG7_SHOTS || "";
const MONEY_ON_FIELD = [/\$\s?\d/, /\bprice\b/i, /\bcost\b/i, /margin/i, /markup/i, /\bwage/i, /labour rate/i];
let browser, server, base, facts, serverOut = "";
const serverErrors = [];
const sessions = {};
const M = {};

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/magnificent_seven_server.py")], {
    cwd: REPO, env: { ...process.env, MAG7_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => { out += c; serverOut += c; });
  server.stderr.on("data", (c) => { out += c; serverOut += c; });
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 300000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 100);
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
  console.log(`MAGNIFICENT_SEVEN SERVER_ERRORS=${serverErrors.length}`);
  if (process.env.MAG7_DEBUG) fs.writeFileSync(process.env.MAG7_DEBUG, serverOut);
});

let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function person(key, viewport) {
  const id = `${key}-${viewport.width}`;
  if (sessions[id]) return sessions[id];
  const phone = viewport.width < 500;
  const ctx = await browser.newContext({ viewport, serviceWorkers: "block",
    ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(20000);
  // Only the local office: web fonts and icon CDNs are not reachable here, and a dozen sessions' hanging tunnels
  // to them exhaust the browser's proxy sockets (net::ERR_INSUFFICIENT_RESOURCES). The pages do not need them.
  await ctx.route(/^https?:\/\/(?!127\.0\.0\.1[:/])/, (route) => route.abort("blockedbyclient"));
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  pg.on("dialog", (d) => d.dismiss().catch(() => {}));
  sessions[id] = { ctx, pg, errors };
  const supplier = key === "darcy";
  const [email, password] = facts.people[key];
  await go(pg, supplier ? "/supplier/login" : "/login");
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await submit(pg, pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(pg.url(), /\/login/, `${key} signs in`);
  return sessions[id];
}
async function go(pg, url) {
  const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`);
  await pg.waitForLoadState();
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
const pathOf = (pg) => new URL(pg.url()).pathname;
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}
async function shot(pg, name) {
  if (!SHOTS) return;
  await pg.screenshot({ path: path.join(SHOTS, `m7-${name}.png`), fullPage: false });
}
async function flash(pg) {
  return (await pg.locator(".flash-stack, .flash, .field-flashes").allInnerTexts().catch(() => [])).join(" | ");
}
async function noMoneyOnField(pg, label) {
  const text = await pg.locator("main").innerText();
  for (const re of MONEY_ON_FIELD) assert.doesNotMatch(text, re, `${label}: Field shows ${re}`);
}
async function postForm(pg, url, fields) {
  return pg.evaluate(async ({ url, fields }) => {
    const token = document.querySelector('meta[name="csrf-token"]').content;
    const body = new URLSearchParams({ csrf_token: token, ...fields });
    const r = await fetch(url, { method: "POST", body, credentials: "same-origin" });
    return r.status;
  }, { url, fields });
}

// A small synthetic receipt photo (PNG, drawn here; no real receipt).
function receiptPng() {
  const w = 120, h = 180;
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 3 + 1)] = 0;
    for (let x = 0; x < w; x++) {
      const i = y * (w * 3 + 1) + 1 + x * 3;
      const line = y > 20 && y % 14 < 3 && x > 10 && x < 110 - (y % 3) * 15;
      raw[i] = raw[i + 1] = raw[i + 2] = line ? 40 : 236;
    }
  }
  const crc = (buf) => { let c = ~0; for (const b of buf) { c ^= b; for (let k = 0; k < 8; k++) c = (c >>> 1) ^ (0xedb88320 & -(c & 1)); } return ~c >>> 0; };
  const chunk = (type, data) => {
    const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
    const td = Buffer.concat([Buffer.from(type), data]);
    const c = Buffer.alloc(4); c.writeUInt32BE(crc(td));
    return Buffer.concat([len, td, c]);
  };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw)), chunk("IEND", Buffer.alloc(0))]);
}
const PHOTO = (name) => ({ name, mimeType: "image/png", buffer: receiptPng() });

// ------------------------------------------------------------------ Home
step("Home: WHAT NEEDS MY ATTENTION? first and compact, the wizards' Start buttons still above the fold", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const attention = pg.locator("[data-needs-attention]");
  assert.match(await attention.innerText(), /WHAT NEEDS MY ATTENTION\?/);
  const aBox = await attention.boundingBox();
  const wBox = await pg.locator("[data-wizard-home]").boundingBox();
  assert.ok(aBox.y < wBox.y, "attention comes before the wizards");
  for (const key of ["NEW_PROJECT", "GUIDED_ESTIMATING", "MANAGE_PROJECT"]) {
    const box = await pg.locator(`[data-start-wizard="${key}"]`).boundingBox();
    assert.ok(box.y + box.height <= DESK.height, `${key}: Start is still above the fold`);
  }
  await shot(pg, "home-attention-desktop");
  const phone = await person("ben", PHONE);
  await go(phone.pg, "/");
  await noSideways(phone.pg, "home phone");
  await shot(phone.pg, "home-attention-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Field quick actions
step("Field Today on the iPhone: the seven quick actions, large and above the fold", async () => {
  const { pg, errors } = await person("kevin", PHONE);
  await go(pg, "/field/today");
  const labels = await pg.locator("[data-quick-action]").allInnerTexts();
  assert.deepEqual(labels.map((s) => s.trim()), ["My Hours", "Add Receipt", "Need Materials", "Extra Work",
    "Confirm Delivery", "Job Update", "My Schedule"]);
  for (const b of await pg.locator("[data-quick-action]").all()) {
    const box = await b.boundingBox();
    assert.ok(box.height >= 44, "touch target at least 44 px");
  }
  const last = await pg.locator('[data-quick-action="schedule"]').boundingBox();
  assert.ok(last.y + last.height <= PHONE.height, "all seven are above the fold");
  await noSideways(pg, "field today");
  await noMoneyOnField(pg, "field today");
  await shot(pg, "field-quick-actions-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Receipt: capture with interrupted upload
step("Add Receipt on the iPhone: the upload is interrupted twice and recovers from the phone, one receipt", async () => {
  const { pg, errors } = await person("kevin", PHONE);
  await go(pg, "/field/today");
  await submit(pg, pg.locator('[data-quick-action="receipt"]'));
  assert.equal(pathOf(pg), "/field/receipt");
  assert.equal(await pg.inputValue("#field-receipt-project"), "", "no job confirmed yet: Kevin chooses it");
  await pg.selectOption("#field-receipt-project", String(facts.project_id));
  await pg.setInputFiles("#field-take-photo", PHOTO("receipt-bmr.png"));
  await pg.fill("#field-receipt-supplier", "BMR");
  await pg.fill("#field-receipt-amount", "113.00");
  await pg.fill("#field-text", "Joist hangers for the deck");
  await shot(pg, "receipt-capture-phone");
  // 1) The photo upload is cut off: the capture stays on the phone.
  await pg.route("**/originals", (route) => route.abort("connectionreset"));
  await pg.click("#field-save");
  await pg.locator("#field-feedback[data-state=needs_retry]").waitFor();
  assert.match(await pg.locator("#field-feedback").innerText(), /still on this phone/);
  await pg.unroute("**/originals");
  // 2) The photo goes, but the answer to the receipt's registration is lost.
  await pg.route("**/field/receipts/register", (route) => route.abort("connectionreset"), { times: 1 });
  await pg.evaluate(() => window.dispatchEvent(new Event("online")));
  await pg.locator("#field-feedback[data-state=needs_retry]").waitFor();
  // 3) Back online: the phone sends what is left; the office answers with the one receipt.
  await pg.evaluate(() => window.dispatchEvent(new Event("online")));
  await pg.locator("#field-feedback[data-state=saved]").waitFor();
  assert.match(await pg.locator("#field-feedback").innerText(), /Receipt R-\d+ saved/);
  await go(pg, "/field/receipt");
  const mine = await pg.locator("[data-field-my-receipts] li").allInnerTexts();
  assert.equal(mine.length, 1, "one receipt, not two");
  assert.match(mine[0], /Sent to the office/);
  await noSideways(pg, "receipt page");
  await shot(pg, "receipt-saved-phone");
  // A Shop / Company Expense receipt.
  await pg.selectOption("#field-receipt-project", { label: "Shop / Company Expense" });
  await pg.setInputFiles("#field-take-photo", PHOTO("receipt-home-hardware.png"));
  await pg.fill("#field-receipt-supplier", "Home Hardware");
  await pg.click("#field-save");
  await pg.locator("#field-feedback[data-state=saved]").waitFor();
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Receipt: Suzanne's inbox to QuickBooks
step("Suzanne's Receipts Inbox: review, approve, confirmed by QuickBooks with the image, reconciliation", async () => {
  const { pg, errors } = await person("suzanne", DESK);
  await go(pg, "/accounting");
  await submit(pg, pg.locator("[data-open-receipts-inbox]"));
  assert.equal(await pg.locator("[data-receipt]").count(), 2);
  await shot(pg, "receipts-inbox-desktop");
  const row = pg.locator("[data-receipt]").filter({ hasText: "BMR" });
  await submit(pg, row.locator("a").first());
  M.receiptUrl = pathOf(pg);
  assert.equal(await pg.locator("img.ops-photo").count(), 1, "the original image is on the page");
  await pg.fill("input[name=vendor_name]", "BMR Winchester (synthetic)");
  const today = await pg.evaluate(() => new Date().toISOString().slice(0, 10));
  await pg.fill("input[name=receipt_date]", await pg.inputValue("input[name=receipt_date]") || today);
  await pg.fill("input[name=subtotal]", "100.00");
  await pg.fill("input[name=tax_amount]", "13.00");
  await pg.fill("input[name=total]", "113.00");
  await shot(pg, "receipt-review-desktop");
  await submit(pg, pg.locator("[data-save-review]"));
  assert.match(await flash(pg), /Review saved/);
  await submit(pg, pg.locator("[data-approve-receipt]"));
  assert.match(await flash(pg), /In QuickBooks: entered as a new expense \d+, with the receipt image \(attachment \d+\)/);
  assert.equal(await pg.getAttribute("[data-receipt-status]", "data-receipt-status"), "SYNCED");
  assert.equal(await pg.getAttribute("[data-qbo-transfer-status]", "data-qbo-transfer-status"), "CONFIRMED");
  assert.equal(await pg.locator("[data-approve-receipt]").count(), 0, "a synced receipt cannot be approved again");
  await shot(pg, "receipt-synced-desktop");
  await go(pg, "/accounting/quickbooks-online/reconciliation");
  assert.equal(await pg.locator("[data-reconciled]").count(), 1);
  assert.match(await pg.locator("[data-qbo-reconciliation]").innerText(), /New expense/);
  // The company receipt matches an expense entered by hand: attached, no second expense.
  await go(pg, "/accounting/receipts?status=NEW");
  await submit(pg, pg.locator("[data-receipt] a").first());
  await pg.fill("input[name=vendor_name]", "Home Hardware Kemptville (synthetic)");
  await pg.fill("input[name=receipt_date]", await pg.inputValue("input[name=receipt_date]") || today);
  await pg.fill("input[name=subtotal]", "50.00");
  await pg.fill("input[name=tax_amount]", "6.50");
  await pg.fill("input[name=total]", "56.50");
  await submit(pg, pg.locator("[data-save-review]"));
  await submit(pg, pg.locator("[data-approve-receipt]"));
  assert.match(await flash(pg), new RegExp(`attached to the existing expense ${facts.hand_entered_purchase}`));
  await go(pg, "/accounting/quickbooks-online/reconciliation");
  assert.equal(await pg.locator("[data-reconciled]").count(), 2);
  assert.match(await pg.locator("[data-qbo-reconciliation]").innerText(), /Attached to existing/);
  await shot(pg, "qbo-reconciliation-desktop");
  await go(pg, "/accounting/quickbooks-online");
  assert.equal(await pg.getAttribute("[data-qbo-connection]", "data-qbo-connection"), "connected");
  assert.match(await pg.locator("[data-qbo-counts]").innerText(), /Confirmed 2/);
  await shot(pg, "qbo-connection-desktop");
  const phone = await person("suzanne", PHONE);
  await go(phone.pg, "/accounting/receipts");
  await noSideways(phone.pg, "inbox phone");
  await shot(phone.pg, "receipts-inbox-phone");
  await go(phone.pg, M.receiptUrl);
  await noSideways(phone.pg, "receipt phone");
  // Kevin sees where his receipt is; the Project Hub lists it.
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/receipt");
  assert.match(await kevin.pg.locator("[data-field-my-receipts]").innerText(), /In QuickBooks/);
  const ben = await person("ben", DESK);
  await go(ben.pg, `/projects/${facts.project_id}#hub-receipts`);
  assert.equal(await ben.pg.locator("[data-hub-receipt]").count(), 1);
  await ben.pg.locator("#hub-field-operations").scrollIntoViewIfNeeded();
  await shot(ben.pg, "hub-field-operations-desktop");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Need Materials and the attention lifecycle
step("Need Materials from the phone appears on Ben's list; one click opens it; approved and sent; it leaves the list", async () => {
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/today");
  await submit(kevin.pg, kevin.pg.locator('[data-quick-action="materials"]'));
  assert.match(pathOf(kevin.pg), new RegExp(`/field/projects/${facts.project_id}/materials$`));
  await kevin.pg.selectOption("#mr-material", { index: 1 });
  await kevin.pg.fill("input[name=quantity]", "24");
  await kevin.pg.fill("textarea[name=note]", "For the stair stringers");
  await shot(kevin.pg, "materials-form-phone");
  await submit(kevin.pg, kevin.pg.locator("[data-send-request]"));
  assert.match(await flash(kevin.pg), /Material request MR-\d+ sent to the office/);
  await noSideways(kevin.pg, "materials");
  await noMoneyOnField(kevin.pg, "materials");
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const item = pg.locator('[data-attention-kind="materials"]').first();
  assert.match(await item.innerText(), /Material request/);
  await submit(pg, item.locator("[data-attention-action]"));
  assert.match(pathOf(pg), /\/operations\/material-requests\/\d+$/, "one click opens the request itself");
  M.materialUrl = pathOf(pg);
  await pg.fill("#mr-qty", "30");
  await shot(pg, "material-review-desktop");
  await submit(pg, pg.locator("[data-approve-request]"));
  assert.match(await flash(pg), /approved/);
  await submit(pg, pg.locator("[data-send-to-supplier] button[type=submit]"));
  assert.match(await flash(pg), /Supplier request SRQ-[\d-]+ sent to BMR Winchester \(synthetic\)/);
  M.shareId = Number((await pg.getAttribute("[data-open-supplier-request]", "href")).split("#share-")[1]);
  await go(pg, "/");
  assert.equal(await pg.locator(`[data-attention-action][href="${M.materialUrl}"]`).count(), 0, "resolved: gone");
  await go(pg, "/operations/attention");
  assert.match(await pg.locator("[data-attention-page]").innerText(), /Waiting for a price from BMR Winchester/);
  await go(kevin.pg, "/field/requests");
  assert.match(await kevin.pg.locator("[data-field-my-requests]").innerText(), /Sent to the supplier/);
  assert.deepEqual(errors, []);
});

step("The supplier prices it in the Supplier Hub; Ben records, approves and orders; Kevin sees Ordered", async () => {
  const darcy = await person("darcy", DESK);
  await go(darcy.pg, `/supplier/${facts.supplier_id}/requests/${M.shareId}`);
  await darcy.pg.fill("input[name=sku_01]", "BMR-STRINGER");
  await darcy.pg.fill("input[name=unit_cost_01]", "4.00");
  await darcy.pg.fill("input[name=discount_01]", "0");
  const today = await darcy.pg.evaluate(() => new Date().toISOString().slice(0, 10));
  await darcy.pg.fill("input[name=response_date]", today);
  const later = await darcy.pg.evaluate(() => new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10));
  await darcy.pg.fill("input[name=valid_until]", later);
  await submit(darcy.pg, darcy.pg.locator("form button[type=submit]").filter({ hasText: /return|send/i }).first());
  assert.match(await darcy.pg.locator("body").innerText(), /Quote returned/);
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${facts.project_id}/supplier-requests`);
  const ref = await pg.evaluate(async (shareId) => {
    const html = await (await fetch(location.pathname, { credentials: "same-origin" })).text();
    const m = html.match(/deck-takeoff\/responses\/(RSP-[\w-]+)/);
    return m ? m[1] : null;
  }, M.shareId);
  assert.ok(ref, "the returned price is on the job's supplier requests");
  assert.equal(await postForm(pg, `/projects/${facts.project_id}/deck-takeoff/responses/${ref}/record`, {}), 200);
  await go(pg, `/projects/${facts.project_id}/deck-takeoff/responses/${ref}`);
  const materialId = await pg.evaluate(() => {
    const input = document.querySelector("input[name=canonical_material_id]");
    return input ? input.value : null;
  });
  assert.ok(materialId, "the recorded line can be approved");
  assert.equal(await postForm(pg, `/projects/${facts.project_id}/deck-takeoff/responses/${ref}/approve`,
    { canonical_material_id: materialId, status: "APPROVED" }), 200);
  // Gate 3 (decision 6): before the customer accepts, Ben (the owner) records an Early Procurement Exception.
  assert.equal(await postForm(pg, `/projects/${facts.project_id}/supplier-requests/${M.shareId}/early-exception`,
    { reason: "Lumber lead time (synthetic)", proposed_commitment: "Deck lumber (synthetic)", financial_exposure: "5000",
      approving_authority: "Ben Brayman, owner (synthetic)" }), 200);
  const orderDay = await pg.evaluate(() => new Date(Date.now() + 2 * 864e5).toISOString().slice(0, 10));
  assert.equal(await postForm(pg, `/projects/${facts.project_id}/supplier-requests/${M.shareId}/order`,
    { delivery_date: orderDay, site_contact: "Kevin", sign_consent: "yes", signer_name: "Ben Synthetic" }), 200);
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/requests");
  assert.match(await kevin.pg.locator("[data-field-my-requests]").innerText(), /Ordered/);
  await noMoneyOnField(kevin.pg, "my requests");
  await shot(kevin.pg, "my-requests-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Extra Work
step("Extra Work with a photo → Ben asks, Kevin answers → the existing change order → customer approval", async () => {
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/today");
  await submit(kevin.pg, kevin.pg.locator('[data-quick-action="extra_work"]'));
  await kevin.pg.fill("textarea[name=description]", "Second set of stairs down to the yard");
  await kevin.pg.fill("input[name=requested_by]", "Morgan Ellis (homeowner)");
  await kevin.pg.setInputFiles("input[name=photos]", PHOTO("stairs.png"));
  await shot(kevin.pg, "extra-work-phone");
  await submit(kevin.pg, kevin.pg.locator("form[data-field-request-form] button[type=submit]"));
  assert.match(await flash(kevin.pg), /Extra work recorded/);
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const item = pg.locator('[data-attention-kind="extra_work"]').filter({ hasText: "Second set of stairs" }).first();
  await submit(pg, item.locator("[data-attention-action]"));
  assert.match(pathOf(pg), /\/operations\/extra-work\/\d+$/);
  M.extraUrl = pathOf(pg);
  assert.equal(await pg.locator("img.ops-photo").count(), 1);
  await pg.fill("#ew-q", "Same width as the main stairs?");
  await submit(pg, pg.locator("[data-ask-crew]"));
  await go(kevin.pg, "/field/extra-work/mine");
  await kevin.pg.fill("textarea[name=answer]", "Yes, 4 ft wide");
  await submit(kevin.pg, kevin.pg.locator("[data-answer-question]"));
  await go(pg, M.extraUrl);
  await shot(pg, "extra-work-review-desktop");
  await submit(pg, pg.locator("[data-prepare-change-order]"));
  assert.match(pathOf(pg), /\/project-controls\/change-orders\/new$/);
  await pg.fill("input[name=title]", "Second stairs to the yard");
  const cost = pg.locator("input[name=approved_internal_direct_cost]");
  if (await cost.count()) await cost.fill("850.00");
  await submit(pg, pg.locator("form button[type=submit]").filter({ hasText: /create|save/i }).first());
  assert.match(pathOf(pg), /\/project-controls\/change-orders\/\d+$/);
  await pg.selectOption("select[name=status]", "Approved");
  await submit(pg, pg.locator("select[name=status]").locator("xpath=ancestor::form//button[@type='submit']"));
  await go(pg, M.extraUrl);
  assert.match(await pg.locator("[data-extra-work-outcome]").innerText(), /Approved by the customer/);
  await go(kevin.pg, "/field/requests");
  assert.match(await kevin.pg.locator("[data-field-my-requests]").innerText(), /Approved by the customer/);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Confirm Delivery
step("Confirm Delivery: Short with a photo → exception → resolved → the rest Received → Delivered", async () => {
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/today");
  await submit(kevin.pg, kevin.pg.locator('[data-quick-action="delivery"]'));
  await noMoneyOnField(kevin.pg, "deliveries");
  await submit(kevin.pg, kevin.pg.locator(`[data-field-order="${facts.order_id}"] a`));
  await noMoneyOnField(kevin.pg, "delivery form");
  await kevin.pg.locator('[data-outcome="SHORT"]').check({ force: true });
  await kevin.pg.fill("input[name=received_1]", "35");
  await kevin.pg.fill("input[name=received_2]", "60");
  await kevin.pg.fill("textarea[name=note]", "5 boards short");
  await kevin.pg.setInputFiles("input[name=photos]", PHOTO("delivery.png"));
  await noSideways(kevin.pg, "delivery form");
  await shot(kevin.pg, "delivery-short-phone");
  await submit(kevin.pg, kevin.pg.locator("[data-save-delivery]"));
  assert.match(await flash(kevin.pg), /Delivery short recorded/);
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const item = pg.locator('[data-attention-kind="deliveries"]').filter({ hasText: facts.order_number }).first();
  await submit(pg, item.locator("[data-attention-action]"));
  assert.match(pathOf(pg), /\/operations\/deliveries\/\d+$/);
  M.deliveryUrl = pathOf(pg);
  assert.match(await pg.locator("[data-delivery-state]").innerText(), /Delivery problem/);
  await shot(pg, "delivery-exception-desktop");
  await pg.locator('input[name=resolution][value=REST_COMING]').check();
  await pg.fill("#dl-note", "Darcy sends the 5 on Friday");
  await submit(pg, pg.locator("[data-resolve-delivery] button[type=submit]"));
  await go(pg, "/");
  assert.equal(await pg.locator(`[data-attention-action][href="${M.deliveryUrl}"]`).count(), 0, "resolved: gone");
  await go(kevin.pg, `/field/projects/${facts.project_id}/deliveries/${facts.order_id}`);
  await kevin.pg.locator('[data-outcome="RECEIVED"]').check({ force: true });
  await submit(kevin.pg, kevin.pg.locator("[data-save-delivery]"));
  await go(pg, `/projects/${facts.project_id}`);
  assert.match(await pg.locator(`[data-hub-po="${facts.order_number}"]`).innerText(), /Delivered/);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Job Update
step("Job Update prefilled from records → saved to the project → the problem on Ben's list → handled", async () => {
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/today");
  await submit(kevin.pg, kevin.pg.locator('[data-quick-action="job_update"]'));
  const factsText = await kevin.pg.locator("[data-job-facts]").innerText();
  assert.match(factsText, /Deck framing/);
  assert.match(factsText, /Photos today: [1-9]/);
  assert.match(factsText, /Delivery recorded/);
  await kevin.pg.fill("textarea[name=completed_text]", "Framed the north side");
  await kevin.pg.fill("textarea[name=problems_text]", "Rain stopped us at 2 pm");
  await kevin.pg.fill("textarea[name=needs_text]", "More hangers");
  await noSideways(kevin.pg, "job update");
  await noMoneyOnField(kevin.pg, "job update");
  await shot(kevin.pg, "job-update-phone");
  await submit(kevin.pg, kevin.pg.locator("[data-save-job-update]"));
  assert.match(await flash(kevin.pg), /Job update saved/);
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const item = pg.locator('[data-attention-kind="tasks"]').filter({ hasText: "Rain stopped us" }).first();
  await submit(pg, item.locator("[data-attention-action]"));
  assert.match(await pg.locator("[data-job-update-detail]").innerText(), /From CalibraytAI records \(verified\)/);
  await shot(pg, "job-update-desktop");
  await pg.fill("#ju-note", "Moved framing to Monday");
  await submit(pg, pg.locator("[data-handle-problem] button[type=submit]"));
  await go(pg, `/projects/${facts.project_id}`);
  assert.match(await pg.locator("[data-hub-job-updates]").innerText(), /Rain stopped us/);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Reminders
step("End-of-day reminders: made once, shown on Field Today with Texts not switched on, never twice", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/operations/reminders");
  assert.match(await pg.locator("[data-reminder-texting]").innerText(), /Texts not switched on/);
  await submit(pg, pg.locator("[data-send-reminders-now]"));
  assert.match(await flash(pg), /Reminders made: [1-9]\d* crew/);
  await submit(pg, pg.locator("[data-send-reminders-now]"));
  assert.match(await flash(pg), /Reminders made: 0 crew, 0 owner; [1-9]\d* already had today's reminder/);
  await shot(pg, "reminders-desktop");
  const kevin = await person("kevin", PHONE);
  await go(kevin.pg, "/field/today");
  const reminder = kevin.pg.locator("[data-field-reminder]");
  assert.match(await reminder.innerText(), /Before you finish today/);
  assert.match(await reminder.innerText(), /Texts not switched on/);
  await shot(kevin.pg, "field-reminder-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Projects into QuickBooks (approved item A)
step("Projects into QuickBooks: Suzanne checks all projects, confirms the existing job once, nothing duplicated", async () => {
  const { pg, errors } = await person("suzanne", DESK);
  await go(pg, "/accounting/quickbooks-online/projects");
  assert.equal(await pg.locator("[data-project-sync-state]").getAttribute("data-project-sync-state"), "on");
  await submit(pg, pg.locator("[data-sync-all-projects]"));
  assert.match(await flash(pg), /Checked \d+ projects: \d+ in step, [1-9]\d* to confirm/);
  const second = pg.locator(`[data-project-link="${facts.second_id}"]`);
  assert.equal(await second.getAttribute("data-qbo-status"), "SYNCED");
  assert.equal(await second.getAttribute("data-qbt-status"), "SYNCED");
  const harbour = pg.locator(`[data-project-link="${facts.project_id}"]`);
  assert.equal(await harbour.getAttribute("data-qbo-status"), "NEEDS_CONFIRM");
  await shot(pg, "qbo-projects-confirm-desktop");
  const ben = await person("ben", DESK);
  await go(ben.pg, "/operations/attention");
  const item = ben.pg.locator(`a[href$="/accounting/quickbooks-online/projects#project-${facts.project_id}"]`).first();
  assert.ok(await item.count(), "the job to confirm is on Ben's list");
  // Confirm each existing record once (customer, then the project; QuickBooks Time made the job code).
  for (let i = 0; i < 3; i++) {
    const button = harbour.locator("[data-confirm-match]").first();
    if (!(await button.count())) break;
    await submit(pg, button);
    assert.match(await flash(pg), /Match confirmed/);
  }
  assert.equal(await harbour.getAttribute("data-qbo-status"), "SYNCED");
  assert.equal(await harbour.getAttribute("data-qbt-status"), "SYNCED");
  await submit(pg, pg.locator("[data-sync-all-projects]"));
  assert.match(await flash(pg), / 0 to confirm, 0 failed/);
  await shot(pg, "qbo-projects-desktop");
  await go(ben.pg, "/operations/attention");
  assert.equal(await ben.pg.locator(`a[href$="#project-${facts.project_id}"]`).count(), 0);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ My Week (approved item B)
step("My Week: Previous week, This week (Coming week on Sunday) and Next week move a week at a time", async () => {
  const { pg, errors } = await person("kevin", PHONE);
  await go(pg, "/field/week");
  const label = await pg.locator("[data-week-this]").innerText();
  assert.match(label, new Date().getDay() === 0 ? /Coming week/ : /This week/);
  const start = await pg.locator("[data-week-window]").innerText();
  await submit(pg, pg.locator("[data-week-next]"));
  assert.match(pathOf(pg) + new URL(pg.url()).search, /\/field\/week\?start=\d{4}-\d{2}-\d{2}/);
  assert.notEqual(await pg.locator("[data-week-window]").innerText(), start);
  await submit(pg, pg.locator("[data-week-this]"));
  assert.equal(await pg.locator("[data-week-window]").innerText(), start);
  await noSideways(pg, "/field/week");
  await shot(pg, "field-week-phone");
  await noMoneyOnField(pg, "/field/week");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Permissions and isolation
step("Kevin is kept out of the office and accounting; Liam out of Kevin's receipt; another company sees nothing", async () => {
  const kevin = await person("kevin", DESK);
  for (const url of ["/accounting/receipts", "/accounting/quickbooks-online", "/accounting/quickbooks-online/projects",
    "/operations/attention",
    "/operations/material-requests", "/"]) {
    await go(kevin.pg, url);
    assert.equal(pathOf(kevin.pg), "/field/today", `${url} sends Field-only crew to Field`);
  }
  const liam = await person("liam", PHONE);
  const r = await go(liam.pg, "/field/receipts/1");
  assert.equal(r.status(), 404);
  await go(liam.pg, "/field/receipt");
  assert.doesNotMatch(await liam.pg.locator("main").innerText(), /Harbour Lane Pool Deck/);
  const other = await person("other", DESK);
  await go(other.pg, "/accounting/receipts");
  assert.equal(await other.pg.locator("[data-receipt]").count(), 0);
  await go(other.pg, "/operations/attention");
  assert.match(await other.pg.locator("[data-attention-page]").innerText(), /Nothing needs your attention right now/);
  const res = await go(other.pg, M.receiptUrl);
  assert.equal(res.status(), 404);
});

step("Every new page on the iPhone without sideways scrolling; no page error, no server error", async () => {
  const kevin = await person("kevin", PHONE);
  for (const url of ["/field/today", "/field/receipt", "/field/requests", "/field/extra-work/mine",
    `/field/projects/${facts.project_id}/materials`, `/field/projects/${facts.project_id}/deliveries`,
    `/field/projects/${facts.project_id}/job-update`, "/field/text-messages"]) {
    await go(kevin.pg, url);
    await noSideways(kevin.pg, url);
  }
  const ben = await person("ben", PHONE);
  for (const url of ["/", "/operations/attention", "/operations/material-requests?show=all", M.materialUrl,
    "/operations/extra-work?show=all", M.extraUrl, "/operations/deliveries", M.deliveryUrl, "/operations/job-updates",
    "/operations/reminders", "/accounting/quickbooks-online", "/accounting/quickbooks-online/projects",
    `/projects/${facts.project_id}`]) {
    await go(ben.pg, url);
    await noSideways(ben.pg, url);
  }
  for (const s of Object.values(sessions)) assert.deepEqual(s.errors, []);
  assert.deepEqual(serverErrors, []);
});
