// Release evidence for the Project Creation UX (27 Oct 2026), in a real browser at desktop (1280 x 900) and iPhone
// size (390 x 844, touch), against a local office built by the real migrations (tests/project_creation_page_server.py:
// owner Ben and one existing customer, Marc Bouliion, with his slab project). Synthetic data only.
//
// The Linda Bushel Production failure, walked as Joel walked it: Home → Start a New Project → no customer selected →
// Project → New customer → Linda (no email or phone) → Save & Continue lands on Details with Linda — never Marc,
// never the Clients pages; Back and forward keep Linda; Save & Exit and Resume from Home keep Linda; "Same as customer
// address" fills the job site; your role and the Project Lead on Details, where the project is created for Linda;
// plans (optional); review with Edit; Finish to Project Created (Compact Open a New Project, 28 Oct 2026). Then Home lists "Linda Bushel — Customer information incomplete" once; Complete information returns to
// Home and the item is gone. Also: the dialog (five numbered steps across the top, focus kept inside, × and Escape
// are Save & Exit),
// Home's one band of guided starts above the fold and one Attention list, every page on a phone without sideways
// scrolling, no page error and no server error.
// Step 4 with a real plan PDF on a desktop and a phone (Production defect, 28 Oct 2026): see below.
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
step("Start a New Project: a dialog with the five steps across the top; Project first", async () => {
  const { pg } = await person(DESK);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  S.run = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  assert.equal(await stepOf(pg), "project_type");
  assert.equal(await pg.locator('[role="dialog"][aria-modal="true"]').count(), 1);
  assert.equal(await pg.locator("#wzc-dialog-title").innerText(), "Start a New Project");
  assert.match(await pg.locator(".wzc-where").innerText(), /Step 1 of 5/);
  assert.equal(await pg.locator("h2.wzc-title").innerText(), "Project");
  assert.deepEqual(await pg.locator("[data-stepper] .wzc-step-name").allInnerTexts(), ["Project", "Customer", "Details", "Plans", "Review"]);
  assert.equal(await pg.locator("[data-stepper] [aria-current=step]").count(), 1);
  // Focus starts in the dialog and Tab stays there.
  assert.equal(await pg.evaluate(() => !!document.activeElement.closest(".wzc-modal")), true);
  for (let i = 0; i < 40; i += 1) await pg.keyboard.press("Tab");
  assert.equal(await pg.evaluate(() => !!document.activeElement.closest(".wzc-modal")), true, "Tab stays in the dialog");
  await continueOn(pg);
  assert.match(await flash(pg), /Before you go on.*Name the project/);
  assert.equal(await stepOf(pg), "project_type");
  // The message is shown inside the dialog, above the task.
  assert.equal(await pg.locator(".wzc-modal [data-wizard-flash]").isVisible(), true);
  await shot(pg, "wizard-project-desktop");
  await pg.fill('[name="name"]', "Bushel rear deck (synthetic)");
  await pg.locator('[name="guided_project_type"][value="OTHER"]').check();
  await continueOn(pg);
  assert.equal(await stepOf(pg), "customer");
  assert.equal(await selectedCustomer(pg), "Choose the customer", "never the first customer in the list");
  await continueOn(pg);
  assert.match(await flash(pg), /Before you go on.*Choose the customer/);
  assert.equal(await stepOf(pg), "customer");
  assert.equal(await pg.locator('[data-step-link="project_type"].is-done').count(), 1, "step 1 is ticked");
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
  assert.equal(await stepOf(pg), "location", "automatic progression to the next task");
  assert.equal(await pg.locator("h2.wzc-title").innerText(), "Details");
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
  assert.equal(await stepOf(pg), "location");
  assert.match(await pg.locator(".wzc-subject").innerText(), /Linda Bushel/);
});

step("Save & Exit (×) keeps everything; Resume from Home keeps Linda; Escape is the same safe close", async () => {
  const { pg } = await person(DESK);
  await pg.fill('[data-job="street"]', "typed then closed");
  await submit(pg, pg.locator("[data-modal-close]"));
  assert.equal(pathOf(pg), "/");
  const line = pg.locator(`[data-resume-run="${S.run}"]`);
  assert.match(await line.innerText(), /Resume Start a New Project[\s\S]*Bushel rear deck \(synthetic\) — Linda Bushel \(synthetic\)[\s\S]*Step 3 of 5/);
  const box = await line.boundingBox();
  assert.ok(box.height <= 70, `the unfinished item is one compact line (height ${Math.round(box.height)})`);
  await shot(pg, "home-resume-desktop");
  await submit(pg, line.locator("[data-resume-wizard]"));
  assert.equal(await stepOf(pg), "location");
  assert.equal(await pg.inputValue('[data-job="street"]'), "typed then closed");
  await pg.fill('[data-job="street"]', "");
  await pg.locator("h2.wzc-title").click();
  await Promise.all([pg.waitForNavigation(), pg.keyboard.press("Escape")]);
  assert.equal(pathOf(pg), "/", "Escape is Save & Exit");
  await submit(pg, pg.locator(`[data-resume-run="${S.run}"] [data-resume-wizard]`));
  assert.equal(await stepOf(pg), "location");
  assert.equal(await pg.inputValue('[name="name"]'), "Bushel rear deck (synthetic)");
});

step("Details: Same as customer address fills the job site; your role is required; Create Project & Continue creates it once", async () => {
  const { pg } = await person(DESK);
  assert.match(await pg.locator("[data-same-as-customer-label]").innerText(), /Same as Linda Bushel \(synthetic\)'s address/);
  await pg.locator("[data-same-as-customer]").check();
  assert.equal(await pg.inputValue('[data-job="street"]'), "12 Synthetic Lane");
  assert.equal(await pg.inputValue('[data-job="municipality"]'), "Kemptville");
  assert.equal(await pg.inputValue('[data-job="postal_zip"]'), "K0G 1J0");
  for (const name of ["permit_context_class", "pricing_posture", "execution_risk", "schedule_condition", "site_condition", "estimate_stage", "delivery_model", "contractor_role", "project_lead_user_id"]) {
    assert.equal(await pg.locator(`[name="${name}"]`).isVisible(), true, name);
  }
  // Two columns at 1280: Site information beside Project settings.
  const site = await pg.locator("#np-sec-site").boundingBox();
  const settings = await pg.locator("#np-sec-settings").boundingBox();
  assert.ok(Math.abs(site.y - settings.y) < 4 && settings.x > site.x + 200, "two columns");
  await pg.locator("[data-create-project]").click();  // held by the browser: no role yet
  assert.equal(await stepOf(pg), "location");
  assert.equal(await pg.locator("[data-contractor-role]").evaluate((el) => el.validity.valueMissing), true);
  await pg.selectOption("[data-contractor-role]", "GENERAL_CONTRACTOR");
  await shot(pg, "wizard-location-desktop");
  await submit(pg, pg.locator("[data-create-project]"));
  assert.equal(await stepOf(pg), "documents", await flash(pg));
  assert.match(await pg.locator(".wzc-subject").innerText(), /Bushel rear deck \(synthetic\) — Linda Bushel \(synthetic\)/);
});

step("Plans are optional; Review shows every section with Edit; Finish shows Project Created", async () => {
  const { pg } = await person(DESK);
  assert.equal(await pg.locator('input[name="plan_file"]').count(), 1);
  await shot(pg, "wizard-plans-desktop");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "review");
  const summary = await pg.locator("[data-project-summary]").innerText();
  assert.match(summary, /Customer\s+Linda Bushel \(synthetic\)/);
  assert.match(summary, /Job site\s+12 Synthetic Lane, Kemptville, Ontario/);
  assert.match(summary, /Your role\s+General Contractor/i);
  assert.doesNotMatch(summary, /Marc/);
  assert.equal(await pg.locator("[data-review-edit]").count(), 5);
  assert.match(await pg.locator("[data-outstanding]").innerText(), /Customer information: email, phone/);
  await shot(pg, "wizard-review-desktop");
  // Edit goes back to the step and nothing is lost.
  await submit(pg, pg.locator('[data-review-edit="project_type"]'));
  assert.equal(await stepOf(pg), "project_type");
  await go(pg, `/wizards/run/${S.run}/step/review`);
  // Finish once: the second press is held.
  let posts = 0;
  const watch = (r) => { if (r.method() === "POST") posts += 1; };
  pg.on("request", watch);
  await Promise.all([pg.waitForURL(new RegExp(`/wizards/run/${S.run}/created$`)), pg.locator("[data-finish-project]").dblclick()]);
  pg.off("request", watch);
  assert.equal(posts, 1, "Finish sent once");
  assert.match(await pg.locator("#np-created-title").innerText(), /Project Created Successfully/);
  assert.match(await pg.locator("[data-created-summary]").innerText(), /Bushel rear deck \(synthetic\)[\s\S]*Linda Bushel \(synthetic\)/);
  await shot(pg, "wizard-created-desktop");
  await submit(pg, pg.locator("[data-open-project]"));
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

// ------------------------------------------------------------------ Step 4 with a real plan PDF (Production, 28 Oct 2026)
// Joel added a plan on Step 4 and pressed Save & Continue: nothing visibly happened while the PDF uploaded, so he
// pressed again and the same PDF was sent twice. The walk above never chose a file. These steps upload a real PDF
// through the real form to the real server (the POST is only held back 2 s so the in-between state can be seen),
// then require: the pressed button says "Uploading plans…" at once, every button is held, a second press sends
// nothing, Step 5 follows, the project has the plan once; a file that is not a PDF stays on Step 4 with the reason;
// a PDF over the limit is stopped before anything is sent.
const PLAN_PDF = fs.readFileSync(path.join(REPO, "tests/fixtures/e2e/synthetic-site-plan.pdf"));
async function toPlans(pg, customer, job) {
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  const run = Number(pathOf(pg).match(/\/wizards\/run\/(\d+)/)[1]);
  await pg.fill('[name="name"]', job);
  await pg.locator('[name="guided_project_type"][value="OTHER"]').check();
  await continueOn(pg);
  assert.equal(await stepOf(pg), "customer", await flash(pg));
  await pg.locator('[data-customer-mode="new"]').check();
  await pg.fill('[name="new_customer_name"]', customer);
  await continueOn(pg);
  assert.equal(await stepOf(pg), "location", await flash(pg));
  await pg.fill('[data-job="street"]', "7 Upload Road");
  await pg.fill('[data-job="municipality"]', "Kemptville");
  await pg.selectOption("[data-contractor-role]", "GENERAL_CONTRACTOR");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "documents", await flash(pg));
  return run;
}
const exposed = new WeakSet();
async function uploadAndContinue(pg, run, label) {
  // What the page shows while the plan is on its way is read inside the page (a page with a form submission in
  // flight cannot be read from outside without racing the next page) and handed back here.
  let busy = null;
  if (!exposed.has(pg)) { await pg.exposeFunction("__planBusy", (s) => { pg.__busy = JSON.parse(s); }); exposed.add(pg); }
  pg.__busy = null;
  const posts = [];
  const watch = (r) => { if (r.method() === "POST" && /\/step\/documents$/.test(new URL(r.url()).pathname)) posts.push(r.url()); };
  pg.on("request", watch);
  await pg.route(`**/wizards/run/${run}/step/documents`, async (route) => {
    if (route.request().method() === "POST") await new Promise((res) => setTimeout(res, 2000));
    await route.continue();
  });
  await pg.setInputFiles('input[name="plan_file"]', { name: "deck-plan-synthetic.pdf", mimeType: "application/pdf", buffer: PLAN_PDF });
  await pg.evaluate(() => {
    const form = document.querySelector("form.wz-nav-form");
    form.addEventListener("submit", () => setTimeout(() => {
      const next = document.querySelector("[data-wizard-next]");
      const state = {
        formBusy: form.getAttribute("aria-busy"),
        nextText: next.textContent.trim(),
        allHeld: [...form.querySelectorAll("button[type=submit]")].every((b) => b.disabled),
        status: document.querySelector("[data-submit-status]").textContent,
        statusShown: !document.querySelector("[data-submit-status]").hidden,
      };
      // A second press, and a scripted second submit: the guard lets neither through.
      let through = 0;
      const count = (e) => { if (!e.defaultPrevented) through += 1; };
      window.addEventListener("submit", count);
      next.click();
      try { form.requestSubmit(); } catch (e) { /* a held button may refuse */ }
      window.removeEventListener("submit", count);
      state.secondSubmitsThrough = through;
      window.__planBusy(JSON.stringify(state));
    }, 50), { once: true });
  });
  const landed = pg.waitForURL(new RegExp(`/wizards/run/${run}/step/review$`), { timeout: 20000 });
  await pg.locator("[data-wizard-next]").click({ noWaitAfter: true });
  await landed;
  await pg.waitForLoadState();
  await pg.unroute(`**/wizards/run/${run}/step/documents`);
  pg.off("request", watch);
  busy = pg.__busy;
  assert.ok(busy, `${label}: the page reported its state while the plan was uploading`);
  assert.equal(busy.formBusy, "true", `${label}: the step is marked busy`);
  assert.equal(busy.nextText, "Uploading plans…", `${label}: the pressed button says what is happening`);
  assert.equal(busy.allHeld, true, `${label}: every button is held`);
  assert.equal(busy.statusShown, true);
  assert.match(busy.status, /Uploading deck-plan-synthetic\.pdf — keep this page open/);
  assert.equal(busy.secondSubmitsThrough, 0, `${label}: a second press sends nothing`);
  assert.equal(posts.length, 1, `${label}: Save & Continue sent the plan once (${posts.length} POSTs)`);
  assert.equal(await stepOf(pg), "review");
  assert.match(await flash(pg), /deck-plan-synthetic\.pdf added to the project/);
  await go(pg, `/wizards/run/${run}/step/documents`);
  assert.equal(await pg.locator("[data-step-items] li", { hasText: "deck-plan-synthetic.pdf" }).count(), 1, `${label}: one plan on the project`);
  assert.equal(await pg.getAttribute("[data-wizard-step]", "data-step-state"), "done");
}

step("Step 4 on a desktop: a real plan PDF, Save & Continue says Uploading at once, sends once, Step 5, one plan", async () => {
  const { pg } = await person(DESK);
  const run = await toPlans(pg, "Upload customer desk (synthetic)", "Upload deck desk (synthetic)");
  await uploadAndContinue(pg, run, "desktop");
  // Back to Step 4 with the same PDF chosen again and Save & Continue: still one plan, and it says so.
  await pg.setInputFiles('input[name="plan_file"]', { name: "deck-plan-synthetic.pdf", mimeType: "application/pdf", buffer: PLAN_PDF });
  await continueOn(pg);
  assert.equal(await stepOf(pg), "review");
  assert.match(await flash(pg), /already on the project \(not added again\)/);
  await go(pg, `/wizards/run/${run}/step/documents`);
  assert.equal(await pg.locator("[data-step-items] li", { hasText: "deck-plan-synthetic.pdf" }).count(), 1);
  // A PDF over the upload limit is stopped here, with the reason; nothing is sent and the buttons stay usable.
  const limit = Number(await pg.getAttribute('input[name="plan_file"]', "data-max-bytes"));
  const big = Buffer.concat([PLAN_PDF, Buffer.alloc(limit + 1024 - PLAN_PDF.length, 32)]);
  await pg.setInputFiles('input[name="plan_file"]', { name: "too-big-set.pdf", mimeType: "application/pdf", buffer: big });
  let sent = 0;
  const count = (r) => { if (r.method() === "POST") sent += 1; };
  pg.on("request", count);
  await pg.locator("[data-wizard-next]").click();
  await pg.waitForTimeout(500);
  pg.off("request", count);
  assert.equal(sent, 0, "nothing sent for a PDF over the limit");
  assert.equal(await stepOf(pg), "documents");
  assert.match(await pg.locator("[data-submit-status]").innerText(), /too-big-set\.pdf is [\d.]+ MB\. The limit is \d+ MB/);
  assert.equal(await pg.locator("[data-wizard-next]").isDisabled(), false);
  await shot(pg, "wizard-plans-too-big-desktop");
});

step("Step 4 on a phone: a real plan PDF goes up once and Step 5 follows; a file that is not a PDF stays on Step 4", async () => {
  const { pg } = await person(PHONE);
  const run = await toPlans(pg, "Upload customer phone (synthetic)", "Upload deck phone (synthetic)");
  await noSideways(pg, "plans phone");
  await uploadAndContinue(pg, run, "phone");
  await noSideways(pg, "plans phone after upload");
  await pg.setInputFiles('input[name="plan_file"]', { name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("not a pdf") });
  await continueOn(pg);
  assert.equal(await stepOf(pg), "documents", "a failed upload stays on Step 4");
  assert.match(await flash(pg), /Only PDF files are allowed/);
  assert.equal(await pg.locator("[data-wizard-next]").isDisabled(), false, "the buttons are usable again");
  await shot(pg, "wizard-plans-not-pdf-phone", true);
});

// ------------------------------------------------------------------ phone
step("On a phone: every task page fits, buttons are full width, the customer form stacks", async () => {
  const { pg, errors } = await person(PHONE);
  await go(pg, "/");
  await submit(pg, pg.locator('[data-start-wizard="NEW_PROJECT"]'));
  assert.equal(await stepOf(pg), "project_type");
  await noSideways(pg, "project phone");
  await shot(pg, "wizard-project-phone", true);
  const next = await pg.locator("[data-wizard-next]").boundingBox();
  assert.ok(next.width >= PHONE.width - 80, `Save & Continue is full width (${Math.round(next.width)}px)`);
  await pg.fill('[name="name"]', "Phone job (synthetic)");
  await pg.locator('[name="guided_project_type"][value="OTHER"]').check();
  await continueOn(pg);
  assert.equal(await stepOf(pg), "customer");
  await noSideways(pg, "customer phone");
  await pg.locator('[data-customer-mode="new"]').check();
  await shot(pg, "wizard-customer-phone", true);
  const name = await pg.locator('[name="new_customer_name"]').boundingBox();
  const email = await pg.locator('[name="new_customer_email"]').boundingBox();
  assert.ok(email.y > name.y + name.height - 1, "fields stack on a phone");
  await pg.fill('[name="new_customer_name"]', "Phone customer (synthetic)");
  await continueOn(pg);
  assert.equal(await stepOf(pg), "location");
  await noSideways(pg, "location phone");
  const site = await pg.locator("#np-sec-site").boundingBox();
  const settings = await pg.locator("#np-sec-settings").boundingBox();
  assert.ok(settings.y > site.y + site.height - 1, "the sections stack on a phone");
  await shot(pg, "wizard-location-phone", true);
  await go(pg, S.project);
  await noSideways(pg, "project page phone");
  assert.deepEqual(errors, []);
  const desk = await person(DESK);
  assert.deepEqual(desk.errors, []);
  assert.deepEqual(serverErrors, []);
});
