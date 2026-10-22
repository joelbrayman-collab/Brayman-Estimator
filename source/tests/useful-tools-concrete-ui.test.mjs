import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import test from "node:test";

const read = path => readFile(new URL(`../${path}`, import.meta.url), "utf8");

test("dormant broad concrete prototype retains its historical shape controls", async () => {
  const source = await read("components/useful-tools/ConcreteCalculator.tsx");
  for (const shape of ["slab","footing","wall","round-column","post-hole","curb","concrete-stairs"]) assert.match(source, new RegExp(`['\"]${shape}['\"]`));
  for (const label of ["Imperial","Metric","Quantity","Waste allowance","Add section","Remove section"]) assert.match(source, new RegExp(label));
  assert.match(source, /\[wastePercent,setWastePercent\]=useState\(["']10["']\)/);
});

test("dormant broad concrete prototype retains its historical results surface", async () => {
  const source = await read("components/useful-tools/ConcreteCalculator.tsx");
  for (const result of ["Base volume","Waste volume","Adjusted volume","Recommended order","Cubic metres","Cubic yards"]) assert.match(source, new RegExp(result));
  assert.match(source, /aria-live="polite"/);
  assert.match(source, /bagYield/);
  assert.match(source, /truckCapacity/);
});

test("dormant broad concrete prototype retains its historical diagram semantics", async () => {
  const source = await read("components/useful-tools/ConcreteDiagram.tsx");
  assert.match(source, /role="img"/);
  assert.match(source, /aria-label=\{description\}/);
  assert.match(source, /measurement/);
});

test("registers the governed concrete slab calculator route", async () => {
  const source = await read("app/useful-tools/concrete/page.tsx");
  assert.match(source, /ConcreteSlabCalculator/);
});
