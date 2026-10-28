// Release evidence for Guided Project Estimating & Universal Calculator Integration (Joel, 23 Oct 2026), in a real
// browser at desktop (1280 x 900) and iPhone size (390 x 844, touch), against a local office built by the real
// migrations (tests/guided_estimating_server.py: synthetic owner Ben, Field-only crew Kevin, another company's
// owner, a customer and the company costs). Synthetic data only.
//
// Checks: Start New Estimate from Home; New Project with project type and contractor role, then "What work are we
// doing?" with nothing listed or decided (selected work, 28 Oct 2026: no stage template, no N/A); five chosen work
// items, Internal by default and three changed to Subcontracted, and the workflow of exactly that work; an internal stage through its calculator, the estimate review, labour hours and Complete & Next;
// a subcontracted stage with a recorded quote, Select and "Use this cost on the line"; Waiting for Quote while
// other stages go on; a stage refused Complete with no cost; Save & Exit and Resume; the internal cost estimate
// marked INTERNAL — NOT FOR CUSTOMER DISTRIBUTION; Review Pricing & Prepare Proposal blocked while costs are
// missing; a calculator's three choices (Use Result Only, Add to Existing Project with no duplicate, Create New
// Project with Cancel back to the same result, then the new project receiving it); phone layouts without sideways
// scrolling; Kevin calculates on his phone with no project choices and is kept out of the office pages; another
// company sees none of it; no page error and no server error.
// GUIDED_SHOTS=<dir> also saves the key screens there.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_guided_estimating.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const SHOTS = process.env.GUIDED_SHOTS || "";
// The selected work, in catalogue order (the order the Work page lists it).
const SCOPE = {
  work_windows: "INTERNAL", work_excavation: "SUBCONTRACTED", work_footings: "INTERNAL",
  work_electrical: "SUBCONTRACTED", work_hvac: "SUBCONTRACTED",
};
const NAMES = ["Windows", "Excavation", "Footings", "Electrical", "HVAC"];
const PROJECT = "Avery New Home (synthetic)";
let browser, server, base, facts;
const serverErrors = [];
const sessions = {};
const W = {};

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/guided_estimating_server.py")], {
    cwd: REPO, env: { ...process.env, GUIDED_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
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
});
after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`GUIDED_ESTIMATING SERVER_ERRORS=${serverErrors.length}`);
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
  const ctx = await browser.newContext({ viewport, acceptDownloads: true, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  sessions[id] = { ctx, pg, errors };
  const [email, password] = facts.people[key];
  await go(pg, "/login");
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
async function shot(pg, name, locator = null) {
  if (!SHOTS) return;
  if (locator) await locator.first().scrollIntoViewIfNeeded().catch(() => {});
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: false });
}
async function flash(pg) {
  return (await pg.locator(".flash-stack").innerText().catch(() => "")) || "";
}
async function stageUrl(pg, key) {
  await go(pg, `/projects/${W.project}/guided`);
  const href = await pg.locator(`[data-stage="${key}"] a.ge-step-link`).getAttribute("href");
  return href;
}
async function openStage(pg, key) {
  await go(pg, await stageUrl(pg, key));
  assert.equal(await pg.locator(`[data-guided-stage="${key}"]`).count(), 1, key);
}
async function press(pg, selector) {
  await submit(pg, pg.locator(selector).first());
}
async function fillFooting(pg) {
  await pg.locator("input[name=footing_length]").nth(0).fill("120");
  await pg.locator("input[name=footing_width]").nth(0).fill("2");
  await pg.locator("input[name=footing_thickness]").nth(0).fill("10");
  await pg.locator("input[name=footing_length]").nth(1).fill("40");
  await pg.locator("input[name=footing_width]").nth(1).fill("2");
  await pg.locator("input[name=footing_thickness]").nth(1).fill("10");
  await pg.fill("input[name=waste_percent]", "5");
  await press(pg, 'form[data-trade-form] button[value="calculate"]');
}
async function recordQuote(pg, { name, code, reference, amount }) {
  const form = pg.locator("form[data-record-quote]");
  if (!(await form.isVisible())) await pg.locator("#quote > summary").click();
  await form.locator("input[name=subcontractor_legal_name]").fill(name);
  await form.locator("input[name=subcontractor_code]").fill(code);
  await form.locator("input[name=quote_reference]").fill(reference);
  await form.locator("input[name=amount]").fill(amount);
  await form.locator("input[name=quote_date]").fill("2026-10-20");
  await form.locator("input[name=included_scope]").fill("Supply and install");
  await submit(pg, form.locator("button[data-save-quote]"));
}

// ------------------------------------------------------------------ desktop: Ben, New Project → scope → workflow
step("Home has Start New Estimate; it offers a new project, an existing project and the calculators", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  await submit(pg, pg.locator("a[data-home-start-estimate]"));
  assert.equal(pathOf(pg), "/estimating/start");
  const text = await pg.locator("main").innerText();
  for (const t of ["Create a new project", "Calculators", "Estimate an existing project"]) assert.match(text, new RegExp(t));
  assert.deepEqual(errors, []);
});

step("New Project asks what is being built and the contractor role, then asks what work we are doing (nothing listed)", async () => {
  const { pg, errors } = await person("ben", DESK);
  await submit(pg, pg.locator("a[data-new-project-estimate]"));
  assert.equal(pathOf(pg), "/projects/new");
  assert.equal(await pg.locator("[data-start-guided]").isChecked(), true);
  await pg.fill("input[name=name]", PROJECT);
  await pg.selectOption("select[name=client_id]", { label: "Jordan Avery (synthetic)" });
  await pg.selectOption("select[data-guided-project-type]", "NEW_HOME");
  assert.equal(await pg.locator('select[name="project_type"]').inputValue(), "New Build", "commercial type follows");
  await pg.check('input[name=contractor_role][value="GENERAL_CONTRACTOR"]');
  for (const [name, value] of [["pricing_posture", "Fair Market"], ["execution_risk", "Normal"], ["schedule_condition", "Normal"],
    ["site_condition", "Normal"], ["estimate_stage", "Preliminary"], ["delivery_model", "Mixed"]]) {
    await pg.selectOption(`select[name=${name}]`, value);
  }
  await submit(pg, pg.locator("form.form-panel button[type=submit]"));
  assert.match(pathOf(pg), /^\/projects\/\d+\/guided\/scope$/);
  W.project = Number(pathOf(pg).split("/")[2]);
  assert.match(await pg.locator("[data-add-work] h2").innerText(), /What work are we doing\?/);
  assert.equal(await pg.locator("[data-work-item]").count(), 0, "no work is listed until it is chosen");
  assert.equal(await pg.locator("[data-stage-row]").count(), 0, "no stage template");
  const main = await pg.locator("main").innerText();
  assert.doesNotMatch(main, /N\/A/, "no N/A anywhere");
  assert.equal(await pg.locator("[data-add-work] input[name=work]:checked").count(), 0, "nothing defaults");
  await shot(pg, "guided-work-choose-desktop", pg.locator("[data-add-work]"));
  assert.deepEqual(errors, []);
});

step("Work: choose five work items; each is Internal until changed; the workflow lists exactly that work", async () => {
  const { pg, errors } = await person("ben", DESK);
  await pg.fill("[data-work-search]", "foot");
  assert.equal(await pg.locator('[data-work-choice="work_siding"]').isVisible(), false, "search narrows the list");
  await pg.fill("[data-work-search]", "");
  for (const key of Object.keys(SCOPE)) await pg.locator(`[data-add-work] input[name=work][value="${key}"]`).check();
  await press(pg, "button[data-add-work-submit]");
  const listed = await pg.locator("[data-work-item]").evaluateAll((els) => els.map((e) => e.getAttribute("data-work-item")));
  assert.deepEqual(listed, ["work_windows", "work_excavation", "work_footings", "work_electrical", "work_hvac"]);
  for (const key of Object.keys(SCOPE)) assert.equal(await pg.locator(`[data-work-item="${key}"]`).getAttribute("data-responsibility"), "INTERNAL", key);
  for (const [key, resp] of Object.entries(SCOPE)) {
    if (resp === "SUBCONTRACTED") await press(pg, `button[data-set-subcontracted="${key}"]`);
  }
  for (const [key, resp] of Object.entries(SCOPE)) {
    assert.equal(await pg.locator(`[data-work-item="${key}"]`).getAttribute("data-responsibility"), resp, key);
  }
  assert.equal(await pg.locator("#work").getAttribute("data-progress"), "0/5");
  await shot(pg, "guided-work-list-desktop", pg.locator("[data-work-list]"));
  await press(pg, "a[data-open-workflow]");
  assert.equal(pathOf(pg), `/projects/${W.project}/guided`);
  assert.match(await pg.locator("[data-progress]").innerText(), /0 of 5 work items complete/);
  assert.match(await pg.locator("[data-estimating-what]").innerText(), /Estimating: Windows, Excavation, Footings, Electrical, HVAC/);
  const names = await pg.locator("[data-stage-list] > li .ge-stage-head > a, [data-stage-list] > li .ge-stage-head > strong").allInnerTexts();
  assert.deepEqual(names.map((n) => n.trim()), NAMES);
  for (const [key, resp] of Object.entries(SCOPE)) {
    const label = { INTERNAL: "Internal", SUBCONTRACTED: "Subcontracted" }[resp];
    assert.match(await pg.locator(`[data-stage="${key}"] .ge-resp`).innerText(), new RegExp(`^${label}`), key);
  }
  assert.doesNotMatch(await pg.locator("main").innerText(), /N\/A|Excluded/, "nothing excluded is shown");
  await shot(pg, "guided-workflow-stage-list-desktop");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ an internal stage through its calculator
step("Internal work: Footings presents its calculator; the footing result goes to this work", async () => {
  const { pg, errors } = await person("ben", DESK);
  await openStage(pg, "work_footings");
  const tools = await pg.locator("[data-internal-tools] a.ge-tool strong").allInnerTexts();
  for (const t of ["Footing calculator", "Labour hours"]) assert.ok(tools.includes(t), t);
  W.footingStage = Number(pathOf(pg).split("/").pop());
  await shot(pg, "guided-internal-stage-tools-desktop", pg.locator("[data-internal-tools]"));
  await submit(pg, pg.locator('a[data-tool="calculator:footing"]'));
  assert.equal(pathOf(pg), "/calculators/footing");
  await fillFooting(pg);
  const options = pg.locator("[data-result-options]");
  assert.match(await options.innerText(), /Use Result Only[\s\S]*Add to Existing Project[\s\S]*Create New Project/);
  assert.equal(await pg.locator("[data-link-select]").inputValue(), String(W.project), "this project is chosen");
  await pg.waitForFunction((id) => document.querySelector("[data-link-stage]")?.value === String(id), W.footingStage);
  await shot(pg, "guided-calculator-three-options-desktop", options);
  await pg.click("[data-link-button]");
  await pg.waitForSelector("[data-link-status]:not([hidden])");
  assert.match(await pg.locator("[data-link-status]").innerText(), /Saved on Avery New Home/);
  await pg.click("[data-link-button]");  // pressed again: never doubled
  await pg.waitForFunction(() => /Already on/.test(document.querySelector("[data-link-status]")?.innerText || ""));
  assert.deepEqual(errors, []);
});

step("Internal stage: the estimate review, then labour hours and Complete & Next (confirmed costs only)", async () => {
  const { pg, errors } = await person("ben", DESK);
  await submit(pg, pg.locator("[data-link-status] a"));
  assert.match(pathOf(pg), /\/calculations\/\d+$/);
  assert.match(await pg.locator("[data-carried-quantities]").innerText(), /concrete/i);
  await submit(pg, pg.locator("button[data-send-review]"));
  assert.match(pathOf(pg), /\/estimates\/\d+\/versions\/\d+\/calculations\/\d+$/);
  const form = pg.locator("form[action*='/confirm']").first();
  assert.match(await form.locator("select[name=section_id] option:checked").innerText(), /Footings/);
  await form.locator("select[name=target]").selectOption({ label: "Ready-mix concrete 25 MPa (synthetic) (yd3)" });
  await submit(pg, form.locator("button[type=submit]"));
  assert.match(await flash(pg), /Quantity added to the estimate/);
  await submit(pg, pg.locator("a[data-back-to-stage]"));
  assert.equal(pathOf(pg), `/projects/${W.project}/guided/stages/${W.footingStage}`);
  await pg.locator("[data-stage-labour] input[name^=hours_]").first().fill("40");
  await press(pg, "button[data-save-labour]");
  await press(pg, "button[data-confirm-routing]");
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Footings is complete/);
  await go(pg, `/projects/${W.project}/guided`);
  assert.equal(await pg.locator('[data-stage="work_footings"]').getAttribute("data-status"), "COMPLETE");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ subcontracted stages
step("Subcontracted stage: Excavation waits for its quote while other stages go on (out of sequence)", async () => {
  const { pg, errors } = await person("ben", DESK);
  await openStage(pg, "work_excavation");
  await pg.fill("textarea[data-scope-description]", "Dig, backfill and haul away (synthetic)");
  await press(pg, "button[data-setup-subcontract]");
  await press(pg, "button[data-quote-requested]");
  assert.equal(await pg.locator("[data-guided-stage]").getAttribute("data-stage-status"), "WAITING_FOR_QUOTE");
  await go(pg, `/projects/${W.project}/guided`);
  assert.equal(await pg.locator('[data-stage="work_excavation"]').getAttribute("data-status"), "WAITING_FOR_QUOTE");
  assert.equal(await pg.locator('[data-stage="work_footings"]').getAttribute("data-status"), "COMPLETE");
  assert.deepEqual(errors, []);
});

step("Subcontracted stage: record two quotes, select one, Use this cost on the line, then Complete & Next", async () => {
  const { pg, errors } = await person("ben", DESK);
  await openStage(pg, "work_electrical");
  await recordQuote(pg, { name: "Sparks Electric (synthetic)", code: "SPARKS", reference: "EL-9", amount: "24500" });
  assert.match(await flash(pg), /Quote recorded/);
  await recordQuote(pg, { name: "Bright Wire (synthetic)", code: "BRIGHT", reference: "EL-10", amount: "26100" });
  assert.equal(await pg.locator("[data-quotes] tbody tr").count(), 2);
  await press(pg, "button[data-complete-next], button[data-nav-complete-next]");
  assert.match(await flash(pg), /Not complete yet/);  // a quote is evidence; it is not yet a cost
  await press(pg, 'button[data-select-quote="EL-9"]');
  assert.match(await pg.locator("[data-suggested-cost]").innerText(), /Suggested cost/);
  await shot(pg, "guided-subcontract-stage-quote-desktop", pg.locator("[data-subcontract]"));
  await press(pg, "button[data-use-quote-cost]");
  assert.match(await pg.locator("[data-stage-lines]").innerText(), /\$24,500\.00/);
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Electrical is complete/);
  assert.deepEqual(errors, []);
});

step("Missing cost: HVAC cannot be completed without a cost, an approved allowance or a no-cost decision", async () => {
  const { pg, errors } = await person("ben", DESK);
  await openStage(pg, "work_hvac");
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Not complete yet/);
  assert.equal(await pg.locator("[data-guided-stage]").getAttribute("data-stage-status"), "NOT_STARTED");
  assert.match(await pg.locator("[data-missing]").innerText(), /No cost yet/);
  assert.deepEqual(errors, []);
});

step("Save & Exit goes to the project page; Resume estimating comes back to the same stage", async () => {
  const { pg, errors } = await person("ben", DESK);
  await openStage(pg, "work_windows");
  const here = pathOf(pg);
  await press(pg, "button[data-nav-save-exit]");
  assert.equal(pathOf(pg), `/projects/${W.project}`);
  await submit(pg, pg.locator("a[data-hub-guided-resume]"));
  assert.equal(pathOf(pg), here);
  assert.deepEqual(errors, []);
});

step("The internal cost estimate is marked INTERNAL — NOT FOR CUSTOMER DISTRIBUTION and shows what is missing", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${W.project}/guided/internal-cost`);
  assert.equal(await pg.locator("[data-internal-marking]").innerText(), "INTERNAL — NOT FOR CUSTOMER DISTRIBUTION");
  assert.match(await pg.locator("[data-cost-stage='work_electrical']").innerText(), /Subcontract quote EL-9/);
  assert.match(await pg.locator("[data-cost-missing]").innerText(), /HVAC is Not Started/);
  await shot(pg, "guided-internal-cost-document-desktop");
  const [download] = await Promise.all([pg.waitForEvent("download").catch(() => null),
    pg.evaluate((href) => { const a = document.createElement("a"); a.href = href; a.download = "x.pdf"; document.body.append(a); a.click(); },
      `/projects/${W.project}/guided/internal-cost.pdf`)]);
  assert.ok(download, "the PDF downloads");
  assert.deepEqual(errors, []);
});

step("Review Pricing & Prepare Proposal waits while any stage's cost is missing", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${W.project}/guided/pricing`);
  assert.match(await pg.locator("[data-pricing-blocked]").innerText(), /HVAC is Not Started/);
  assert.equal(await pg.locator("[data-create-proposal]").count(), 0);
  assert.equal(await pg.locator("[data-approve-costing]").count(), 0);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ the three choices from an independent calculator
step("Independent calculator: Use Result Only keeps the result and saves nothing", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/calculators/concrete");
  await pg.fill("#length", "24"); await pg.fill("#width", "24"); await pg.fill("#slab_thickness", "4"); await pg.fill("#waste_percent", "5");
  await pg.click("button.cc-calculate");
  await pg.waitForSelector("[data-concrete-result]:not([hidden])");
  W.concrete = await pg.locator("[data-order-amount]").innerText();
  await pg.click("[data-use-result-only]");
  assert.match(await pg.locator("[data-a-status]").innerText(), /Nothing was saved/);
  assert.equal(await pg.locator("[data-order-amount]").innerText(), W.concrete);
  assert.deepEqual(errors, []);
});

step("Independent calculator: Create New Project, then Cancel returns to the calculator with the same result", async () => {
  const { pg, errors } = await person("ben", DESK);
  await submit(pg, pg.locator("[data-new-project-button]"));
  assert.equal(pathOf(pg), "/projects/new");
  assert.match(await pg.locator("[data-carry-banner]").innerText(), /Bringing your Concrete result/);
  await submit(pg, pg.locator("a[data-carry-cancel]"));
  assert.equal(pathOf(pg), "/calculators/concrete");
  await pg.waitForSelector("[data-concrete-result]:not([hidden])");
  assert.equal(await pg.locator("[data-order-amount]").innerText(), W.concrete, "the same result, not entered again");
  assert.equal(await pg.inputValue("#length"), "24");
  assert.equal(await pg.locator("[data-carry-restored]").count(), 1);
  assert.deepEqual(errors, []);
});

step("Independent calculator: Create New Project carries the result into the new Garage project", async () => {
  const { pg, errors } = await person("ben", DESK);
  await submit(pg, pg.locator("[data-new-project-button]"));
  await pg.fill("input[name=name]", "Rivera Garage (synthetic)");
  await pg.selectOption("select[name=client_id]", { label: "Jordan Avery (synthetic)" });
  await pg.selectOption("select[data-guided-project-type]", "GARAGE_OUTBUILDING");
  await pg.check('input[name=contractor_role][value="SELECTED_PORTIONS"]');
  for (const [name, value] of [["pricing_posture", "Fair Market"], ["execution_risk", "Normal"], ["schedule_condition", "Normal"],
    ["site_condition", "Normal"], ["estimate_stage", "Preliminary"], ["delivery_model", "Mixed"]]) {
    await pg.selectOption(`select[name=${name}]`, value);
  }
  await submit(pg, pg.locator("form.form-panel button[type=submit]"));
  assert.match(pathOf(pg), /\/guided\/scope$/);
  W.garage = Number(pathOf(pg).split("/")[2]);
  assert.match(await flash(pg), /Concrete result is saved on the project/);
  assert.equal(await pg.locator("[data-work-item]").count(), 0, "no garage template: the work is chosen");
  await pg.locator('[data-add-work] input[name=work][value="work_concrete_slab"]').check();
  await pg.locator('[data-add-work] input[name=work][value="work_garage_door"]').check();
  await press(pg, "button[data-add-work-submit]");
  assert.equal(await pg.locator("[data-work-item]").count(), 2);
  await press(pg, "a[data-open-workflow]");
  assert.match(await pg.locator("[data-waiting-calculations]").innerText(), /Concrete/);
  await submit(pg, pg.locator("a[data-waiting-calculation]").first());
  assert.match(await pg.locator("[data-carried-inputs]").innerText(), /Length: 24/);
  assert.match(await pg.locator("select[data-stage-select] option:checked").innerText(), /Concrete slab/);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ phone
step("iPhone: the work, the workflow and a work item fit the screen with large choices", async () => {
  const { pg, errors } = await person("ben", PHONE);
  await go(pg, `/projects/${W.project}/guided/scope`);
  await noSideways(pg, "work");
  const box = await pg.locator('button[data-set-internal="work_windows"]').boundingBox();
  assert.ok(box.height >= 44, `Internal / Subcontracted are large enough to tap (${box.height}px)`);
  await shot(pg, "guided-work-phone", pg.locator('[data-work-item="work_windows"]'));
  await go(pg, `/projects/${W.project}/guided`);
  await noSideways(pg, "workflow");
  await shot(pg, "guided-workflow-phone");
  await go(pg, `/projects/${W.project}/guided/stages/${W.footingStage}`);
  await noSideways(pg, "stage");
  await shot(pg, "guided-stage-phone", pg.locator("[data-stage-lines]"));
  await go(pg, `/projects/${W.project}/guided/internal-cost`);
  await noSideways(pg, "internal cost");
  assert.deepEqual(errors, []);
});

step("iPhone Useful Calculators: the office sees the three choices after a result", async () => {
  const { pg, errors } = await person("ben", PHONE);
  await go(pg, "/useful-calculators/footing");
  await fillFooting(pg);
  const options = pg.locator("[data-result-options]");
  assert.match(await options.innerText(), /Use Result Only[\s\S]*Add to Existing Project[\s\S]*Create New Project/);
  await noSideways(pg, "phone calculator");
  await shot(pg, "guided-calculator-three-options-phone", options);
  await pg.selectOption("[data-link-select]", String(W.garage));
  await pg.waitForSelector("[data-stage-wrap]:not([hidden])");
  await pg.click("[data-link-button]");
  await pg.waitForFunction(() => /Saved on Rivera Garage/.test(document.querySelector("[data-link-status]")?.innerText || ""));
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ roles and isolation
step("Kevin (Field only) calculates on his phone but gets no project choices and no office pages", async () => {
  const { pg, errors } = await person("kevin", PHONE);
  await go(pg, "/useful-calculators/footing");
  await fillFooting(pg);
  assert.equal(await pg.locator(".cc-result").count(), 1);
  assert.equal(await pg.locator("[data-result-options], [data-link-project], [data-new-project-button]").count(), 0);
  for (const url of [`/projects/${W.project}/guided`, "/estimating/start", "/projects/new",
    `/projects/${W.project}/guided/internal-cost`]) {
    await go(pg, url);
    assert.equal(pathOf(pg), "/field/today", url);
  }
  assert.deepEqual(errors, []);
});

step("Another company sees none of the project, its stages or its costs", async () => {
  const { pg, errors } = await person("other", DESK);
  for (const url of [`/projects/${W.project}/guided`, `/projects/${W.project}/guided/internal-cost`]) {
    const r = await go(pg, url);
    assert.equal(r.status(), 404, url);
  }
  await go(pg, "/calculators/footing");
  assert.ok(!(await pg.locator("body").innerText()).includes(PROJECT));
  assert.deepEqual(errors, []);
});

step("No server error anywhere in the walk", async () => {
  assert.deepEqual(serverErrors, []);
});
