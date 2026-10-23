import { calculateConcreteSlab } from "./concrete-slab-1.0.0.js";

// Every volume on this page comes from the preserved concrete_slab 1.0.0 engine.
// To show the other unit, the page runs the engine a second time with the same
// measurements written in the other system (feet to metres and inches to millimetres
// are exact; metres to feet is carried to 12 decimal places). The page itself has no
// volume formula and no unit conversion factor for volumes.

const form = document.querySelector("[data-concrete-calculator]");
const resultNode = document.querySelector("[data-concrete-result]");
const emptyNode = document.querySelector("[data-concrete-empty]");
const errorNode = document.querySelector("[data-concrete-error]");
const edgeFields = document.querySelector("[data-concrete-edge]");

const LABELS = {
  base_slab_concrete: "Base slab concrete",
  thickened_edge_concrete: "Thickened-edge concrete",
  waste: "Waste allowance",
  total_concrete: "Total concrete",
  length: "Length",
  width: "Width",
  slab_thickness: "Slab thickness",
  edge_width: "Edge width",
  edge_depth_below_slab: "Depth below slab",
};
const UNIT_TEXT = { m: "m", mm: "mm", ft: "ft", in: "in", m3: "m³", yd3: "yd³" };

function measurementUnits(system) {
  if (system === "metric") {
    return { plan: "m", thickness: "mm", edgeWidth: "mm", edgeDepth: "mm" };
  }
  return { plan: "ft", thickness: "in", edgeWidth: "ft", edgeDepth: "in" };
}

function chosen(name) {
  const node = form.querySelector(`input[name=${name}]:checked`);
  return node ? node.value : "";
}

function showUnits(system) {
  const units = measurementUnits(system);
  document.querySelectorAll("[data-unit]").forEach((node) => {
    node.textContent = units[node.getAttribute("data-unit")];
  });
}

function fieldValue(name) {
  return document.getElementById(name).value.trim();
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}

// ---- exact decimals (strings in, strings out) ----
function parseDecimal(text) {
  const match = /^(\d*)(?:\.(\d*))?$/.exec(String(text).trim());
  if (!match || (match[1] === "" && (match[2] || "") === "")) return null;
  const fraction = match[2] || "";
  return { n: BigInt((match[1] || "0") + fraction), d: 10n ** BigInt(fraction.length) };
}

function scaled(text, factorN, factorD, places) {
  const value = parseDecimal(text);
  if (!value) return text; // the engine refuses it with its own message
  const unit = 10n ** BigInt(places);
  const n = value.n * factorN * unit;
  const d = value.d * factorD;
  const q = (n * 2n + d) / (2n * d); // round half up
  let digits = q.toString().padStart(places + 1, "0");
  digits = `${digits.slice(0, -places)}.${digits.slice(-places)}`.replace(/\.?0+$/, "");
  return digits === "" ? "0" : digits;
}

const TO_METRIC = { ft: ["m", 3048n, 10000n, 4], in: ["mm", 254n, 10n, 1] };
const TO_IMPERIAL = { m: ["ft", 10000n, 3048n, 12], mm: ["in", 10n, 254n, 12] };

function otherSystemRun(run) {
  const table = run.measurement_system === "metric" ? TO_IMPERIAL : TO_METRIC;
  return {
    ...run,
    measurement_system: run.measurement_system === "metric" ? "imperial" : "metric",
    inputs: run.inputs.map((item) => {
      const [unit, n, d, places] = table[item.unit_code];
      return { ...item, unit_code: unit, value: scaled(item.value, n, d, places) };
    }),
  };
}

function milli(text) {
  const value = parseDecimal(text);
  return (value.n * 1000n) / value.d;
}

function formatMilli(value, trim = false) {
  const text = value.toString().padStart(4, "0");
  let out = `${text.slice(0, -3)}.${text.slice(-3)}`;
  if (trim && out.endsWith("0")) out = out.slice(0, -1); // 11.500 -> 11.50
  return out;
}

function totalOf(result) {
  return result.quantities.find((row) => row.code === "total_concrete").quantity;
}

function buildRun() {
  const system = chosen("measurement_system");
  const variant = chosen("variant");
  const units = measurementUnits(system);
  const inputs = [
    { code: "length", value: fieldValue("length"), unit_code: units.plan },
    { code: "width", value: fieldValue("width"), unit_code: units.plan },
    { code: "slab_thickness", value: fieldValue("slab_thickness"), unit_code: units.thickness },
  ];
  if (variant === "thickened_edge") {
    inputs.push(
      { code: "edge_width", value: fieldValue("edge_width"), unit_code: units.edgeWidth },
      { code: "edge_depth_below_slab", value: fieldValue("edge_depth"), unit_code: units.edgeDepth },
    );
  }
  return {
    variant,
    measurement_system: system,
    inputs,
    assumptions: [{ code: "waste_percent", value: fieldValue("waste_percent"), unit_code: "percent" }],
  };
}

function orderFigures(run, result) {
  const other = calculateConcreteSlab(otherSystemRun(run));
  const metric = run.measurement_system === "metric" ? result : other;
  const imperial = run.measurement_system === "metric" ? other : result;
  const m3 = milli(totalOf(metric));
  const yd3 = milli(totalOf(imperial));
  const unit = chosen("order_unit");
  const exact = unit === "m3" ? m3 : yd3;
  const stepText = fieldValue("order_increment");
  let order = exact;
  let stepMilli = 0n;
  if (stepText !== "") {
    const step = parseDecimal(stepText);
    if (!step || step.n <= 0n) throw new Error("Round the order up to a number above zero, or leave it blank.");
    if ((step.n * 1000n) % step.d !== 0n) throw new Error("Round the order up to a step of 0.001 or more.");
    stepMilli = (step.n * 1000n) / step.d;
    order = ((exact + stepMilli - 1n) / stepMilli) * stepMilli;
  }
  return { unit, m3, yd3, exact, order, stepMilli, stepText };
}

function render(run, result, figures) {
  const unit = UNIT_TEXT[figures.unit];
  const other = figures.unit === "m3" ? `${formatMilli(figures.yd3)} yd³` : `${formatMilli(figures.m3)} m³`;
  const rounding = figures.stepMilli > 0n ? `rounded up to the next ${escapeHtml(figures.stepText)} ${unit}` : "not rounded";
  const lines = (rows) =>
    rows
      .map((row) => `<div class="cc-line"><span>${LABELS[row.code] || row.code}</span><strong>${row.quantity} ${UNIT_TEXT[row.unit_code]}</strong></div>`)
      .join("");
  const inputs = result.inputs
    .map((row) => `<div class="cc-line"><span>${LABELS[row.code] || row.code}</span><strong>${row.value} ${UNIT_TEXT[row.unit_code]}</strong></div>`)
    .join("");
  const total = result.quantities[0];
  resultNode.innerHTML = `
    <div class="cc-order" data-concrete-order>
      <span>Order</span>
      <strong data-order-amount>${formatMilli(figures.order, figures.stepMilli > 0n)} ${unit}</strong>
      <p>Total with waste <b data-order-exact>${formatMilli(figures.exact)} ${unit}</b> (${other}), ${rounding}.</p>
    </div>
    <dl class="cc-meta">
      <div><dt>Slab type</dt><dd>${result.variant === "standard" ? "Standard slab" : "Thickened edge"}</dd></div>
      <div><dt>Measured in</dt><dd data-measured>${result.measurement_system === "metric" ? "Metric" : "Feet and inches"}</dd></div>
    </dl>
    <div class="cc-block"><h3>Quantity breakdown</h3>${lines(result.components)}
      <div class="cc-line cc-total"><span>Total concrete</span><strong data-total>${total.quantity} ${UNIT_TEXT[total.unit_code]}</strong></div></div>
    <div class="cc-block"><h3>Measurements</h3>${inputs}
      <div class="cc-line"><span>Waste allowance</span><strong>${result.assumptions[0].value}%</strong></div></div>
    <p class="cc-note">A quantity only, not an engineering design. Confirm the order with the supplier. This result is not on an estimate.</p>
  `;
  resultNode.dataset.linkSummary = `Order ${formatMilli(figures.order, figures.stepMilli > 0n)} ${unit} · total ${formatMilli(figures.exact)} ${unit} (${other}) · ${result.variant === "standard" ? "standard slab" : "thickened edge"}, measured in ${result.measurement_system === "metric" ? "metric" : "feet and inches"}`;
  // The engine's own Contract V1 result, for "Add to Existing Project" / "Create New Project" (the estimate review).
  resultNode.dataset.contract = JSON.stringify(result);
  resultNode.hidden = false;
  emptyNode.hidden = true;
  resultNode.dispatchEvent(new CustomEvent("calculator:result", { bubbles: true }));
}

function clearResult() {
  resultNode.hidden = true;
  emptyNode.hidden = false;
  delete resultNode.dataset.linkSummary;
  delete resultNode.dataset.contract;
  resultNode.dispatchEvent(new CustomEvent("calculator:cleared", { bubbles: true }));
}

function calculate() {
  errorNode.hidden = true;
  try {
    const run = buildRun();
    const result = calculateConcreteSlab(run);
    render(run, result, orderFigures(run, result));
  } catch (error) {
    clearResult();
    errorNode.textContent = error && error.message ? error.message : "The calculation was refused.";
    errorNode.hidden = false;
  }
}

form.addEventListener("change", (event) => {
  const name = event.target.name;
  if (name === "variant") edgeFields.hidden = chosen("variant") !== "thickened_edge";
  if (name === "measurement_system") showUnits(chosen("measurement_system"));
  if (name === "order_unit") {
    document.querySelector("[data-order-unit]").textContent = UNIT_TEXT[chosen("order_unit")];
    if (!resultNode.hidden) calculate();
  }
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  calculate();
});

showUnits(chosen("measurement_system"));
edgeFields.hidden = chosen("variant") !== "thickened_edge";
