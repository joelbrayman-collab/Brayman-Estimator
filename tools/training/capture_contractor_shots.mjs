// Screenshots for the contractor pathway of the Training & Acceptance Centre (21 Oct 2026).
//
// Starts the local training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on,
// the synthetic training company from app/training/environment.py), signs in as the training people and
// walks ONE connected job through the real pages, as the lessons in app/training/contractor.py teach it:
// Harbour Lane Pool Deck (training) for Morgan Ellis (training), BMR Winchester (training) with Darcy.
// Each picture is saved to app/static/training/shots/c<module>-<name>.png (desktop 1280 x 900, phone
// 390 x 844 for Field and phone steps), a viewport picture with the control in view, then shrunk to
// stay under ~350 KB. Synthetic data only. Any response of 500 or more, or a page JavaScript error,
// fails the walk.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium \
//      node --test --test-concurrency=1 tools/training/capture_contractor_shots.mjs
// CAPTURE_DUMP=<file> also writes the headings, buttons, links and labels of every pictured page.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "../release/evidence_common.mjs";

const SHOTS = path.join(REPO, "app/static/training/shots");
const DUMP = process.env.CAPTURE_DUMP || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const PY = path.join(REPO, "venv/bin/python");
let browser, server, base, facts;
const serverErrors = [];
const pageErrors = [];
const saved = [];
const W = {}; // what the walk made, for the later steps
const JOB = "Harbour Lane Pool Deck (training)";
const CUSTOMER = "Morgan Ellis (training)";
const SUPPLIER = "BMR Winchester (training)";
const CREW = "Pool deck crew (training)";
const WORK_ITEM = "Pool deck framing and decking (training)";
const ACTIVITY = "Framing and decking (training)";
const NEW_PERSON = ["Tyler Field (training crew)", "tyler@training.calibraytai.invalid", "Synthetic-tyler-training-1"];
const LINES = [
  ["Pool deck framing, pressure-treated, supplied and installed (training)", "1", "ls", "6800"],
  ["Composite decking, supplied and installed (training)", "420", "sq ft", "12.00"],
  ["Concrete for the equipment pad, 2.5 m³ delivered by BMR (training)", "1", "ls", "612.50"],
];
const day = (offset) => new Date(Date.now() + offset * 864e5).toISOString().slice(0, 10);
const dayUrl = (d, extra = "") => `/schedule?year=${d.slice(0, 4)}&month=${Number(d.slice(5, 7))}&day=${Number(d.slice(8))}${extra}`;

before(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  if (DUMP) fs.writeFileSync(DUMP, "");
  const port = await freePort();
  server = spawn(PY, [path.join(REPO, "tests/training_page_server.py")], {
    cwd: REPO, env: { ...process.env, TRAINING_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("training site did not start\n" + out)), 240000);
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
  await browser?.close();
  server?.kill();
  shrink();
  console.log(`CONTRACTOR_SHOTS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
  for (const name of saved) console.log(`SHOT ${name}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

// ------------------------------------------------------------------ helpers
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
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
const PASSWORD = (key) => `Synthetic-${key}-training-1`;
async function signIn(s, email, password, loginPath = "/login") {
  await go(s.pg, loginPath);
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(s.pg.url(), /\/login/, `${email} signs in`);
}
async function person(key, viewport = DESK) {
  const id = `${key}-${viewport.width}`;
  if (!sessions[id]) {
    const phone = viewport.width <= 500;
    sessions[id] = await context(viewport, phone ? { isMobile: true, hasTouch: true } : {});
    const who = facts.people[key];
    await signIn(sessions[id], who.email, PASSWORD(key), ["darcy", "pat"].includes(key) ? "/supplier/login" : "/login");
  }
  return sessions[id];
}
const ben = () => person("ben");
const olivia = () => person("olivia");
const kevinPhone = () => person("kevin", PHONE);
async function flash(pg) { return (await pg.locator(".flash, .alert, .field-flash, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
// A viewport picture; `focus` (a locator) is scrolled to the middle of the screen first.
async function shot(pg, name, focus) {
  assert.match(name, /^c\d{2}-[a-z0-9-]+$/);
  if (pg.viewportSize().width <= 500) await noSideways(pg, name);
  if (focus) {
    const el = focus.first();
    await el.waitFor({ state: "attached" });
    await el.evaluate((e) => e.scrollIntoView({ block: "center", inline: "nearest" }));
  } else {
    await pg.evaluate(() => window.scrollTo(0, 0));
  }
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`) });
  saved.push(`${name}.png`);
  if (DUMP) fs.appendFileSync(DUMP, `\n===== ${name}.png  ${pg.url().replace(base, "")}\n${await labels(pg)}\n`);
}
async function labels(pg) {
  return pg.evaluate(() => {
    const t = (e) => (e.innerText || e.value || e.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ");
    const m = document.querySelector("main") || document.body;
    const vis = (e) => e.offsetParent !== null || e.tagName === "SUMMARY";
    const out = [];
    for (const e of m.querySelectorAll("h1,h2,h3,summary,legend,.alert,button,a,label")) {
      if (!vis(e) || e.closest("[data-contextual-help], .contextual-help, .help-panel")) continue;
      const s = t(e);
      if (!s || /^\d+$/.test(s)) continue;
      out.push(`${e.tagName} ${s.slice(0, 140)}`);
    }
    return [...new Set(out)].join("\n");
  });
}
function newestMail(template, to) {
  const dir = facts.mail_dir;
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.includes(template)).sort() : [];
  const bodies = files.map((f) => fs.readFileSync(path.join(dir, f), "utf8")).filter((b) => b.includes(`To: ${to}`));
  return { count: bodies.length, body: bodies.at(-1) || "" };
}
async function menu(pg, section, href) {
  await go(pg, "/");
  const nav = pg.locator("nav.sidebar-nav .sidebar-section").filter({ has: pg.locator(".sidebar-section-label", { hasText: new RegExp(`^\\s*${section}\\s*$`) }) }).first();
  await submit(pg, nav.locator(`a.sidebar-link[href="${href}"]`));
}
async function markDone(pg, key) {
  await go(pg, "/getting-started");
  const form = pg.locator(`form[action="/getting-started/steps/${key}"] button`, { hasText: "Mark done" });
  if (await form.count()) await submit(pg, form);
  assert.equal(await pg.locator(`#step-${key}`).getAttribute("data-done"), "yes");
}
function python(code, args = []) {
  const r = spawnSync(PY, ["-c", code, ...args], { maxBuffer: 16 * 1024 * 1024 });
  assert.equal(r.status, 0, String(r.stderr));
  return r.stdout;
}
function syntheticPlanPdf() {
  return python("import io,sys;from PIL import Image,ImageDraw;im=Image.new('RGB',(1650,1275),'white');d=ImageDraw.Draw(im);" +
    "d.rectangle([150,200,1250,900],outline='black',width=6);d.rectangle([400,350,1000,700],outline=(30,90,160),width=4);" +
    "d.text((420,520),'POOL (existing)',fill=(30,90,160));d.text((160,960),'HARBOUR LANE POOL DECK - DECK PLAN (TRAINING, SYNTHETIC)',fill='black');" +
    "d.text((160,1000),'14 Harbour Lane, Merrickville ON - Morgan Ellis (training) - Scale 1/4 in = 1 ft',fill='black');" +
    "d.rectangle([1300,950,1600,1200],outline='black',width=3);d.text((1310,960),'Brayman Construction (training)',fill='black');" +
    "b=io.BytesIO();im.save(b,'PDF',resolution=150);sys.stdout.buffer.write(b.getvalue())");
}
function syntheticPhoto() {
  return python("import io,sys;from PIL import Image,ImageDraw;im=Image.new('RGB',(1200,900),(120,150,170));d=ImageDraw.Draw(im);" +
    "[d.rectangle([60+i*70,500,110+i*70,860],fill=(150,110,70)) for i in range(15)];d.rectangle([0,0,1200,300],fill=(170,200,230));" +
    "d.text((40,40),'Harbour Lane Pool Deck - joists in (training photo, synthetic)',fill='black');" +
    "b=io.BytesIO();im.save(b,'JPEG',quality=80);sys.stdout.buffer.write(b.getvalue())");
}
// Keep every picture under ~350 KB: PNG with an adaptive palette when the full-colour file is too big.
function shrink() {
  if (!saved.length) return;
  const r = spawnSync(PY, ["-c",
    "import os,sys\nfrom PIL import Image\nroot=sys.argv[1]\nfor n in sys.argv[2:]:\n p=os.path.join(root,n)\n" +
    " if os.path.getsize(p)<=330000: continue\n im=Image.open(p).convert('RGB')\n" +
    " im.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).save(p,optimize=True)\n" +
    " if os.path.getsize(p)>330000:\n  w,h=im.size;im.resize((int(w*0.8),int(h*0.8)),Image.LANCZOS).quantize(colors=128).save(p,optimize=True)\n",
    SHOTS, ...new Set(saved)]);
  if (r.status !== 0) console.log(String(r.stderr));
}

// ================================================================== Module 1: welcome, registration, sign-in
step("c01: the training centre, signing in, Home and the password page", async () => {
  const s = await context(DESK);
  sessions.anon = s;
  await go(s.pg, "/training/signin");
  await shot(s.pg, "c01-training-signin", s.pg.locator("[data-signin=contractor]"));
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", facts.people.ben.email);
  await shot(s.pg, "c01-sign-in", s.pg.locator("form button[type=submit]"));
  await go(s.pg, "/forgot-password");
  await shot(s.pg, "c01-forgot-password");
  const { pg } = await ben();
  await go(pg, "/");
  assert.match(await pg.locator("main").innerText(), /Good (morning|afternoon|evening), Ben/);
  await shot(pg, "c01-home");
  await shot(pg, "c01-key-button", pg.locator('header a[href="/account/password"]'));
  await go(pg, "/account/password");
  await shot(pg, "c01-change-password", pg.locator("main form button[type=submit]"));
  await go(pg, "/training");
  assert.match(await pg.locator("main, body").first().innerText(), /Start my training/);
  await shot(pg, "c01-register", pg.locator("[data-register]"));
  await pg.check("input[name=role][value=OWNER]");
  await submit(pg, pg.locator("[data-register]"));
  await shot(pg, "c01-training-home");
  const o = await olivia();
  await go(o.pg, "/");
  await shot(o.pg, "c01-office-home");
  const k = await kevinPhone();
  assert.match(k.pg.url(), /\/field\/today/);
  await shot(k.pg, "c01-field-today");
  await go(k.pg, "/training");
  await shot(k.pg, "c01-field-register", k.pg.locator("[data-register]"));
  await k.pg.check("input[name=role][value=FIELD]");
  await submit(k.pg, k.pg.locator("[data-register]"));
  const ph = await context(PHONE, { isMobile: true, hasTouch: true });
  sessions.anonPhone = ph;
  await go(ph.pg, "/login");
  await ph.pg.fill("input[name=email]", facts.people.kevin.email);
  await shot(ph.pg, "c01-field-sign-in", ph.pg.locator("form button[type=submit]"));
});

// ================================================================== Module 2: company, users, permissions
step("c02: Getting started, brand profile and the pricing policy with 13 % HST", async () => {
  const { pg } = await ben();
  await menu(pg, "Company", "/getting-started");
  await shot(pg, "c02-getting-started");
  await shot(pg, "c02-getting-started-steps", pg.locator("#step-people"));
  await go(pg, "/settings/brand-profile");
  await pg.fill("[name=legal_name]", "Brayman Construction (training)");
  await pg.fill("[name=customer_facing_name]", "Brayman Construction (training)");
  await pg.fill("[name=phone]", "613-555-0100");
  await pg.fill("[name=email]", "office@training.calibraytai.invalid");
  await pg.fill("[name=address]", "1 Training Road, Merrickville, ON (training)");
  await pg.fill("[name=primary_color]", "#1F4E8C");
  await pg.fill("[name=accent_color]", "#C79A2B");
  await shot(pg, "c02-brand-profile", pg.locator("[name=phone]"));
  await submit(pg, pg.getByRole("button", { name: "Save Brand Profile" }));
  assert.match(await flash(pg), /Brand Profile saved/);
  await shot(pg, "c02-brand-saved");
  await menu(pg, "Costs & pricing", "/pricing-engine/");
  await shot(pg, "c02-how-we-price");
  await submit(pg, pg.getByRole("link", { name: "New pricing draft" }));
  await pg.fill("[name=policy_code]", "HARBOUR-GM-20");
  await pg.selectOption("[name=method]", "TRUE_GROSS_MARGIN");
  await pg.fill("[name=target_gross_margin]", "0.20");
  await pg.selectOption("[name=overhead_treatment]", "INCLUDED_IN_MARGIN_ECONOMICS");
  await pg.selectOption("[name=profit_treatment]", "INCLUDED_IN_MARGIN_ECONOMICS");
  await pg.selectOption("[name=contingency_visibility]", "NOT_APPLIED");
  await pg.fill("[name=tax_jurisdiction]", "CA-ON");
  await pg.fill("[name=tax_percent]", "13");
  await pg.fill("[name=provenance]", "Training: 20 % gross margin, Ontario HST");
  await shot(pg, "c02-pricing-draft", pg.locator("[name=tax_percent]"));
  await submit(pg, pg.getByRole("button", { name: "Create draft" }));
  assert.match(await flash(pg), /Draft pricing policy created/);
  await shot(pg, "c02-pricing-approve", pg.getByRole("button", { name: "Approve (human)" }));
  await submit(pg, pg.getByRole("button", { name: "Approve (human)" }));
  await shot(pg, "c02-pricing-use", pg.getByRole("button", { name: "Use for this company" }));
  await submit(pg, pg.getByRole("button", { name: "Use for this company" }));
  const text = await pg.locator("main").innerText();
  assert.match(text, /Company default/);
  assert.match(text, /20% of the customer price is margin/);
  await shot(pg, "c02-pricing-default");
});

step("c02: People & Access: add a Field-only person, the access controls, Crews", async () => {
  const { pg } = await ben();
  await menu(pg, "Company", "/settings/people");
  await shot(pg, "c02-people-list");
  await submit(pg, pg.locator('main a[href="/settings/people/new"]').first());
  await pg.fill("[name=display_name]", NEW_PERSON[0]);
  await pg.fill("[name=email]", NEW_PERSON[1]);
  await pg.check("[name=field_only]");
  await shot(pg, "c02-people-add", pg.locator("main form button[type=submit]"));
  await submit(pg, pg.locator("main form button[type=submit]"));
  assert.match(await flash(pg), /was added/);
  W.tylerUrl = new URL(pg.url()).pathname;
  await shot(pg, "c02-people-added");
  // Olivia's record: Field only, access areas, System Administrator, deactivate.
  await go(pg, "/settings/people");
  await submit(pg, pg.locator("main a", { hasText: "Olivia Office" }).first());
  W.oliviaUrl = new URL(pg.url()).pathname;
  await shot(pg, "c02-people-detail");
  await shot(pg, "c02-people-access", pg.locator(`form[action$="/access"]`));
  // Office staff do not see People & Access.
  const o = await olivia();
  await go(o.pg, "/");
  assert.equal(await o.pg.locator('nav a[href="/settings/people"]').count(), 0, "office staff are not offered People & Access");
  // Crews.
  await menu(pg, "Company", "/settings/crews");
  await shot(pg, "c02-crews");
  await submit(pg, pg.locator('a[href="/settings/crews/new"]').first());
  await pg.fill("[name=name]", CREW);
  await shot(pg, "c02-crew-add", pg.locator("main form button[type=submit]"));
  await submit(pg, pg.locator("main form button[type=submit]"));
  assert.match(await flash(pg), /Crew saved/);
  await submit(pg, pg.getByRole("link", { name: CREW }));
  W.crewUrl = new URL(pg.url()).pathname;
  for (const who of ["Kevin Field (training crew)", "Liam Field (training crew)"]) {
    await pg.selectOption("[name=user_id]", { label: who });
    await pg.fill('form[action$="/members"] [name=effective_from]', day(-1));
    if (who.startsWith("Kevin")) await shot(pg, "c02-crew-member", pg.locator('form[action$="/members"]'));
    await submit(pg, pg.locator('form[action$="/members"] button[type=submit]'));
  }
  const crew = await pg.locator("main").innerText();
  assert.match(crew, /Kevin Field/);
  assert.match(crew, /Liam Field/);
});

// ================================================================== Module 3: workers and iPhones
step("c03: Tyler opens the invitation on his phone, chooses a password and sees Field; Ben checks and marks phones done", async () => {
  const { pg } = await ben();
  await go(pg, W.tylerUrl);
  await shot(pg, "c03-send-link", pg.getByRole("button", { name: "Email a link to choose a password" }));
  const mail = newestMail("ACCOUNT_INVITATION", NEW_PERSON[1]);
  assert.equal(mail.count, 1, "one invitation to Tyler");
  const p = await context(PHONE, { isMobile: true, hasTouch: true });
  sessions.tyler = p;
  await go(p.pg, mail.body.match(/\/reset-password\/[A-Za-z0-9_\-.]+/)[0]);
  await p.pg.fill("[name=password]", NEW_PERSON[2]);
  await p.pg.fill("[name=confirm_password]", NEW_PERSON[2]);
  await shot(p.pg, "c03-set-password", p.pg.locator("form button[type=submit]"));
  await submit(p.pg, p.pg.locator("form button[type=submit]"));
  await shot(p.pg, "c03-password-set");
  await signIn(p, NEW_PERSON[1], NEW_PERSON[2]);
  await go(p.pg, "/field/today");
  await shot(p.pg, "c03-field-today");
  await go(p.pg, "/field/week");
  await shot(p.pg, "c03-field-week");
  for (const url of ["/projects/", "/settings/people", "/accounting", "/estimates/"]) {
    const r = await p.ctx.request.get(`${base}${url}`, { maxRedirects: 0 });
    assert.ok([302, 403, 404].includes(r.status()), `Field-only Tyler is kept out of ${url} (${r.status()})`);
  }
  await go(pg, W.tylerUrl);
  await shot(pg, "c03-activated");
  await go(pg, "/getting-started");
  await shot(pg, "c03-mark-phones", pg.locator("#step-phones"));
  await markDone(pg, "phones");
});

// ================================================================== Module 5: calendars
step("c05: My Calendar, Company Calendar, a company site visit and a personal appointment, the calendar feed", async () => {
  const { pg } = await ben();
  await go(pg, "/schedule");
  await shot(pg, "c05-calendar");
  await shot(pg, "c05-my-company-switch", pg.getByRole("link", { name: "Company Calendar" }).first());
  for (const [visibility, title, type, start, shotName] of [
    ["COMPANY", "Site visit: Harbour Lane Pool Deck (training)", "SITE_VISIT", "10:00", "c05-appointment-company"],
    ["PERSONAL", "Truck service (training, personal)", "GENERAL", "15:00", ""]]) {
    await go(pg, "/schedule");
    await submit(pg, pg.locator("a[data-new-appointment]").first());
    await pg.check(`[name=visibility][value=${visibility}]`);
    await pg.fill("[name=title]", title);
    await pg.selectOption("[name=appointment_type]", type);
    await pg.fill("[name=appointment_date]", day(1));
    await pg.fill("[name=start_time]", start);
    await pg.fill("[name=end_time]", `${String(Number(start.slice(0, 2)) + 1).padStart(2, "0")}:00`);
    if (visibility === "COMPANY") {
      await pg.fill("[name=location]", "14 Harbour Lane, Merrickville, ON");
      await pg.selectOption("[name=assigned_user_id]", { label: "Ben Brayman (training)" });
      await pg.selectOption("[name=client_id]", { label: CUSTOMER });
      await pg.selectOption("[name=project_id]", { label: JOB });
      await shot(pg, "c05-appointment-form");
    }
    if (shotName) await shot(pg, shotName, pg.getByRole("button", { name: "Add appointment" }));
    await submit(pg, pg.getByRole("button", { name: "Add appointment" }));
    assert.doesNotMatch(await flash(pg), /error|could not|required/i);
  }
  await go(pg, dayUrl(day(1), "&view=day"));
  const text = await pg.locator("main").innerText();
  assert.match(text, /Site visit: Harbour Lane/);
  assert.match(text, /Truck service/);
  await shot(pg, "c05-day");
  await go(pg, dayUrl(day(1), "&view=week"));
  await shot(pg, "c05-week");
  // Olivia sees the company appointment, not Ben's personal one.
  const o = await olivia();
  await go(o.pg, dayUrl(day(1), "&view=day&scope=company"));
  const otext = await o.pg.locator("main").innerText();
  assert.match(otext, /Site visit: Harbour Lane/);
  assert.doesNotMatch(otext, /Truck service/);
  const phone = await person("ben", PHONE);
  await go(phone.pg, dayUrl(day(1), "&view=day"));
  // The feed.
  await go(pg, "/schedule");
  await submit(pg, pg.getByRole("link", { name: /Outlook · Google · Apple Calendar/ }));
  await shot(pg, "c05-feed-off", pg.getByRole("button", { name: "Turn on my calendar feed" }));
  await submit(pg, pg.getByRole("button", { name: "Turn on my calendar feed" }));
  const address = await pg.locator("#feed-https").inputValue();
  assert.match(address, /\/calendar-feed\/[^/]+\.ics$/);
  await shot(pg, "c05-feed-address", pg.locator("#feed-https"));
  await shot(pg, "c05-feed-instructions", pg.getByRole("button", { name: "Make a new address" }));
  const ics = (await (await pg.context().request.get(`${base}${new URL(address).pathname}`)).text()).replace(/\r?\n[ \t]/g, "");
  assert.ok(ics.includes("Site visit: Harbour Lane Pool Deck (training)"));
});

// ================================================================== Module 6: customers and projects
step("c06: Clients, Morgan Ellis, the Harbour Lane project hub, setup, location and an existing job", async () => {
  const { pg } = await ben();
  await go(pg, "/clients/");
  await shot(pg, "c06-clients");
  await submit(pg, pg.getByRole("link", { name: "New Client" }));
  await shot(pg, "c06-client-new", pg.getByRole("button", { name: "Save Client" }));
  await go(pg, "/clients/");
  await submit(pg, pg.getByRole("link", { name: CUSTOMER }).first());
  await pg.fill("[name=notes]", "Pool deck around the existing in-ground pool. Prefers email. (training)");
  await shot(pg, "c06-client-edit", pg.getByRole("button", { name: "Save Client" }));
  await submit(pg, pg.getByRole("button", { name: "Save Client" }));
  await go(pg, "/projects/");
  await shot(pg, "c06-projects");
  await submit(pg, pg.locator("main a", { hasText: JOB }).first());
  W.projectId = Number(pg.url().match(/\/projects\/(\d+)/)[1]);
  await shot(pg, "c06-project-hub");
  await submit(pg, pg.getByRole("link", { name: "Continue setup" }).first());
  await shot(pg, "c06-project-setup");
  await go(pg, `/projects/${W.projectId}/location/edit`);
  for (const [name, value] of [["street", "14 Harbour Lane"], ["municipality", "Merrickville"], ["province_state", "Ontario"], ["country", "Canada"]]) {
    const f = pg.locator(`[name=${name}]`);
    if (await f.count()) await f.fill(value);
  }
  await shot(pg, "c06-location", pg.locator("main form button[type=submit]").last());
  await submit(pg, pg.locator("main form button[type=submit]").last());
  await go(pg, `/projects/${W.projectId}/setup`);
  await go(pg, "/projects/new");
  await pg.fill("[name=name]", "Ellis Front Steps (training, existing job)");
  await pg.selectOption("[name=client_id]", { label: CUSTOMER });
  await pg.selectOption("[name=status]", "Active");
  await shot(pg, "c06-project-new");
  await shot(pg, "c06-project-gate", pg.getByRole("button", { name: "Save Project" }));
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c06-project-tabs", pg.locator('a[href="#hub-identity"]'));
});

// ================================================================== Module 7: drawings, calculators, takeoffs
step("c07: the plan PDF on the project, the concrete calculator, Deck Takeoff and Construction Drawings", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c07-hub-drawings", pg.getByRole("button", { name: "Drawings are required" }));
  await submit(pg, pg.getByRole("button", { name: "Drawings are required" }));
  await go(pg, `/projects/${W.projectId}/plans`);
  await shot(pg, "c07-drawings");
  await submit(pg, pg.locator('main a[href$="/plans/upload"]').first());
  await pg.setInputFiles("[name=plan_file]", { name: "harbour-lane-deck-plan-training.pdf", mimeType: "application/pdf", buffer: syntheticPlanPdf() });
  await pg.fill("[name=notes]", "Deck plan from Morgan Ellis (training)");
  await shot(pg, "c07-upload", pg.getByRole("button", { name: "Upload" }));
  await submit(pg, pg.getByRole("button", { name: "Upload" }));
  assert.doesNotMatch(await flash(pg), /error|could not/i);
  await go(pg, `/projects/${W.projectId}/plans`);
  assert.match(await pg.locator("main").innerText(), /harbour-lane-deck-plan-training/);
  await shot(pg, "c07-plan-listed", pg.locator("main", { hasText: "harbour-lane-deck-plan-training" }).locator("a", { hasText: /harbour-lane-deck-plan-training/ }));
  // The concrete calculator (Calculators → Concrete calculator).
  await go(pg, "/calculators/concrete");
  await pg.selectOption("#variant", "standard");
  await pg.selectOption("#measurement_system", "imperial");
  await pg.fill("#length", "12");
  await pg.fill("#width", "10");
  await pg.fill("#slab_thickness", "6");
  await pg.fill("#waste_percent", "5");
  await shot(pg, "c07-concrete-calculator", pg.getByRole("button", { name: "Calculate" }));
  await pg.getByRole("button", { name: "Calculate" }).click();
  await pg.locator("[data-concrete-result]").waitFor({ state: "visible" });
  W.concreteResult = await pg.locator("[data-concrete-result]").innerText();
  console.log("RECORDED concrete calculator result:\n" + W.concreteResult);
  await shot(pg, "c07-concrete-result", pg.locator("[data-concrete-result]"));
  await go(pg, `/projects/${W.projectId}/deck-takeoff`);
  await shot(pg, "c07-deck-takeoff");
  await shot(pg, "c07-deck-product-facts", pg.getByRole("button", { name: "Save product facts" }));
  await go(pg, `/projects/${W.projectId}/drawings`);
  await shot(pg, "c07-construction-drawings");
  await go(pg, `/projects/${W.projectId}/setup`);
});

// ================================================================== Module 8: suppliers, quotes (the order is placed after acceptance)
step("c08: Suppliers, a concrete request to BMR, Darcy quotes in the Supplier Hub, Ben approves the quote", async () => {
  const { pg } = await ben();
  await menu(pg, "Company", "/suppliers");
  await shot(pg, "c08-suppliers");
  await shot(pg, "c08-supplier-signins", pg.getByRole("button", { name: "Give Supplier Hub sign-in" }));
  await shot(pg, "c08-add-supplier", pg.getByRole("button", { name: "Add supplier" }));
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c08-hub-purchasing", pg.getByRole("link", { name: "Supplier requests, concrete and orders" }));
  await submit(pg, pg.getByRole("link", { name: "Supplier requests, concrete and orders" }));
  const f = pg.locator("form[action$='/concrete-requests']");
  await f.locator("[name=volume_m3]").fill("2.5");
  await f.locator("[name=strength_mpa]").fill("32");
  await f.locator("[name=exposure_class]").fill("C-2");
  await f.locator("[name=delivery_date]").fill(day(0));
  await f.locator("[name=delivery_window]").fill("7:00–9:00");
  await f.locator("[name=placement]").selectOption("Chute");
  await f.locator("[name=delivery_town]").fill("Merrickville");
  await f.locator("[name=notes]").fill("Equipment pad beside the pool deck (training)");
  await f.locator("[name=contractor_supplier_account_id]").selectOption({ label: SUPPLIER });
  await shot(pg, "c08-concrete-request", f.locator("button[type=submit]"));
  await submit(pg, f.locator("button[type=submit]"));
  const sent = await flash(pg);
  assert.match(sent, new RegExp(`sent to ${SUPPLIER.replace(/[()]/g, "\\$&")}`));
  W.share = sent.match(/SRQ-\d{4}-\d{4}/)[0];
  await shot(pg, "c08-request-sent");
  // Darcy, at the store, in the Supplier Hub.
  const store = await person("darcy");
  await go(store.pg, "/supplier/");
  await shot(store.pg, "c08-supplier-inbox");
  await submit(store.pg, store.pg.getByRole("link", { name: W.share }).first());
  const hub = await store.pg.locator("main").innerText();
  for (const m of [CUSTOMER, "morgan.ellis"]) assert.ok(!hub.includes(m), `the supplier sees ${m}`);
  await store.pg.fill("[name=quote_number]", "BMR-Q-2026-0142");
  await store.pg.fill("[name=price_per_m3]", "215.00");
  await store.pg.fill("[name=short_load_charge]", "75.00");
  await store.pg.fill("[name=valid_until]", day(30));
  await shot(store.pg, "c08-supplier-quote", store.pg.getByRole("button", { name: "Return quote" }));
  await submit(store.pg, store.pg.getByRole("button", { name: "Return quote" }));
  assert.match(await flash(store.pg), /Quote returned/);
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  assert.match(await pg.locator("main").innerText(), /\$612\.50 before tax/);
  await shot(pg, "c08-quote-returned", pg.getByRole("button", { name: "Approve this quote" }));
  await submit(pg, pg.getByRole("button", { name: "Approve this quote" }));
  assert.match(await flash(pg), /Concrete quote approved/);
  await shot(pg, "c08-quote-approved", pg.locator("form[action$='/order']"));
});

// ================================================================== Module 9: estimate, costing, pricing
step("c09: the estimate, lines, Scope Delivery Review, costing approved, the company pricing applied", async () => {
  const { pg } = await ben();
  await menu(pg, "Costs & pricing", "/cost-library/");
  await shot(pg, "c09-what-we-pay");
  await go(pg, "/assemblies/");
  await shot(pg, "c09-reusable-work");
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c09-hub-estimates", pg.getByRole("link", { name: "New estimate" }).first());
  await submit(pg, pg.getByRole("link", { name: "New estimate" }).first());
  await pg.fill("[name=title]", "Pool deck and equipment pad (training)");
  await shot(pg, "c09-estimate-new", pg.getByRole("button", { name: "Save Estimate" }));
  await submit(pg, pg.getByRole("button", { name: "Save Estimate" }));
  assert.match(await flash(pg), /Estimate created/);
  W.estimateId = Number(pg.url().match(/\/estimates\/(\d+)/)[1]);
  await shot(pg, "c09-estimate", pg.getByRole("link", { name: "View Version" }).first());
  await submit(pg, pg.getByRole("link", { name: "View Version" }).first());
  W.versionUrl = new URL(pg.url()).pathname;
  await pg.fill("form[action$='/sections/new'] [name=name]", "Pool deck");
  await shot(pg, "c09-section", pg.locator("form[action$='/sections/new'] button[type=submit]"));
  await submit(pg, pg.locator("form[action$='/sections/new'] button[type=submit]"));
  const custom = () => pg.locator("form[action$='/items/new']").filter({ has: pg.locator("[name=unit_cost]") });
  for (const [i, [description, quantity, unit, cost]] of LINES.entries()) {
    await custom().locator("[name=description]").fill(description);
    await custom().locator("[name=quantity]").fill(quantity);
    await custom().locator("[name=unit]").fill(unit);
    await custom().locator("[name=unit_cost]").fill(cost);
    if (i === 0) await shot(pg, "c09-line", custom().locator("button[type=submit]"));
    await submit(pg, custom().locator("button[type=submit]"));
  }
  const lines = await pg.locator("main").innerText();
  W.subtotal = (lines.match(/SUBTOTAL\s*\$([\d,.]+)/i) || [])[1];
  console.log(`RECORDED estimate subtotal ${W.subtotal}`);
  await shot(pg, "c09-lines", pg.getByRole("link", { name: "Open Scope Delivery Review" }));
  await submit(pg, pg.getByRole("link", { name: "Open Scope Delivery Review" }));
  for (let i = 0; i < LINES.length; i++) {
    await Promise.all([pg.waitForNavigation(), pg.locator("select[name=material_procurement]").nth(i).selectOption("CONTRACTOR_PURCHASED")]);
    await Promise.all([pg.waitForNavigation(), pg.locator("select[name=labour_delivery]").nth(i).selectOption("INTERNAL")]);
  }
  await shot(pg, "c09-scope-delivery", pg.getByRole("button", { name: "Approve All Scope Routing" }));
  await submit(pg, pg.getByRole("button", { name: "Approve All Scope Routing" }));
  assert.match(await flash(pg), /Approved scope routing for 3/);
  await go(pg, W.versionUrl);
  await shot(pg, "c09-approve-costing", pg.locator("form[action$='/approve-all-costing'] button"));
  await submit(pg, pg.locator("form[action$='/approve-all-costing'] button"));
  assert.match(await flash(pg), /Costing approved/);
  await shot(pg, "c09-apply-pricing", pg.locator("form[action$='/apply-org-pricing'] button"));
  await submit(pg, pg.locator("form[action$='/apply-org-pricing'] button"));
  assert.match(await flash(pg), /pricing policy applied/);
  const text = await pg.locator("main").innerText();
  assert.match(text, /Target gross margin: 0\.200000/);
  assert.match(text, /TAX \(13\.00%\)/);
  W.customerTotal = (text.match(/CUSTOMER TOTAL\s*\$([\d,.]+)/) || [])[1];
  console.log(`RECORDED customer total ${W.customerTotal}`);
  await shot(pg, "c09-priced", pg.locator("main").getByText(/customer total/i).last());
});

// ================================================================== Module 10: proposal, acceptance, contract
step("c10: a proposal template, sign off, send to Morgan, Morgan accepts on her phone, the contract", async () => {
  const { pg } = await ben();
  await go(pg, "/proposal-templates");
  await shot(pg, "c10-templates");
  await submit(pg, pg.locator('main a[href="/proposal-templates/new"]').first());
  await pg.fill("[name=name]", "Pool decks (training)");
  await pg.fill("[name=default_intro_text]", "Thank you for asking Brayman Construction to quote your pool deck.");
  await pg.fill("[name=default_payment_terms]", "30% deposit on acceptance; balance on completion.");
  await pg.check("[name=is_default]");
  await pg.check("[name=is_active]");
  await shot(pg, "c10-template-new", pg.getByRole("button", { name: "Save Template" }));
  await submit(pg, pg.getByRole("button", { name: "Save Template" }));
  assert.match(await flash(pg), /Proposal template created/);
  await go(pg, W.versionUrl);
  await shot(pg, "c10-sign-off", pg.locator("form[action$='/sign-off'] button"));
  await submit(pg, pg.locator("form[action$='/sign-off'] button"));
  assert.match(await flash(pg), /Estimate signed off and locked/);
  W.proposalUrl = new URL(pg.url()).pathname;
  await shot(pg, "c10-proposal");
  const send = pg.locator("form[action$='/send-to-client']");
  assert.match(await send.locator("[name=client_email]").inputValue(), /morgan\.ellis/);
  await shot(pg, "c10-send", send.locator("button[type=submit]"));
  await submit(pg, send.locator("button[type=submit]"));
  assert.match(await flash(pg), /Proposal sent to/);
  const mail = newestMail("PROPOSAL_INVITATION", "morgan.ellis@training.calibraytai.invalid");
  assert.equal(mail.count, 1);
  const c = await context(PHONE, { isMobile: true, hasTouch: true });
  sessions.customer = c;
  await go(c.pg, mail.body.match(/\/proposal\/[A-Za-z0-9_\-.]+/)[0]);
  const page = await c.pg.locator("body").innerText();
  for (const marker of ["6800", "6,800", "Unit cost", "Markup"]) assert.ok(!page.includes(marker), `the customer sees ${marker}`);
  await shot(c.pg, "c10-customer-link");
  await c.pg.check("[name=accept]");
  await c.pg.fill("[name=confirmed_name]", CUSTOMER);
  await shot(c.pg, "c10-customer-accept", c.pg.getByRole("button", { name: "Accept Proposal" }));
  await submit(c.pg, c.pg.getByRole("button", { name: "Accept Proposal" }));
  assert.match(await c.pg.locator("body").innerText(), /Proposal accepted/);
  await go(pg, W.proposalUrl);
  assert.match(await pg.locator("main").innerText(), /Accepted/);
  await shot(pg, "c10-accepted");
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "Review contract" }).first());
  await shot(pg, "c10-contract-review");
  const gen = pg.getByRole("button", { name: "Generate contract" });
  if (await gen.count()) {
    await submit(pg, gen);
    console.log("RECORDED contract: " + (await flash(pg)));
    await shot(pg, "c10-contract-generated", pg.locator("#contract-snapshots"));
  } else console.log("RECORDED no Generate contract button");
});

// ================================================================== Module 11 (office part): work item, dates, crew
step("c11: a work item with an activity, Set dates on the calendar, the crew assigned", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c11-hub-project-work", pg.getByRole("link", { name: "Open project work" }));
  await submit(pg, pg.getByRole("link", { name: "Open project work" }));
  const element = pg.locator("form[action$='/elements']");
  await element.locator("[name=display_name]").fill(WORK_ITEM);
  await shot(pg, "c11-work-item", element.locator("button[type=submit]"));
  await submit(pg, element.locator("button[type=submit]"));
  assert.match(await flash(pg), /Work item added/);
  const activity = pg.locator("form[action*='/activities']").last();
  await activity.locator("[name=display_name]").fill(ACTIVITY);
  await shot(pg, "c11-activity", activity.locator("button[type=submit]"));
  await submit(pg, activity.locator("button[type=submit]"));
  assert.match(await pg.locator("main").innerText(), /Framing and decking \(training\)/);
  // The framing was added after the proposal was accepted, so it shows as extra work until reviewed:
  // it is the accepted proposal's work, so it is recorded as original work.
  const original = pg.locator("form").filter({ has: pg.getByRole("button", { name: "Record as original work" }) }).first();
  await original.locator("[name=reason]").fill("Part of the accepted proposal (training)");
  await shot(pg, "c11-record-original", original.getByRole("button", { name: "Record as original work" }));
  await submit(pg, original.getByRole("button", { name: "Record as original work" }));
  assert.doesNotMatch(await flash(pg), /can no longer/);
  console.log("RECORDED original work: " + (await flash(pg)));
  await go(pg, "/schedule");
  await submit(pg, pg.getByRole("link", { name: "Set dates" }).first());
  await Promise.all([pg.waitForNavigation(), pg.selectOption("[name=project_id]", { label: JOB })]);
  await pg.selectOption("[name=project_work_element_id]", { label: WORK_ITEM });
  await pg.fill("[name=scheduled_start]", day(0));
  await pg.fill("[name=scheduled_end]", day(2));
  await shot(pg, "c11-set-dates", pg.getByRole("button", { name: "Set dates" }));
  await submit(pg, pg.getByRole("button", { name: "Set dates" }));
  assert.match(await flash(pg), /Schedule saved/);
  const dates = pg.locator("details[data-project-dates]");
  if ((await dates.getAttribute("open")) === null) await dates.locator("summary").first().click();
  const card = pg.locator(`details[data-project-card="${W.projectId}"]`);
  if ((await card.getAttribute("open")) === null) await card.locator("summary").click();
  await submit(pg, card.getByRole("link", { name: "Edit dates" }).first());
  W.itemUrl = new URL(pg.url()).pathname;
  await pg.selectOption("[name=crew_id]", { label: CREW });
  await shot(pg, "c11-assign-crew", pg.getByRole("button", { name: "Assign" }));
  await submit(pg, pg.getByRole("button", { name: "Assign" }));
  assert.match(await flash(pg), /Assignment saved/);
  await go(pg, W.itemUrl);
  assert.match(await pg.locator("main").innerText(), /Pool deck crew \(training\)/);
  await go(pg, dayUrl(day(0), "&view=week&scope=company"));
});

// ================================================================== Module 8 (order): after acceptance, linked to the schedule
step("c08: Ben places the concrete order for today's work; Darcy confirms; Deliveries", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  const order = pg.locator("form[action$='/order']");
  await order.locator("[name=delivery_date]").fill(day(0));
  await order.locator("[name=delivery_window]").fill("7:00–9:00");
  const link = order.locator("[name=schedule_item_id] option").nth(1);
  if (await link.count()) await order.locator("[name=schedule_item_id]").selectOption(await link.getAttribute("value"));
  await order.locator("[name=site_contact]").fill("Kevin Field (training crew) 613-555-0101");
  await order.locator("[name=notes]").fill("Chute from the driveway, equipment pad beside the pool (training)");
  await shot(pg, "c08-place-order", order.locator("button[type=submit]"));
  await submit(pg, order.locator("button[type=submit]"));
  const placed = await flash(pg);
  assert.match(placed, /Purchase order PO-\d{4}-\d{4} sent/);
  W.po = placed.match(/PO-\d{4}-\d{4}/)[0];
  await shot(pg, "c08-order-sent");
  const store = await person("darcy");
  await go(store.pg, "/supplier/");
  await submit(store.pg, store.pg.getByRole("link", { name: W.po }).first());
  await shot(store.pg, "c08-supplier-order", store.pg.getByRole("button", { name: "Confirm order" }));
  await submit(store.pg, store.pg.getByRole("button", { name: "Confirm order" }));
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  assert.match(await pg.locator("main").innerText(), /[Cc]onfirmed/);
  await go(pg, "/deliveries");
  assert.match(await pg.locator("main").innerText(), new RegExp(W.po));
  await shot(pg, "c08-deliveries");
  const o = await olivia();
  await go(o.pg, "/deliveries");
  await shot(o.pg, "c08-deliveries-office");
});

// ================================================================== Module 11 (Field): Kevin's day
step("c11: Kevin on Field: Today with the job and the delivery, confirm, capture, drawings, extra work, time", async () => {
  const k = await kevinPhone();
  await go(k.pg, "/field/today");
  const today = await k.pg.locator("body").innerText();
  assert.match(today, /Harbour Lane Pool Deck/);
  for (const m of ["$", "6800", "6,800", "612.50", "Unit cost", "Markup"]) assert.ok(!today.includes(m), `Kevin sees ${m}`);
  await shot(k.pg, "c11-field-today");
  const deliveries = k.pg.locator("[data-field-deliveries]");
  if (await deliveries.count()) await shot(k.pg, "c11-field-delivery", deliveries);
  else console.log("RECORDED no delivery shown on Field Today");
  await go(k.pg, "/field/week");
  await shot(k.pg, "c11-field-week");
  await go(k.pg, "/field/month");
  await shot(k.pg, "c11-field-month");
  await go(k.pg, "/field/company-today");
  await shot(k.pg, "c11-field-company-today");
  await go(k.pg, "/field/today");
  await submit(k.pg, k.pg.getByRole("link", { name: "Choose Project" }));
  await shot(k.pg, "c11-field-projects", k.pg.locator(`a[href="/field/projects/${W.projectId}"]`));
  await submit(k.pg, k.pg.locator(`a[href="/field/projects/${W.projectId}"]`).first());
  await shot(k.pg, "c11-field-confirm", k.pg.getByRole("button", { name: "Confirm for Today" }));
  await submit(k.pg, k.pg.getByRole("link", { name: "Drawings and plans" }));
  assert.match(await k.pg.locator("body").innerText(), /harbour-lane-deck-plan-training/);
  await shot(k.pg, "c07-field-drawings");
  await go(k.pg, `/field/projects/${W.projectId}`);
  await submit(k.pg, k.pg.getByRole("button", { name: "Confirm and Capture" }));
  assert.match(k.pg.url(), /\/capture/);
  await k.pg.fill("#field-text", "Ledger and joists in on the north side. Pool coping protected with plywood. (training)");
  await k.pg.setInputFiles("#field-choose-photo", { name: "joists-training.jpg", mimeType: "image/jpeg", buffer: syntheticPhoto() });
  await shot(k.pg, "c11-capture", k.pg.locator("#field-save"));
  await k.pg.locator("#field-save").click();
  await k.pg.waitForFunction(() => /Saved/.test(document.querySelector("#field-feedback")?.innerText || ""), null, { timeout: 30000 });
  await k.pg.waitForFunction(() => document.querySelector("#field-retry-panel")?.hidden !== false, null, { timeout: 20000 }).catch(() => console.log("RECORDED capture still pending on the phone after 20 s"));
  await shot(k.pg, "c11-capture-saved", k.pg.locator("#field-feedback"));
  await go(k.pg, `/field/projects/${W.projectId}/extra-work`);
  await k.pg.fill("[name=description]", "Morgan asked for two extra steps down to the lawn on the east side. (training)");
  await k.pg.fill("[name=new_element_name]", "Extra steps to the lawn (training)");
  await shot(k.pg, "c11-extra-work", k.pg.getByRole("button", { name: "Record extra work" }));
  await submit(k.pg, k.pg.getByRole("button", { name: "Record extra work" }));
  assert.match(await flash(k.pg), /Extra work recorded/);
  await shot(k.pg, "c11-extra-work-recorded");
  await go(k.pg, "/field/today");
  await submit(k.pg, k.pg.getByRole("link", { name: "Enter time" }).first());
  const other = k.pg.locator("#field-time-other-toggle");
  if (await other.count()) await other.click();
  await k.pg.selectOption("[name=project_work_element_id]", { label: WORK_ITEM });
  const v = await k.pg.locator("[name=project_work_activity_id] option", { hasText: "Framing and decking" }).first().getAttribute("value");
  await k.pg.selectOption("[name=project_work_activity_id]", v);
  await k.pg.fill("[name=hours]", "8");
  await k.pg.fill("[name=worker_note]", "Ledger and joists, north side (training)");
  await shot(k.pg, "c11-time", k.pg.getByRole("button", { name: "Send time" }));
  await submit(k.pg, k.pg.getByRole("button", { name: "Send time" }));
  assert.match(await flash(k.pg), /Time sent for approval/);
  await shot(k.pg, "c11-time-sent");
  await go(k.pg, "/field/time");
  await shot(k.pg, "c11-my-time");
});

// ================================================================== Module 11 (office): observations, extra work → change order, time, delivered
step("c11: the office sees the field note, turns the extra work into an approved change order, approves time, marks delivered", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c11-field-observations", pg.locator("h2", { hasText: "Field Observations" }));
  await go(pg, `/work-structure/projects/${W.projectId}`);
  await shot(pg, "c11-extra-work-office", pg.locator("h2", { hasText: "Extra steps to the lawn" }));
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "New Change Order" }));
  await pg.fill("[name=title]", "Extra steps to the lawn (training)");
  const pick = pg.locator("[name=project_id]");
  if (!(await pick.inputValue())) await pick.selectOption({ label: JOB });
  await pg.fill("[name=requested_by]", CUSTOMER);
  await pg.fill("[name=requested_date]", day(0));
  await pg.fill("[name=description]", "Two composite steps from the east side of the deck down to the lawn.");
  await pg.fill("[name=reason]", "Customer request on site, recorded by Kevin on Field as extra work.");
  await shot(pg, "c11-change-order-form", pg.getByRole("button", { name: "Create Change Order" }));
  await submit(pg, pg.getByRole("button", { name: "Create Change Order" }));
  console.log("RECORDED change order: " + (await flash(pg)) + " -> " + pg.url());
  W.coUrl = new URL(pg.url()).pathname;
  await go(pg, `${W.coUrl}?tab=items`);
  const add = pg.locator("form").filter({ has: pg.getByRole("button", { name: "Add Item" }) });
  await add.locator("[name=description]").fill("Two extra steps to the lawn, composite, supplied and installed (training)");
  await add.locator("[name=quantity]").fill("1");
  await add.locator("[name=unit]").fill("ls");
  await add.locator("[name=unit_price]").fill("850");
  await shot(pg, "c11-change-order-item", add.getByRole("button", { name: "Add Item" }));
  await submit(pg, add.getByRole("button", { name: "Add Item" }));
  await go(pg, W.coUrl);
  await pg.selectOption("form[action$='/status'] [name=status]", "Approved");
  await shot(pg, "c11-change-order-approve", pg.getByRole("button", { name: "Save Status" }));
  await submit(pg, pg.getByRole("button", { name: "Save Status" }));
  console.log("RECORDED change order status: " + (await flash(pg)));
  // Time review.
  await go(pg, `/time?project_id=${W.projectId}`);
  assert.match(await pg.locator("main").innerText(), /Kevin Field/);
  await shot(pg, "c11-time-review");
  await submit(pg, pg.locator('main a[href^="/time/"]').filter({ hasText: day(0) }).first());
  await shot(pg, "c11-time-approve", pg.getByRole("button", { name: "Approve", exact: true }));
  await submit(pg, pg.getByRole("button", { name: "Approve", exact: true }));
  assert.match(await pg.locator("main").innerText(), /Approved/);
  // The concrete arrived.
  await go(pg, `/projects/${W.projectId}/supplier-requests`);
  await pg.locator("details[data-mark-delivered] summary").first().click();
  await pg.fill("details[data-mark-delivered] [name=note]", "Poured at the equipment pad (training)");
  await shot(pg, "c11-mark-delivered", pg.getByRole("button", { name: "Mark delivered" }));
  await submit(pg, pg.getByRole("button", { name: "Mark delivered" }));
  console.log("RECORDED delivered: " + (await flash(pg)));
});

// ================================================================== Module 4: QuickBooks
step("c04: invoices from the proposal and the change order; files for QuickBooks; Check QuickBooks", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c04-hub-invoice", pg.getByRole("link", { name: "Make an invoice" }));
  await submit(pg, pg.getByRole("link", { name: "Make an invoice" }));
  await pg.selectOption("[name=kind]", "DEPOSIT");
  await pg.fill("[name=percent]", "30");
  await shot(pg, "c04-make-invoice", pg.getByRole("button", { name: "Make the invoice" }));
  await submit(pg, pg.getByRole("button", { name: "Make the invoice" }));
  const made = await flash(pg);
  assert.match(made, /Invoice INV-\d{4}-\d{4} made/);
  console.log("RECORDED deposit invoice: " + made);
  await shot(pg, "c04-invoice-made");
  await go(pg, `/accounting/projects/${W.projectId}/invoices/new`);
  const co = pg.getByRole("button", { name: "Invoice the change order" });
  if (await co.count()) {
    await shot(pg, "c04-invoice-change-order", co);
    await submit(pg, co);
    console.log("RECORDED change order invoice: " + (await flash(pg)));
  } else console.log("RECORDED no approved change order offered for invoicing");
  await menu(pg, "Company", "/accounting");
  await shot(pg, "c04-accounting");
  await shot(pg, "c04-files", pg.locator('main a[href="/accounting/export/customers"]'));
  for (const kind of ["customers", "suppliers", "invoices", "bills"]) {
    await go(pg, "/accounting");
    await submit(pg, pg.locator(`main a[href="/accounting/export/${kind}"]`).first());
    await shot(pg, `c04-export-${kind}`);
    const button = pg.getByRole("button", { name: /Download the file/ });
    if (await button.count()) {
      const [download] = await Promise.all([pg.waitForEvent("download"), button.click()]);
      const body = fs.readFileSync(await download.path(), "utf8");
      if (kind === "customers") assert.ok(body.includes("Morgan Ellis"), "the Customers file has Morgan Ellis");
      console.log(`RECORDED ${kind} file ${download.suggestedFilename()} ${body.split("\n")[0]}`);
    } else console.log(`RECORDED ${kind}: nothing to download`);
  }
  await go(pg, "/accounting/export/invoices");
  await shot(pg, "c04-nothing-new");
  await go(pg, "/accounting/invoices");
  await shot(pg, "c04-invoices");
  await go(pg, "/accounting/reconcile");
  await shot(pg, "c04-check-quickbooks", pg.getByRole("button", { name: "Check" }));
  const o = await olivia();
  await go(o.pg, "/accounting");
});

// ================================================================== Module 12: the working day and closeout
step("c12: Home in the morning, the final invoice, Getting started 15 of 15, closing and reopening the project", async () => {
  const { pg } = await ben();
  await go(pg, "/");
  assert.match(await pg.locator("main").innerText(), /Harbour Lane Pool Deck/);
  await shot(pg, "c12-home-morning");
  const o = await olivia();
  await go(o.pg, "/");
  const phone = await person("ben", PHONE);
  await go(phone.pg, "/");
  await shot(phone.pg, "c12-home-phone");
  const k = await kevinPhone();
  await go(k.pg, "/field/today");
  await shot(k.pg, "c12-field-day");
  await go(pg, `/projects/${W.projectId}`);
  await shot(pg, "c12-hub-money", pg.locator('a[href="#hub-monitor"]'));
  await go(pg, `/accounting/projects/${W.projectId}/invoices/new`);
  await pg.selectOption("[name=kind]", "FINAL");
  await shot(pg, "c12-final-invoice", pg.getByRole("button", { name: "Make the invoice" }));
  await submit(pg, pg.getByRole("button", { name: "Make the invoice" }));
  console.log("RECORDED final invoice: " + (await flash(pg)));
  await markDone(pg, "working_day");
  await go(pg, "/getting-started");
  const [done, total] = (await pg.locator("[data-getting-started]").getAttribute("data-getting-started")).split("/").map(Number);
  console.log(`RECORDED Getting started ${done} of ${total}`);
  await shot(pg, "c12-getting-started-done");
  await go(pg, `/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("link", { name: "Close Project" }));
  await shot(pg, "c12-close-confirm");
  const box = pg.locator("main form input[type=checkbox]");
  if (await box.count()) await box.first().check();
  await submit(pg, pg.locator("main form button[type=submit]", { hasText: "Close Project" }));
  console.log("RECORDED close: " + (await flash(pg)));
  await shot(pg, "c12-closed");
  await go(pg, "/projects/?view=closed");
  assert.match(await pg.locator("main").innerText(), /Harbour Lane Pool Deck/);
  const reopen = pg.locator(`a[href="/projects/${W.projectId}/reopen"]`);
  await go(pg, `/projects/${W.projectId}`);
  assert.equal(await reopen.count() > 0, true, "the owner is offered Reopen Project");
  await submit(pg, reopen.first());
  await shot(pg, "c12-reopen-confirm");
  await submit(pg, pg.locator("main form button[type=submit]", { hasText: "Reopen Project" }));
  assert.match(await flash(pg), /This Project is current/);
  // Office staff are not offered Close Project.
  await go(o.pg, `/projects/${W.projectId}`);
  assert.equal(await o.pg.locator(`a[href="/projects/${W.projectId}/close"]`).count(), 0);
});
