// Release evidence for the Calendar (Joel, 19 Oct 2026): My Calendar | Company Calendar, hourly Day and Week,
// appointments, personal privacy, calendar feed. Google Chrome; a local office on a temporary database
// (tests/calendar_page_server.py), synthetic data only, dates relative to this week.
import assert from "node:assert/strict";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/calendar_page_server.py")], {
    cwd: REPO, env: { ...process.env, CALENDAR_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("calendar office did not start\n" + out)), 60000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("calendar office exited\n" + out)); }
      setTimeout(poll, 50);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => { await browser?.close(); server?.kill(); });

async function signedIn(width, height, email = "office@example.com", password = "office-test-password") {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  await pg.goto(`${base}/login`);
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await pg.click("button[type=submit]");
  await pg.waitForLoadState();
  return { ctx, pg, errors };
}
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
const workspace = (pg) => pg.locator(".cal-workspace").innerText();
const at = (iso) => { const [y, m, d] = iso.split("-").map(Number); return `year=${y}&month=${m}&day=${d}`; };

for (const [label, width, height] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
  test(`${label}: the sidebar says Calendar and it opens on My Calendar with the switch`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week`);
    assert.equal((await pg.locator(".header-page-title").innerText()).trim(), "My Calendar");
    const navLabels = (await pg.locator('a.sidebar-link[href="/schedule"] .sidebar-link-label').allTextContents()).map((s) => s.trim());
    assert.deepEqual(navLabels, ["Calendar"]);
    assert.equal((await pg.locator(".cal-scope a[aria-current=page]").innerText()).trim(), "My Calendar");
    await pg.click(".cal-scope a[data-scope=company]");
    await pg.waitForLoadState();
    assert.equal((await pg.locator(".header-page-title").innerText()).trim(), "Company Calendar");
    assert.ok(pg.url().includes("view=week") && pg.url().includes("scope=company"), pg.url());
    await noSideways(pg, label);
    assert.deepEqual(errors, []);
    await ctx.close();
  });

  test(`${label}: an empty day shows the hourly grid, 7 AM to 6 PM, and every half hour starts an appointment`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.empty_day)}&view=day`);
    const labels = (await pg.locator(".cal-hour-label").allInnerTexts()).map((s) => s.trim());
    assert.equal(labels[0], "7 AM"); assert.equal(labels.at(-1), "5 PM"); assert.equal(labels.length, 11);
    assert.equal(await pg.locator(".cal-hours-body .cal-appt").count(), 0);
    await pg.locator(`[data-slot="${facts.empty_day}T14:30"]`).click();
    await pg.waitForURL(/appointments\/new/);
    assert.equal(await pg.inputValue("[name=start_time]"), "14:30");
    assert.equal(await pg.inputValue("[name=end_time]"), "15:30");
    assert.ok(await pg.locator("input[name=visibility][value=PERSONAL]").isChecked(), "from My Calendar: Personal by default");
    await noSideways(pg, label);
    assert.deepEqual(errors, []);
    await ctx.close();
  });

  test(`${label}: My Calendar holds my appointments, my personal one and my crew's work, not others'`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week`);
    const text = await workspace(pg);
    for (const t of ["Site visit — new client", "Lunch with accountant", "Slab pour", "Deck framing"]) assert.ok(text.includes(t), t);
    for (const t of ["Wall framing", "Weekly office meeting", "Kevin dentist"]) assert.ok(!text.includes(t), t);
    await noSideways(pg, label);
    assert.deepEqual(errors, []);
    await ctx.close();
  });

  test(`${label}: Company Calendar holds all company work and company appointments, no personal ones`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week&scope=company`);
    const text = await workspace(pg);
    for (const t of ["Wall framing", "Weekly office meeting", "Site visit — new client"]) assert.ok(text.includes(t), t);
    for (const t of ["Kevin dentist", "Synthetic Clinic", "Lunch with accountant"]) assert.ok(!text.includes(t), t);
    await noSideways(pg, label);
    assert.deepEqual(errors, []);
    await ctx.close();
  });
}

test("desktop: overlapping appointments sit side by side on the company week", async () => {
  const { ctx, pg } = await signedIn(1280, 900);
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week&scope=company`);
  const a = await pg.locator(".cal-appt", { hasText: "Estimate consultation" }).boundingBox();
  const b = await pg.locator(".cal-appt", { hasText: "Weekly office meeting" }).boundingBox();
  assert.ok(a && b && a.x + a.width <= b.x + 2, JSON.stringify({ a, b }));
  await ctx.close();
});

test("desktop: add, reschedule and cancel an appointment, with its history", async () => {
  const { ctx, pg, errors } = await signedIn(1280, 900);
  await pg.goto(`${base}/schedule?${at(facts.empty_day)}&view=day`);
  await pg.locator(`[data-slot="${facts.empty_day}T10:00"]`).click();
  await pg.waitForURL(/appointments\/new/);
  await pg.check("input[name=visibility][value=COMPANY]");
  await pg.fill("[name=title]", "Release check appointment");
  await pg.click("button:has-text('Add appointment')");
  await pg.waitForURL(/view=day/);
  assert.equal(await pg.locator(".cal-appt", { hasText: "Release check appointment" }).count(), 1);
  await pg.locator(".cal-appt", { hasText: "Release check appointment" }).click();
  await pg.fill("[name=start_time]", "15:00"); await pg.fill("[name=end_time]", "16:00");
  await pg.click("button:has-text('Save appointment')");
  await pg.waitForURL(/view=day/);
  await pg.locator(".cal-appt", { hasText: "Release check appointment" }).click();
  assert.ok((await pg.locator("[data-appointment-history] summary").innerText()).includes("History (2)"));
  await pg.click("button:has-text('Cancel this appointment')");
  await pg.waitForURL(/view=day/);
  assert.equal(await pg.locator(".cal-appt", { hasText: "Release check appointment" }).count(), 0);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("personal appointments: only the owner sees them; others get not found", async () => {
  const owner = await signedIn(1280, 900, facts.kevin[0], facts.kevin[1]);
  await owner.pg.goto(`${base}/schedule?${at(facts.monday)}&view=week`);
  const link = owner.pg.locator(".cal-appt", { hasText: "Kevin dentist" }).first();
  assert.equal(await link.count(), 1);
  const href = (await link.getAttribute("href")).split("?")[0];
  await owner.ctx.close();
  const other = await signedIn(1280, 900);
  const res = await other.ctx.request.get(`${base}${href}`);
  assert.equal(res.status(), 404);
  assert.equal((await other.ctx.request.get(`${base}${href}/calendar.ics`)).status(), 404);
  await other.ctx.close();
});

test("calendar feed: shown once, fetched without signing in, stops when replaced", async () => {
  const { ctx, pg } = await signedIn(1280, 900);
  await pg.goto(`${base}/schedule/calendar-feed`);
  await pg.click("button:has-text('Turn on my calendar feed')");
  const first = await pg.inputValue("#feed-https");
  const anonymous = await browser.newContext();
  const body = await (await anonymous.request.get(first)).text();
  assert.ok(body.startsWith("BEGIN:VCALENDAR") && body.includes("Site visit") && !body.includes("Kevin dentist"));
  await pg.click("button:has-text('Make a new address')");
  assert.equal((await anonymous.request.get(first)).status(), 404);
  await anonymous.close(); await ctx.close();
});
