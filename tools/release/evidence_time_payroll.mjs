// Release evidence for the payroll handoff (Joel, 22 Oct 2026): Ben enters the company's own hours policy
// (the form starts empty), sets up Shop / Company Work and links Kevin and the job to QuickBooks Time; Kevin,
// on a 390 px iPhone page, sends job time and shop time once; Ben approves on a desktop and sees each entry
// "In QuickBooks Time"; Kevin sees his banked balance and the policy; a correction updates the same QuickBooks
// Time timesheet; the check matches; time off comes off the balance. QuickBooks Time is a FAKE account inside
// the local office (tests/time_payroll_server.py): nothing goes to Intuit. Real pages only. Synthetic data only.
//
// Any response of 500 or more, or a page JavaScript error, fails the walk. Phone pages must not scroll sideways
// and never show a dollar amount, a rate, wages or payroll.
//
// Run: EVIDENCE_REPO=$PWD node --test --test-concurrency=1 tools/release/evidence_time_payroll.mjs
// EVIDENCE_SHOTS=<folder> saves full-page desktop (1280 x 900) and phone (390 x 844) screenshots.
// TRAINING_SHOTS=<folder> saves the Training Centre pictures (c04-*.png desktop, f05-banked-*.png at iPhone size).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts, kevin, ben;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const TRAINING = process.env.TRAINING_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const saved = [];
const MONEY = /\$\s?\d|costing rate|hourly wage|payroll/i;
const W = {};

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/time_payroll_server.py")], {
    cwd: REPO, env: { ...process.env, TIME_PAYROLL_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("time-payroll office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("time-payroll office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
  kevin = await context(PHONE);
  ben = await context(DESK);
});
after(async () => {
  for (const s of [kevin, ben]) await s?.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`TIME_PAYROLL_SCREENS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function context(viewport) {
  const ctx = await browser.newContext({ viewport, acceptDownloads: true });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
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
async function signIn(s, [email, password]) {
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
}
async function flash(pg) { return (await pg.locator(".flash, .alert, .field-flash, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function text(pg) { return pg.locator("body").innerText(); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function phone(pg, label) {
  await noSideways(pg, label);
  assert.doesNotMatch(await text(pg), MONEY, `${label}: Kevin's page shows money`);
  await shot(pg, label);
}
async function shot(pg, name) {
  const device = pg.viewportSize().width <= 500 ? "phone" : "desktop";
  const file = `${name}-${device}.png`;
  saved.push(file);
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, file), fullPage: true });
}
// A Training Centre picture: phone ones at exactly iPhone size (the viewport), desktop ones full page.
async function training(pg, file, locator) {
  if (!TRAINING) return;
  fs.mkdirSync(TRAINING, { recursive: true });
  if (locator) await locator.scrollIntoViewIfNeeded();
  const isPhone = pg.viewportSize().width <= 500;
  await pg.screenshot({ path: path.join(TRAINING, file), fullPage: !isPhone });
}
async function sendTime(pg, { element, work, hours }) {
  const other = pg.locator("#field-time-other-toggle");
  if (await other.isVisible()) await other.click();
  if (element) await pg.selectOption("#field-time-element", { label: element });
  await pg.selectOption("#field-time-activity", { label: work });
  await pg.fill("input[name=hours]", hours);
  await submit(pg, pg.getByRole("button", { name: "Send time" }));
}

// ------------------------------------------------------------------ the walk

step("1 Ben enters the company's own hours policy from Getting started; the form starts empty", async () => {
  await signIn(ben, facts.ben);
  const pg = ben.pg;
  await go(pg, "/getting-started");
  assert.equal(await pg.locator("#step-hours_policy").getAttribute("data-done"), "no");
  await submit(pg, pg.locator("#step-hours_policy").getByRole("link", { name: /Go there/ }));
  assert.match(new URL(pg.url()).pathname, /\/settings\/hours-policy$/);
  const form = pg.locator("[data-hours-policy-form]");
  for (const name of ["normal_week_hours", "extra_after_hours", "bank_rate", "effective_from"]) {
    assert.equal(await form.locator(`[name=${name}]`).inputValue(), "", `${name} starts empty`);
  }
  assert.equal(await form.locator("input[type=radio]:checked").count(), 0, "no choice is preset");
  assert.equal(await form.locator("[name=week_start_day]").inputValue(), "");
  assert.match(await text(pg), /No hours policy has been entered yet, so no hours are banked\./);
  await shot(pg, "01-hours-policy-empty");
  await training(pg, "c04-hours-policy-empty.png");
  // Saving with a value missing names it.
  await form.locator("[name=normal_week_hours]").fill("8");
  await pg.evaluate(() => { for (const el of document.querySelectorAll("[data-hours-policy-form] [required]")) el.removeAttribute("required"); });
  await submit(pg, pg.getByRole("button", { name: "Save hours policy" }));
  assert.match(await flash(pg), /Enter the weekly hours after which extra hours start|Choose whether/);
  const monday = new Date(); monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  W.monday = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, "0")}-${String(monday.getDate()).padStart(2, "0")}`;
  // A synthetic policy with a short week, so one day's hours show banking: 8 hours, extra after 8, banked 1.5.
  await form.locator("[name=normal_week_hours]").fill("8");
  await form.locator("[name=extra_after_hours]").fill("8");
  await form.locator("input[name=extra_hours_treatment][value=BANK]").check();
  await form.locator("[name=bank_rate]").fill("1.5");
  await form.locator("input[name=counts_company_time][value=yes]").check();
  await form.locator("[name=week_start_day]").selectOption("0");
  await form.locator("[name=effective_from]").fill(W.monday);
  await submit(pg, pg.getByRole("button", { name: "Save hours policy" }));
  assert.match(await flash(pg), /Hours policy saved \(version 1, in effect from/);
  const current = await pg.locator("[data-hours-policy-current]").innerText();
  assert.match(current, /Normal work week: 8\.00 hours \(Monday to Sunday\)\. Hours after 8\.00 in a week are banked: 1\.5 banked hour for each extra hour\. Shop \/ Company Work counts\./);
  assert.match(await pg.locator("[data-hours-policy-history]").innerText(), new RegExp(facts.ben_name.replace(/[()]/g, "\\$&")));
  await shot(pg, "01-hours-policy-saved");
  await training(pg, "c04-hours-policy-saved.png");
  await go(pg, "/getting-started");
  assert.equal(await pg.locator("#step-hours_policy").getAttribute("data-done"), "yes");
});

step("2 Ben sets up Shop / Company Work and links Kevin, the job and shop work to QuickBooks Time", async () => {
  const pg = ben.pg;
  // Office tidy (24 Oct 2026): the one-time set-up is on Hours policy (company setup), not Time review.
  await go(pg, "/settings/hours-policy");
  await submit(pg, pg.getByRole("button", { name: "Set up Shop / Company Work" }));
  assert.match(await flash(pg), /Shop \/ Company Work is ready\./);
  assert.match(new URL(pg.url()).pathname, /\/time\/company$/);
  await shot(pg, "02-shop-company-work");
  await go(pg, "/accounting");
  await submit(pg, pg.locator("[data-payroll-panel]").getByRole("link", { name: "QuickBooks Time transfers" }));
  assert.match(await pg.locator("[data-qbt-connection]").innerText(), /TEST QuickBooks Time account/);
  await submit(pg, pg.getByRole("link", { name: "People and job links" }));
  // Kevin has not recorded time yet, so he is not listed; the job and the shop categories are.
  const job = pg.locator(`[data-qbt-job="${facts.project_id}"]`);
  await job.locator("select[name=qbt_jobcode_id]").selectOption(facts.qbt_job);
  await submit(pg, job.getByRole("button", { name: "Save" }));
  assert.match(await flash(pg), /Link saved\./);
  const safety = pg.locator("[data-qbt-category]").filter({ hasText: "Safety meetings and training" });
  await safety.locator("select[name=qbt_jobcode_id]").selectOption(facts.qbt_shop);
  await submit(pg, safety.getByRole("button", { name: "Save" }));
  assert.match(await pg.locator(`[data-qbt-job="${facts.project_id}"]`).innerText(), /Linked to Mill Pond Road deck \(synthetic\)/);
  await shot(pg, "02-links");
});

step("3 Kevin, on his iPhone, sends job time and shop time once", async () => {
  await signIn(kevin, facts.kevin);
  const pg = kevin.pg;
  assert.match(pg.url(), /\/field\/today$/);
  assert.match(await text(pg), /Banked hours[\s\S]*0\.00[\s\S]*Normal work week: 8\.00 hours/);
  await phone(pg, "03-today-before");
  await submit(pg, pg.getByRole("link", { name: "Enter time" }).first());
  await sendTime(pg, { element: facts.element, work: facts.activity, hours: "10" });
  assert.match(await flash(pg), /Time sent for approval\./);
  await go(pg, "/field/today");
  await submit(pg, pg.locator("a[data-company-time]").first());
  assert.match(await text(pg), /Shop \/ Company Work: paid company time, not a customer's job/);
  await phone(pg, "03-shop-form");
  await sendTime(pg, { work: "Safety meetings and training", hours: "1" });
  const page = await text(pg);
  assert.match(page, /10\.00 hours · Original work/);
  assert.match(page, /1\.00 hours · Company time/);
  await phone(pg, "03-my-time");
});

step("4 Ben links Kevin, approves both on the desktop and sees them In QuickBooks Time", async () => {
  const pg = ben.pg;
  await go(pg, "/time/quickbooks-time/links");
  const person = pg.locator(`[data-qbt-person="${facts.kevin_id}"]`);
  await person.locator("select[name=qbt_user_id]").selectOption(facts.qbt_kevin);
  await submit(pg, person.getByRole("button", { name: "Save" }));
  assert.match(await flash(pg), /Link saved\./);
  await go(pg, "/time");
  const rows = pg.locator("tbody tr").filter({ hasText: facts.kevin_name });
  assert.equal(await rows.count(), 2);
  for (let i = 0; i < 2; i += 1) await rows.nth(i).locator("input[type=checkbox]").check();
  await submit(pg, pg.getByRole("button", { name: "Approve selected" }));
  const said = await flash(pg);
  assert.match(said, /Approved 2 time entries\./);
  assert.match(said, /Sent to QuickBooks Time: 2\./);
  const labels = await pg.locator("[data-qbt-label]").allInnerTexts();
  assert.deepEqual(labels.filter((l) => /In QuickBooks Time/.test(l)).length, 2, labels.join("|"));
  await shot(pg, "04-time-review-sent");
  await training(pg, "c04-time-review-qbt.png");
  await go(pg, "/time/quickbooks-time");
  assert.equal(await pg.locator('[data-qbt-status="SENT"]').count(), 2);
  W.jobRow = pg.locator("[data-qbt-transfer]").filter({ hasText: facts.activity });
  W.jobEntry = (await W.jobRow.locator("a").first().getAttribute("href")).match(/\/time\/(\d+)/)[1];
  // Pressing Send again sends nothing more (no duplicates).
  await submit(pg, pg.locator("[data-qbt-send]"));
  assert.match(await flash(pg), /QuickBooks Time: 0 sent, 0 updated\./);
  await shot(pg, "04-quickbooks-time");
  await training(pg, "c04-quickbooks-time.png");
});

step("5 Kevin sees his banked balance on the phone: hours only, no money, no sideways scrolling", async () => {
  const pg = kevin.pg;
  await go(pg, "/field/today");
  const card = pg.locator("[data-banked-balance]");
  assert.equal(await card.getAttribute("data-banked-balance"), "4.50"); // (10 + 1 - 8) x 1.5
  assert.match(await card.innerText(), /4\.50[\s\S]*worked 11\.00 approved · regular 8\.00 · extra 3\.00 · banked 4\.50/);
  await phone(pg, "05-today-banked");
  await training(pg, "f05-banked-hours.png");
  await submit(pg, pg.getByRole("link", { name: "See banked hours" }));
  const history = await text(pg);
  assert.match(history, /Banked hours history/);
  assert.match(history, /worked 11\.00, regular 8\.00, extra 3\.00/);
  await phone(pg, "05-banked-history");
  await training(pg, "f05-banked-history.png", pg.locator("[data-banked-ledger]"));
  await go(pg, "/field/time");
  assert.equal(await pg.locator("[data-banked-balance]").getAttribute("data-banked-balance"), "4.50");
  await phone(pg, "05-my-time-banked");
});

step("6 Ben corrects the job hours: the same QuickBooks Time timesheet is updated and the balance follows", async () => {
  const pg = ben.pg;
  await go(pg, `/time/${W.jobEntry}`);
  assert.match(await pg.locator("[data-qbt-entry-status]").innerText(), /In QuickBooks Time · timesheet \d+/);
  const before = (await pg.locator("[data-qbt-entry-status]").innerText()).match(/timesheet (\d+)/)[1];
  await pg.fill("input[name=hours]", "9");
  await pg.fill("input[name=reason]", "Left an hour early (synthetic)");
  await submit(pg, pg.getByRole("button", { name: "Correct approved time" }));
  const said = await flash(pg);
  assert.match(said, /Approved time corrected\. The original entry is kept\./);
  assert.match(said, /Sent to QuickBooks Time: 1\./);
  assert.match(await pg.locator("[data-qbt-entry-status]").innerText(), new RegExp(`In QuickBooks Time · timesheet ${before}`));
  await go(pg, "/time/quickbooks-time");
  assert.equal(await pg.locator('[data-qbt-status="REPLACED"]').count(), 1);
  assert.match(await pg.locator('[data-qbt-status="SENT"]').filter({ hasText: "(correction)" }).innerText(), new RegExp(`Timesheet ${before}`));
  await go(pg, "/time/quickbooks-time/check");
  await pg.fill("input[name=from]", W.monday);
  await submit(pg, pg.locator("[data-qbt-check]"));
  const check = await pg.locator("[data-qbt-reconciliation]").innerText();
  assert.match(check, /2 match\./);
  assert.doesNotMatch(check, /Different in QuickBooks Time|no longer|more than once|Entered directly|not in QuickBooks Time yet/);
  await shot(pg, "06-check");
});

step("7 Ben records time off; the ledger and Kevin's phone show the new balance", async () => {
  const pg = ben.pg;
  await go(pg, "/accounting");
  await submit(pg, pg.locator("[data-payroll-panel]").getByRole("link", { name: "Banked hours" }));
  assert.match(await pg.locator(`[data-banked-worker="${facts.kevin_id}"]`).innerText(), /3\.00/); // (9 + 1 - 8) x 1.5
  await training(pg, "c04-banked-hours.png");
  await submit(pg, pg.locator(`[data-banked-worker="${facts.kevin_id}"] a`));
  const off = pg.locator("[data-banked-time-off]");
  await off.locator("[name=hours]").fill("2");
  await off.locator("[name=reason]").fill("Friday afternoon (synthetic)");
  await submit(pg, off.getByRole("button", { name: "Record time off" }));
  assert.match(await flash(pg), /Time off recorded\./);
  assert.equal(await pg.locator("[data-banked-balance]").getAttribute("data-banked-balance"), "1.00");
  const ledger = await pg.locator("[data-banked-ledger]").innerText();
  assert.match(ledger, /Time off taken\s+-2\.00/);
  assert.match(ledger, /Earned\s+-1\.50/); // the correction's difference row
  await shot(pg, "07-banked-ledger");
  await go(kevin.pg, "/field/today");
  assert.equal(await kevin.pg.locator("[data-banked-balance]").getAttribute("data-banked-balance"), "1.00");
  await phone(kevin.pg, "07-today-after-time-off");
});

step("8 Kevin never reaches the payroll pages; Shop / Company Work is never shown as a customer job", async () => {
  const k = kevin.pg;
  for (const url of ["/time/quickbooks-time", "/time/banked-hours", `/time/banked-hours/${facts.kevin_id}`,
    "/settings/hours-policy", "/time/company", "/time/quickbooks-time/check"]) {
    await go(k, url);
    assert.match(k.url(), /\/field\//, `${url} is refused to field-only crew`);
    assert.doesNotMatch(await text(k), MONEY, url);
  }
  const pg = ben.pg;
  for (const url of ["/projects/", "/clients/"]) {
    await go(pg, url);
    assert.doesNotMatch(await text(pg), /Shop \/ Company Work|own company, not a customer/, url);
  }
  await go(pg, "/time/company");
  assert.match(await pg.locator("[data-company-hours]").innerText(), /Safety meetings and training: 1\.00 h/);
  await shot(pg, "08-shop-company-work");
});
