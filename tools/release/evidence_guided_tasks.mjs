// Release evidence for the Guided Tasks (Task-First UX, Slice C, 1 Nov 2026), in a real browser against
// tests/guided_tasks_page_server.py (real migrations, temporary database, CSRF on; synthetic owner/estimator Ben,
// project manager Pat, Field-only crew Kevin booked today). Synthetic data only.
//
// Checks: Home's "Start something" offers the three Guided Tasks; Set Up This Project is one screen (settings closed)
// and creates the job with its Brayman Project #; Price This Job shows the work and ONE next item, and after pricing
// points to Review This Estimate; Review This Estimate has ONE Approve that names the total, approves (Gate 1),
// builds the proposal and leaves the estimate locked and approved; the retired wizard starts open the Guided Tasks;
// the project manager reaches the three tasks at 390 px without sideways scrolling; Field Today at 390 px leads with
// today's work, has exactly one visible primary action, keeps "More for today" closed, and the office tasks send
// Field crew back to Field; no 5xx.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_guided_tasks.mjs
import assert from "node:assert/strict";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
let browser, server, base, facts;
const serverErrors = [];
const W = {};  // what one check leaves for the next

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/guided_tasks_page_server.py")], {
    cwd: REPO, env: { ...process.env, GUIDED_TASKS_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 180000);
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
  console.log(`GUIDED_TASKS SERVER_ERRORS=${serverErrors.length}`);
});

async function person(who, viewport = DESK) {
  const ctx = await browser.newContext({ viewport, ...(viewport.width < 500 ? { isMobile: true, hasTouch: true } : {}) });
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
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}
async function flash(pg) {
  return (await pg.locator(".flash-stack, .flash").allInnerTexts().catch(() => [])).join(" | ");
}
// The Task Screen standard: exactly ONE primary action, and it is visible.
async function onePrimary(pg, label) {
  const visible = await pg.locator("main .ts-primary").evaluateAll((els) => els.filter((e) => e.offsetParent !== null).length);
  assert.equal(visible, 1, `${label}: one primary action`);
}
// For the release report: what a person sees on a screen (visible links and buttons in the page body, not the menu).
async function visibleControls(pg, label) {
  const counts = await pg.evaluate(() => {
    const seen = (e) => e.offsetParent !== null && !e.closest("nav, .shell-sidebar, header");
    const main = document.querySelector("main") || document.body;
    return { links: [...main.querySelectorAll("a[href]")].filter(seen).length,
      buttons: [...main.querySelectorAll("button, input[type=submit]")].filter(seen).length };
  });
  console.log(`SCREEN ${label}: ${counts.links} links, ${counts.buttons} buttons visible`);
  return counts;
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

test("Home: Start something offers Set Up This Project, Price This Job and Review This Estimate", async () => {
  const { ctx, pg, errors } = await person("ben");
  await go(pg, "/");
  const band = pg.locator("[data-wizard-home]");
  assert.match(await band.innerText(), /Start something/i);
  const names = await band.locator("[data-guided-task]").allInnerTexts();
  assert.deepEqual(names.map((s) => s.trim()), ["Set Up This Project", "Price This Job", "Review This Estimate"]);
  assert.equal(await band.locator("text=Continue manually").count(), 0, "no wizard / manual fork");
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Set Up This Project: one screen, settings closed, creates the job with its Brayman Project #", async () => {
  const { ctx, pg, errors } = await person("ben");
  await go(pg, "/");
  await press(pg, '[data-guided-task="set_up"]');
  assert.equal(pathOf(pg), "/projects/new");
  await onePrimary(pg, "Set Up This Project");
  await visibleControls(pg, "Set Up This Project");
  assert.equal(await pg.locator("#ts-project-settings").evaluate((d) => d.open), false, "settings closed");
  await pg.selectOption("select[name=client_id]", String(facts.customer_id));
  await pg.fill("input[name=name]", "Avery rear deck (synthetic)");
  await pg.selectOption("select[name=guided_project_type]", "OTHER");
  await pg.check('input[name=contractor_role][value="GENERAL_CONTRACTOR"]');
  await pg.locator("[data-same-as-customer]").check();
  await pg.locator("label[for=plan-start-none]").click();
  assert.equal(await pg.inputValue("input[name=street]"), "12 Synthetic Lane", "same as the customer's address");
  await press(pg, "[data-create-project]");
  assert.match(await flash(pg), /Project BC-\d{4}-\d{4} created/);
  assert.match(pathOf(pg), /^\/projects\/(\d+)\/guided\/scope$/, "the estimate starts on its own: choose the work");
  W.project = Number(pathOf(pg).split("/")[2]);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Price This Job: the work list and ONE next item; priced, it points to Review This Estimate", async () => {
  const { ctx, pg, errors } = await person("ben");
  await go(pg, `/projects/${W.project}/guided/scope`);
  await pg.locator('[data-add-work] input[name=work][value="work_deck"]').check();
  await press(pg, "button[data-add-work-submit]");
  await go(pg, `/projects/${W.project}/guided`);
  assert.match(await pg.locator("[data-ts-purpose]").innerText(), /Price This Job/);
  await onePrimary(pg, "Price This Job");
  await visibleControls(pg, "Price This Job");
  const next = pg.locator("[data-next-step-action]");
  assert.match(await next.innerText(), /^Price Deck/);
  assert.equal(await pg.locator("#ts-price-details").evaluate((d) => d.open), false, "details closed");
  await submit(pg, next);
  assert.match(pathOf(pg), new RegExp(`/projects/${W.project}/guided/stages/\\d+$`));
  await manualCost(pg, { kind: "material", description: "Deck boards (synthetic)", quantity: "40", unit: "ea", unitCost: "32" });
  await manualCost(pg, { kind: "labour", description: "Deck build (synthetic)", quantity: "24" });
  await press(pg, "button[data-confirm-routing]");
  await press(pg, "button[data-nav-complete-next]");
  await go(pg, `/projects/${W.project}/guided`);
  await onePrimary(pg, "Price This Job, priced");
  assert.equal((await pg.locator("[data-next-step-action]").innerText()).trim(), "Review This Estimate");
  assert.match(await pg.locator("[data-progress]").innerText(), /1 of 1 work item complete/);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Review This Estimate: ONE Approve names the total; approving locks it and builds the proposal", async () => {
  const { ctx, pg, errors } = await person("ben");
  await go(pg, `/projects/${W.project}`);
  const step = pg.locator("[data-next-step-action]");
  assert.equal((await step.innerText()).trim(), "Review This Estimate", "the project's next step opens the task");
  await submit(pg, step);
  assert.equal(pathOf(pg), `/projects/${W.project}/guided/pricing`);
  await onePrimary(pg, "Review This Estimate");
  await visibleControls(pg, "Review This Estimate");
  const total = await pg.locator("input[name=expected_total]").inputValue();
  const shown = Number(total).toLocaleString("en-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  assert.match(await pg.locator("[data-approve-consequence]").innerText(), new RegExp(`locks .*\\$${shown.replace(/,/g, ",")}`));
  assert.equal(await pg.locator("#ts-approve-steps").evaluate((d) => d.open), false, "the separate steps are closed");
  await press(pg, "button[data-approve-estimate]");
  assert.match(pathOf(pg), /^\/proposals\/\d+$/, "on to the proposal");
  assert.match(await flash(pg), /Estimate approved and locked/);
  await go(pg, `/projects/${W.project}/guided/pricing`);
  assert.equal(await pg.locator("[data-estimate-approved]").count(), 1);
  assert.equal(await pg.locator("[data-approve-estimate]").count(), 0, "approved once; never again");
  await onePrimary(pg, "Review This Estimate, approved");
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("The retired wizard starts open the Guided Tasks", async () => {
  const { ctx, pg, errors } = await person("ben");
  await go(pg, "/wizards/NEW_PROJECT/start");
  assert.equal(pathOf(pg), "/projects/new");
  await go(pg, `/wizards/GUIDED_ESTIMATING/start?project_id=${W.project}`);
  assert.equal(pathOf(pg), `/projects/${W.project}/guided`);
  await go(pg, `/wizards/MANAGE_PROJECT/start?project_id=${W.project}`);
  assert.equal(pathOf(pg), `/projects/${W.project}`);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Project manager at 390 px: the three Guided Tasks, one primary each, no sideways scrolling", async () => {
  const { ctx, pg, errors } = await person("pat", PHONE);
  await go(pg, "/");
  assert.equal(await pg.locator("[data-guided-task]").count(), 3);
  await noSideways(pg, "home");
  for (const [url, label] of [["/projects/new", "Set Up This Project"], [`/projects/${W.project}/guided`, "Price This Job"],
    [`/projects/${W.project}/guided/pricing`, "Review This Estimate"], ["/tasks/review-this-estimate", "Review list"]]) {
    await go(pg, url);
    assert.ok((await pg.locator("main").innerText()).includes(label.replace(" list", "")), label);
    if (url !== "/tasks/review-this-estimate") await onePrimary(pg, label);
    await noSideways(pg, label);
  }
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Field Today at 390 px: today's work first, one visible primary, the rest closed", async () => {
  const { ctx, pg, errors } = await person("kevin", PHONE);
  assert.equal(pathOf(pg), "/field/today");
  const work = pg.locator("[data-field-today-work]");
  assert.match(await work.innerText(), /Deck framing \(synthetic\)/);
  const primaries = await pg.locator(".field-btn-primary").evaluateAll(
    (els) => els.filter((e) => e.offsetParent !== null && !e.closest("[data-field-texts-setup]")).length);
  assert.equal(primaries, 1, "one primary action");
  await visibleControls(pg, "Field Today (phone)");
  assert.equal(await pg.locator("[data-field-today-more]").evaluate((d) => d.open), false, "More for today is closed");
  const workBox = await work.boundingBox();
  const moreBox = await pg.locator("[data-field-today-more]").boundingBox();
  assert.ok(workBox.y < moreBox.y, "the work list comes before the rest");
  assert.equal(await pg.locator("[data-quick-action]").count(), 7, "the seven quick actions stay");
  await noSideways(pg, "field today");
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("Field crew are sent back to Field from every office Guided Task", async () => {
  const { ctx, pg, errors } = await person("kevin", PHONE);
  for (const url of ["/projects/new", "/estimating/start", "/tasks/review-this-estimate",
    `/projects/${W.project}/guided`, `/projects/${W.project}/guided/pricing`, "/wizards/NEW_PROJECT/start"]) {
    await go(pg, url);
    assert.equal(pathOf(pg), "/field/today", url);
  }
  const refused = await pg.request.post(`${base}/projects/${W.project}/guided/approve`, { maxRedirects: 0 });
  assert.ok([400, 403].includes(refused.status()), `approve refused for crew (${refused.status()})`);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("No server errors in the walk", async () => {
  assert.deepEqual(serverErrors, []);
});
