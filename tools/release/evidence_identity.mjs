// One CalibraytAI identity, in the browser, across two real sites (26 Oct 2026). Synthetic data only.
// Production (identity provider) and the Training Centre (connected) run as separate processes with separate
// databases (tests/identity_pair_site.py) and talk over HTTP, as the hosted sites do. Proves Joel's rules: one email
// and one password everywhere a person is authorized; changes and resets from either site work on both; adding a
// person creates one identity and gives the owner a link to text; roles stay per site; practice personas stay local.
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const DESK = { width: 1280, height: 900 };
const JOEL = ["joel.owner@example.com", "Synthetic-Joel-prod-1"];
const KEVIN = "kevin.reviewer@example.com";
let browser, P, T, PB, TB, mailP, mailT;
const servers = [];
const contexts = [];
const S = {};

function start(role, args) {
  const child = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/identity_pair_site.py"), role, ...args], {
    cwd: REPO, env: { ...process.env, MAIL_PRODUCTION: mailP, MAIL_TRAINING: mailT }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  child.stdout.on("data", (c) => (out += c)); child.stderr.on("data", (c) => (out += c));
  servers.push(child);
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error(`${role} did not start\n` + out)), 300000);
    const poll = () => {
      if (out.includes(`READY ${args[0]}`)) { clearTimeout(t); return resolve(); }
      if (child.exitCode !== null) { clearTimeout(t); return reject(new Error(`${role} exited\n` + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
}

before(async () => {
  mailP = fs.mkdtempSync(path.join(os.tmpdir(), "identity-mail-p-"));
  mailT = fs.mkdtempSync(path.join(os.tmpdir(), "identity-mail-t-"));
  P = await freePort(); T = await freePort();
  PB = `http://127.0.0.1:${P}`; TB = `http://127.0.0.1:${T}`;
  await Promise.all([start("production", [String(P), "0", String(T)]), start("training", [String(T), String(P)])]);
  browser = await launch();
});
after(async () => {
  for (const c of contexts) await c.close().catch(() => {});
  await browser?.close();
  for (const s of servers) s.kill();
});

let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function page() {
  const ctx = await browser.newContext({ viewport: DESK });
  contexts.push(ctx);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => { throw e; });
  return pg;
}
async function signIn(pg, base, email, password) {
  await pg.goto(base + "/login");
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await Promise.all([pg.waitForNavigation(), pg.press("input[name=password]", "Enter")]);
  return !/\/login/.test(pg.url());
}
async function freshSignIn(base, email, password) { return signIn(await page(), base, email, password); }
function lastMail(dir, to) {
  const files = fs.readdirSync(dir).map((n) => path.join(dir, n)).filter((n) => fs.readFileSync(n, "utf8").includes(`To: ${to}`)).sort();
  return files.length ? fs.readFileSync(files[files.length - 1], "utf8") : "";
}
async function setPassword(link, password) {
  const pg = await page();
  await pg.goto(link);
  await pg.waitForLoadState("networkidle");
  const f = pg.locator("input[type=password]");
  await f.nth(0).fill(password); await f.nth(1).fill(password);
  await Promise.all([pg.waitForNavigation(), f.nth(1).press("Enter")]);
  return pg;
}

step("Joel: his Production password signs him in to both sites; the old Training Centre one is refused", async () => {
  S.joel = await page();
  assert.ok(await signIn(S.joel, PB, ...JOEL), "Production");
  assert.ok(!(await freshSignIn(TB, JOEL[0], "Synthetic-admin-training-1")), "old Training Centre password");
  S.joelT = await page();
  assert.ok(await signIn(S.joelT, TB, ...JOEL), "Training Centre with the Production password");
});

step("Joel keeps the Training administrator's rights there", async () => {
  assert.equal((await S.joelT.goto(TB + "/training/admin")).status(), 200);
  assert.equal((await S.joelT.goto(TB + "/settings/people")).status(), 200);
});

step("Adding Kevin once on the Training Centre: Production's one-time link with Text it, emailed by Production", async () => {
  const pg = S.joelT;
  await pg.goto(TB + "/settings/people/new");
  await pg.fill("input[name=display_name]", "Kevin Garnett");
  await pg.fill("input[name=email]", KEVIN);
  await Promise.all([pg.waitForNavigation(), pg.press("input[name=email]", "Enter")]);
  S.link = (await pg.content()).match(/id="one-time-link" value="([^"]+)"/)?.[1] || "";
  assert.ok(S.link.startsWith(PB + "/reset-password#"), S.link.replace(/#.*/, "#…"));
  assert.equal(await pg.locator("[data-text-it]").count(), 1);
  assert.match(lastMail(mailP, KEVIN), /reset-password#/);
  assert.equal(lastMail(mailT, KEVIN), "");
});

step("Kevin sets his one password with the link; the page points him to the Training Centre", async () => {
  const pg = await setPassword(S.link, "Synthetic-Kevin-pass-1");
  assert.match(await pg.content(), /Training Centre/);
});

step("Kevin on the Training Centre: Contractor pathway, Workflow Map, practice project, Field; no admin areas", async () => {
  const pg = await page();
  assert.ok(await signIn(pg, TB, KEVIN, "Synthetic-Kevin-pass-1"));
  await pg.goto(TB + "/training");
  await pg.check("input[name=role][value=OWNER]");
  await Promise.all([pg.waitForNavigation(), pg.locator("form button[type=submit]").first().click()]);
  assert.ok((await pg.locator('a[href*="/training/lessons/"]').count()) > 10);
  assert.equal((await pg.goto(TB + "/training/workflow")).status(), 200);
  assert.match(await (await pg.goto(TB + "/projects/")).text(), /Harbour Lane Pool Deck \(training\)/);
  assert.equal((await pg.goto(TB + "/field/today")).status(), 200);
  assert.equal((await pg.goto(TB + "/settings/people")).status(), 403);
});

step("Production refuses Kevin politely (identity only) and points to the Training Centre", async () => {
  const pg = await page();
  assert.ok(!(await signIn(pg, PB, KEVIN, "Synthetic-Kevin-pass-1")));
  const html = await pg.content();
  assert.match(html, /give no access to this site/);
  assert.ok(html.includes(TB));
});

step("Forgot password started on the Training Centre: Production emails it; new password works, old one stops", async () => {
  const pg = await page();
  await pg.goto(TB + "/forgot-password");
  await pg.fill("input[name=email]", KEVIN);
  await Promise.all([pg.waitForNavigation(), pg.press("input[name=email]", "Enter")]);
  const mail = lastMail(mailP, KEVIN);
  assert.match(mail, /Reset your CalibraytAI password/);
  await setPassword(mail.match(/(http\S*\/reset-password#\S+)/)[1], "Synthetic-Kevin-pass-2");
  assert.ok(await freshSignIn(TB, KEVIN, "Synthetic-Kevin-pass-2"));
  assert.ok(!(await freshSignIn(TB, KEVIN, "Synthetic-Kevin-pass-1")));
});

step("Change password on the Training Centre: the new one works, the old one stops", async () => {
  const pg = await page();
  assert.ok(await signIn(pg, TB, KEVIN, "Synthetic-Kevin-pass-2"));
  await pg.goto(TB + "/account/password");
  await pg.fill("input[name=current_password]", "Synthetic-Kevin-pass-2");
  await pg.fill("input[name=password]", "Synthetic-Kevin-pass-3");
  await pg.fill("input[name=confirm_password]", "Synthetic-Kevin-pass-3");
  await Promise.all([pg.waitForNavigation(), pg.press("input[name=confirm_password]", "Enter")]);
  assert.ok(await freshSignIn(TB, KEVIN, "Synthetic-Kevin-pass-3"));
  assert.ok(!(await freshSignIn(TB, KEVIN, "Synthetic-Kevin-pass-2")));
});

step("Joel changes his password on Production: it works on both sites at once", async () => {
  const pg = S.joel;
  await pg.goto(PB + "/account/password");
  await pg.fill("input[name=current_password]", JOEL[1]);
  await pg.fill("input[name=password]", "Synthetic-Joel-prod-2");
  await pg.fill("input[name=confirm_password]", "Synthetic-Joel-prod-2");
  await Promise.all([pg.waitForNavigation(), pg.press("input[name=confirm_password]", "Enter")]);
  assert.ok(await freshSignIn(TB, JOEL[0], "Synthetic-Joel-prod-2"));
  assert.ok(await freshSignIn(PB, JOEL[0], "Synthetic-Joel-prod-2"));
  assert.ok(!(await freshSignIn(TB, ...JOEL)));
});

step("A practice persona still signs in locally on the Training Centre", async () => {
  assert.ok(await freshSignIn(TB, "ben@training.calibraytai.invalid", "Synthetic-ben-training-1"));
});
