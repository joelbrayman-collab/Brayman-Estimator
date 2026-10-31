// Release evidence for Selected-work estimating (Approach B, Joel 28 Oct 2026): "Pick the work. Estimate the work.
// Everything else stays out of the way." In a real browser at desktop (1280 x 900) and iPhone size (390 x 844, touch),
// against a local office built by the real migrations (tests/guided_estimating_server.py with a proposal template).
// Synthetic data only.
//
// Checks:
//  Guided — Project Creation → Guided Estimating wizard "What work are we doing?" → Siding (Internal) and Windows
//    (Subcontracted) → quantities and labour on Siding, a selected quote on Windows → internal cost → pricing →
//    customer proposal, with only that work anywhere and no N/A.
//  Manual — project → estimate → Add work → Flooring → its costs → pricing → proposal, with no wizard run.
//  Cross-entry — the wizard, the Work page and the estimate page show and change the same work: work added from the
//    estimate page appears in the wizard; empty work is removed after confirmation; work holding estimate data
//    cannot be removed.
//  Phone — the Work page, the wizard step and the estimate panel fit the screen with large choices.
//  No page error and no server error.
// SELECTED_WORK_SHOTS=<dir> also saves the key screens there.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_selected_work.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const SHOTS = process.env.SELECTED_WORK_SHOTS || "";
const GUIDED = "Harlow Siding & Windows (synthetic)";
const MANUAL = "Okafor Flooring (synthetic)";
let browser, server, base, facts;
const serverErrors = [];
const sessions = {};
const W = {};

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/guided_estimating_server.py")], {
    cwd: REPO, env: { ...process.env, GUIDED_PAGE_PORT: String(port), GUIDED_PROPOSAL_TEMPLATE: "1" },
    stdio: ["ignore", "pipe", "pipe"] });
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
  console.log(`SELECTED_WORK SERVER_ERRORS=${serverErrors.length}`);
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
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
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
const press = (pg, selector) => submit(pg, pg.locator(selector).first());
const pathOf = (pg) => new URL(pg.url()).pathname;
const mainText = (pg) => pg.locator("main").innerText();
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
  return (await pg.locator(".flash-stack, .flash").allInnerTexts().catch(() => [])).join(" | ");
}
const workKeys = (pg) => pg.locator("[data-work-item]").evaluateAll((els) => els.map((e) => e.getAttribute("data-work-item")));
async function stageHref(pg, project, key) {
  await go(pg, `/projects/${project}/guided`);
  return pg.locator(`[data-stage="${key}"] a.ge-step-link`).getAttribute("href");
}
async function manualCost(pg, { kind, description, quantity, unit = "", unitCost = "" }) {
  const form = pg.locator("form[data-manual-cost]");
  if (!(await form.isVisible())) await pg.locator("#manual > summary").click();
  await form.locator("select[name=kind]").selectOption(kind);
  await form.locator("input[name=description]").fill(description);
  await form.locator("input[name=quantity]").fill(quantity);
  if (unit) await form.locator("input[name=unit]").fill(unit);
  if (unitCost) await form.locator("input[name=unit_cost]").fill(unitCost);
  await submit(pg, form.locator("button[type=submit]"));
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
async function newProject(pg, name, guided) {
  await go(pg, guided ? "/projects/new?guided=1" : "/projects/new");
  await pg.fill("input[name=name]", name);
  await pg.selectOption("select[name=client_id]", { label: "Jordan Avery (synthetic)" });
  if (guided) {
    await pg.selectOption("select[data-guided-project-type]", "ADDITION_RENOVATION");
    await pg.check('input[name=contractor_role][value="SELECTED_PORTIONS"]');
  } else if (await pg.locator("[data-start-guided]").isChecked()) {
    await pg.locator("[data-start-guided]").uncheck();
  }
  for (const [field, value] of [["pricing_posture", "Fair Market"], ["execution_risk", "Normal"], ["schedule_condition", "Normal"],
    ["site_condition", "Normal"], ["estimate_stage", "Preliminary"], ["delivery_model", "Mixed"]]) {
    await pg.selectOption(`select[name=${field}]`, value);
  }
  if (!guided) await pg.selectOption('select[name="project_type"]', { index: 1 }).catch(() => {});
  await submit(pg, pg.locator("form.form-panel button[type=submit]"));
}
async function priceAndPropose(pg, project) {
  await go(pg, `/projects/${project}/guided/pricing`);
  if (await pg.locator("[data-approve-costing]").count()) await press(pg, "[data-approve-costing]");
  if (await pg.locator("[data-apply-pricing]").count()) await press(pg, "[data-apply-pricing]");
  await go(pg, `/projects/${project}/guided/pricing`);
  assert.equal(await pg.locator("[data-pricing-blocked]").count(), 0, "nothing blocks pricing");
  await press(pg, "a[data-create-proposal]");
  assert.match(pathOf(pg), /\/proposals\/new|\/proposal/);
  await submit(pg, pg.locator("main form button[type=submit]").last());
  assert.match(pathOf(pg), /^\/proposals\/\d+$/, `the proposal is created (${pathOf(pg)})`);
}

// ------------------------------------------------------------------ Guided: Project Creation → the wizard's work step
step("Guided: Project Creation hands over to What work are we doing? with nothing listed and no N/A", async () => {
  const { pg, errors } = await person("ben", DESK);
  await newProject(pg, GUIDED, true);
  assert.match(pathOf(pg), /^\/projects\/\d+\/guided\/scope$/);
  W.guided = Number(pathOf(pg).split("/")[2]);
  assert.match(await flash(pg), /What work are we doing\?/);
  assert.equal(await pg.locator("[data-work-item]").count(), 0);
  await go(pg, `/projects/${W.guided}`);
  await submit(pg, pg.locator('[data-start-wizard="GUIDED_ESTIMATING"]').first());
  W.run = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  if (!/\/step\/work$/.test(pathOf(pg))) await go(pg, `/wizards/run/${W.run}/step/work`);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "work");
  const text = await mainText(pg);
  assert.match(text, /What work are we doing\?/);
  assert.doesNotMatch(text, /N\/A|construction stages|Review the construction stages/);
  assert.equal(await pg.locator("[data-work-item]").count(), 0, "nothing is chosen for the contractor");
  assert.equal(await pg.locator("input[name=work]:checked").count(), 0);
  await shot(pg, "selected-wizard-work-empty-desktop", pg.locator("[data-add-work]"));
  assert.deepEqual(errors, []);
});

step("Guided: choose Siding and Windows; Windows to Subcontracted; the wizard estimates exactly that work", async () => {
  const { pg, errors } = await person("ben", DESK);
  await submit(pg, pg.locator("[data-wizard-next]"));  // refused: no work chosen
  assert.match(await flash(pg), /Choose the work this estimate is for/);
  await go(pg, `/wizards/run/${W.run}/step/work`);
  await pg.locator('input[name=work][value="work_siding"]').check();
  await pg.locator('input[name=work][value="work_windows"]').check();
  await submit(pg, pg.locator("[data-wizard-next]"));
  await go(pg, `/wizards/run/${W.run}/step/work`);
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows"]);
  assert.match(await pg.locator("[data-step-headline], .wzc-headline, main").first().innerText(), /Estimating: Siding, Windows/);
  await pg.locator('[data-work-item="work_windows"] input[value="SUBCONTRACTED"]').check();
  await submit(pg, pg.locator("[data-wizard-next]"));
  await go(pg, `/wizards/run/${W.run}/step/work`);
  assert.equal(await pg.locator('[data-work-item="work_windows"] input[value="SUBCONTRACTED"]').isChecked(), true);
  assert.equal(await pg.locator('[data-work-item="work_siding"] input[value="INTERNAL"]').isChecked(), true);
  await shot(pg, "selected-wizard-work-chosen-desktop", pg.locator("[data-work-list]"));
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Cross-entry synchronization
step("Cross-entry: the Work page and the estimate page show the same work the wizard chose", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${W.guided}/guided/scope`);
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows"]);
  assert.equal(await pg.locator('[data-work-item="work_siding"]').getAttribute("data-responsibility"), "INTERNAL");
  assert.equal(await pg.locator('[data-work-item="work_windows"]').getAttribute("data-responsibility"), "SUBCONTRACTED");
  await press(pg, "a[data-open-estimate]");
  assert.match(pathOf(pg), /^\/estimates\/\d+/);
  W.guidedEstimate = pathOf(pg);
  const panel = await pg.locator("[data-estimate-work]").innerText();
  assert.match(panel, /What we are estimating/i);
  assert.match(panel, /Siding/); assert.match(panel, /Windows/);
  assert.doesNotMatch(panel, /N\/A|Roofing|Electrical/);
  assert.deepEqual(errors, []);
});

step("Cross-entry: work added from the estimate page appears in the wizard; empty work is removed after confirming", async () => {
  const { pg, errors } = await person("ben", DESK);
  await press(pg, "a[data-estimate-add-work]");
  assert.match(pathOf(pg), new RegExp(`/projects/${W.guided}/guided/scope$`));
  await pg.locator('[data-add-work] input[name=work][value="work_deck"]').check();
  await press(pg, "button[data-add-work-submit]");
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows", "work_deck"]);
  await go(pg, `/wizards/run/${W.run}/step/work`);
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows", "work_deck"], "the wizard sees the same work");
  await go(pg, `/projects/${W.guided}/guided/scope`);
  const deck = pg.locator('[data-work-item="work_deck"]');
  await deck.locator("details.sw-more > summary", { hasText: "More: split materials" }).click();
  await deck.locator('[data-remove-confirm="work_deck"]').check();
  await submit(pg, deck.locator('button[data-remove-work="work_deck"]'));
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows"]);
  await go(pg, `/wizards/run/${W.run}/step/work`);
  assert.deepEqual(await workKeys(pg), ["work_siding", "work_windows"], "removed everywhere");
  await go(pg, W.guidedEstimate);
  assert.doesNotMatch(await pg.locator("[data-estimate-work]").innerText(), /Deck/);
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Guided: quantities, costs, pricing, proposal
step("Guided: Siding (internal) gets its quantity and labour; Windows (subcontracted) gets a selected quote", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, await stageHref(pg, W.guided, "work_siding"));
  assert.equal(await pg.locator('[data-guided-stage="work_siding"]').count(), 1);
  const tools = await pg.locator("[data-internal-tools] a.ge-tool strong").allInnerTexts();
  assert.ok(tools.includes("Labour hours"), "labour is offered for internal work");
  const options = await pg.locator("select[data-change-responsibility] option").allTextContents();
  assert.deepEqual(options.map((o) => o.trim()), ["Internal", "Subcontracted"], "no N/A for selected work");
  await manualCost(pg, { kind: "material", description: "Vinyl siding (synthetic)", quantity: "12", unit: "sq", unitCost: "180" });
  await manualCost(pg, { kind: "labour", description: "Siding install (synthetic)", quantity: "32" });
  await press(pg, "button[data-confirm-routing]");  // the existing rule: who supplies and builds each line
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Siding is complete/);
  await go(pg, await stageHref(pg, W.guided, "work_windows"));
  await recordQuote(pg, { name: "Clearview Windows (synthetic)", code: "CLEAR", reference: "WN-4", amount: "9800" });
  await press(pg, 'button[data-select-quote="WN-4"]');
  await press(pg, "button[data-use-quote-cost]");
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Windows is complete/);
  await go(pg, `/projects/${W.guided}/guided`);
  assert.match(await pg.locator("[data-progress]").innerText(), /2 of 2 work items complete/);
  assert.deepEqual(errors, []);
});

step("Guided: work holding estimate data cannot be removed (nothing is lost)", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${W.guided}/guided/scope`);
  const siding = pg.locator('[data-work-item="work_siding"]');
  await siding.locator("details.sw-more > summary", { hasText: "More: split materials" }).click();
  assert.match(await siding.locator('[data-remove-blocked="work_siding"]').innerText(), /estimate line/);
  assert.equal(await siding.locator('button[data-remove-work="work_siding"]').count(), 0);
  assert.deepEqual(errors, []);
});

step("Guided: the internal cost, the wizard's pricing and the proposal carry only the selected work", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${W.guided}/guided/internal-cost`);
  assert.equal(await pg.locator("[data-cost-stage]").count(), 2);
  assert.equal(await pg.locator("[data-cost-stage='work_siding']").count(), 1);
  assert.equal(await pg.locator("[data-cost-stage='work_windows']").count(), 1);
  assert.doesNotMatch(await mainText(pg), /N\/A|Excluded|Deck/);
  await shot(pg, "selected-internal-cost-desktop");
  await go(pg, `/wizards/run/${W.run}/step/pricing`);
  await submit(pg, pg.locator('[data-wizard-action="approve-costing"]'));
  await submit(pg, pg.locator('[data-wizard-action="apply-pricing"]'));
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-step-state"), "done");
  await go(pg, `/wizards/run/${W.run}/step/proposal`);
  await submit(pg, pg.locator('[data-wizard-action="create-proposal"]'));
  await submit(pg, pg.locator("main form button[type=submit]").last());
  assert.match(pathOf(pg), /^\/proposals\/\d+$/, `the proposal is created (${pathOf(pg)})`);
  const proposal = await mainText(pg);
  assert.match(proposal, /Siding/); assert.match(proposal, /Windows/);
  assert.doesNotMatch(proposal, /N\/A|Deck|Roofing|INTERNAL — NOT FOR CUSTOMER/);
  await shot(pg, "selected-proposal-desktop");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Manual: project → estimate → Add work → proposal
step("Manual: project, estimate, Add work (Flooring) from the estimate, cost it, price it and propose it — no wizard", async () => {
  const { pg, errors } = await person("ben", DESK);
  await newProject(pg, MANUAL, false);
  await go(pg, "/projects/");
  const href = await pg.locator('a[href^="/projects/"]', { hasText: MANUAL }).first().getAttribute("href");
  W.manual = Number(href.split("#")[0].split("/")[2]);
  await go(pg, `/estimates/new?project_id=${W.manual}`);
  await pg.fill("input[name=estimate_number]", "EST-SW-1");
  await pg.fill("input[name=title]", "Okafor flooring estimate (synthetic)");
  await submit(pg, pg.locator("main form button[type=submit]").first());
  if (!/^\/estimates\/\d+/.test(pathOf(pg))) {
    await go(pg, "/estimates/");
    await go(pg, await pg.locator("a", { hasText: "Okafor flooring estimate (synthetic)" }).first().getAttribute("href"));
  }
  W.manualEstimate = pathOf(pg);
  assert.match(await pg.locator("[data-estimate-work]").innerText(), /No work chosen yet/);
  await press(pg, "a[data-estimate-add-work]");
  assert.match(await pg.locator("[data-add-work] h2").innerText(), /What work are we doing\?/);
  await pg.locator('[data-add-work] input[name=work][value="work_flooring"]').check();
  await press(pg, "button[data-add-work-submit]");
  assert.deepEqual(await workKeys(pg), ["work_flooring"]);
  await go(pg, W.manualEstimate);
  const panel = await pg.locator("[data-estimate-work]").innerText();
  assert.match(panel, /Flooring/); assert.match(panel, /0 of 1/);
  await go(pg, await stageHref(pg, W.manual, "work_flooring"));
  await manualCost(pg, { kind: "material", description: "Engineered hardwood (synthetic)", quantity: "600", unit: "ft²", unitCost: "6.5" });
  await manualCost(pg, { kind: "labour", description: "Flooring install (synthetic)", quantity: "24" });
  await press(pg, "button[data-confirm-routing]");  // the existing rule: who supplies and builds each line
  await press(pg, "button[data-nav-complete-next]");
  assert.match(await flash(pg), /Flooring is complete/);
  await priceAndPropose(pg, W.manual);
  const proposal = await mainText(pg);
  assert.match(proposal, /Flooring/);
  assert.doesNotMatch(proposal, /N\/A|Siding|Windows/);
  await go(pg, `/projects/${W.manual}`);
  assert.match(await pg.locator("[data-hub-work]").innerText(), /Estimating: Flooring · 1 of 1 work item complete/);
  assert.equal(await pg.locator('[data-resume-wizard="GUIDED_ESTIMATING"]').count(), 0, "no wizard was started");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ phone
step("iPhone: the Work page, the wizard's work step and the estimate panel fit the screen with large choices", async () => {
  const { pg, errors } = await person("ben", PHONE);
  await go(pg, `/projects/${W.guided}/guided/scope`);
  await noSideways(pg, "work page");
  const choice = await pg.locator('[data-work-choice="work_roofing"]').boundingBox();
  assert.ok(choice.height >= 44, `work choices are large enough to tap (${choice.height}px)`);
  await shot(pg, "selected-work-page-phone", pg.locator("[data-work-list]"));
  await go(pg, `/wizards/run/${W.run}/step/work`);
  await noSideways(pg, "wizard work step");
  await shot(pg, "selected-wizard-work-phone", pg.locator("[data-work-list]"));
  await go(pg, W.manualEstimate);
  await noSideways(pg, "estimate panel");
  await shot(pg, "selected-estimate-panel-phone", pg.locator("[data-estimate-work]"));
  await go(pg, `/projects/${W.manual}/guided`);
  await noSideways(pg, "workflow");
  assert.deepEqual(errors, []);
});

step("No server error anywhere in the walk", async () => {
  assert.deepEqual(serverErrors, []);
});
