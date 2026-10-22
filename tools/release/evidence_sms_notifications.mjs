// Release evidence for automatic schedule-change texts (Joel, 22 Oct 2026, mandatory V1). Kevin, a Field-only
// crew member on an iPhone-sized screen (390 x 844), answers Yes to the one-time question when he first opens
// Field (his number, saved by the office, filled in); Liam answers Not now and Field carries on. Ben, the owner, on a
// desktop, moves Kevin's work on the calendar, opens Text notices, sends the waiting notice and sees it with its
// status; Kevin's consent and its history show on Kevin's People & Access page. Kevin then stops texts. Real
// pages only, against a local office on a temporary database (tests/sms_notifications_server.py); texts go to a
// fake transport that writes them to a file (never Twilio, never a phone). Synthetic data only.
//
// Any response of 500 or more, or a page JavaScript error, fails the walk. Phone pages must not scroll sideways.
// The text never carries the customer's name, the project name, the street address or money.
//
// Run: EVIDENCE_REPO=$PWD node --test --test-concurrency=1 tools/release/evidence_sms_notifications.mjs
// EVIDENCE_SHOTS=<folder> saves desktop (1280 x 900) and phone (390 x 844) screenshots.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts, kevin, ben;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const saved = [];

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/sms_notifications_server.py")], {
    cwd: REPO, env: { ...process.env, SMS_NOTICES_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("sms office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("sms office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
  kevin = await context(PHONE, { isMobile: true, hasTouch: true });
  ben = await context(DESK);
});
after(async () => {
  for (const s of [kevin, ben]) await s?.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`SMS_NOTICES_SCREENS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

// Each step builds on the one before: once a step fails, the later steps are skipped.
let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function context(viewport, opts = {}) {
  const ctx = await browser.newContext({ viewport, ...opts });
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
async function signIn(s, [email, password]) {
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await submit(s.pg, s.pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(s.pg.url(), /\/login/, `${email} signs in`);
}
async function flash(pg) { return (await pg.locator(".flash, .alert, .field-flash, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function text(pg) { return pg.locator("body").innerText(); }
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function shot(pg, name) {
  const device = pg.viewportSize().width <= 500 ? "phone" : "desktop";
  if (device === "phone") await noSideways(pg, name);
  const file = `${name}-${device}.png`;
  saved.push(file);
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, file), fullPage: true });
}
function texts() {
  return fs.existsSync(facts.outbox)
    ? fs.readFileSync(facts.outbox, "utf8").trim().split("\n").filter(Boolean).map((l) => JSON.parse(l)) : [];
}
const day = (iso, plus) => new Date(Date.parse(iso + "T12:00:00Z") + plus * 864e5).toISOString().slice(0, 10);

// ------------------------------------------------------------------ the walk

step("1 Kevin opens Field on his iPhone for the first time: one question, his number filled in; he says Yes", async () => {
  await signIn(kevin, facts.kevin);
  const pg = kevin.pg;
  assert.match(pg.url(), /\/field\/today$/);
  const ask = pg.locator("[data-field-texts-setup]");
  assert.match(await ask.innerText(), /Get a text when your schedule changes\?/);
  assert.equal(await ask.locator("input[name=mobile_phone]").inputValue(), "+16135550142", "the office's number");
  assert.doesNotMatch(await text(pg), /Ben Brayman|Pat Synthetic|\$\s?\d/);
  await shot(pg, "01-field-setup-question");
  await submit(pg, pg.locator("[data-texts-setup-yes]"));
  assert.match(pg.url(), /\/field\/today$/);
  assert.match(await flash(pg), /Schedule texts are on/);
  assert.equal(await pg.locator("[data-field-texts-setup]").count(), 0, "asked once only");
  await noSideways(pg, "Field Today after Yes");
});

step("2 Kevin's Texts page shows his own setting: on, agreed at Field setup", async () => {
  const pg = kevin.pg;
  await submit(pg, pg.locator("[data-field-texts-link]"));
  assert.match(pg.url(), /\/field\/text-messages$/);
  assert.match(await pg.locator("[data-field-texts-status]").innerText(), /Texts are on for \+16135550142/);
  assert.match(await text(pg), /Texts turned on/);
  await shot(pg, "02-field-texts-on");
});

step("2b Liam answers Not now: Field opens normally and the question does not come back", async () => {
  const liam = await context(PHONE, { isMobile: true, hasTouch: true });
  try {
    await signIn(liam, facts.liam);
    const pg = liam.pg;
    await noSideways(pg, "Field Today with the question");
    await submit(pg, pg.locator("[data-texts-setup-no]"));
    assert.match(pg.url(), /\/field\/today$/);
    assert.match(await flash(pg), /turn them on any time under Texts/);
    await go(pg, "/field/week");
    await go(pg, "/field/today");
    assert.equal(await pg.locator("[data-field-texts-setup]").count(), 0);
    await go(pg, "/field/text-messages");
    assert.match(await pg.locator("[data-field-texts-status]").innerText(), /Texts are off/);
    await shot(pg, "02b-field-texts-not-now");
  } finally {
    await liam.ctx.close();
  }
});

step("3 Ben moves Kevin's work two days later on the desktop", async () => {
  await signIn(ben, facts.ben);
  const pg = ben.pg;
  await go(pg, `/schedule/items/${facts.item_id}`);
  const moved = day(facts.start, 2);
  await pg.fill("[name=scheduled_start]", moved);
  await pg.fill("[name=scheduled_end]", moved);
  await submit(pg, pg.getByRole("button", { name: "Save dates" }));
  assert.match(await flash(pg), /agreed to texts get one text about it in about 5 minutes/);
  assert.equal(texts().length, 0, "nothing is sent while the office may still be editing");
  await shot(pg, "03-calendar-after-move");
});

step("4 Ben opens Text notices from the calendar, sends the waiting notice and sees it Sent", async () => {
  const pg = ben.pg;
  await submit(pg, pg.locator("[data-text-notices-link]"));
  assert.match(pg.url(), /\/schedule\/text-notices$/);
  assert.equal(await pg.locator("[data-sms-waiting]").getAttribute("data-sms-waiting"), "1");
  await shot(pg, "04-text-notices-waiting");
  await submit(pg, pg.locator("[data-sms-send-now]"));
  assert.match(await flash(pg), /Waiting notices sent: 1 text/);
  const sent = texts();
  assert.equal(sent.length, 1);
  assert.equal(sent[0].to, "+16135550142");
  const body = sent[0].body;
  assert.match(body, /Footings \(synthetic\) \(Merrickville\) moved: .* -> /);
  assert.match(body, /Field: https:\/\/calibraytai\.example\.invalid\/field\/week/);
  for (const secret of [facts.client, facts.project, "7 Synthetic Lane", "$"]) assert.ok(!body.includes(secret), secret);
  const item = pg.locator("[data-sms-text]").first();
  assert.equal(await item.getAttribute("data-sms-status"), "SENT");
  assert.match(await item.innerText(), /Kevin Fieldhand \(synthetic\)[\s\S]*•••-0142[\s\S]*Sent/);
  assert.doesNotMatch(await text(pg), /613-555-0142|\+16135550142/, "office list shows only the last four digits");
  await shot(pg, "05-text-notices-sent");
});

step("5 Kevin's consent and its history show on his People & Access page", async () => {
  const pg = ben.pg;
  await go(pg, `/settings/people/${facts.kevin_membership_id}`);
  const section = pg.locator("[data-person-texts]");
  assert.equal(await section.getAttribute("data-person-texts"), "on");
  assert.match(await section.innerText(), /Texts turned on · by them at Field setup \(self, at Field setup\)/);
  await section.scrollIntoViewIfNeeded();
  await shot(pg, "06-people-access-texts");
});

step("6 Text notices also fits a phone; Kevin sees the new day on This week, then stops texts", async () => {
  const office = await context(PHONE, { isMobile: true, hasTouch: true });
  try {
    await signIn(office, facts.ben);
    await go(office.pg, "/schedule/text-notices");
    await shot(office.pg, "07-text-notices");
  } finally {
    await office.ctx.close();
  }
  const pg = kevin.pg;
  await go(pg, "/field/week");
  await noSideways(pg, "This week");
  await go(pg, "/field/text-messages");
  await submit(pg, pg.locator("[data-field-texts-stop]"));
  assert.match(await flash(pg), /Schedule texts are off/);
  assert.match(await text(pg), /Texts turned off/);
  await shot(pg, "08-field-texts-stopped");
  // Field only: the office's Text notices page is closed to Kevin.
  await go(pg, "/schedule/text-notices");
  assert.match(pg.url(), /\/field\/today$/);
});
