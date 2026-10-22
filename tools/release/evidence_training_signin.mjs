// Release evidence for the training site's sign-in, password recovery and owner review (Joel, 21 Oct 2026), in a
// real browser against a local training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT
// on, the synthetic training company plus a synthetic administrator, mail captured, never delivered).
//
// Signed out: every sign-in page states the method (training account; not the live password; no ChatGPT), a wrong
// password is refused, Forgot password says this site cannot send email and who gives a link (same words for any
// address). The administrator signs in, reviews the Contractor and Supplier Workflow Maps without registering:
// every stage expands, every link answers, a lesson and an acceptance test open read-only and come back to the
// same stage; desktop and a 390-pixel iPhone without sideways scrolling. The administrator gives a supplier
// person a one-time link from Company -> Suppliers; it opens on this site (not localhost), sets the password once,
// the person signs in, and the same link is refused the second time. Any 500 or page error fails the walk.
//
// Run: EVIDENCE_REPO=$PWD node --test --test-concurrency=1 tools/release/evidence_training_signin.mjs
import assert from "node:assert/strict";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

let browser, server, base, facts;
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const serverErrors = [];
const pageErrors = [];
const contexts = [];
const NEW_PW = "Synthetic-darcy-renewed-77";

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
  for (const c of contexts) await c.close().catch(() => {});
  await browser?.close(); server?.kill();
  console.log(`TRAINING_SIGNIN_SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

async function page(viewport, name) {
  const ctx = await browser.newContext({ viewport });
  contexts.push(ctx);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${name}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
}
async function noSideways(pg, label) {
  const [sw, iw] = await pg.evaluate(() => [document.documentElement.scrollWidth, window.innerWidth]);
  assert.ok(sw <= iw + 1, `${label}: page scrolls sideways (${sw} > ${iw})`);
}
async function signInOffice(pg, email, password) {
  await pg.goto(`${base}/training/signin`);
  await Promise.all([pg.waitForNavigation(), pg.click('[data-signin="contractor"]')]);
  await pg.fill("input[name=email]", email);
  await pg.fill("input[name=password]", password);
  await Promise.all([pg.waitForNavigation(), pg.locator("form button[type=submit]").first().click()]);
}
const admin = () => facts.people.admin;

for (const [label, vp] of [["desktop", DESK], ["iPhone", PHONE]]) {
  test(`signed out (${label}): the sign-in method is stated, a wrong password is refused, Forgot password is honest`, async () => {
    const { pg } = await page(vp, `signed-out-${label}`);
    await pg.goto(`${base}/training/signin`);
    assert.match(await pg.textContent("[data-training-signin-method]"), /training account/);
    await noSideways(pg, "training sign-in");
    await Promise.all([pg.waitForNavigation(), pg.click('[data-signin="contractor"]')]);
    assert.match(await pg.textContent("h1"), /Training sign in/);
    assert.match(await pg.textContent("[data-training-signin-method]"), /ChatGPT/);
    await pg.fill("input[name=email]", admin().email);
    await pg.fill("input[name=password]", "not-the-password");
    await Promise.all([pg.waitForNavigation(), pg.locator("form button[type=submit]").first().click()]);
    assert.equal(new URL(pg.url()).pathname, "/login", "a wrong password stays on the sign-in page");
    await noSideways(pg, "login");
    await Promise.all([pg.waitForNavigation(), pg.click(".login-forgot-link")]);
    assert.ok(await pg.locator("[data-no-email]").isVisible(), "the forgot page says the site cannot send email");
    await pg.fill("input[name=email]", admin().email);
    await Promise.all([pg.waitForNavigation(), pg.click("form button[type=submit]")]);
    const known = await pg.textContent("[data-no-email]");
    assert.match(known, /no email is on its way/);
    await pg.goto(`${base}/forgot-password`);
    await pg.fill("input[name=email]", "nobody@training-test.invalid");
    await Promise.all([pg.waitForNavigation(), pg.click("form button[type=submit]")]);
    assert.equal(await pg.textContent("[data-no-email]"), known, "the same words for any address");
    await noSideways(pg, "forgot sent");
    await pg.goto(`${base}/supplier/login`);
    assert.match(await pg.textContent("[data-training-signin-method]"), /training account/);
  });

  test(`administrator (${label}): both Workflow Maps without registering; stages, links, lessons and tests`, async () => {
    const s = await page(vp, `admin-${label}`);
    const { pg, ctx } = s;
    await signInOffice(pg, admin().email, admin().password);
    assert.equal(new URL(pg.url()).pathname, "/training");
    assert.ok(await pg.locator("[data-owner-review-start]").isVisible(), "owner review offered without registering");
    for (const key of ["contractor", "supplier"]) {
      await Promise.all([pg.waitForNavigation(), pg.locator(`[data-review-map-link="${key}"]`).first().click()]);
      assert.equal(new URL(pg.url()).pathname, `/training/review/${key}`);
      await noSideways(pg, `${key} map`);
      const cards = await pg.locator("[data-wf-card]").evaluateAll((els) => els.map((e) => e.getAttribute("data-wf-card")));
      assert.ok(cards.length >= 5, `${key}: stages shown`);
      for (const id of cards) {
        await pg.locator(`[data-wf-card="${id}"]`).click();
        assert.ok(await pg.locator(`[data-wf-page="${id}"]`).isVisible(), `${key}: stage ${id} expands`);
        assert.equal(new URL(pg.url()).searchParams.get("stage"), id);
      }
      // every link in the map answers (no 404/500, nobody sent to sign in)
      const hrefs = await pg.locator("[data-wf-map] a[href]").evaluateAll((as) =>
        [...new Set(as.map((a) => a.getAttribute("href")).filter((h) => h && !h.startsWith("#")).map((h) => h.split("#")[0]))]);
      for (const href of hrefs) {
        const r = await ctx.request.get(`${base}${href}`, { maxRedirects: 0 });
        assert.ok([200, 302].includes(r.status()), `${key}: ${href} answered ${r.status()}`);
        if (r.status() === 302) assert.ok(!/\/login|\/signin/.test(r.headers().location || ""), `${key}: ${href} asks to sign in`);
      }
      // a lesson and an acceptance test open read-only and come back to the same stage
      const stage = cards[1];
      await pg.locator(`[data-wf-card="${stage}"]`).click();
      for (const kind of ["lessons", "uat"]) {
        const link = pg.locator(`[data-wf-page="${stage}"] a[href^="/training/review/${kind}/"]`).first();
        if ((await link.count()) === 0) continue;
        await Promise.all([pg.waitForNavigation(), link.click()]);
        assert.ok(await pg.locator(kind === "lessons" ? "[data-review-lesson]" : "[data-review-uat]").isVisible());
        assert.equal(await pg.locator("form[data-tick-form], form[action*='/uat/']").count(), 0, "read-only");
        await noSideways(pg, `${key} ${kind} review`);
        await Promise.all([pg.waitForNavigation(), pg.locator("[data-review-back]").click()]);
        assert.equal(new URL(pg.url()).pathname, `/training/review/${key}`);
        assert.equal(new URL(pg.url()).searchParams.get("stage"), stage, "back at the same stage");
        assert.ok(await pg.locator(`[data-wf-page="${stage}"]`).isVisible());
      }
      await pg.goto(`${base}/training`);
    }
    const trainees = await ctx.request.get(`${base}/training/admin`);
    assert.equal(trainees.status(), 200, "the administrator dashboard opens");
  });
}

test("administrator gives a supplier person a one-time link; it works once on this site", async () => {
  const { pg } = await page(DESK, "admin-suppliers");
  await signInOffice(pg, admin().email, admin().password);
  await pg.goto(`${base}/suppliers`);
  const form = pg.locator("[data-supplier-send-link]").first();
  await Promise.all([pg.waitForNavigation(), form.locator("button").click()]);
  const url = await pg.inputValue("#one-time-link");
  assert.ok(url.startsWith(base + "/reset-password#"), `the link opens on this site, not localhost (${url.slice(0, 40)}...)`);
  const who = await pg.textContent("#one-time-link-heading");
  const supplierKey = Object.keys(facts.people).find((k) => who.includes(facts.people[k].name.split(" (")[0]));
  assert.ok(supplierKey, "the link names the person");
  const fresh = await page(PHONE, "supplier-phone");
  await fresh.pg.goto(url);
  // the credential is after "#": the page's script posts it, then the password form opens (22 Oct 2026)
  await fresh.pg.waitForSelector("input[name=password]");
  assert.ok(!fresh.pg.url().includes("#"), "the credential is taken out of the address bar");
  await fresh.pg.fill("input[name=password]", NEW_PW);
  await fresh.pg.fill("input[name=confirm_password]", NEW_PW);
  await Promise.all([fresh.pg.waitForNavigation(), fresh.pg.click("form button[type=submit]")]);
  await noSideways(fresh.pg, "reset complete (phone)");
  await fresh.pg.goto(`${base}/supplier/login`);
  await fresh.pg.fill("input[name=email]", facts.people[supplierKey].email);
  await fresh.pg.fill("input[name=password]", NEW_PW);
  await Promise.all([fresh.pg.waitForNavigation(), fresh.pg.locator("form button[type=submit]").first().click()]);
  assert.ok(!/\/login/.test(new URL(fresh.pg.url()).pathname), "the supplier person signs in with the new password");
  const again = await page(DESK, "reuse");
  await again.pg.goto(url);
  await again.pg.waitForFunction(() => !document.querySelector("[data-reset-open]"));
  const body = await again.pg.textContent("body");
  const reused = (await again.pg.locator("input[name=password]").count()) === 0 || /no longer|expired|used|not valid|invalid/i.test(body);
  assert.ok(reused, "the same link does not work twice");
});

test("the supplier map from the Supplier Hub and the contractor map from the office, with permissions", async () => {
  const { pg, ctx } = await page(DESK, "admin-office");
  await signInOffice(pg, admin().email, admin().password);
  await pg.goto(`${base}/workflow?stage=c-price`);
  assert.ok((await pg.locator('[data-wf-map] a[href^="/training/review/lessons/"]').count()) > 0,
    "an unregistered administrator's office map opens lessons in owner review");
  const supplierMap = await ctx.request.get(`${base}/supplier/${facts.supplier_id}/workflow`, { maxRedirects: 0 });
  assert.notEqual(supplierMap.status(), 200, "office staff do not open the Supplier Hub's own map");
  const darcy = await page(PHONE, "darcy-phone");
  await darcy.pg.goto(`${base}/supplier/login`);
  await darcy.pg.fill("input[name=email]", facts.people.pat.email);
  await darcy.pg.fill("input[name=password]", facts.people.pat.password);
  await Promise.all([darcy.pg.waitForNavigation(), darcy.pg.locator("form button[type=submit]").first().click()]);
  const r = await darcy.pg.goto(`${base}/supplier/${facts.supplier_id}/workflow`);
  assert.equal(r.status(), 200, "supplier staff open the Supplier Workflow Map from the Supplier Hub");
  await noSideways(darcy.pg, "supplier map (phone)");
  const review = await darcy.ctx.request.get(`${base}/training/review/supplier`, { maxRedirects: 0 });
  assert.equal(review.status(), 403, "owner review is for administrators only");
});
