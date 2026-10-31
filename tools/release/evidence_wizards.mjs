// Release evidence for the four Guided Workflow Wizards (Joel, 24 Oct 2026), in a real browser at desktop
// (1280 x 900) and iPhone size (390 x 844, touch), against a local office built by the real migrations
// (tests/wizards_page_server.py: synthetic owner Ben, Field-only crew Kevin, another company's owner, a customer,
// two New Homes estimated stage by stage — one accepted with its work plan — and a synthetic store with its
// price file and a rival store). Synthetic data only.
//
// Checks: Home asks "What do you need to do?" with Start Guided Wizard / Continue Manually above the fold; Start a
// New Project end to end in its dialog (Next refused without the required answers, automatic draft saving, your role
// required on Details, Create the project once — a second Create makes nothing — the drawings choice, review with
// Edit, Finish to Project Created, then Start Guided Estimating);
// Save & Exit and Resume from Home; Continue Manually and back; Guided Estimating on a costed project (approve the
// costing and apply the company pricing from the wizard, back to the step, 15.0 % true gross margin); Manage a
// Project on the accepted project (real schedule counts, the not-switched-on QuickBooks Time and texting status);
// the Supplier Pro Desk wizard from Quick Quote through issue, the customer's answer and the order package; the
// Project Lead (decision 1) set in Start a New Project and Manage a Project and shown on the Hub and the Company
// Calendar, a Field-only lead still kept out; availability only from the price file, otherwise "Availability not
// confirmed" (decision 3); pickup or delivery "Arranged in the store's own system" and never shown done (decision 2); Ask
// the Tutor answers in place; every wizard page on a phone without sideways scrolling; Kevin kept out; another
// company and a rival store see nothing; no page error and no server error.
// WIZARD_SHOTS=<dir> saves each wizard's screens (desktop and phone) there.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_wizards.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";
import { projectRows } from "./evidence_identity_gate3.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const SHOTS = process.env.WIZARD_SHOTS || "";
const PREFIX = process.env.WIZARD_SHOT_PREFIX || "";
let browser, server, base, facts;
const serverErrors = [];
const sessions = {};
const W = {};

before(async () => {
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/wizards_page_server.py")], {
    cwd: REPO, env: { ...process.env, WIZARDS_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
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
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`WIZARDS SERVER_ERRORS=${serverErrors.length}`);
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
  const supplier = key === "store" || key === "rival";
  const [email, password] = supplier ? facts[`${key}_login`] : facts.people[key];
  await go(pg, supplier ? "/supplier/login" : "/login");
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
async function shot(pg, name) {
  if (!SHOTS) return;
  await pg.screenshot({ path: path.join(SHOTS, `${PREFIX}${name}.png`), fullPage: false });
}
async function flash(pg) {
  return (await pg.locator(".flash-stack, .flash").allInnerTexts().catch(() => [])).join(" | ");
}
async function state(pg) {
  return pg.locator("[data-wizard-step]").getAttribute("data-step-state");
}
async function stepUrl(run, key) { return `/wizards/run/${run}/step/${key}`; }
async function next(pg) { await submit(pg, pg.locator("[data-wizard-next]")); }

// ------------------------------------------------------------------ Home
step("Home: GUIDED WIZARDS with the three wizards above the fold, existing tools kept", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  const section = pg.locator("[data-wizard-home]");
  assert.match(await section.innerText(), /guided wizards/i);
  for (const key of ["NEW_PROJECT", "GUIDED_ESTIMATING", "MANAGE_PROJECT"]) {
    const start = pg.locator(`[data-start-wizard="${key}"]`);
    assert.equal(await start.count(), 1, key);
    const box = await start.boundingBox();
    assert.ok(box.y + box.height <= DESK.height, `${key}: Start is above the fold`);
    assert.equal(await pg.locator(`[data-continue-manually="${key}"]`).count(), 1, key);
  }
  for (const sel of ["a[data-home-start-estimate]", "a.home-start", "a.home-calendar"]) assert.equal(await pg.locator(sel).count(), 1, sel);
  // Compact Home (Joel, 27 Oct 2026): each start once — no separate + Start New Project or Start New Estimate.
  assert.equal(await pg.getByText("+ Start New Project").count(), 0);
  assert.equal(await pg.getByText("Start New Estimate", { exact: true }).count(), 0);
  await shot(pg, "home-what-do-you-need-to-do-desktop");
  const phone = await person("ben", PHONE);
  await go(phone.pg, "/");
  await noSideways(phone.pg, "home phone");
  await shot(phone.pg, "home-what-do-you-need-to-do-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Wizard 1
step("Start a New Project: required answers, autosave, Create once on Details, plans, review, Project Created", async () => {
  // Five compact steps in a dialog since Compact Open a New Project (Joel, 28 Oct 2026): Project, Customer, Details
  // (site, settings, your role and the Project Lead; Continue creates the project), Plans, Review, then Project Created.
  const { pg, errors } = await person("ben", DESK);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  W.run1 = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "project_type");
  assert.match(await pg.locator(".wzc-where").innerText(), /Step 1 of 5/);
  assert.equal(await pg.locator('[role="dialog"][aria-modal="true"]').count(), 1);
  await shot(pg, "wizard1-project-desktop");
  await next(pg);  // refused: not named yet
  assert.match(await flash(pg), /Before you go on/);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "project_type");
  await pg.fill("input[name=name]", "Browser Wizard Home (synthetic)");
  await pg.locator("[data-autosave-status]").filter({ hasText: "Saved automatically" }).waitFor();
  await pg.locator('input[name=guided_project_type][value=NEW_HOME]').check();
  assert.equal(await pg.inputValue("select[name=project_type]"), "New Build");
  await next(pg);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "customer");
  await next(pg);  // refused: no customer chosen yet
  assert.match(await flash(pg), /Before you go on/);
  await pg.selectOption("select[name=client_id]", { label: "Jordan Avery (synthetic)" });
  await shot(pg, "wizard1-customer-desktop");
  await next(pg);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "location");
  await pg.fill("input[name=street]", "21 Synthetic Lane");
  await pg.fill("input[name=municipality]", "Merrickville");
  await pg.selectOption("select[name=province_state]", "Ontario");
  await pg.fill("input[name=postal_zip]", "K0G 1N0");
  assert.equal(await pg.locator("select[data-project-lead-select] option", { hasText: "Other Builder Owner" }).count(), 0);
  await pg.selectOption("select[data-project-lead-select]", { label: "Ben Brayman (synthetic)" });
  // Your role is required: the browser holds Create Project & Continue until it is chosen.
  await pg.locator("[data-create-project]").click();
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "location");
  await pg.selectOption("select[data-contractor-role]", "GENERAL_CONTRACTOR");
  await shot(pg, "wizard1-location-desktop");
  await submit(pg, pg.locator("[data-create-project]"));
  assert.match(pathOf(pg), new RegExp(`/wizards/run/${W.run1}/step/documents$`));
  // Back to Details: the project exists, Create is gone; a replayed Create makes nothing.
  await go(pg, await stepUrl(W.run1, "location"));
  assert.equal(await pg.locator("[data-create-project]").count(), 0);
  assert.equal(await state(pg), "done");
  const replay = await pg.evaluate(async (run) => {
    const token = document.querySelector('meta[name="csrf-token"]').content;
    const body = new URLSearchParams({ csrf_token: token, wizard_run: String(run), name: "Browser Wizard Home (synthetic)",
      client_id: "1", project_type: "New Build", pricing_posture: "Competitive", execution_risk: "Normal",
      schedule_condition: "Normal", site_condition: "Normal", estimate_stage: "Preliminary", delivery_model: "Self-Perform",
      contractor_role: "GENERAL_CONTRACTOR" });
    const r = await fetch("/projects/new", { method: "POST", body, redirect: "manual", credentials: "same-origin" });
    return r.type;
  }, W.run1);
  assert.ok(replay);
  await go(pg, "/projects/");
  assert.equal(await projectRows(pg, "Browser Wizard Home (synthetic)"), 1, "created once");
  // Plans: "This job needs no drawings" is the project's own choice, recorded by Save & Continue.
  await go(pg, await stepUrl(W.run1, "documents"));
  await shot(pg, "wizard1-documents-desktop");
  await pg.locator("[data-no-drawings]").check();
  await next(pg);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "review");
  const summary = await pg.locator("[data-project-summary]").innerText();
  assert.match(summary, /Ben Brayman \(synthetic\)/);
  assert.match(summary, /Jordan Avery \(synthetic\)/);
  assert.match(summary, /General Contractor/i);
  assert.equal(await pg.locator("[data-review-edit]").count(), 5);
  await shot(pg, "wizard1-continue-desktop");
  await submit(pg, pg.locator("[data-finish-project]"));
  assert.match(pathOf(pg), new RegExp(`/wizards/run/${W.run1}/created$`));
  assert.match(await pg.locator("#np-created-title").innerText(), /Project Created Successfully/);
  await shot(pg, "wizard1-created-desktop");
  await submit(pg, pg.locator("[data-start-estimating]"));
  assert.match(pathOf(pg), /\/wizards\/run\/\d+\/step\//);
  assert.match(await pg.locator(".wz-eyebrow").innerText(), /Guided Estimating · Browser Wizard Home/);
  // The Project Hub shows the Project Lead chosen in the wizard.
  await go(pg, "/projects/");
  const hubHref = await pg.locator('a[href^="/projects/"]', { hasText: "Browser Wizard Home (synthetic)" }).first().getAttribute("href");
  await go(pg, hubHref.split("#")[0]);
  assert.equal(await pg.locator("[data-hub-project-lead] [data-project-lead]").innerText(), "Ben Brayman (synthetic)");
  assert.deepEqual(errors, []);
});

step("Start a New Project on a phone: compact, no sideways scroll, the steps across the top", async () => {
  const { pg, errors } = await person("ben", PHONE);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  await noSideways(pg, "wizard 1 phone");
  assert.equal(await pg.locator("[data-stepper] li").count(), 5);
  const nextBox = await pg.locator("[data-wizard-next]").boundingBox();
  assert.ok(nextBox.width >= 120, "Save & Continue is a large tap target");
  await shot(pg, "wizard1-project-phone");
  // Save & Exit, then Resume from Home where it stopped.
  await pg.fill("input[name=name]", "Phone draft (synthetic)");
  await pg.locator('input[name=guided_project_type][value=NEW_HOME]').check();
  await next(pg);
  await submit(pg, pg.locator("[data-wizard-save-exit]"));
  assert.equal(pathOf(pg), "/");
  const resume = pg.locator('[data-resume-wizard="NEW_PROJECT"]');
  assert.ok((await resume.count()) >= 1);
  await submit(pg, resume.first());
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-wizard-step"), "customer");
  await submit(pg, pg.locator("[data-wizard-back]"));
  assert.equal(await pg.inputValue("input[name=name]"), "Phone draft (synthetic)");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Wizard 2
step("Guided Estimating on a costed project: approve costing and price it from the wizard (15.0 % margin)", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${facts.projects.estimate}`);
  await submit(pg, pg.locator('[data-start-wizard="GUIDED_ESTIMATING"]'));
  W.run2 = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  for (const key of ["scope", "internal", "select_quotes", "internal_cost"]) {
    await go(pg, await stepUrl(W.run2, key));
    assert.equal(await state(pg), "done", key);
  }
  await go(pg, await stepUrl(W.run2, "internal"));
  await shot(pg, "wizard2-internal-desktop");
  await go(pg, await stepUrl(W.run2, "pricing"));
  await submit(pg, pg.locator('[data-wizard-action="approve-costing"]'));
  assert.match(pathOf(pg), new RegExp(`/wizards/run/${W.run2}/step/pricing$`));
  await submit(pg, pg.locator('[data-wizard-action="apply-pricing"]'));
  assert.match(pathOf(pg), new RegExp(`/wizards/run/${W.run2}/step/pricing$`));
  assert.equal(await state(pg), "done");
  assert.match(await pg.locator("[data-step-items]").innerText(), /15\.0%/);
  await shot(pg, "wizard2-pricing-desktop");
  // Ask the Tutor answers on the step, without leaving it.
  await pg.locator(".contextual-help summary").click();
  await pg.fill(".contextual-help-question", "What should I do here?");
  await pg.locator(".contextual-help-ask-btn").click();
  await pg.locator(".contextual-help-answer:not([hidden])").waitFor();
  assert.match(pathOf(pg), /\/step\/pricing$/);
  const phone = await person("ben", PHONE);
  await go(phone.pg, await stepUrl(W.run2, "pricing"));
  await noSideways(phone.pg, "wizard 2 phone");
  await shot(phone.pg, "wizard2-pricing-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ Wizard 3
step("Manage a Project on the accepted project: real schedule counts and the actual status of features not on", async () => {
  const { pg, errors } = await person("ben", DESK);
  await go(pg, `/projects/${facts.projects.manage}`);
  await submit(pg, pg.locator('[data-start-wizard="MANAGE_PROJECT"]'));
  W.run3 = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  await go(pg, await stepUrl(W.run3, "schedule"));
  assert.match(await pg.locator("[data-step-headline]").innerText(), /0 of 5 work items scheduled/);
  await shot(pg, "wizard3-schedule-desktop");
  await go(pg, await stepUrl(W.run3, "progress"));
  assert.match(await pg.locator("[data-step-items]").innerText(), /QuickBooks Time[\s\S]*Not switched on/);
  await go(pg, await stepUrl(W.run3, "close"));
  assert.equal(await pg.locator('[data-wizard-action="close-project"]').count(), 1); // Ben is the owner
  await shot(pg, "wizard3-close-desktop");
  // Continue Manually opens the existing page, with the way back.
  await go(pg, await stepUrl(W.run3, "schedule"));
  await submit(pg, pg.locator("[data-continue-manually]"));
  assert.equal(pathOf(pg), "/schedule");
  await submit(pg, pg.locator("[data-wizard-return] a"));
  assert.match(pathOf(pg), /\/step\/schedule$/);
  const phone = await person("ben", PHONE);
  await go(phone.pg, await stepUrl(W.run3, "schedule"));
  await noSideways(phone.pg, "wizard 3 phone");
  await shot(phone.pg, "wizard3-schedule-phone");
  assert.deepEqual(errors, []);
});

step("Project Lead: set in Manage a Project, shown on the Hub and the Calendar; a Field-only lead gains nothing", async () => {
  const { pg, errors } = await person("ben", DESK);
  const pid = facts.projects.manage;
  await go(pg, await stepUrl(W.run3, "people"));
  assert.match(await pg.locator("[data-step-items]").innerText(), /Project Lead[\s\S]*Unassigned/);
  // Kevin (Field-only crew) is authorized company personnel, so he may be the Project Lead.
  await pg.selectOption("select[data-project-lead-select]", { label: "Kevin Field (synthetic crew) (Field crew)" });
  await submit(pg, pg.locator("[data-save-project-lead]"));
  assert.match(pathOf(pg), /\/step\/people$/);
  assert.match(await pg.locator("[data-step-items]").innerText(), /Project Lead[\s\S]*Kevin Field \(synthetic crew\)/);
  assert.match(await pg.locator("[data-step-headline]").innerText(), /0 of \d+|Schedule the work first/); // never an assignment
  await shot(pg, "wizard3-people-desktop");
  await go(pg, `/projects/${pid}`);
  assert.equal(await pg.locator("[data-hub-project-lead] [data-project-lead]").innerText(), "Kevin Field (synthetic crew)");
  await shot(pg, "hub-project-lead-desktop");
  await go(pg, `/schedule?project_id=${pid}`);
  const card = pg.locator(`[data-project-card="${pid}"] [data-calendar-project-lead]`);
  assert.equal(await card.count(), 1);
  assert.equal((await card.textContent()).trim(), "Project Lead: Kevin Field (synthetic crew)");
  // Being the Project Lead gives Kevin no office access: every office page still sends him to Field.
  const kevin = await person("kevin", PHONE);
  for (const url of [`/projects/${pid}`, `/projects/${pid}/lead`, "/schedule", `/wizards/run/${W.run3}/step/people`]) {
    await go(kevin.pg, url);
    assert.equal(pathOf(kevin.pg), "/field/today", url);
  }
  assert.deepEqual(errors, []);
  assert.deepEqual(kevin.errors, []);
});

// ------------------------------------------------------------------ Wizard 4
step("Supplier Pro Desk: Quick Quote, choose it, price, issue, the customer's answer, the order package", async () => {
  const { pg, errors } = await person("store", DESK);
  const sid = facts.store.supplier_id;
  await go(pg, `/supplier/${sid}/`);
  assert.match(await pg.locator("[data-wizard-home]").innerText(), /what do you need to do\?/i);
  await submit(pg, pg.locator('[data-start-wizard="SUPPLIER_PRO_DESK"]'));
  W.run4 = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  await shot(pg, "wizard4-open-desktop");
  await submit(pg, pg.locator('[data-wizard-action="quick-quote"]'));
  assert.match(pathOf(pg), /\/pro-desk\/quick$/);
  await pg.fill("input[name=customer_name]", "Pat Walk-in (synthetic)");
  const q = facts.quick;
  for (const [name, value] of Object.entries(q)) {
    const field = pg.locator(`[name="${name}"]`).first();
    if (!(await field.count())) continue;
    const tag = await field.evaluate((el) => el.tagName);
    if (tag === "SELECT") await field.selectOption(value); else await field.fill(value);
  }
  const standard = pg.locator('[name="assembly_id"]');
  if (await standard.count()) {
    const tag = await standard.first().evaluate((el) => el.tagName + ":" + (el.type || ""));
    if (tag.startsWith("SELECT")) await standard.selectOption(String(facts.store.standard_id));
    else await pg.locator(`[name="assembly_id"][value="${facts.store.standard_id}"]`).check();
  }
  const demo = pg.locator('[name="demo_synthetic"]');
  if (await demo.count()) await demo.first().check().catch(() => {});
  await submit(pg, pg.locator("[data-quick-submit]"));
  assert.match(pathOf(pg), /\/pro-desk\/\d+$/, await flash(pg));
  W.quote = Number(pathOf(pg).match(/\/pro-desk\/(\d+)$/)[1]);
  await submit(pg, pg.locator("[data-wizard-return] a"));
  await pg.locator(`input[name=record][value="quote:${W.quote}"]`).check();
  await submit(pg, pg.locator("[data-use-record]"));
  assert.equal(await state(pg), "done");
  await go(pg, `/supplier/${sid}/wizards/run/${W.run4}/step/pricing`);
  await shot(pg, "wizard4-pricing-desktop");
  assert.match(await pg.locator(".wz-main").innerText(), /No rewards or Pro Account points program/);
  // The quotation's own page does the work: leave out the trusses (quote to follow), issue, record the answer,
  // prepare the order. Each wizard step follows.
  const wiz = (key) => `/supplier/${sid}/wizards/run/${W.run4}/step/${key}`;
  await go(pg, `/supplier/${sid}/pro-desk/${W.quote}`);
  const trusses = pg.locator('tr[data-price-line^="CAL-OB-TRUSS"]:not([data-price-status="EXCLUDED"])');
  for (let guard = 0; guard < 10 && await trusses.count(); guard++) {
    const row = trusses.first();
    await row.locator("details summary", { hasText: "Leave out" }).click();
    await row.locator("input[name=exclude_reason]").fill("Truss quote to follow");
    await submit(pg, row.locator("button", { hasText: "Leave out" }));
  }
  await go(pg, wiz("pricing"));
  assert.equal(await state(pg), "done", await pg.locator("[data-step-missing]").innerText().catch(() => ""));
  await go(pg, wiz("send"));
  assert.equal(await state(pg), "todo");
  await go(pg, `/supplier/${sid}/pro-desk/${W.quote}`);
  await submit(pg, pg.locator("[data-issue]"));
  await go(pg, wiz("send"));
  assert.equal(await state(pg), "done");
  await go(pg, wiz("responses"));
  assert.equal(await state(pg), "waiting");
  await go(pg, `/supplier/${sid}/pro-desk/${W.quote}`);
  const accept = pg.locator("form[data-record-acceptance]");
  await accept.locator("[name=method]").selectOption("in_person").catch(async () => accept.locator('[name=method][value=in_person]').check());
  await accept.locator("[name=customer_name]").fill("Pat Walk-in");
  await submit(pg, accept.locator("button[type=submit]"));
  await go(pg, wiz("order"));
  assert.equal(await state(pg), "todo");
  await submit(pg, pg.locator('[data-wizard-action="order-ready"]'));
  await go(pg, wiz("order"));
  assert.equal(await state(pg), "done");
  await go(pg, wiz("close"));
  // Decision 2: a walk-in order is completed in the store's own system, never shown done here.
  assert.equal(await state(pg), "info");
  assert.match(await pg.locator("[data-step-headline]").innerText(), /Arranged in the store's own system[\s\S]*not confirmed in CalibraytAI/);
  await shot(pg, "wizard4-close-desktop");
  const phone = await person("store", PHONE);
  await go(phone.pg, `/supplier/${sid}/wizards/run/${W.run4}/step/pricing`);
  await noSideways(phone.pg, "wizard 4 phone");
  await shot(phone.pg, "wizard4-pricing-phone");
  assert.deepEqual(errors, []);
});

step("Supplier Pro Desk: availability only from the price file; pickup or delivery arranged in the store's system", async () => {
  const { pg, errors } = await person("store", DESK);
  const sid = facts.store.supplier_id;
  const wiz = (key) => `/supplier/${sid}/wizards/run/${W.run4}/step/${key}`;
  await go(pg, wiz("availability"));
  const items = await pg.locator("[data-step-items]").innerText();
  assert.match(items, /In stock \(supplier-reported\)/); // the synthetic price file's own availability column
  assert.doesNotMatch(items, /\d+\s*(on hand|in stock|available)/i); // never a quantity
  await shot(pg, "wizard4-availability-desktop");
  // The quotation page (where Quick Quote lands) words it the same way.
  await go(pg, `/supplier/${sid}/pro-desk/${W.quote}`);
  const marks = await pg.locator("[data-availability]").allInnerTexts();
  assert.ok(marks.length > 0 && marks.every((t) => /^(In stock|Limited|Special order) \(supplier-reported\)$|^Availability not confirmed$/.test(t)), marks.join("|"));
  // Pickup or delivery: what the customer asked for, recorded; the real status; never shown done.
  await go(pg, wiz("delivery"));
  assert.match(await pg.locator("[data-step-headline]").innerText(), /Arranged in the store's own system/);
  await pg.selectOption("select[data-fulfilment-select]", "PICKUP");
  await submit(pg, pg.locator("[data-save-fulfilment]"));
  assert.match(pathOf(pg), /\/step\/delivery$/);
  assert.match(await pg.locator("[data-step-items]").innerText(), /Pickup at the store/);
  assert.match(await pg.locator("[data-step-headline]").innerText(), /not tracked in CalibraytAI/);
  await shot(pg, "wizard4-delivery-desktop");
  await go(pg, `/supplier/${sid}/pro-desk/${W.quote}/order`);
  assert.equal(await pg.locator('[data-fulfilment="PICKUP"]').count(), 1);
  await go(pg, wiz("close"));
  assert.equal(await state(pg), "info");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ roles and isolation
step("Kevin (Field only) is kept out of every wizard page", async () => {
  const { pg, errors } = await person("kevin", PHONE);
  for (const url of ["/wizards/", `/wizards/run/${W.run1}/step/project_type`, `/wizards/run/${W.run2}/step/pricing`]) {
    await go(pg, url);
    assert.equal(pathOf(pg), "/field/today", url);
  }
  assert.deepEqual(errors, []);
});

step("Another company and a rival store see none of the wizards", async () => {
  const { pg, errors } = await person("other", DESK);
  for (const run of [W.run1, W.run2, W.run3]) {
    const r = await go(pg, `/wizards/run/${run}/step/project`);
    assert.equal(r.status(), 404, `run ${run}`);
  }
  await go(pg, "/");
  assert.equal(await pg.locator("[data-wizard-resume-list]").count(), 0);
  const rival = await person("rival", DESK);
  const sid = facts.store.supplier_id;
  const r = await go(rival.pg, `/supplier/${sid}/wizards/run/${W.run4}/step/open`);
  assert.equal(r.status(), 404);
  assert.deepEqual(errors, []);
  assert.deepEqual(rival.errors, []);
});

step("No server error anywhere in the walk", async () => {
  assert.deepEqual(serverErrors, []);
});
