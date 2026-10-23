// Release evidence for Site Plans (Joel, 23 Oct 2026): the crew's Home Screen app and the office viewer at
// /site-plans/, in a real browser on an iPhone-sized screen (390 x 844, touch, iPhone Safari's user agent so the
// page-by-page layout is used) and a desktop, against tests/site_plans_page_server.py (temporary database,
// synthetic owner, Field-only crew member Kevin booked on Harbour Lane, Lee booked on nothing, a second job, a
// generated drawing set, a priced estimate, and another organization's project and plan). Synthetic data only.
//
// Checks: signed out, Site Plans goes to its own sign-in; its own manifest (name, start_url, scope distinct from
// Field's and Useful Calculators'), apple-touch-icon (180, opaque) and manifest icons with their sizes; Kevin signs
// in from the Home Screen start page and sees only his job; he opens its plans and a plan (every page, sheet
// numbers); Save for offline keeps the plans and they open with no signal; sign out removes them; another job's
// and another organization's plans never open and office pages send him to Field; the office project pages carry
// one plan button, "View project plan" (release 8: Site Plans' duplicate "Plans" button was removed), and the owner
// opens the Site Plans viewer from /site-plans/; no sideways scrolling; no 5xx.
// SITE_PLANS_SHOTS=<dir> also saves the screenshots (the Training Centre pictures and the release evidence).
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_site_plans.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import net from "node:net";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1";
const MONEY = [/\$\s?\d/, /\bprice/i, /\bcost/i, /margin/i, /markup/i, /invoice/i, /wage/i, /labour rate/i, /\bquote/i];
const SHOTS = process.env.SITE_PLANS_SHOTS || "";
let browser, server, base, facts, relay;
const serverErrors = [];
const sessions = {};

// "No signal": the browser reaches the office through this relay; switched off, every connection (the page's and
// the service worker's) fails at once, as on a phone with no signal. (context.setOffline does not reach a
// service worker's own requests.)
function startRelay(target) {
  const live = new Set();
  const state = { offline: false };
  const srv = net.createServer((socket) => {
    if (state.offline) { socket.destroy(); return; }
    const upstream = net.connect(target, "127.0.0.1");
    live.add(socket); live.add(upstream);
    const drop = () => { live.delete(socket); live.delete(upstream); socket.destroy(); upstream.destroy(); };
    socket.on("error", drop); upstream.on("error", drop); socket.on("close", drop); upstream.on("close", drop);
    socket.pipe(upstream); upstream.pipe(socket);
  });
  return {
    srv, state,
    listen: (port) => new Promise((resolve) => srv.listen(port, "127.0.0.1", resolve)),
    offline(on) { state.offline = on; if (on) for (const s of live) s.destroy(); },
  };
}

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/site_plans_page_server.py")], {
    cwd: REPO, env: { ...process.env, SITE_PLANS_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 120000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  relay = startRelay(port);
  const relayPort = await freePort();
  await relay.listen(relayPort);
  base = `http://127.0.0.1:${relayPort}`;
  if (SHOTS) fs.mkdirSync(SHOTS, { recursive: true });
  browser = await launch();
});
after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close(); server?.kill(); relay?.srv.close();
  console.log(`SITE_PLANS SERVER_ERRORS=${serverErrors.length}`);
});

async function context(key, viewport, { iphone = false } = {}) {
  const phone = viewport.width < 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}),
                                         ...(iphone ? { userAgent: IPHONE_UA } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  // While the relay is off, the 503/504 answers are the service worker's own "no signal" replies, not the office's.
  pg.on("response", (r) => { if (r.status() >= 500 && !relay.state.offline && !r.fromServiceWorker()) serverErrors.push(`${r.status()} ${r.url()}`); });
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
async function shot(pg, name) {
  if (SHOTS) await pg.screenshot({ path: path.join(SHOTS, name) });
}
const pathOf = (pg) => new URL(pg.url()).pathname;
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}
async function noMoneyOrContacts(pg, label) {
  const text = await pg.locator("body").innerText();
  for (const m of MONEY) assert.doesNotMatch(text, m, `${label}: shows ${m}`);
  for (const v of [facts.internal_cost, facts.customer[1], facts.customer[2], facts.org_b_project, facts.org_b_plan_name]) {
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
async function imageFacts(pg, src) {
  return pg.evaluate(async (u) => {
    const img = new Image();
    img.src = u;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    const x = c.getContext("2d");
    x.drawImage(img, 0, 0);
    const d = x.getImageData(0, 0, c.width, c.height).data;
    let minAlpha = 255;
    for (let i = 3; i < d.length; i += 4) minAlpha = Math.min(minAlpha, d[i]);
    return { w: img.naturalWidth, h: img.naturalHeight, minAlpha, corner: [d[0], d[1], d[2], d[3]] };
  }, src);
}
async function siteCaches(pg) {
  return pg.evaluate(async () => (await caches.keys()).filter((k) => k.startsWith("calibrayt-site-plans")));
}
// Plans and pages kept on the phone (the app's own static files, which hold no company data, are not counted).
async function keptPlans(pg) {
  return pg.evaluate(async () => {
    const out = [];
    for (const k of (await caches.keys()).filter((k) => k.startsWith("calibrayt-site-plans"))) {
      for (const r of await (await caches.open(k)).keys()) {
        const p = new URL(r.url).pathname;
        if (!p.startsWith("/static/")) out.push(p);
      }
    }
    return out.sort();
  });
}

test("iPhone, signed out: Site Plans has its own sign-in, Home Screen metadata, manifest and icons", async () => {
  const s = await context("anon", PHONE, { iphone: true });
  const sp = await (await s.ctx.request.get(`${base}/static/site-plans/manifest.webmanifest`)).json();
  assert.equal(sp.name, "Site Plans");
  assert.equal(sp.short_name, "Site Plans");
  assert.equal(sp.scope, "/site-plans/");
  assert.equal(sp.start_url, "/site-plans/?source=home-screen");
  assert.equal(sp.display, "standalone");
  await go(s.pg, sp.start_url);
  assert.equal(pathOf(s.pg), "/site-plans/sign-in", "the start page asks for a sign-in");
  assert.equal(await s.pg.locator("[data-sp-sign-in-form]").count(), 1);
  const tags = await homeScreenTags(s.pg);
  assert.deepEqual(tags, { manifest: "/static/site-plans/manifest.webmanifest", title: "Site Plans",
                           touch: "/static/site-plans/site-plans-icon-180.png", capable: "yes" });
  const field = await (await s.ctx.request.get(`${base}/static/manifest.webmanifest`)).json();
  const uc = await (await s.ctx.request.get(`${base}/static/useful-calculators/manifest.webmanifest`)).json();
  assert.deepEqual([field.name, field.scope], ["CalibraytAI", "/"]);
  assert.deepEqual([uc.name, uc.scope], ["Useful Calculators", "/useful-calculators/"]);
  for (const icon of sp.icons) {
    const res = await s.ctx.request.get(`${base}${icon.src}`);
    assert.equal(res.status(), 200, icon.src);
    assert.equal(res.headers()["content-type"], "image/png");
    const f = await imageFacts(s.pg, icon.src);
    assert.equal(`${f.w}x${f.h}`, icon.sizes, icon.src);
    if (icon.purpose === "maskable" || icon.src.endsWith("-180.png")) assert.equal(f.minAlpha, 255, `${icon.src} is opaque`);
  }
  const touch = await imageFacts(s.pg, tags.touch);
  assert.deepEqual([touch.w, touch.h, touch.minAlpha], [180, 180, 255], "apple-touch-icon 180 x 180, no transparency");
  assert.deepEqual(touch.corner.slice(0, 3), [26, 43, 63], "corner is the tile's navy #1a2b3f");
  for (const p of ["/site-plans/", `/site-plans/projects/${facts.assigned_id}`,
                   `/site-plans/projects/${facts.assigned_id}/plan/${facts.plan_id}.pdf`]) {
    await go(s.pg, p);
    assert.equal(pathOf(s.pg), "/site-plans/sign-in", `${p} needs a sign-in`);
  }
  await noSideways(s.pg, "sign-in");
  await shot(s.pg, "f04-sp-sign-in.png");
  if (SHOTS) {
    const icon = await s.ctx.newPage();
    await icon.setViewportSize({ width: 180, height: 180 });
    await icon.goto(`${base}${tags.touch}`);
    await icon.screenshot({ path: path.join(SHOTS, "site-plans-home-screen-icon-180.png"), clip: { x: 0, y: 0, width: 180, height: 180 } });
    await icon.close();
  }
  assert.deepEqual(s.errors, []);
});

test("iPhone, Field-only crew: signs in from the Home Screen start page and sees only the job he is booked on", async () => {
  const s = await context("kevin", PHONE, { iphone: true });
  await go(s.pg, "/site-plans/?source=home-screen");
  assert.equal(pathOf(s.pg), "/site-plans/sign-in");
  await s.pg.fill("input[name=email]", facts.kevin[0]);
  await s.pg.fill("input[name=password]", facts.kevin[1]);
  await submit(s.pg, s.pg.locator("[data-sp-sign-in-form] button[type=submit]"));
  assert.equal(pathOf(s.pg), "/site-plans/");
  const ids = await s.pg.locator("[data-sp-project]").evaluateAll((as) => as.map((a) => Number(a.dataset.spProject)));
  assert.deepEqual(ids, [facts.assigned_id], "only Harbour Lane");
  const text = await s.pg.locator("main").innerText();
  assert.ok(text.includes(facts.assigned) && !text.includes(facts.unassigned) && !text.includes(facts.org_b_project));
  // The same jobs Field shows him.
  await go(s.pg, "/field/projects");
  const field = await s.pg.locator("main").innerText();
  assert.ok(field.includes(facts.assigned) && !field.includes(facts.unassigned));
  await go(s.pg, "/site-plans/");
  await noMoneyOrContacts(s.pg, "crew project list");
  await noSideways(s.pg, "crew project list");
  await shot(s.pg, "f04-sp-projects.png");
  assert.deepEqual(s.errors, []);
});

test("iPhone, crew: the job's plans and a plan, every page with its sheet number, zoomable", async () => {
  const s = sessions.kevin;
  await submit(s.pg, s.pg.locator(`[data-sp-project="${facts.assigned_id}"]`));
  assert.equal(pathOf(s.pg), `/site-plans/projects/${facts.assigned_id}`);
  const keys = await s.pg.locator("[data-sp-file]").evaluateAll((li) => li.map((e) => e.dataset.spFile));
  assert.deepEqual(keys, [`plan-${facts.plan_id}`, `drawing-${facts.drawing_set_id}`]);
  const chips = await s.pg.locator("[data-sp-sheet]").allInnerTexts();
  assert.deepEqual(chips, [...facts.sheets, ...facts.drawing_sheets].map(([n, t]) => `${n} · ${t}`));
  await noMoneyOrContacts(s.pg, "crew project plans");
  await noSideways(s.pg, "crew project plans");
  await shot(s.pg, "f04-sp-project.png");
  const pdfs = [];
  s.pg.on("response", (r) => { if (r.url().endsWith(".pdf")) pdfs.push([new URL(r.url()).pathname, r.status(), r.headers()["content-type"], r.headers()["cache-control"]]); });
  await submit(s.pg, s.pg.locator(`[data-sp-open="plan-${facts.plan_id}"]`));
  const view = `/site-plans/projects/${facts.assigned_id}/plan/${facts.plan_id}`;
  assert.equal(pathOf(s.pg), view);
  assert.equal(await s.pg.getAttribute("body", "data-sp-layout"), "pages", "iPhone: page by page");
  assert.equal(await s.pg.locator("[data-sp-page]").count(), facts.plan_pages);
  const headings = await s.pg.locator("[data-sp-page] h2").allInnerTexts();
  assert.deepEqual(headings, [...facts.sheets.map(([n, t]) => `${n} · ${t}`), "Page 3"]);
  const viewport = await s.pg.getAttribute('meta[name="viewport"]', "content");
  assert.doesNotMatch(viewport, /user-scalable=no|maximum-scale=1\b/, "pinch zoom is allowed");
  await s.pg.locator('[data-sp-viewer][data-sp-kept="yes"]').waitFor({ timeout: 20000 });  // the opened plan is kept
  for (let n = 1; n <= facts.plan_pages; n++) {
    assert.ok(pdfs.some(([p, st, type, cc]) => p === `${view}/page-${n}.pdf` && st === 200 && type === "application/pdf"
                                            && /no-store/.test(cc) && /private/.test(cc)), `page ${n} served, private`);
  }
  await noMoneyOrContacts(s.pg, "plan viewer");
  await noSideways(s.pg, "plan viewer");
  if (SHOTS) await s.pg.waitForTimeout(4000);  // let the browser draw the PDF pages before the picture
  if (SHOTS) await s.pg.screenshot({ path: path.join(SHOTS, "site-plans-phone-plan-open.png") });
  await submit(s.pg, s.pg.locator("[data-sp-back]"));
  assert.equal(pathOf(s.pg), `/site-plans/projects/${facts.assigned_id}`);
  assert.deepEqual(s.errors, []);
});

test("iPhone, crew: Save for offline, the plans open with no signal, and sign out removes them", async () => {
  const s = sessions.kevin;
  const scope = await s.pg.evaluate(async () => (await navigator.serviceWorker.ready).scope);
  assert.equal(scope, `${base}/site-plans/`, "Site Plans' own service worker, scope /site-plans/ only");
  await go(s.pg, `/site-plans/projects/${facts.assigned_id}`);  // now controlled by the service worker
  await s.pg.locator("[data-sp-save]").click();
  await s.pg.locator("[data-sp-save][data-sp-saved-count]").waitFor({ timeout: 30000 });
  assert.match(await s.pg.locator("[data-sp-save-status]").innerText(), /Saved 2 of 2 plans on this phone/);
  assert.equal(await s.pg.locator("[data-sp-saved]:not([hidden])").count(), 2, "each plan says On this phone");
  await noSideways(s.pg, "saved");
  await shot(s.pg, "f04-sp-saved.png");
  assert.deepEqual(await siteCaches(s.pg), ["calibrayt-site-plans-v1"]);
  const kept = await keptPlans(s.pg);
  for (const p of ["/site-plans/", `/site-plans/projects/${facts.assigned_id}`,
                   `/site-plans/projects/${facts.assigned_id}/plan/${facts.plan_id}/page-3.pdf`,
                   `/site-plans/projects/${facts.assigned_id}/drawing/${facts.drawing_set_id}/page-2.pdf`]) {
    assert.ok(kept.includes(p), `${p} kept on the phone`);
  }
  assert.ok(kept.every((p) => p.startsWith("/site-plans/")), "only Site Plans pages and files are kept");
  // No signal.
  relay.offline(true);
  const drawing = `/site-plans/projects/${facts.assigned_id}/drawing/${facts.drawing_set_id}`;
  for (const p of ["/site-plans/?source=home-screen", `/site-plans/projects/${facts.assigned_id}`, drawing]) {
    await go(s.pg, p);
    assert.equal(await s.pg.getAttribute("body", "data-sp-copy"), "offline", `${p} opens from the phone`);
    assert.ok(await s.pg.locator("[data-sp-offline-note]").isVisible(), `${p} says it is the saved copy`);
  }
  assert.equal(await s.pg.locator("[data-sp-page]").count(), facts.drawing_sheets.length);
  const offlinePages = await s.pg.evaluate(async (v) => {
    const out = [];
    for (let n = 1; n <= 2; n++) {
      const r = await fetch(`${v}/page-${n}.pdf`);
      out.push([r.status, r.headers.get("content-type")]);
    }
    return out;
  }, drawing);
  assert.deepEqual(offlinePages, [[200, "application/pdf"], [200, "application/pdf"]], "each sheet opens with no signal");
  relay.offline(false);
  // Sign out: the copies on the phone are removed; with no signal nothing opens afterwards.
  await go(s.pg, "/site-plans/");
  await submit(s.pg, s.pg.locator("[data-sp-sign-out]"));
  assert.equal(pathOf(s.pg), "/site-plans/sign-in");
  await s.pg.waitForTimeout(300);
  assert.deepEqual(await keptPlans(s.pg), [], "sign out removed the saved plans");
  relay.offline(true);
  await go(s.pg, drawing);
  assert.match(await s.pg.locator("body").innerText(), /This page is not saved on this phone/);
  relay.offline(false);
  await go(s.pg, drawing);
  assert.equal(pathOf(s.pg), "/site-plans/sign-in", "signed out: back to the Site Plans sign-in");
  assert.deepEqual(s.errors, []);
});

test("iPhone, crew: another job's and another company's plans never open; office pages send him to Field", async () => {
  const s = await context("kevin2", PHONE, { iphone: true });
  await go(s.pg, "/site-plans/sign-in");
  await s.pg.fill("input[name=email]", facts.kevin[0]);
  await s.pg.fill("input[name=password]", facts.kevin[1]);
  await submit(s.pg, s.pg.locator("[data-sp-sign-in-form] button[type=submit]"));
  for (const id of [facts.unassigned_id, facts.org_b_project_id]) {
    await go(s.pg, `/site-plans/projects/${id}`);
    assert.equal(pathOf(s.pg), "/site-plans/", `project ${id} goes back to the list`);
    assert.match(await s.pg.locator("main").innerText(), /not available to you/);
  }
  for (const p of [`/site-plans/projects/${facts.unassigned_id}/plan/${facts.other_plan_id}.pdf`,
                   `/site-plans/projects/${facts.unassigned_id}/plan/${facts.other_plan_id}`,
                   `/site-plans/projects/${facts.org_b_project_id}/plan/${facts.org_b_plan_id}.pdf`,
                   `/site-plans/projects/${facts.assigned_id}/plan/${facts.org_b_plan_id}.pdf`,
                   `/site-plans/projects/${facts.assigned_id}/plan/${facts.other_plan_id}/page-1.pdf`]) {
    const r = await s.ctx.request.get(`${base}${p}`, { maxRedirects: 0 });
    assert.equal(r.status(), 404, p);
  }
  for (const p of [`/projects/${facts.assigned_id}`, `/estimates/${facts.estimate_id}`, `/projects/${facts.assigned_id}/plans`]) {
    await go(s.pg, p);
    assert.equal(pathOf(s.pg), "/field/today", `${p} sends the crew to Field`);
  }
  assert.deepEqual(s.errors, []);
});

test("Desktop, owner: one plan button (View project plan) on project pages, and the Site Plans viewer", async () => {
  const s = await context("owner", DESK);
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", facts.owner[0]);
  await s.pg.fill("input[name=password]", facts.owner[1]);
  await submit(s.pg, s.pg.locator("button[type=submit].login-primary"));
  const project = `/site-plans/projects/${facts.assigned_id}`;
  for (const p of [`/projects/${facts.assigned_id}`, `/estimates/${facts.estimate_id}`,
                   `/estimates/${facts.estimate_id}/versions/${facts.version_id}`, `/projects/${facts.assigned_id}/drawings`,
                   `/projects/${facts.assigned_id}/plans`, `/projects/${facts.assigned_id}/supplier-requests`,
                   `/schedule/items/${facts.schedule_item_id}`]) {
    const r = await go(s.pg, p);
    assert.equal(r.status(), 200, p);
    assert.equal(await s.pg.locator("[data-plans-button], .header-plans-btn").count(), 0, `${p}: no duplicate Plans button`);
    assert.ok(await s.pg.locator("[data-view-project-plan]").count() <= 1, `${p}: at most one View project plan`);
  }
  await go(s.pg, `/projects/${facts.assigned_id}`);
  assert.equal(await s.pg.locator("[data-view-project-plan]").count(), 1, "the project hub has View project plan");
  if (SHOTS) await s.pg.screenshot({ path: path.join(SHOTS, "office-project-view-project-plan.png") });
  await go(s.pg, "/site-plans/");
  await submit(s.pg, s.pg.locator(`[data-sp-project="${facts.assigned_id}"]`));
  assert.equal(pathOf(s.pg), project);
  assert.equal(await s.pg.locator("[data-sp-file]").count(), 2);
  assert.equal(await s.pg.locator("[data-sp-office-project]").getAttribute("href"), `/projects/${facts.assigned_id}`);
  await noMoneyOrContacts(s.pg, "office project plans");
  await submit(s.pg, s.pg.locator(`[data-sp-open="plan-${facts.plan_id}"]`));
  assert.equal(await s.pg.getAttribute("body", "data-sp-layout"), "whole", "computer: the browser's own PDF viewer");
  const src = await s.pg.locator("[data-sp-whole-frame] iframe").getAttribute("src");
  assert.equal(src, `/site-plans/projects/${facts.assigned_id}/plan/${facts.plan_id}.pdf#view=FitH`);
  const file = await s.ctx.request.get(`${base}${src.split("#")[0]}`);
  assert.equal(file.status(), 200);
  assert.equal(file.headers()["content-type"], "application/pdf");
  assert.match(file.headers()["content-disposition"], /^inline/);
  assert.match(file.headers()["cache-control"], /private/);
  assert.match(file.headers()["cache-control"], /no-store/);
  await noMoneyOrContacts(s.pg, "office viewer");
  await noSideways(s.pg, "office viewer");
  if (SHOTS) await s.pg.waitForTimeout(4000);
  if (SHOTS) await s.pg.screenshot({ path: path.join(SHOTS, "office-plans-viewer-desktop.png") });
  // The office list: this organization's active projects, never the other organization's.
  await go(s.pg, "/site-plans/");
  const ids = await s.pg.locator("[data-sp-project]").evaluateAll((as) => as.map((a) => Number(a.dataset.spProject)));
  assert.deepEqual(ids.sort(), [facts.assigned_id, facts.unassigned_id].sort());
  await go(s.pg, `/site-plans/projects/${facts.org_b_project_id}`);
  assert.equal(pathOf(s.pg), "/site-plans/");
  assert.deepEqual(s.errors, []);
});

test("iPhone 390, owner: project pages fit without sideways scrolling and carry no duplicate Plans button", async () => {
  const s = await context("owner-phone", PHONE, { iphone: true });
  await go(s.pg, "/login");
  await s.pg.fill("input[name=email]", facts.owner[0]);
  await s.pg.fill("input[name=password]", facts.owner[1]);
  await submit(s.pg, s.pg.locator("button[type=submit].login-primary"));
  for (const p of [`/projects/${facts.assigned_id}`, `/estimates/${facts.estimate_id}`]) {
    await go(s.pg, p);
    assert.equal(await s.pg.locator("[data-plans-button], .header-plans-btn").count(), 0, `${p}: no duplicate Plans button`);
    await noSideways(s.pg, p);
  }
  await go(s.pg, `/site-plans/projects/${facts.assigned_id}`);
  assert.equal(pathOf(s.pg), `/site-plans/projects/${facts.assigned_id}`);
  await noSideways(s.pg, "office project plans on the phone");
  assert.deepEqual(s.errors, []);
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
});
