import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const read = (path) => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("the public Concrete route has one governed calculation authority", async () => {
  const route = await read("app/useful-tools/concrete/page.tsx");
  const consumer = await read("components/useful-tools/ConcreteSlabCalculator.tsx");

  assert.match(route, /ConcreteSlabCalculator/);
  assert.doesNotMatch(route, /ConcreteCalculator/);
  assert.match(consumer, /@\/lib\/calculation-engine\/concrete-slab/);
  assert.doesNotMatch(consumer, /lib\/useful-tools\/concrete/);
});

test("the Useful Tools directory advertises only live governed Concrete modes", async () => {
  const directory = await read("app/useful-tools/page.tsx");

  assert.match(directory, /standard slabs and slabs with thickened perimeter edges/i);
  assert.doesNotMatch(directory, /footings|walls|columns|post holes|curbs|concrete stairs/i);
});

test("the broad Concrete implementation is explicitly retained as dormant compatibility code", async () => {
  const component = await read("components/useful-tools/ConcreteCalculator.tsx");
  const engine = await read("lib/useful-tools/concrete.mjs");
  const authority = await read("docs/calculation-engine/concrete-authority.md");

  assert.match(component, /DORMANT BROAD CONCRETE PROTOTYPE/);
  assert.match(engine, /DORMANT BROAD CONCRETE PROTOTYPE/);
  assert.match(authority, /GOVERNED LIVE AUTHORITY/);
  assert.match(authority, /DORMANT SUPERSEDED PROTOTYPE/);
  assert.match(authority, /must not be advertised as current public capability/i);
});

test("legacy compatibility checks cannot masquerade as live governed conformance", async () => {
  const verifier = await read("scripts/verify-useful-tools-conformance.mjs");
  const legacyTests = await read("tests/useful-tools-concrete.test.mjs");
  const legacyUiTests = await read("tests/useful-tools-concrete-ui.test.mjs");

  assert.match(verifier, /dormant broad concrete prototype/i);
  assert.match(legacyTests, /dormant broad concrete prototype/i);
  assert.match(legacyUiTests, /dormant broad concrete prototype/i);
});
