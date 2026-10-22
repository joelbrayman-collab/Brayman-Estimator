import assert from "node:assert/strict";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const vite = await createServer({
  appType: "custom",
  configFile: false,
  root,
  resolve: { alias: { "@": root } },
  server: { middlewareMode: true },
});

after(async () => {
  await vite.close();
});

const exampleResult = {
  contract_version: "1",
  result_id: "result-1",
  engine_id: "concrete_slab",
  engine_version: "1.0.0",
  variant: "standard",
  measurement_system: "metric",
  inputs: [
    { code: "length", value: "10", unit_code: "m" },
    { code: "width", value: "8", unit_code: "m" },
    { code: "slab_thickness", value: "100", unit_code: "mm" },
  ],
  assumptions: [{ code: "waste_percent", value: "5", unit_code: "percent" }],
  product_specification: null,
  components: [
    { code: "base_slab_concrete", quantity: "8", unit_code: "m3" },
    { code: "waste", quantity: "0.4", unit_code: "m3" },
  ],
  quantities: [{ code: "total_concrete", quantity: "8.4", unit_code: "m3" }],
};

test("creates the approved two-object handoff without merging consumer metadata", async () => {
  const { createCalculationDownload } = await vite.ssrLoadModule(
    "/lib/calculation-engine/consumer.ts",
  );
  const handoff = createCalculationDownload(exampleResult, "West foundation", "2026-09-26T18:00:00.000Z");

  assert.deepEqual(handoff, {
    calculation_result: exampleResult,
    consumer_metadata: {
      project_reference_name: "West foundation",
      download_title: "Calculation Summary",
      saved_at: "2026-09-26T18:00:00.000Z",
    },
  });
  assert.equal("project_reference_name" in handoff.calculation_result, false);
});

test("renders a complete mobile-ready calculator entry surface", async () => {
  const { default: ConcreteCalculator } = await vite.ssrLoadModule(
    "/components/useful-tools/ConcreteSlabCalculator.tsx",
  );
  const html = renderToStaticMarkup(React.createElement(ConcreteCalculator));

  assert.match(html, /Project \/ Reference Name/);
  assert.match(html, /Standard Slab/);
  assert.match(html, /Thickened Edge/);
  assert.match(html, /Metric/);
  assert.match(html, /Imperial/);
  assert.match(html, /Waste/);
  assert.match(html, /Calculate Concrete/);
  assert.match(html, /Calculation Summary/);
  assert.match(html, /Save on This Device/);
  assert.match(html, /Download Calculation/);
});
