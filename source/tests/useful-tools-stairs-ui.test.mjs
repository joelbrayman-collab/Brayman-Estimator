import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const read=path=>readFile(new URL(`../${path}`,import.meta.url),"utf8");

test("stair calculator exposes required inputs and named profile",async()=>{
  const source=await read("components/useful-tools/StairCalculator.tsx");
  for(const text of ["Total rise","Available run","Stair width","Tread thickness","Imperial","Metric","Ontario Residential — V1"])
    assert.ok(source.includes(text),text);
});

test("measurement-system buttons convert inputs instead of reinterpreting their numbers",async()=>{
  const source=await read("components/useful-tools/StairCalculator.tsx");
  assert.ok(source.includes("convertStairMeasurements"));
  assert.ok(source.includes('onClick={()=>switchUnits("imperial")}'));
  assert.ok(source.includes('onClick={()=>switchUnits("metric")}'));
});

test("stair calculator exposes geometry, checks, disclaimer and live results",async()=>{
  const source=await read("components/useful-tools/StairCalculator.tsx");
  for(const text of ["Risers","Treads","Exact rise","Exact run","Stair angle","Stringer length","Profile checks","authority having jurisdiction","aria-live=\"polite\""])
    assert.ok(source.includes(text),text);
});

test("dynamic diagram labels every required measurement",async()=>{
  const source=await read("components/useful-tools/StairDiagram.tsx");
  for(const text of ["Total rise","Available run","Riser height","Tread run","Stringer","Angle"])
    assert.ok(source.includes(text),text);
  assert.ok(source.includes("aria-label"));
});

test("stair diagram dimensions a typical riser and tread on the stair profile",async()=>{
  const source=await read("components/useful-tools/StairDiagram.tsx");
  assert.ok(source.includes('className="stair-dimension typical-riser"'));
  assert.ok(source.includes('className="stair-dimension typical-tread"'));
  assert.ok(source.includes("Typical riser"));
  assert.ok(source.includes("Typical tread"));
  assert.ok(source.includes('className="stair-extension"'));
  assert.ok(source.includes('viewBox="0 0 760 480"'));
});

test("stair diagram renders construction anatomy rather than a simple stair silhouette",async()=>{
  const source=await read("components/useful-tools/StairDiagram.tsx");
  for(const text of ["Finished floor","Tread thickness","stair-tread-board","stair-riser-face","stair-stringer-body","Upper landing"])
    assert.ok(source.includes(text),text);
  const calculator=await read("components/useful-tools/StairCalculator.tsx");
  assert.ok(calculator.includes("treadThicknessLabel={displayInput(treadThickness)}"));
});

test("stair diagram uses the active calculator units for every measurement",async()=>{
  const diagram=await read("components/useful-tools/StairDiagram.tsx");
  assert.ok(diagram.includes("formatLength"));
  assert.ok(!diagram.includes("const mm="));
  const calculator=await read("components/useful-tools/StairCalculator.tsx");
  assert.ok(calculator.includes("formatLength={display}"));
});

test("rendered stair geometry is supplied by the governed diagram geometry",async()=>{
  const source=await read("components/useful-tools/StairDiagram.tsx");
  assert.ok(source.includes("createStairDiagramGeometry(result)"));
  assert.ok(source.includes("d={geometry.stairPath}"));
  assert.ok(source.includes("points={stringerPoints}"));
  assert.ok(source.includes("geometry.stringer.angleDegrees"));
  assert.ok(!source.includes("rotate(28"));
});

test("stairs route renders the calculator",async()=>{
  const source=await read("app/useful-tools/stairs/page.tsx");
  assert.ok(source.includes("StairCalculator"));
  assert.ok(source.includes("Stair Calculator"));
});
