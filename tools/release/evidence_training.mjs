// Release evidence for the Training & Acceptance Centre (21 Oct 2026), in a real browser against a local
// training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on, the synthetic
// training company). Synthetic data only.
//
// Contractor and supplier registration, role-specific lessons (a field worker gets no office lessons),
// Back / Next, Save and exit then Continue where I left off, screenshot enlargement, Tutor minimize and
// restore (kept after reloading) and its answers, a lesson completes only with its exercise ticked, notes,
// acceptance tests separate from training with Pass / Fail / Blocked and a retest that keeps the earlier
// result, the administrator dashboard (and its refusal to others), no sideways scrolling on a phone, module times,
// and one office trainee changing role to Field and back with both records kept and on the dashboard.
// Any response of 500 or more, or a page JavaScript error, fails the walk.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test --test-concurrency=1 tools/release/evidence_training.mjs
// EVIDENCE_SHOTS=<folder> saves a screenshot of each Training Centre screen.
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
  console.log(`TRAINING_SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

async function context(viewport) {
  const ctx = await browser.newContext({ viewport });
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
}
async function shot(pg, name) {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
}
async function noSideways(pg, label) {
  const [sw, iw] = await pg.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  assert.ok(sw <= iw + 1, `${label}: page scrolls sideways (${sw} > ${iw})`);
}
// The Tutor is a drawer opened from the header's Ask the Tutor button (23 Oct 2026); it starts closed on every page.
async function openTutor(pg) {
  const launch = pg.locator("header [data-tutor-launch]");
  assert.ok(await launch.isVisible(), "Ask the Tutor is in the header");
  assert.equal(await launch.getAttribute("aria-expanded"), "false", "the drawer starts closed");
  const saved = pg.waitForResponse((r) => r.url().endsWith("/training/tutor") && r.request().method() === "POST");
  await launch.click();
  await pg.waitForFunction(() => document.querySelector("[data-tutor]").classList.contains("is-open"));
  await saved;  // the open state is saved on the server
  assert.equal(await launch.getAttribute("aria-expanded"), "true");
}
async function closeTutor(pg) {
  const saved = pg.waitForResponse((r) => r.url().endsWith("/training/tutor") && r.request().method() === "POST");
  await pg.click("[data-tutor-button]");
  await pg.waitForFunction(() => !document.querySelector("[data-tutor]").classList.contains("is-open"));
  await saved;
  assert.equal(await pg.getAttribute("header [data-tutor-launch]", "aria-expanded"), "false");
}
async function signIn(key, viewport) {
  if (sessions[key]) return sessions[key];
  const s = await context(viewport);
  const person = facts.people[key];
  await s.pg.goto(`${base}/training`);
  assert.match(new URL(s.pg.url()).pathname, /\/training\/signin$/);
  const supplier = person.role === "SUPPLIER";
  await Promise.all([s.pg.waitForLoadState(), s.pg.click(`[data-signin="${supplier ? "supplier" : "contractor"}"]`)]);
  await s.pg.fill("input[name=email]", person.email);
  await s.pg.fill("input[name=password]", person.password);
  await Promise.all([s.pg.waitForNavigation(), s.pg.locator("form button[type=submit]").first().click()]);
  assert.match(new URL(s.pg.url()).pathname, /^\/training$/, `${key} comes back to the Training Centre`);
  sessions[key] = s;
  return s;
}
async function register(s, roleLabel) {
  await s.pg.getByLabel(roleLabel).check();
  await Promise.all([s.pg.waitForNavigation(), s.pg.click("[data-register]")]);
  await s.pg.waitForSelector("[data-progress]");
}

test("contractor owner registers and sees the contractor modules", async () => {
  const ben = await signIn("ben", DESK);
  const page = await ben.pg.content();
  for (const label of ["Contractor owner", "Office staff", "Field worker"]) assert.ok(page.includes(label));
  await shot(ben.pg, "training-register-contractor");
  await register(ben, "Contractor owner");
  assert.ok(await ben.pg.locator('[data-module="c01"]').isVisible());
  assert.equal(await ben.pg.locator('[data-module^="s"]').count(), 0, "no supplier modules for a contractor");
  await shot(ben.pg, "training-home-owner");
});

test("tick each step: it turns green and is saved; screenshot enlargement; Save and exit then Continue", async () => {
  const { pg } = sessions.ben;
  await Promise.all([pg.waitForNavigation(), pg.click("[data-continue]")]);
  const lesson = await pg.getAttribute("[data-lesson-page]", "data-lesson-page");
  const total = await pg.locator("[data-step-card]").count();
  assert.ok(total >= 1);
  assert.match(await pg.textContent("[data-stepcount]"), new RegExp(`^0 of ${total} steps done`));
  await pg.click('[data-tick="0"]');
  await pg.waitForFunction(() => document.querySelector('[data-step-card="0"]').classList.contains("is-done"));
  const green = await pg.locator('[data-step-card="0"] .tc-check').evaluate((el) => getComputedStyle(el).backgroundColor);
  assert.equal(green, "rgb(47, 125, 74)", "the step's circle turns green");
  assert.equal((await pg.textContent('[data-step-card="0"] .tc-check')).trim(), "\u2713");
  assert.match(await pg.textContent("[data-stepcount]"), new RegExp(`^1 of ${total} steps done`));
  await pg.reload();
  assert.ok(await pg.locator('[data-step-card="0"]').evaluate((c) => c.classList.contains("is-done")), "the tick is saved");
  const enlarge = pg.locator("[data-enlarge]");
  if (await enlarge.count()) {
    await enlarge.first().click();
    assert.ok(await pg.locator("[data-lightbox]").evaluate((d) => d.open), "the picture opens full size");
    await shot(pg, "training-screenshot-enlarged");
    await pg.locator("[data-lightbox] button").click();
    assert.equal(await pg.locator("[data-lightbox]").evaluate((d) => d.open), false);
  }
  await shot(pg, "training-lesson-desktop");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-exit]")]);
  assert.match(new URL(pg.url()).pathname, /^\/training$/);
  const href = await pg.getAttribute("[data-continue]", "href");
  assert.ok(href.includes(`/training/lessons/${lesson}`), `Continue returns to ${lesson}: ${href}`);
  assert.match(await pg.locator(`[data-lesson-row="${lesson}"]`).textContent(), new RegExp(`1 of ${total} steps`));
});

test("Training Tutor: follows the step, quick help, troubleshooting, the header drawer's state kept on every page", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/training`);
  assert.equal(await pg.getAttribute("[data-tutor]", "data-tutor-mode"), "home");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-continue]")]);
  assert.equal(await pg.getAttribute("[data-tutor]", "data-tutor-mode"), "lesson");
  // The Tutor follows the step: point it at a step and it shows that step.
  const cards = await pg.locator("[data-step-card]").count();
  const target = cards > 1 ? 1 : 0;
  const title = await pg.getAttribute(`[data-step-card="${target}"]`, "data-t-title");
  await pg.locator(`[data-step-card="${target}"] .tc-step-head h2`).click();
  await openTutor(pg);
  assert.ok((await pg.textContent("[data-tutor-title]")).includes(title), "the Tutor shows the step the trainee is on");
  // Quick help: "It didn't work" gives that step's recovery.
  await pg.click('[data-tutor-quick="It didn\'t work"]');
  await pg.waitForFunction(() => { const a = document.querySelector("[data-tutor-live]"); return a && !a.hidden && a.textContent.length > 20; });
  assert.match(await pg.textContent("[data-tutor-live]"), /If it did not work/);
  await pg.click('[data-tutor-quick="What comes next?"]');
  await pg.waitForFunction(() => /Next is step|last step/.test(document.querySelector("[data-tutor-live]").textContent));
  await pg.fill("#tutor-q", "Where is the button?");
  await pg.locator("[data-tutor-ask] button").click();
  await pg.waitForFunction(() => /Go to/.test(document.querySelector("[data-tutor-live]").textContent));
  await shot(pg, "training-tutor");
  // Close: saved (minimized) after reloading and on the other training pages; the drawer starts closed everywhere.
  await closeTutor(pg);
  await pg.waitForFunction(() => document.querySelector("[data-tutor]").classList.contains("is-min"));
  await pg.reload();
  assert.ok(await pg.locator("[data-tutor]").evaluate((t) => t.classList.contains("is-min") && !t.classList.contains("is-open")), "still closed after reload");
  await pg.goto(`${base}/training`);
  assert.ok(await pg.locator("[data-tutor]").evaluate((t) => t.classList.contains("is-min")), "still closed on the home page");
  await openTutor(pg);
  await pg.keyboard.press("Escape");
  await pg.waitForFunction(() => !document.querySelector("[data-tutor]").classList.contains("is-open"));
  assert.equal(await pg.evaluate(() => document.activeElement?.hasAttribute("data-tutor-launch")), true, "Escape returns focus to Ask the Tutor");
  await pg.goto(`${base}/training/uat`);
  const first = await pg.locator("[data-uat-row] a").first().getAttribute("href");
  await pg.goto(`${base}${first}`);
  assert.equal(await pg.getAttribute("[data-tutor]", "data-tutor-mode"), "uat");
  await openTutor(pg);
  await pg.click('[data-tutor-quick="When is it a fail or blocked?"]');
  await pg.waitForFunction(() => /Blocked:/.test(document.querySelector("[data-tutor-live]").textContent));
  await pg.reload();
  assert.ok(await pg.locator("[data-tutor]").evaluate((t) => !t.classList.contains("is-min")), "opening is saved too");
});

test("a lesson completes only when its exercise is ticked; notes are kept", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/training/lessons/c01-sign-in`);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-complete]")]);
  assert.ok((await pg.content()).includes("Tick each step as you do it first"), "refused until every step is ticked");
  const steps = await pg.locator("[data-step-card]").count();
  for (let i = 0; i < steps; i += 1) {
    if (await pg.locator(`[data-tick="${i}"]`).getAttribute("aria-pressed") === "true") continue;
    await pg.click(`[data-tick="${i}"]`);
    await pg.waitForFunction((n) => document.querySelector(`[data-step-card="${n}"]`).classList.contains("is-done"), i);
  }
  await Promise.all([pg.waitForNavigation(), pg.click("[data-complete]")]);
  assert.ok((await pg.content()).includes("I did the practice exercise"), "refused without the exercise");
  await pg.check("[data-exercise]");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-complete]")]);
  await pg.goto(`${base}/training/lessons/c01-sign-in`);
  await pg.locator(".tc-notes summary").click();
  await pg.fill(".tc-notes textarea", "The sign-in page was clear (synthetic note).");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-save-note]")]);
  await pg.locator(".tc-notes summary").click();
  assert.ok(await pg.locator("[data-note]", { hasText: "The sign-in page was clear" }).isVisible());
  await pg.goto(`${base}/training`);
  assert.match(await pg.textContent("[data-progress]"), /^[1-9]\d* of \d+ lessons done/);
});

// Lesson status on the training home (24 Oct 2026): Completed with a green check and Review again, In Progress, the
// next recommended lesson highlighted; reviewing a completed lesson keeps it Completed.
async function lessonBadges(pg, label) {
  await pg.goto(`${base}/training`);
  const done = pg.locator('[data-lesson-row="c01-sign-in"]');
  assert.equal(await done.getAttribute("data-lesson-status"), "completed", `${label}: the finished lesson is Completed`);
  assert.equal((await done.locator("[data-lesson-state]").textContent()).trim(), "Completed");
  const box = await done.locator(".tc-lesson-box").evaluate((el) => [getComputedStyle(el).backgroundColor, el.textContent.trim()]);
  assert.deepEqual(box, ["rgb(47, 125, 74)", "\u2713"], `${label}: a green checked box`);
  assert.ok(await done.locator("[data-review-again]").isVisible(), `${label}: Review again is shown`);
  const started = pg.locator('[data-lesson-status="in-progress"]');
  assert.ok(await started.count() >= 1, `${label}: the started lesson is In Progress`);
  assert.equal((await started.first().locator("[data-lesson-state]").textContent()).trim(), "In Progress");
  const next = pg.locator("[data-next-recommended]");
  assert.equal(await next.count(), 1, `${label}: one next recommended lesson`);
  assert.ok(await next.locator("[data-next-badge]").isVisible());
  const key = await next.getAttribute("data-lesson-row");
  assert.ok((await pg.getAttribute("[data-continue]", "href")).includes(`/training/lessons/${key}`), `${label}: Next is where Continue goes`);
  assert.notEqual(await next.evaluate((el) => getComputedStyle(el).borderTopColor), "rgba(0, 0, 0, 0)", `${label}: Next is highlighted`);
  assert.match(await pg.locator('[data-module="c01"] [data-module-count-text]').textContent(), /^\d+ of \d+ lessons completed$/);
  assert.match(await pg.locator('[data-module="c01"] [data-module-summary]').textContent(), /in progress/);
  await noSideways(pg, `${label}: training home`);
  return { done, key };
}

test("training home: Completed, In Progress and Next; Review again keeps the lesson Completed (desktop)", async () => {
  const { pg } = sessions.ben;
  const { done, key } = await lessonBadges(pg, "desktop");
  await shot(pg, "training-home-progress-desktop");
  await Promise.all([pg.waitForNavigation(), done.locator("[data-review-again]").click()]);
  assert.ok(await pg.locator("[data-reviewing]").isVisible(), "the lesson says it is being reviewed");
  assert.equal(await pg.locator("[data-complete]").count(), 0, "no Finish button on a completed lesson");
  assert.ok(await pg.locator('[data-tick="0"]').isDisabled(), "ticks cannot be undone while reviewing");
  const last = (await pg.locator("[data-step-card]").count()) - 1;
  await pg.goto(`${base}/training/lessons/c01-sign-in?step=${last}`);
  await pg.locator(`[data-step-card="${last}"] .tc-step-head h2`).click();
  await Promise.all([pg.waitForNavigation(), pg.click("[data-exit]")]);
  assert.equal(await pg.getAttribute('[data-lesson-row="c01-sign-in"]', "data-lesson-status"), "completed", "still Completed after review");
  assert.equal(await pg.getAttribute("[data-next-recommended]", "data-lesson-row"), key, "Next is unchanged by the review");
});

test("training home: Completed, In Progress and Next on the phone (390 px), no sideways scrolling", async () => {
  const s = await context(PHONE);
  sessions.benPhone = s;
  const ben = facts.people.ben;
  await s.pg.goto(`${base}/login`);
  await s.pg.fill("input[name=email]", ben.email);
  await s.pg.fill("input[name=password]", ben.password);
  await Promise.all([s.pg.waitForNavigation(), s.pg.locator("form button[type=submit]").first().click()]);
  await lessonBadges(s.pg, "phone");
  const right = await s.pg.locator('[data-lesson-row="c01-sign-in"] [data-review-again]').evaluate((el) => el.getBoundingClientRect().right);
  assert.ok(right <= 390, "Review again fits the phone width");
  await shot(s.pg, "training-home-progress-phone");
  await s.pg.goto(`${base}/training/lessons/c01-sign-in`);
  await noSideways(s.pg, "reviewing a completed lesson (phone)");
});

test("acceptance tests: separate from lessons; Fail, then a retest Pass keeps the first result", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/training/uat`);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-uat-continue]")]);
  const key = await pg.getAttribute("[data-uat-case]", "data-uat-case");
  await pg.check('input[name=status][value="FAIL"]');
  await Promise.all([pg.waitForNavigation(), pg.click("[data-record]")]);
  assert.ok((await pg.content()).includes("Say what went wrong"), "a Fail needs the issue");
  await pg.check('input[name=status][value="FAIL"]');
  await pg.fill('textarea[name=issue]', "The password message did not appear (synthetic)");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-record]")]);
  await pg.goto(`${base}/training/uat/${key}`);
  await pg.check('input[name=status][value="PASS"]');
  await pg.fill('textarea[name=notes]', "Retested after the fix (synthetic)");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-record]")]);
  await pg.goto(`${base}/training/uat/${key}`);
  assert.equal(await pg.locator("[data-attempt]").count(), 2);
  assert.ok((await pg.content()).includes("The password message did not appear"));
  await shot(pg, "training-uat-case");
  await pg.goto(`${base}/training/uat`);
  assert.match(await pg.textContent("[data-uat-counts]"), /^1 passed/);
  await shot(pg, "training-uat-list");
});

test("field worker on an iPhone: Field lessons only, no sideways scrolling", async () => {
  const kevin = await signIn("kevin", PHONE);
  const page = await kevin.pg.content();
  // Field-only crew go straight into the Field Crew training (22 Oct 2026; the full walk is evidence_field_crew.mjs).
  assert.ok(page.includes("Start my Field Crew training") && !page.includes("Contractor owner"));
  await noSideways(kevin.pg, "register (phone)");
  await Promise.all([kevin.pg.waitForNavigation(), kevin.pg.click("[data-register]")]);
  await kevin.pg.waitForSelector("[data-progress]");
  assert.equal(await kevin.pg.locator('[data-module^="c"]').count(), 0, "no contractor modules for the crew");
  await noSideways(kevin.pg, "home (phone)");
  await shot(kevin.pg, "training-home-field-phone");
  for (const href of await kevin.pg.locator("a[data-lesson]").evaluateAll((as) => as.map((a) => a.getAttribute("href")))) {
    await kevin.pg.goto(`${base}${href}`);
    await noSideways(kevin.pg, href);
  }
  await openTutor(kevin.pg);
  await noSideways(kevin.pg, "lesson with the Tutor drawer open (phone)");
  await kevin.pg.click('[data-tutor-quick="Where is it?"]');
  await kevin.pg.waitForFunction(() => /Go to/.test(document.querySelector("[data-tutor-live]").textContent));
  await noSideways(kevin.pg, "lesson with the Tutor answer (phone)");
  await kevin.pg.goto(`${base}/training/uat`);
  await noSideways(kevin.pg, "acceptance tests (phone)");
  const r = await kevin.pg.goto(`${base}/training/admin`);
  assert.equal(r.status(), 403, "a field worker is not an administrator");
});

test("supplier signs in from the Training Centre and registers for supplier training", async () => {
  const darcy = await signIn("darcy", DESK);
  const page = await darcy.pg.content();
  for (const label of ["Supplier owner", "Supplier administrator", "PRO Desk staff"]) assert.ok(page.includes(label));
  assert.ok(!page.includes("Contractor owner"));
  await register(darcy, "Supplier administrator");
  assert.ok(await darcy.pg.locator('[data-module="s01"]').isVisible());
  assert.equal(await darcy.pg.locator('[data-module^="c"]').count(), 0, "no contractor modules for a supplier");
  await shot(darcy.pg, "training-home-supplier");
  const pat = await signIn("pat", PHONE);
  await register(pat, "PRO Desk staff");
  await noSideways(pat.pg, "supplier home (phone)");
});

test("administrator dashboard: Ben sees his company and BMR's trainees; others are refused", async () => {
  const kevinCase = await sessions.kevin.pg.goto(`${base}/training/uat`);
  assert.equal(kevinCase.status(), 200);
  const first = await sessions.kevin.pg.locator("[data-uat-row] a").first().getAttribute("href");
  await sessions.kevin.pg.goto(`${base}${first}`);
  await sessions.kevin.pg.check('input[name=status][value="BLOCKED"]');
  await sessions.kevin.pg.fill('textarea[name=issue]', "No signal on site (synthetic)");
  await Promise.all([sessions.kevin.pg.waitForNavigation(), sessions.kevin.pg.click("[data-record]")]);
  const { pg } = sessions.ben;
  await pg.goto(`${base}/training`);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-admin-link]")]);
  const text = await pg.content();
  for (const who of ["Kevin Field", "Darcy", "Pat at the PRO Desk"]) assert.ok(text.includes(who), who);
  assert.ok(text.includes("No signal on site"), "the blocked test is an outstanding issue");
  await shot(pg, "training-admin");
  const r = await sessions.darcy.pg.goto(`${base}/training/admin`);
  assert.equal(r.status(), 403);
});

// One office training account on two pathways (Joel, 23 Oct 2026): Olivia (Office staff, not Field-only) takes a
// Contractor lesson and test, changes role to Field (Change my role), takes a Field Crew lesson and test, and changes
// back. Each pathway's progress and results are kept separately, and Ben's dashboard shows both.
async function finishFirstLesson(pg) {
  const href = await pg.locator("a[data-lesson]").first().getAttribute("href");
  await pg.goto(`${base}${href}`);
  const steps = await pg.locator("[data-step-card]").count();
  for (let i = 0; i < steps; i += 1) {
    await pg.click(`[data-tick="${i}"]`);
    await pg.waitForFunction((n) => document.querySelector(`[data-step-card="${n}"]`).classList.contains("is-done"), i);
  }
  await pg.check("[data-exercise]");
  await Promise.all([pg.waitForNavigation(), pg.click("[data-complete]")]);
  await pg.goto(`${base}/training`);
}
async function recordFirstTest(pg, status, issue) {
  await pg.goto(`${base}/training/uat`);
  const first = await pg.locator("[data-uat-row] a").first().getAttribute("href");
  await pg.goto(`${base}${first}`);
  await pg.check(`input[name=status][value="${status}"]`);
  if (issue) await pg.fill("textarea[name=issue]", issue);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-record]")]);
  await pg.goto(`${base}/training`);
}
async function changeRole({ pg }, role) {
  await pg.locator("details.tc-card summary", { hasText: "Change my role" }).click();
  await pg.check(`.tc-roles input[name=role][value="${role}"]`);
  await Promise.all([pg.waitForNavigation(), pg.locator(".tc-roles button[type=submit]").click()]);
  await pg.waitForSelector("[data-progress]");
}

test("one office trainee: Contractor, then Field (Change my role), then back; both records kept and on the dashboard", async () => {
  const olivia = await signIn("olivia", DESK);
  const { pg } = olivia;
  await register(olivia, "Office staff");
  assert.match(await pg.textContent('[data-module="c06"] [data-module-time]'), /^About \d+ minutes$/, "module time shown");
  assert.ok(await pg.locator('[data-module="c04"] [data-session="2"]').count(), "a long module is shown in sessions");
  await finishFirstLesson(pg);
  await recordFirstTest(pg, "PASS");
  const office = await pg.textContent("[data-progress]");
  assert.match(office, /^1 of \d+ lessons done .*1 passed, 0 failed/);
  await shot(pg, "training-home-office-times");
  await changeRole(olivia, "FIELD");
  assert.equal(await pg.locator('[data-module^="c"]').count(), 0, "Field: only the Field Crew lessons");
  assert.match(await pg.textContent("[data-progress]"), /^0 of 35 lessons done .*0 passed, 0 failed, 0 blocked/);
  await finishFirstLesson(pg);
  await recordFirstTest(pg, "FAIL", "Synthetic: the Field button was greyed out");
  assert.match(await pg.textContent("[data-progress]"), /^1 of 35 lessons done .*0 passed, 1 failed/);
  await changeRole(olivia, "OFFICE");
  assert.equal(await pg.textContent("[data-progress]"), office, "the Contractor record is exactly as it was");
  await changeRole(olivia, "FIELD");
  assert.match(await pg.textContent("[data-progress]"), /^1 of 35 lessons done .*0 passed, 1 failed/, "and the Field record");
  await changeRole(olivia, "OFFICE");
  const ben = sessions.ben.pg;
  await ben.goto(`${base}/training/admin`);
  const rows = ben.locator('tr[data-admin-trainee^="Olivia"]');
  assert.equal(await rows.count(), 2, "the dashboard shows both pathways");
  const contractor = ben.locator('tr[data-admin-trainee^="Olivia"][data-admin-track="CONTRACTOR"]');
  const field = ben.locator('tr[data-admin-trainee^="Olivia"][data-admin-track="FIELD_CREW"]');
  assert.equal(await contractor.getAttribute("data-admin-current"), "");
  assert.match(await contractor.textContent(), /1 pass · 0 fail/);
  assert.match(await field.textContent(), /1\/35[\s\S]*0 pass · 1 fail/);
  assert.match(await ben.textContent('[data-admin-crew-member^="Olivia"]'), /Lessons: 1 of 35 done/);
  assert.ok(await ben.locator("[data-admin-module-times]").isVisible(), "Module times on the dashboard");
  await shot(ben, "training-admin-two-pathways");
});

// Change training pathway in the header (24 Oct 2026): beside the account name, Office -> Field -> Office, each
// pathway's record kept; it works on the phone without sideways scrolling.
async function switchPathway(pg, role, label) {
  const sw = pg.locator("header [data-pathway-switch]");
  await sw.locator("summary").click();
  assert.ok(await sw.evaluate((d) => d.open), `${label}: the switch opens`);
  const btn = sw.locator(`[data-pathway="${role}"]`);
  assert.ok(await btn.isVisible(), `${label}: ${role} is offered`);
  const box = await btn.boundingBox();
  assert.ok(box.x >= 0 && box.x + box.width <= pg.viewportSize().width + 1, `${label}: the choice fits the screen`);
  await noSideways(pg, `${label}: switch open`);
  await Promise.all([pg.waitForNavigation(), btn.click()]);
}
test("Change training pathway in the header: Office -> Field -> Office on desktop and the phone (390 px)", async () => {
  const { pg } = sessions.olivia;
  await pg.goto(`${base}/training`);
  const summary = pg.locator("header [data-pathway-switch] summary");
  assert.match(await summary.textContent(), /Pathway: Contractor \(office\)/);
  const adjacent = await pg.locator("header [data-pathway-switch]").evaluate((d) => d.nextElementSibling?.classList.contains("tc-who"));
  assert.ok(adjacent, "the switch sits next to the account name");
  const office = await pg.textContent("[data-progress]");
  const s = await context(PHONE);
  sessions.oliviaPhone = s;
  await s.pg.goto(`${base}/login`);
  await s.pg.fill("input[name=email]", facts.people.olivia.email);
  await s.pg.fill("input[name=password]", facts.people.olivia.password);
  await Promise.all([s.pg.waitForNavigation(), s.pg.locator("form button[type=submit]").first().click()]);
  await s.pg.goto(`${base}/training`);
  await noSideways(s.pg, "phone home with the switch");
  await switchPathway(s.pg, "FIELD", "phone");
  assert.match(await s.pg.textContent("header [data-pathway-switch] summary"), /Pathway: Field Crew/);
  assert.match(await s.pg.textContent("main"), /You are now on Field Crew training/);
  assert.equal(await s.pg.locator('[data-module^="c"]').count(), 0, "Field: only the Field Crew lessons");
  assert.match(await s.pg.textContent("[data-progress]"), /^1 of 35 lessons done .*0 passed, 1 failed/, "the Field record is kept");
  await noSideways(s.pg, "phone home on Field Crew");
  await switchPathway(s.pg, "OFFICE", "phone");
  assert.match(await s.pg.textContent("header [data-pathway-switch] summary"), /Pathway: Contractor \(office\)/);
  assert.equal(await s.pg.textContent("[data-progress]"), office, "the Contractor record is exactly as it was");
  await noSideways(s.pg, "phone home back on Office");
});

test("the training site says so on every workspace and links to the Centre", async () => {
  const { pg } = sessions.ben;
  await pg.goto(`${base}/`);
  assert.ok(await pg.locator("[data-training-site]").isVisible());
  assert.match(await pg.textContent("[data-training-link]"), /Back to my training/);
  await Promise.all([pg.waitForNavigation(), pg.click("[data-training-link]")]);
  assert.match(new URL(pg.url()).pathname, /^\/training$/);
  await sessions.darcy.pg.goto(`${base}/supplier/`);
  assert.ok(await sessions.darcy.pg.locator("[data-training-site]").isVisible());
  await sessions.kevin.pg.goto(`${base}/field/today`);
  assert.ok(await sessions.kevin.pg.locator("[data-training-site]").isVisible());
  await noSideways(sessions.kevin.pg, "Field Today with the training bar (phone)");
});
