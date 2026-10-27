// Release evidence for the Project Creation UX (27 Oct 2026), in a real browser at desktop (1280 x 900) and iPhone
// size (390 x 844, touch), against a local office built by the real migrations (tests/project_creation_page_server.py:
// owner Ben and one existing customer, Marc Bouliion, with his slab project). Synthetic data only.
//
// The Linda Bushel Production failure, walked as Joel walked it: Home → Start a New Project → no customer selected →
// New customer → Linda (no email or phone) → Save & Continue lands on "What are we building?" with Linda — never Marc,
// never the Clients pages; Back and forward keep Linda; Save & Exit and Resume from Home keep Linda; "Same as customer
// address" fills the job site; the project is created for Linda; plans (optional), role, lead (optional), review,
// finish. Then Home lists "Linda Bushel — Customer information incomplete" once; Complete information returns to
// Home and the item is gone. Also: the compact page (Step X of Y, View all steps collapsed, no permanent roadmap),
// Home's one band of guided starts above the fold and one Attention list, every page on a phone without sideways
// scrolling, no page error and no server error.
// CREATION_SHOTS=<dir> saves the screens there.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_project_creation.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const SHOTS = process.env.CREATION_SHOTS || "";
const LINDA = "Linda Bushel (synthetic)";
const MARC = "Marc Bouliion (synthetic)";
let browser, server, base, facts;
const serverErrors = [];
const sessions = {};
const S = {};

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
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`PROJECT_CREATION SERVER_ERRORS=${serverErrors.length}`);
});

let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function person(viewport) {
  const id = `ben-${viewport.width}`;
  if (sessions[id]) return sessions[id];
  const phone = viewport.width < 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  const errors = [];
  const visited = [];
  pg.on("pageerror", (e) => errors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  pg.on("framenavigated", (f) => { if (f === pg.mainFrame()) visited.push(new URL(f.url()).pathname); });
  sessions[id] = { ctx, pg, errors, visited };
  const [email, password] = facts.people.ben;
  await go(pg, "/login");
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await submit(pg, pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(pg.url(), /\/login/, "Ben signs in");
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
const stepOf = (pg) => pg.getAttribute("[data-wizard-step]", "data-wizard-step");
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}
async function shot(pg, name, full = false) {
  if (!SHOTS) return;
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: full });
}
async function flash(pg) {
  return (await pg.locator(".flash-stack, .flash").allInnerTexts().catch(() => [])).join(" | ");
}
async function selectedCustomer(pg) {
  return pg.locator("[data-customer-select]").evaluate((s) => s.options[s.selectedIndex].textContent.trim());
}
async function continueOn(pg) { await submit(pg, pg.locator("[data-wizard-next]")); }

// ------------------------------------------------------------------ Home
step("Home: one Attention list first, one band of guided starts above the fold, nothing repeated", async () => {
  const { pg, errors } = await person(DESK);
  await go(pg, "/");
  assert.equal(await pg.locator("[data-needs-attention]").count(), 1, "one Attention list");
  assert.equal(await pg.getByText("What needs attention", { exact: true }).count(), 0, "no second attention column");
  const attention = await pg.locator("[data-needs-attention]").boundingBox();
  assert.ok(attention.y < 260, `Attention comes first, right under the greeting (y=${Math.round(attention.y)})`);
  for (const key of ["NEW_PROJECT", "GUIDED_ESTIMATING", "MANAGE_PROJECT"]) {
    const start = pg.locator(`[data-start-wizard="${key}"]`);
    assert.equal(await start.count(), 1, key);
    const box = await start.boundingBox();
    assert.ok(box.y > attention.y && box.y + box.height <= DESK.height, `${key}: Start right after Attention, above the fold (y=${Math.round(box.y)})`);
    assert.equal(await pg.locator(`[data-continue-manually="${key}"]`).count(), 1, key);
  }
  const body = await pg.locator("main, body").first().innerText();
  assert.doesNotMatch(body, /\+ Start New Project|Start New Estimate/);
  await shot(pg, "home-compact-desktop");
  const phone = await person(PHONE);
  await go(phone.pg, "/");
  await noSideways(phone.pg, "home phone");
  await shot(phone.pg, "home-compact-phone");
  assert.deepEqual(errors, []);
});

// ------------------------------------------------------------------ the Linda failure, walked
step("Start a New Project: compact task page, no customer preselected", async () => {
  const { pg } = await person(DESK);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  S.run = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  assert.equal(await stepOf(pg), "customer");
  assert.match(await pg.locator(".wzc-where").innerText(), /Start a New Project · Step 1 of 7/);
  assert.equal(await pg.locator("h1.wzc-title").innerText(), "Who is the customer?");
  assert.equal(await pg.locator(".wzc-steps").isVisible(), false, "the step list is folded away");
  await pg.locator("[data-view-all-steps] summary").click();
  assert.equal(await pg.locator("[data-step-link]").count(), 7);
  await pg.locator("[data-view-all-steps] summary").click();
  assert.equal(await selectedCustomer(pg), "Choose the customer", "never the first customer in the list");
  await continueOn(pg);
  assert.match(await flash(pg), /Before you go on.*Choose the customer/);
  assert.equal(await stepOf(pg), "customer");
  await shot(pg, "wizard-customer-desktop");
});

step("New customer Linda (no email or phone): Save & Continue goes straight on with Linda, never Marc", async () => {
  const { pg, visited } = await person(DESK);
  const before = visited.length;
  await pg.locator('[data-customer-mode="new"]').check();
  assert.equal(await pg.locator('[data-customer-panel="new"]').isVisible(), true);
  await pg.fill('[name="new_customer_name"]', LINDA);
  await pg.fill('[name="new_customer_street_address"]', "12 Synthetic Lane");
  await pg.fill('[name="new_customer_city"]', "Kemptville");
  await pg.selectOption('[name="new_customer_province_state"]', "Ontario");
  await pg.fill('[name="new_customer_postal_code"]', "k0g1j0");
  await shot(pg, "wizard-new-customer-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "project_type", "automatic progression to the next task");
  assert.equal(await pg.locator("h1.wzc-title").innerText(), "What are we building?");
  assert.match(await pg.locator(".wzc-subject").innerText(), new RegExp(LINDA.replace(/[()]/g, "\\$&")));
  assert.doesNotMatch(await pg.locator(".wzc-subject").innerText(), /Marc/);
  assert.ok(!visited.slice(before).some((p) => p.startsWith("/clients")), `no Clients detour: ${visited.slice(before)}`);
  assert.match(await flash(pg), /Customer Linda Bushel \(synthetic\) added — still to add: email, phone/);
});

step("Back keeps Linda; forward keeps Linda", async () => {
  const { pg } = await person(DESK);
  await submit(pg, pg.locator("[data-wizard-back]"));
  assert.equal(await stepOf(pg), "customer");
  assert.equal(await selectedCustomer(pg), LINDA);
  await continueOn(pg);
  assert.equal(await stepOf(pg), "project_type");
  assert.match(await pg.locator(".wzc-subject").innerText(), /Linda Bushel/);
});

step("Save & Exit keeps Linda; Resume from Home keeps Linda", async () => {
  const { pg } = await person(DESK);
  await pg.fill('[name="name"]', "Bushel rear deck (synthetic)");
  await pg.locator('[name="guided_project_type"][value="OTHER"]').check();
  await submit(pg, pg.locator("[data-wizard-save-exit]"));
  assert.equal(pathOf(pg), "/");
  const line = pg.locator(`[data-resume-run="${S.run}"]`);
  assert.match(await line.innerText(), /Resume Start a New Project[\s\S]*Bushel rear deck \(synthetic\) — Linda Bushel \(synthetic\)[\s\S]*Step 2 of 7/);
  const box = await line.boundingBox();
  assert.ok(box.height <= 70, `the unfinished item is one compact line (height ${Math.round(box.height)})`);
  await shot(pg, "home-resume-desktop");
  await submit(pg, line.locator("[data-resume-wizard]"));
  assert.equal(await stepOf(pg), "project_type");
  assert.equal(await pg.inputValue('[name="name"]'), "Bushel rear deck (synthetic)");
  await shot(pg, "wizard-project-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "location");
});

step("Where is the job? Same as customer address fills the job site; Save & Continue creates Linda's project", async () => {
  const { pg } = await person(DESK);
  assert.match(await pg.locator("[data-same-as-customer-label]").innerText(), /Same as Linda Bushel \(synthetic\)'s address/);
  await pg.locator("[data-same-as-customer]").check();
  assert.equal(await pg.inputValue('[data-job="street"]'), "12 Synthetic Lane");
  assert.equal(await pg.inputValue('[data-job="municipality"]'), "Kemptville");
  assert.equal(await pg.inputValue('[data-job="postal_zip"]'), "K0G 1J0");
  await shot(pg, "wizard-location-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "documents", await flash(pg));
  assert.match(await pg.locator(".wzc-subject").innerText(), /Bushel rear deck \(synthetic\) — Linda Bushel \(synthetic\)/);
});

step("Plans are optional; role; lead optional; review shows Linda and what to add later; finish", async () => {
  const { pg } = await person(DESK);
  assert.equal(await pg.locator('input[name="plan_file"]').count(), 1);
  await shot(pg, "wizard-plans-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "role");
  await pg.locator('[name="contractor_role"][value="GENERAL_CONTRACTOR"]').check();
  await shot(pg, "wizard-role-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "responsibility", await flash(pg));
  await continueOn(pg);
  assert.equal(await stepOf(pg), "review");
  const summary = await pg.locator("[data-project-summary]").innerText();
  assert.match(summary, /Customer\s+Linda Bushel \(synthetic\)/);
  assert.match(summary, /Job site\s+12 Synthetic Lane, Kemptville, Ontario/);
  assert.doesNotMatch(summary, /Marc/);
  assert.match(await pg.locator("[data-outstanding]").innerText(), /Customer information: email, phone/);
  await shot(pg, "wizard-review-desktop");
  await submit(pg, pg.locator("[data-finish-later]"));
  assert.match(pathOf(pg), /^\/projects\/\d+$/);
  S.project = pathOf(pg);
  const head = await pg.locator(".hub-heading-identity").innerText();
  assert.match(head, /Linda Bushel \(synthetic\)/);
  assert.match(head, /Customer information incomplete — missing email, phone/);
});

step("Home lists Linda's missing information once; Complete information returns to Home and clears it", async () => {
  const { pg } = await person(DESK);
  await go(pg, "/");
  const item = pg.locator('[data-attention-kind="customers"]', { hasText: LINDA });
  assert.equal(await item.count(), 1);
  assert.match(await item.innerText(), /Linda Bushel \(synthetic\) — Customer information incomplete[\s\S]*Missing: Email, Phone/);
  await shot(pg, "home-attention-customer-desktop");
  await submit(pg, item.locator(".na-go"));
  assert.match(pathOf(pg), /^\/clients\/\d+$/);
  assert.match(await pg.locator("[data-customer-incomplete]").innerText(), /Missing: Email, Phone/);
  await pg.fill('[name="email"]', "linda.bushel@example.invalid");
  await pg.fill('[name="phone"]', "613-555-0142");
  await shot(pg, "customer-complete-desktop");
  await submit(pg, pg.locator("[data-customer-form] button[type=submit]"));
  assert.equal(pathOf(pg), "/");
  assert.equal(await pg.locator('[data-attention-kind="customers"]', { hasText: LINDA }).count(), 0);
});

// ------------------------------------------------------------------ phone
step("On a phone: every task page fits, buttons are full width, the customer form stacks", async () => {
  const { pg, errors } = await person(PHONE);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  assert.equal(await stepOf(pg), "customer");
  await noSideways(pg, "customer phone");
  await pg.locator('[data-customer-mode="new"]').check();
  await shot(pg, "wizard-customer-phone", true);
  const next = await pg.locator("[data-wizard-next]").boundingBox();
  assert.ok(next.width >= PHONE.width - 80, `Save & Continue is full width (${Math.round(next.width)}px)`);
  const name = await pg.locator('[name="new_customer_name"]').boundingBox();
  const email = await pg.locator('[name="new_customer_email"]').boundingBox();
  assert.ok(email.y > name.y + name.height - 1, "fields stack on a phone");
  await pg.fill('[name="new_customer_name"]', "Phone customer (synthetic)");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "project_type");
  await noSideways(pg, "project phone");
  await shot(pg, "wizard-project-phone", true);
  await pg.fill('[name="name"]', "Phone job (synthetic)");
  await pg.locator('[name="guided_project_type"][value="OTHER"]').check();
  await continueOn(pg);
  await noSideways(pg, "location phone");
  await shot(pg, "wizard-location-phone", true);
  await go(pg, S.project);
  await noSideways(pg, "project page phone");
  assert.deepEqual(errors, []);
  const desk = await person(DESK);
  assert.deepEqual(desk.errors, []);
  assert.deepEqual(serverErrors, []);
});
