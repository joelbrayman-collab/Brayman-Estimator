// Release evidence for Field time and labour cost (Joel, 22 Oct 2026): Kevin records his hours on an
// iPhone-sized page, Ben returns one and approves on a desktop, Kevin fixes it and sends it again, shop
// time goes on Shop / Company Work, and the job shows estimated against actual labour hours and
// cost. The approved hours go to QuickBooks as a file once and are checked back. Real pages only,
// against a local office on a temporary database (tests/field_time_server.py). Synthetic data only.
//
// Any response of 500 or more, or a page JavaScript error, fails the walk. Phone pages (390 x 844) must
// not scroll sideways. Kevin's pages never show a dollar amount, a rate, wages or payroll.
//
// Run: EVIDENCE_REPO=$PWD node --test --test-concurrency=1 tools/release/evidence_field_time.mjs
// EVIDENCE_SHOTS=<folder> saves desktop (1280 x 900) and phone (390 x 844) screenshots.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts, kevin, ben;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const saved = [];
const MONEY = /\$\s?\d|costing rate|hourly wage|payroll/i;
const W = {}; // what the walk made, for later steps

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/field_time_server.py")], {
    cwd: REPO, env: { ...process.env, FIELD_TIME_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("field-time office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("field-time office exited\n" + out)); }
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
  console.log(`FIELD_TIME_SCREENS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

// Each step builds on the one before: once a step fails, the later steps are skipped.
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
async function menu(pg, section, href) {
  await go(pg, "/");
  const nav = pg.locator("nav.sidebar-nav .sidebar-section").filter({ has: pg.locator(".sidebar-section-label", { hasText: new RegExp(`^\\s*${section}\\s*$`) }) }).first();
  await submit(pg, nav.locator(`a.sidebar-link[href="${href}"]`));
}
// Kevin's time form: choose the work item and the work, the hours, a note; Send time.
async function sendTime(pg, { element, work, hours, note }) {
  const other = pg.locator("#field-time-other-toggle");
  if (await other.isVisible()) await other.click();
  if (element) await pg.selectOption("#field-time-element", { label: element });
  await pg.selectOption("#field-time-activity", { label: work });
  await pg.fill("input[name=hours]", hours);
  if (note !== undefined) await pg.fill("textarea[name=worker_note]", note);
  await submit(pg, pg.getByRole("button", { name: "Send time" }));
}
// Ben's Time review row for one of Kevin's entries (by its work), opened.
// Time review is reached from the job's Project page ("Review time"); it is not in the menu (FG-035).
async function timeReview(pg) {
  await go(pg, `/projects/${facts.project_id}`);
  await submit(pg, pg.locator("#hub-time").getByRole("link", { name: "Review time" }));
  await go(pg, "/time"); // all jobs, the last seven days (the company-time project too)
}
async function openEntry(pg, work, hours) {
  await timeReview(pg);
  const row = pg.locator("tbody tr").filter({ hasText: facts.kevin_name }).filter({ hasText: work }).filter({ hasText: hours }).first();
  await submit(pg, row.locator("a[data-time-entry]"));
}

// ------------------------------------------------------------------ the walk

step("1 Kevin, on his iPhone, records hours against the job and its work", async () => {
  await signIn(kevin, facts.kevin);
  const pg = kevin.pg;
  assert.match(pg.url(), /\/field\/today$/);
  await phone(pg, "01-today");
  await submit(pg, pg.getByRole("link", { name: "Enter time" }).first());
  assert.match(pg.url(), new RegExp(`/field/projects/${facts.project_id}/time`));
  assert.match(await text(pg), new RegExp(facts.project.replace(/[()]/g, "\\$&")));
  await phone(pg, "01-time-form");
  // "Scheduled today": the office scheduled the whole work item, which has two works. The button picks
  // the work item and opens the Work box, holding only that item's work (iPhone Safari ignores hidden
  // options), for Kevin to choose one. Sending never fails with "Work not found".
  assert.match(await text(pg), /Scheduled today/i);
  await pg.locator('.field-time-recent-btn[data-activity-id=""]').first().click();
  assert.ok(await pg.locator("#field-time-other-work").isVisible(), "the Work box opens");
  assert.equal(await pg.inputValue("#field-time-element"), String(await pg.locator('.field-time-recent-btn[data-activity-id=""]').first().getAttribute("data-element-id")));
  const works = (await pg.locator("#field-time-activity option").allInnerTexts()).filter((w) => w !== "Choose work");
  assert.deepEqual(works.sort(), [facts.activity, facts.co_activity].sort(), `work list: ${works}`);
  await shot(pg, "01-scheduled-today");
  await pg.selectOption("#field-time-activity", { label: facts.activity });
  await pg.fill("input[name=hours]", "8");
  await pg.fill("textarea[name=worker_note]", "Formed the east footing (synthetic)");
  await submit(pg, pg.getByRole("button", { name: "Send time" }));
  assert.match(pg.url(), /\/field\/time$/);
  assert.match(await flash(pg), /Time sent for approval\./);
  await go(pg, `/field/projects/${facts.project_id}/time`);
  await sendTime(pg, { element: facts.element, work: facts.co_activity, hours: "3" });
  const page = await text(pg);
  assert.match(page, /8\.00 hours · Original work/);
  assert.match(page, new RegExp(`3\\.00 hours · Change order work · ${facts.co_number}`));
  assert.match(page, /This week[^\n]*11\.00 hours/);
  assert.equal(await pg.locator('[data-status="SUBMITTED"]').count(), 2);
  await phone(pg, "01-my-time");
});

step("2 Ben, on the desktop, returns one entry with a reason and approves the change-order hours", async () => {
  await signIn(ben, facts.ben);
  const pg = ben.pg;
  await timeReview(pg);
  const review = await text(pg);
  assert.match(review, /Time review/);
  assert.match(review, /Submitted 11\.00/);
  assert.match(review, new RegExp(`Change order work · ${facts.co_number}[^\\n]*3\\.00`));
  await shot(pg, "02-time-review");
  await openEntry(pg, facts.activity, "8.00");
  W.originalEntry = pg.url().match(/\/time\/(\d+)/)[1];
  await pg.fill("input[name=reason]", "Lunch is unpaid: 7.5 hours (synthetic)");
  await submit(pg, pg.getByRole("button", { name: "Return" }));
  assert.match(await flash(pg), /Time returned\./);
  assert.match(await text(pg), /Returned: Lunch is unpaid/);
  await shot(pg, "02-returned");
  await openEntry(pg, facts.co_activity, "3.00");
  await submit(pg, pg.getByRole("button", { name: "Approve" }));
  assert.match(await flash(pg), /Time approved\./);
});

step("3 Kevin sees why, fixes the returned entry and sends it again", async () => {
  const pg = kevin.pg;
  await go(pg, "/field/today");
  const notice = pg.locator("[data-returned-time] a");
  assert.match(await notice.innerText(), /1 time entry was returned to you/);
  await phone(pg, "03-today-returned");
  await submit(pg, notice);
  assert.match(await text(pg), /Returned: Lunch is unpaid: 7\.5 hours/);
  await phone(pg, "03-my-time-returned");
  await submit(pg, pg.getByRole("link", { name: "Fix and send again" }));
  assert.match(await text(pg), /Returned: Lunch is unpaid/);
  assert.equal(await pg.inputValue("input[name=hours]"), "8.00");
  await phone(pg, "03-fix");
  await pg.fill("input[name=hours]", "7.5");
  await submit(pg, pg.getByRole("button", { name: "Send time" }));
  assert.match(await flash(pg), /Time sent again for approval\./);
  const page = await text(pg);
  assert.match(page, /7\.50 hours · Original work/);
  assert.doesNotMatch(page, /Fix and send again/);
  await phone(pg, "03-sent-again");
});

step("4 Ben approves the corrected entry; its whole history is kept", async () => {
  const pg = ben.pg;
  await go(pg, `/time/${W.originalEntry}`);
  await submit(pg, pg.getByRole("button", { name: "Approve" }));
  assert.match(await flash(pg), /Time approved\./);
  const history = await pg.locator("table.data-table tbody").last().innerText();
  const lines = history.split("\n").filter((l) => l.trim());
  assert.equal(lines.length, 4, history);
  assert.match(lines[0], /Submitted[\s\S]*8\.00/);
  assert.match(lines[1], /Returned[\s\S]*8\.00[\s\S]*Lunch is unpaid/);
  assert.match(lines[2], /Sent again[\s\S]*7\.50/);
  assert.match(lines[3], /Approved[\s\S]*7\.50/);
  await shot(pg, "04-approved-history");
});

step("5 Shop time goes on Shop / Company Work, never a customer's job", async () => {
  const pg = ben.pg;
  await timeReview(pg);
  await submit(pg, pg.getByRole("button", { name: "Set up Shop / Company Work" }));
  assert.match(await flash(pg), /Shop \/ Company Work is ready\./);
  const k = kevin.pg;
  await go(k, "/field/time");
  await submit(k, k.getByRole("link", { name: "Shop / Company Work" }));
  assert.match(await text(k), /never billed to a customer/);
  assert.equal(await k.locator("#field-time-extra-toggle").count(), 0);
  await phone(k, "05-shop-time-form");
  await sendTime(k, { work: "Equipment and vehicle upkeep", hours: "1.5", note: "Truck oil change (synthetic)" });
  assert.match(await text(k), /1\.50 hours · Company time/);
  await phone(k, "05-my-time-shop");
  await timeReview(pg);
  const row = pg.locator("tbody tr").filter({ hasText: "Equipment and vehicle upkeep" });
  assert.match(await row.innerText(), /Shop \/ Company Work[\s\S]*Company time/);
  await row.locator("input[type=checkbox]").check();
  await submit(pg, pg.getByRole("button", { name: "Approve selected" }));
  assert.match(await flash(pg), /Approved 1 time entry\./);
});

step("6 The job shows estimated against actual labour hours and cost, by kind of work", async () => {
  const pg = ben.pg;
  await go(pg, `/projects/${facts.project_id}`);
  const table = pg.locator("[data-labour-cost]");
  await table.scrollIntoViewIfNeeded();
  const original = await table.locator('[data-labour-kind="ORIGINAL"]').innerText();
  assert.match(original, /Original work\s+40\.00\s+7\.50\s+-32\.50\s+\$2,600\.00\s+\$487\.50\s+-\$2,112\.50\s+0\.00/);
  const co = await table.locator('[data-labour-kind="CHANGE_ORDER"]').innerText();
  assert.match(co, new RegExp(`${facts.co_number}[\\s\\S]*10\\.00\\s+3\\.00\\s+-7\\.00\\s+\\$650\\.00\\s+\\$195\\.00`));
  const total = await table.locator('[data-labour-kind="TOTAL"]').innerText();
  assert.match(total, /All labour\s+50\.00\s+10\.50\s+-39\.50\s+\$3,250\.00\s+\$682\.50/);
  assert.doesNotMatch(await table.innerText(), /Company time/); // shop time is not on the customer's job
  assert.match(await text(pg), /Wages and payroll are not used/);
  await shot(pg, "06-project-labour");
  await go(pg, `/projects/${facts.project_id}`);
});

step("7 Kevin never reaches office pages, rates or costs", async () => {
  const pg = kevin.pg;
  for (const url of [`/projects/${facts.project_id}`, "/time", `/time/${W.originalEntry}`, "/accounting",
    "/accounting/export/time", "/labour-engine/cost-rates"]) {
    await go(pg, url);
    assert.match(pg.url(), /\/field\//, `${url} is refused to field-only crew`);
    assert.doesNotMatch(await text(pg), MONEY, url);
  }
  await go(pg, "/field/time");
  await phone(pg, "07-my-time-final");
});

step("8 Ben puts the approved hours in a QuickBooks file once and checks QuickBooks matches", async () => {
  const pg = ben.pg;
  await menu(pg, "Company", "/accounting");
  await submit(pg, pg.locator('[data-export="time"] a'));
  assert.match(await text(pg), /12\.00 approved hours in this file/);
  const [download] = await Promise.all([pg.waitForEvent("download"), pg.getByRole("button", { name: /Download the file/ }).click()]);
  const csv = fs.readFileSync(await download.path(), "utf8").replace(/^﻿/, "");
  const lines = csv.trim().split(/\r?\n/);
  assert.equal(lines.length, 4, csv);
  assert.match(lines[0], /^Activity Date,Employee,Customer,Job,Service Item,Hours,Duration \(h:mm\),Billable,Kind of work,Change order/);
  assert.doesNotMatch(csv, /\$/);
  assert.ok(lines.some((l) => l.includes("Company time") && l.includes(",Shop / Company Work,")), csv);
  await go(pg, "/accounting/export/time");
  assert.match(await pg.locator("[data-fresh-count]").innerText(), /^0$/);
  // QuickBooks' Time Activities by Employee Detail report, as exported to CSV after entering the timesheet
  const rows = lines.slice(1).map((l) => l.split(","));
  const report = ["Brayman Construction (synthetic)", "Time Activities by Employee Detail", "",
    ",Activity Date,Customer,Product/Service,Memo/Description,Rates,Duration,Billable,Amount", `${facts.kevin_name},,,,,,,,`,
    ...rows.map((r) => `,${r[0]},${r[2]},Labour,${r.at(-1)},0.00,${r[6]},${r[7]},0.00`), `Total for ${facts.kevin_name},,,,,,12:00,,`].join("\n");
  const file = path.join(facts.workdir, "quickbooks-time.csv");
  fs.writeFileSync(file, report);
  await go(pg, "/accounting/reconcile/time");
  await pg.setInputFiles("input[name=report]", file);
  await submit(pg, pg.getByRole("button", { name: "Check" }));
  const result = await pg.locator("[data-time-reconciliation]").innerText();
  assert.match(result, /1 worker-days match\./);
  assert.doesNotMatch(result, /Hours differ|not in QuickBooks|not approved here|more than once/);
  await shot(pg, "08-quickbooks-check");
});
