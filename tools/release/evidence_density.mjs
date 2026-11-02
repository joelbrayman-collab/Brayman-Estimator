// Release evidence for the viewport-first density standard (UX corrective, 2 Nov 2026), in a real browser against
// tests/density_page_server.py (real migrations, temporary database, CSRF on; synthetic owner/estimator Ben, Field-only
// crew Kevin booked today, five customers, five projects, a subcontractor, a supplier account, one piece of equipment
// and filed documents on each of them). Synthetic data only.
//
// The standard (docs/ux/viewport-density-audit-2026-11-02.md): at a 1280 x 800 laptop viewport, 100% zoom, the ACTIVE
// TASK of each primary screen (what the person must see and fill in, and its primary action) is inside the first
// viewport, with no routine vertical scrolling. 1280 x 720 is measured for the record. At 390 x 844 a phone may
// scroll, but Field Today shows today's work and its primary action at once, and no screen scrolls sideways.
//
// Each check prints one line per screen for the release report:
//   DENSITY <screen> vp=<w>x<h> doc=<px> scroll=<px> task=<px> fits=YES|NO fields=<n> blocks=<n>
// where doc is the page height, scroll how far the page scrolls, task the bottom of the active task (its primary
// action and every required input), fields the visible form controls and blocks the visible sections/cards.
// DENSITY_BASELINE=1 only measures (it was used once on the ec80e6f1 screens to record the before numbers).
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_density.mjs
import assert from "node:assert/strict";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const LAPTOP = { width: 1280, height: 800 };
const SHORT = { width: 1280, height: 720 };
const PHONE = { width: 390, height: 844 };
const BASELINE = process.env.DENSITY_BASELINE === "1";
let browser, server, base, facts;
const serverErrors = [];
const W = {};
const report = [];

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/density_page_server.py")], {
    cwd: REPO, env: { ...process.env, DENSITY_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 240000);
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
  await priceOneJob();
});
after(async () => {
  await browser?.close(); server?.kill();
  for (const line of report) console.log(line);
  console.log(`DENSITY SERVER_ERRORS=${serverErrors.length}`);
});

async function person(who, viewport = LAPTOP) {
  const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1,
    ...(viewport.width < 500 ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(20000);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  const [email, password] = facts.people[who];
  await go(pg, "/login");
  await pg.fill("#email", email);
  await pg.fill("#password", password);
  await submit(pg, pg.locator("button[type=submit]"));
  return { ctx, pg, errors };
}
async function go(pg, url) {
  const r = await pg.goto(`${base}${url}`);
  await pg.waitForLoadState();
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
const press = (pg, selector) => submit(pg, pg.locator(selector).first());
const pathOf = (pg) => new URL(pg.url()).pathname;

// The project every office screen is measured on: set up, one work item, priced, so Price This Job and Review This
// Estimate show a real job (the same steps evidence_guided_tasks.mjs proves).
async function priceOneJob() {
  const { ctx, pg } = await person("ben");
  await go(pg, "/projects/new");
  await pg.evaluate(() => document.querySelectorAll("[data-set-up-form] details").forEach((d) => { d.open = true; }));
  await pg.check('input[name=customer_mode][value="existing"]').catch(() => {});
  await pg.selectOption("select[name=client_id]", String(facts.customer_id));
  await pg.fill("input[name=name]", "Avery rear deck (synthetic)");
  await pg.selectOption("select[name=guided_project_type]", "OTHER");
  await pg.check('input[name=contractor_role][value="GENERAL_CONTRACTOR"]');
  await pg.locator("[data-same-as-customer]").check();
  await pg.locator("label[for=plan-start-none]").click();
  await press(pg, "[data-create-project]");
  W.project = Number(pathOf(pg).split("/")[2]);
  await pg.locator('[data-add-work] input[name=work][value="work_deck"]').check();
  await press(pg, "button[data-add-work-submit]");
  await go(pg, `/projects/${W.project}/guided`);
  await submit(pg, pg.locator("[data-next-step-action]"));
  for (const [kind, description, quantity, unit, unitCost] of [["material", "Deck boards (synthetic)", "40", "ea", "32"],
    ["labour", "Deck build (synthetic)", "24", "", ""]]) {
    const form = pg.locator("form[data-manual-cost]");
    if (!(await form.isVisible())) await pg.locator("#manual > summary").click();
    await form.locator("select[name=kind]").selectOption(kind);
    await form.locator("input[name=description]").fill(description);
    await form.locator("input[name=quantity]").fill(quantity);
    if (unit) await form.locator("input[name=unit]").fill(unit);
    if (unitCost) await form.locator("input[name=unit_cost]").fill(unitCost);
    await submit(pg, form.locator("button[type=submit]"));
  }
  await press(pg, "button[data-confirm-routing]");
  await press(pg, "button[data-nav-complete-next]");
  // A second job, set up but not priced: Price This Job with its next item to price.
  await go(pg, `/projects/${facts.project_ids[0]}/guided/scope`);
  if (await pg.locator('[data-add-work] input[name=work][value="work_deck"]').count()) {
    await pg.locator('[data-add-work] input[name=work][value="work_deck"]').check();
    await press(pg, "button[data-add-work-submit]");
  }
  W.unpriced = facts.project_ids[0];
  await ctx.close();
}

// Measure the screen. task: selectors whose visible elements make up the active task (the primary action and the
// required inputs); the task fits when the lowest of them ends inside the first viewport.
async function measure(pg, label, task, { mustFit = true, reason = "" } = {}) {
  await pg.evaluate(() => window.scrollTo(0, 0));
  const m = await pg.evaluate((selectors) => {
    const seen = (e) => e.offsetParent !== null || (e.getClientRects && e.getClientRects().length > 0);
    const main = document.querySelector("main") || document.body;
    let bottom = 0; const missing = [];
    for (const sel of selectors) {
      const els = [...document.querySelectorAll(sel)].filter(seen);
      if (!els.length) { missing.push(sel); continue; }
      for (const e of els) bottom = Math.max(bottom, e.getBoundingClientRect().bottom + window.scrollY);
    }
    const fields = [...main.querySelectorAll("input, select, textarea")]
      .filter((e) => e.type !== "hidden" && seen(e)).length;
    const blocks = [...main.querySelectorAll("section, fieldset, details, .panel, .form-panel, .ge-card, .field-panel")]
      .filter(seen).filter((e) => e.getBoundingClientRect().height > 0).length;
    return { doc: document.documentElement.scrollHeight, vh: window.innerHeight, vw: window.innerWidth,
      side: document.documentElement.scrollWidth - window.innerWidth, bottom: Math.round(bottom), missing, fields, blocks };
  }, task);
  const fits = m.missing.length === 0 && m.bottom <= m.vh;
  if (process.env.DENSITY_SHOTS) {  // optional: full-page screenshots for the audit (not used by the gate)
    await pg.screenshot({ path: path.join(process.env.DENSITY_SHOTS, `${label.replace(/[^A-Za-z0-9@]+/g, "_")}.png`), fullPage: true });
  }
  const row = { label, ...m, scroll: Math.max(0, m.doc - m.vh), fits };
  report.push(`DENSITY ${label} vp=${m.vw}x${m.vh} doc=${m.doc} scroll=${row.scroll} task=${m.bottom} ` +
    `fits=${fits ? "YES" : "NO"} fields=${m.fields} blocks=${m.blocks}${reason ? ` reason="${reason}"` : ""}` +
    `${m.missing.length ? ` missing=${m.missing.join("|")}` : ""}`);
  if (!BASELINE) {
    assert.deepEqual(m.missing, [], `${label}: the active task's parts are on the screen`);
    assert.ok(m.side <= 1, `${label}: page scrolls sideways by ${m.side}px`);
    if (mustFit) assert.ok(fits, `${label}: the active task ends at ${m.bottom}px, below the ${m.vh}px viewport`);
  }
  return row;
}

// A documents page: upload, and the first documents filed there.
const DOC_TASK = ["[data-documents-upload]", "[data-documents-list] tbody tr:first-child"];
// The laptop screens: [label, url, active-task selectors]. Each is measured at 1280 x 800 (the gate) and 1280 x 720.
const screens = () => [
  ["Home", "/", ["[data-needs-attention] .na-head", "[data-wizard-home] [data-guided-task]"]],
  ["Attention", "/operations/attention", ["[data-attention-page] .na-title", "[data-attention-page] [data-attention-list] li:nth-child(-n+5), [data-attention-empty], [data-attention-empty-mine]"]],
  ["Projects", "/projects", [".projects-toolbar .home-start", "[data-project-search-input]", ".projects-row:nth-of-type(-n+6)"]],
  ["Project page", `/projects/${W.project}`, ["[data-next-step-action]"]],
  ["Price This Job (priced)", `/projects/${W.project}/guided`, ["[data-next-step-action]", "[data-stage-list]"]],
  ["Price This Job (to price)", `/projects/${W.unpriced}/guided`, ["[data-next-step-action]", "[data-stage-list]"]],
  ["Review This Estimate", `/projects/${W.project}/guided/pricing`, ["button[data-approve-estimate]", "[data-approve-consequence]", "[data-project-figures]"]],
  ["Documents library", "/documents", ["[data-documents-search] button[type=submit]", "[data-documents-upload]", "[data-documents-list] tbody tr:nth-child(-n+3)"]],
  ["Project documents", `/projects/${facts.field_job_id}/documents`, DOC_TASK],
  ["Customer documents", `/customers/${facts.customer_id}/documents`, DOC_TASK],
  ["Supplier documents", `/suppliers/${facts.supplier_id}/documents`, DOC_TASK],
  ["Subcontractor documents", `/subcontractors/${facts.sub_id}/documents`, DOC_TASK],
  ["Person documents", `/people/${facts.kevin_membership_id}/documents`, DOC_TASK],
  ["Equipment", `/equipment/${facts.equipment_id}`, DOC_TASK],
  ["Purchasing", "/purchasing", ["[data-task-landing] [data-ts-attention]", "[data-task-landing] .link-hub-grid"]],
  ["Time & Money", "/time-and-money", ["[data-task-landing] [data-ts-attention]", "[data-task-landing] .link-hub-grid"]],
  // The calendar grid is its own scrolling box sized to the window (the months scroll inside it, by design).
  ["Calendar", "/schedule", ["main .cal-toolbar", "main .cal-subbar", "main [data-month-scroll]"]],
];

test("1280 x 800: every primary screen shows its active task in the first viewport", async () => {
  const { ctx, pg, errors } = await person("ben", LAPTOP);
  for (const [label, url, task] of screens()) {
    await go(pg, url);
    await measure(pg, label, task);
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("1280 x 720 (for the record): the same screens", async () => {
  const { ctx, pg, errors } = await person("ben", SHORT);
  for (const [label, url, task] of screens()) {
    await go(pg, url);
    await measure(pg, `${label} @720`, task, { mustFit: false });
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

// UX-DENSITY-001. The task: choose the customer, name the job, what is built, your role, the job site and the plans,
// then Create. Calibrayt fills in the rest.
const SET_UP_TASK = ["[data-su-customer]", "input[name=name]", "select[name=guided_project_type]",
  "[data-contractor-role]", "[data-su-site] input[name=street]", "[data-plan-start]", "[data-create-project]"];

test("Set Up This Project, a customer we have: no new-customer fields, the whole task on one screen", async () => {
  const { ctx, pg, errors } = await person("ben", LAPTOP);
  await go(pg, "/projects/new");
  if (!BASELINE) {
    assert.equal(await pg.locator('input[name=customer_mode][value="existing"]').isChecked(), true, "starts on a customer we have");
    assert.equal(await pg.locator("[data-su-new-customer]").isVisible(), false, "new-customer fields take no space");
    assert.equal(await pg.locator("select[name=client_id]").isVisible(), true);
    assert.equal(await pg.locator("#ts-project-settings").evaluate((d) => d.open), false, "settings closed");
  }
  await measure(pg, "Set Up (customer we have)", SET_UP_TASK);
  await pg.setViewportSize(SHORT);
  await measure(pg, "Set Up (customer we have) @720", SET_UP_TASK, { mustFit: false });
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Set Up This Project, a new customer: only what creates one; the customer list takes no space", async () => {
  const { ctx, pg, errors } = await person("ben", LAPTOP);
  await go(pg, "/projects/new");
  await pg.check('input[name=customer_mode][value="new"]');
  if (!BASELINE) {
    assert.equal(await pg.locator("[data-su-new-customer]").isVisible(), true);
    assert.equal(await pg.locator("input[name=new_customer_name]").isVisible(), true, "the name is asked");
    assert.equal(await pg.locator("select[name=client_id]").isVisible(), false, "the customer list is put away");
    assert.equal(await pg.locator("[data-same-as-customer]").isVisible(), false, "no address to copy from a new customer");
  }
  await measure(pg, "Set Up (new customer)", [...SET_UP_TASK, "input[name=new_customer_name]"]);
  // Back to a customer we have: the list returns and the new-customer fields go away again (nothing typed is lost).
  await pg.fill("input[name=new_customer_name]", "Kept while switching (synthetic)");
  await pg.check('input[name=customer_mode][value="existing"]');
  if (!BASELINE) {
    assert.equal(await pg.locator("[data-su-new-customer]").isVisible(), false);
    assert.equal(await pg.locator("select[name=client_id]").isVisible(), true);
    assert.equal(await pg.inputValue("input[name=new_customer_name]"), "Kept while switching (synthetic)");
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Set Up This Project, optional settings: closed until asked for; opened, they sit beside each other", async () => {
  const { ctx, pg, errors } = await person("ben", LAPTOP);
  await go(pg, "/projects/new");
  await pg.locator("#ts-project-settings > summary").click();
  const row = await measure(pg, "Set Up (settings opened)", ["#ts-project-settings select[name=status]"], { mustFit: false,
    reason: "optional settings opened on purpose; the page scrolls to them" });
  if (!BASELINE) {
    // Opened, the settings are a grid of compact selects (several per row), not a tall stack.
    const tops = await pg.locator("[data-project-settings] select").evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().top)));
    const rows = new Set(tops).size;
    assert.ok(rows <= Math.ceil(tops.length / 3), `settings in ${rows} rows for ${tops.length} selects`);
    const tall = await pg.locator("#ts-project-settings").evaluate((d) => Math.round(d.getBoundingClientRect().height));
    assert.ok(tall < 420, `the opened settings are a compact block (${tall}px)`);
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Set Up This Project, refused: the screen comes back with what was typed and opens the part to fix", async () => {
  const { ctx, pg, errors } = await person("ben", LAPTOP);
  // A new customer with no name: refused by the route; the new-customer part is open again with the job kept.
  await go(pg, "/projects/new");
  await pg.check('input[name=customer_mode][value="new"]');
  await pg.fill("input[name=name]", "Refused job (synthetic)");
  await press(pg, "[data-create-project]");
  assert.equal(pathOf(pg), "/projects/new");
  assert.match(await pg.locator(".flash-stack").innerText(), /required/i);
  if (!BASELINE) {
    assert.equal(await pg.inputValue("input[name=name]"), "Refused job (synthetic)");
    assert.equal(await pg.locator('input[name=customer_mode][value="new"]').isChecked(), true);
    assert.equal(await pg.locator("input[name=new_customer_name]").isVisible(), true, "the missing name is in view");
  }
  await measure(pg, "Set Up (refused: no customer name)", [...SET_UP_TASK, ".flash-stack", "input[name=new_customer_name]"]);
  // An exceptional setting with no reason: refused; the settings open on their own, with the reason in view.
  await pg.check('input[name=customer_mode][value="existing"]');
  await pg.selectOption("select[name=client_id]", String(facts.customer_id));
  await pg.evaluate(() => { document.querySelector("#ts-project-settings").open = true; });
  await pg.selectOption("select[name=pricing_posture]", "Premium");
  await pg.evaluate(() => { document.querySelector("#ts-project-settings").open = false; });
  await press(pg, "[data-create-project]");
  assert.equal(pathOf(pg), "/projects/new");
  if (!BASELINE) {
    assert.equal(await pg.locator("#ts-project-settings").evaluate((d) => d.open), true, "the settings with the problem are open");
    assert.equal(await pg.locator("textarea[name=justification_reason]").isVisible(), true);
  }
  await measure(pg, "Set Up (refused: reason needed)", [".flash-stack", "textarea[name=justification_reason]"], { mustFit: false,
    reason: "the refused setting is open below the task; the page scrolls to it" });
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Phone 390 x 844: Field Today shows today's work and its primary action at once; no sideways scrolling", async () => {
  const { ctx, pg, errors } = await person("kevin", PHONE);
  assert.equal(pathOf(pg), "/field/today");
  const row = await measure(pg, "Field Today (phone)", ["[data-field-today-work] h1",
    "[data-field-today-work] .field-btn-primary"]);
  if (!BASELINE) assert.ok(row.fits, "today's work and the primary action are on the first screen");
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Phone 390 x 844: the office screens stay one column with no sideways scrolling", async () => {
  const { ctx, pg, errors } = await person("ben", PHONE);
  for (const [label, url, task] of [["Home", "/", ["[data-wizard-home]"]],
    ["Set Up", "/projects/new", ["[data-create-project]"]],
    ["Project page", `/projects/${W.project}`, ["[data-next-step-action]"]],
    ["Price This Job", `/projects/${W.project}/guided`, ["[data-next-step-action]"]],
    ["Review This Estimate", `/projects/${W.project}/guided/pricing`, ["button[data-approve-estimate]"]],
    ["Documents library", "/documents", ["main"]]]) {
    await go(pg, url);
    await measure(pg, `${label} (phone)`, task, { mustFit: false, reason: "phones may scroll" });
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("No server errors in the walk", async () => {
  assert.deepEqual(serverErrors, []);
});
