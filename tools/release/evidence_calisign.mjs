// Release evidence for CaliSIGN native e-signature (Joel, 28 Oct 2026), in a real browser, on a local office with a
// temporary database (tests/calisign_page_server.py), synthetic data only. Nothing is signed by the server or the
// database: every send, signature, countersignature, order, confirmation and delivery change is done on the page,
// and every invitation link is read from the captured email the office sent.
//
//   Client Contract       office Send for E-Signature (1600) → email → desktop ceremony (1600 and 1280×800)
//                         → Sign & Accept → Document Signed Successfully → office Awaiting Your Signature
//                         → Countersign & Execute → Download Executed Copy (a real PDF)
//   Client Change Order   office send (1280×800) → email → ceremony on a 390 px phone → signed → countersign
//   Supplier PO           office Sign & Send for E-Signature → supplier email → Hub Sign & Confirm Order → executed
//   Delivery change       office signs a change → Hub Sign & Accept → executed, signed change PDF
//
// EVIDENCE_SHOTS=<folder> saves each screen. CALISIGN_SHOTS_ONLY is not used: the walk always asserts.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, execFileSync } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";
import { recordEarlyException } from "./evidence_identity_gate3.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const WIDE = [1600, 1000];
const LAPTOP = [1280, 800];
const PHONE = [390, 844];
const serverErrors = [];
const pageErrors = [];
let screens = 0;
const W = {};

const day = (n) => { const d = new Date(`${facts.today}T12:00:00`); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/calisign_page_server.py")], {
    cwd: REPO, env: { ...process.env, CALISIGN_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("CaliSIGN office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("CaliSIGN office exited\n" + out)); }
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
  console.log(`CALISIGN_SCREENS=${screens} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});

const sessions = {};
function watch(pg) {
  pg.on("pageerror", (e) => pageErrors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
}
async function session(key, [width, height], login = null) {
  if (sessions[key]) return sessions[key];
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  watch(pg);
  if (login) {
    const [loginPath, [email, password]] = login;
    await pg.goto(`${base}${loginPath}`);
    await pg.fill("input[name=email]", email);
    await pg.fill("input[name=password]", password);
    await pg.click("button[type=submit]");
    await pg.waitForLoadState();
  }
  sessions[key] = { ctx, pg };
  return sessions[key];
}
const officeWide = () => session("officeWide", WIDE, ["/login", facts.office]);
const officeLaptop = () => session("officeLaptop", LAPTOP, ["/login", facts.office]);
const storeLaptop = () => session("store", LAPTOP, ["/supplier/login", facts.store]);
const signerWide = () => session("signerWide", WIDE);
const signerLaptop = () => session("signerLaptop", LAPTOP);
const signerPhone = () => session("signerPhone", PHONE);

async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function screen(pg, name, { full = true } = {}) {
  screens += 1;
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.waitForTimeout(250); // fonts and the PDF viewer settle
  await pg.screenshot({ path: path.join(SHOTS, `${String(screens).padStart(2, "0")}-${name}.png`), fullPage: full });
}
async function go(pg, url) { const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`); await pg.waitForLoadState(); return r; }
async function flash(pg) { return (await pg.locator(".flash, .flash-stack .alert").allInnerTexts()).join(" | "); }

// The newest captured email of one template, with its text, its html file and the link it carries.
function captured(template, to) {
  const files = fs.readdirSync(facts.mail).filter((f) => f.endsWith(`-${template}.txt`)).sort();
  const hits = files.map((f) => ({ f, text: fs.readFileSync(path.join(facts.mail, f), "utf8") }))
    .filter((m) => !to || m.text.includes(to));
  assert.ok(hits.length, `no ${template} email${to ? ` to ${to}` : ""} was captured`);
  const last = hits[hits.length - 1];
  const html = path.join(facts.mail, last.f.replace(/\.txt$/, ".html"));
  return { ...last, html: fs.existsSync(html) ? html : null, count: hits.length };
}
function linkIn(text, label) {
  const m = text.match(new RegExp(`${label}: (\\S+)`));
  assert.ok(m, `the email has a "${label}" link`);
  return m[1];
}
async function showEmail(pg, mail, name) {
  assert.ok(mail.html, "the email has an HTML version");
  await pg.goto(`file://${mail.html}`);
  await pg.waitForLoadState("networkidle").catch(() => {});
  await screen(pg, name);
}
async function adopt(scope, name) {
  await scope.locator("[name=sign_consent]").check();
  await scope.locator("[name=signer_name]").fill(name);
  assert.equal((await scope.locator("[data-calisign-preview]").innerText()).trim(), name, "the script preview shows the typed name");
}
async function executedPdf(ctx, href) {
  const r = await ctx.request.get(href.startsWith("http") ? href : `${base}${href}`);
  assert.equal(r.status(), 200);
  const body = await r.body();
  assert.equal(body.subarray(0, 5).toString(), "%PDF-", "the executed copy is a PDF");
  return body.length;
}

// ── Client Contract ────────────────────────────────────────────────────────────────────────────────────────────
const contractPage = () => `/projects/${facts.contract_project_id}/contract`;

test("contract 1: Send for E-Signature on the contract, with the client already filled in (1600)", async () => {
  const { pg } = await officeWide();
  await go(pg, contractPage());
  const panel = pg.locator("[data-calisign-panel=contract]");
  assert.equal(await panel.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Not sent for signature");
  const send = panel.locator("[data-calisign-send]");
  if ((await send.getAttribute("open")) === null) await send.locator("summary").click();
  assert.equal(await send.locator("[name=signer_email]").inputValue(), facts.client_email, "signer email comes from the record");
  assert.ok((await send.locator("[name=signer_name]").inputValue()).trim().length > 0, "signer name comes from the record");
  assert.match(await send.innerText(), /No CalibraytAI account is needed/);
  await noSideways(pg, "contract send");
  await screen(pg, "client-contract-review-and-send-1600");
  await send.locator("[data-calisign-send-submit]").click();
  await pg.waitForLoadState();
  assert.equal(await panel.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Signature");
  assert.equal(await panel.getAttribute("data-signing-status"), "SENT");
  W.contractSigner = (await pg.locator("[data-calisign-panel=contract] .calisign-facts dd").first().innerText()).split("\n")[0].trim();
});

test("contract 2: the client's CaliSIGN email says Review and Sign Document, and no account is needed", async () => {
  const mail = captured("SIGNING_INVITATION", facts.client_email);
  assert.match(mail.text, /No CalibraytAI account is needed/);
  W.contractLink = linkIn(mail.text, "Review and Sign Document");
  assert.ok(W.contractLink.startsWith(`${base}/sign/`), "the link opens this office's signing page");
  const html = fs.readFileSync(mail.html, "utf8");
  assert.match(html, /Review and Sign Document/);
  assert.ok(!/Okonkwo|Darcy/.test(html), "no hard-coded names from other walks");
  const { pg } = await signerWide();
  await showEmail(pg, mail, "client-contract-email");
});

test("contract 3: the ceremony shows the frozen contract beside the signing panel on a wide screen (1600)", async () => {
  const { pg } = await signerWide();
  await go(pg, W.contractLink);
  assert.equal(await pg.locator("body").getAttribute("data-sign-page"), "ceremony");
  const viewer = pg.locator(".sign-viewer-frame");
  assert.equal(await viewer.count(), 1, "the actual document is on the page");
  const [v, side] = [await pg.locator(".sign-viewer").boundingBox(), await pg.locator(".sign-side").boundingBox()];
  assert.ok(v.x + v.width <= side.x + 1, "document viewer | signing panel, side by side");
  const steps = await pg.locator("[data-sign-steps] li").allInnerTexts();
  assert.deepEqual(steps.map((s) => s.replace(/^\d\s*/, "").trim()),
    ["Review Document", "Consent to Sign", "Adopt Signature", "Sign & Accept", "Confirmation"]);
  assert.equal(await pg.locator("[name=consent_accepted]").isChecked(), false, "consent is not preselected");
  const doc = await pg.context().request.get(W.contractLink + "/document");
  assert.equal(doc.status(), 200);
  assert.equal((await doc.body()).subarray(0, 5).toString(), "%PDF-", "the viewer shows the frozen PDF");
  await noSideways(pg, "contract ceremony 1600");
  await pg.waitForTimeout(1500);
  await screen(pg, "client-contract-ceremony-1600", { full: false });
  // Chromium in this workspace does not draw PDF pages inside a frame (Chrome on the Mac does). As a supplement,
  // page 1 of the exact bytes the viewer was served is rendered beside the screens, so the evidence shows them.
  if (SHOTS) {
    const pdf = path.join(SHOTS, "frozen-contract-as-served.pdf");
    fs.writeFileSync(pdf, await doc.body());
    try {
      execFileSync("pdftoppm", ["-png", "-r", "70", "-f", "1", "-l", "1", "-singlefile", pdf, path.join(SHOTS, "03b-supplement-frozen-contract-page-1")]);
    } catch { /* pdftoppm is optional */ }
    fs.rmSync(pdf);
  }
});

test("contract 4: consent, adopt the typed signature, Sign & Accept once (1280×800)", async () => {
  const { pg } = await signerLaptop();
  await go(pg, W.contractLink);
  // Sign & Accept without consent is refused by the browser and the server: nothing is signed.
  const name = pg.locator("#confirmed_signer_name");
  await name.fill("");
  await name.fill(W.contractSigner);
  assert.equal((await pg.locator("[data-calisign-preview]").innerText()).trim(), W.contractSigner);
  assert.match(await pg.locator(".calisign-preview-hint").innerText(), /This is how your name will appear as your electronic signature\./);
  await pg.locator("[name=consent_accepted]").check();
  await noSideways(pg, "contract ceremony 1280");
  await pg.evaluate(() => document.querySelector("[data-calisign-adopt]").scrollIntoView({ block: "center" }));
  assert.ok(await pg.evaluate(() => document.fonts.check('600 32px "CaliSIGN Script"')), "the signature script font is loaded from the app");
  await screen(pg, "client-contract-consent-and-adopt-1280", { full: false });
  // Double-submit protection: a second click does not send a second signature.
  const posts = [];
  pg.on("request", (r) => { if (r.method() === "POST" && r.url().endsWith("/sign")) posts.push(r.url()); });
  await Promise.all([
    pg.waitForNavigation(),
    pg.evaluate(() => { const b = document.querySelector("[data-sign-submit]"); b.click(); b.click(); }),
  ]);
  await pg.waitForSelector("[data-sign-complete]");
  assert.equal(posts.length, 1, "Sign & Accept posts once");
});

test("contract 5: Document Signed Successfully — signed, not yet executed (1280×800)", async () => {
  const { pg } = await signerLaptop();
  const done = pg.locator("[data-sign-complete]");
  assert.match(await done.innerText(), /Document Signed Successfully/);
  assert.match(await done.innerText(), new RegExp(`Signed by ${W.contractSigner}`));
  assert.equal(await pg.locator("[data-sign-pending-countersign]").count(), 1, "signed is not executed");
  assert.equal(await pg.locator("[data-sign-download]").count(), 0, "no executed copy before countersignature");
  await screen(pg, "client-contract-signed-confirmation-1280");
  // The same link cannot sign again.
  const again = await pg.context().request.post(W.contractLink + "/sign", { form: { consent_accepted: "yes", confirmed_signer_name: W.contractSigner } });
  assert.ok([400, 403, 404, 409, 410].includes(again.status()), `a second signature is refused (${again.status()})`);
});

test("contract 6: the office sees Awaiting Your Signature and countersigns (1600)", async () => {
  const { pg } = await officeWide();
  await go(pg, contractPage());
  const panel = pg.locator("[data-calisign-panel=contract]");
  assert.equal(await panel.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Your Signature");
  assert.equal(await panel.locator("[data-calisign-countersign]").count(), 1);
  const history = await panel.locator("[data-calisign-history]").textContent();
  for (const step of ["Invitation sent", "Opened by the signer", "Agreed to sign electronically", "Signed"]) assert.match(history, new RegExp(step), `history has ${step}`);
  await screen(pg, "client-contract-office-awaiting-your-signature-1600");
  await panel.locator("[data-calisign-countersign]").click();
  await pg.waitForLoadState();
  assert.equal(await pg.locator("[data-calisign-panel=contract] [data-calisign-status]").getAttribute("data-calisign-status"), "Executed");
});

test("contract 7: Executed — Download Executed Copy is a real PDF; the client's link offers it too", async () => {
  const { pg, ctx } = await officeWide();
  const panel = pg.locator("[data-calisign-panel=contract]");
  const href = await panel.locator("[data-calisign-download]").getAttribute("href");
  W.contractExecutedBytes = await executedPdf(ctx, href);
  await panel.locator("[data-calisign-history] summary").click();
  await screen(pg, "client-contract-office-executed-1600");
  const signer = await signerLaptop();
  await go(signer.pg, W.contractLink);
  assert.match(await signer.pg.locator("[data-sign-complete]").innerText(), /This document is complete/);
  await executedPdf(signer.ctx, await signer.pg.locator("[data-sign-download]").getAttribute("href"));
  const completion = captured("SIGNING_COMPLETE");
  assert.ok(completion.text.length > 0, "a completion email was sent");
});

// ── Client Change Order ────────────────────────────────────────────────────────────────────────────────────────
const coPage = () => `/project-controls/change-orders/${facts.change_order_id}`;

test("change order 1: Send for E-Signature on the approved change order (1280×800)", async () => {
  const { pg } = await officeLaptop();
  await go(pg, coPage());
  const panel = pg.locator("[data-calisign-panel=change_order]");
  const send = panel.locator("[data-calisign-send]");
  if ((await send.getAttribute("open")) === null) await send.locator("summary").click();
  assert.equal(await send.locator("[name=signer_email]").inputValue(), "robin.owner@example.invalid");
  await noSideways(pg, "co send");
  await screen(pg, "client-co-review-and-send-1280");
  await send.locator("[data-calisign-send-submit]").click();
  await pg.waitForLoadState();
  assert.equal(await panel.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Signature");
  W.coLink = linkIn(captured("SIGNING_INVITATION", "robin.owner@example.invalid").text, "Review and Sign Document");
});

test("change order 2: the phone ceremony at 390 px — one column, no sideways scrolling", async () => {
  const { pg } = await signerPhone();
  await go(pg, W.coLink);
  await noSideways(pg, "co ceremony phone");
  const submit = await pg.locator("[data-sign-submit]").boundingBox();
  assert.ok(submit.height >= 44, "the Sign & Accept button is a full touch target");
  await screen(pg, "mobile-co-ceremony-390");
  await pg.locator("[name=consent_accepted]").check();
  await pg.locator("#confirmed_signer_name").fill("Robin Synthetic Owner");
  await pg.locator("[data-sign-submit]").click();
  await pg.waitForSelector("[data-sign-complete]");
  assert.match(await pg.locator("[data-sign-complete]").innerText(), /Document Signed Successfully/);
  await noSideways(pg, "co signed phone");
  await screen(pg, "mobile-co-signed-390");
});

test("change order 3: the office countersigns the change order and downloads the executed copy (1280×800)", async () => {
  const { pg, ctx } = await officeLaptop();
  await go(pg, coPage());
  const panel = pg.locator("[data-calisign-panel=change_order]");
  assert.equal(await panel.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Your Signature");
  await screen(pg, "client-co-office-awaiting-your-signature-1280");
  await panel.locator("[data-calisign-countersign]").click();
  await pg.waitForLoadState();
  const done = pg.locator("[data-calisign-panel=change_order]");
  assert.equal(await done.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Executed");
  await executedPdf(ctx, await done.locator("[data-calisign-download]").getAttribute("href"));
  await screen(pg, "client-co-office-executed-1280");
});

test("an used link is refused plainly: already signed, nothing changes", async () => {
  const { pg } = await signerPhone();
  const r = await pg.context().request.post(W.coLink + "/sign", { form: { consent_accepted: "yes", confirmed_signer_name: "Robin" } });
  assert.ok(r.status() >= 400, "a second signature is refused");
});

// ── Supplier Purchase Order ────────────────────────────────────────────────────────────────────────────────────
const requestsPage = () => `/projects/${facts.order_project_id}/supplier-requests`;
const hubRequest = () => `/supplier/${facts.supplier_id}/requests/${facts.share_id}`;

test("supplier PO 1: the office adopts its signature and selects Sign & Send for E-Signature (1600)", async () => {
  const { pg } = await officeWide();
  await go(pg, requestsPage());
  assert.ok(await recordEarlyException(pg, facts.share_id), "Gate 3: the office records the Early Procurement Exception");
  const form = pg.locator(`article#share-${facts.share_id} [data-place-order]`);
  await form.locator("[name=delivery_date]").fill(day(10));
  await form.locator("[name=delivery_window]").fill("7:00–9:00");
  if (await form.locator("[name=site_contact]").count()) await form.locator("[name=site_contact]").fill("Site lead (synthetic)");
  await adopt(form, "Office Test User");
  assert.match(await form.locator("[data-calisign-po-note]").innerText(), /Supplier Hub/);
  await noSideways(pg, "place order");
  await screen(pg, "supplier-po-office-sign-and-send-1600");
  await form.locator("[data-calisign-po-send]").click();
  await pg.waitForLoadState();
  const po = pg.locator(`article#share-${facts.share_id} [data-po]`);
  assert.equal(await po.getAttribute("data-po"), "PLACED");
  W.poNumber = (await po.locator("strong").innerText()).replace("Purchase order ", "").trim();
  const line = pg.locator(`article#share-${facts.share_id} > [data-signing]`);
  assert.equal(await line.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Signature");
  await screen(pg, "supplier-po-office-awaiting-supplier-1600");
});

test("supplier PO 2: the store's CaliSIGN email points to the Supplier Hub", async () => {
  const mail = captured("SIGNING_SUPPLIER_INVITATION", facts.store[0]);
  assert.match(mail.text, new RegExp(W.poNumber));
  assert.match(mail.text, /Supplier Hub/);
  assert.match(mail.text, /Project: \S+/, "the store's email names the project reference it already knows");
  const { pg } = await storeLaptop();
  await showEmail(pg, mail, "supplier-po-email");
});

test("supplier PO 3: the store signs and confirms the order in the Hub (1280×800)", async () => {
  const { pg } = await storeLaptop();
  await go(pg, hubRequest());
  const form = pg.locator("[data-confirm-order]");
  const line = pg.locator("[data-signing]").first();
  assert.equal(await line.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Your Signature");
  await adopt(form, facts.store_name);
  await screen(pg, "supplier-po-hub-adopt-and-confirm-1280");
  await form.locator("[data-calisign-confirm]").click();
  await pg.waitForLoadState();
  assert.equal(await pg.locator("[data-signing]").first().locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Executed");
  await screen(pg, "supplier-po-hub-executed-1280");
});

test("supplier PO 4: the office sees the purchase order executed, both signatures, signed copy (1600)", async () => {
  const { pg, ctx } = await officeWide();
  await go(pg, requestsPage());
  const line = pg.locator(`article#share-${facts.share_id} > [data-signing]`);
  assert.equal(await line.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Executed");
  const text = await line.innerText();
  assert.match(text, /signed by Office Test User/);
  assert.match(text, new RegExp(`signed by ${facts.store_name.replace(/[()]/g, ".")}`));
  await executedPdf(ctx, await line.locator("a").getAttribute("href"));
  await screen(pg, "supplier-po-office-executed-1600");
});

// ── Supplier Delivery Change ───────────────────────────────────────────────────────────────────────────────────
test("delivery change 1: the office signs a delivery change and sends it to the store (1600)", async () => {
  const { pg } = await officeWide();
  await go(pg, requestsPage());
  const ask = pg.locator(`article#share-${facts.share_id} [data-request-change]`);
  await ask.locator("summary").click();
  await ask.locator("[name=new_date]").fill(day(14));
  await ask.locator("[name=new_window]").fill("10:00–12:00");
  await ask.locator("[name=note]").fill("Forms inspection moved (synthetic)");
  await adopt(ask, "Office Test User");
  await screen(pg, "supplier-dc-office-sign-and-send-1600");
  await ask.locator("button:has-text('Sign & Send the Change')").click();
  await pg.waitForLoadState();
  const pending = pg.locator(`article#share-${facts.share_id} [data-delivery-change=PENDING]`);
  assert.equal(await pending.count(), 1);
  assert.equal(await pending.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Signature");
  const mail = captured("SIGNING_SUPPLIER_INVITATION", facts.store[0]);
  assert.equal(mail.count, 2, "the store is invited to sign the change");
  assert.match(mail.text, /delivery change/);
});

test("delivery change 2: the store sees Awaiting Your Signature, signs and accepts (1280×800)", async () => {
  const { pg } = await storeLaptop();
  await go(pg, hubRequest());
  const pending = pg.locator("[data-delivery-change=PENDING]");
  assert.equal(await pending.locator("[data-calisign-status]").getAttribute("data-calisign-status"), "Awaiting Your Signature");
  const answer = pending.locator("[data-answer-change]");
  await adopt(answer, facts.store_name);
  await screen(pg, "supplier-dc-hub-awaiting-your-signature-1280");
  await answer.locator("button[value=accept]").click();
  await pg.waitForLoadState();
  assert.equal(await pg.locator("[data-delivery-change=PENDING]").count(), 0);
  assert.equal(await pg.locator("[data-change-status=ACCEPTED]").count(), 1);
  await pg.locator("#delivery details summary:has-text('Delivery changes')").click();
  await screen(pg, "supplier-dc-hub-accepted-1280");
});

test("delivery change 3: the office sees the change agreed and its signed PDF (1600)", async () => {
  const { pg, ctx } = await officeWide();
  await go(pg, requestsPage());
  const art = pg.locator(`article#share-${facts.share_id}`);
  await art.locator("#delivery details summary:has-text('Delivery changes')").click();
  const signed = art.locator("[data-signed-change]");
  assert.equal(await signed.count(), 1, "the signed change is downloadable");
  await executedPdf(ctx, await signed.getAttribute("href"));
  assert.match(await art.locator("[data-delivery-agreed]").innerText(), /Agreed delivery/);
  await screen(pg, "supplier-dc-office-executed-1600");
});

test("no server errors and no page script errors during the walk", async () => {
  assert.deepEqual(serverErrors, []);
  assert.deepEqual(pageErrors, []);
});
