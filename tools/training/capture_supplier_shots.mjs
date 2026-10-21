// Screenshots for the SUPPLIER pathway of the Training & Acceptance Centre (Joel, 21 Oct 2026).
//
// Starts the local training site (tests/training_page_server.py: real migrations, the training company,
// BMR Winchester (training) with Darcy and Pat), then follows the Harbour Lane Pool Deck job from the
// supplier's side through the real pages only:
//   Ben (contractor office) sends a material request and a separate concrete request to BMR;
//   Darcy signs in, quotes both, Ben records and orders, Darcy confirms, both sides move a delivery,
//   Darcy marks the material order delivered; an updated request shows remembered SKUs;
//   Pat sets up the PRO Desk (quote settings, price file, a standard building, product matches) and quotes
//   a walk-in customer: sketch → quotation → customer link on a phone → order-ready package.
// The one record with no office page (the job's construction model, which comes with the estimate's
// drawings) comes with the training site (app/training/environment.py). Synthetic data only.
//
// Saves PNGs into app/static/training/shots/ named s<module>-<name>.png: desktop 1280x900, phone 390x844,
// viewport shots with the control scrolled into view, each kept under about 350 KB.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium \
//      node --test --test-concurrency=1 tools/training/capture_supplier_shots.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "../release/evidence_common.mjs";

const OUT = path.join(REPO, "app/static/training/shots");
const DESK = { width: 1280, height: 900 };
const PHONE = { width: 390, height: 844 };
const SKETCH = path.join(REPO, "tests/fixtures/pro_desk/synthetic-sketch.png");
const MAX_BYTES = 350 * 1024;
let browser, server, base, facts, tmp;
const saved = [];
const serverErrors = [];
const pageErrors = [];
const W = {}; // what the walk learns: request numbers, ids, order numbers

const day = (n) => { const d = new Date(); d.setDate(d.getDate() + n); return d.toLocaleDateString("en-CA"); };

before(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  tmp = fs.mkdtempSync(path.join(os.tmpdir(), "supplier-shots-"));
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/training_page_server.py")], {
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
});

after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close();
  server?.kill();
  if (saved.length) {
    // Keep each file small: downscale to 1280 wide at most and quantize when it is still too big.
    const code = [
      "import sys", "from PIL import Image", `limit = ${MAX_BYTES}`,
      "for p in sys.argv[1:]:",
      "    im = Image.open(p).convert('RGB')",
      "    if im.width > 1280:",
      "        im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)",
      "    im.save(p, optimize=True)",
      "    import os",
      "    if os.path.getsize(p) > limit:",
      "        im.quantize(colors=256, method=Image.Quantize.MEDIANCUT).save(p, optimize=True)",
      "    if os.path.getsize(p) > limit:",
      "        im.quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(p, optimize=True)",
      "    print(os.path.basename(p), os.path.getsize(p))",
    ].join("\n");
    const r = spawnSync(path.join(REPO, "venv/bin/python"), ["-c", code, ...saved], { encoding: "utf8" });
    process.stdout.write(r.stdout || ""); process.stderr.write(r.stderr || "");
  }
  console.log(`SUPPLIER_SHOTS=${saved.length} SERVER_ERRORS=${serverErrors.length}`);
});

const sessions = {};
async function session(key, viewport, person, loginPath, next = "") {
  if (sessions[key]) return sessions[key];
  const ctx = await browser.newContext({ viewport, acceptDownloads: true, locale: "en-CA" });
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${key}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  if (person) {
    await pg.goto(`${base}${loginPath}${next ? `?next=${encodeURIComponent(next)}` : ""}`);
    await pg.fill("input[name=email]", person.email);
    await pg.fill("input[name=password]", person.password);
    await pg.click("button[type=submit]");
    await pg.waitForLoadState();
  }
  sessions[key] = { ctx, pg };
  return sessions[key];
}
const ben = () => session("ben", DESK, facts.people.ben, "/login");
const darcy = () => session("darcy", DESK, facts.people.darcy, "/supplier/login");
const darcyPhone = () => session("darcyPhone", PHONE, facts.people.darcy, "/supplier/login");
const pat = () => session("pat", DESK, facts.people.pat, "/supplier/login");

async function go(pg, url) { await pg.goto(url.startsWith("http") ? url : `${base}${url}`); await pg.waitForLoadState(); }
async function flash(pg) { return (await pg.locator(".flash, .flash-stack .alert").allInnerTexts()).join(" | "); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
// A viewport screenshot with the element `at` near the top of the screen (or the page top).
async function snap(pg, name, at = null, offset = 70) {
  if (at) {
    const loc = pg.locator(at).first();
    await loc.waitFor({ state: "attached" });
    await loc.evaluate((el, off) => { const y = el.getBoundingClientRect().top + window.scrollY - off; window.scrollTo(0, Math.max(0, y)); }, offset);
  } else {
    await pg.evaluate(() => window.scrollTo(0, 0));
  }
  await pg.waitForTimeout(150);
  const file = path.join(OUT, `${name}.png`);
  await pg.screenshot({ path: file });
  saved.push(file);
}
const hub = (rest = "") => `/supplier/${facts.supplier_id}/${rest}`;
const requestsPage = () => `/projects/${W.projectId}/supplier-requests`;
const share = (pg, id) => pg.locator(`article#share-${id}`);

const FACTS_V1 = {
  "cutting.kerf_in": "0.125", "cutting.offcut_reuse": "across_uses",
  "decking.product_type": "capped_composite", "decking.product_name": "Capped composite board, grey (training)",
  "decking.actual_width_in": "5.5", "decking.gap_in": "0.1875", "decking.stock_lengths_ft": "12, 16, 20",
  "decking.end_overhang_in": "0.75", "decking.max_joist_spacing_in": "16", "decking.max_stair_stringer_spacing_in": "16",
  "decking.tread_nosing_overhang_in": "1.0", "decking.min_rip_width_in": "1.5", "decking.riser_closure": "required",
  "decking.riser_board_width_in": "7.25", "decking.nosing": "not_used", "decking.fasteners_per_crossing": "1",
  "decking.fasteners_per_package": "90",
  "fascia.product_name": "Composite fascia, grey (training)", "fascia.actual_height_in": "11.25", "fascia.thickness_in": "0.5",
  "fascia.stock_lengths_ft": "12", "fascia.fastener_spacing_in": "16", "fascia.fasteners_per_station": "2",
  "fascia.fasteners_per_package": "100",
  "railing.system_name": "Black aluminum railing (training)", "railing.level_panel_lengths_ft": "6, 8",
  "railing.stair_panel_lengths_ft": "6", "railing.stair_panel_span_basis": "horizontal", "railing.panels_cut_to_length": "yes",
  "railing.max_post_spacing_in": "72", "railing.guard_height_in": "42", "railing.fittings_per_junction": "1",
  "foundations.pier_includes_bracket": "no",
  "gate.product_name": "Black aluminum pool gate (training)", "gate.clear_opening_in": "42", "gate.hinges_per_gate": "2",
  "gate.latches_per_gate": "1",
};

// ------------------------------------------------------------------ module 1: sign-in and registration

test("s1: the Training Centre sign-in, the supplier sign-in and registration", async () => {
  const anon = await session("anon", DESK, null);
  await go(anon.pg, "/training/signin");
  await snap(anon.pg, "s1-training-signin");
  await anon.pg.click("[data-signin=supplier]");
  await anon.pg.waitForLoadState();
  assert.match(anon.pg.url(), /\/supplier\/login\?next=/);
  await anon.pg.fill("input[name=email]", facts.people.darcy.email);
  await snap(anon.pg, "s1-supplier-sign-in");
  await anon.pg.click("[data-supplier-forgot]");
  await anon.pg.waitForLoadState();
  await snap(anon.pg, "s1-forgot-password");
  const phone = await session("anonPhone", PHONE, null);
  await go(phone.pg, "/supplier/login");
  await noSideways(phone.pg, "phone sign-in");
  await snap(phone.pg, "s1-supplier-sign-in-phone");
  // Darcy signs in from the Training Centre and registers as the supplier owner.
  const d = await session("darcyTraining", DESK, facts.people.darcy, "/supplier/login", "/training");
  assert.match(d.pg.url(), /\/training$/);
  assert.match(await d.pg.locator("main").innerText(), /Supplier owner[\s\S]*PRO Desk staff/i);
  await snap(d.pg, "s1-register");
  await d.pg.check("input[name=role][value=SUPPLIER_OWNER]");
  await d.pg.click("[data-register]");
  await d.pg.waitForLoadState();
  assert.match(await d.pg.locator("main").innerText(), /Supplier training · Supplier owner/i);
  await snap(d.pg, "s1-training-home");
  // Pat registers as PRO Desk staff: the PRO Desk lessons and the basics only.
  const p = await session("patTraining", DESK, facts.people.pat, "/supplier/login", "/training");
  await p.pg.check("input[name=role][value=PRO_DESK]");
  await p.pg.click("[data-register]");
  await p.pg.waitForLoadState();
  assert.match(await p.pg.locator("main").innerText(), /PRO Desk staff/i);
  await snap(p.pg, "s1-training-home-pro-desk");
  // The Supplier Hub itself: one store, so it opens straight on BMR's requests.
  await go(d.pg, "/supplier/");
  assert.ok(d.pg.url().endsWith(hub()), d.pg.url());
});

// ------------------------------------------------------------------ module 2: who can sign in

test("s2: the contractor's Suppliers page, and a supplier's own text settings", async () => {
  const { pg } = await ben();
  await go(pg, "/suppliers");
  const art = pg.locator(`article#supplier-${facts.supplier_id}`);
  const text = await art.innerText();
  assert.ok(text.includes("Darcy") && text.includes("Pat at the PRO Desk"), text);
  assert.match(text, /can sign in/);
  await snap(pg, "s2-office-suppliers", `article#supplier-${facts.supplier_id}`);
  await art.locator("details.supplier-branding summary").click();
  await snap(pg, "s2-office-branding", `article#supplier-${facts.supplier_id} details.supplier-branding`);
  const dp = (await darcyPhone()).pg;
  await go(dp, "/supplier/account");
  await noSideways(dp, "phone text settings");
  await snap(dp, "s2-text-settings-phone");
});

// ------------------------------------------------------------------ Ben sends the requests

test("office: Ben sends the Harbour Lane material request and a separate concrete request to BMR", async () => {
  const { pg } = await ben();
  await go(pg, "/projects/");
  await pg.locator(`a:has-text("${facts.job}")`).first().click();
  await pg.waitForLoadState();
  W.projectId = Number(pg.url().match(/\/projects\/(\d+)/)[1]);
  // The job's construction model comes with the training site (flask training build-environment).
  await sendMaterialRequest(pg, FACTS_V1, day(10));
  W.first = await newestShare(pg);
  // Concrete is its own request, sent only to the concrete supplier (here BMR, who buys it from Tomlinson).
  await go(pg, requestsPage());
  const form = pg.locator("[data-new-concrete]");
  await form.locator("[name=volume_m3]").fill("6.5");
  await form.locator("[name=strength_mpa]").fill("32");
  await form.locator("[name=exposure_class]").fill("C-2");
  await form.locator("[name=air_entrainment]").fill("5–8%");
  await form.locator("[name=slump_mm]").fill("100");
  await form.locator("[name=delivery_date]").fill(day(14));
  await form.locator("[name=delivery_window]").fill("7:00–9:00");
  await form.locator("[name=placement]").selectOption("Pump");
  await form.locator("[name=notes]").fill("Pier footings and the equipment pad (training)");
  await form.locator("[name=contractor_supplier_account_id]").selectOption({ index: 1 });
  await snap(pg, "s4-office-concrete-request", "#concrete");
  await form.locator("button:has-text('Save concrete request')").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Concrete request .* sent to BMR Winchester/);
  W.concrete = await newestShare(pg);
  await snap(pg, "s4-office-requests-sent", "[data-material-requests]");
});

async function sendMaterialRequest(pg, values, neededBy) {
  await go(pg, `/projects/${W.projectId}/deck-takeoff`);
  for (const [name, value] of Object.entries(values)) await pg.locator(`[name="${name}"]`).fill(value);
  await pg.fill("[name=facts_source]", "Manufacturer sheets (training)");
  await pg.locator("form:has([name=facts_source]) [name=actor_display_name]").fill("Ben Brayman (training)");
  await pg.click("button:has-text('Save product facts')");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Product facts saved/);
  await pg.locator("form:has(button:has-text('Download the supplier request')) [name=actor_display_name]").fill("Ben Brayman (training)");
  const download = pg.waitForEvent("download");
  await pg.click("button:has-text('Download the supplier request')");
  await (await download).path();
  await go(pg, `/projects/${W.projectId}/deck-takeoff`);
  const ids = await pg.locator("[data-send-to-supplier]").evaluateAll((fs) => fs.map((f) => f.dataset.sendToSupplier));
  W.sentRequests = W.sentRequests || [];
  const fresh = ids.find((id) => !W.sentRequests.includes(id));
  assert.ok(fresh, `a new supplier request was issued (${ids})`);
  W.sentRequests.push(fresh);
  const sendForm = pg.locator(`[data-send-to-supplier="${fresh}"]`);
  await sendForm.locator("[name=needed_by]").fill(neededBy);
  await sendForm.locator("button").click();
  await pg.waitForURL(/\/supplier-requests$/);
  assert.match(await flash(pg), /is in their Supplier Hub inbox now/);
}

async function newestShare(pg) {
  const art = pg.locator("article.supplier-share").first();
  return { number: await art.getAttribute("data-share"), id: Number((await art.getAttribute("id")).replace("share-", "")) };
}

// ------------------------------------------------------------------ modules 3 and 4: inbox and quotations

test("s3/s4: Darcy's inbox, and the material request quoted on his phone", async () => {
  const { pg } = await darcy();
  await go(pg, hub());
  assert.equal(await pg.locator("[data-attention-quotes]").getAttribute("data-attention-quotes"), "2");
  await snap(pg, "s3-inbox");
  await snap(pg, "s3-inbox-requests", "[data-supplier-inbox]");
  const dp = (await darcyPhone()).pg;
  await go(dp, hub());
  await noSideways(dp, "phone inbox");
  await snap(dp, "s3-inbox-phone");
  await pg.locator(`tr[data-share="${W.first.number}"] a`).click();
  await pg.waitForLoadState();
  assert.match(await pg.locator("main").innerText(), /Material request/i);
  await snap(pg, "s4-material-request");
  await snap(pg, "s4-material-quote-form", "[data-material-quote]", 140);
  await go(dp, hub(`requests/${W.first.id}`));
  await noSideways(dp, "phone quote form");
  await snap(dp, "s4-material-quote-phone", "[data-quote-lines]", 120);
  await priceMaterial(dp, 0);
  await dp.fill("[name=valid_until]", day(30));
  await dp.fill("[name=minutes_reported]", "14");
  await snap(dp, "s4-material-quote-send-phone", "[name=valid_until]", 200);
  await dp.locator("[data-material-quote] button:has-text('Return quote')").click();
  await dp.waitForLoadState();
  assert.match(await flash(dp), /Quote returned to the contractor/);
  await go(pg, hub(`requests/${W.first.id}`));
  await snap(pg, "s4-quote-returned");
});

// One SKU and one price per product, as the store has; the last line is left blank (not stocked).
async function priceMaterial(pg, seed) {
  const rows = pg.locator("tr[data-line]");
  const n = await rows.count();
  W.lines = n;
  for (let i = 0; i < n - 1; i += 1) {
    const row = rows.nth(i);
    const num = await row.getAttribute("data-line");
    const sku = row.locator(`[name=sku_${num}]`);
    if (!(await sku.inputValue())) await sku.fill(`BMR-${String(20400 + i * 7 + seed).padStart(5, "0")}`);
    await row.locator(`[name=unit_cost_${num}]`).fill(`${(12 + i * 3.4).toFixed(2)}`);
    await row.locator(`[name=discount_${num}]`).fill("5");
  }
}

test("s4: Darcy quotes the concrete request (BMR's price; Tomlinson supplies BMR)", async () => {
  const { pg } = await darcy();
  await go(pg, hub(`requests/${W.concrete.id}`));
  assert.match(await pg.locator("main").innerText(), /Concrete request/i);
  await snap(pg, "s4-concrete-request");
  const q = pg.locator("[data-concrete-quote]");
  await q.locator("[name=quote_number]").fill("BMR-CQ-1042");
  await q.locator("[name=price_per_m3]").fill("245.00");
  await q.locator("[name=pump_charge]").fill("350.00");
  await q.locator("[name=valid_until]").fill(day(21));
  await q.locator("[name=notes]").fill("32 MPa C-2, 5–8% air, from Tomlinson Ready-Mix (training)");
  await q.locator("[name=minutes_reported]").fill("6");
  await snap(pg, "s4-concrete-quote-form", "[data-concrete-quote]", 90);
  await q.locator("button:has-text('Return quote')").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Quote returned/);
  await snap(pg, "s4-concrete-quote-returned", "[data-quote-returned]", 300);
});

// ------------------------------------------------------------------ module 7: SKU reuse (an updated request)

test("s7: Ben records the first quote; his updated request arrives with Darcy's SKUs filled in", async () => {
  const { pg } = await ben();
  await recordAndApprove(pg, W.first.id);
  // The pool gate changes; Ben sends the updated request. The lines Darcy priced before keep his SKUs.
  await sendMaterialRequest(pg, { ...FACTS_V1, "gate.product_name": "Black aluminum self-closing pool gate (training)" }, day(10));
  W.second = await newestShare(pg);
  assert.notEqual(W.second.id, W.first.id);
  const dp = (await darcyPhone()).pg;
  await go(dp, hub(`requests/${W.second.id}`));
  const prefill = dp.locator("[data-sku-prefill]");
  assert.ok(await prefill.count(), "remembered SKUs are offered");
  assert.equal(await dp.locator("tr[data-line] [name^=unit_cost_]").first().inputValue(), "", "a price is never filled in");
  await snap(dp, "s7-sku-remembered-phone", "[data-sku-prefill]", 90);
  const { pg: d } = await darcy();
  await go(d, hub(`requests/${W.second.id}`));
  await snap(d, "s7-sku-remembered", "[data-sku-prefill]", 90);
  await priceMaterial(dp, 3);
  await dp.fill("[name=valid_until]", day(30));
  await dp.fill("[name=minutes_reported]", "6");
  await dp.locator("[data-material-quote] button:has-text('Return quote')").click();
  await dp.waitForLoadState();
  assert.match(await flash(dp), /Quote returned to the contractor/);
});

async function recordAndApprove(pg, shareId) {
  await go(pg, requestsPage());
  await share(pg, shareId).locator("a:has-text('Review the returned quote')").click();
  await pg.waitForLoadState();
  const notes = pg.locator("[name=notes_reviewed]");
  if (await notes.count()) await notes.check();
  await pg.locator("form:has(button:has-text('Record the ready prices')) [name=actor_display_name]").fill("Ben Brayman (training)");
  await pg.click("button:has-text('Record the ready prices')");
  await pg.waitForLoadState();
  const n = await pg.locator("button[name=status][value=APPROVED]").count();
  for (let i = 0; i < n; i += 1) {
    const form = pg.locator("form:has(button[name=status][value=APPROVED])").nth(i);
    const approver = form.locator("input[type=text], input:not([type])");
    for (let k = 0; k < (await approver.count()); k += 1) {
      if (!(await approver.nth(k).inputValue())) await approver.nth(k).fill("Ben Brayman (training)");
    }
    await form.locator("button[value=APPROVED]").click();
    await pg.waitForLoadState();
  }
}

// ------------------------------------------------------------------ module 5: orders and confirmations

test("s5: Ben places both orders; Darcy confirms them", async () => {
  const { pg } = await ben();
  await recordAndApprove(pg, W.second.id);
  await go(pg, requestsPage());
  const form = share(pg, W.second.id).locator(`[data-place-order="${W.second.id}"]`);
  await form.locator("[name=delivery_date]").fill(day(10));
  await form.locator("[name=delivery_window]").fill("8:00–10:00");
  await form.locator("[name=site_contact]").fill("Ben Brayman (training), 613-555-0100");
  await form.locator("[name=notes]").fill("Side gate on the left; pool is full, keep clear of the fence (training)");
  await snap(pg, "s5-office-place-order", `[data-place-order="${W.second.id}"]`, 160);
  await form.locator("button:has-text('Place order')").click();
  await pg.waitForLoadState();
  W.materialPo = (await flash(pg)).match(/Purchase order (\S+) sent/)[1];
  const art = share(pg, W.concrete.id);
  await art.locator("[data-approve-quote] button").click();
  await pg.waitForLoadState();
  const cform = share(pg, W.concrete.id).locator(`[data-place-order="${W.concrete.id}"]`);
  await cform.locator("[name=delivery_date]").fill(day(14));
  await cform.locator("[name=delivery_window]").fill("7:00–9:00");
  await cform.locator("[name=site_contact]").fill("Ben Brayman (training), 613-555-0100");
  await cform.locator("[name=notes]").fill("Pump truck from Harbour Lane; call 30 minutes ahead (training)");
  await cform.locator("button:has-text('Place order')").click();
  await pg.waitForLoadState();
  W.concretePo = (await flash(pg)).match(/Purchase order (\S+) sent/)[1];
  const { pg: d } = await darcy();
  await go(d, hub());
  assert.equal(await d.locator("[data-attention-orders]").getAttribute("data-attention-orders"), "2");
  await snap(d, "s5-orders-to-confirm", ".supplier-attention");
  await go(d, hub(`requests/${W.second.id}`));
  assert.equal(await d.locator("[data-supplier-order]").getAttribute("data-supplier-order"), "PLACED");
  await snap(d, "s5-order-to-confirm", "[data-supplier-order]");
  await snap(d, "s5-confirm-form", "[data-confirm-order]", 260);
  await d.locator("[data-confirm-order] [name=note]").fill("Boards and railing from the Winchester yard (training)");
  await d.click("[data-confirm-order] button[value=confirm]");
  await d.waitForLoadState();
  assert.match(await flash(d), new RegExp(`Order ${W.materialPo} confirmed`));
  await snap(d, "s5-order-confirmed", "[data-supplier-order]");
  await go(d, hub(`requests/${W.concrete.id}`));
  await d.locator("[data-confirm-order] [name=note]").fill("Booked with Tomlinson Ready-Mix (training)");
  await d.click("[data-confirm-order] button[value=confirm]");
  await d.waitForLoadState();
  assert.match(await flash(d), new RegExp(`Order ${W.concretePo} confirmed`));
  await go(pg, requestsPage());
  assert.match(await share(pg, W.second.id).locator("[data-po]").innerText(), /The order is agreed/);
  await snap(pg, "s5-office-order-agreed", `article#share-${W.second.id} [data-po]`, 120);
});

// ------------------------------------------------------------------ module 6: deliveries and changes

test("s6: deliveries, a change from each side, and the material order marked delivered", async () => {
  const dp = (await darcyPhone()).pg;
  await go(dp, hub("deliveries"));
  assert.match(await dp.locator(`tr[data-delivery="${W.materialPo}"]`).innerText(), /Agreed/);
  await noSideways(dp, "phone deliveries");
  await snap(dp, "s6-deliveries-phone");
  const { pg: d } = await darcy();
  await go(d, hub("deliveries"));
  await snap(d, "s6-deliveries");
  // Darcy asks: Tomlinson's plant has no truck that morning.
  await go(d, hub(`requests/${W.concrete.id}`));
  const ask = d.locator(`[data-request-change]`);
  await ask.locator("summary").click();
  await ask.locator("[name=new_date]").fill(day(15));
  await ask.locator("[name=new_window]").fill("10:00–12:00");
  await ask.locator("[name=reason]").selectOption("Supplier availability");
  await ask.locator("[name=note]").fill("Tomlinson Ready-Mix has no pump truck that morning (training)");
  await snap(d, "s6-request-change", "#delivery", 80);
  await ask.locator("button:has-text('Send the change')").click();
  await d.waitForLoadState();
  assert.match(await flash(d), /Delivery change sent to the contractor/);
  await snap(d, "s6-change-sent", "#delivery", 120);
  const { pg } = await ben();
  await go(pg, requestsPage());
  await share(pg, W.concrete.id).locator("[data-answer-change] button[value=accept]").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Answer sent to the supplier/);
  // Ben asks: rain is forecast, so the material delivery moves a day.
  await go(pg, requestsPage());
  const panel = share(pg, W.second.id).locator("#delivery");
  await panel.locator("summary:has-text('Change the delivery')").click();
  await panel.locator("[name=new_date]").fill(day(11));
  await panel.locator("[name=new_window]").fill("8:00–10:00");
  await panel.locator("[name=reason]").selectOption("Weather");
  await panel.locator("[name=note]").fill("Rain forecast; the yard will be soft (training)");
  await panel.locator("button:has-text('Send the change')").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Delivery change sent/);
  await go(dp, hub());
  assert.equal(await dp.locator("[data-changes-waiting]").getAttribute("data-changes-waiting"), "1");
  await snap(dp, "s6-change-waiting-phone", "[data-changes-waiting]", 80);
  await dp.locator("[data-changes-waiting] a").first().click();
  await dp.waitForLoadState();
  await noSideways(dp, "phone answer change");
  await snap(dp, "s6-answer-change-phone", "[data-delivery-change]", 120);
  await dp.click("[data-answer-change] button[value=accept]");
  await dp.waitForLoadState();
  assert.match(await flash(dp), /Answer sent to the contractor/);
  assert.equal(await dp.locator("[data-delivery-agreed]").getAttribute("data-delivery-agreed"), "yes");
  await snap(dp, "s6-change-accepted-phone", "#delivery", 80);
  // The boards arrive: Darcy marks the order delivered on his phone (the training site allows today).
  const mark = dp.locator("[data-mark-delivered]");
  await mark.locator("summary").click();
  await mark.locator("[name=note]").fill("Unloaded at the side gate (training)");
  await snap(dp, "s6-mark-delivered-phone", "[data-mark-delivered]", 160);
  await mark.locator("button:has-text('Mark delivered')").click();
  await dp.waitForLoadState();
  assert.match(await flash(dp), new RegExp(`Order ${W.materialPo} marked delivered`));
  await snap(dp, "s6-delivered-phone", "[data-order-delivered]", 200);
  await go(d, hub(`requests/${W.second.id}`));
  await snap(d, "s10-request-history", ".supplier-history", 120);
});

// ------------------------------------------------------------------ modules 3 and 7: dashboard and demand

test("s3/s7: Darcy's dashboard and material demand", async () => {
  const { pg } = await darcy();
  await go(pg, hub("dashboard?period=month"));
  await snap(pg, "s3-dashboard");
  await snap(pg, "s3-dashboard-figures", "[data-period-figures]", 80);
  await go(pg, hub("demand?period=month"));
  await snap(pg, "s7-demand");
  await snap(pg, "s7-demand-products", "[data-demand-category]", 140);
  const dp = (await darcyPhone()).pg;
  await go(dp, hub("dashboard?period=month"));
  await noSideways(dp, "phone dashboard");
  await snap(dp, "s3-dashboard-phone", "[data-period-figures]", 70);
});

// ------------------------------------------------------------------ module 8: PRO Desk set-up (pricing)

const PRICES = [ // sku, description, unit, price, discount, rule — synthetic training prices
  ["BMR-T-POST", "Laminated column 3-ply 2x6 (training)", "EA", "62.00", "", ""],
  ["BMR-T-2416", "2x4x16 SPF (training)", "EA", "9.25", "", ""],
  ["BMR-T-PT2816", "2x8x16 treated (training)", "EA", "31.50", "", ""],
  ["BMR-T-PANEL", "Steel panel, cut to length (training)", "LF", "4.10", "5", "Farm account 5% (training)"],
  ["BMR-T-TRIM10", "Steel trim, 10 ft (training)", "EA", "21.00", "", ""],
  ["BMR-T-OH1010", "Overhead door 10x10 (training)", "EA", "1650.00", "", ""],
  ["BMR-T-MAN3068", "Steel man door 3068 (training)", "EA", "425.00", "", ""],
  ["BMR-T-SCREW250", "Cladding screws, box of 250 (training)", "BOX", "38.00", "", ""],
];
const MATCHES = { // takeoff line → [sku, selling units per takeoff unit]
  "CAL-OB-POST": ["BMR-T-POST", "1"], "CAL-OB-PURLIN-2X4-SPF": ["BMR-T-2416", "0.0625"],
  "CAL-OB-GIRT-2X4-SPF": ["BMR-T-2416", "0.0625"], "CAL-OB-SKIRT-2X8-PRESSURE-TREATED": ["BMR-T-PT2816", "0.0625"],
  "CAL-OB-ROOF-PANEL": ["BMR-T-PANEL", "1"], "CAL-OB-WALL-PANEL": ["BMR-T-PANEL", "1"],
  "CAL-OB-RIDGE-CAP": ["BMR-T-TRIM10", "0.1"], "CAL-OB-TRIM-EAVE": ["BMR-T-TRIM10", "0.1"],
  "CAL-OB-TRIM-RAKE": ["BMR-T-TRIM10", "0.1"], "CAL-OB-TRIM-CORNER": ["BMR-T-TRIM10", "0.1"],
  "CAL-OB-TRIM-BASE": ["BMR-T-TRIM10", "0.1"], "CAL-OB-TRIM-OPENING": ["BMR-T-TRIM10", "0.1"],
  "CAL-OB-DOOR-OH-120X120": ["BMR-T-OH1010", "1"], "CAL-OB-DOOR-MAN-36X80": ["BMR-T-MAN3068", "1"],
  "CAL-OB-CLADDING-SCREW": ["BMR-T-SCREW250", "0.004"],
};
const STANDARD = {
  building_system: "POST_FRAME_STEEL", roof_type: "GABLE", eave_overhang_in: "12", gable_overhang_in: "12",
  post_spacing_ft: "8", endwall_post_spacing_ft: "10", post_description: "3-ply 2×6 laminated column, treated",
  truss_spacing_ft: "8", purlin_spacing_in: "24", purlin_lumber: "2×4 SPF", girt_spacing_in: "24", girt_lumber: "2×4 SPF",
  skirt_lumber: "2×8 pressure-treated", roof_panel_coverage_in: "36", wall_panel_coverage_in: "36", screws_per_sqft: "0.8",
};
const QUICK = { width_ft: "30", length_ft: "40", wall_height_ft: "12", roof_pitch: "4", foundation: "NONE",
  qd_0_kind: "OVERHEAD_DOOR", qd_0_count: "1", qd_0_width_in: "120", qd_0_height_in: "120", qd_0_wall: "LEFT",
  qd_1_kind: "MAN_DOOR", qd_1_count: "1", qd_1_width_in: "36", qd_1_height_in: "80", qd_1_wall: "FRONT" };

async function fill(pg, scope, values) {
  for (const [key, value] of Object.entries(values)) {
    const field = pg.locator(`${scope} [name="${key}"]`);
    if ((await field.evaluate((el) => el.tagName)) === "SELECT") await field.selectOption(value); else await field.fill(value);
  }
}

test("s8: Pat sets up the PRO Desk: quote settings, the price file and a standard building", async () => {
  const { pg } = await pat();
  await go(pg, hub());
  await snap(pg, "s9-pro-desk-button", "[data-pro-desk-link]", 120);
  await pg.click("[data-pro-desk-link]");
  await pg.waitForLoadState();
  assert.match(await pg.locator("main").innerText(), /Before the first quotation/);
  await snap(pg, "s8-pro-desk-before-setup");
  await pg.click("a:has-text('Quote settings')");
  await pg.waitForLoadState();
  await fill(pg, "[data-quote-settings]", { tax_label: "HST", tax_rate_percent: "13", validity_days: "30",
    default_delivery_charge: "150", contact_line: "613-555-0199 · prodesk@training.calibraytai.invalid · Winchester (training)" });
  await pg.fill("[name=terms_text]", "Training quotation. Synthetic prices, not BMR's real prices. Materials only; labour, installation and permits not included.");
  await snap(pg, "s8-quote-settings");
  await pg.click("button:has-text('Save settings')");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Quote settings saved/);
  // The store's own price file: a CSV with a header row.
  const csv = path.join(tmp, "bmr-winchester-training-prices.csv");
  const from = day(-3);
  fs.writeFileSync(csv, ["sku,description,unit,price,discount_percent,discount_rule,effective_from,availability",
    ...PRICES.map(([s, d, u, p, disc, rule]) => [s, `"${d}"`, u, p, disc, `"${rule}"`, from, "IN_STOCK"].join(","))].join("\n") + "\n");
  await go(pg, hub("pro-desk/prices"));
  await pg.setInputFiles("[name=price_file]", csv);
  await pg.fill("[name=authorized_by]", "Darcy, store manager (training)");
  await pg.check("[name=demo_synthetic]");
  await snap(pg, "s8-price-file-load", "[data-price-file-form]", 90);
  await pg.click("button:has-text('Load prices')");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /8 prices loaded; 0 rows not loaded/);
  await snap(pg, "s8-price-file-loaded");
  // A standard building for Quick Quote, set up once.
  await go(pg, hub("pro-desk/standards"));
  await pg.fill("[data-standard-form] [name=name]", "Post-frame steel, 8 ft bays (training)");
  await pg.fill("[data-standard-form] [name=basis]", "BMR Winchester store standard (training, synthetic)");
  await fill(pg, "[data-standard-form]", STANDARD);
  await pg.check("[data-standard-form] [name=demo_synthetic]");
  await snap(pg, "s8-standard-building-form", "[data-standard-form]", 80);
  await pg.click("button:has-text('Save the standard')");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /saved for Quick Quote/);
  await snap(pg, "s8-standard-building");
});

// ------------------------------------------------------------------ module 9: the walk-in quotation

test("s8/s9: Pat quotes a walk-in customer: sketch, product matches, quotation, customer link, order", async () => {
  const { pg, ctx } = await pat();
  await go(pg, hub("pro-desk/"));
  await snap(pg, "s9-pro-desk");
  await pg.click("[data-quick-quote]");
  await pg.waitForURL(/pro-desk\/quick$/);
  await pg.fill("[name=customer_name]", "Jordan Tremblay (training walk-in)");
  await pg.fill("[name=customer_phone]", "613-555-0177");
  await pg.fill("[name=customer_email]", "jordan.tremblay@training.calibraytai.invalid");
  await pg.fill("[name=customer_town]", "Winchester");
  await pg.check("[name=consent_email]");
  await pg.check("[name=demo_synthetic]");
  await snap(pg, "s9-quick-quote-customer", "[data-quick-form]", 80);
  await fill(pg, "[data-quick-form]", QUICK);
  await pg.setInputFiles("[data-quick-form] [name=sketch]", SKETCH);
  await snap(pg, "s9-quick-quote-size", ".pd-quick-doors", 260);
  await pg.click("[data-quick-submit]");
  await pg.waitForURL(/pro-desk\/\d+#pricing$/);
  const quoteUrl = pg.url().split("#")[0];
  W.quoteUrl = quoteUrl;
  await snap(pg, "s9-sketch-kept", "#sketch", 80);
  await snap(pg, "s9-building-from-standard", "#building", 80);
  await snap(pg, "s9-materials", "#materials", 80);
  // One-time product matches: each takeoff line the store sells gets its SKU and unit conversion.
  let first = true;
  for (const [code, [sku, factor]] of Object.entries(MATCHES)) {
    const row = pg.locator(`[data-price-line="${code}"]`);
    if (!(await row.count())) continue;
    if ((await row.getAttribute("data-price-status")) !== "NO_PRODUCT") continue;
    await row.locator("summary:has-text('Match a product')").click();
    const form = row.locator("[data-match-form]");
    const value = await form.locator("select[name=product_id] option").evaluateAll(
      (opts, s) => (opts.find((o) => o.textContent.startsWith(`${s} ·`)) || {}).value, sku);
    assert.ok(value, `${sku} is in the price file`);
    await form.locator("select[name=product_id]").selectOption(value);
    await form.locator("[name=sales_per_unit]").fill(factor);
    if (first) { await snap(pg, "s8-match-product", `[data-price-line="${code}"]`, 160); first = false; }
    await form.locator("button:has-text('Match')").click();
    await pg.waitForLoadState();
  }
  // Trusses come from the truss manufacturer: left out with a reason.
  const truss = pg.locator("[data-price-line^='CAL-OB-TRUSS']");
  if (await truss.count()) {
    await truss.locator("summary:has-text('Leave out')").click();
    await truss.locator("[name=exclude_reason]").fill("Truss quote to follow from the truss manufacturer");
    await truss.locator("button:has-text('Leave out')").click();
    await pg.waitForLoadState();
  }
  await go(pg, `${quoteUrl}#pricing`);
  await snap(pg, "s9-pricing", "#pricing", 80);
  const blockers = await pg.locator("[data-blockers]").count();
  if (blockers) console.log("BLOCKERS", await pg.locator("[data-blockers]").innerText());
  assert.equal(blockers, 0, "nothing left open before issue");
  await snap(pg, "s9-quotation-totals", "#quotation", 80);
  await pg.click("[data-issue]");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /issued/);
  await snap(pg, "s9-issued", "#quotation", 80);
  const pdf = await ctx.request.get(`${quoteUrl}/quotation.pdf`);
  assert.equal(pdf.status(), 200);
  await pg.click("button:has-text('Create approval link')");
  await pg.waitForLoadState();
  const link = (await pg.locator("[data-approval-link]").innerText()).trim();
  await snap(pg, "s9-approval-link", "#approval", 80);
  // The customer opens the link on a phone and accepts.
  const customer = await session("customer", PHONE, null);
  await go(customer.pg, link);
  await noSideways(customer.pg, "customer link");
  await snap(customer.pg, "s9-customer-link-phone");
  await customer.pg.fill("[name=customer_name]", "Jordan Tremblay (training walk-in)");
  await customer.pg.check("[name=agree]");
  await snap(customer.pg, "s9-customer-accept-phone", "[data-customer-answer]", 60);
  await customer.pg.click("button[value=accept]");
  await customer.pg.waitForLoadState();
  assert.match(await customer.pg.locator("h2").first().innerText(), /accepted/);
  await snap(customer.pg, "s9-customer-accepted-phone");
  await go(pg, `${quoteUrl}#approval`);
  await snap(pg, "s9-accepted", "#approval", 80);
  await pg.click("[data-order-ready]");
  await pg.waitForURL(/\/order$/);
  await snap(pg, "s9-order");
  await go(pg, hub("pro-desk/timing"));
  await snap(pg, "s9-timing");
});

// ------------------------------------------------------------------ module 10: acceptance tests

test("s10: the Training Centre acceptance tests and the end of the day", async () => {
  const d = await session("darcyTraining", DESK, facts.people.darcy, "/supplier/login", "/training");
  await go(d.pg, "/training/uat");
  await snap(d.pg, "s10-uat-list");
  const first = d.pg.locator("a[href^='/training/uat/']").first();
  if (await first.count()) {
    await first.click();
    await d.pg.waitForLoadState();
    await snap(d.pg, "s10-uat-case");
  }
  const { pg } = await darcy();
  await go(pg, hub());
  await snap(pg, "s10-inbox-end-of-day");
  assert.deepEqual(serverErrors, [], "no 500 responses");
  assert.deepEqual(pageErrors, [], "no page script errors");
});
