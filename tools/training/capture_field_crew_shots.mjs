// Screenshots for the Field Crew pathway of the Training & Acceptance Centre (Joel, 22 Oct 2026).
//
// Starts the local training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on,
// the synthetic training company from app/training/environment.py). Ben (the owner, on a desktop) does only
// what puts work on the crew's phones, through the real office pages: the Pool deck crew with Kevin and Liam,
// a work item with an activity on Harbour Lane Pool Deck (training), its dates with the crew assigned, and the
// deck plan PDF. Kevin then does what app/training/field_crew.py teaches, on an iPhone-sized screen
// (390 x 844, touch): the Training Centre, Field Today, the job, the week and month, drawings, Capture (also
// with no signal), extra work, time, time the office returned, a date the office moved, acceptance tests.
// Each picture is saved to app/static/training/shots/f<module>-<name>.png (and the two Training Centre
// pictures of the contractor pathway that changed with the third pathway). Synthetic data only. Any response
// of 500 or more, a page JavaScript error, sideways scrolling on the phone, or money on a Field page fails it.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium \
//      node --test --test-concurrency=1 tools/training/capture_field_crew_shots.mjs
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
const W = {};
const JOB = "Harbour Lane Pool Deck (training)";
const CREW = "Pool deck crew (training)";
const WORK_ITEM = "Pool deck framing and decking (training)";
const ACTIVITY = "Framing and decking (training)";
const MONEY = [/\$\s?\d/, /\bprice/i, /\bcost/i, /margin/i, /markup/i, /invoice/i, /estimate/i];
const day = (offset) => new Date(Date.now() + offset * 864e5).toISOString().slice(0, 10);

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
  console.log(`FIELD_CREW_SHOTS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
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
  pg.on("dialog", (d) => d.accept());
  return { ctx, pg };
}
const phoneContext = () => context(PHONE, { isMobile: true, hasTouch: true });
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
async function signIn(s, email, password, next = "") {
  await go(s.pg, `/login${next ? `?next=${encodeURIComponent(next)}` : ""}`);
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(s.pg.url(), /\/login/, `${email} signs in`);
}
async function ben() {
  if (!sessions.ben) {
    sessions.ben = await context(DESK);
    await signIn(sessions.ben, facts.people.ben.email, PASSWORD("ben"));
  }
  return sessions.ben;
}
async function flash(pg) { return (await pg.locator(".flash, .alert, .field-flash, .tc-flash, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function noMoney(pg, label) {
  if (!new URL(pg.url()).pathname.startsWith("/field")) return;
  const text = await pg.locator("body").innerText();
  for (const m of MONEY) assert.doesNotMatch(text, m, `${label}: Field shows ${m}`);
}
// A viewport picture; `focus` (a locator) is scrolled to the middle of the screen first.
async function shot(pg, name, focus) {
  assert.match(name, /^[cf]\d{2}-[a-z0-9-]+$/);
  if (pg.viewportSize().width <= 500) { await noSideways(pg, name); await noMoney(pg, name); }
  if (focus) {
    const el = focus.first();
    await el.waitFor({ state: "attached" });
    await el.evaluate((e) => e.scrollIntoView({ block: "center", inline: "nearest" }));
  } else {
    await pg.evaluate(() => window.scrollTo(0, 0));
  }
  await pg.waitForTimeout(200);
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
    for (const e of m.querySelectorAll("h1,h2,h3,summary,legend,.alert,.field-flash,button,a,label,p")) {
      if (!vis(e)) continue;
      const s = t(e);
      if (!s || /^\d+$/.test(s)) continue;
      out.push(`${e.tagName} ${s.slice(0, 160)}`);
    }
    return [...new Set(out)].join("\n");
  });
}
function newestMail(to) {
  const dir = facts.mail_dir;
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).sort() : [];
  const bodies = files.map((f) => fs.readFileSync(path.join(dir, f), "utf8")).filter((b) => b.includes(`To: ${to}`));
  return bodies.at(-1) || "";
}
function python(code) {
  const r = spawnSync(PY, ["-c", code], { maxBuffer: 16 * 1024 * 1024 });
  assert.equal(r.status, 0, String(r.stderr));
  return r.stdout;
}
function syntheticPlanPdf() {
  return python("import io,sys;from PIL import Image,ImageDraw;im=Image.new('RGB',(1650,1275),'white');d=ImageDraw.Draw(im);" +
    "d.rectangle([150,200,1250,900],outline='black',width=6);d.rectangle([400,350,1000,700],outline=(30,90,160),width=4);" +
    "d.text((420,520),'POOL (existing)',fill=(30,90,160));d.text((160,960),'HARBOUR LANE POOL DECK - DECK PLAN (TRAINING, SYNTHETIC)',fill='black');" +
    "d.text((160,1000),'14 Harbour Lane, Merrickville ON - Scale 1/4 in = 1 ft',fill='black');" +
    "b=io.BytesIO();im.save(b,'PDF',resolution=150);sys.stdout.buffer.write(b.getvalue())");
}
function syntheticPhoto() {
  return python("import io,sys;from PIL import Image,ImageDraw;im=Image.new('RGB',(1200,900),(120,150,170));d=ImageDraw.Draw(im);" +
    "[d.rectangle([60+i*70,500,110+i*70,860],fill=(150,110,70)) for i in range(15)];d.rectangle([0,0,1200,300],fill=(170,200,230));" +
    "d.text((40,40),'Harbour Lane Pool Deck - joists in (training photo, synthetic)',fill='black');" +
    "b=io.BytesIO();im.save(b,'JPEG',quality=80);sys.stdout.buffer.write(b.getvalue())");
}
function shrink() {
  if (!saved.length) return;
  const r = spawnSync(PY, ["-c",
    "import os,sys\nfrom PIL import Image\nroot=sys.argv[1]\nfor n in sys.argv[2:]:\n p=os.path.join(root,n)\n" +
    " if os.path.getsize(p)<=330000: continue\n im=Image.open(p).convert('RGB')\n" +
    " im.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).save(p,optimize=True)\n",
    SHOTS, ...new Set(saved)]);
  if (r.status !== 0) console.log(String(r.stderr));
}

// ================================================================== the Training Centre's front door
step("sign-in page with three groups; the contractor register page; the phone sign-in and forgot-password pages", async () => {
  const d = await context(DESK);
  sessions.anon = d;
  await go(d.pg, "/training/signin");
  assert.equal(await d.pg.locator("[data-signin]").count(), 3);
  await shot(d.pg, "c01-training-signin", d.pg.locator("[data-signin=contractor]"));
  const p = await phoneContext();
  sessions.anonPhone = p;
  await go(p.pg, "/training/signin");
  await shot(p.pg, "f01-training-signin", p.pg.locator("[data-signin=field]"));
  await submit(p.pg, p.pg.locator("[data-signin=field]"));
  assert.match(p.pg.url(), /\/login\?next=/);
  await p.pg.fill("input[name=email]", facts.people.kevin.email);
  await shot(p.pg, "f01-sign-in", p.pg.locator("form button[type=submit]"));
  await go(p.pg, "/forgot-password");
  await shot(p.pg, "f01-forgot", p.pg.locator("form button[type=submit]"));
  const { pg } = await ben();
  await go(pg, "/training");
  assert.match(await pg.locator("main").innerText(), /Start my training/);
  await shot(pg, "c01-register", pg.locator("[data-register]"));
});

// ================================================================== the office puts the work on the crew's phones
step("Ben: the Pool deck crew, a work item with its activity, dates with the crew assigned, the deck plan", async () => {
  const { pg } = await ben();
  await go(pg, "/projects/");
  await submit(pg, pg.locator("main a", { hasText: JOB }).first());
  W.projectId = Number(pg.url().match(/\/projects\/(\d+)/)[1]);
  await go(pg, "/settings/crews/new");
  await pg.fill("[name=name]", CREW);
  await submit(pg, pg.locator("main form button[type=submit]"));
  assert.match(await flash(pg), /Crew saved/);
  await submit(pg, pg.getByRole("link", { name: CREW }));
  for (const who of ["Kevin Field (training crew)", "Liam Field (training crew)"]) {
    await pg.selectOption("[name=user_id]", { label: who });
    await pg.fill('form[action$="/members"] [name=effective_from]', day(-1));
    await submit(pg, pg.locator('form[action$="/members"] button[type=submit]'));
  }
  await go(pg, `/work-structure/projects/${W.projectId}`);
  const element = pg.locator("form[action$='/elements']");
  await element.locator("[name=display_name]").fill(WORK_ITEM);
  await element.locator("input[name=scope_origin][value=ORIGINAL]").check();
  await submit(pg, element.locator("button[type=submit]"));
  assert.match(await flash(pg), /Work item added/);
  const activity = pg.locator("form[action*='/activities']").last();
  await activity.locator("[name=display_name]").fill(ACTIVITY);
  await activity.locator("input[name=scope_origin][value=ORIGINAL]").check();
  await submit(pg, activity.locator("button[type=submit]"));
  await go(pg, "/schedule");
  await submit(pg, pg.getByRole("link", { name: "Set dates" }).first());
  await Promise.all([pg.waitForNavigation(), pg.selectOption("[name=project_id]", { label: JOB })]);
  await pg.selectOption("[name=project_work_element_id]", { label: WORK_ITEM });
  await pg.fill("[name=scheduled_start]", day(0));
  await pg.fill("[name=scheduled_end]", day(2));
  await submit(pg, pg.getByRole("button", { name: "Set dates" }));
  assert.match(await flash(pg), /Schedule saved/);
  const dates = pg.locator("details[data-project-dates]");
  if ((await dates.getAttribute("open")) === null) await dates.locator("summary").first().click();
  const card = pg.locator(`details[data-project-card="${W.projectId}"]`);
  if ((await card.getAttribute("open")) === null) await card.locator("summary").click();
  await submit(pg, card.getByRole("link", { name: "Edit dates" }).first());
  W.itemUrl = new URL(pg.url()).pathname;
  await pg.selectOption("[name=crew_id]", { label: CREW });
  await submit(pg, pg.getByRole("button", { name: "Assign" }));
  assert.match(await flash(pg), /Assignment saved/);
  await go(pg, `/projects/${W.projectId}`);
  const req = pg.getByRole("button", { name: "Drawings are required" });
  if (await req.count()) await submit(pg, req);
  await go(pg, `/projects/${W.projectId}/plans/upload`);
  await pg.setInputFiles("[name=plan_file]", { name: "harbour-lane-deck-plan-training.pdf", mimeType: "application/pdf", buffer: syntheticPlanPdf() });
  await pg.fill("[name=notes]", "Deck plan (training)");
  await submit(pg, pg.getByRole("button", { name: "Upload" }));
  await go(pg, `/projects/${W.projectId}/plans`);
  assert.match(await pg.locator("main").innerText(), /harbour-lane-deck-plan-training/);
});

step("Liam's set-password email opens Set New Password on the iPhone", async () => {
  const { pg } = await ben();
  await go(pg, "/settings/people");
  await submit(pg, pg.locator("main a", { hasText: "Liam Field" }).first());
  await submit(pg, pg.getByRole("button", { name: "Email a link to choose a password" }));
  // With email delivery off, People & Access shows the one-time link for Ben to give Liam himself.
  const shown = pg.locator("#one-time-link");
  const url = (await shown.count()) ? await shown.inputValue() : (newestMail(facts.people.liam.email).match(/https?:\/\/\S+/) || [""])[0];
  assert.ok(url, `a set-password link for Liam: ${await flash(pg)}`);
  const u = new URL(url);
  const link = [u.pathname + u.search + u.hash];  // the credential is after "#" (never sent to the server)
  const l = await phoneContext();
  sessions.liam = l;
  await go(l.pg, link[0]);
  await l.pg.waitForSelector("[name=password]");
  await l.pg.fill("[name=password]", "Synthetic-liam-new-1");
  await l.pg.fill("[name=confirm_password]", "Synthetic-liam-new-1");
  await shot(l.pg, "f01-set-password", l.pg.locator("form button[type=submit]"));
});

// ================================================================== Kevin: the Training Centre on his iPhone
step("Kevin registers into the Field Crew training, ticks a step, asks the Tutor", async () => {
  const k = await phoneContext();
  sessions.kevin = k;
  await go(k.pg, "/training/signin");
  await submit(k.pg, k.pg.locator("[data-signin=field]"));
  await k.pg.fill("input[name=email]", facts.people.kevin.email);
  await k.pg.fill("input[name=password]", PASSWORD("kevin"));
  await submit(k.pg, k.pg.locator("form button[type=submit]").first());
  assert.match(new URL(k.pg.url()).pathname, /^\/training$/);
  const reg = await k.pg.locator("main").innerText();
  assert.match(reg, /Start my Field Crew training/);
  assert.doesNotMatch(reg, /Contractor owner|Office staff|Supplier/);
  await shot(k.pg, "f01-register", k.pg.locator("[data-register]"));
  await submit(k.pg, k.pg.locator("[data-register]"));
  assert.equal(await k.pg.locator("[data-module]").count(), 8);
  await shot(k.pg, "f01-training-home", k.pg.locator("[data-continue]"));
  await submit(k.pg, k.pg.locator("[data-continue]"));
  assert.equal(await k.pg.getAttribute("[data-lesson-page]", "data-lesson-page"), "f01-start-training");
  await k.pg.click('[data-tick="0"]');
  await k.pg.waitForFunction(() => document.querySelector('[data-step-card="0"]').classList.contains("is-done"));
  await shot(k.pg, "f01-lesson", k.pg.locator('[data-step-card="0"] [data-tick]'));
  await k.pg.click("[data-tutor-launch]");  // the Tutor opens as a drawer from the header (23 Oct 2026)
  await k.pg.waitForFunction(() => document.querySelector("[data-tutor]").classList.contains("is-open"));
  await k.pg.click('[data-tutor-quick="Where is it?"]');
  await k.pg.waitForFunction(() => /Go to/.test(document.querySelector("[data-tutor-live]")?.textContent || ""));
  await shot(k.pg, "f01-tutor", k.pg.locator("[data-tutor-live]"));
});

// ================================================================== Kevin on Field
step("Kevin on Field: Today, Help, Guide, Password, the job, Company today, the week and month, drawings", async () => {
  const { pg } = sessions.kevin;
  await go(pg, "/training");
  await submit(pg, pg.locator("[data-open-field]"));
  assert.match(pg.url(), /\/field\/today/);
  const today = await pg.locator("main").innerText();
  assert.match(today, /Harbour Lane Pool Deck/);
  // The one-time schedule-texts question on the first Field visit (22 Oct 2026). Kevin answers Not now here;
  // module 3 turns texts on from Field → Texts.
  assert.match(await pg.locator("[data-field-texts-setup]").innerText(), /Get a text when your schedule changes\?/);
  await shot(pg, "f01-texts-setup", pg.locator("[data-field-texts-setup]"));
  await submit(pg, pg.locator("[data-texts-setup-no]"));
  assert.equal(await pg.locator("[data-field-texts-setup]").count(), 0);
  await shot(pg, "f01-field-today");
  await shot(pg, "f02-today", pg.locator(".field-schedule-group").first());
  await pg.locator("details.contextual-help summary").first().click();
  await shot(pg, "f02-help", pg.locator("details.contextual-help .contextual-help-body"));
  await go(pg, "/field/workflow");
  await shot(pg, "f01-guide");
  await go(pg, "/account/password");
  await shot(pg, "f01-password", pg.locator("main form button[type=submit]"));
  await go(pg, "/field/today");
  await submit(pg, pg.getByRole("link", { name: "Choose Project" }));
  await shot(pg, "f02-projects", pg.locator(`a[href="/field/projects/${W.projectId}"]`));
  await submit(pg, pg.locator(`a[href="/field/projects/${W.projectId}"]`).first());
  await shot(pg, "f02-confirm", pg.getByRole("button", { name: "Confirm for Today" }));
  await shot(pg, "f04-confirm", pg.getByRole("link", { name: "Drawings and plans" }));
  await submit(pg, pg.getByRole("link", { name: "Drawings and plans" }));
  assert.match(await pg.locator("main").innerText(), /harbour-lane-deck-plan-training/);
  await shot(pg, "f04-drawings");
  await go(pg, `/field/projects/${W.projectId}`);
  await submit(pg, pg.getByRole("button", { name: "Confirm for Today" }));
  assert.match(pg.url(), /\/field\/today/);
  await shot(pg, "f02-today-confirmed", pg.getByRole("link", { name: "Capture", exact: true }));
  await go(pg, "/field/company-today");
  await shot(pg, "f02-company-today");
  await go(pg, "/field/week");
  await shot(pg, "f03-week", pg.locator(".field-schedule-day.is-today"));
  await go(pg, "/field/month");
  const dot = pg.locator("a.field-calendar-day:has(.field-calendar-dot)").nth(1);
  if (await dot.count()) await submit(pg, dot);
  await shot(pg, "f03-month", pg.locator(".field-calendar"));
});

step("Kevin: Capture a note and a photo, Recent observations, extra work, time", async () => {
  const { pg } = sessions.kevin;
  await go(pg, `/field/projects/${W.projectId}/capture`);
  await pg.fill("#field-text", "Ledger and joists in on the north side. Pool coping protected with plywood. (training)");
  await pg.setInputFiles("#field-choose-photo", { name: "joists-training.jpg", mimeType: "image/jpeg", buffer: syntheticPhoto() });
  await shot(pg, "f06-capture", pg.locator("#field-save"));
  await pg.locator("#field-save").click();
  await pg.waitForFunction(() => /Saved/.test(document.querySelector("#field-feedback")?.innerText || ""), null, { timeout: 30000 });
  await shot(pg, "f06-capture-saved", pg.locator("#field-feedback"));
  await go(pg, "/field/today");
  const recent = pg.locator("h2", { hasText: "Recent observations" });
  await recent.waitFor();
  await shot(pg, "f06-recent", recent);
  await go(pg, `/field/projects/${W.projectId}/extra-work`);
  await pg.fill("[name=description]", "Morgan asked for two extra steps down to the lawn on the east side. (training)");
  await pg.fill("[name=new_element_name]", "Extra steps to the lawn (training)");
  await shot(pg, "f05-extra-work", pg.getByRole("button", { name: "Record extra work" }));
  await submit(pg, pg.getByRole("button", { name: "Record extra work" }));
  assert.match(await flash(pg), /Extra work recorded/);
  await shot(pg, "f05-extra-recorded");
  await submit(pg, pg.getByRole("link", { name: "Enter time" }).first());
  // TIME ENTRY (module 5): the Scheduled today button chooses the booked work (docs/operations/field-time.md).
  const scheduled = pg.locator(".field-time-recent-btn", { hasText: WORK_ITEM }).first();
  await shot(pg, "f05-time-scheduled", scheduled);
  await scheduled.click();
  const work = pg.locator("[name=project_work_activity_id]");
  if (await work.isVisible() && !(await work.inputValue())) {
    const v = await work.locator("option", { hasText: ACTIVITY }).first().getAttribute("value");
    await work.selectOption(v);
  }
  await pg.fill("[name=hours]", "8");
  await pg.fill("[name=worker_note]", "Ledger and joists, north side (training)");
  await shot(pg, "f05-time", (await work.isVisible()) ? work : scheduled);
  await submit(pg, pg.getByRole("button", { name: "Send time" }));
  assert.match(await flash(pg), /Time sent for approval/);
  await shot(pg, "f05-time-sent", pg.locator(".field-time-item").first());
  await shot(pg, "f05-my-time-week", pg.locator("[data-week-hours]"));
});

step("No signal: the Offline bar, a capture kept on the phone, then sent when the signal is back", async () => {
  const { pg, ctx } = sessions.kevin;
  await go(pg, "/field/today");
  await ctx.setOffline(true);
  await pg.waitForFunction(() => document.getElementById("field-offline-banner")?.hidden === false);
  await shot(pg, "f07-offline-banner");
  await ctx.setOffline(false);
  await go(pg, `/field/projects/${W.projectId}/capture`);
  await ctx.setOffline(true);
  await pg.fill("#field-text", "No signal at the back of the lot. Framing on the east side done. (training)");
  await pg.locator("#field-save").click();
  await pg.waitForFunction(() => /Saved on this phone/.test(document.querySelector("#field-feedback")?.innerText || ""), null, { timeout: 30000 });
  await pg.waitForFunction(() => document.getElementById("field-retry-panel")?.hidden === false, null, { timeout: 10000 }).catch(() => {});
  await shot(pg, "f07-offline-saved", pg.locator("#field-feedback"));
  await ctx.setOffline(false);
  await pg.waitForFunction(() => /^Saved/.test((document.querySelector("#field-feedback")?.innerText || "").trim()) || document.getElementById("field-retry-panel")?.hidden === true, null, { timeout: 30000 });
  await pg.waitForTimeout(1500);
  await shot(pg, "f07-synced", pg.locator("#field-feedback"));
});

// ------------------------------------------------------------------ TIME ENTRY (module 5 only)
// Time, My time, returned time and Ben's approval. Re-capture these after v1/field-time-labour-2026-10-22 merges
// (final buttons and statuses: docs/operations/field-time.md); the lessons using them are all in module 5.
step("the office returns Kevin's time; Kevin fixes it from My time; Ben approves it", async () => {
  const { pg } = await ben();
  await go(pg, `/time?project_id=${W.projectId}`);
  await submit(pg, pg.locator('main a[href^="/time/"]').filter({ hasText: day(0) }).first());
  await pg.fill("form[action$='/return'] [name=reason]", "You left at 3:30. Please send 7.5 hours. (training)");
  await submit(pg, pg.locator("form[action$='/return'] button[type=submit]"));
  const k = sessions.kevin.pg;
  await go(k, "/field/today");
  await shot(k, "f05-today-returned", k.locator("[data-returned-time]"));
  await submit(k, k.locator("[data-returned-time] a"));
  assert.match(new URL(k.url()).pathname, /^\/field\/time$/);
  assert.match(await k.locator("main").innerText(), /Returned: You left at 3:30/);
  await shot(k, "f05-time-returned", k.getByRole("link", { name: "Fix and send again" }));
  await submit(k, k.getByRole("link", { name: "Fix and send again" }));
  assert.match(await k.locator("main").innerText(), /Returned: You left at 3:30/);
  await k.fill("[name=hours]", "7.5");
  await shot(k, "f05-time-fix", k.locator(".field-time-returned"));
  await submit(k, k.getByRole("button", { name: "Send time" }));
  assert.match(await flash(k), /Time sent again for approval/);
  // Ben approves the fixed entry; Kevin sees Approved on My time.
  await go(pg, `/time?project_id=${W.projectId}`);
  await submit(pg, pg.locator('main a[href^="/time/"]').filter({ hasText: day(0) }).first());
  await submit(pg, pg.getByRole("button", { name: "Approve", exact: true }));
  assert.match(await pg.locator("main").innerText(), /Approved/);
  await go(k, "/field/time");
  assert.match(await k.locator("main").innerText(), /Approved/);
  assert.equal(await k.getByRole("link", { name: "Fix and send again" }).count(), 0);
  await shot(k, "f05-time-approved", k.locator(".field-time-item").first());
  // Shop / Company Work: Ben sets it up once; Kevin sends 1.5 hours of equipment upkeep.
  await go(pg, "/time");
  await submit(pg, pg.getByRole("button", { name: "Set up Shop / Company Work" }));
  assert.match(await flash(pg), /Shop \/ Company Work is ready/);
  await go(k, "/field/time");
  await submit(k, k.locator("[data-company-time]"));
  assert.match(await k.locator("main").innerText(), /Shop \/ Company Work: paid company time, not a customer's job/);
  const cw = k.locator("[name=project_work_activity_id]");
  if (await k.locator("#field-time-other-toggle").count() && !(await cw.isVisible())) await k.click("#field-time-other-toggle");
  const shopEl = k.locator("[name=project_work_element_id]");
  if (await shopEl.isVisible() && !(await shopEl.inputValue())) await shopEl.selectOption({ index: 1 });
  const cv = await cw.locator("option", { hasText: "Equipment and vehicle upkeep" }).first().getAttribute("value");
  await cw.selectOption(cv);
  await k.fill("[name=hours]", "1.5");
  await shot(k, "f05-company-time", cw);
  await submit(k, k.getByRole("button", { name: "Send time" }));
  assert.match(await flash(k), /Time sent for approval/);
  assert.match(await k.locator("main").innerText(), /Company time/);
});

step("Kevin turns on schedule texts on Field (SMS notices, 22 Oct 2026)", async () => {
  const k = sessions.kevin.pg;
  await go(k, "/field/today");
  await submit(k, k.locator("[data-field-texts-link]"));
  assert.match(k.url(), /\/field\/text-messages$/);
  assert.match(await k.locator("[data-field-texts-status]").innerText(), /Texts are off/);
  await shot(k, "f03-texts-off");
  await k.fill("input[name=mobile_phone]", "613-555-0142");
  await k.check("input[name=consent]");
  await submit(k, k.locator("[data-field-texts-save]"));
  assert.match(await flash(k), /Schedule texts are on/);
  await shot(k, "f03-texts-on");
});

step("the office moves the dates; Kevin sees them on This week", async () => {
  const { pg } = await ben();
  await go(pg, W.itemUrl);
  await pg.fill("[name=scheduled_start]", day(1));
  await pg.fill("[name=scheduled_end]", day(2));
  await submit(pg, pg.getByRole("button", { name: "Save dates" }));
  console.log("RECORDED move: " + (await flash(pg)));
  const k = sessions.kevin.pg;
  await go(k, "/field/week");
  const todayCard = await k.locator(".field-schedule-day.is-today").innerText();
  assert.doesNotMatch(todayCard, /Harbour Lane/, "the work moved off today");
  await shot(k, "f03-week-moved", k.locator(".field-schedule-day.is-today"));
});

step("Kevin's Field acceptance tests on the iPhone", async () => {
  const k = sessions.kevin.pg;
  await go(k, "/training/uat");
  assert.match(await k.locator("[data-uat-counts]").innerText(), /of 21/);
  await shot(k, "f08-uat-list", k.locator("[data-uat-continue]"));
  await submit(k, k.locator("[data-uat-continue]"));
  await k.check('input[name=status][value="FAIL"]');
  await k.fill('textarea[name=issue]', "The training site took me to my training, not to Field Today (synthetic example)");
  await shot(k, "f08-uat-case", k.locator("[data-record]"));
});
