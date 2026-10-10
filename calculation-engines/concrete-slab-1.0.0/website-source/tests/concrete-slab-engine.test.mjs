import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const fixtureDirectory = path.join(
  root,
  "docs/calculation-engine/fixtures/concrete-slab-1.0.0",
);
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

async function readJson(file) {
  return JSON.parse(await readFile(path.join(fixtureDirectory, file), "utf8"));
}

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(",")}]`;
  if (value !== null && typeof value === "object") {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

test("reproduces every approved concrete_slab 1.0.0 fixture and fingerprint", async () => {
  const { calculateConcreteSlab } = await vite.ssrLoadModule(
    "/lib/calculation-engine/concrete-slab.ts",
  );
  const manifest = await readJson("manifest.json");

  for (const fixtureCase of manifest.cases) {
    const expected = await readJson(fixtureCase.file);
    const actual = calculateConcreteSlab(
      {
        variant: expected.variant,
        measurement_system: expected.measurement_system,
        inputs: expected.inputs,
        assumptions: expected.assumptions,
      },
      { result_id: expected.result_id },
    );

    assert.deepEqual(actual, expected, fixtureCase.file);
    const fingerprintPayload = structuredClone(actual);
    delete fingerprintPayload.result_id;
    delete fingerprintPayload.produced_at;
    const fingerprint = createHash("sha256")
      .update(canonicalize(fingerprintPayload))
      .digest("hex");
    assert.equal(fingerprint, fixtureCase.fingerprint_sha256, fixtureCase.file);
  }
});

test("rejects invalid geometry without producing a Contract V1 result", async () => {
  const { calculateConcreteSlab, ConcreteSlabValidationError } =
    await vite.ssrLoadModule("/lib/calculation-engine/concrete-slab.ts");

  const invalidCases = [
    {
      name: "zero length",
      run: {
        variant: "standard",
        measurement_system: "metric",
        inputs: [
          { code: "length", value: "0", unit_code: "m" },
          { code: "width", value: "8", unit_code: "m" },
          { code: "slab_thickness", value: "100", unit_code: "mm" },
        ],
        assumptions: [{ code: "waste_percent", value: "0", unit_code: "percent" }],
      },
    },
    {
      name: "mixed measurement systems",
      run: {
        variant: "standard",
        measurement_system: "metric",
        inputs: [
          { code: "length", value: "10", unit_code: "m" },
          { code: "width", value: "8", unit_code: "ft" },
          { code: "slab_thickness", value: "100", unit_code: "mm" },
        ],
        assumptions: [{ code: "waste_percent", value: "0", unit_code: "percent" }],
      },
    },
    {
      name: "overlapping edge bands",
      run: {
        variant: "thickened_edge",
        measurement_system: "metric",
        inputs: [
          { code: "length", value: "10", unit_code: "m" },
          { code: "width", value: "8", unit_code: "m" },
          { code: "slab_thickness", value: "100", unit_code: "mm" },
          { code: "edge_width", value: "4", unit_code: "m" },
          { code: "edge_depth_below_slab", value: "300", unit_code: "mm" },
        ],
        assumptions: [{ code: "waste_percent", value: "5", unit_code: "percent" }],
      },
    },
  ];

  for (const invalidCase of invalidCases) {
    assert.throws(
      () => calculateConcreteSlab(invalidCase.run),
      ConcreteSlabValidationError,
      invalidCase.name,
    );
  }
});

test("rejects edge inputs on a standard slab and missing edge inputs on a thickened slab", async () => {
  const { calculateConcreteSlab, ConcreteSlabValidationError } =
    await vite.ssrLoadModule("/lib/calculation-engine/concrete-slab.ts");
  const baseInputs = [
    { code: "length", value: "10", unit_code: "m" },
    { code: "width", value: "8", unit_code: "m" },
    { code: "slab_thickness", value: "100", unit_code: "mm" },
  ];
  const assumptions = [{ code: "waste_percent", value: "0", unit_code: "percent" }];

  assert.throws(
    () =>
      calculateConcreteSlab({
        variant: "standard",
        measurement_system: "metric",
        inputs: [...baseInputs, { code: "edge_width", value: "0.5", unit_code: "m" }],
        assumptions,
      }),
    ConcreteSlabValidationError,
  );
  assert.throws(
    () =>
      calculateConcreteSlab({
        variant: "thickened_edge",
        measurement_system: "metric",
        inputs: baseInputs,
        assumptions,
      }),
    ConcreteSlabValidationError,
  );
});
