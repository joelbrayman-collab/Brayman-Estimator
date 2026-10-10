import { calculateConcreteSlab } from "./concrete-slab-1.0.0.js";

const form = document.querySelector("[data-concrete-calculator]");
const resultNode = document.querySelector("[data-concrete-result]");
const errorNode = document.querySelector("[data-concrete-error]");
const edgeFields = document.querySelector("[data-concrete-edge]");

const QUANTITY_LABELS = {
  base_slab_concrete: "Base slab concrete",
  thickened_edge_concrete: "Additional thickened-edge concrete",
  waste: "Waste allowance",
  total_concrete: "Total concrete",
};

function measurementUnits(system) {
  if (system === "metric") {
    return {
      plan: "m",
      thickness: "mm",
      edgeWidth: "mm",
      edgeDepth: "mm",
    };
  }
  return {
    plan: "ft",
    thickness: "in",
    edgeWidth: "ft",
    edgeDepth: "in",
  };
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

function buildRun() {
  const system = form.elements.measurement_system.value;
  const variant = form.elements.variant.value;
  const units = measurementUnits(system);
  const inputs = [
    { code: "length", value: fieldValue("length"), unit_code: units.plan },
    { code: "width", value: fieldValue("width"), unit_code: units.plan },
    {
      code: "slab_thickness",
      value: fieldValue("slab_thickness"),
      unit_code: units.thickness,
    },
  ];
  if (variant === "thickened_edge") {
    inputs.push(
      { code: "edge_width", value: fieldValue("edge_width"), unit_code: units.edgeWidth },
      {
        code: "edge_depth_below_slab",
        value: fieldValue("edge_depth"),
        unit_code: units.edgeDepth,
      },
    );
  }
  return {
    variant,
    measurement_system: system,
    inputs,
    assumptions: [
      { code: "waste_percent", value: fieldValue("waste_percent"), unit_code: "percent" },
    ],
  };
}

function renderResult(result) {
  const rows = [...(result.components || []), ...(result.quantities || [])];
  const body = rows
    .map((row) => {
      const label = QUANTITY_LABELS[row.code] || row.code;
      return `<tr><td>${label}</td><td>${row.quantity}</td><td>${row.unit_code}</td></tr>`;
    })
    .join("");
  resultNode.innerHTML = `
    <h2>Result</h2>
    <p>concrete_slab ${result.engine_version}. ${result.variant}. ${result.measurement_system}.</p>
    <p>This result is not on an estimate.</p>
    <table>
      <thead><tr><th>Quantity</th><th>Amount</th><th>Unit</th></tr></thead>
      <tbody>${body}</tbody>
    </table>
  `;
  resultNode.hidden = false;
}

form.elements.variant.addEventListener("change", () => {
  edgeFields.hidden = form.elements.variant.value !== "thickened_edge";
});
form.elements.measurement_system.addEventListener("change", () => {
  showUnits(form.elements.measurement_system.value);
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  errorNode.hidden = true;
  resultNode.hidden = true;
  try {
    renderResult(calculateConcreteSlab(buildRun()));
  } catch (error) {
    errorNode.textContent = error && error.message ? error.message : "The calculation was refused.";
    errorNode.hidden = false;
  }
});

showUnits(form.elements.measurement_system.value);
edgeFields.hidden = form.elements.variant.value !== "thickened_edge";
