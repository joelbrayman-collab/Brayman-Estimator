// Release evidence, same assertions as tests/test_trade_calculator_pages_browser.py (decision 6).
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
  await pg.goto(`${base}/login`);
  await pg.fill("input[name=email]", "office@example.com");
  await pg.fill("input[name=password]", "office-test-password");
  await pg.click("button[type=submit]");
  await pg.waitForLoadState();
  return { ctx, pg };
}
async function fill(pg, values) {
  for (const [f, v] of Object.entries(values)) {
    if (f === "unit_system" || f === "sheet_size") await pg.selectOption(`#${f}`, v); else await pg.fill(`#${f}`, v);
  }
}
async function submit(pg) { await Promise.all([pg.waitForLoadState(), pg.click("button[value=calculate]")]); await pg.waitForLoadState(); }
async function noSideways(pg, width) {
  const o = await pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
  assert.ok(o <= 1, `page scrolls sideways by ${o}px at ${width}px`);
}
const CASES = {
  roofing: [{ plane_length_1: "40", plane_width_1: "30", plane_pitch_1: "6", waste_percent: "10", bundle_coverage: "33.3", underlayment_coverage: "400" },
    { "[data-roof-area]": "1341.64 ft²", "[data-bundles]": "45 shingle bundles", "[data-rolls]": "4 underlayment rolls" }],
  siding: [{ wall_length_1: "100", wall_height_1: "9", gable_base_1: "24", gable_height_1: "6", opening_width_1: "3", opening_height_1: "5", opening_count_1: "4", waste_percent: "10", piece_coverage: "100" },
    { "[data-net-area]": "912", "[data-pieces]": "11 pieces" }],
  drywall: [{ wall_length_1: "40", wall_height_1: "8", ceiling_length_1: "12", ceiling_width_1: "10", opening_width_1: "3", opening_height_1: "7", waste_percent: "10", sheet_size: "4x8" },
    { "[data-net-area]": "419", "[data-sheets]": "15 sheets of 4 × 8 ft" }],
  flooring: [{ room_length_1: "12", room_width_1: "15", waste_percent: "8", box_coverage: "20" },
    { "[data-floor-area]": "180", "[data-boxes]": "10 boxes", "[data-perimeter]": "54" }],
  footing: [{ footing_length_1: "20", footing_width_1: "2", footing_thickness_1: "12", footing_count_1: "2", waste_percent: "5" },
    { "[data-volume]": "2.963 yd³", "[data-order-volume]": "3.111 yd³" }],
};
const BAD = [
  ["flooring", { room_length_1: "-12", room_width_1: "15", waste_percent: "0" }, "greater than zero"],
  ["drywall", { wall_length_1: "abc", wall_height_1: "8", waste_percent: "0" }, "number"],
  ["roofing", { plane_length_1: "40", plane_width_1: "30", plane_pitch_1: "6" }, "Waste"],
  ["footing", { waste_percent: "0" }, "at least one footing"],
];
for (const [label, width, height] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
  for (const [kind, [values, expected]] of Object.entries(CASES)) {
    test(`${label}: ${kind} gives the hand-worked figures`, async () => {
      const { ctx, pg } = await signedIn(width, height);
      await pg.goto(`${base}/calculators/${kind}`);
      assert.ok(await pg.locator(`[data-trade-form=${kind}]`).isVisible());
      await fill(pg, values); await submit(pg);
      const result = pg.locator(`[data-trade-result=${kind}]`);
      assert.ok(await result.isVisible());
      for (const [sel, text] of Object.entries(expected)) assert.ok((await result.locator(sel).first().textContent()).includes(text), `${kind} ${sel}`);
      assert.ok((await result.textContent()).includes("not on an estimate"));
      await noSideways(pg, width); await ctx.close();
    });
  }
  test(`${label}: metric footing and the unit labels switch`, async () => {
    const { ctx, pg } = await signedIn(width, height);
    await pg.goto(`${base}/calculators/footing`);
    const label = pg.locator("label[for=footing_length_1]");
    let t = await label.innerText(); assert.ok(t.includes("feet") && !t.includes("metres"));
    await pg.selectOption("#unit_system", "metric");
    t = await label.innerText(); assert.ok(t.includes("metres") && !t.includes("feet"));
    assert.ok((await pg.locator("label[for=footing_thickness_1]").innerText()).includes("millimetres"));
    await fill(pg, { footing_length_1: "6", footing_width_1: "0.6", footing_thickness_1: "300", waste_percent: "0" });
    await submit(pg);
    const volume = await pg.locator("[data-volume]").textContent();
    assert.ok(volume.includes("1.413 yd³") && volume.includes("1.080 m³"), volume);
    assert.equal(await pg.locator("#unit_system").inputValue(), "metric");
    await ctx.close();
  });
  for (const [kind, values, message] of BAD) {
    test(`${label}: bad ${kind} entry shows a message, not a result`, async () => {
      const { ctx, pg } = await signedIn(width, height);
      await pg.goto(`${base}/calculators/${kind}`);
      await fill(pg, values); await submit(pg);
      const alert = pg.locator("[role=alert]");
      assert.ok(await alert.isVisible());
      assert.ok((await alert.textContent()).toLowerCase().includes(message.toLowerCase()));
      assert.equal(await pg.locator(`[data-trade-result=${kind}]`).count(), 0);
      await noSideways(pg, width); await ctx.close();
    });
  }
}
