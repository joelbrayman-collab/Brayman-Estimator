// Release evidence for Cal Assistant Phase 1 — Find It (17 Oct 2026), in Google Chrome.
// Same harness as the other release checks: a local office on a temporary database, synthetic data only.
import assert from "node:assert/strict";
import test, { after, before } from "node:test";
import { freePort, launch, startOffice } from "./evidence_common.mjs";

let browser, office, base;
before(async () => {
  const port = await freePort();
  office = startOffice(port); await office.ready;
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => { await browser?.close(); office?.child.kill(); });

async function signedIn(width, height) {
  const ctx = await browser.newContext({ viewport: { width, height } });
  const pg = await ctx.newPage();
  const errors = [];
  pg.on("pageerror", (e) => errors.push(String(e)));
  await pg.goto(`${base}/login`);
  await pg.fill("input[name=email]", "office@example.com");
  await pg.fill("input[name=password]", "office-test-password");
  await pg.click("button[type=submit]");
  await pg.waitForLoadState();
  return { ctx, pg, errors };
}
async function ask(pg, query) {
  await pg.fill("#cal-query", query);
  await pg.press("#cal-query", "Enter");
  await pg.waitForFunction(() => {
    const r = document.querySelector("#cal-results");
    return r && r.innerText.trim() && !r.innerText.includes("Looking");
  });
}
async function noSideways(pg, width) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `page scrolls sideways by ${o}px at ${width}px`);
}

test("signed out: no Cal and the endpoint sends visitors to sign-in", async () => {
  const ctx = await browser.newContext();
  const pg = await ctx.newPage();
  await pg.goto(`${base}/login`);
  assert.equal(await pg.locator("#cal-launch").count(), 0);
  const res = await ctx.request.get(`${base}/cal/find?q=harbour`, { maxRedirects: 0 });
  assert.equal(res.status(), 302);
  assert.ok((res.headers()["location"] || "").includes("/login"));
  await ctx.close();
});

for (const [label, width, height] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
  test(`${label}: header shows Cal, closed, and no disabled Search button`, async () => {
    const { ctx, pg, errors } = await signedIn(width, height);
    assert.ok(await pg.locator("#cal-launch").isVisible());
    assert.ok(await pg.locator("#cal-panel").isHidden());
    assert.equal(await pg.locator('[aria-label="Search (coming soon)"]').count(), 0);
    assert.equal(await pg.locator(".header-actions .bi-search").count(), 0);
    const src = await pg.locator("#cal-launch img").getAttribute("src");
    assert.ok(src.includes("img/cal-assistant/cal-64.png"), src);
    assert.ok(await pg.locator("#cal-launch img").evaluate((i) => i.complete && i.naturalWidth > 0));
    await noSideways(pg, width);
    assert.deepEqual(errors, []);
    await ctx.close();
  });
  test(`${label}: opens on click with the query box focused; Esc closes and returns focus`, async () => {
    const { ctx, pg } = await signedIn(width, height);
    const url = pg.url();
    await pg.click("#cal-launch");
    assert.ok(await pg.locator("#cal-panel").isVisible());
    await pg.waitForFunction(() => document.activeElement && document.activeElement.id === "cal-query");
    const box = await pg.locator("#cal-panel").boundingBox();
    assert.ok(box.x >= 0 && box.x + box.width <= width, JSON.stringify(box));
    assert.ok((await pg.locator(".cal-find-btn").boundingBox()).height >= 44);
    await pg.keyboard.press("Escape");
    assert.ok(await pg.locator("#cal-panel").isHidden());
    assert.equal(await pg.evaluate(() => document.activeElement.id), "cal-launch");
    await pg.click("#cal-launch");
    await pg.mouse.click(20, height - 20);
    assert.ok(await pg.locator("#cal-panel").isHidden());
    assert.equal(pg.url(), url);
    await ctx.close();
  });
  test(`${label}: the "Upcoming deliveries" example answers with the delivery schedule`, async () => {
    const { ctx, pg } = await signedIn(width, height);
    await pg.click("#cal-launch");
    const chip = pg.locator('[data-cal-example="Upcoming deliveries"]');
    assert.equal(await chip.count(), 1);
    await chip.click();
    await pg.waitForSelector(".cal-group");
    const text = await pg.locator("#cal-results").innerText();
    assert.ok(text.toLowerCase().includes("delivery schedule"), text);
    assert.ok(await pg.locator('#cal-results a.cal-result[href="/deliveries"]').count() >= 1);
    await ctx.close();
  });
  test(`${label}: a tool result opens the page; nothing found is said plainly`, async () => {
    const { ctx, pg } = await signedIn(width, height);
    await pg.click("#cal-launch");
    await ask(pg, "zzqx unicorn ranch");
    assert.ok((await pg.locator("#cal-results").innerText()).includes("could not find"));
    assert.equal(await pg.locator("#cal-results a.cal-result").count(), 0);
    await ask(pg, "stair calculator");
    const link = pg.locator('#cal-results a.cal-result[href="/calculators/stairs"]').first();
    assert.ok(await link.isVisible());
    await Promise.all([pg.waitForURL(/\/calculators\/stairs$/), link.click()]);
    await noSideways(pg, width);
    await ctx.close();
  });
  test(`${label}: existing Help is still on the page`, async () => {
    const { ctx, pg } = await signedIn(width, height);
    assert.ok(await pg.locator("details.contextual-help").count() > 0);
    assert.ok(await pg.locator("[data-help-voice]").count() > 0);
    await ctx.close();
  });
}
