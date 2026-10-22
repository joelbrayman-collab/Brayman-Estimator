import assert from "node:assert/strict";
import test from "node:test";

import {toMetres} from "../lib/useful-tools/units.mjs";
import {
  UsefulToolsValidationError,
  calculateConcretePour,
  calculateConcreteSection,
} from "../lib/useful-tools/concrete.mjs";

const m = (value, unit = "m") => ({value, unit});
const close = (actual, expected, tolerance = 1e-9) =>
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);

test("dormant broad concrete prototype normalizes supported length units to metres", () => {
  for (const measurement of [m(12, "in"), m(1, "ft"), m(0.3048), m(304.8, "mm")]) {
    close(toMetres(measurement.value, measurement.unit), 0.3048);
  }
});

test("dormant broad concrete prototype calculates equivalent imperial and metric slabs", () => {
  const imperial = calculateConcreteSection({
    type: "slab", length: m(20, "ft"), width: m(24, "ft"), thickness: m(4, "in"), quantity: 1,
  });
  const metric = calculateConcreteSection({
    type: "slab", length: m(6.096), width: m(7.3152), thickness: m(0.1016), quantity: 1,
  });
  close(imperial.baseM3, metric.baseM3);
});

test("dormant broad concrete prototype calculates every rectangular and cylindrical field shape", () => {
  close(calculateConcreteSection({type:"footing",length:m(4),width:m(.5),thickness:m(.25),quantity:1}).baseM3, .5);
  close(calculateConcreteSection({type:"wall",length:m(8),height:m(2.4),thickness:m(.2),quantity:1}).baseM3, 3.84);
  close(calculateConcreteSection({type:"round-column",diameter:m(.5),height:m(3),quantity:1}).baseM3, Math.PI*.25*.25*3);
  close(calculateConcreteSection({type:"post-hole",diameter:m(.3),height:m(1.2),quantity:1}).baseM3, Math.PI*.15*.15*1.2);
  close(calculateConcreteSection({type:"curb",length:m(10),width:m(.2),height:m(.3),quantity:1}).baseM3, .6);
});

test("dormant broad concrete prototype calculates solid stepped concrete stairs", () => {
  const result = calculateConcreteSection({
    type:"concrete-stairs", width:m(1.2), treadRun:m(.28), riserHeight:m(.18), riserCount:5, quantity:1,
  });
  close(result.baseM3, 1.2*.28*.18*(5*6/2));
});

test("dormant broad concrete prototype applies quantity before waste and rounds orders upward", () => {
  const result = calculateConcretePour({
    sections:[{type:"slab",length:m(2),width:m(2),thickness:m(.1),quantity:2}],
    wastePercent:10,
    orderIncrementM3:.25,
  });
  close(result.baseM3, .8);
  close(result.wasteM3, .08);
  close(result.adjustedM3, .88);
  assert.equal(result.recommendedOrderM3, 1);
  assert.ok(result.recommendedOrderM3 >= result.adjustedM3);
});

test("dormant broad concrete prototype uses supplied bag yields and truck capacities", () => {
  const result = calculateConcretePour({
    sections:[{type:"slab",length:m(2),width:m(2),thickness:m(.1),quantity:1}],
    wastePercent:0,
    orderIncrementM3:.1,
    bagYieldM3:.02,
    truckCapacityM3:.3,
  });
  assert.equal(result.bagCount, 20);
  assert.equal(result.truckCount, 2);
});

test("dormant broad concrete prototype rejects invalid dimensions", () => {
  const invalid = [undefined, 0, -1, Number.NaN, Number.POSITIVE_INFINITY];
  for (const value of invalid) {
    assert.throws(
      () => calculateConcreteSection({type:"slab",length:m(value),width:m(2),thickness:m(.1),quantity:1}),
      error => error instanceof UsefulToolsValidationError && error.issues[0].field === "length",
    );
  }
});

test("dormant broad concrete prototype keeps valid volumes finite", () => {
  for (const value of [1e-6, 1e6]) {
    const result = calculateConcreteSection({type:"slab",length:m(value),width:m(value),thickness:m(value),quantity:1});
    assert.ok(Number.isFinite(result.baseM3));
    assert.ok(result.baseM3 > 0);
  }
});
