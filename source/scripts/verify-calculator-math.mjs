import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const html = await readFile(
  new URL("../public/employment-vs-entrepreneurship/index.html", import.meta.url),
  "utf8",
);
const script = html.match(/<script>([\s\S]*)<\/script>/)?.[1];
assert.ok(script, "calculator script is missing");

const values = {
  wage: 45, eh: 40, ew: 50, tb: 12000, fb: 8000, ob: 6500,
  weeks: 40, site: 40, admin: 10, sales: 3, util: 85, rate: 90,
  helper: "no", gain: 25, hw: 25, hh: 35, burden: 18,
};
const outputIds = [
  "lBill", "lAnnual", "lRev", "lOwner", "lCost", "lPayroll",
  "lTotalCost", "lCostRev", "cur", "biz", "delta", "curHr", "bizHr",
  "hourDelta", "cash", "benefits", "curHours", "revenue", "allCosts",
  "bizHours", "beRate", "tBill", "tWeeks", "tUtil", "rateMsg", "sum1", "sum2",
];
const elements = Object.fromEntries(
  [...Object.entries(values).map(([id, value]) => [id, { value: String(value), textContent: "" }]),
   ...outputIds.map((id) => [id, { value: "", textContent: "" }])],
);
const annualCosts = [12000, 8000, 3000, 3000, 6000, 5500, 3000, 2500, 2000, 3000, 0]
  .map((value) => ({ value: String(value) }));
const document = {
  getElementById(id) {
    return elements[id] ?? (elements[id] = { value: "", textContent: "" });
  },
  querySelectorAll(selector) {
    assert.equal(selector, "[data-cost]");
    return annualCosts;
  },
};
const context = vm.createContext({ document, Intl, console });
const calculationSource = `${script.split("function go")[0]}\nglobalThis.runCalc = calc;`;
vm.runInContext(calculationSource, context);

context.runCalc();
assert.equal(elements.cur.textContent, "$116,500");
assert.equal(elements.revenue.textContent, "$122,400");
assert.equal(elements.allCosts.textContent, "$48,000");
assert.equal(elements.biz.textContent, "$74,400");
assert.equal(elements.delta.textContent, "−$42,100");
assert.equal(elements.beRate.textContent, "$121/hr");

for (const element of [...Object.values(elements), ...annualCosts]) element.value = "0";
context.runCalc();
for (const id of outputIds) {
  assert.doesNotMatch(elements[id].textContent, /NaN|Infinity/, `${id} has unstable zero output`);
}

Object.assign(elements.wage, { value: "45.75" });
Object.assign(elements.eh, { value: "37.5" });
Object.assign(elements.ew, { value: "52" });
Object.assign(elements.weeks, { value: "52" });
Object.assign(elements.site, { value: "80" });
Object.assign(elements.util, { value: "1000" });
Object.assign(elements.rate, { value: "1000" });
context.runCalc();
assert.equal(elements.tUtil.textContent, "100%", "utilization must cap at 100%");
assert.equal(elements.tWeeks.textContent, "52 weeks", "working weeks must cap at 52");
for (const id of outputIds) {
  assert.doesNotMatch(elements[id].textContent, /NaN|Infinity/, `${id} has unstable boundary output`);
}

console.log("calculator math verification passed");
