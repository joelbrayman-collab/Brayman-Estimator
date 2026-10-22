// Release evidence for the Workflow Maps (Joel, 21 Oct 2026), in a real browser against a local training site
// (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on, the synthetic training company with
// its owner, office staff, field crew, supplier owner and PRO Desk person). Synthetic data only.
//
// The Contractor Workflow Map from the office menu, the Supplier Workflow Map from the Supplier Hub, the Field
// workflow from Field and the Workflow map in the Training Centre: stage cards expand the stage, Back / Next and
// the arrow keys move between stages and keep the address (?stage=), keyboard focus, every link shown answers
// (no 404, no 500, nobody sent to sign in), each person sees only what they may open, desktop and a 390-pixel
// iPhone without sideways scrolling, and map -> lesson -> tick a step -> back to the map keeps the ticked step.
// Any response of 500 or more, or a page JavaScript error, fails the walk.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test --test-concurrency=1 tools/release/evidence_workflow_map.mjs
// EVIDENCE_SHOTS=<folder> saves a screenshot of each map.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const sessions = {};

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/training_page_server.py")], {
    cwd: REPO, env: { ...process.env, TRAINING_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("training site did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("training site exited\n" + out)); }
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
  console.log(`WORKFLOW_MAP_SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

async function shot(pg, name) {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: false });
}
async function noSideways(pg, label) {
  const [sw, iw] = await pg.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  assert.ok(sw <= iw + 1, `${label}: page scrolls sideways (${sw} > ${iw})`);
}
async function signIn(name, key, viewport) {
  if (sessions[name]) return sessions[name];
  const ctx = await browser.newContext({ viewport });
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${name}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  const person = facts.people[key];
  const supplier = person.role === "SUPPLIER";
  await pg.goto(`${base}${supplier ? "/supplier/login" : "/login"}`);
  await pg.fill("input[name=email]", person.email);
  await pg.fill("input[name=password]", person.password);
  await Promise.all([pg.waitForNavigation(), pg.locator("form button[type=submit]").first().click()]);
  sessions[name] = { ctx, pg };
  return sessions[name];
}
// Every link inside the map answers: no 404, no 500, and nobody is sent to sign in.
async function everyLinkAnswers(s, label) {
  const hrefs = await s.pg.locator("[data-wf-map] a[href]").evaluateAll((as) =>
    [...new Set(as.map((a) => a.getAttribute("href")).filter((h) => h && !h.startsWith("#")).map((h) => h.split("#")[0]))]);
  assert.ok(hrefs.length > 5, `${label}: the map has links`);
  for (const href of hrefs) {
    const r = await s.ctx.request.get(`${base}${href}`, { maxRedirects: 0 });
    assert.ok([200, 302].includes(r.status()), `${label}: ${href} answered ${r.status()}`);
    if (r.status() === 302) assert.ok(!/\/login|\/signin/.test(r.headers().location || ""), `${label}: ${href} asks to sign in`);
  }
  return hrefs;
}
async function current(pg) { return pg.getAttribute("[data-wf-map]", "data-wf-current"); }

test("contractor owner: Workflow Guide in the menu, stage cards, Back / Next, arrow keys, links", async () => {
  const ben = await signIn("ben", "ben", DESK);
  const { pg } = ben;
  await pg.goto(`${base}/`);
  await Promise.all([pg.waitForNavigation(), pg.locator('.sidebar-link[href="/workflow"]').click()]);
  assert.equal(new URL(pg.url()).pathname, "/workflow");
  assert.equal(await current(pg), "c-setup");
  assert.ok(await pg.locator('[data-wf-page="c-setup"]').isVisible());
  for (const id of ["c-plan", "c-price", "c-win", "c-build", "c-close"]) assert.equal(await pg.locator(`[data-wf-page="${id}"]`).isVisible(), false);
  await shot(pg, "workflow-contractor-desktop");
  await pg.locator('[data-wf-card="c-price"]').click();
  assert.equal(await current(pg), "c-price");
  assert.ok(await pg.locator('[data-wf-page="c-price"]').isVisible());
  assert.equal(await pg.getAttribute('[data-wf-card="c-price"]', "aria-expanded"), "true");
  assert.equal(new URL(pg.url()).searchParams.get("stage"), "c-price", "the address keeps the stage");
  const [fg, bg] = await pg.locator('[data-wf-page="c-price"] [data-wf-open]').evaluate((el) =>
    [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]);
  assert.notEqual(fg, bg, "Open in CalibraytAI is readable (text and button differ)");
  await pg.locator("[data-wf-control-next]").click();
  assert.equal(await current(pg), "c-win");
  assert.match(await pg.textContent("[data-wf-count]"), /^4 of 6 · WIN/);
  await pg.locator("[data-wf-control-back]").click();
  assert.equal(await current(pg), "c-price");
  await pg.locator("body").click({ position: { x: 5, y: 300 } });
  await pg.keyboard.press("ArrowRight");
  assert.equal(await current(pg), "c-win", "→ moves to the next stage");
  await pg.keyboard.press("ArrowLeft");
  assert.equal(await current(pg), "c-price", "← moves back");
  // Keyboard: focus a card and press Enter
  await pg.locator('[data-wf-card="c-build"]').focus();
  await pg.keyboard.press("Enter");
  assert.equal(await current(pg), "c-build");
  assert.equal(await pg.evaluate(() => document.activeElement.id), "wf-h-c-build", "focus moves to the stage heading");
  await pg.locator('[data-wf-page="c-build"] [data-wf-next-step]').click();
  assert.equal(await current(pg), "c-close");
  assert.equal(await pg.getAttribute("[data-wf-control-next]", "aria-disabled"), "true", "Next stops at the last stage");
  await pg.reload();
  assert.equal(await current(pg), "c-close", "reloading keeps the stage");
  assert.ok((await pg.locator("[data-wf-map] a[href='/settings/people']").count()) > 0, "the owner reaches People & Access");
  await everyLinkAnswers(ben, "owner map");
  // A project: links open that project and the map shows where the job is
  await pg.selectOption("#wf-project-select", { label: facts.job });
  await Promise.all([pg.waitForNavigation(), pg.locator("[data-wf-project] button").click()]);
  assert.ok((await pg.textContent("[data-wf-project-name]")).includes(facts.job));
  const hrefs = await everyLinkAnswers(ben, "owner map with the project");
  assert.ok(hrefs.some((h) => /^\/projects\/\d+\/supplier-requests$/.test(h)), "project context kept in the links");
  await shot(pg, "workflow-contractor-project");
});

test("contractor owner on an iPhone: readable, no sideways scrolling, a tap opens the stage", async () => {
  const s = await signIn("ben-phone", "ben", PHONE);
  await s.pg.goto(`${base}/workflow`);
  await noSideways(s.pg, "contractor map (phone)");
  await s.pg.locator('[data-wf-card="c-build"]').click();
  assert.ok(await s.pg.locator('[data-wf-page="c-build"]').isVisible());
  assert.ok(await s.pg.locator("[data-wf-control-next]").isVisible(), "Back / Next stay in reach");
  const size = await s.pg.locator('[data-wf-page="c-build"] .wf-step-label').first().evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
  assert.ok(size >= 14, `readable text (${size}px)`);
  await noSideways(s.pg, "contractor stage (phone)");
  await shot(s.pg, "workflow-contractor-phone");
});

test("office staff: no owner pages, the reason instead", async () => {
  const s = await signIn("olivia", "olivia", DESK);
  await s.pg.goto(`${base}/workflow?stage=c-setup`);
  assert.equal(await s.pg.locator("[data-wf-map] a[href='/settings/people']").count(), 0);
  assert.match(await s.pg.locator('[data-wf-substep="c-setup:people"]').textContent(), /Only the owner or a System Administrator/);
  await everyLinkAnswers(s, "office map");
});

test("Cal answers where am I and what comes next from the project page", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/projects/`);
  const projectHref = await pg.locator(`a:has-text("${facts.job}")`).first().getAttribute("href");
  await pg.goto(`${base}${projectHref}`);
  await pg.click("#cal-launch");
  await pg.fill("#cal-query", "What's next?");
  await pg.locator(".cal-find-btn").click();
  await pg.waitForFunction(() => /You are in/.test(document.querySelector("#cal-results").textContent));
  const text = await pg.textContent("#cal-results");
  assert.match(text, /You are in PRICE/);
  assert.match(text, /Next: WIN/);
  await shot(pg, "workflow-cal-whats-next");
});

test("field crew on an iPhone: the Field workflow from Field, Field pages only", async () => {
  const s = await signIn("kevin", "kevin", PHONE);
  await s.pg.goto(`${base}/field/today`);
  await Promise.all([s.pg.waitForNavigation(), s.pg.click("[data-field-workflow]")]);
  assert.equal(new URL(s.pg.url()).pathname, "/field/workflow");
  await noSideways(s.pg, "Field workflow (phone)");
  const hrefs = await everyLinkAnswers(s, "Field workflow");
  for (const h of hrefs) assert.ok(/^\/(field|account\/password|training)/.test(h), `Field link ${h}`);
  await s.pg.locator("[data-wf-control-next]").click();
  assert.equal(await current(s.pg), "f-today");
  await noSideways(s.pg, "Field stage (phone)");
  await shot(s.pg, "workflow-field-phone");
  const r = await s.pg.goto(`${base}/workflow`);
  assert.equal(new URL(s.pg.url()).pathname, "/field/workflow", "the office map sends Field crew to the Field workflow");
  assert.equal(r.status(), 200);
});

test("supplier owner: the Supplier Workflow Map from the Supplier Hub, three journeys, own store only", async () => {
  const s = await signIn("darcy", "darcy", DESK);
  await s.pg.goto(`${base}/supplier/`);
  await Promise.all([s.pg.waitForNavigation(), s.pg.click("[data-supplier-workflow]")]);
  assert.equal(new URL(s.pg.url()).pathname, `/supplier/${facts.supplier_id}/workflow`);
  for (const j of ["supplier-a", "supplier-b", "supplier-c"]) assert.ok(await s.pg.locator(`[data-wf-journey-map="${j}"]`).isVisible());
  assert.equal(await current(s.pg), "sa-receive");
  await s.pg.locator('[data-wf-card="sb-order"]').click();
  assert.match(await s.pg.locator('[data-wf-substep="sb-order:pos"]').textContent(), /Not in CalibraytAI yet/);
  assert.equal(await s.pg.locator('[data-wf-substep="sb-order:pos"] a').count(), 0, "no link for what is not in CalibraytAI");
  await s.pg.locator("[data-wf-control-next]").click();
  assert.equal(await current(s.pg), "sc-setup", "Next continues into Journey C");
  const hrefs = await everyLinkAnswers(s, "supplier map");
  for (const h of hrefs) assert.ok(/^\/(supplier|training)/.test(h), `supplier link ${h}`);
  const html = await s.pg.content();
  assert.ok(!html.includes(facts.customer) && !html.includes(facts.job), "no contractor record on the supplier map");
  await shot(s.pg, "workflow-supplier-desktop");
});

test("PRO Desk staff on an iPhone: the supplier map without sideways scrolling", async () => {
  const s = await signIn("pat", "pat", PHONE);
  await s.pg.goto(`${base}/supplier/${facts.supplier_id}/workflow?stage=sb-sketch`);
  assert.equal(await current(s.pg), "sb-sketch");
  await noSideways(s.pg, "supplier map (phone)");
  await s.pg.locator("[data-wf-control-back]").click();
  assert.equal(await current(s.pg), "sb-customer");
  await everyLinkAnswers(s, "PRO Desk map");
  await shot(s.pg, "workflow-supplier-phone");
});

test("Training Centre: the map lists each stage's lessons; map -> lesson -> tick -> back keeps the tick", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/training`);
  await pg.getByLabel("Contractor owner").check();
  await Promise.all([pg.waitForNavigation(), pg.click("[data-register]")]);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-home-workflow-map]")]);
  assert.equal(new URL(pg.url()).pathname, "/training/workflow");
  await pg.locator('[data-wf-card="c-price"]').click();
  const colours = await pg.locator('[data-wf-page="c-price"] [data-wf-open]').evaluate((el) =>
    [getComputedStyle(el).color, getComputedStyle(el).backgroundColor]);
  assert.notEqual(colours[0], colours[1], "Open in CalibraytAI is readable in the Training Centre");
  const lesson = '[data-wf-page="c-price"] [data-wf-lesson="c09-new-estimate"]';
  assert.match(await pg.textContent(`${lesson} [data-wf-lesson-state]`), /steps/);
  await Promise.all([pg.waitForNavigation(), pg.locator(`${lesson} a`).click()]);
  assert.match(new URL(pg.url()).pathname, /\/training\/lessons\/c09-new-estimate$/);
  await pg.click('[data-tick="0"]');
  await pg.waitForFunction(() => document.querySelector('[data-step-card="0"]').classList.contains("is-done"));
  await Promise.all([pg.waitForNavigation(), pg.click('[data-lesson-stage="c-price"]')]);
  assert.equal(await current(pg), "c-price", "the lesson links back to its stage");
  assert.match(await pg.textContent(`${lesson} [data-wf-lesson-state]`), /^1 of \d+ steps$/, "the ticked step is kept");
  await everyLinkAnswers(sessions.ben, "training map");
  await pg.goto(`${base}/training/lessons/c09-new-estimate`);
  assert.ok(await pg.locator('[data-step-card="0"]').evaluate((c) => c.classList.contains("is-done")), "still ticked in the lesson");
  await pg.goto(`${base}/training/workflow?stage=c-price`);
  await shot(pg, "workflow-training-desktop");
  // The office map on the training site opens training for the stage
  await pg.goto(`${base}/workflow?stage=c-price`);
  await Promise.all([pg.waitForNavigation(), pg.locator('[data-wf-page="c-price"] [data-wf-training]').click()]);
  assert.equal(new URL(pg.url()).pathname, "/training/workflow");
  assert.equal(await current(pg), "c-price");
});

test("Training Centre on an iPhone: a field trainee gets the Field workflow with Field lessons", async () => {
  const s = sessions.kevin;
  await s.pg.goto(`${base}/training`);
  // Field-only crew register straight into the Field Crew training: no role to choose (22 Oct 2026).
  assert.equal(await s.pg.locator("input[name=role][type=radio]").count(), 0);
  await Promise.all([s.pg.waitForNavigation(), s.pg.click("[data-register]")]);
  await s.pg.goto(`${base}/training/workflow`);
  assert.ok(await s.pg.locator('a[href^="/training/lessons/f0"]').count() > 0, "the Field Crew lessons are on the map");
  assert.ok(await s.pg.locator('[data-wf-card="f-today"]').isVisible());
  assert.equal(await s.pg.locator('[data-wf-card="c-price"]').count(), 0);
  await noSideways(s.pg, "training map (phone)");
  await everyLinkAnswers(s, "field training map");
});
