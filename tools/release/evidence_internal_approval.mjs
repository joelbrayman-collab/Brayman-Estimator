// Release evidence for CaliSIGN internal approval (Joel, 3 Nov 2026), in a real browser, on a local office with a
// temporary database (tests/internal_approval_page_server.py), synthetic data only. The office freezes the working
// Internal Project Financial Summary as REV1 and sends it for internal approval on the page; the approver reads the
// link from the captured email and signs signed out (no Calibrayt account) on a laptop; a second REV is signed on a
// 390 px phone; the signed copies are in the project's Documents; the link opens nothing but its own document.
// The customer estimate (3 Nov 2026): the office freezes the exact customer estimate PDF on the proposal page and
// sends it to Ben; Ben reviews it signed out on a laptop and signs on a 390 px phone; the estimate is then
// "authorized for customer issue" on the proposal (at the send form), the estimate and the pricing pages.
//
// EVIDENCE_SHOTS=<folder> saves each screen.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const LAPTOP = [1280, 800];
const PHONE = [390, 844];
const serverErrors = [];
const pageErrors = [];
let screens = 0;
const W = {};

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/internal_approval_page_server.py")], {
    cwd: REPO, env: { ...process.env, INTERNAL_APPROVAL_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("internal-approval office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("internal-approval office exited\n" + out)); }
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
  console.log(`INTERNAL_APPROVAL_SCREENS=${screens} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});

const sessions = {};
function watch(pg) {
  pg.on("pageerror", (e) => pageErrors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
}
async function session(key, [width, height], login = false) {
  if (sessions[key]) return sessions[key];
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  watch(pg);
  if (login) {
    await pg.goto(`${base}/login`);
    await pg.fill("input[name=email]", facts.owner[0]);
    await pg.fill("input[name=password]", facts.owner[1]);
    await pg.click("button[type=submit]");
    await pg.waitForLoadState();
  }
  sessions[key] = { ctx, pg };
  return sessions[key];
}
const office = () => session("office", LAPTOP, true);
const approverLaptop = () => session("approverLaptop", LAPTOP);
const approverPhone = () => session("approverPhone", PHONE);

async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function screen(pg, name, { full = true } = {}) {
  screens += 1;
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.waitForTimeout(250);
  await pg.screenshot({ path: path.join(SHOTS, `${String(screens).padStart(2, "0")}-${name}.png`), fullPage: full });
}
async function go(pg, url) { const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`); await pg.waitForLoadState(); return r; }
function invitation(to, n) {
  const files = fs.readdirSync(facts.mail).filter((f) => f.endsWith("-SIGNING_INVITATION.txt")).sort();
  const hits = files.map((f) => fs.readFileSync(path.join(facts.mail, f), "utf8")).filter((t) => t.includes(to));
  assert.equal(hits.length, n, `${n} invitation email(s) to ${to}`);
  const m = hits[n - 1].match(/Review and Sign Document: (\S+)/);
  assert.ok(m, "the email has the one-time link");
  return { text: hits[n - 1], link: m[1] };
}
const review = () => `/projects/${facts.project_id}/guided/pricing`;

async function freezeAndSend(pg, label) {
  await go(pg, review());
  const section = pg.locator("#ts-review-internal-approval");
  if (!(await section.getAttribute("open"))) await section.locator("summary").click();
  await Promise.all([pg.waitForNavigation(), section.locator("[data-freeze-revision]").click()]);
  const row = pg.locator(`[data-summary-revision=${label}]`);
  assert.equal(await row.getAttribute("data-revision-state"), "not_sent");
  const form = pg.locator(`[data-send-approval=${label}]`);
  await form.locator("[name=approver_name]").fill(facts.approver[0]);
  await form.locator("[name=approver_email]").fill(facts.approver[1]);
  await Promise.all([pg.waitForNavigation(), form.locator("button[type=submit]").click()]);
  assert.equal(await pg.locator(`[data-summary-revision=${label}]`).getAttribute("data-revision-state"), "awaiting_approver");
}

async function sign(pg, link) {
  await go(pg, link);
  assert.equal(await pg.locator("body").getAttribute("data-sign-page"), "ceremony");
  assert.equal(await pg.locator("body").getAttribute("data-sign-family"), "internal-approval");
  assert.equal(await pg.locator("[name=consent_accepted]").isChecked(), false, "consent is not preselected");
  await pg.locator("#confirmed_signer_name").fill(facts.approver[0]);
  await pg.locator("[name=consent_accepted]").check();
  const posts = [];
  pg.on("request", (r) => { if (r.method() === "POST" && r.url().endsWith("/sign")) posts.push(r.url()); });
  await Promise.all([pg.waitForNavigation(),
    pg.evaluate(() => { const b = document.querySelector("[data-sign-submit]"); b.click(); b.click(); })]);
  await pg.waitForSelector("[data-sign-complete]");
  assert.equal(posts.length, 1, "Sign & Accept posts once");
  assert.match(await pg.locator("[data-sign-complete]").innerText(), /Document Signed Successfully/);
}

test("1: the office freezes the working summary as REV1 and sends it for internal approval (1280×800)", async () => {
  const { pg } = await office();
  await freezeAndSend(pg, "REV1");
  await noSideways(pg, "review internal approval");
  await screen(pg, "office-rev1-sent-1280");
});

test("2: the approver's email is the normal CaliSIGN invitation with the one-time link", async () => {
  const mail = invitation(facts.approver[1], 1);
  assert.match(mail.text, /document for internal approval/);
  assert.match(mail.text, /Internal Project Financial Summary REV1/);
  assert.match(mail.text, /No CalibraytAI account is needed/);
  W.link1 = mail.link;
  assert.ok(W.link1.startsWith(`${base}/sign/`));
});

test("3: signed out on a laptop, the approver sees the exact frozen REV1 and the consent (1280×800)", async () => {
  const { pg } = await approverLaptop();
  await go(pg, W.link1);
  assert.equal(await pg.locator(".sign-viewer-frame").count(), 1, "the frozen document is on the page");
  const body = await pg.locator("body").innerText();
  assert.match(body, /Internal approval/i);
  assert.match(body, /you approve this internal document electronically/);
  assert.ok(!/\$55\.77|\$31\.25|Worker A|hourly wage/i.test(body), "the ceremony page itself shows no compensation detail");
  const doc = await pg.context().request.get(W.link1 + "/document");
  assert.equal(doc.status(), 200);
  assert.equal((await doc.body()).subarray(0, 5).toString(), "%PDF-");
  await noSideways(pg, "ceremony laptop");
  await screen(pg, "approver-ceremony-1280", { full: false });
});

test("4: the link opens nothing else: office pages, Documents and employee pages ask for a sign-in", async () => {
  const { pg } = await approverLaptop();
  for (const p of [`/projects/${facts.project_id}`, `/projects/${facts.project_id}/documents`, "/documents",
    review(), `/projects/${facts.project_id}/guided/internal-financial-summary.pdf`, "/settings/people/employees"]) {
    await go(pg, p);
    assert.match(pg.url(), /\/login/, `${p} is not reachable with the signing link`);
  }
});

test("5: consent and sign once; approver only, so the approval is complete (1280×800)", async () => {
  const { pg } = await approverLaptop();
  await sign(pg, W.link1);
  assert.equal(await pg.locator("[data-sign-download]").count(), 1, "approver only: the signed copy is ready");
  await noSideways(pg, "signed laptop");
  await screen(pg, "approver-rev1-signed-1280");
  const again = await pg.context().request.post(W.link1 + "/sign", { form: { consent_accepted: "yes", confirmed_signer_name: facts.approver[0] } });
  assert.ok([400, 403, 404, 409, 410].includes(again.status()), `a second signature is refused (${again.status()})`);
});

test("6: the office sees REV1 approved and its signed copy in the project's Documents (1280×800)", async () => {
  const { pg } = await office();
  await go(pg, review());
  assert.equal(await pg.locator("[data-summary-revision=REV1]").getAttribute("data-revision-state"), "approved");
  await go(pg, `/projects/${facts.project_id}/documents`);
  assert.match(await pg.locator("body").innerText(), /Internal Project Financial Summary REV1 — approved by/);
  await screen(pg, "office-documents-signed-rev1-1280");
});

test("7: a change becomes REV2, sent and signed on a 390 px phone; REV1 stays approved", async () => {
  const { pg } = await office();
  await go(pg, review());
  const budget = pg.locator(`input[name=budget_${facts.stage_id}]`);
  await budget.fill("2950");
  await Promise.all([pg.waitForNavigation(), pg.locator("[data-save-scenario]").click()]);
  await freezeAndSend(pg, "REV2");
  assert.equal(await pg.locator("[data-summary-revision=REV1]").getAttribute("data-revision-state"), "approved");
  const mail = invitation(facts.approver[1], 2);
  assert.match(mail.text, /REV2/);
  const phone = (await approverPhone()).pg;
  await go(phone, mail.link);
  await noSideways(phone, "ceremony phone");
  const submit = await phone.locator("[data-sign-submit]").boundingBox();
  assert.ok(submit.height >= 44, "Sign & Accept is a full touch target");
  await screen(phone, "approver-rev2-ceremony-390");
  await sign(phone, mail.link);
  await noSideways(phone, "signed phone");
  await screen(phone, "approver-rev2-signed-390");
  await go(pg, review());
  assert.equal(await pg.locator("[data-summary-revision=REV2]").getAttribute("data-revision-state"), "approved");
  assert.equal(await pg.locator("[data-summary-revision=REV1]").getAttribute("data-revision-state"), "approved");
});

const proposalPage = () => `/proposals/${facts.proposal_id}`;
async function sign_as(pg, link, name) {
  await go(pg, link);
  assert.equal(await pg.locator("body").getAttribute("data-sign-family"), "internal-approval");
  assert.equal(await pg.locator("[name=consent_accepted]").isChecked(), false, "consent is not preselected");
  await pg.locator("#confirmed_signer_name").fill(name);
  await pg.locator("[name=consent_accepted]").check();
  await Promise.all([pg.waitForNavigation(), pg.locator("[data-sign-submit]").click()]);
  await pg.waitForSelector("[data-sign-complete]");
}

test("8: the office freezes the exact customer estimate and sends it to Ben from the proposal page (1280×800)", async () => {
  const { pg } = await office();
  await go(pg, proposalPage());
  assert.equal(await pg.locator("[data-customer-issue-state]").getAttribute("data-customer-issue-state"), "not_frozen");
  await Promise.all([pg.waitForNavigation(), pg.locator("[data-freeze-customer-estimate] button").click()]);
  const row = pg.locator("[data-customer-estimate-revision=REV1]");
  assert.equal(await row.getAttribute("data-revision-state"), "not_sent");
  const frozen = await pg.context().request.get(base + await row.locator("a").getAttribute("href"));
  W.estimatePdf = await frozen.body();
  assert.equal(W.estimatePdf.subarray(0, 5).toString(), "%PDF-");
  const form = pg.locator("[data-send-customer-estimate=REV1]");
  await form.locator("[name=approver_name]").fill(facts.ben[0]);
  await form.locator("[name=approver_email]").fill(facts.ben[1]);
  await Promise.all([pg.waitForNavigation(), form.locator("button[type=submit]").click()]);
  assert.equal(await pg.locator("[data-customer-issue-state]").getAttribute("data-customer-issue-state"), "awaiting");
  assert.equal(await pg.locator("[data-send-customer-issue]").getAttribute("data-send-customer-issue"), "awaiting");
  await noSideways(pg, "proposal approval sent");
  await screen(pg, "office-estimate-rev1-sent-1280");
});

test("9: signed out on a laptop, Ben reviews the exact frozen estimate PDF; the link opens nothing else (1280×800)", async () => {
  const mail = invitation(facts.ben[1], 1);
  assert.match(mail.text, /Customer estimate REV1/);
  W.estimateLink = mail.link;
  const ctx = await browser.newContext({ viewport: { width: LAPTOP[0], height: LAPTOP[1] } });
  const pg = await ctx.newPage();
  watch(pg);
  sessions.benLaptop = { ctx, pg };
  await go(pg, W.estimateLink);
  const body = await pg.locator("body").innerText();
  assert.match(body, /Customer estimate REV1/);
  assert.ok(!/\$55\.77|margin|Worker A/i.test(body), "no internal figures on the ceremony page");
  const doc = await pg.context().request.get(W.estimateLink + "/document");
  assert.equal(doc.status(), 200);
  assert.ok(Buffer.compare(await doc.body(), W.estimatePdf) === 0, "the exact frozen PDF, byte for byte");
  await noSideways(pg, "estimate ceremony laptop");
  await screen(pg, "ben-estimate-ceremony-1280", { full: false });
  for (const p of [proposalPage(), `/estimates/${facts.estimate_id}`, `/projects/${facts.estimate_project_id}/documents`,
    `/projects/${facts.estimate_project_id}/guided/pricing`, `${proposalPage()}/pdf`]) {
    await go(pg, p);
    assert.match(pg.url(), /\/login/, `${p} is not reachable with the signing link`);
  }
});

test("10: Ben signs on a 390 px phone", async () => {
  const ctx = await browser.newContext({ viewport: { width: PHONE[0], height: PHONE[1] } });
  const pg = await ctx.newPage();
  watch(pg);
  sessions.benPhone = { ctx, pg };
  await go(pg, W.estimateLink);
  await noSideways(pg, "estimate ceremony phone");
  const submit = await pg.locator("[data-sign-submit]").boundingBox();
  assert.ok(submit.height >= 44, "Sign & Accept is a full touch target");
  await screen(pg, "ben-estimate-ceremony-390");
  await sign_as(pg, W.estimateLink, facts.ben[0]);
  await noSideways(pg, "estimate signed phone");
  await screen(pg, "ben-estimate-signed-390");
});

test("11: authorized for customer issue on the proposal (and its send form), estimate and pricing pages; filed in Documents", async () => {
  const { pg } = await office();
  await go(pg, proposalPage());
  assert.equal(await pg.locator("[data-customer-issue-state]").getAttribute("data-customer-issue-state"), "authorized");
  assert.match(await pg.locator("[data-send-customer-issue]").innerText(), /authorized for customer issue/);
  assert.equal(await pg.locator("[data-proposal-acceptance]").count(), 0, "Ben's approval is not the client's acceptance");
  await screen(pg, "office-estimate-authorized-1280");
  await go(pg, `/estimates/${facts.estimate_id}`);
  assert.equal(await pg.locator("[data-customer-issue-status]").getAttribute("data-customer-issue-status"), "authorized");
  await go(pg, `/projects/${facts.estimate_project_id}/guided/pricing`);
  assert.equal(await pg.locator("[data-customer-issue-status]").getAttribute("data-customer-issue-status"), "authorized");
  await go(pg, `/projects/${facts.estimate_project_id}/documents`);
  assert.match(await pg.locator("body").innerText(), /Customer estimate REV1 .* approved for customer issue by Ben Approver Synthetic/);
  await screen(pg, "office-estimate-documents-1280");
  const phone = (await approverPhone()).pg;  // a phone with no office session still reaches nothing
  await go(phone, proposalPage());
  assert.match(phone.url(), /\/login/);
});

test("no server errors and no page script errors during the walk", async () => {
  assert.deepEqual(serverErrors, []);
  assert.deepEqual(pageErrors, []);
});
