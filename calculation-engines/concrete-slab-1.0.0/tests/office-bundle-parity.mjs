import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { createServer } from "vite";

const packageRoot = fileURLToPath(new URL("..", import.meta.url));
const websiteRoot = path.join(packageRoot, "website-source");
const fixtureDirectory = path.join(
  websiteRoot,
  "docs/calculation-engine/fixtures/concrete-slab-1.0.0",
);
const officeBundle = path.resolve(
  packageRoot,
  "../../app/static/js/concrete-slab-1.0.0.js",
);

const vite = await createServer({
  appType: "custom",
  configFile: false,
  root: websiteRoot,
  resolve: { alias: { "@": websiteRoot } },
  server: { middlewareMode: true },
});

after(async () => {
  await vite.close();
});

async function readJson(name) {
  return JSON.parse(await readFile(path.join(fixtureDirectory, name), "utf8"));
}

test("the office bundle matches the preserved concrete_slab 1.0.0 engine", async () => {
  const { calculateConcreteSlab } = await vite.ssrLoadModule(
    "/lib/calculation-engine/concrete-slab.ts",
  );
  const office = await import(pathToFileURL(officeBundle).href);
  const manifest = await readJson("manifest.json");

  for (const fixtureCase of manifest.cases) {
    const expected = await readJson(fixtureCase.file);
    const run = {
      variant: expected.variant,
      measurement_system: expected.measurement_system,
      inputs: expected.inputs,
      assumptions: expected.assumptions,
    };
    const options = { result_id: expected.result_id };
    assert.deepEqual(
      office.calculateConcreteSlab(run, options),
      calculateConcreteSlab(run, options),
      fixtureCase.file,
    );
  }
});
