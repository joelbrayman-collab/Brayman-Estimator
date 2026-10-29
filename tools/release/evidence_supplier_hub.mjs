// Release evidence for the contractor-initiated Supplier Hub, as the supplier employee Darcy sees it
// (Joel, 20 Oct 2026). The nine demonstration steps, in order, in a real browser: 1 the office sends a
// material request → 2 Darcy signs in and receives it → 3 Darcy returns the quotation on screen →
// 4 the office reviews, records and approves it → 5 the office places the purchase order → 6 Darcy
// confirms it → 7 the delivery is scheduled on both sides → 8 a delivery change from either side and its
// answer → 9 completion: Darcy marks the order delivered → 10 the office cancels another (the rival
// store's) confirmed order and that store sees it cancelled. Then Darcy's dashboard, reporting periods, needs attention and material demand,
// and isolation (a second supplier, the contractor's internal costs). Office on desktop; Darcy on desktop
// and a 390 px phone with no sideways scrolling. Local office on a temporary database
// (tests/supplier_hub_page_server.py), synthetic data only.
// EVIDENCE_SHOTS=<folder> also saves a screenshot of each screen.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = [390, 844];
const DESK = [1440, 900];
const serverErrors = []; // every response of 500 or more, from any page in the walk
const darcyPages = []; // every Supplier Hub page Darcy saw: {label, html}
let screens = 0;
const W = {}; // what the walk learns as it goes (share, order, totals)

const day = (n) => { const d = new Date(`${facts.today}T12:00:00`); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
const money = (text) => { const m = String(text).replace(/,/g, "").match(/-?\d+(\.\d+)?/); assert.ok(m, `no amount in "${text}"`); return Number(m[0]); };

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/supplier_hub_page_server.py")], {
    cwd: REPO, env: { ...process.env, SUPPLIER_HUB_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("Supplier Hub office did not start\n" + out)), 120000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("Supplier Hub office exited\n" + out)); }
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
  console.log(`SUPPLIER_HUB_SCREENS=${screens} SERVER_ERRORS=${serverErrors.length}`);
});

const sessions = {};
async function session(key, [width, height], [email, password], loginPath) {
  if (sessions[key]) return sessions[key];
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  await pg.goto(`${base}${loginPath}`);
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await pg.click("button[type=submit]");
  await pg.waitForLoadState();
  sessions[key] = { ctx, pg, errors };
  return sessions[key];
}
const office = () => session("office", DESK, facts.office, "/login");
const darcyDesk = () => session("darcyDesk", DESK, facts.darcy, "/supplier/login");
const darcyPhone = () => session("darcyPhone", PHONE, facts.darcy, "/supplier/login");

async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function screen(pg, name, { darcy = false } = {}) {
  screens += 1;
  if (darcy) darcyPages.push({ label: name, html: await pg.content() });
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${String(screens).padStart(2, "0")}-${name}.png`), fullPage: true });
}
// Text inside a closed <details> (history lists), whitespace collapsed.
async function hidden(loc) { return (await loc.textContent()).replace(/\s+/g, " "); }
async function flash(pg) { return (await pg.locator(".flash, .flash-stack .alert").allInnerTexts()).join(" | "); }
async function go(pg, url) { const r = await pg.goto(`${base}${url}`); await pg.waitForLoadState(); return r; }
const hub = (rest = "") => `/supplier/${facts.bmr_id}/${rest}`;
const requests = () => `/projects/${facts.project_id}/supplier-requests`;
function article(pg) { return pg.locator(`article#share-${W.shareId}`); }

test("step 1: the office sends the material request to BMR from the deck takeoff", async () => {
  const { pg } = await office();
  await go(pg, `/projects/${facts.project_id}/deck-takeoff`);
  const form = pg.locator(`[data-send-to-supplier="${facts.request_id}"]`);
  await form.locator("[name=needed_by]").fill(day(10));
  await screen(pg, "office-deck-takeoff-send");
  await form.locator("button[type=submit]").click();
  await pg.waitForURL(/\/supplier-requests$/);
  assert.match(await flash(pg), /is in their Supplier Hub inbox now/);
  const art = pg.locator("article.supplier-share").first();
  W.shareNumber = await art.getAttribute("data-share");
  W.shareId = Number((await art.getAttribute("id")).replace("share-", ""));
  assert.equal(await art.getAttribute("data-share-status"), "SENT");
  assert.match(await art.innerText(), /Sent, not opened/);
  await screen(pg, "office-request-sent");
});

test("step 2: Darcy signs in and the request is waiting (desktop and phone)", async () => {
  for (const [who, label] of [[darcyDesk, "desktop"], [darcyPhone, "phone"]]) {
    const { pg } = await who();
    assert.ok(pg.url().endsWith(hub()), `${label}: one area goes straight to the inbox (${pg.url()})`);
    const row = pg.locator(`tr[data-share="${W.shareNumber}"]`);
    assert.match(await row.innerText(), /New/);
    assert.equal(await pg.locator("[data-attention-quotes]").getAttribute("data-attention-quotes"), "1");
    assert.ok((await pg.content()).includes(facts.earlier_number), "the earlier request is listed too");
    await noSideways(pg, `${label} inbox`);
    await screen(pg, `darcy-${label}-inbox`, { darcy: true });
  }
  const { pg } = await darcyDesk();
  await pg.locator(`tr[data-share="${W.shareNumber}"] a`).click();
  await pg.waitForLoadState();
  const text = await pg.locator("main").innerText();
  assert.match(text, /Material request/i);
  assert.match(text, /Needed by/);
  assert.ok(text.includes(day(10)), "needed-by date shown");
  assert.equal(await pg.locator("[data-material-quote]").count(), 1);
  await screen(pg, "darcy-desktop-request", { darcy: true });
  const o = (await office()).pg;
  await go(o, requests());
  assert.match(await article(o).innerText(), /Opened by the supplier/);
});

test("step 3: Darcy returns the quotation on screen, on the phone", async () => {
  const { pg } = await darcyPhone();
  await go(pg, hub(`requests/${W.shareId}`));
  // SKUs Darcy quoted on the earlier, recorded request are suggested; prices never are.
  assert.ok(Number(await pg.locator("[data-sku-prefill]").getAttribute("data-sku-prefill")) > 0, "remembered SKUs offered");
  const firstPrice = pg.locator("tr[data-line] [name^=unit_cost_]").first();
  assert.equal(await firstPrice.inputValue(), "", "a price is never prefilled");
  await noSideways(pg, "phone quote form");
  // Every price box is on screen at 390 px: no sideways scrolling inside the quote table either.
  const box = await firstPrice.boundingBox();
  assert.ok(box && box.x >= 0 && box.x + box.width <= PHONE[0], `unit cost box is off screen at x=${box && box.x}`);
  await screen(pg, "darcy-phone-quote-form", { darcy: true });
  const rows = pg.locator("tr[data-line]");
  const n = await rows.count();
  W.lines = n;
  const prices = new Map(); // the store has one price per SKU
  for (let i = 0; i < n - 1; i += 1) { // the last line (structural screws) is left unpriced, as on the earlier request
    const row = rows.nth(i);
    const num = await row.getAttribute("data-line");
    const sku = row.locator(`[name=sku_${num}]`);
    if (!(await sku.inputValue())) await sku.fill(`BMR-${String(5000 + i).padStart(5, "0")}`); // keep a remembered SKU
    const code = await sku.inputValue();
    if (!prices.has(code)) prices.set(code, `${10 + prices.size * 2}.25`);
    await row.locator(`[name=unit_cost_${num}]`).fill(prices.get(code));
    await row.locator(`[name=discount_${num}]`).fill("5");
  }
  await pg.fill("[name=valid_until]", day(30));
  await pg.fill("[name=minutes_reported]", "15");
  await pg.locator("[data-material-quote] button[type=submit]").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Quote returned to the contractor/);
  const returned = await pg.locator("[data-quote-returned]").innerText();
  assert.match(returned, new RegExp(`Returned by ${facts.darcy_name}|returned by ${facts.darcy_name}`, "i"));
  assert.match(returned, new RegExp(`${n - 1} of ${n} lines priced`));
  W.quotedTotal = money(await pg.locator("[data-quote-returned] strong").innerText());
  assert.ok(W.quotedTotal > 0, "a quoted total");
  await noSideways(pg, "phone quote returned");
  await screen(pg, "darcy-phone-quote-returned", { darcy: true });
});

test("step 4: the office reviews the returned quote, records it and approves the costs", async () => {
  const { pg } = await office();
  await go(pg, requests());
  const art = article(pg);
  assert.equal(await art.getAttribute("data-share-status"), "RETURNED");
  assert.match(await art.innerText(), new RegExp(`Quote returned.*by ${facts.darcy_name}`));
  assert.match(await art.locator("[data-order-blocked]").innerText(), /Record/);
  await art.locator("a:has-text('Review the returned quote')").click();
  await pg.waitForLoadState();
  assert.equal(money(await pg.locator("[data-recordable-total]").innerText()), W.quotedTotal,
    "the office sees the same quoted total Darcy returned");
  assert.match(await pg.locator("main").innerText(), /Ready to record/);
  await screen(pg, "office-returned-quote");
  const notes = pg.locator("[name=notes_reviewed]");
  if (await notes.count()) await notes.check();
  await pg.click("button:has-text('Record the ready prices')");
  await pg.waitForLoadState();
  const approve = pg.locator("button[name=status][value=APPROVED]");
  const count = await approve.count();
  assert.ok(count > 0, "recorded lines can be approved");
  for (let i = 0; i < count; i += 1) {
    await pg.locator("button[name=status][value=APPROVED]").nth(i).click();
    await pg.waitForLoadState();
    assert.match(await flash(pg), /Contractor cost approved/, `approval ${i + 1}`);
  }
  assert.equal(await pg.locator("text=Latest decision: approved").count(), count, "every recorded line approved");
  await screen(pg, "office-costs-approved");
  W.approved = count;
});

// Supplier Native Signing (FG-041): placing, confirming and agreeing a delivery change are signed.
async function sign(scope, name) {
  await scope.locator("[name=sign_consent]").check();
  await scope.locator("[name=signer_name]").fill(name);
}

test("step 5: the office places the purchase order", async () => {
  const { pg } = await office();
  await go(pg, requests());
  const form = article(pg).locator(`[data-place-order="${W.shareId}"]`);
  const summary = await form.locator("p").first().innerText();
  W.orderPreview = money(summary.split("total")[1]);
  await form.locator("[name=delivery_date]").fill(day(12));
  await form.locator("[name=delivery_window]").fill("7:00–9:00");
  await form.locator("[name=site_contact]").fill("Ben (synthetic)");
  await form.locator("[name=notes]").fill("Call Ben 30 minutes before arrival.");
  await sign(form, "Ben Synthetic");
  await screen(pg, "office-place-order");
  await form.locator("[data-calisign-po-send]").click(); // CaliSIGN: "Sign & Send for E-Signature" places the order
  await pg.waitForLoadState();
  assert.match(await flash(pg), /It is agreed when they sign and confirm it/);
  const po = article(pg).locator("[data-po]");
  assert.equal(await po.getAttribute("data-po"), "PLACED");
  W.poNumber = (await po.locator("strong").innerText()).replace("Purchase order ", "").trim();
  assert.equal(money((await po.innerText()).split("—")[1]), W.orderPreview, "order total matches the order preview");
  assert.match(await po.innerText(), /Waiting for the supplier to confirm/);
  await screen(pg, "office-order-placed");
});

test("step 6: Darcy confirms the order on the desktop; the office sees it agreed", async () => {
  const { pg } = await darcyDesk();
  await go(pg, hub());
  assert.equal(await pg.locator("[data-attention-orders]").getAttribute("data-attention-orders"), "1");
  assert.match(await pg.locator(`tr[data-share="${W.shareNumber}"]`).innerText(), new RegExp(`${W.poNumber} — to confirm`));
  await pg.locator(`tr[data-share="${W.shareNumber}"] a`).click();
  await pg.waitForLoadState();
  const order = pg.locator("[data-supplier-order]");
  assert.equal(await order.getAttribute("data-supplier-order"), "PLACED");
  const text = await order.innerText();
  assert.ok(text.includes(facts.address), "the order carries the site address");
  assert.ok(text.includes("Ben (synthetic)") && text.includes("Call Ben 30 minutes"), "site contact and notes");
  // Each ordered line is quantity × net, net = unit cost less 5%, to the cent; the lines add up to the total.
  const cells = await order.locator("tbody tr").evaluateAll((trs) => trs.map((tr) => [...tr.cells].map((c) => c.innerText.trim())));
  let sum = 0;
  for (const [, , , qty, , net, value] of cells) {
    assert.ok(Math.abs(Number(qty) * Number(net) - Number(value)) < 0.006, `line ${qty} × ${net} ≠ ${value}`);
    sum += Number(value);
  }
  assert.ok(Math.abs(sum - W.orderPreview) < 0.01, `ordered lines ${sum} ≠ order total ${W.orderPreview}`);
  assert.equal(await pg.locator("[name=expected_delivery]").inputValue(), day(12), "the requested date is offered");
  await screen(pg, "darcy-desktop-order-to-confirm", { darcy: true });
  await pg.locator("[name=note]").first().fill("Boards from the Winchester yard (synthetic).");
  await sign(pg.locator("[data-confirm-order]"), facts.darcy_name);
  await pg.click("button[value=confirm]");
  await pg.waitForLoadState();
  assert.match(await flash(pg), new RegExp(`Order ${W.poNumber} signed and confirmed`));
  assert.match(await pg.locator("[data-order-answer]").innerText(), new RegExp(`Confirmed.*by ${facts.darcy_name}`));
  await screen(pg, "darcy-desktop-order-confirmed", { darcy: true });
  const o = (await office()).pg;
  await go(o, requests());
  const po = await article(o).locator("[data-po]").innerText();
  assert.match(po, /The order is agreed\./);
  assert.ok(po.includes(`agreed delivery ${day(12)} 7:00–9:00`), po);
  await screen(o, "office-order-agreed");
});

test("step 7: the delivery is scheduled on both sides", async () => {
  const { pg } = await darcyPhone();
  await go(pg, hub("deliveries"));
  const row = pg.locator(`tr[data-delivery="${W.poNumber}"]`);
  assert.match(await row.innerText(), /Agreed/);
  assert.ok((await row.innerText()).includes("7:00–9:00"));
  await noSideways(pg, "phone deliveries");
  await screen(pg, "darcy-phone-deliveries", { darcy: true });
  await go(pg, hub());
  assert.equal(await pg.locator("[data-attention-upcoming]").getAttribute("data-attention-upcoming"), "1");
  const o = (await office()).pg;
  await go(o, "/deliveries");
  assert.ok((await o.locator("main").innerText()).includes(W.poNumber), "the office's deliveries list has the order");
  await screen(o, "office-deliveries");
  await go(o, requests());
  assert.match(await o.locator("[data-project-deliveries]").innerText(), new RegExp(`${W.poNumber}.*agreed`));
});

test("step 8: either side asks to move the delivery, and the other answers", async () => {
  // The office asks; Darcy accepts on his phone.
  const o = (await office()).pg;
  await go(o, requests());
  const panel = article(o).locator("#delivery");
  await panel.locator("summary:has-text('Change the delivery')").click();
  await panel.locator("[name=new_date]").fill(day(13));
  await panel.locator("[name=new_window]").fill("10:00–12:00");
  await panel.locator("[name=reason]").selectOption("Weather");
  await panel.locator("[name=note]").fill("Rain forecast (synthetic)");
  await sign(panel.locator("[data-request-change]"), "Ben Synthetic");
  await panel.locator("button:has-text('Send the change')").click();
  await o.waitForLoadState();
  assert.match(await flash(o), /Delivery change sent/);
  const { pg } = await darcyPhone();
  await go(pg, hub());
  assert.equal(await pg.locator("[data-changes-waiting]").getAttribute("data-changes-waiting"), "1");
  assert.equal(await pg.locator("[data-attention-changes]").getAttribute("data-attention-changes"), "1");
  await noSideways(pg, "phone change waiting");
  await screen(pg, "darcy-phone-change-waiting", { darcy: true });
  await pg.locator("[data-changes-waiting] a").first().click();
  await pg.waitForLoadState();
  assert.equal(await pg.locator("[data-delivery-change]").getAttribute("data-delivery-change"), "PENDING");
  assert.match(await pg.locator("[data-delivery-change]").innerText(), /Weather/);
  await noSideways(pg, "phone answer change");
  await screen(pg, "darcy-phone-answer-change", { darcy: true });
  await sign(pg.locator("[data-answer-change]"), facts.darcy_name);
  await pg.click("[data-answer-change] button[value=accept]");
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Answer sent to the contractor/);
  assert.equal(await pg.locator("[data-delivery-agreed]").getAttribute("data-delivery-agreed"), "yes");
  assert.match(await pg.locator("[data-delivery-agreed]").innerText(), /10:00–12:00/);
  await go(o, requests());
  assert.ok((await article(o).locator("[data-po]").innerText()).includes(`agreed delivery ${day(13)} 10:00–12:00`));
  assert.match(await hidden(article(o).locator(".delivery-history")), new RegExp(`accepted by ${facts.darcy_name}`));
  // Darcy asks; the office declines with a note; Darcy sees the answer and the agreed date stands.
  await go(pg, hub(`requests/${W.shareId}`));
  await pg.locator("summary:has-text('Change the delivery')").click();
  await pg.locator("[data-request-change] [name=new_date]").fill(day(15));
  await pg.locator("[data-request-change] [name=reason]").selectOption("Supplier availability");
  await pg.locator("[data-request-change] [name=note]").fill("Truck in for service (synthetic)");
  await sign(pg.locator("[data-request-change]"), facts.darcy_name);
  await noSideways(pg, "phone request change");
  await pg.locator("button:has-text('Send the change')").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), /Delivery change sent to the contractor/);
  await go(o, requests());
  const pending = article(o).locator("[data-delivery-change=PENDING]");
  assert.match(await pending.innerText(), new RegExp(`Change requested by ${facts.darcy_name}`));
  await pending.locator("[name=note]").fill("Site crew booked that day (synthetic)");
  await pending.locator("button[value=decline]").click();
  await o.waitForLoadState();
  assert.match(await flash(o), /Answer sent to the supplier/);
  await screen(o, "office-change-declined");
  await go(pg, hub(`requests/${W.shareId}`));
  const history = await hidden(pg.locator(".delivery-history"));
  assert.match(history, /declined/);
  assert.ok(history.includes("Site crew booked that day"), "Darcy sees the decline note");
  assert.match(await pg.locator("[data-delivery-agreed]").innerText(), /10:00–12:00/, "the agreed delivery stands");
  await screen(pg, "darcy-phone-change-declined", { darcy: true });
});

test("step 9: completion — Darcy marks the confirmed order delivered on his phone", async () => {
  // Joel, 21 Oct 2026: a confirmed order can be marked delivered by either side (date, optional note).
  const { pg } = await darcyPhone();
  await go(pg, hub(`requests/${W.shareId}`));
  assert.equal(await pg.locator("[data-supplier-order]").getAttribute("data-supplier-order"), "CONFIRMED");
  const form = pg.locator("[data-mark-delivered]");
  await form.locator("summary").click();
  assert.equal(await form.locator("[name=delivered_on]").inputValue(), facts.today, "today is offered");
  await form.locator("[name=note]").fill("Unloaded at the side gate (synthetic)");
  await noSideways(pg, "phone mark delivered");
  await screen(pg, "darcy-phone-mark-delivered", { darcy: true });
  await form.locator("button:has-text('Mark delivered')").click();
  await pg.waitForLoadState();
  assert.match(await flash(pg), new RegExp(`Order ${W.poNumber} marked delivered`));
  assert.equal(await pg.locator("[data-supplier-order]").getAttribute("data-supplier-order"), "DELIVERED");
  assert.equal(await pg.locator("[data-order-delivered]").getAttribute("data-order-delivered"), facts.today);
  assert.match(await pg.locator("[data-order-delivered]").innerText(), /Delivered on .+Unloaded at the side gate/);
  assert.equal(await pg.locator("summary:has-text('Change the delivery')").count(), 0, "a delivered order cannot be moved");
  await screen(pg, "darcy-phone-order-delivered", { darcy: true });
  await go(pg, hub("deliveries"));
  assert.equal(await pg.locator(`tr[data-delivery="${W.poNumber}"]`).count(), 0, "it leaves upcoming deliveries");
  await go(pg, hub("dashboard"));
  assert.match(await pg.locator("main").innerText(), /marked delivered here by you or the contractor/);
  const o = (await office()).pg;
  await go(o, requests());
  assert.equal(await article(o).locator("[data-po]").getAttribute("data-po"), "DELIVERED");
  assert.match(await article(o).locator("[data-po]").innerText(), new RegExp(`Delivered on .+recorded by ${facts.darcy_name}.+Unloaded at the side gate`));
  assert.equal(await article(o).locator("[data-cancel-order]").count(), 0, "a delivered order cannot be cancelled");
  await go(o, "/deliveries");
  assert.ok(!(await o.locator("main").innerText()).includes(W.poNumber), "gone from the office's deliveries");
  await screen(o, "office-order-delivered");
});

test("step 10: the office cancels a confirmed order with a reason; the supplier sees it cancelled", async () => {
  // The rival store's concrete request (seeded) is quoted, ordered and confirmed, then cancelled before delivery.
  const rival = await session("rival", PHONE, facts.rival, "/supplier/login");
  const rp = rival.pg;
  const rhub = (rest = "") => `/supplier/${facts.rival_id}/${rest}`;
  await go(rp, rhub(`requests/${facts.rival_share_id}`));
  const quote = rp.locator("[data-concrete-quote]");
  await quote.locator("[name=price_per_m3]").fill("205");
  await quote.locator("[name=valid_until]").fill(day(20));
  await quote.locator("button:has-text('Return quote')").click();
  await rp.waitForLoadState();
  const o = (await office()).pg;
  const second = `/projects/${facts.second_id}/supplier-requests`;
  await go(o, second);
  const art = o.locator(`article#share-${facts.rival_share_id}`);
  await art.locator("[data-approve-quote] button").click();
  await o.waitForLoadState();
  await sign(o.locator(`article#share-${facts.rival_share_id} [data-place-order]`), "Ben Synthetic");
  await o.locator(`article#share-${facts.rival_share_id} [data-place-order] [data-calisign-po-send]`).click();
  await o.waitForLoadState();
  const rivalPo = (await flash(o)).match(/Purchase order (PO-\d{4}-\d{4})/)[1];
  await go(rp, rhub(`requests/${facts.rival_share_id}`));
  await sign(rp.locator("[data-confirm-order]"), "Rival Store Synthetic");
  await rp.click("button[value=confirm]");
  await rp.waitForLoadState();
  await go(o, second);
  const cancel = o.locator(`article#share-${facts.rival_share_id} [data-cancel-order]`);
  await cancel.locator("summary").click();
  await cancel.locator("[name=reason]").fill("Pour moved to the spring (synthetic)");
  await screen(o, "office-cancel-order");
  await cancel.locator("button:has-text('Cancel order')").click();
  await o.waitForLoadState();
  assert.match(await flash(o), new RegExp(`Order ${rivalPo} cancelled`));
  const po = o.locator(`article#share-${facts.rival_share_id} [data-po]`);
  assert.equal(await po.getAttribute("data-po"), "CANCELLED");
  assert.match(await po.innerText(), /Cancelled by .+Reason: Pour moved to the spring/);
  await go(rp, rhub(`requests/${facts.rival_share_id}`));
  assert.match(await rp.locator("[data-order-cancelled]").innerText(), /Cancelled by the contractor[\s\S]*Do not deliver[\s\S]*Pour moved to the spring/);
  await noSideways(rp, "rival phone cancelled order");
  await screen(rp, "rival-phone-order-cancelled");
  await go(rp, rhub("deliveries"));
  assert.match(await rp.locator(`[data-cancelled-delivery="${rivalPo}"]`).innerText(), /Cancelled: Pour moved to the spring/);
  assert.equal(await rp.locator(`tr[data-delivery="${rivalPo}"]`).count(), 0);
  await noSideways(rp, "rival phone deliveries");
  await go(rp, rhub());  // back to the inbox for the isolation check
});

test("Darcy's dashboard, reporting periods and needs attention show the recorded figures", async () => {
  for (const [who, label] of [[darcyDesk, "desktop"], [darcyPhone, "phone"]]) {
    const { pg } = await who();
    await go(pg, hub("dashboard?period=week"));
    const fig = async (k) => (await pg.locator(`[data-figure="${k}"]`).innerText());
    assert.match(await fig("quotes-received"), /\n?2\b/);
    assert.match(await fig("quotes-returned"), /\b2\b/);
    assert.match(await fig("conversion"), /1 of 2/);
    assert.match(await fig("orders-placed"), /\b1\b[\s\S]*1 confirmed/);
    assert.equal(money((await fig("average-order")).split("\n").find((l) => l.startsWith("$"))), W.orderPreview);
    assert.match(await fig("effort"), /12 min/); // 9 and 15 minutes entered by Darcy
    assert.match(await fig("upcoming"), /\b0\b/); // the one order was delivered in step 9
    assert.equal(await pg.locator("[data-attention]").getAttribute("data-attention"), "0", "nothing waiting");
    await noSideways(pg, `${label} dashboard`);
    await screen(pg, `darcy-${label}-dashboard`, { darcy: true });
    // Reporting periods: a custom range before any record is empty; All time matches.
    await pg.locator("[data-period-form] select[name=period]").selectOption("custom");
    await pg.fill("[data-period-form] [name=from]", "2020-01-01");
    await pg.fill("[data-period-form] [name=to]", "2020-01-31");
    await pg.click("[data-period-form] button[type=submit]");
    await pg.waitForLoadState();
    assert.equal(await pg.locator("[data-period-figures]").getAttribute("data-period-figures"), "custom");
    assert.match(await fig("quotes-received"), /\b0\b/);
    assert.match(await fig("conversion"), /No quotes returned in this period/);
    await noSideways(pg, `${label} dashboard custom period`);
    await go(pg, hub("dashboard?period=all"));
    assert.match(await fig("quotes-returned"), /\b2\b/);
    await go(pg, hub("dashboard?period=month"));
    assert.match(await fig("orders-placed"), /\b1\b/);
  }
});

test("Darcy's material demand adds up the requests sent to BMR (desktop and phone)", async () => {
  for (const [who, label] of [[darcyDesk, "desktop"], [darcyPhone, "phone"]]) {
    const { pg } = await who();
    await go(pg, hub("demand?period=week"));
    assert.equal(await pg.locator("[data-demand-requests]").innerText(), "2");
    assert.ok(Number(await pg.locator("[data-demand-recurring]").innerText()) > 0, "products asked for twice");
    // The structural screws were returned without a price on both requests: a possible gap to look at.
    const gaps = pg.locator("[data-demand-gaps]");
    assert.ok(Number(await gaps.getAttribute("data-demand-gaps")) >= 1);
    assert.match(await gaps.innerText(), /in 2 requests, returned without a price in 2/);
    const ordered = await pg.locator("[data-demand-row] td:nth-child(7)").allInnerTexts();
    assert.ok(ordered.some((t) => t.trim() !== "—"), "ordered quantities appear");
    const priced = await pg.locator("[data-demand-row] td:nth-child(6)").allInnerTexts();
    assert.ok(priced.some((t) => t.trim() === "2 of 2"), "products priced on both requests");
    await noSideways(pg, `${label} demand`);
    await screen(pg, `darcy-${label}-demand`, { darcy: true });
    await go(pg, hub("demand?period=custom&from=2020-01-01&to=2020-01-31"));
    assert.equal(await pg.locator("[data-demand-empty]").count(), 1);
  }
});

test("isolation: a second supplier sees only its own requests, and Darcy only BMR's", async () => {
  const rival = await session("rival", PHONE, facts.rival, "/supplier/login");
  const rp = rival.pg;
  assert.ok(rp.url().endsWith(`/supplier/${facts.rival_id}/`), rp.url());
  const inbox = await rp.content();
  assert.ok(inbox.includes(facts.rival_number), "the rival sees its own concrete request");
  assert.ok(!inbox.includes(W.shareNumber) && !inbox.includes(facts.earlier_number), "never BMR's requests");
  await noSideways(rp, "rival inbox");
  await screen(rp, "rival-phone-inbox");
  for (const url of [hub(), hub(`requests/${W.shareId}`), hub("dashboard"), hub("demand"), hub("deliveries"),
    `/supplier/${facts.rival_id}/requests/${W.shareId}`]) {
    assert.equal((await rival.ctx.request.get(`${base}${url}`)).status(), 404, `rival: ${url}`);
  }
  const darcy = await darcyDesk();
  for (const url of [`/supplier/${facts.rival_id}/`, `/supplier/${facts.rival_id}/requests/${facts.rival_share_id}`,
    hub(`requests/${facts.rival_share_id}`)]) {
    assert.equal((await darcy.ctx.request.get(`${base}${url}`)).status(), 404, `darcy: ${url}`);
  }
  // Office pages send a supplier back to the Supplier Hub; the office cannot open a supplier page.
  for (const url of [`/projects/${facts.project_id}`, requests(), `/projects/${facts.project_id}/deck-takeoff`, "/cost-items/"]) {
    const r = await darcy.ctx.request.get(`${base}${url}`, { maxRedirects: 0 });
    assert.equal(r.status(), 302, url);
    assert.ok(r.headers().location.endsWith("/supplier/"), `${url} → ${r.headers().location}`);
  }
  assert.equal((await (await office()).ctx.request.get(`${base}${hub()}`)).status(), 403);
});

test("Darcy never sees the contractor's internal costs, customer or project, and no page failed", async () => {
  const [code, name, cost] = facts.internal_cost;
  const formatted = Number(cost).toLocaleString("en-US", { minimumFractionDigits: 2 });
  assert.ok(darcyPages.length >= 15, `${darcyPages.length} Darcy screens captured`);
  for (const { label, html } of darcyPages) {
    for (const secret of [facts.project, facts.client, code, name, cost, formatted]) {
      assert.ok(!html.includes(secret), `${label} shows "${secret}"`);
    }
  }
  // The site address reaches Darcy only with the purchase order.
  const before = darcyPages.filter((p) => !/order|deliver|change|dashboard|demand/.test(p.label));
  for (const { label, html } of before) assert.ok(!html.includes(facts.address), `${label} shows the address before an order`);
  assert.deepEqual(serverErrors, [], "no 500 responses");
  for (const s of Object.values(sessions)) assert.deepEqual(s.errors, [], "no page script errors");
});
