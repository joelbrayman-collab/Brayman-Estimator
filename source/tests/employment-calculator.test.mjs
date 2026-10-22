import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const html = await readFile(
  new URL("../public/employment-vs-entrepreneurship/index.html", import.meta.url),
  "utf8",
);
const script = html.match(/<script>([\s\S]*)<\/script>/)?.[1];
assert.ok(script, "calculator script is missing");

const outputIds = [
  "lBill", "lAnnual", "lRev", "lOwner", "lCost", "lPayroll",
  "lTotalCost", "lCostRev", "cur", "biz", "delta", "curHr", "bizHr",
  "hourDelta", "cash", "benefits", "curHours", "revenue", "allCosts",
  "bizHours", "beRate", "tBill", "tWeeks", "tUtil", "rateMsg", "sum1", "sum2",
];

function harness(overrides = {}) {
  const values = {
    wage: 45, eh: 40, ew: 50, tb: 12000, fb: 8000, ob: 6500,
    weeks: 40, site: 40, admin: 10, sales: 3, util: 85, rate: 90,
    helper: "no", gain: 25, hw: 25, hh: 35, burden: 18,
    ...overrides,
  };
  const elements = Object.fromEntries([
    ...Object.entries(values).map(([id, value]) => [id, { value: String(value), textContent: "" }]),
    ...outputIds.map((id) => [id, { value: "", textContent: "" }]),
  ]);
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
  vm.runInContext(
    `${script.split("function go")[0]}\nglobalThis.runCalc = calc;`,
    context,
  );
  const run = () => {
    context.runCalc();
    return Object.fromEntries(outputIds.map((id) => [id, elements[id].textContent]));
  };
  return { annualCosts, elements, run };
}

const dollars = (value) => Number(value.replace(/[^0-9.-]/g, ""));

test("shows only controls backed by the governed comparison model", () => {
  assert.doesNotMatch(html, /id=['"]win['"]/, "quote win rate must not masquerade as active");
  assert.doesNotMatch(html, /id=['"]season['"]/, "seasonality must be represented by working weeks");
  assert.doesNotMatch(html, /id=['"]winter['"]/, "slower-season approach must not masquerade as active");
  assert.doesNotMatch(html, /data-m=['"]Crew['"]/, "unsupported crew economics must not be offered");
  assert.match(
    html,
    /Enter the actual working weeks[^<]*Winter Protection \/ Heat/i,
    "season guidance must point to the two active assumptions",
  );
  assert.match(
    html,
    /Helper wage \/ hour\s*<span class=['"]tag est['"]>OWNER ESTIMATE<\/span>/,
    "helper wage must be presented as an active owner estimate",
  );
});

test("every employment input changes its intended result", () => {
  const cases = [
    ["wage", "cur", 55],
    ["eh", "cur", 45],
    ["ew", "cur", 52],
    ["tb", "benefits", 15000],
    ["fb", "benefits", 10000],
    ["ob", "benefits", 8000],
  ];
  for (const [id, output, value] of cases) {
    const { elements, run } = harness();
    const before = dollars(run()[output]);
    elements[id].value = String(value);
    const after = dollars(run()[output]);
    assert.ok(after > before, `${id} must increase ${output}`);
  }
});

test("every owner-capacity input changes the intended result", () => {
  for (const [id, value] of [["weeks", 45], ["site", 45], ["rate", 100], ["util", 90]]) {
    const { elements, run } = harness();
    const before = dollars(run().biz);
    elements[id].value = String(value);
    const after = dollars(run().biz);
    assert.ok(after > before, `${id} must increase entrepreneurship income`);
  }
  for (const [id, value] of [["admin", 15], ["sales", 8]]) {
    const { elements, run } = harness();
    const before = dollars(run().bizHr);
    elements[id].value = String(value);
    const after = dollars(run().bizHr);
    assert.ok(after < before, `${id} must reduce effective owner income per hour`);
  }
});

test("every helper input participates only when helper economics are enabled", () => {
  for (const [id, value, direction] of [
    ["hw", 30, "down"],
    ["hh", 40, "down"],
    ["burden", 25, "down"],
    ["gain", 35, "up"],
  ]) {
    const active = harness({ helper: "yes" });
    const before = dollars(active.run().biz);
    active.elements[id].value = String(value);
    const after = dollars(active.run().biz);
    assert.ok(direction === "up" ? after > before : after < before, `${id} active relationship`);

    const solo = harness({ helper: "no" });
    const soloBefore = solo.run().biz;
    solo.elements[id].value = String(value);
    assert.equal(solo.run().biz, soloBefore, `${id} must not affect a solo model`);
  }
});

test("every annual operating-cost input reduces entrepreneurship income dollar for dollar", () => {
  const { annualCosts, run } = harness();
  for (let index = 0; index < annualCosts.length; index += 1) {
    const before = dollars(run().biz);
    annualCosts[index].value = String(Number(annualCosts[index].value) + 100);
    const after = dollars(run().biz);
    assert.equal(after, before - 100, `operating cost ${index + 1} must reduce income`);
    annualCosts[index].value = String(Number(annualCosts[index].value) - 100);
  }
});
