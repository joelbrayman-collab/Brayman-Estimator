// Release evidence for the Calendar (Joel, 19 Oct 2026): My Calendar | Company Calendar, hourly Day and Week,
// Print from one date to another and the tighter header (23 Oct 2026),
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
    // Header clean-up (Joel, 23 Oct 2026): the switch is in the top bar in place of the title; the heading
    // stays for screen readers.
    assert.equal((await pg.locator(".header-page-title").textContent()).trim(), "My Calendar");
    assert.equal(await pg.locator(".shell-header [data-scope-switch] a").count(), 2);
    assert.ok(await pg.locator(".shell-header [data-scope-switch]").isVisible());
    const navLabels = (await pg.locator('a.sidebar-link[href="/schedule"] .sidebar-link-label').allTextContents()).map((s) => s.trim());
    assert.deepEqual(navLabels, ["Calendar"]);
    assert.equal((await pg.locator(".cal-scope a[aria-current=page]").innerText()).trim(), "My Calendar");
    await pg.click(".cal-scope a[data-scope=company]");
    await pg.waitForLoadState();
    assert.equal((await pg.locator(".header-page-title").textContent()).trim(), "Company Calendar");
    assert.ok(pg.url().includes("view=week") && pg.url().includes("scope=company"), pg.url());
    await noSideways(pg, label);
    assert.deepEqual(errors, []);
    await ctx.close();
  });

  test(`${label}: an empty day scrolls through all 24 hours, opens at 7 AM, and every half hour starts an appointment`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.empty_day)}&view=day`);
    const labels = (await pg.locator(".cal-hour-label").allInnerTexts()).map((s) => s.trim());
    assert.equal(labels[0], "12 AM"); assert.equal(labels.at(-1), "11 PM"); assert.equal(labels.length, 24);
    assert.equal(await pg.locator(".cal-hours-body .cal-appt").count(), 0);
    // About 11 hours on screen, opening at 7 AM; 5 AM and 11 PM are a scroll away (Joel, 20 Oct 2026).
    const body = pg.locator(".cal-hours-body");
    const box = await body.evaluate((el) => ({ top: el.scrollTop, view: el.clientHeight, all: el.scrollHeight }));
    const hour = box.all / 24;
    assert.ok(Math.abs(box.top - 7 * hour) <= 2, JSON.stringify(box));
    assert.ok(box.view <= 11 * hour + 2 && box.view >= 6 * hour, JSON.stringify(box));
    await body.evaluate((el) => { el.scrollTop = 0; });
    assert.ok(await pg.locator(`[data-slot="${facts.empty_day}T05:00"]`).isVisible());
    await body.evaluate((el) => { el.scrollTop = el.scrollHeight; });
    assert.ok(await pg.locator(`[data-slot="${facts.empty_day}T23:30"]`).isVisible());
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

for (const [label, width, height] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
  test(`${label}: the month view scrolls across months with a sticky month heading`, async () => {
    // Joel, 20 Oct 2026: scroll through months instead of clicking; the month in view must be
    // immediately identifiable, so each month opens with a heading that stays at the top.
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?${at(facts.monday)}&view=month&scope=company`);
    const box = pg.locator("[data-month-scroll]");
    const topHeading = () => box.evaluate((el) => {
      const r = el.getBoundingClientRect();
      const stuck = [...el.querySelectorAll(".cal-month-band")].filter((b) => Math.abs(b.getBoundingClientRect().top - r.top) < 2);
      return stuck.length ? stuck[stuck.length - 1].textContent.trim() : "";  // the last one is drawn on top
    });
    const title = () => pg.locator("[data-month-title-live]").innerText().then((t) => t.trim());
    const opened = await box.evaluate((el) => ({ top: el.scrollTop, view: el.clientHeight, all: el.scrollHeight }));
    assert.ok(opened.all > opened.view * 4, JSON.stringify(opened));  // months above and below
    const first = await title();
    assert.equal(await topHeading(), first);  // opens on this month, its heading at the top
    // Cross into the next month: its heading takes the top and the page title follows.
    await box.evaluate((el) => { const s = el.querySelectorAll(".home-week[data-month-anchor]")[4]; el.scrollTop = s.offsetTop + 40; });
    await pg.waitForFunction((t) => document.querySelector("[data-month-title-live]").textContent.trim() !== t, first);
    const next = await title();
    assert.notEqual(next, first);
    assert.match(next, /^[A-Z][a-z]+ 20\d\d$/);
    assert.equal(await topHeading(), next);
    // Back up a little: the earlier month's heading returns.
    await box.evaluate((el) => { const s = el.querySelectorAll(".home-week[data-month-anchor]")[4]; const b = el.querySelector(".cal-month-band").offsetHeight; el.scrollTop = s.offsetTop - b - 200; });
    await pg.waitForFunction((t) => document.querySelector("[data-month-title-live]").textContent.trim() === t, first);
    assert.equal(await topHeading(), first);
    await box.evaluate((el) => { el.scrollTop = 0; });
    assert.equal(await pg.locator("[data-month-earlier]").isVisible(), true);
    await noSideways(pg, `${label} month`);
    assert.deepEqual(errors, []);
    await ctx.close();
  });
}

// Print from one date to another (Joel, 23 Oct 2026).
const addDays = (iso, n) => { const d = new Date(`${iso}T12:00:00Z`); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); };
for (const [label, width, height] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
  test(`${label}: Print opens From / To on the week shown and prints that range, day by day`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    const failed = [];
    pg.on("response", (r) => { if (r.status() >= 500) failed.push(`${r.status()} ${r.url()}`); });
    await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week&scope=company`);
    await pg.locator("[data-print-control] > summary").click();
    const form = pg.locator("[data-print-open-form]");
    assert.equal(await form.locator("[name=from]").inputValue(), facts.monday);
    assert.equal(await form.locator("[name=to]").inputValue(), addDays(facts.monday, 6));
    await noSideways(pg, `${label} print form open`);
    await form.locator("[name=to]").fill(addDays(facts.monday, 13));
    await Promise.all([pg.waitForURL(/\/schedule\/print\?/), form.getByRole("button", { name: "Print" }).click()]);
    const text = await pg.locator("[data-calendar-print]").innerText();
    for (const t of ["Slab pour", "Wall framing", "Site visit — new client", "Weekly office meeting", "Printed on", "Company Calendar"]) assert.ok(text.includes(t), t);
    for (const t of ["Kevin dentist", "Lunch with accountant"]) assert.ok(!text.includes(t), t);
    assert.equal(await pg.locator("[data-print-day]").count(), 14);
    assert.equal(await pg.locator(`[data-print-day="${facts.empty_day}"]`).innerText().then((t) => t.includes("No scheduled work")), true);
    assert.ok(await pg.locator("[data-print-now]").isVisible());
    await noSideways(pg, `${label} printout`);
    // On paper: no menu, top bar, Cal or buttons.
    await pg.emulateMedia({ media: "print" });
    for (const sel of [".shell-sidebar", ".shell-header", "[data-print-now]", "[data-print-form]", "[data-print-back]"]) {
      assert.equal(await pg.locator(sel).first().isVisible(), false, `${sel} prints`);
    }
    await pg.emulateMedia({ media: "screen" });
    // A To before the From: the form again with a plain message, never a server error.
    await pg.goto(`${base}/schedule/print?scope=company&from=${addDays(facts.monday, 5)}&to=${facts.monday}`);
    assert.match(await pg.locator("[data-print-message]").innerText(), /From date must be on or before the To date/);
    await noSideways(pg, `${label} print message`);
    await Promise.all([pg.waitForURL(/\/schedule(\?|$)/), pg.locator("[data-print-back]").click()]);
    assert.deepEqual(failed, []);
    assert.deepEqual(errors, []);
    await ctx.close();
  });
}

// Laptop screens (Joel, 23 Oct 2026): a whole five-week month (October 2026: Sep 28 – Nov 1) shows without
// scrolling, its heading and last week row on screen, with New Appointment and Print at the top right. Page
// viewports of 1440 x 900 and 1366 x 768 screens less the browser's own bars.
for (const [width, height] of [[1440, 800], [1366, 670]]) {
  test(`desktop ${width}x${height}: the whole month shows, heading to last week row; New Appointment and Print top right`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    await pg.goto(`${base}/schedule?year=2026&month=10&view=month`);
    const box = await pg.locator("[data-month-scroll]").boundingBox();
    const heading = await pg.locator('[data-month-band="2026-10"]').boundingBox();
    const last = await pg.locator('.home-week[data-week-start="2026-10-26"]').boundingBox();
    assert.ok(heading.y >= box.y - 1, JSON.stringify({ box, heading }));
    assert.ok(last.y + last.height <= box.y + box.height + 1, JSON.stringify({ box, last }));
    assert.ok(last.y + last.height <= height, `last week row ends at ${last.y + last.height} > ${height}`);
    const dayText = await pg.locator(".home-day-num").first().evaluate((el) => parseFloat(getComputedStyle(el).fontSize));
    assert.ok(dayText >= 14, `day numbers ${dayText}px`);
    const appt = await pg.locator(".cal-new-appt").boundingBox();
    const print = await pg.locator("[data-print-control] > summary").boundingBox();
    assert.ok(print.y >= appt.y + appt.height && print.y - (appt.y + appt.height) < 16, JSON.stringify({ appt, print }));
    assert.ok(Math.abs(print.x + print.width - (appt.x + appt.width)) <= 2, JSON.stringify({ appt, print }));
    const sw = await pg.locator(".shell-header [data-scope-switch]").boundingBox();
    assert.ok(sw && sw.y + sw.height <= 64, JSON.stringify(sw));
    await noSideways(pg, `${width} month`);
    assert.deepEqual(errors, []);
    await ctx.close();
  });
}

test("desktop: a busy day shows two entries and +N more, which opens the day with everything", async () => {
  const { ctx, pg, errors } = await signedIn(1440, 800);
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=month`);
  const more = pg.locator(`[data-more-day="${facts.monday}"]`);
  assert.equal((await more.innerText()).trim(), "+1 more");  // "+1" on a phone
  await Promise.all([pg.waitForURL(/view=day/), more.click()]);
  const text = await workspace(pg);
  for (const t of ["Slab pour", "Site visit — new client", "Meet supplier — BMR"]) assert.ok(text.includes(t), t);
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("desktop: Mon–Fri hides the weekend in Month and Week, marks weekend work, and is remembered", async () => {
  const { ctx, pg, errors } = await signedIn(1440, 800);
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=month`);
  const sw = pg.locator("[data-days-switch]");
  assert.ok(await sw.isVisible());
  assert.equal(await sw.locator('[data-days-choice="7"]').getAttribute("aria-pressed"), "true");  // Full week first
  const satCell = pg.locator(`.home-week[data-week-start="${facts.monday}"] .home-day.is-weekend`).first();
  const monCell = pg.locator(`.home-week[data-week-start="${facts.monday}"] .home-day`).first();
  const fullWidth = (await monCell.boundingBox()).width;
  assert.ok(await satCell.isVisible());
  const marker = pg.locator(`[data-weekend-marker="${facts.monday}"]`);
  assert.equal(await marker.isVisible(), false);
  await sw.locator('[data-days-choice="5"]').click();
  assert.equal(await satCell.isVisible(), false);
  assert.ok((await monCell.boundingBox()).width > fullWidth * 1.3, "weekday columns widen");
  assert.ok(await marker.isVisible());
  assert.match(await marker.innerText(), /Sat: 1 item/);
  await noSideways(pg, "Mon–Fri month");
  // Remembered: the week view opens in Mon–Fri, without Saturday and Sunday, with the weekend named.
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week`);
  assert.equal(await pg.locator(".cal-workspace").getAttribute("data-days"), "5");
  assert.equal(await pg.locator(".cal-hours-day:visible").count(), 5);
  assert.match(await pg.locator("[data-weekend-note]").innerText(), /Sat: 1 item/);
  await Promise.all([pg.waitForURL(/view=day/), pg.locator("[data-weekend-note] a").first().click()]);
  assert.ok((await workspace(pg)).includes("Saturday pour check"));
  // Back to Full week.
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=week`);
  await pg.locator('[data-days-choice="7"]').click();
  assert.equal(await pg.locator(".cal-hours-day:visible").count(), 7);
  assert.equal(await pg.locator("[data-weekend-note]").isVisible(), false);
  await pg.reload();
  assert.equal(await pg.locator(".cal-workspace").getAttribute("data-days"), "7");
  assert.deepEqual(errors, []);
  await ctx.close();
});

test("phone: Mon–Fri on the week list hides the weekend and names what it holds", async () => {
  const { ctx, pg, errors } = await signedIn(390, 844);
  await pg.goto(`${base}/schedule?${at(facts.monday)}`);
  await pg.locator('[data-days-choice="5"]').click();
  assert.equal(await pg.locator(".cal-week-view .cal-week-day:visible").count(), 5);
  assert.match(await pg.locator("[data-weekend-note]").innerText(), /Sat: 1 item/);
  await noSideways(pg, "phone Mon–Fri");
  await pg.goto(`${base}/schedule?${at(facts.monday)}&view=month`);
  assert.ok(await pg.locator(`[data-weekend-marker="${facts.monday}"]`).isVisible());
  await noSideways(pg, "phone Mon–Fri month");
  assert.deepEqual(errors, []);
  await ctx.close();
});

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
