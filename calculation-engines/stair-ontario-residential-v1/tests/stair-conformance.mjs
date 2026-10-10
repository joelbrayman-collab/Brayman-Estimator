import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { evaluateStairProfile, selectRecommendedStair } from "../website-source/lib/useful-tools/stairs.mjs";
import profile from "../website-source/lib/useful-tools/profiles/ontario-residential-v1.json" with { type: "json" };

const stairs = JSON.parse(
  await readFile(
    new URL("../website-source/lib/useful-tools/conformance/stairs.json", import.meta.url),
    "utf8",
  ),
);

const near = (actual, expected, label) =>
  assert.ok(Math.abs(actual - expected) < 1e-10, `${label}: ${actual} !== ${expected}`);

test("recovered stair conformance fixtures match the preserved engine", () => {
  assert.equal(stairs.profileId, profile.id);
  for (const fixture of stairs.cases) {
    const result = fixture.layout
      ? { ...fixture.layout, ...evaluateStairProfile(fixture.layout, profile) }
      : selectRecommendedStair(fixture.input, profile);
    for (const [field, expected] of Object.entries(fixture.expect)) {
      if (field === "checks") {
        for (const [id, checkExpected] of Object.entries(expected)) {
          const check = result.checks.find((candidate) => candidate.id === id);
          assert.ok(check, `${fixture.id}.${id}`);
          for (const [checkField, checkValue] of Object.entries(checkExpected)) {
            assert.equal(check[checkField], checkValue, `${fixture.id}.${id}.${checkField}`);
          }
        }
        continue;
      }
      if (typeof expected === "number") near(result[field], expected, `${fixture.id}.${field}`);
      else assert.equal(result[field], expected, `${fixture.id}.${field}`);
    }
    assert.equal(result.checks.length, profile.limits.length, `${fixture.id} named checks`);
  }
});
