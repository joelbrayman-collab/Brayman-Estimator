// Release evidence for the roles and the isolation between them (V1 completion, 20 Oct 2026), in a real
// browser against a local office on a temporary database (tests/roles_page_server.py), synthetic data only.
//
// Administrator: owner-only actions shown to the owner and refused (403, not offered) to an ordinary office
// user; crews; brand profile; account password; access domain and System Administrator grants (operator
// commands, tests/roles_operator.py); a deactivated account; People & Access pages (add a person, deactivate,
// reactivate, give/remove access; refused to others). Security: 30-minute inactivity sign-out (the
// office clock is moved forward, nothing waits), password recovery from the captured mail, sign-out empties
// the Field offline cache, signed-out access goes to the right sign-in. Customer, on a 390 px phone: proposal
// link (view, PDF, accept), contract signing, change order signing and declining, PRO Desk quotation link
// (accept, decline) — no sideways scrolling, nothing internal, replaced/expired/used/tampered links refused.
// Isolation: organization A vs B, field-only user vs office pages and schedule changes (refused), supplier vs contractor,
// supplier A vs B, customer link holder vs everything else.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_roles.mjs
// EVIDENCE_SHOTS=<folder> also saves a screenshot of each customer screen.
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const SHOTS = process.env.EVIDENCE_SHOTS || "";
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = []; // every response of 500 or more, from any page in the walk
const recorded = []; // what a role CAN do that is an owner policy question (printed, not changed)
let screens = 0;

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/roles_page_server.py")], {
    cwd: REPO, env: { ...process.env, ROLES_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("roles office did not start\n" + out)), 180000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("roles office exited\n" + out)); }
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
  for (const line of recorded) console.log(`RECORDED ${line}`);
  console.log(`ROLES_SCREENS=${screens} SERVER_ERRORS=${serverErrors.length}`);
});

// ------------------------------------------------------------------ helpers
const sessions = {};
async function context(viewport) {
  const ctx = await browser.newContext({ viewport });
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg, errors };
}
async function signIn(s, email, password, loginPath = "/login") {
  await s.pg.goto(`${base}${loginPath}`);
  await s.pg.fill("input[name=email]", email);
  await s.pg.fill("input[name=password]", password);
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator("form button[type=submit]").first().click()]);
  await s.pg.waitForLoadState();
}
async function session(key, viewport, [email, password], loginPath = "/login") {
  if (sessions[key]) return sessions[key];
  const s = await context(viewport);
  await signIn(s, email, password, loginPath);
  sessions[key] = s;
  return s;
}
const owner = () => session("owner", DESK, facts.owner);
const staff = () => session("staff", DESK, facts.staff);
const kevin = () => session("kevin", PHONE, facts.kevin);
const bea = () => session("bea", DESK, facts.bea);
const store = () => session("store", DESK, facts.store, "/supplier/login");
const rival = () => session("rival", DESK, facts.rival, "/supplier/login");
async function go(pg, url) {
  const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`);
  await pg.waitForLoadState();
  // A set-password link carries its credential after "#": the landing page's script posts it and moves on
  // (22 Oct 2026). Wait for that second page.
  if (url.includes("/reset-password#")) await pg.waitForFunction(() => !document.querySelector("[data-reset-open]"));
  return r;
}
// Status of a GET, without following a redirect (so a sign-in redirect is seen as one).
async function status(ctx, url) {
  let r = await ctx.request.get(`${base}${url}`, { maxRedirects: 0 });
  // Flask's trailing-slash redirect (308) is not an answer about access: follow it once.
  if (r.status() === 308) r = await ctx.request.get(new URL(r.headers()["location"], base).href, { maxRedirects: 0 });
  return { code: r.status(), location: r.headers()["location"] || "" };
}
async function noSideways(pg, label) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `${label}: page scrolls sideways by ${o}px`);
}
async function shot(pg, name) {
  screens += 1;
  if (!SHOTS) return;
  fs.mkdirSync(SHOTS, { recursive: true });
  await pg.screenshot({ path: path.join(SHOTS, `${String(screens).padStart(2, "0")}-${name}.png`), fullPage: true });
}
async function flash(pg) { return (await pg.locator(".flash, .alert, [role=alert], [role=status]").allInnerTexts()).join(" | "); }
async function navText(pg) { return (await pg.locator("nav, .app-sidebar, aside").allInnerTexts()).join(" "); }
function pdfText(buffer) {
  const r = spawnSync(path.join(REPO, "venv/bin/python"), ["-c",
    "import sys,io;from pypdf import PdfReader;print('\\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(sys.stdin.buffer.read())).pages))"],
  { input: buffer, maxBuffer: 64 * 1024 * 1024 });
  assert.equal(r.status, 0, String(r.stderr));
  return String(r.stdout);
}
// Nothing the company keeps to itself, and no other customer or organization, on a customer's screen.
function internalMarkers() {
  const i = facts.internal;
  return [i.code, i.name, i.unit_cost, Number(i.unit_cost).toLocaleString("en-CA"), i.markup + "%", i.note,
    "Approved contractor cost", i.project_note, i.co_internal_cost, "Internal Direct Cost", "extended_cost",
    facts.other_customer[0], facts.other_customer[1], facts.org_b_client, facts.org_b_project, facts.org_b[1],
    "office@example.com", facts.staff[2], facts.kevin[2]];
}
function noInternal(text, label, extra = []) {
  for (const marker of [...internalMarkers(), ...extra]) {
    assert.ok(!String(text).includes(marker), `${label}: shows internal "${marker}"`);
  }
}
async function customerPage(pg, label) {
  await noSideways(pg, label);
  const html = await pg.content();
  noInternal(html, `${label} (page source)`);
  // A customer page links only to its own link, static files, fonts, mail and phone: never an office page.
  const hrefs = await pg.locator("a[href], form[action]").evaluateAll((els) => els.map((e) => e.getAttribute("href") || e.getAttribute("action")));
  for (const href of hrefs) {
    const ok = /^(#|mailto:|tel:|https:\/\/fonts\.)/.test(href) || /^\/(proposal|sign|quote|static)\//.test(href.replace(base, ""));
    assert.ok(ok, `${label}: links to "${href}"`);
  }
}
function operator(action, email) {
  const r = spawnSync(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/roles_operator.py"), facts.database_uri, action, email],
    { cwd: REPO, encoding: "utf8" });
  assert.equal(r.status, 0, `${action}: ${r.stdout} ${r.stderr}`);
  return r.stdout.trim();
}
function newestMail(template, to) {
  const files = fs.existsSync(facts.mail_dir) ? fs.readdirSync(facts.mail_dir).filter((f) => f.includes(template)).sort() : [];
  const bodies = files.map((f) => fs.readFileSync(path.join(facts.mail_dir, f), "utf8")).filter((b) => b.includes(`To: ${to}`));
  return { count: bodies.length, body: bodies.at(-1) || "" };
}
function setClock(seconds) { fs.writeFileSync(facts.clock_file, String(seconds)); }
const tamper = (link) => link.slice(0, -3) + (link.endsWith("xyz") ? "abc" : "xyz");

// ================================================================== 1. Administrator
test("owner sees the owner-only actions; an ordinary office user is not offered them and is refused (403)", async () => {
  const o = await owner();
  await go(o.pg, `/projects/${facts.project_id}`);
  assert.equal(await o.pg.locator(`a[href="/projects/${facts.project_id}/close"]`).count(), 1, "owner is offered Close project");
  assert.equal((await status(o.ctx, `/projects/${facts.project_id}/close`)).code, 200);
  const s = await staff();
  await go(s.pg, `/projects/${facts.project_id}`);
  assert.equal(await s.pg.locator(`a[href="/projects/${facts.project_id}/close"]`).count(), 0, "staff is not offered Close project");
  assert.equal((await status(s.ctx, `/projects/${facts.project_id}/close`)).code, 403);
  assert.equal((await status(s.ctx, `/projects/${facts.project_id}/reopen`)).code, 403);
  assert.equal(await s.pg.locator('a[href="/company-attention"]').count(), 0, "staff is not offered Needs attention");
  assert.equal((await status(s.ctx, "/company-attention")).code, 403);
  // The owner has no management grant either: the company attention page is a separate access domain.
  assert.equal((await status(o.ctx, "/company-attention")).code, 403);
  recorded.push("Instance Owner is refused /company-attention until the COMPANY_MANAGEMENT access domain is granted (by operator command).");
});

test("access domain and System Administrator: granted and removed by the operator commands, the office follows at once", async () => {
  const s = await staff();
  operator("grant-management", facts.staff[0]);
  await go(s.pg, "/");
  assert.ok(await s.pg.locator('a[href="/company-attention"]').count() >= 1, "Needs attention appears once granted");
  assert.equal((await status(s.ctx, "/company-attention")).code, 200);
  operator("revoke-management", facts.staff[0]);
  await go(s.pg, "/");
  assert.equal(await s.pg.locator('a[href="/company-attention"]').count(), 0);
  assert.equal((await status(s.ctx, "/company-attention")).code, 403);
  operator("appoint-administrator", facts.staff[0]);
  await go(s.pg, `/projects/${facts.project_id}`);
  assert.equal(await s.pg.locator(`a[href="/projects/${facts.project_id}/close"]`).count(), 1, "a System Administrator may close");
  operator("remove-administrator", facts.staff[0]);
  await go(s.pg, `/projects/${facts.project_id}`);
  assert.equal(await s.pg.locator(`a[href="/projects/${facts.project_id}/close"]`).count(), 0);
  assert.equal((await status(s.ctx, `/projects/${facts.project_id}/close`)).code, 403);
});

test("crew management: create a crew, add a person with dates, close the dates, retire the crew", async () => {
  const { pg } = await owner();
  await go(pg, "/settings/crews");
  await Promise.all([pg.waitForLoadState(), pg.locator('a[href="/settings/crews/new"]').click()]);
  await pg.fill("[name=name]", "South Crew (synthetic)");
  await Promise.all([pg.waitForLoadState(), pg.locator("main form button[type=submit]").click()]);
  assert.match(await flash(pg), /Crew saved/);
  await Promise.all([pg.waitForLoadState(), pg.getByRole("link", { name: "South Crew (synthetic)" }).click()]);
  const crewUrl = pg.url();
  await pg.selectOption("[name=user_id]", { label: facts.staff[2] });
  const today = new Date().toISOString().slice(0, 10);
  await pg.fill('form[action$="/members"] [name=effective_from]', today);
  await Promise.all([pg.waitForLoadState(), pg.locator('form[action$="/members"] button[type=submit]').click()]);
  assert.match(await flash(pg), /Crew dates saved/);
  assert.match(await pg.locator("main").innerText(), new RegExp(facts.staff[2].replace(/[()]/g, ".")));
  await pg.fill('form[action*="/close"] [name=effective_to]', today);
  await Promise.all([pg.waitForLoadState(), pg.locator('form[action*="/close"] button[type=submit]').click()]);
  assert.match(await flash(pg), /Crew dates closed/);
  await go(pg, crewUrl);
  await Promise.all([pg.waitForLoadState(), pg.locator('form[action$="/retire"] button[type=submit]').click()]);
  assert.match(await flash(pg), /Crew retired/);
  // Kevin's crew is untouched.
  await go(pg, `/settings/crews/${facts.crew_id}`);
  assert.match(await pg.locator("main").innerText(), /Kevin Field/);
  const s = await staff();
  assert.equal((await status(s.ctx, "/settings/crews/new")).code, 200);
  recorded.push("Crews (/settings/crews) and Brand Profile (/settings/brand-profile) are open to every signed-in office member, not only the owner.");
});

test("organization settings: the owner saves the brand profile", async () => {
  const { pg } = await owner();
  await go(pg, "/settings/brand-profile");
  await pg.fill("[name=legal_name]", "Brayman Construction (synthetic) Ltd.");
  await pg.fill("[name=customer_facing_name]", "Brayman Construction (synthetic)");
  await Promise.all([pg.waitForLoadState(), pg.getByRole("button", { name: "Save Brand Profile" }).click()]);
  assert.doesNotMatch(await flash(pg), /error|could not/i);
  assert.equal(await pg.locator("[name=customer_facing_name]").inputValue(), "Brayman Construction (synthetic)");
});

test("account settings: a person changes their own password; the old one stops working", async () => {
  const s = await context(DESK);
  await signIn(s, facts.staff[0], facts.staff[1]);
  await go(s.pg, "/account/password");
  await s.pg.fill("[name=current_password]", facts.staff[1]);
  await s.pg.fill("[name=password]", "Synthetic-staff-pass-2");
  await s.pg.fill("[name=confirm_password]", "Synthetic-staff-pass-2");
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator("main form button[type=submit], form button[type=submit]").first().click()]);
  const fresh = await context(DESK);
  await signIn(fresh, facts.staff[0], facts.staff[1]);
  assert.match(fresh.pg.url(), /\/login/, "the old password is refused");
  await signIn(fresh, facts.staff[0], "Synthetic-staff-pass-2");
  assert.doesNotMatch(fresh.pg.url(), /\/login/, "the new password signs in");
  // Put it back for the rest of the walk.
  await go(fresh.pg, "/account/password");
  await fresh.pg.fill("[name=current_password]", "Synthetic-staff-pass-2");
  await fresh.pg.fill("[name=password]", facts.staff[1]);
  await fresh.pg.fill("[name=confirm_password]", facts.staff[1]);
  await Promise.all([fresh.pg.waitForLoadState(), fresh.pg.locator("form button[type=submit]").first().click()]);
  await s.ctx.close(); await fresh.ctx.close();
  // Changing the password signs out the person's other sessions (credentials epoch).
  delete sessions.staff;
});

test("a deactivated account is signed out on its next page and cannot sign in again", async () => {
  const s = await context(DESK);
  await signIn(s, facts.staff[0], facts.staff[1]);
  assert.equal((await status(s.ctx, "/projects")).code, 200);
  operator("deactivate-user", facts.staff[0]);
  try {
    const r = await status(s.ctx, "/projects");
    assert.equal(r.code, 302); assert.match(r.location, /\/login/);
    const again = await context(DESK);
    await signIn(again, facts.staff[0], facts.staff[1]);
    assert.match(again.pg.url(), /\/login/);
    await again.ctx.close();
  } finally {
    operator("reactivate-user", facts.staff[0]);
  }
  await s.ctx.close();
});

test("People & Access on a 390 px phone: the owner adds a person (set-password email), deactivates and reactivates them; others are refused", async () => {
  const o = await context(PHONE);
  await signIn(o, ...facts.owner);
  await go(o.pg, "/settings/people");
  await noSideways(o.pg, "People & Access");
  await shot(o.pg, "people-access");
  assert.match(await o.pg.locator("main").innerText(), new RegExp(facts.staff[0].replace(/\./g, "\\.")));
  assert.ok(!(await o.pg.locator("main").innerText()).includes(facts.bea[0]), "organization B's people are not listed");
  await Promise.all([o.pg.waitForURL(/\/settings\/people\/new$/), o.pg.locator('a[href="/settings/people/new"]').click()]);
  await o.pg.waitForLoadState("load");
  await noSideways(o.pg, "Add a person");
  const person = ["Petra Newhire (synthetic)", "petra.newhire@example.invalid", "Synthetic-petra-pass-1"];
  await o.pg.fill("[name=display_name]", person[0]);
  await o.pg.fill("[name=email]", person[1]);
  await Promise.all([o.pg.waitForURL(/\/settings\/people\/\d+$/), o.pg.locator("main form button[type=submit]").click()]);
  await o.pg.waitForLoadState("load");
  assert.match(await flash(o.pg), /was added/);
  assert.match(await flash(o.pg), /link to choose a password was emailed/);
  const personUrl = o.pg.url();
  await noSideways(o.pg, "person page");
  // The same email again is refused.
  await go(o.pg, "/settings/people/new");
  await o.pg.fill("[name=display_name]", "Duplicate (synthetic)");
  await o.pg.fill("[name=email]", person[1]);
  await Promise.all([o.pg.waitForLoadState(), o.pg.locator("main form button[type=submit]").click()]);
  assert.match(await flash(o.pg), /already has a sign-in/);
  // The new person chooses a password from the captured email and signs in.
  const mail = newestMail("ACCOUNT_INVITATION", person[1]);  // a proper invitation since 21 Oct 2026
  assert.equal(mail.count, 1, "one invitation email captured");
  assert.match(mail.body, /invited you to CalibraytAI/);
  const p = await context(PHONE);
  await go(p.pg, mail.body.match(/\/reset-password#[A-Za-z0-9_\-.]+/)[0]);
  await p.pg.fill("[name=password]", person[2]);
  await p.pg.fill("[name=confirm_password]", person[2]);
  await Promise.all([p.pg.waitForLoadState(), p.pg.locator("form button[type=submit]").click()]);
  await signIn(p, person[1], person[2]);
  assert.doesNotMatch(p.pg.url(), /\/login/, "the new person signs in");
  assert.equal((await status(p.ctx, "/projects/")).code, 200);
  assert.equal((await status(p.ctx, "/settings/people")).code, 403, "a new person is not an administrator");
  // Deactivate: their open session ends on the next page and they cannot sign in.
  await go(o.pg, personUrl);
  await Promise.all([o.pg.waitForLoadState(), o.pg.getByRole("button", { name: "Deactivate sign-in" }).click()]);
  assert.match(await flash(o.pg), /is deactivated/);
  assert.match(await o.pg.locator("[data-sign-in-status]").innerText(), /Deactivated/);
  const ended = await status(p.ctx, "/projects/");
  assert.equal(ended.code, 302); assert.match(ended.location, /\/login/);
  await signIn(p, person[1], person[2]);
  assert.match(p.pg.url(), /\/login/, "a deactivated person cannot sign in");
  // Reactivate: they sign in again.
  await Promise.all([o.pg.waitForLoadState(), o.pg.getByRole("button", { name: "Reactivate sign-in" }).click()]);
  assert.match(await flash(o.pg), /can sign in again/);
  await signIn(p, person[1], person[2]);
  assert.doesNotMatch(p.pg.url(), /\/login/, "reactivated person signs in");
  // Give and remove Company Management from the page.
  await Promise.all([o.pg.waitForLoadState(), o.pg.getByRole("button", { name: "Give" }).click()]);
  assert.equal((await status(p.ctx, "/company-attention")).code, 200);
  await Promise.all([o.pg.waitForLoadState(), o.pg.getByRole("button", { name: "Remove", exact: true }).click()]);
  assert.equal((await status(p.ctx, "/company-attention")).code, 403);
  // The owner is not offered deactivation of their own sign-in.
  await go(o.pg, "/settings/people");
  await Promise.all([o.pg.waitForLoadState(), o.pg.locator(".register-row", { hasText: "(you)" }).click()]);
  assert.equal(await o.pg.getByRole("button", { name: "Deactivate sign-in" }).count(), 0);
  await p.ctx.close(); await o.ctx.close();
  // An ordinary office user is neither offered nor allowed the pages; organization B's owner never reaches A's people.
  const s = await staff();
  await go(s.pg, "/projects/");
  assert.equal(await s.pg.locator('a[href="/settings/people"]').count(), 0, "staff is not offered People & Access");
  for (const url of ["/settings/people", "/settings/people/new"]) assert.equal((await status(s.ctx, url)).code, 403, url);
  const refused = await s.ctx.request.post(`${base}/settings/people/new`, { form: { display_name: "X", email: "x.staff@example.invalid" }, maxRedirects: 0 });
  assert.ok([400, 403].includes(refused.status()), `staff add-person POST: ${refused.status()}`);
  // A separate session: the password-recovery check later changes Bea's password.
  const b = await context(DESK);
  await signIn(b, facts.bea[0], facts.bea[1]);
  const personId = personUrl.split("/").pop();
  assert.ok([403, 404].includes((await status(b.ctx, `/settings/people/${personId}`)).code), "org B cannot open org A's person");
  await b.ctx.close();
});

// ================================================================== 2. Security behaviours
test("30 minutes without activity signs the office and a supplier out (office clock moved forward 31 minutes)", async () => {
  const o = await context(DESK);
  await signIn(o, ...facts.owner);
  const sup = await context(DESK);
  await signIn(sup, ...facts.store, "/supplier/login");
  await go(o.pg, "/projects");
  await go(sup.pg, `/supplier/${facts.store_supplier_id}/pro-desk/`);
  try {
    setClock(29 * 60);
    assert.equal((await status(o.ctx, "/projects")).code, 200, "29 minutes: still signed in");
    setClock(29 * 60 + 31 * 60); // 31 minutes after that last request
    await go(o.pg, "/projects");
    assert.match(o.pg.url(), /\/login\?next=(%2F|\/)projects/);
    assert.match(await o.pg.locator("body").innerText(), /signed out after 30 minutes without activity/i);
    await go(sup.pg, `/supplier/${facts.store_supplier_id}/pro-desk/`);
    assert.match(sup.pg.url(), /\/supplier\/login/);
  } finally {
    setClock(0);
  }
  await o.ctx.close(); await sup.ctx.close();
});

test("password recovery end to end with the captured email; the link works once; an unknown address looks the same", async () => {
  const s = await context(PHONE);
  await go(s.pg, "/login");
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator(".login-forgot-link").click()]);
  await noSideways(s.pg, "forgot password");
  await s.pg.fill("[name=email]", facts.bea[0]);
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator("form button[type=submit]").click()]);
  assert.match(s.pg.url(), /\/forgot-password\/sent/);
  const sentText = await s.pg.locator("body").innerText();
  const mail = newestMail("PASSWORD_RESET", facts.bea[0]);
  assert.equal(mail.count, 1, "one reset email captured");
  const link = mail.body.match(/\/reset-password#[A-Za-z0-9_\-.]+/)[0];
  await go(s.pg, link);
  await noSideways(s.pg, "reset password");
  await s.pg.fill("[name=password]", "Synthetic-orgb-pass-2");
  await s.pg.fill("[name=confirm_password]", "Synthetic-orgb-pass-2");
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator("form button[type=submit]").click()]);
  assert.match(s.pg.url(), /\/reset-password\/complete/);
  await go(s.pg, link);
  assert.equal(await s.pg.locator("[name=password]").count(), 0, "a used reset link is refused");
  await signIn(s, facts.bea[0], facts.bea[1]);
  assert.match(s.pg.url(), /\/login/, "the old password no longer works");
  await signIn(s, facts.bea[0], "Synthetic-orgb-pass-2");
  assert.doesNotMatch(s.pg.url(), /\/login/);
  facts.bea[1] = "Synthetic-orgb-pass-2";
  await s.ctx.close();
  // An address with no account: the same page, no mail.
  const u = await context(PHONE);
  await go(u.pg, "/forgot-password");
  await u.pg.fill("[name=email]", "nobody.here@example.invalid");
  await Promise.all([u.pg.waitForLoadState(), u.pg.locator("form button[type=submit]").click()]);
  assert.equal(await u.pg.locator("body").innerText(), sentText);
  assert.equal(newestMail("PASSWORD_RESET", "nobody.here@example.invalid").count, 0);
  // A made-up reset link is refused.
  await go(u.pg, tamper(link));
  assert.equal(await u.pg.locator("[name=password]").count(), 0);
  await u.ctx.close();
});

test("signing out of Field empties the Field offline cache on the phone", async () => {
  const s = await context(PHONE);
  await signIn(s, facts.kevin[0], facts.kevin[1]);
  await go(s.pg, "/field/today");
  await s.pg.waitForFunction(() => navigator.serviceWorker && navigator.serviceWorker.ready.then(() => true), null, { timeout: 15000 });
  await go(s.pg, "/field/today"); // the second load is served through the worker and kept for offline use
  await go(s.pg, "/field/projects");
  const cached = async () => s.pg.evaluate(async () => {
    const keys = (await caches.keys()).filter((k) => k.startsWith("calibrayt-field-shell"));
    let entries = 0;
    for (const k of keys) entries += (await (await caches.open(k)).keys()).length;
    return { keys: keys.length, entries };
  });
  const before = await cached();
  assert.ok(before.entries > 0, `Field pages are kept offline before sign-out (${JSON.stringify(before)})`);
  await Promise.all([s.pg.waitForURL(/\/login/), s.pg.locator("#field-logout-form button[type=submit]").click()]);
  const afterOut = await cached();
  assert.equal(afterOut.entries, 0, `nothing is kept after sign-out (${JSON.stringify(afterOut)})`);
  assert.equal((await status(s.ctx, "/field/today")).code, 302);
  await s.ctx.close();
});

test("signed out, every role's pages go to that role's sign-in; the API answers 401", async () => {
  const s = await context(DESK);
  const office = ["/", "/projects", `/projects/${facts.project_id}`, `/estimates/${facts.estimate_id}/versions/${facts.version_id}`,
    `/proposals/${facts.proposal_id}`, "/clients", "/schedule", "/settings/crews", "/settings/brand-profile", "/company-attention",
    `/projects/${facts.project_id}/close`, "/account/password", "/field/today", "/field/week", "/field/projects", "/costs-and-pricing"];
  for (const url of office) {
    const r = await status(s.ctx, url);
    assert.equal(r.code, 302, `${url} → ${r.code}`);
    assert.match(r.location, /\/login\?next=/, `${url} → ${r.location}`);
  }
  for (const url of [`/supplier/${facts.store_supplier_id}/`, `/supplier/${facts.store_supplier_id}/pro-desk/`,
    `/supplier/${facts.store_supplier_id}/pro-desk/${facts.quotes[0].quote_id}`]) {
    const r = await status(s.ctx, url);
    assert.equal(r.code, 302, `${url} → ${r.code}`);
    assert.match(r.location, /\/supplier\/login/, `${url} → ${r.location}`);
  }
  const api = await s.ctx.request.get(`${base}/api/v1/projects`, { maxRedirects: 0 });
  assert.equal(api.status(), 401);
  // Following the redirect, the person sees the sign-in form and lands back where they were going.
  await go(s.pg, `/projects/${facts.project_id}`);
  await s.pg.fill("[name=email]", facts.owner[0]); await s.pg.fill("[name=password]", facts.owner[1]);
  await Promise.all([s.pg.waitForLoadState(), s.pg.locator("form button[type=submit]").first().click()]);
  assert.ok(s.pg.url().endsWith(`/projects/${facts.project_id}`), s.pg.url());
  await s.ctx.close();
});

// ================================================================== 3. Customer, on a 390 px phone
test("proposal link: the customer reads it and downloads the PDF; nothing internal on either", async () => {
  const c = await context(PHONE);
  const r = await go(c.pg, facts.proposal_link);
  assert.equal(r.status(), 200);
  assert.equal(r.headers()["cache-control"], "no-store");
  const text = await c.pg.locator("body").innerText();
  assert.ok(text.includes(facts.customer_line), "the customer sees the work");
  assert.match(text, /Accept Proposal/);
  await customerPage(c.pg, "proposal link");
  await shot(c.pg, "customer-proposal");
  const pdf = await c.ctx.request.get(`${base}${facts.proposal_link}/pdf`);
  assert.equal(pdf.status(), 200);
  const pdfBody = await pdf.body();
  assert.equal(pdfBody.subarray(0, 5).toString(), "%PDF-");
  const words = pdfText(pdfBody);
  assert.ok(words.includes(facts.proposal_number));
  noInternal(words, "proposal PDF");
  await c.ctx.close();
});

test("proposal link: accept needs the tick and the name; accepted once; a second accept is refused", async () => {
  const c = await context(PHONE);
  const stale = await c.ctx.newPage(); // the same link left open in a second tab
  await go(stale, facts.proposal_link);
  await go(c.pg, facts.proposal_link);
  // Without the tick the phone does not send the form (the box is required); the office side refuses it too
  // (tests/test_proposal_client_acceptance.py).
  assert.equal(await c.pg.locator("[name=accept]").getAttribute("required"), "");
  await c.pg.fill("[name=confirmed_name]", facts.customer[0]);
  await c.pg.getByRole("button", { name: "Accept Proposal" }).click();
  assert.equal(await c.pg.locator("[name=accept]").evaluate((el) => el.validity.valueMissing), true);
  assert.equal(await c.pg.locator("[data-proposal-accepted]").count(), 0);
  await c.pg.check("[name=accept]");
  await c.pg.fill("[name=confirmed_name]", facts.customer[0]);
  await Promise.all([c.pg.waitForLoadState(), c.pg.getByRole("button", { name: "Accept Proposal" }).click()]);
  assert.match(await c.pg.locator("body").innerText(), /Proposal accepted/);
  await customerPage(c.pg, "proposal accepted");
  await shot(c.pg, "customer-proposal-accepted");
  assert.equal(await c.pg.getByRole("button", { name: "Accept Proposal" }).count(), 0, "no accept button once accepted");
  // Accepting again from the tab left open is refused.
  await stale.check("[name=accept]");
  await stale.fill("[name=confirmed_name]", facts.customer[0]);
  const [again] = await Promise.all([stale.waitForResponse((r) => r.url().endsWith("/accept")),
    stale.getByRole("button", { name: "Accept Proposal" }).click()]);
  assert.equal(again.status(), 400, "a second accept is refused");
  assert.match(await stale.locator("body").innerText(), /Proposal accepted/);
  // The office sees the acceptance.
  const o = await owner();
  await go(o.pg, `/proposals/${facts.proposal_id}`);
  assert.match(await o.pg.locator("main").innerText(), new RegExp(`Accepted by ${facts.customer[0]}`));
  recorded.push("The proposal link has Accept only; there is no customer Decline on a proposal (decline exists on signing and PRO Desk links).");
  await c.ctx.close();
});

test("proposal links: replaced, expired and tampered links are refused and show nothing of the proposal", async () => {
  const c = await context(PHONE);
  for (const [label, link, code, words] of [
    ["replaced", facts.replaced_proposal_link, 410, /replaced or withdrawn/],
    ["expired", facts.expired_proposal_link, 410, /expired/],
    ["tampered", tamper(facts.proposal_link), 410, /not valid/],
  ]) {
    const r = await go(c.pg, link);
    assert.equal(r.status(), code, `${label}: ${r.status()}`);
    const text = await c.pg.locator("body").innerText();
    assert.match(text, words, `${label}: ${text}`);
    assert.ok(!text.includes(facts.customer_line), `${label}: shows the proposal`);
    await customerPage(c.pg, `${label} proposal link`);
    assert.equal((await c.ctx.request.get(`${base}${link}/pdf`)).status(), 410, `${label} PDF`);
  }
  await shot(c.pg, "customer-proposal-refused");
  await c.ctx.close();
});

async function signDocument(link, label, { decline = false } = {}) {
  const c = await context(PHONE);
  c.stale = await c.ctx.newPage(); // the same link left open in a second tab
  await go(c.stale, link);
  const r = await go(c.pg, link);
  assert.equal(r.status(), 200, `${label}: ${r.status()}`);
  await customerPage(c.pg, label);
  await shot(c.pg, `customer-${label}`);
  const doc = await c.ctx.request.get(`${base}${link}/document`);
  assert.equal(doc.status(), 200, `${label} document`);
  const body = await doc.body();
  if (body.subarray(0, 5).toString() === "%PDF-") noInternal(pdfText(body), `${label} document`);
  if (decline) {
    await Promise.all([c.pg.waitForLoadState(), c.pg.locator(".sign-form-decline button[type=submit]").click()]);
    assert.match(await c.pg.locator("body").innerText(), /declin/i);
  } else {
    await c.pg.fill("[name=confirmed_signer_name]", facts.customer[0]);
    await Promise.all([c.pg.waitForLoadState(), c.pg.getByRole("button", { name: "Sign & Accept" }).click()]);
    assert.equal(await c.pg.locator("body").getAttribute("data-sign-status"), "SENT", "not signed without consent");
    await c.pg.check("[name=consent_accepted]");
    await c.pg.fill("[name=confirmed_signer_name]", facts.customer[0]);
    await Promise.all([c.pg.waitForLoadState(), c.pg.getByRole("button", { name: "Sign & Accept" }).click()]);
    assert.match(await c.pg.locator("body").innerText(), /You have signed this document/);
  }
  await noSideways(c.pg, `${label} done`);
  noInternal(await c.pg.content(), `${label} done`);
  await shot(c.pg, `customer-${label}-done`);
  return c;
}

test("contract signing ceremony on the phone: review, consent, sign; the used link cannot sign again", async () => {
  const c = await signDocument(facts.contract_sign_link, "contract");
  await go(c.pg, facts.contract_sign_link);
  assert.equal(await c.pg.getByRole("button", { name: "Sign & Accept" }).count(), 0, "a signed contract offers no Sign button");
  // Signing again from the tab left open is refused.
  await c.stale.check("[name=consent_accepted]");
  await c.stale.fill("[name=confirmed_signer_name]", facts.customer[0]);
  const [again] = await Promise.all([c.stale.waitForResponse((r) => r.url().endsWith("/sign")),
    c.stale.getByRole("button", { name: "Sign & Accept" }).click()]);
  assert.equal(again.status(), 409, `a second signature: ${again.status()}`);
  const o = await owner();
  await go(o.pg, `/projects/${facts.signed_project_id}/contract`);
  assert.match(await o.pg.locator("[data-signing-overlay]").first().innerText(), /SIGNED/);
  await c.ctx.close();
});

test("change order signing on the phone; its internal direct cost is never shown", async () => {
  const c = await signDocument(facts.co_sign_link, "change-order");
  await c.ctx.close();
});

test("change order declined on the phone; the link then refuses to sign", async () => {
  const c = await signDocument(facts.co_decline_link, "change-order-decline", { decline: true });
  const r = await go(c.pg, facts.co_decline_link);
  assert.equal(await c.pg.getByRole("button", { name: "Sign & Accept" }).count(), 0);
  assert.notEqual(r.status(), 200, `a declined link: ${r.status()}`);
  await customerPage(c.pg, "declined signing link");
  await c.stale.check("[name=consent_accepted]");
  await c.stale.fill("[name=confirmed_signer_name]", facts.customer[0]);
  const [late] = await Promise.all([c.stale.waitForResponse((res) => res.url().endsWith("/sign")),
    c.stale.getByRole("button", { name: "Sign & Accept" }).click()]);
  assert.notEqual(late.status(), 200, "a declined change order cannot then be signed");
  assert.doesNotMatch(await c.stale.locator("body").innerText(), /You have signed this document/);
  await c.ctx.close();
});

test("signing links: expired and tampered links are refused", async () => {
  const c = await context(PHONE);
  const expired = await go(c.pg, facts.co_expired_link);
  assert.equal(expired.status(), 410);
  await customerPage(c.pg, "expired signing link");
  const tampered = await go(c.pg, tamper(facts.contract_sign_link));
  assert.equal(tampered.status(), 404);
  await customerPage(c.pg, "tampered signing link");
  assert.equal((await c.ctx.request.get(`${base}${tamper(facts.co_sign_link)}/document`)).status(), 404);
  await shot(c.pg, "customer-signing-refused");
  await c.ctx.close();
});

test("PRO Desk quotation link on the phone: view, PDF, accept; another customer's quotation is not visible", async () => {
  const [mine, other, replaced] = facts.quotes;
  const c = await context(PHONE);
  const r = await go(c.pg, mine.link);
  assert.equal(r.status(), 200);
  assert.equal(r.headers()["cache-control"], "no-store");
  await customerPage(c.pg, "quotation link");
  const html = await c.pg.content();
  for (const name of [other.customer, replaced.customer, other.number, replaced.number, "Synthetic-pro-desk-pass", facts.store[0]]) {
    assert.ok(!html.includes(name), `quotation link shows "${name}"`);
  }
  await shot(c.pg, "customer-quotation");
  const pdf = await c.ctx.request.get(`${base}${mine.link}/quotation.pdf`);
  assert.equal(pdf.status(), 200);
  const words = pdfText(await pdf.body());
  assert.ok(words.includes(mine.number));
  for (const name of [other.customer, replaced.customer]) assert.ok(!words.includes(name), `quotation PDF shows ${name}`);
  await c.pg.fill("[name=customer_name]", mine.customer);
  await Promise.all([c.pg.waitForLoadState(), c.pg.locator("button[value=accept]").click()]);
  assert.match(await c.pg.locator("body").innerText(), /Tick the box/);
  await c.pg.fill("[name=customer_name]", mine.customer);
  await c.pg.check("[name=agree]");
  await Promise.all([c.pg.waitForLoadState(), c.pg.locator("button[value=accept]").click()]);
  assert.match(await c.pg.locator("h2").first().innerText(), /accepted/i);
  await noSideways(c.pg, "quotation accepted");
  await shot(c.pg, "customer-quotation-accepted");
  await go(c.pg, mine.link);
  assert.equal(await c.pg.locator("button[value=accept]").count(), 0, "an answered quotation offers no Accept");
  await c.ctx.close();
});

test("PRO Desk quotation link: decline; replaced and tampered links are refused", async () => {
  const [, other, replaced] = facts.quotes;
  const c = await context(PHONE);
  await go(c.pg, other.link);
  await c.pg.fill("[name=customer_name]", other.customer);
  await Promise.all([c.pg.waitForLoadState(), c.pg.locator("button[value=decline]").click()]);
  assert.match(await c.pg.locator("body").innerText(), /declined/i);
  await noSideways(c.pg, "quotation declined");
  for (const [label, link, words] of [["replaced", replaced.link, /replaced/], ["tampered", tamper(other.link), /not valid/]]) {
    const r = await go(c.pg, link);
    assert.equal(r.status(), 410, label);
    const text = await c.pg.locator("body").innerText();
    assert.match(text, words, `${label}: ${text}`);
    assert.ok(!text.includes(replaced.total) && !text.includes(replaced.customer), `${label} shows the quotation`);
    await customerPage(c.pg, `${label} quotation link`);
    assert.equal((await c.ctx.request.get(`${base}${link}/quotation.pdf`)).status(), 410);
  }
  await c.ctx.close();
});

// ================================================================== 4. Isolation
test("organization A and organization B never see each other's projects, clients, estimates or proposals", async () => {
  const b = await bea();
  for (const url of [`/projects/${facts.project_id}`, `/projects/${facts.signed_project_id}/contract`,
    `/estimates/${facts.estimate_id}/versions/${facts.version_id}`, `/proposals/${facts.proposal_id}`, `/settings/crews/${facts.crew_id}`]) {
    const r = await status(b.ctx, url);
    assert.ok([302, 403, 404].includes(r.code) && !/\/projects\/\d+$/.test(r.location), `org B reaches ${url} (${r.code} ${r.location})`);
  }
  await go(b.pg, "/projects");
  const list = await b.pg.locator("main").innerText();
  assert.ok(list.includes(facts.org_b_project));
  for (const leak of ["Roles walk deck", "Contract and change order job", facts.customer[0]]) assert.ok(!list.includes(leak), `org B list shows ${leak}`);
  await go(b.pg, "/clients");
  assert.ok(!(await b.pg.locator("main").innerText()).includes("Interim Client"));
  const o = await owner();
  assert.equal((await status(o.ctx, `/projects/${facts.org_b_project_id}`)).code, 404);
  await go(o.pg, "/projects");
  assert.ok(!(await o.pg.locator("main").innerText()).includes(facts.org_b_project));
  await go(o.pg, "/clients");
  assert.ok(!(await o.pg.locator("main").innerText()).includes(facts.org_b_client));
});

test("field user (crew, marked field-only): Kevin reaches Field only, sees no costs and cannot move scheduled work", async () => {
  // Joel, 21 Oct 2026: crew are marked field-only by the operator command (flask auth set-field-only).
  assert.match(operator("mark-field-only", facts.kevin[0]), /field_only: yes/);
  const k = await kevin();
  await go(k.pg, "/field/today");
  await noSideways(k.pg, "Field today");
  assert.ok(!/Projects|Estimates|Proposals|Clients|Costs/.test(await navText(k.pg)), "Field shows office navigation");
  const probes = {
    "Office home /": "/", "Projects": "/projects/", "Project page": `/projects/${facts.project_id}`,
    "Estimate (internal costs)": `/estimates/${facts.estimate_id}/versions/${facts.version_id}`,
    "Estimates": "/estimates/", "Proposals": "/proposals/",
    "Proposal": `/proposals/${facts.proposal_id}`, "Contract": `/projects/${facts.signed_project_id}/contract`,
    "Clients": "/clients/", "Company calendar": "/schedule", "Crews": "/settings/crews",
    "Brand profile": "/settings/brand-profile", "Costs and pricing": "/costs-and-pricing/",
    "New schedule item": "/schedule/items/new", "Schedule item": `/schedule/items/${facts.schedule_item_id}`,
    "Close project": `/projects/${facts.project_id}/close`, "Needs attention": "/company-attention",
    "People & Access": "/settings/people",
  };
  for (const [label, url] of Object.entries(probes)) {
    const r = await status(k.ctx, url);
    assert.equal(r.code, 302, `Kevin on ${label} (${url}): ${r.code}`);
    assert.equal(new URL(r.location, base).pathname, "/field/today", `Kevin on ${label} → ${r.location}`);
  }
  for (const url of ["/field/today", "/field/week", "/field/month", "/field/company-today", "/field/projects", "/field/time",
    "/account/password"]) {
    assert.equal((await status(k.ctx, url)).code, 200, `Kevin on ${url}`);
  }
  // No internal cost, markup or customer commercial detail on any page Kevin reaches.
  const estimate = await k.ctx.request.get(`${base}/estimates/${facts.estimate_id}/versions/${facts.version_id}`);
  const landed = await estimate.text();
  for (const marker of [facts.internal.code, facts.internal.unit_cost, facts.internal.markup + "%", "Approved contractor cost"]) {
    assert.ok(!landed.includes(String(marker)), `Kevin sees ${marker}`);
  }
  // Kevin cannot move, retire or add scheduled work (G7), even with a valid form token.
  await go(k.pg, "/field/today");
  const token = await k.pg.locator("meta[name=csrf-token]").getAttribute("content");
  const moved = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
  for (const [url, form] of [[`/schedule/items/${facts.schedule_item_id}`, { scheduled_start: moved, scheduled_end: moved }],
    [`/schedule/items/${facts.schedule_item_id}/retire`, {}], ["/schedule/items/new", { scheduled_start: moved, scheduled_end: moved }],
    [`/schedule/projects/${facts.project_id}/shift`, { days: "3" }]]) {
    const r = await k.ctx.request.post(`${base}${url}`, { form: { csrf_token: token, ...form }, maxRedirects: 0 });
    assert.equal(r.status(), 403, `Kevin POST ${url}: ${r.status()}`);
  }
  const o = await owner();
  await go(o.pg, `/schedule/items/${facts.schedule_item_id}`);
  assert.equal(await o.pg.locator("[name=scheduled_start]").inputValue(), facts.schedule_item_start, "the work did not move");
});

test("supplier and contractor: each is kept to its own side", async () => {
  const s = await store();
  for (const url of ["/", "/projects", `/projects/${facts.project_id}`, `/proposals/${facts.proposal_id}`, "/field/today", "/settings/crews"]) {
    const r = await status(s.ctx, url);
    assert.equal(r.code, 302, `supplier on ${url}: ${r.code}`);
    assert.match(r.location, /\/supplier\//, `supplier on ${url} → ${r.location}`);
  }
  assert.equal((await s.ctx.request.get(`${base}/api/v1/projects`, { maxRedirects: 0 })).status(), 403);
  const o = await owner();
  for (const url of [`/supplier/${facts.store_supplier_id}/`, `/supplier/${facts.store_supplier_id}/pro-desk/`,
    `/supplier/${facts.store_supplier_id}/pro-desk/${facts.quotes[0].quote_id}`]) {
    assert.equal((await status(o.ctx, url)).code, 403, `office on ${url}`);
  }
});

test("supplier A and supplier B: neither opens the other's PRO Desk, quotations or prices", async () => {
  const r = await rival();
  const sid = facts.store_supplier_id;
  for (const url of [`/supplier/${sid}/`, `/supplier/${sid}/pro-desk/`, `/supplier/${sid}/pro-desk/${facts.quotes[0].quote_id}`,
    `/supplier/${sid}/pro-desk/${facts.quotes[0].quote_id}/quotation.pdf`, `/supplier/${sid}/pro-desk/prices`]) {
    const res = await status(r.ctx, url);
    assert.ok([403, 404].includes(res.code), `rival on ${url}: ${res.code}`);
  }
  const own = `/supplier/${facts.rival_supplier_id}/pro-desk/${facts.quotes[0].quote_id}`;
  assert.equal((await status(r.ctx, own)).code, 404, "another store's quotation under the rival's own address");
  await go(r.pg, `/supplier/${facts.rival_supplier_id}/pro-desk/`);
  const page = await r.pg.locator("body").innerText();
  for (const q of facts.quotes) assert.ok(!page.includes(q.customer) && !page.includes(q.number), `rival sees ${q.number}`);
});

test("a customer link holder reaches only their own document", async () => {
  const c = await context(PHONE);
  await go(c.pg, facts.used_proposal_link); // a real, accepted proposal link
  const cred = facts.used_proposal_link.split("/").pop();
  for (const url of ["/projects", `/projects/${facts.signed_project_id}`, `/projects/${facts.signed_project_id}/contract`, "/field/today"]) {
    const r = await status(c.ctx, url);
    assert.equal(r.code, 302, url); assert.match(r.location, /\/login/, url);
  }
  // One kind of link never opens another kind of document.
  assert.equal((await status(c.ctx, `/sign/${cred}`)).code, 404);
  assert.equal((await status(c.ctx, `/quote/${cred}`)).code, 410);
  const signCred = facts.contract_sign_link.split("/").pop();
  assert.equal((await status(c.ctx, `/proposal/${signCred}`)).code, 410);
  assert.equal((await status(c.ctx, `/supplier/${facts.store_supplier_id}/pro-desk/`)).location.includes("/supplier/login"), true);
  await c.ctx.close();
});

test("no page in the walk answered with a server error", async () => {
  assert.deepEqual(serverErrors, []);
});

// ================================================================== Crew Access acceptance (Joel, 21 Oct 2026)
test("crew access: Ben invites two workers as Field only; each activates on a phone; only the assigned one sees the job; schedule change shows; deactivation is immediate", async () => {
  const o = await owner();
  const stamp = Date.now() % 100000;
  const workers = [[`Crew One ${stamp} (synthetic)`, `crew.one.${stamp}@example.invalid`, "Synthetic-crew-one-1"],
                   [`Crew Two ${stamp} (synthetic)`, `crew.two.${stamp}@example.invalid`, "Synthetic-crew-two-1"]];
  const phones = [];
  for (const [name, email, password] of workers) {
    // 1. Ben invites the worker (Field only) from People & Access.
    await go(o.pg, "/settings/people/new");
    await o.pg.fill("[name=display_name]", name);
    await o.pg.fill("[name=email]", email);
    await o.pg.check("[name=field_only]");
    await Promise.all([o.pg.waitForLoadState(), o.pg.locator("main form button[type=submit]").click()]);
    assert.match(await flash(o.pg), /was added/);
    assert.equal(await o.pg.locator("[data-field-only]").getAttribute("data-field-only"), "yes");
    // 2. The worker activates the account from the invitation, on an iPhone-sized screen.
    const mail = newestMail("ACCOUNT_INVITATION", email);
    assert.equal(mail.count, 1);
    const p = await context(PHONE);
    await go(p.pg, mail.body.match(/\/reset-password#[A-Za-z0-9_\-.]+/)[0]);
    await p.pg.fill("[name=password]", password);
    await p.pg.fill("[name=confirm_password]", password);
    await Promise.all([p.pg.waitForLoadState(), p.pg.locator("form button[type=submit]").click()]);
    // 3. Signs in: lands on Field, no sideways scrolling.
    await signIn(p, email, password);
    await go(p.pg, "/field/today");
    assert.match(p.pg.url(), /\/field\/today$/);
    await noSideways(p.pg, "crew Field today");
    phones.push(p);
  }
  // Ben assigns worker 1 to the scheduled work.
  await go(o.pg, `/schedule/items/${facts.schedule_item_id}`);
  const option = o.pg.locator("select[name=worker_user_id] option", { hasText: workers[0][0] });
  await o.pg.selectOption("select[name=worker_user_id]", await option.getAttribute("value"));
  await Promise.all([o.pg.waitForLoadState(), o.pg.locator("#schedule-assignments form.form-grid button[type=submit]").first().click()]);
  const [one, two] = phones;
  // 4. Worker 1 sees the assigned job and its drawings; worker 2 sees nothing of it.
  await go(one.pg, "/field/projects");
  assert.ok(await one.pg.locator(`a[href$="/field/projects/${facts.project_id}"]`).count() >= 1, "worker 1 sees the assigned job");
  assert.equal((await status(one.ctx, `/field/projects/${facts.project_id}/drawings`)).code, 200);
  await go(two.pg, "/field/projects");
  assert.equal(await two.pg.locator(`a[href$="/field/projects/${facts.project_id}"]`).count(), 0, "worker 2 does not see it");
  assert.notEqual((await status(two.ctx, `/field/projects/${facts.project_id}/drawings`)).code, 200);
  assert.equal((await status(two.ctx, `/api/v1/projects/${facts.project_id}`)).code, 404);
  // 5. Neither reaches internal costs or office pages (server-level: direct URLs and POSTs).
  for (const p of phones) {
    for (const url of [`/estimates/${facts.estimate_id}/versions/${facts.version_id}`, "/costs-and-pricing/", "/proposals/",
      "/settings/people", `/projects/${facts.project_id}`]) {
      const r = await status(p.ctx, url);
      assert.equal(r.code, 302, url); assert.equal(new URL(r.location, base).pathname, "/field/today", url);
    }
    const token = await p.pg.locator("meta[name=csrf-token]").getAttribute("content");
    const post = await p.ctx.request.post(`${base}/schedule/items/${facts.schedule_item_id}`,
      { form: { csrf_token: token, scheduled_start: facts.schedule_item_start, scheduled_end: facts.schedule_item_start }, maxRedirects: 0 });
    assert.equal(post.status(), 403, "crew cannot change the schedule");
  }
  // 6. Ben moves the work; 7. worker 1 sees the new date on Field.
  const moved = new Date(Date.now() + 2 * 86400000).toISOString().slice(0, 10);
  await go(o.pg, `/schedule/items/${facts.schedule_item_id}`);
  await o.pg.fill("[name=scheduled_start]", moved);
  await o.pg.fill("[name=scheduled_end]", moved);
  await Promise.all([o.pg.waitForLoadState(), o.pg.locator("form button[type=submit]", { hasText: /save|update/i }).first().click()]);
  await go(o.pg, `/schedule/items/${facts.schedule_item_id}`);
  assert.equal(await o.pg.locator("[name=scheduled_start]").inputValue(), moved, "the move was saved");
  const month = await one.ctx.request.get(`${base}/field/month?year=${moved.slice(0, 4)}&month=${Number(moved.slice(5, 7))}&day=${Number(moved.slice(8, 10))}`);
  assert.equal(month.status(), 200);
  assert.ok((await month.text()).includes("Deck framing"), "worker 1 sees the work on its new date");
  // 8. Ben deactivates worker 1; 9. their next request is refused immediately.
  await go(o.pg, "/settings/people");
  await Promise.all([o.pg.waitForLoadState(), o.pg.locator(".register-row", { hasText: workers[0][0] }).click()]);
  await Promise.all([o.pg.waitForLoadState(), o.pg.getByRole("button", { name: "Deactivate sign-in" }).click()]);
  const after = await status(one.ctx, "/field/today");
  assert.equal(after.code, 302); assert.match(after.location, /\/login/);
  assert.match(await o.pg.locator("[data-person-history]").innerText(), /Invitation emailed[\s\S]*Chose a password|Chose a password[\s\S]*Invitation emailed/);
  await shot(o.pg, "crew-access-history");
  for (const p of phones) await p.ctx.close();
});
