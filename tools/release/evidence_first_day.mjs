// Release evidence for Ben's First Day (21 Oct 2026): a brand-new synthetic contractor account walks the
// sixteen steps of the Getting started checklist (app/services/onboarding.py, Company → Getting started)
// in a real browser, through the real pages only, against a local office on a temporary database
// (tests/first_day_server.py). Synthetic data only.
//
// After each step the checklist must show that step done (steps the platform cannot see are marked with
// the page's own Mark done button), and at the end 16 of 16. Any response of 500 or more, or a page
// JavaScript error, fails the walk. Phone pages (390 x 844) must not scroll sideways.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test --test-concurrency=1 tools/release/evidence_first_day.mjs
// EVIDENCE_SHOTS=<folder> saves desktop (1280 x 900) and phone (390 x 844) screenshots for the illustrated
// manual, named <step number>-<step>-<part>-<desktop|phone>.png.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const saved = [];
const W = {}; // what the walk made, for the later steps
const CREW = [
  ["Kevin Fieldhand (synthetic)", "kevin.fieldhand@example.invalid", "Synthetic-kevin-field-1"],
  ["Tyler Fieldhand (synthetic)", "tyler.fieldhand@example.invalid", "Synthetic-tyler-field-1"],
];
const CLIENT = { name: "Pat Synthetic Homeowner", email: "pat.homeowner@example.invalid", phone: "613-555-0142",
  address: "27 Mill Pond Road, Merrickville, ON (synthetic)" };
const PROJECT = "Mill Pond Road deck (synthetic)";
const LINES = [
  ["Pressure-treated deck framing, supplied and installed (synthetic)", "1", "ls", "4200"],
  ["Composite decking, supplied and installed (synthetic)", "320", "sq ft", "11.50"],
];
const COMPANY_APPT = "Site visit at Mill Pond Road (synthetic)";
const PERSONAL_APPT = "Dentist (synthetic personal)";
const day = (offset) => new Date(Date.now() + offset * 864e5).toISOString().slice(0, 10);

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/first_day_server.py")], {
    cwd: REPO, env: { ...process.env, FIRST_DAY_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("first-day office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("first-day office exited\n" + out)); }
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
  console.log(`FIRST_DAY_SCREENS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
  for (const name of saved) console.log(`SCREEN ${name}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

// ------------------------------------------------------------------ helpers
// Each step builds on the one before: once a step fails, the later steps are skipped (not run on a broken day).
let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
const sessions = {};
async function context(viewport, opts = {}) {
  const ctx = await browser.newContext({ viewport, acceptDownloads: true, ...opts });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
}
async function go(pg, url) {
  const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`);
  await pg.waitForLoadState();
  // A set-password link carries its credential after "#": the landing page's script posts it and moves on
  // (22 Oct 2026). Wait for that second page.
  if (url.includes("/reset-password#")) await pg.waitForFunction(() => !document.querySelector("[data-reset-open]"));
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
async function signIn(s, [email, password], loginPath = "/login") {
  await go(s.pg, loginPath);
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
}
async function flash(pg) { return (await pg.locator(".flash, .alert, .field-flash, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function shot(pg, step, part) {
  const viewport = pg.viewportSize();
  const device = viewport.width <= 500 ? "phone" : "desktop";
  if (device === "phone") await noSideways(pg, `${step} ${part}`);
  const name = `${step}${part ? "-" + part : ""}-${device}.png`;
  saved.push(name);
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, name), fullPage: true });
}
function newestMail(template, to) {
  const dir = facts.mail_dir;
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.includes(template)).sort() : [];
  const bodies = files.map((f) => fs.readFileSync(path.join(dir, f), "utf8")).filter((b) => b.includes(`To: ${to}`));
  return { count: bodies.length, body: bodies.at(-1) || "" };
}
// A page from the sidebar menu: the link under its section heading (e.g. Company → Getting started).
async function menu(pg, section, href) {
  await go(pg, "/");
  const nav = pg.locator("nav.sidebar-nav .sidebar-section").filter({ has: pg.locator(".sidebar-section-label", { hasText: new RegExp(`^\\s*${section}\\s*$`) }) }).first();
  await submit(pg, nav.locator(`a.sidebar-link[href="${href}"]`));
}
// Company → Getting started, from the menu; returns {done, total, steps: {key: bool}}.
async function checklist(pg) {
  await menu(pg, "Company", "/getting-started");
  const [done, total] = (await pg.locator("[data-getting-started]").getAttribute("data-getting-started")).split("/").map(Number);
  const steps = Object.fromEntries(await pg.locator("[data-step]").evaluateAll((els) => els.map((e) => [e.dataset.step, e.dataset.done === "yes"])));
  return { done, total, steps };
}
async function expectDone(pg, key, number) {
  const c = await checklist(pg);
  assert.equal(c.total, 16);
  assert.equal(c.steps[key], true, `Getting started shows step ${number} (${key}) done`);
  await pg.locator(`#step-${key}`).scrollIntoViewIfNeeded();
  return c;
}
async function markDone(pg, key) {
  await checklist(pg);
  await submit(pg, pg.locator(`form[action="/getting-started/steps/${key}"] button`, { hasText: "Mark done" }));
  assert.equal(await pg.locator(`#step-${key}`).getAttribute("data-done"), "yes");
}
const ownerPhone = async () => {
  if (!sessions.benPhone) { sessions.benPhone = await context(PHONE, { isMobile: true, hasTouch: true }); await signIn(sessions.benPhone, facts.ben); }
  return sessions.benPhone;
};
const owner = async () => {
  if (!sessions.ben) { sessions.ben = await context(DESK); await signIn(sessions.ben, facts.ben); }
  return sessions.ben;
};
function syntheticLogo() {
  const r = spawnSync(path.join(REPO, "venv/bin/python"), ["-c",
    "import io,sys;from PIL import Image,ImageDraw;im=Image.new('RGB',(360,120),(31,78,140));d=ImageDraw.Draw(im);" +
    "d.rectangle([12,12,108,108],fill=(199,154,43));d.text((128,50),'BRAYMAN (synthetic)',fill=(255,255,255));" +
    "b=io.BytesIO();im.save(b,'PNG');sys.stdout.buffer.write(b.getvalue())"], { maxBuffer: 8 * 1024 * 1024 });
  assert.equal(r.status, 0, String(r.stderr));
  return r.stdout;
}
// Nothing a crew member may see on Field: prices, costs, totals of this job.
const COST_MARKERS = ["$", "4200", "4,200", "11.50", "9270", "9,270", "10475", "10,475", "Unit cost", "unit cost", "Markup", "markup",
  "Gross margin", "612.50", "215.00"];
function noCosts(text, label) {
  for (const m of COST_MARKERS) assert.ok(!text.includes(m), `${label}: a crew member sees "${m}"`);
}

// ================================================================== 1. Sign in
step("01 sign in: Ben signs in for the first time; the empty office and the checklist (1 of 16)", async () => {
  const s = await context(DESK);
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", facts.ben[0]);
  await shot(s.pg, "01-sign-in", "");
  await s.pg.fill("input[name=password]", facts.ben[1]);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
  sessions.ben = s;
  assert.doesNotMatch(s.pg.url(), /\/login/);
  assert.match(await s.pg.locator("main").innerText(), /Good (morning|afternoon|evening), Ben/);
  await shot(s.pg, "01-sign-in", "home");
  const c = await expectDone(s.pg, "sign_in", 1);
  // Brand new: nothing the company has to do itself is done yet (the seeded pricing policy is recorded below).
  for (const key of ["company", "accounting", "people", "phones", "calendars", "subscribe", "suppliers", "customers", "estimate",
    "proposal", "purchase_order", "crew_schedule", "hours_policy", "working_day"]) assert.equal(c.steps[key], false, `${key} not done on a new account`);
  W.financeAtStart = c.steps.finance;
  console.log(`RECORDED finance step done before Ben did anything: ${c.steps.finance} (the migrations seed the company's approved pricing policy)`);
  await shot(s.pg, "01-sign-in", "checklist");
});

// ================================================================== 2. Company
step("02 company: brand profile with logo, colours, address and phone", async () => {
  const { pg } = await owner();
  await go(pg, "/settings/brand-profile");
  let c = await checklist(pg);
  assert.equal(c.steps.company, false, "opening the brand profile page alone does not tick the step");
  await go(pg, "/settings/brand-profile");
  await pg.fill("[name=legal_name]", "Brayman Construction Inc.");
  await pg.fill("[name=customer_facing_name]", "Brayman Construction");
  await pg.fill("[name=phone]", "613-555-0100");
  await pg.fill("[name=email]", "office.first-day@example.invalid");
  await pg.fill("[name=website]", "https://example.invalid");
  await pg.fill("[name=primary_color]", "#1F4E8C");
  await pg.fill("[name=accent_color]", "#C79A2B");
  await pg.setInputFiles("[name=logo]", { name: "brayman-synthetic-logo.png", mimeType: "image/png", buffer: syntheticLogo() });
  await shot(pg, "02-company", "form");
  await submit(pg, pg.getByRole("button", { name: "Save Brand Profile" }));
  assert.match(await flash(pg), /Brand Profile saved/);
  await shot(pg, "02-company", "saved");
  await expectDone(pg, "company", 2);
});

// ================================================================== 3. Finance
step("03 finance: a gross-margin pricing policy with 13 % Ontario HST, approved and used for the company", async () => {
  const { pg } = await owner();
  await go(pg, "/pricing-engine/");
  await submit(pg, pg.getByRole("link", { name: "New pricing draft" }));
  await pg.fill("[name=policy_code]", "BEN-GM-20");
  await pg.selectOption("[name=method]", "TRUE_GROSS_MARGIN");
  await pg.fill("[name=target_gross_margin]", "0.20");
  await pg.selectOption("[name=overhead_treatment]", "INCLUDED_IN_MARGIN_ECONOMICS");
  await pg.selectOption("[name=profit_treatment]", "INCLUDED_IN_MARGIN_ECONOMICS");
  await pg.selectOption("[name=contingency_visibility]", "NOT_APPLIED");
  await pg.fill("[name=tax_jurisdiction]", "CA-ON");
  await pg.fill("[name=tax_percent]", "13");
  await pg.fill("[name=provenance]", "Ben's first-day pricing (synthetic walk)");
  await shot(pg, "03-finance", "form");
  await submit(pg, pg.getByRole("button", { name: "Create draft" }));
  assert.match(await flash(pg), /Draft pricing policy created/);
  await submit(pg, pg.getByRole("button", { name: "Approve (human)" }));
  await submit(pg, pg.getByRole("button", { name: "Use for this company" }));
  const text = await pg.locator("main").innerText();
  assert.match(text, /Company default/);
  assert.match(text, /20% of the customer price is margin/);
  assert.match(text, /13\.00/);
  await shot(pg, "03-finance", "policy");
  await expectDone(pg, "finance", 3);
});

// ================================================================== 5 + 6. People and phones
step("05 people: two crew added as Field only; each gets a set-password email", async () => {
  const { pg } = await owner();
  W.people = [];
  for (const [name, email] of CREW) {
    await menu(pg, "Company", "/settings/people");
    await submit(pg, pg.locator('main a[href="/settings/people/new"]').first());
    await pg.fill("[name=display_name]", name);
    await pg.fill("[name=email]", email);
    await pg.check("[name=field_only]");
    if (W.people.length === 0) await shot(pg, "05-people", "add");
    await submit(pg, pg.locator("main form button[type=submit]"));
    assert.match(await flash(pg), /was added/);
    assert.match(await flash(pg), /link to choose a password was emailed/);
    assert.equal(await pg.locator("[data-field-only]").getAttribute("data-field-only"), "yes");
    W.people.push({ name, email, url: pg.url() });
    assert.equal(newestMail("ACCOUNT_INVITATION", email).count, 1, `one invitation to ${email}`);
  }
  await shot(pg, "05-people", "person");
  await go(pg, "/settings/people");
  for (const [name] of CREW) assert.match(await pg.locator("main").innerText(), new RegExp(name.replace(/[()]/g, "\\$&")));
  await shot(pg, "05-people", "list");
  const phone = await ownerPhone();
  await go(phone.pg, "/settings/people");
  await shot(phone.pg, "05-people", "list");
  await expectDone(pg, "people", 5);
});

step("06 phones: Kevin opens the email link on his phone, sets his password and sees Field Today", async () => {
  const [name, email, password] = CREW[0];
  const mail = newestMail("ACCOUNT_INVITATION", email);
  assert.match(mail.body, /invited you to CalibraytAI/);
  const p = await context(PHONE, { isMobile: true, hasTouch: true });
  sessions.kevin = p;
  await go(p.pg, mail.body.match(/\/reset-password#[A-Za-z0-9_\-.]+/)[0]);
  await shot(p.pg, "06-phones", "set-password");
  await p.pg.fill("[name=password]", password);
  await p.pg.fill("[name=confirm_password]", password);
  await submit(p.pg, p.pg.locator("form button[type=submit]"));
  await shot(p.pg, "06-phones", "password-set");
  await signIn(p, [email, password]);
  assert.doesNotMatch(p.pg.url(), /\/login/, "Kevin signs in");
  await go(p.pg, "/field/today");
  assert.match(p.pg.url(), /\/field\/today$/);
  await shot(p.pg, "06-phones", "field-today");
  // Field only: no office pages.
  for (const url of ["/projects/", "/estimates/", "/settings/people", "/accounting"]) {
    const r = await p.ctx.request.get(`${base}${url}`, { maxRedirects: 0 });
    assert.ok([302, 403, 404].includes(r.status()), `Field-only Kevin is kept out of ${url} (${r.status()})`);
  }
  const { pg } = await owner();
  await go(pg, W.people[0].url);
  assert.doesNotMatch(await pg.locator("main").innerText(), /not activated|Not activated yet/i);
  await shot(pg, "06-phones", "activated");
  await markDone(pg, "phones");
  await expectDone(pg, "phones", 6);
});

// ================================================================== 7 + 8. Calendars and the feed
step("07 calendars: a company appointment and a personal appointment", async () => {
  const { pg } = await owner();
  for (const [visibility, title, type, start] of [["COMPANY", COMPANY_APPT, "SITE_VISIT", "10:00"], ["PERSONAL", PERSONAL_APPT, "GENERAL", "15:00"]]) {
    await go(pg, "/schedule");
    await submit(pg, pg.locator("a[data-new-appointment]").first());
    await pg.check(`[name=visibility][value=${visibility}]`);
    await pg.fill("[name=title]", title);
    await pg.selectOption("[name=appointment_type]", type);
    await pg.fill("[name=appointment_date]", day(1));
    await pg.fill("[name=start_time]", start);
    const [h, m] = start.split(":").map(Number);
    await pg.fill("[name=end_time]", `${String(h + 1).padStart(2, "0")}:${String(m).padStart(2, "0")}`);
    if (visibility === "COMPANY") {
      await pg.fill("[name=location]", "27 Mill Pond Road, Merrickville (synthetic)");
      await shot(pg, "07-calendars", "company-form");
    }
    await submit(pg, pg.getByRole("button", { name: "Add appointment" }));
    assert.doesNotMatch(await flash(pg), /error|could not|required/i);
  }
  await go(pg, `/schedule?year=${day(1).slice(0, 4)}&month=${Number(day(1).slice(5, 7))}&day=${Number(day(1).slice(8))}&view=day`);
  const text = await pg.locator("main").innerText();
  assert.match(text, /Site visit at Mill Pond Road/);
  assert.match(text, /Dentist \(synthetic personal\)/);
  await shot(pg, "07-calendars", "day");
  const phone = await ownerPhone();
  await go(phone.pg, `/schedule?year=${day(1).slice(0, 4)}&month=${Number(day(1).slice(5, 7))}&day=${Number(day(1).slice(8))}&view=day`);
  assert.match(await phone.pg.locator("main").innerText(), /Site visit at Mill Pond Road/);
  await shot(phone.pg, "07-calendars", "day");
  await expectDone(pg, "calendars", 7);
});

step("08 subscribe: Ben turns on his calendar feed; the .ics has both appointments", async () => {
  const s = await owner();
  const { pg } = s;
  await go(pg, "/schedule");
  await submit(pg, pg.getByRole("link", { name: /Outlook · Google · Apple Calendar/ }));
  await submit(pg, pg.getByRole("button", { name: "Turn on my calendar feed" }));
  const address = await pg.locator("#feed-https").inputValue();
  assert.match(address, /\/calendar-feed\/[^/]+\.ics$/);
  await shot(pg, "08-subscribe", "address");
  const feed = await s.ctx.request.get(`${base}${new URL(address).pathname}`);
  assert.equal(feed.status(), 200);
  const ics = await feed.text();
  assert.match(ics, /BEGIN:VCALENDAR/);
  assert.ok(ics.replace(/\r?\n[ \t]/g, "").includes(COMPANY_APPT), "the feed has the company appointment");
  assert.ok(ics.replace(/\r?\n[ \t]/g, "").includes(PERSONAL_APPT), "the feed has Ben's personal appointment");
  await expectDone(pg, "subscribe", 8);
});

// ================================================================== 9. Suppliers
step("09 suppliers: Ben adds his supplier, already on the platform with its own store sign-in", async () => {
  const { pg } = await owner();
  await menu(pg, "Company", "/suppliers");
  assert.match(await pg.locator("main").innerText(), /No supplier accounts yet/);
  // Picked from the suppliers already on CalibraytAI, by public name only (defect 4, 21 Oct 2026).
  const picker = pg.locator("[data-add-supplier] select[name=supplier_id]");
  assert.deepEqual((await picker.locator("option").allInnerTexts()).filter((t) => !t.startsWith("—")), [facts.supplier_name]);
  await picker.selectOption({ label: facts.supplier_name });
  await shot(pg, "09-suppliers", "add");
  await submit(pg, pg.locator("[data-add-supplier] button"));
  assert.match(await flash(pg), new RegExp(`${facts.supplier_name.replace(/[()]/g, "\\$&")} added`));
  const account = pg.locator(`#supplier-${facts.supplier_id}`);
  assert.equal(await account.count(), 1, "the platform supplier is the one added (no duplicate company)");
  assert.match(await account.innerText(), new RegExp(facts.store_name.replace(/[()]/g, "\\$&") + ".*can sign in"));
  await shot(pg, "09-suppliers", "added");
  await expectDone(pg, "suppliers", 9);
});

// ================================================================== 10. Customers
step("10 customers: a client, then a project with the job address", async () => {
  const { pg } = await owner();
  await go(pg, "/clients/");
  await submit(pg, pg.getByRole("link", { name: "New Client" }));
  await pg.fill("[name=name]", CLIENT.name);
  await pg.fill("[name=email]", CLIENT.email);
  await pg.fill("[name=phone]", CLIENT.phone);
  await pg.fill("[name=address]", CLIENT.address);
  await shot(pg, "10-customers", "client");
  await submit(pg, pg.getByRole("button", { name: "Save Client" }));
  assert.match(await flash(pg), /Client created/);
  await go(pg, "/");
  await submit(pg, pg.getByRole("link", { name: /Start New Project/ }).first());
  await pg.fill("[name=name]", PROJECT);
  await pg.selectOption("[name=client_id]", { label: CLIENT.name });
  await pg.selectOption("[name=status]", "Estimating");
  await pg.fill("[name=address]", CLIENT.address);
  await pg.fill("[name=street]", "27 Mill Pond Road");
  await pg.fill("[name=municipality]", "Merrickville");
  await pg.fill("[name=province_state]", "Ontario");
  await pg.fill("[name=country]", "Canada");
  await pg.selectOption("[name=permit_context_class]", "Renovation");
  await pg.selectOption("[name=project_type]", "Renovation");
  await shot(pg, "10-customers", "project");
  await submit(pg, pg.getByRole("button", { name: "Save Project" }));
  assert.match(await flash(pg), /Project created/);
  W.projectId = Number(pg.url().match(/\/projects\/(\d+)/)[1]);
  assert.match(await pg.locator("main").innerText(), /job location is complete/);
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("button", { name: "Drawings are not required" }));
  await shot(pg, "10-customers", "project-hub");
  await expectDone(pg, "customers", 10);
});

// ================================================================== 11. Estimate
step("11 estimate: lines, scope delivery, costing approved, company pricing applied", async () => {
  const { pg } = await owner();
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "New estimate" }).first());
  await pg.fill("[name=title]", "Deck rebuild (synthetic)");
  await submit(pg, pg.getByRole("button", { name: "Save Estimate" }));
  assert.match(await flash(pg), /Estimate created/);
  W.estimateId = Number(pg.url().match(/\/estimates\/(\d+)/)[1]);
  // The estimate summary (versions table) fits the 1280 px desktop: no sideways scroll (defect 3, 21 Oct 2026).
  await noSideways(pg, "11 estimate summary (desktop)");
  await submit(pg, pg.getByRole("link", { name: "View Version" }).first());
  W.versionUrl = new URL(pg.url()).pathname;
  await pg.fill("form[action$='/sections/new'] [name=name]", "Deck");
  await submit(pg, pg.locator("form[action$='/sections/new'] button[type=submit]"));
  const custom = () => pg.locator("form[action$='/items/new']").filter({ has: pg.locator("[name=unit_cost]") });
  for (const [description, quantity, unit, cost] of LINES) {
    await custom().locator("[name=description]").fill(description);
    await custom().locator("[name=quantity]").fill(quantity);
    await custom().locator("[name=unit]").fill(unit);
    await custom().locator("[name=unit_cost]").fill(cost);
    await submit(pg, custom().locator("button[type=submit]"));
  }
  assert.match(await pg.locator("main").innerText(), /SUBTOTAL\s*\$7880\.00/i);
  await shot(pg, "11-estimate", "lines");
  // Costing review asks who supplies and who builds each line first (Scope Delivery Review).
  await submit(pg, pg.getByRole("link", { name: "Open Scope Delivery Review" }));
  for (let i = 0; i < LINES.length; i++) {
    await Promise.all([pg.waitForNavigation(), pg.locator("select[name=material_procurement]").nth(i).selectOption("CONTRACTOR_PURCHASED")]);
    await Promise.all([pg.waitForNavigation(), pg.locator("select[name=labour_delivery]").nth(i).selectOption("INTERNAL")]);
  }
  await submit(pg, pg.getByRole("button", { name: "Approve All Scope Routing" }));
  assert.match(await flash(pg), /Approved scope routing for 2/);
  await shot(pg, "11-estimate", "scope-delivery");
  await go(pg, W.versionUrl);
  await submit(pg, pg.locator("form[action$='/approve-all-costing'] button"));
  assert.match(await flash(pg), /Costing approved/);
  await submit(pg, pg.locator("form[action$='/apply-org-pricing'] button"));
  assert.match(await flash(pg), /pricing policy applied/);
  const text = await pg.locator("main").innerText();
  assert.match(text, /Target gross margin: 0\.200000/);   // Ben's policy from step 3
  assert.match(text, /TAX \(13\.00%\)/);
  assert.match(text, /CUSTOMER TOTAL\s*\$11130\.50/);       // 7880 / 0.8 = 9850.00, + 13 % HST
  await shot(pg, "11-estimate", "priced");
  await go(pg, `/estimates/${W.estimateId}`);
  await noSideways(pg, "11 estimate summary, priced (desktop)");
  await go(pg, W.versionUrl);
  await expectDone(pg, "estimate", 11);
});

// ================================================================== 12. Proposal
step("12 proposal: a template, sign off, send to the client; the client accepts on a phone", async () => {
  const { pg } = await owner();
  await go(pg, W.versionUrl);
  await submit(pg, pg.locator("form[action$='/sign-off'] button"));
  if (/Create an active proposal template/.test(await flash(pg))) {
    console.log("RECORDED sign-off asks for a proposal template first; a new company has none (Proposals → Templates)");
    await shot(pg, "12-proposal", "needs-template");
    await go(pg, "/proposal-templates");
    await submit(pg, pg.locator('main a[href="/proposal-templates/new"]').first());
    await pg.fill("[name=name]", "Standard residential (synthetic)");
    await pg.fill("[name=default_intro_text]", "Thank you for the chance to quote your project.");
    await pg.fill("[name=default_payment_terms]", "30% deposit on acceptance; balance on completion.");
    await pg.check("[name=is_default]");
    await pg.check("[name=is_active]");
    await shot(pg, "12-proposal", "template");
    await submit(pg, pg.getByRole("button", { name: "Save Template" }));
    assert.match(await flash(pg), /Proposal template created/);
    await go(pg, W.versionUrl);
    await submit(pg, pg.locator("form[action$='/sign-off'] button"));
  }
  assert.match(await flash(pg), /Estimate signed off and locked/);
  W.proposalUrl = new URL(pg.url()).pathname;
  assert.match(W.proposalUrl, /^\/proposals\/\d+$/);
  await shot(pg, "12-proposal", "ready");
  const send = pg.locator("form[action$='/send-to-client']");
  assert.equal(await send.locator("[name=client_email]").inputValue(), CLIENT.email);
  await submit(pg, send.locator("button[type=submit]"));
  assert.match(await flash(pg), /Proposal sent to/);
  await shot(pg, "12-proposal", "sent");
  const mail = newestMail("PROPOSAL_INVITATION", CLIENT.email);
  assert.equal(mail.count, 1);
  const link = mail.body.match(/\/proposal\/[A-Za-z0-9_\-.]+/)[0];
  const c = await context(PHONE, { isMobile: true, hasTouch: true });
  sessions.customer = c;
  await go(c.pg, link);
  const page = await c.pg.locator("body").innerText();
  assert.match(page, /Grand Total\s*\$11130\.50/);
  for (const marker of ["4200", "4,200", "11.50", "Unit cost", "Markup"]) assert.ok(!page.includes(marker), `customer sees ${marker}`);
  await shot(c.pg, "12-proposal", "customer");
  await c.pg.check("[name=accept]");
  await c.pg.fill("[name=confirmed_name]", CLIENT.name);
  await submit(c.pg, c.pg.getByRole("button", { name: "Accept Proposal" }));
  assert.match(await c.pg.locator("body").innerText(), /Proposal accepted/);
  await shot(c.pg, "12-proposal", "accepted");
  await go(pg, W.proposalUrl);
  assert.match(await pg.locator("main").innerText(), /Accepted/);
  await expectDone(pg, "proposal", 12);
});

// ================================================================== 4. Accounting
step("04 accounting: a deposit invoice from the accepted proposal; Customers and Invoices files for QuickBooks", async () => {
  const { pg } = await owner();
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "Make an invoice" }));
  await pg.selectOption("[name=kind]", "DEPOSIT");
  await pg.fill("[name=percent]", "30");
  await shot(pg, "04-accounting", "make-invoice");
  await submit(pg, pg.getByRole("button", { name: "Make the invoice" }));
  const made = await flash(pg);
  assert.match(made, /Invoice INV-\d{4}-\d{4} made/);
  W.invoiceNumber = made.match(/INV-\d{4}-\d{4}/)[0];
  assert.match(made, /\$3,339\.15 with HST/);   // 30 % of 9,850.00 = 2,955.00, + 13 % HST
  await shot(pg, "04-accounting", "invoice");
  await menu(pg, "Company", "/accounting");
  await shot(pg, "04-accounting", "page");
  const files = {};
  for (const kind of ["customers", "invoices"]) {
    await go(pg, "/accounting");
    await submit(pg, pg.locator(`main a[href="/accounting/export/${kind}"]`).first());
    await shot(pg, "04-accounting", `${kind}-file`);
    const [download] = await Promise.all([pg.waitForEvent("download"), pg.getByRole("button", { name: /Download the file/ }).click()]);
    files[kind] = fs.readFileSync(await download.path(), "utf8");
    assert.match(download.suggestedFilename(), /\.csv$/);
  }
  assert.ok(files.customers.includes(CLIENT.name), "the Customers file has the client");
  assert.ok(files.invoices.includes(W.invoiceNumber), "the Invoices file has the invoice number");
  await go(pg, "/accounting/export/invoices");
  assert.match(await pg.locator("main").innerText(), /Nothing new/);
  await shot(pg, "04-accounting", "nothing-new");
  await expectDone(pg, "accounting", 4);
});

// ================================================================== 13. Purchase order
step("13 purchase order: concrete request to the supplier, the store quotes in the Supplier Hub, Ben orders, the store confirms", async () => {
  const { pg } = await owner();
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "Supplier requests, concrete and orders" }));
  const f = pg.locator("form[action$='/concrete-requests']");
  await f.locator("[name=volume_m3]").fill("2.5");
  await f.locator("[name=strength_mpa]").fill("32");
  await f.locator("[name=delivery_date]").fill(day(9));
  await f.locator("[name=delivery_window]").fill("7:00–9:00");
  await f.locator("[name=placement]").selectOption("Chute");
  await f.locator("[name=delivery_town]").fill("Merrickville");
  await f.locator("[name=contractor_supplier_account_id]").selectOption({ label: facts.supplier_name });
  await shot(pg, "13-purchase-order", "request");
  await submit(pg, f.locator("button[type=submit]"));
  const sent = await flash(pg);
  assert.match(sent, new RegExp(`sent to ${facts.supplier_name}`));
  const share = sent.match(/SRQ-\d{4}-\d{4}/)[0];
  // The store person, at their own desk, in the Supplier Hub.
  const store = await context(DESK);
  sessions.store = store;
  await signIn(store, facts.store, "/supplier/login");
  assert.match(await store.pg.locator("main").innerText(), new RegExp(`QUOTES TO ANSWER\\s*1`, "i"));
  await shot(store.pg, "13-purchase-order", "supplier-inbox");
  await submit(store.pg, store.pg.getByRole("link", { name: share }).first());
  const hubText = await store.pg.locator("main").innerText();
  for (const marker of ["11130", "9850", "4200", CLIENT.name, CLIENT.email]) assert.ok(!hubText.includes(marker), `the supplier sees ${marker}`);
  await store.pg.fill("[name=quote_number]", "RB-Q-1001");
  await store.pg.fill("[name=price_per_m3]", "215.00");
  await store.pg.fill("[name=short_load_charge]", "75.00");
  await store.pg.fill("[name=valid_until]", day(30));
  await shot(store.pg, "13-purchase-order", "supplier-quote");
  await submit(store.pg, store.pg.getByRole("button", { name: "Return quote" }));
  assert.match(await flash(store.pg), /Quote returned/);
  // Ben approves the quote and places the order.
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  assert.match(await pg.locator("main").innerText(), /\$612\.50 before tax/);
  await submit(pg, pg.getByRole("button", { name: "Approve this quote" }));
  assert.match(await flash(pg), /Concrete quote approved/);
  const order = pg.locator("form[action$='/order']");
  await order.locator("[name=delivery_date]").fill(day(9));
  await order.locator("[name=delivery_window]").fill("7:00–9:00");
  await order.locator("[name=site_contact]").fill("Ben Brayman (synthetic) 613-555-0100");
  await shot(pg, "13-purchase-order", "approve-and-order");
  await submit(pg, order.locator("button[type=submit]"));
  const placed = await flash(pg);
  assert.match(placed, /Purchase order PO-\d{4}-\d{4} sent/);
  W.po = placed.match(/PO-\d{4}-\d{4}/)[0];
  // The store confirms the order.
  await go(store.pg, "/supplier/");
  await submit(store.pg, store.pg.getByRole("link", { name: W.po }).first());
  await submit(store.pg, store.pg.getByRole("button", { name: "Confirm order" }));
  await shot(store.pg, "13-purchase-order", "supplier-confirmed");
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  assert.match(await pg.locator("main").innerText(), /[Cc]onfirmed/);
  await shot(pg, "13-purchase-order", "confirmed");
  await expectDone(pg, "purchase_order", 13);
});

// ================================================================== 14. Crew schedule
step("14 crew schedule: a work item, dates on the calendar, a crew with Kevin; Kevin sees it on Field and no costs", async () => {
  const { pg } = await owner();
  // A crew with Kevin (Company → Crews).
  await go(pg, "/settings/crews");
  await submit(pg, pg.locator('a[href="/settings/crews/new"]').first());
  await pg.fill("[name=name]", "Deck crew (synthetic)");
  await submit(pg, pg.locator("main form button[type=submit]"));
  assert.match(await flash(pg), /Crew saved/);
  await submit(pg, pg.getByRole("link", { name: "Deck crew (synthetic)" }));
  await pg.selectOption("[name=user_id]", { label: CREW[0][0] });
  await pg.fill('form[action$="/members"] [name=effective_from]', day(-1));
  await submit(pg, pg.locator('form[action$="/members"] button[type=submit]'));
  assert.match(await pg.locator("main").innerText(), /Kevin Fieldhand/);
  await shot(pg, "14-crew-schedule", "crew");
  // The work to schedule: a work item on the project.
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "Open project work" }));
  const element = pg.locator("form[action$='/elements']");
  await element.locator("[name=display_name]").fill("Deck framing and decking (synthetic)");
  // Added after the proposal was accepted: the office says whether it is original or extra work (defect 7).
  await element.locator("input[name=scope_origin][value=ORIGINAL]").check();
  await submit(pg, element.locator("button[type=submit]"));
  assert.match(await flash(pg), /Work item added/);
  const activity = pg.locator("form[action*='/activities']").last();
  await activity.locator("[name=display_name]").fill("Framing and decking (synthetic)");
  await activity.locator("input[name=scope_origin][value=ORIGINAL]").check();
  await submit(pg, activity.locator("button[type=submit]"));
  assert.match(await pg.locator("main").innerText(), /Framing and decking \(synthetic\)/);
  assert.match(await pg.locator("tr").filter({ hasText: "Framing and decking (synthetic)" }).first().innerText(), /Original work/);
  // Calendar → Set dates.
  await go(pg, "/schedule");
  await submit(pg, pg.getByRole("link", { name: "Set dates" }).first());
  await Promise.all([pg.waitForNavigation(), pg.selectOption("[name=project_id]", { label: PROJECT })]);
  await pg.selectOption("[name=project_work_element_id]", { label: "Deck framing and decking (synthetic)" });
  await pg.fill("[name=scheduled_start]", day(0));
  await pg.fill("[name=scheduled_end]", day(0));
  await shot(pg, "14-crew-schedule", "set-dates");
  await submit(pg, pg.getByRole("button", { name: "Set dates" }));
  assert.match(await flash(pg), /Schedule saved/);
  // The saved dates: Project dates in this period → the project → Edit dates.
  const dates = pg.locator("details[data-project-dates]");
  if ((await dates.getAttribute("open")) === null) await dates.locator("summary").first().click();
  const card = pg.locator(`details[data-project-card="${W.projectId}"]`);
  if ((await card.getAttribute("open")) === null) await card.locator("summary").click();
  await submit(pg, card.getByRole("link", { name: "Edit dates" }).first());
  await pg.selectOption("[name=crew_id]", { label: "Deck crew (synthetic)" });
  const itemUrl = new URL(pg.url()).pathname;
  await submit(pg, pg.getByRole("button", { name: "Assign" }));
  assert.match(await flash(pg), /Assignment saved/);
  await go(pg, itemUrl);
  assert.match(await pg.locator("main").innerText(), /Deck crew \(synthetic\)/);
  await shot(pg, "14-crew-schedule", "assigned");
  // Kevin, on his phone.
  const k = sessions.kevin;
  await go(k.pg, "/field/today");
  const today = await k.pg.locator("body").innerText();
  assert.match(today, /Mill Pond Road deck/);
  noCosts(today, "Field Today");
  await shot(k.pg, "14-crew-schedule", "field-today");
  await submit(k.pg, k.pg.locator(`a[href*="/field/projects/${W.projectId}"]`).first());
  noCosts(await k.pg.locator("body").innerText(), "Field job page");
  await shot(k.pg, "14-crew-schedule", "field-job");
  for (const url of [W.versionUrl, W.proposalUrl, `/accounting/projects/${W.projectId}/invoices/new`, `/projects/${W.projectId}/supplier-requests`]) {
    const r = await k.ctx.request.get(`${base}${url}`, { maxRedirects: 0 });
    assert.ok([302, 403, 404].includes(r.status()), `Kevin is kept out of ${url} (${r.status()})`);
  }
  await expectDone(pg, "crew_schedule", 14);
});

// ================================================================== 15. Hours and banked time (22 Oct 2026)
step("15 hours policy: Ben enters the company's own work-week rules (no preset values); Kevin sees the policy on Field", async () => {
  const { pg } = await owner();
  await checklist(pg);
  await submit(pg, pg.locator("#step-hours_policy").getByRole("link", { name: /Go there/ }));
  assert.match(new URL(pg.url()).pathname, /\/settings\/hours-policy$/);
  const form = pg.locator("[data-hours-policy-form]");
  for (const name of ["normal_week_hours", "extra_after_hours", "bank_rate", "effective_from"]) {
    assert.equal(await form.locator(`[name=${name}]`).inputValue(), "", `${name} starts empty`);
  }
  assert.equal(await form.locator("input[type=radio]:checked").count(), 0, "no choice is preset");
  assert.match(await pg.locator("main").innerText(), /No hours policy has been entered yet/);
  await shot(pg, "15-hours-policy", "empty");
  const monday = new Date(); monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
  const iso = `${monday.getFullYear()}-${String(monday.getMonth() + 1).padStart(2, "0")}-${String(monday.getDate()).padStart(2, "0")}`;
  await form.locator("[name=normal_week_hours]").fill("40");
  await form.locator("[name=extra_after_hours]").fill("40");
  await form.locator("input[name=extra_hours_treatment][value=BANK]").check();
  await form.locator("[name=bank_rate]").fill("1");
  await form.locator("input[name=counts_company_time][value=yes]").check();
  await form.locator("[name=week_start_day]").selectOption("0");
  await form.locator("[name=effective_from]").fill(iso);
  await shot(pg, "15-hours-policy", "filled");
  await submit(pg, pg.getByRole("button", { name: "Save hours policy" }));
  assert.match(await flash(pg), /Hours policy saved \(version 1/);
  assert.match(await pg.locator("[data-hours-policy-current]").innerText(), /Normal work week: 40\.00 hours \(Monday to Sunday\)\. Hours after 40\.00 in a week are banked/);
  await shot(pg, "15-hours-policy", "saved");
  const k = sessions.kevin;
  await go(k.pg, "/field/today");
  const today = await k.pg.locator("body").innerText();
  assert.match(today, /Banked hours[\s\S]*0\.00[\s\S]*Normal work week: 40\.00 hours/);
  noCosts(today, "Field Today with banked hours");
  await noSideways(k.pg, "Field Today with banked hours");
  await shot(k.pg, "15-hours-policy", "field-today");
  await expectDone(pg, "hours_policy", 15);
});

// ================================================================== 16. Working day
step("16 working day: Home in the morning, Kevin's Field day, then Ben marks the day done: 16 of 16", async () => {
  const { pg } = await owner();
  await go(pg, "/");
  assert.match(await pg.locator("main").innerText(), /Mill Pond Road deck/);
  await shot(pg, "16-working-day", "home");
  const phone = await ownerPhone();
  await go(phone.pg, "/");
  await shot(phone.pg, "16-working-day", "home");
  // Kevin sends his hours from Field Today.
  const k = sessions.kevin;
  await go(k.pg, "/field/today");
  await submit(k.pg, k.pg.getByRole("link", { name: "Enter time" }).first());
  const other = k.pg.locator("#field-time-other-toggle");
  if (await other.count()) await other.click();
  await k.pg.selectOption("[name=project_work_element_id]", { label: "Deck framing and decking (synthetic)" });
  const activityValue = await k.pg.locator("[name=project_work_activity_id] option", { hasText: "Framing and decking" }).first().getAttribute("value");
  await k.pg.selectOption("[name=project_work_activity_id]", activityValue);
  await k.pg.fill("[name=hours]", "8");
  await k.pg.fill("[name=worker_note]", "Ledger and joists in (synthetic)");
  await shot(k.pg, "16-working-day", "field-time");
  await submit(k.pg, k.pg.getByRole("button", { name: "Send time" }));
  assert.match(await flash(k.pg), /Time sent for approval/);
  noCosts(await k.pg.locator("body").innerText(), "Field my time");
  await shot(k.pg, "16-working-day", "time-sent");
  // Ben approves it.
  await go(pg, `/time?project_id=${W.projectId}`);
  assert.match(await pg.locator("main").innerText(), /Kevin Fieldhand/);
  await shot(pg, "16-working-day", "time-review");
  await submit(pg, pg.locator('main a[href^="/time/"]').filter({ hasText: day(0) }).first());
  await submit(pg, pg.getByRole("button", { name: "Approve", exact: true }));
  assert.match(await pg.locator("main").innerText(), /Approved/);
  await shot(pg, "16-working-day", "time-approved");
  await go(k.pg, "/field/week");
  noCosts(await k.pg.locator("body").innerText(), "Field week");
  await shot(k.pg, "16-working-day", "field-week");
  await go(pg, "/deliveries");
  assert.match(await pg.locator("main").innerText(), new RegExp(W.po));
  await shot(pg, "16-working-day", "deliveries");
  await markDone(pg, "working_day");
  const c = await checklist(pg);
  assert.equal(c.done, 16, `Getting started shows ${c.done} of 16`);
  assert.equal(await pg.locator("[data-all-done]").count(), 1);
  await shot(pg, "16-working-day", "all-done");
});
