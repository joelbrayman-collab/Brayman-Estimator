// Release evidence for Compact Open a New Project (Joel, 28 Oct 2026), in a real browser at three widths — desktop
// (1600 x 1000), laptop (1280 x 800) and narrow (390 x 844, touch) — against a local office built by the real
// migrations (tests/project_creation_page_server.py: owner Ben and one existing customer, Marc Bouliion). Synthetic
// data only; everything goes through the normal pages (no database edits, no shortcuts).
//
// At each width, one synthetic project end to end through the normal UI: Project → Customer (a new customer) →
// Details (job site, the pre-filled settings, your role, the Project Lead; Create Project & Continue creates it) →
// Plans (a real plan PDF uploaded with the proven Step-4 form) → Review (each section with Edit; Edit and back keeps
// everything) → Finish → Project Created → Open Project, and the project page shows what was entered. Also: the
// dialog (role="dialog", aria-modal, the five numbered steps, the current one marked), every field labelled, the role
// marked required beyond colour (an asterisk and aria-required), validation messages announced (role="alert"),
// Tab kept inside the dialog, × and Escape are Save & Exit (nothing lost), the plan kept through Back and Continue,
// no sideways scrolling, how much each step scrolls, no page error and no server error.
// COMPACT_SHOTS=<dir> saves the six screens (Project, Customer, Details, Plans, Review, Project Created) per width.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_compact_new_project.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";
import { projectRows } from "./evidence_identity_gate3.mjs";

const WIDTHS = [
  { label: "desktop", viewport: { width: 1600, height: 1000 } },
  { label: "laptop-1280", viewport: { width: 1280, height: 800 } },
  { label: "narrow", viewport: { width: 390, height: 844 } },
];
const SHOTS = process.env.COMPACT_SHOTS || "";
const PLAN_PDF = fs.readFileSync(path.join(REPO, "tests/fixtures/e2e/synthetic-site-plan.pdf"));
let browser, server, base, facts;
const serverErrors = [];
const measures = [];

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/project_creation_page_server.py")], {
    cwd: REPO, env: { ...process.env, PROJECT_CREATION_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
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
  await browser?.close(); server?.kill();
  for (const m of measures) console.log(`SCROLL ${m}`);
  console.log(`COMPACT_NEW_PROJECT SERVER_ERRORS=${serverErrors.length}`);
});

async function session(viewport) {
  const phone = viewport.width < 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  const [email, password] = facts.people.ben;
  await go(pg, "/login");
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await submit(pg, pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(pg.url(), /\/login/, "Ben signs in");
  return { ctx, pg, errors };
}
async function go(pg, url) { await pg.goto(url.startsWith("http") ? url : `${base}${url}`); await pg.waitForLoadState(); }
async function submit(pg, locator) { await Promise.all([pg.waitForNavigation(), locator.click()]); await pg.waitForLoadState(); }
const pathOf = (pg) => new URL(pg.url()).pathname;
const stepOf = (pg) => pg.getAttribute("[data-wizard-step]", "data-wizard-step");
async function flash(pg) { return (await pg.locator(".flash-stack").allInnerTexts().catch(() => [])).join(" | "); }
async function continueOn(pg) { await submit(pg, pg.locator("[data-wizard-next]")); }
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
  const overlay = await pg.evaluate(() => { const o = document.querySelector(".wzc-overlay"); return o ? o.scrollWidth - o.clientWidth : 0; });
  assert.ok(overlay <= 1, `${label}: the dialog scrolls sideways by ${overlay}px`);
}
async function measure(pg, label, step) {
  const m = await pg.evaluate(() => {
    const d = document.querySelector(".wzc-modal");
    const r = d.getBoundingClientRect();
    return { h: Math.round(d.scrollHeight), vh: window.innerHeight, w: Math.round(r.width) };
  });
  measures.push(`${label} ${step}: dialog ${m.w}x${m.h}px in a ${m.vh}px window (${m.h <= m.vh ? "no scrolling" : `scrolls ${m.h - m.vh}px`})`);
  return m;
}
async function shot(pg, label, name) {
  if (!SHOTS) return;
  await pg.evaluate(() => { const o = document.querySelector(".wzc-overlay"); if (o) o.scrollTop = 0; });
  await pg.screenshot({ path: path.join(SHOTS, `${label}-${name}.png`), fullPage: false });
}
async function everyFieldLabelled(pg, label) {
  const unlabelled = await pg.evaluate(() => [...document.querySelectorAll(".wzc-form input:not([type=hidden]), .wzc-form select, .wzc-form textarea")]
    .filter((el) => !el.disabled && el.offsetParent !== null)
    .filter((el) => !(el.labels && el.labels.length) && !el.getAttribute("aria-label") && !el.getAttribute("aria-labelledby"))
    .map((el) => el.name || el.id));
  assert.deepEqual(unlabelled, [], `${label}: every visible field has a label`);
}

for (const { label, viewport } of WIDTHS) {
  test(`${label} (${viewport.width}px): Project → Customer → Details → Plans → Review → Finish → Open Project`, async () => {
    const narrow = viewport.width < 500;
    const { ctx, pg, errors } = await session(viewport);
    const job = `Compact ${label} deck (synthetic)`;
    const customer = `Compact ${label} customer (synthetic)`;
    await go(pg, "/");
    await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
    const run = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);

    // 1 Project: the dialog launches with the five steps, Project current.
    assert.equal(await stepOf(pg), "project_type");
    assert.equal(await pg.locator('[role="dialog"][aria-modal="true"]').count(), 1);
    assert.equal(await pg.locator("[data-stepper] li").count(), 5);
    assert.equal(await pg.locator('[data-stepper] [aria-current="step"]').count(), 1);
    await noSideways(pg, `${label} project`);
    await everyFieldLabelled(pg, `${label} project`);
    // Required validation, announced inside the dialog.
    await continueOn(pg);
    assert.match(await flash(pg), /Before you go on.*Name the project/);
    assert.equal(await pg.locator('.wzc-modal [data-wizard-flash] [role="alert"]').count(), 1, "the refusal is announced");
    await pg.fill('[name="name"]', job);
    // The Brayman Project # is assigned when the project is created (Joel, 30 Oct 2026); the client's own number is typed.
    assert.match(await pg.locator("[data-brayman-number]").innerText(), /Assigned automatically/);
    await pg.fill('[name="client_project_number"]', `CNP-${viewport.width}`);
    await pg.locator('[name="guided_project_type"][value="ADDITION_RENOVATION"]').check();
    await pg.fill('[name="description"]', "Rear deck and stairs (synthetic)");
    await measure(pg, label, "1 Project");
    await shot(pg, label, "1-project");
    await continueOn(pg);

    // 2 Customer: a new customer, saved in place.
    assert.equal(await stepOf(pg), "customer");
    await pg.locator('[data-customer-mode="new"]').check();
    await pg.fill('[name="new_customer_name"]', customer);
    await pg.fill('[name="new_customer_phone"]', "613-555-0101");
    await pg.fill('[name="new_customer_email"]', "compact.customer@example.invalid");
    await pg.fill('[name="new_customer_street_address"]', "40 Synthetic Crescent");
    await pg.fill('[name="new_customer_city"]', "Kemptville");
    await pg.selectOption('[name="new_customer_province_state"]', "Ontario");
    await pg.fill('[name="new_customer_postal_code"]', "K0G 1J0");
    await noSideways(pg, `${label} customer`);
    await everyFieldLabelled(pg, `${label} customer`);
    await measure(pg, label, "2 Customer");
    await shot(pg, label, "2-customer");
    await continueOn(pg);

    // 3 Details: Back keeps Project and Customer; the role is required (an asterisk and aria-required, not colour).
    assert.equal(await stepOf(pg), "location", await flash(pg));
    await submit(pg, pg.locator("[data-wizard-back]"));
    assert.equal(await stepOf(pg), "customer");
    await submit(pg, pg.locator("[data-wizard-back]"));
    assert.equal(await pg.inputValue('[name="name"]'), job, "Back keeps the project");
    assert.equal(await pg.inputValue('[name="client_project_number"]'), `CNP-${viewport.width}`);
    await continueOn(pg);
    assert.match(await pg.locator("[data-customer-select]").evaluate((s) => s.options[s.selectedIndex].textContent), new RegExp(customer.replace(/[()]/g, "\\$&")));
    await continueOn(pg);
    assert.equal(await stepOf(pg), "location");
    assert.equal(await pg.getAttribute("[data-contractor-role]", "aria-required"), "true");
    assert.match(await pg.locator('label:has([data-contractor-role])').innerText(), /\*/);
    await pg.locator("[data-same-as-customer]").check();
    assert.equal(await pg.inputValue('[data-job="street"]'), "40 Synthetic Crescent");
    // The settings come pre-filled from the existing defaults (nothing hard-coded here).
    const settings = {};
    for (const n of ["permit_context_class", "pricing_posture", "execution_risk", "schedule_condition", "site_condition", "estimate_stage", "delivery_model"]) {
      settings[n] = await pg.inputValue(`[name="${n}"]`);
      assert.ok(settings[n], `${n} is pre-filled`);
    }
    await pg.selectOption("[name=execution_risk]", { index: 0 });
    settings.execution_risk = await pg.inputValue("[name=execution_risk]");
    await pg.selectOption("[data-project-lead-select]", { label: "Ben Brayman (synthetic)" });
    await pg.locator("[data-create-project]").click();  // held: no role yet
    assert.equal(await stepOf(pg), "location");
    assert.equal(await pg.locator("[data-contractor-role]").evaluate((el) => el.validity.valueMissing), true);
    await pg.selectOption("[data-contractor-role]", "GENERAL_CONTRACTOR");
    await noSideways(pg, `${label} details`);
    await everyFieldLabelled(pg, `${label} details`);
    if (!narrow) {
      const site = await pg.locator("#np-sec-site").boundingBox();
      const set = await pg.locator("#np-sec-settings").boundingBox();
      assert.ok(Math.abs(site.y - set.y) < 4 && set.x > site.x + 200, "Site information beside Project settings");
    }
    await measure(pg, label, "3 Details");
    await shot(pg, label, "3-details");
    await submit(pg, pg.locator("[data-create-project]"));

    // 4 Plans: the proven Step-4 upload (a real PDF); the plan stays through Back and Continue.
    assert.equal(await stepOf(pg), "documents", await flash(pg));
    await noSideways(pg, `${label} plans`);
    await everyFieldLabelled(pg, `${label} plans`);
    await measure(pg, label, "4 Plans");
    await shot(pg, label, "4-plans");
    await pg.setInputFiles('input[name="plan_file"]', { name: "compact-plan-synthetic.pdf", mimeType: "application/pdf", buffer: PLAN_PDF });
    await continueOn(pg);
    assert.equal(await stepOf(pg), "review", await flash(pg));
    assert.match(await flash(pg), /compact-plan-synthetic\.pdf added to the project/);
    await submit(pg, pg.locator("[data-wizard-back]"));
    assert.equal(await stepOf(pg), "documents");
    assert.equal(await pg.locator("[data-step-items] li", { hasText: "compact-plan-synthetic.pdf" }).count(), 1, "the plan is kept");
    assert.equal(await pg.getAttribute("[data-wizard-step]", "data-step-state"), "done");
    await continueOn(pg);

    // 5 Review: every section with Edit; Edit and back keeps everything.
    assert.equal(await stepOf(pg), "review");
    const summary = await pg.locator("[data-project-summary]").innerText();
    for (const expected of [job, `CNP-${viewport.width}`, "Rear deck and stairs (synthetic)", customer, "613-555-0101",
      "compact.customer@example.invalid", "40 Synthetic Crescent", "General Contractor", "Ben Brayman (synthetic)", "compact-plan-synthetic.pdf",
      settings.pricing_posture, settings.estimate_stage]) {
      assert.ok(summary.toLowerCase().includes(expected.toLowerCase()), `Review shows ${expected}`);
    }
    assert.equal(await pg.locator("[data-review-edit]").count(), 5);
    await noSideways(pg, `${label} review`);
    await measure(pg, label, "5 Review");
    await shot(pg, label, "5-review");
    for (const key of ["project_type", "customer", "location", "documents"]) {
      await submit(pg, pg.locator(`[data-review-edit="${key}"]`).first());
      assert.equal(await stepOf(pg), key, `Edit goes to ${key}`);
      await go(pg, `/wizards/run/${run}/step/review`);
    }
    assert.equal(await pg.locator("[data-project-summary]").innerText(), summary, "Edit and back erased nothing");

    // Keyboard: Tab stays inside the dialog; × and Escape are Save & Exit (tested here, then resumed).
    for (let i = 0; i < 60; i += 1) await pg.keyboard.press("Tab");
    assert.equal(await pg.evaluate(() => !!document.activeElement.closest(".wzc-modal")), true, "Tab stays in the dialog");
    assert.equal(await pg.evaluate(() => getComputedStyle(document.activeElement).outlineStyle !== "none" || getComputedStyle(document.activeElement).boxShadow !== "none"), true, "focus is visible");
    await pg.locator("#wzc-dialog-title").focus();
    await Promise.all([pg.waitForNavigation(), pg.keyboard.press("Escape")]);
    assert.equal(pathOf(pg), "/", "Escape is Save & Exit");
    await submit(pg, pg.locator(`[data-resume-run="${run}"] [data-resume-wizard]`));
    assert.equal(await stepOf(pg), "review");
    assert.equal(await pg.locator("[data-project-summary]").innerText(), summary, "Save & Exit kept everything");

    // Finish (double-pressed: sent once) → Project Created → Open Project.
    let posts = 0;
    const watch = (r) => { if (r.method() === "POST") posts += 1; };
    pg.on("request", watch);
    await Promise.all([pg.waitForURL(new RegExp(`/wizards/run/${run}/created$`)), pg.locator("[data-finish-project]").dblclick()]);
    pg.off("request", watch);
    assert.equal(posts, 1, "Finish sent once");
    const created = await pg.locator("[data-created-summary]").innerText();
    for (const expected of [job, `CNP-${viewport.width}`, customer, "Lead"]) assert.ok(created.includes(expected), `Project Created shows ${expected}`);
    assert.match(await pg.locator("[data-brayman-project-number]").innerText(), /^BC-\d{4}-\d{4}$/, "the Brayman Project # was assigned");
    await noSideways(pg, `${label} created`);
    await shot(pg, label, "6-created");
    const open = await pg.locator("[data-open-project]").boundingBox();
    const another = await pg.locator("[data-create-another]").boundingBox();
    assert.ok(narrow ? open.y < another.y : open.x < another.x, "Open Project comes first");
    await submit(pg, pg.locator("[data-open-project]"));
    assert.match(pathOf(pg), /^\/projects\/\d+$/);
    const page = await pg.locator("main").innerText();
    for (const expected of [job, customer]) assert.ok(page.includes(expected), `the project page shows ${expected}`);
    // Exactly one project was made.
    await go(pg, "/projects/");
    assert.equal(await projectRows(pg, job), 1, "one project");
    assert.deepEqual(errors, []);
    await ctx.close();
  });
}

test("no server error anywhere", () => { assert.deepEqual(serverErrors, []); });
