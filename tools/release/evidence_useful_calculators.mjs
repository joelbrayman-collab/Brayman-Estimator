// Release evidence for Useful Calculators (Joel, 22 Oct 2026): the phone dashboard and Home Screen app at
// /useful-calculators/, in a real browser on an iPhone-sized screen (390 x 844, touch) and a desktop, against the
// roles office (tests/roles_page_server.py: temporary database, synthetic owner, Field-only crew member Kevin,
// a priced estimate carrying internal cost, markup and notes). Synthetic data only.
//
// Checks: signed out the dashboard shows the public calculators and a sign-in; its own manifest (name, start_url,
// scope distinct from Field's), apple-touch-icon and apple-mobile-web-app-title; no service worker registered by
// it; the manifest's start page opens the dashboard; sign-in round trip back to the calculator; every calculator
// the person may use opens and calculates; Kevin (Field-only) sees no project, customer, cost, price or margin,
// the office cards say Office only, and the job calculators and office pages send him to Field; the owner reaches
// every calculator and the job calculators on the desktop; no sideways scrolling; Field's manifest, service
// worker and Home Screen metadata are unchanged; sign out returns to the public dashboard.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_useful_calculators.mjs
import assert from "node:assert/strict";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const CREW_CALCS = ["concrete", "footing", "wall-form", "stairs", "wall-framing", "roofing", "siding", "drywall", "flooring"];
const OFFICE_CALCS = ["employment", "supplier-model"];
const MONEY = [/\$\s?\d/, /\bprice/i, /\bcost/i, /margin/i, /markup/i, /invoice/i, /labour rate/i];
let browser, server, base, facts;
const serverErrors = [];
const sessions = {};

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/roles_page_server.py")], {
    cwd: REPO, env: { ...process.env, ROLES_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  // Kevin is crew: marked field-only by the operator command, as the roles walk does (tests/roles_operator.py).
  const marked = spawnSync(path.join(REPO, "venv/bin/python"),
    [path.join(REPO, "tests/roles_operator.py"), facts.database_uri, "mark-field-only", facts.kevin[0]], { cwd: REPO });
  assert.match(String(marked.stdout), /field_only: yes/, String(marked.stderr));
  browser = await launch();
});
after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`USEFUL_CALCULATORS SERVER_ERRORS=${serverErrors.length}`);
});

async function context(key, viewport) {
  const phone = viewport.width < 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  sessions[key] = { ctx, pg, errors };
  return sessions[key];
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
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}
async function noInternal(pg, label) {
  const text = await pg.locator("body").innerText();
  for (const m of MONEY) assert.doesNotMatch(text, m, `${label}: shows ${m}`);
  for (const v of Object.values(facts.internal)) assert.ok(!text.includes(v), `${label}: shows internal ${v}`);
  for (const v of [facts.org_b_client, facts.org_b_project, facts.customer[0], "Roles walk deck"]) {
    assert.ok(!text.includes(v), `${label}: shows ${v}`);
  }
}
async function homeScreenTags(pg) {
  return pg.evaluate(() => ({
    manifest: document.querySelector('link[rel="manifest"]')?.getAttribute("href"),
    title: document.querySelector('meta[name="apple-mobile-web-app-title"]')?.content,
    touch: document.querySelector('link[rel="apple-touch-icon"]')?.getAttribute("href"),
    capable: document.querySelector('meta[name="apple-mobile-web-app-capable"]')?.content,
  }));
}
async function useCalculator(pg, key) {
  if (key === "concrete") {
    // The redesigned calculator (release 8): Feet and inches is a radio choice; order in m³ or yd³.
    await pg.locator("#ms-imperial").check({ force: true });
    await pg.fill("#length", "20"); await pg.fill("#width", "10"); await pg.fill("#slab_thickness", "4");
    await pg.fill("#waste_percent", "0");
    await pg.locator("[data-concrete-calculator] button[type=submit]").click();
    await pg.locator("[data-concrete-result]:not([hidden])").waitFor();
    return pg.locator("[data-concrete-result]").innerText();
  }
  if (key === "stairs") {
    await pg.locator("[data-stair-calculator] *").first().waitFor();
    return pg.locator("[data-stair-calculator]").innerText();
  }
  if (key === "footing") {
    await pg.fill("#footing_length_1", "20"); await pg.fill("#footing_width_1", "2");
    await pg.fill("#footing_thickness_1", "8"); await pg.fill("#waste_percent", "0");
    await submit(pg, pg.locator('[data-trade-form] button[value="calculate"]'));
    const text = await pg.locator('[data-trade-result="footing"]').innerText();
    assert.match(text, /Concrete 0\.988 yd³/);
    return text;
  }
  return pg.locator("main").innerText();
}

test("iPhone, signed out: public calculators, a sign-in, its own Home Screen metadata, no service worker", async () => {
  const s = await context("anon", PHONE);
  const r = await go(s.pg, "/useful-calculators/");
  assert.equal(r.status(), 200);
  assert.equal(await s.pg.locator('[data-uc-dashboard="signed_out"]').count(), 1);
  const tags = await homeScreenTags(s.pg);
  assert.deepEqual(tags, { manifest: "/static/useful-calculators/manifest.webmanifest", title: "Useful Calculators",
                           touch: "/static/useful-calculators/useful-calculators-icon-180.png", capable: "yes" });
  const uc = await (await s.ctx.request.get(`${base}${tags.manifest}`)).json();
  const field = await (await s.ctx.request.get(`${base}/static/manifest.webmanifest`)).json();
  assert.equal(uc.name, "Useful Calculators");
  assert.equal(uc.scope, "/useful-calculators/");
  assert.ok(uc.start_url.startsWith("/useful-calculators/"));
  assert.deepEqual([field.name, field.start_url, field.scope, field.id], ["CalibraytAI", "/", "/", "/"]);
  for (const icon of [...uc.icons, { src: tags.touch }]) {
    const res = await s.ctx.request.get(`${base}${icon.src}`);
    assert.equal(res.status(), 200, icon.src);
    assert.equal(res.headers()["content-type"], "image/png");
  }
  const publicLinks = await s.pg.locator('[data-uc-state="public"]').evaluateAll((as) => as.map((a) => a.href));
  assert.deepEqual(publicLinks.sort(), ["https://calibraytai.com/employment-vs-entrepreneurship/",
                                        "https://calibraytai.com/useful-tools/concrete/", "https://calibraytai.com/useful-tools/stairs/"]);
  assert.equal(await s.pg.locator('[data-uc-state="sign_in"]').count(), 8);
  for (const p of ["/useful-calculators/wall-framing", "/useful-calculators/roofing", "/useful-calculators/wall-form"]) {
    await go(s.pg, p);
    assert.equal(pathOf(s.pg), "/useful-calculators/sign-in", `${p} needs a sign-in`);
  }
  await go(s.pg, "/useful-calculators/");
  await s.pg.waitForTimeout(300);
  assert.equal(await s.pg.evaluate("navigator.serviceWorker ? navigator.serviceWorker.getRegistrations().then(r => r.length) : 0"), 0);
  await noSideways(s.pg, "signed-out dashboard");
  // The manifest's start page opens the dashboard.
  await go(s.pg, uc.start_url);
  assert.equal(pathOf(s.pg), "/useful-calculators/");
  assert.deepEqual(s.errors, []);
});

test("iPhone, Field-only crew: sign in from a calculator and come straight back to it", async () => {
  const s = await context("kevin", PHONE);
  await go(s.pg, "/useful-calculators/footing");
  assert.equal(pathOf(s.pg), "/useful-calculators/sign-in");
  assert.equal(await s.pg.locator("[data-uc-sign-in-needed]").count(), 1);
  assert.equal((await homeScreenTags(s.pg)).title, "Useful Calculators");
  await s.pg.fill("input[name=email]", facts.kevin[0]);
  await s.pg.fill("input[name=password]", facts.kevin[1]);
  await submit(s.pg, s.pg.locator("[data-uc-sign-in-form] button[type=submit]"));
  assert.equal(pathOf(s.pg), "/useful-calculators/footing");
  await useCalculator(s.pg, "footing");
  await noSideways(s.pg, "footing result");
  await submit(s.pg, s.pg.locator("[data-uc-back]"));
  assert.equal(pathOf(s.pg), "/useful-calculators/");
  assert.equal(await s.pg.locator('[data-uc-dashboard="field_only"]').count(), 1);
  assert.deepEqual(s.errors, []);
});

test("iPhone, Field-only crew: every crew calculator opens and works; office ones are named, never linked", async () => {
  const s = sessions.kevin;
  await go(s.pg, "/useful-calculators/");
  await noInternal(s.pg, "crew dashboard");
  await noSideways(s.pg, "crew dashboard");
  for (const key of CREW_CALCS) {
    assert.equal(await s.pg.locator(`[data-uc-calc="${key}"][data-uc-state="open"]`).count(), 1, key);
  }
  for (const key of [...OFFICE_CALCS, "jobs"]) {
    const card = s.pg.locator(`[data-uc-calc="${key}"][data-uc-state="restricted"]`);
    assert.equal(await card.count(), 1, key);
    assert.equal(await card.evaluate((e) => e.tagName), "DIV", `${key} is not a link`);
    assert.match(await card.innerText(), /Office only/);
  }
  for (const key of CREW_CALCS) {
    await go(s.pg, "/useful-calculators/");
    await submit(s.pg, s.pg.locator(`[data-uc-calc="${key}"]`));
    assert.match(pathOf(s.pg), new RegExp(`^/useful-calculators/${key}$`));
    assert.equal(await s.pg.locator("[data-uc-back]").count(), 1, key);
    assert.equal(await s.pg.locator(".shell-sidebar, #shell-sidebar").count(), 0, `${key}: no office navigation`);
    await useCalculator(s.pg, key);
    assert.equal(await s.pg.locator("[data-link-project]").count(), 0, `${key}: no "Link to a project" for the crew`);
    await noSideways(s.pg, key);
    await noInternal(s.pg, key);
  }
  for (const p of ["/useful-calculators/projects", "/calculators/concrete", "/calculators/employment-vs-entrepreneurship",
                   "/supplier-program/economic-model", `/estimates/${facts.estimate_id}/versions/${facts.version_id}/calculations`,
                   `/projects/${facts.project_id}/deck-takeoff`, "/cost-library/", "/pricing-engine/"]) {
    await go(s.pg, p);
    assert.equal(pathOf(s.pg), "/field/today", `${p} sends the crew to Field`);
  }
  assert.deepEqual(s.errors, []);
});

test("iPhone, Field-only crew: reopening from the Home Screen start page keeps the session; Field is untouched", async () => {
  const s = sessions.kevin;
  const uc = await (await s.ctx.request.get(`${base}/static/useful-calculators/manifest.webmanifest`)).json();
  await go(s.pg, uc.start_url);
  assert.equal(await s.pg.locator('[data-uc-dashboard="field_only"]').count(), 1);
  await go(s.pg, "/field/today");
  const tags = await homeScreenTags(s.pg);
  assert.deepEqual(tags, { manifest: "/static/manifest.webmanifest", title: "CalibraytAI",
                           touch: "/static/branding/calibraytai-app-icon-180.png", capable: "yes" });
  const scopes = await s.pg.evaluate(async () => {
    const reg = await navigator.serviceWorker.ready;
    return [reg.scope, reg.active && new URL(reg.active.scriptURL).pathname];
  });
  assert.deepEqual(scopes, [`${base}/`, "/field-sw.js"]);
  assert.deepEqual(s.errors, []);
});

test("Desktop, owner: every calculator and the job calculators open in the right place", async () => {
  const s = await context("owner", DESK);
  await go(s.pg, "/useful-calculators/sign-in");
  await s.pg.fill("input[name=email]", facts.owner[0]);
  await s.pg.fill("input[name=password]", facts.owner[1]);
  await submit(s.pg, s.pg.locator("[data-uc-sign-in-form] button[type=submit]"));
  assert.equal(pathOf(s.pg), "/useful-calculators/");
  assert.equal(await s.pg.locator('[data-uc-dashboard="office"]').count(), 1);
  assert.equal(await s.pg.locator('[data-uc-state="restricted"]').count(), 0);
  await noSideways(s.pg, "office dashboard");
  const links = await s.pg.locator("a[data-uc-calc]").evaluateAll((as) => as.map((a) => [a.dataset.ucCalc, a.getAttribute("href"), a.target]));
  assert.deepEqual(links.map(([k]) => k).sort(), [...CREW_CALCS, ...OFFICE_CALCS, "jobs"].sort());
  for (const [key, href, target] of links) {
    const r = await go(s.pg, href);
    assert.equal(r.status(), 200, `${key} ${href}`);
    if (CREW_CALCS.includes(key)) {
      assert.equal(target, "", `${key} stays in the app`);
      await useCalculator(s.pg, key);
    }
    if (OFFICE_CALCS.includes(key)) assert.equal(target, "_blank", `${key} opens in the office`);
  }
  await go(s.pg, "/useful-calculators/projects");
  await s.pg.locator("[data-uc-job] summary").first().click();
  const tools = await s.pg.locator("[data-uc-tool]").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  assert.ok(tools.includes(`/estimates/${facts.estimate_id}/versions/${facts.version_id}/calculations`), "Add from calculation for the job");
  assert.ok(tools.includes(`/projects/${facts.project_id}/deck-takeoff`), "deck takeoff for the job");
  for (const href of [...new Set(tools)].slice(0, 16)) {
    const r = await go(s.pg, href);
    assert.equal(r.status(), 200, href);
  }
  assert.deepEqual(s.errors, []);
});

test("iPhone: sign out returns to the public dashboard", async () => {
  const s = sessions.kevin;
  await go(s.pg, "/useful-calculators/");
  await submit(s.pg, s.pg.locator("[data-uc-sign-out]"));
  assert.equal(pathOf(s.pg), "/useful-calculators/");
  assert.equal(await s.pg.locator('[data-uc-dashboard="signed_out"]').count(), 1);
  await go(s.pg, "/useful-calculators/concrete");
  assert.equal(pathOf(s.pg), "/useful-calculators/sign-in");
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
});
