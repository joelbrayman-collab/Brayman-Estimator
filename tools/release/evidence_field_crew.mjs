// Release evidence for the Field Crew training (Joel, 22 Oct 2026): the Training Centre's third pathway, walked
// in a real browser on an iPhone-sized screen (390 x 844, touch) against a local training site
// (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on, the synthetic training company).
// Synthetic data only.
//
// Kevin (Field only) chooses "I work on a crew (Field)", signs in and registers straight into the Field Crew
// training (nothing else offered); ticks steps (they turn green and stay after a reload); Save and exit, then
// Continue where I left off; the screenshot opens full size; the Tutor answers, minimizes and restores (kept
// across pages); every Field Crew lesson and test has no sideways scrolling and no money, and every picture
// loads; a Field acceptance test fails (the issue is required), then a retest passes and both attempts are
// kept; the Workflow Map's Field section carries his lessons, from the Training Centre and from Field's Guide;
// the Field pages fit the phone; Ben's administrator dashboard shows Kevin with the blocked test flagged, also
// on an iPhone; Kevin cannot open it. Any response of 500 or more, or a page JavaScript error, fails the walk.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test --test-concurrency=1 tools/release/evidence_field_crew.mjs
// EVIDENCE_SHOTS=<folder> saves a full-page screenshot of each screen.
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
const MONEY = /\$\s?\d|\bprice|\bpricing|\bcost|margin|markup|estimate|invoice|\bquote/i;
const serverErrors = [];
const pageErrors = [];
const S = {};

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
  for (const s of Object.values(S)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`FIELD_CREW_SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

async function context(viewport) {
  const phone = viewport.width <= 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
}
async function go(pg, url) { const r = await pg.goto(`${base}${url}`); await pg.waitForLoadState(); return r; }
async function nav(pg, locator) { await Promise.all([pg.waitForNavigation(), locator.click()]); await pg.waitForLoadState(); }
async function shot(pg, name) {
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
}
async function noSideways(pg, label) {
  const [sw, iw] = await pg.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  assert.ok(sw <= iw + 1, `${label}: page scrolls sideways (${sw} > ${iw})`);
}
async function noMoney(pg, label) {
  const text = await pg.locator("main").innerText();
  assert.doesNotMatch(text, MONEY, `${label}: money words on a Field Crew page`);
}
async function signInKevin() {
  const s = await context(PHONE);
  await go(s.pg, "/training");
  assert.match(new URL(s.pg.url()).pathname, /\/training\/signin$/);
  assert.equal(await s.pg.locator("[data-signin]").count(), 3, "three groups on the sign-in page");
  await noSideways(s.pg, "training sign-in (phone)");
  await shot(s.pg, "field-crew-signin");
  await nav(s.pg, s.pg.locator('[data-signin="field"]'));
  await s.pg.fill("input[name=email]", facts.people.kevin.email);
  await s.pg.fill("input[name=password]", facts.people.kevin.password);
  await nav(s.pg, s.pg.locator("form button[type=submit]").first());
  assert.match(new URL(s.pg.url()).pathname, /^\/training$/, "Kevin comes back to the Training Centre");
  return s;
}

test("Kevin chooses the crew, signs in and registers straight into the Field Crew training", async () => {
  S.kevin = await signInKevin();
  const { pg } = S.kevin;
  const reg = await pg.locator("main").innerText();
  assert.match(reg, /Start my Field Crew training/);
  assert.doesNotMatch(reg, /Contractor owner|Office staff|Supplier owner|PRO Desk/);
  assert.equal(await pg.locator("input[type=radio][name=role]").count(), 0, "no role to choose: Field Crew only");
  await noSideways(pg, "register (phone)");
  await shot(pg, "field-crew-register");
  await nav(pg, pg.locator("[data-register]"));
  const modules = await pg.locator("[data-module]").evaluateAll((els) => els.map((e) => e.getAttribute("data-module")));
  assert.deepEqual(modules, ["f01", "f02", "f03", "f04", "f05", "f06", "f07", "f08"]);
  assert.match(await pg.textContent("[data-track]"), /Field Crew training/);
  assert.equal(await pg.locator("[data-open-field]").getAttribute("href"), "/field/today");
  await noSideways(pg, "Field Crew home (phone)");
  await shot(pg, "field-crew-home");
});

test("ticked steps turn green and are saved; Save and exit, then Continue where I left off; picture full size", async () => {
  const { pg } = S.kevin;
  await nav(pg, pg.locator("[data-continue]"));
  const lesson = await pg.getAttribute("[data-lesson-page]", "data-lesson-page");
  assert.equal(lesson, "f01-start-training");
  const total = await pg.locator("[data-step-card]").count();
  for (const i of [0, 1]) {
    await pg.click(`[data-tick="${i}"]`);
    await pg.waitForFunction((n) => document.querySelector(`[data-step-card="${n}"]`).classList.contains("is-done"), i);
  }
  const green = await pg.locator('[data-step-card="0"] .tc-check').evaluate((el) => getComputedStyle(el).backgroundColor);
  assert.equal(green, "rgb(47, 125, 74)", "the ticked step turns green");
  assert.match(await pg.textContent("[data-stepcount]"), new RegExp(`^2 of ${total} steps done`));
  await noSideways(pg, "lesson with ticks (phone)");
  await pg.reload();
  assert.equal(await pg.locator(".tc-step-card.is-done").count(), 2, "the ticks are saved");
  await pg.locator("[data-enlarge]").first().click();
  assert.ok(await pg.locator("[data-lightbox]").evaluate((d) => d.open), "the picture opens full size");
  await pg.locator("[data-lightbox] button").click();
  await shot(pg, "field-crew-lesson");
  await nav(pg, pg.locator("[data-exit]"));
  assert.match(new URL(pg.url()).pathname, /^\/training$/);
  assert.match(await pg.locator(".tc-flash").first().innerText(), /Saved/);
  const href = await pg.getAttribute("[data-continue]", "href");
  assert.equal(href, `/training/lessons/${lesson}?step=2`, "Continue returns to the first step not ticked");
  await nav(pg, pg.locator("[data-continue]"));
  assert.equal(await pg.locator(".tc-step-card.is-done").count(), 2);
  assert.ok(await pg.locator('[data-step-card="2"]').evaluate((c) => c.classList.contains("is-current")));
  // Next lesson and back.
  await nav(pg, pg.locator("[data-next-lesson]"));
  assert.equal(await pg.getAttribute("[data-lesson-page]", "data-lesson-page"), "f01-activate");
  await nav(pg, pg.locator("[data-prev-lesson]"));
  assert.equal(await pg.getAttribute("[data-lesson-page]", "data-lesson-page"), lesson);
});

test("the Tutor answers from the Field Crew step, minimizes and restores, kept across pages", async () => {
  const { pg } = S.kevin;
  await go(pg, "/training/lessons/f05-send-time");
  await pg.locator('[data-step-card="1"] .tc-step-head h2').click();
  assert.match(await pg.textContent("[data-tutor-title]"), /Pick the work/);
  await pg.click('[data-tutor-quick="It didn\'t work"]');
  await pg.waitForFunction(() => /Work not found/.test(document.querySelector("[data-tutor-live]")?.textContent || ""));
  await pg.click('[data-tutor-quick="What do I type?"]');
  await pg.waitForFunction(() => /Framing and decking/.test(document.querySelector("[data-tutor-live]").textContent));
  await noSideways(pg, "lesson with a Tutor answer (phone)");
  await shot(pg, "field-crew-tutor");
  await pg.click("[data-tutor-button]");
  await pg.waitForFunction(() => document.querySelector("[data-tutor]").classList.contains("is-min"));
  await pg.reload();
  assert.ok(await pg.locator("[data-tutor]").evaluate((t) => t.classList.contains("is-min")), "minimized after a reload");
  await go(pg, "/training");
  assert.ok(await pg.locator("[data-tutor]").evaluate((t) => t.classList.contains("is-min")), "minimized on the home page");
  assert.equal(await pg.textContent("[data-tutor-button]"), "Open the Tutor");
  await pg.click("[data-tutor-button]");
  await pg.waitForFunction(() => !document.querySelector("[data-tutor]").classList.contains("is-min"));
  await go(pg, "/training/lessons/f05-send-time");
  assert.ok(!(await pg.locator("[data-tutor]").evaluate((t) => t.classList.contains("is-min"))), "restored everywhere");
});

test("every Field Crew lesson fits the iPhone, shows no money, and every picture loads", async () => {
  const { pg } = S.kevin;
  await go(pg, "/training");
  const hrefs = await pg.locator("a[data-lesson]").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  assert.equal(hrefs.length, 24);
  for (const href of hrefs) {
    assert.match(href, /^\/training\/lessons\/f0[1-8]-/);
    await go(pg, href.split("?")[0]);
    await noSideways(pg, href);
    await noMoney(pg, href);
    const broken = await pg.locator(".tc-shot img").evaluateAll(async (imgs) => {
      for (const img of imgs) { img.loading = "eager"; if (!img.complete) await new Promise((r) => { img.onload = img.onerror = r; }); }
      return imgs.filter((img) => !img.naturalWidth).map((img) => img.src);
    });
    assert.deepEqual(broken, [], `${href}: pictures load`);
    const links = await pg.locator("main a[href]").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    for (const l of links) assert.match(l, /^(\/training|\/field|#)/, `${href}: ${l} is not a Field Crew link`);
  }
});

test("a Field acceptance test fails, then a retest passes; both attempts are kept, apart from the lessons", async () => {
  const { pg } = S.kevin;
  await go(pg, "/training/uat");
  assert.match(await pg.textContent("[data-uat-counts]"), /0 passed · 0 failed · 0 blocked · 14 not tested, of 14/);
  await noSideways(pg, "acceptance tests (phone)");
  await nav(pg, pg.locator("[data-uat-continue]"));
  const key = await pg.getAttribute("[data-uat-case]", "data-uat-case");
  assert.match(key, /^uat-f0/);
  await pg.check('input[name=status][value="FAIL"]');
  await nav(pg, pg.locator("[data-record]"));
  assert.match(await pg.locator("main").innerText(), /Say what went wrong/);
  await pg.check('input[name=status][value="FAIL"]');
  await pg.fill("textarea[name=issue]", "The sign-in sent me to my training, not Field (synthetic)");
  await pg.fill("textarea[name=notes]", "iPhone, Safari (synthetic)");
  await nav(pg, pg.locator("[data-record]"));
  // Saved: the list opens with the result beside the test. The next test: Blocked (Ben will see it flagged).
  assert.match(new URL(pg.url()).pathname, /^\/training\/uat$/);
  assert.match(await pg.locator(`[data-uat-row="${key}"]`).innerText(), /Fail · retest/);
  await nav(pg, pg.locator("[data-uat-row] a").nth(1));
  const second = await pg.getAttribute("[data-uat-case]", "data-uat-case");
  assert.notEqual(second, key);
  await pg.check('input[name=status][value="BLOCKED"]');
  await pg.fill("textarea[name=issue]", "No signal on site (synthetic)");
  await nav(pg, pg.locator("[data-record]"));
  // Retest the failed one after the fix.
  await go(pg, `/training/uat/${key}`);
  await pg.check('input[name=status][value="PASS"]');
  await pg.fill("textarea[name=notes]", "Retested after the fix (synthetic)");
  await nav(pg, pg.locator("[data-record]"));
  await go(pg, `/training/uat/${key}`);
  assert.equal(await pg.locator("[data-attempt]").count(), 2, "the retest is a new attempt");
  assert.match(await pg.locator("main").innerText(), /The sign-in sent me to my training, not Field/);
  await noSideways(pg, "test with two attempts (phone)");
  await shot(pg, "field-crew-uat-case");
  await go(pg, "/training/uat");
  assert.match(await pg.textContent("[data-uat-counts]"), /^1 passed · 0 failed · 1 blocked · 12 not tested/);
  await go(pg, "/training");
  assert.match(await pg.textContent("[data-progress]"), /^0 of 24 lessons done .* 1 passed, 0 failed, 1 blocked/);
});

test("the Workflow Map's Field section carries the Field Crew lessons, in training and on Field's Guide", async () => {
  const { pg } = S.kevin;
  await go(pg, "/training/lessons/f04-drawings");
  await nav(pg, pg.locator("[data-lesson-stage]").first());
  assert.match(pg.url(), /\/training\/workflow\?stage=f-job/);
  const html = await pg.content();
  for (const label of ["SIGN IN", "TODAY", "ON THE JOB", "CAPTURE", "TIME"]) assert.ok(html.includes(label), label);
  assert.ok(html.includes("/training/lessons/f04-drawings") && !html.includes("/training/lessons/c"));
  await noSideways(pg, "training Workflow map (phone)");
  await shot(pg, "field-crew-workflow");
  await go(pg, "/field/workflow");
  const guide = await pg.content();
  assert.ok(guide.includes("/training/lessons/f06-capture"), "Field's Guide links to the Field Crew lessons");
  await noSideways(pg, "Field Guide (phone)");
});

test("Field itself fits the iPhone and shows no money", async () => {
  const { pg } = S.kevin;
  await go(pg, "/training");
  await nav(pg, pg.locator("[data-open-field]"));
  assert.match(new URL(pg.url()).pathname, /^\/field\/today$/);
  for (const url of ["/field/today", "/field/week", "/field/month", "/field/company-today", "/field/projects",
    "/field/time", "/account/password"]) {
    await go(pg, url);
    await noSideways(pg, url);
    assert.doesNotMatch(await pg.locator("body").innerText(), MONEY, `${url}: money on Field`);
  }
  for (const url of ["/projects/", "/accounting", "/settings/people"]) {
    await go(pg, url);
    assert.match(new URL(pg.url()).pathname, /^\/field\/today$/, `${url} sends the crew back to Field Today`);
  }
});

test("Ben's administrator dashboard shows Kevin's Field Crew progress with the blocked test flagged", async () => {
  const r = await S.kevin.pg.goto(`${base}/training/admin`);
  assert.equal(r.status(), 403, "the crew are not administrators");
  for (const [key, viewport] of [["ben", DESK], ["benPhone", PHONE]]) {
    const s = await context(viewport);
    S[key] = s;
    await go(s.pg, "/login");
    await s.pg.fill("input[name=email]", facts.people.ben.email);
    await s.pg.fill("input[name=password]", facts.people.ben.password);
    await nav(s.pg, s.pg.locator("form button[type=submit]").first());
    await go(s.pg, "/training/admin");
    const card = s.pg.locator('[data-admin-crew-member="Kevin Field (training crew)"]');
    assert.ok(await card.isVisible(), "Kevin is in Ben's crew");
    const text = await card.innerText();
    assert.match(text, /Lessons: 0 of 24 done/);
    assert.match(text, /1 pass · 0 fail · 1 blocked · 12 to do · 1 retested/);
    assert.match(text, /Issues to fix/);
    assert.equal(await card.locator("[data-flag]").count(), 1, "the blocked test is flagged; the retested one is not");
    assert.match(await card.locator("[data-flag]").innerText(), /No signal on site/);
    if (viewport === PHONE) await noSideways(s.pg, "administrator dashboard (phone)");
    await shot(s.pg, `field-crew-admin-${viewport.width}`);
  }
  await go(S.ben.pg, "/training/review/field-crew");
  assert.equal(await S.ben.pg.locator("[data-review-lesson-link]").count(), 24, "the owner previews all 24 lessons");
});
