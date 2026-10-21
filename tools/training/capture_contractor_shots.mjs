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
  await shot(pg, "c02-crew-members");
});
