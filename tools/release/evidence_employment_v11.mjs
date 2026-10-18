// Release evidence, same assertions as tests/test_employment_calculator_v11.py (decision 5).
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import test, { after, before } from "node:test";
import { pathToFileURL } from "node:url";
import { REPO, launch } from "./evidence_common.mjs";

const ROOT = path.join(REPO, "calculation-engines/employment-vs-entrepreneurship");
const ORIGINAL = path.join(ROOT, "website-source/public/employment-vs-entrepreneurship/index.html");
const V11 = path.join(ROOT, "v1.1/index.html");
const OUTPUTS = ["lBill","lAnnual","lRev","lOwner","lCost","lPayroll","lTotalCost","lCostRev","cur","biz","delta",
  "curHr","bizHr","hourDelta","cash","benefits","curHours","revenue","allCosts","bizHours","beRate",
  "tBill","tWeeks","tUtil","rateMsg","sum1","sum2"];
let browser;
before(async () => { browser = await launch(); });
after(async () => { await browser?.close(); });

async function open(file) { const p = await browser.newPage(); await p.goto(pathToFileURL(file).href); return p; }
function results(page, entries, costs = null) {
  return page.evaluate(([entries, costs, outputs]) => {
    for (const [id, v] of Object.entries(entries)) document.getElementById(id).value = v;
    if (costs) document.querySelectorAll("[data-cost]").forEach((el, i) => { if (costs[i] !== undefined) el.value = costs[i]; });
    calc();
    return Object.fromEntries(outputs.map((id) => [id, (document.getElementById(id) || {}).textContent || ""]));
  }, [entries, costs, OUTPUTS]);
}

const VALID_SETS = [
  [{}, null],
  [{ wage: "60", site: "35", util: "70", rate: "120", weeks: "44" }, null],
  [{ helper: "yes", hw: "28", hh: "30", burden: "20" }, null],
  [{ wage: "0", tb: "0", fb: "0", ob: "0" }, null],
  [{ weeks: "60", util: "130" }, ["15000", "9000", "1000"]],
];
VALID_SETS.forEach(([entries, costs], i) => {
  test(`valid set ${i}: version 1.1 gives exactly the original results`, async () => {
    const o = await open(ORIGINAL), c = await open(V11);
    assert.deepEqual(await results(c, entries, costs), await results(o, entries, costs));
    assert.ok(await c.locator("#inputError").isHidden());
    await o.close(); await c.close();
  });
});
for (const [field, value] of [["wage", ""], ["site", "-5"], ["rate", ""], ["weeks", "-1"]]) {
  test(`${field}=${JSON.stringify(value)} is refused with a message`, async () => {
    const p = await open(V11);
    const before = await results(p, {});
    assert.deepEqual(await results(p, { [field]: value }), before);
    const msg = p.locator("#inputError");
    assert.ok(await msg.isVisible()); assert.match(await msg.textContent(), /number of 0 or more/);
    assert.equal(await p.locator(`#${field}`).getAttribute("aria-invalid"), "true");
    const fixed = await results(p, { [field]: "41" });
    assert.ok(await msg.isHidden()); assert.equal(await p.locator(`#${field}`).getAttribute("aria-invalid"), null);
    const o = await open(ORIGINAL);
    assert.deepEqual(fixed, await results(o, { [field]: "41" }));
    await o.close(); await p.close();
  });
}
test("a text annual cost is refused", async () => {
  const p = await open(V11);
  const before = await results(p, {});
  assert.deepEqual(await results(p, {}, ["abc"]), before);
  assert.ok(await p.locator("#inputError").isVisible());
  await p.close();
});
test("a typed letter in a number box is refused", async () => {
  const p = await open(V11);
  await p.locator("#wage").fill("");
  await p.locator("#wage").pressSequentially("abc");
  await p.evaluate("calc()");
  assert.ok(await p.locator("#inputError").isVisible());
  await p.close();
});
test("the original file is unchanged and still reads bad entries as zero", async () => {
  assert.equal(crypto.createHash("sha256").update(fs.readFileSync(ORIGINAL)).digest("hex"),
    "41f449de2a148a4f26b89cf52d6e878052a97d61e341f8a3fac8b5586e5fa295");
  const p = await open(ORIGINAL);
  assert.notEqual((await results(p, { wage: "" })).cash, (await results(p, { wage: "45" })).cash);
  await p.close();
});
