import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {calculateConcretePour,calculateConcreteSection} from "../lib/useful-tools/concrete.mjs";
import {evaluateStairProfile,selectRecommendedStair} from "../lib/useful-tools/stairs.mjs";
import profile from "../lib/useful-tools/profiles/ontario-residential-v1.json" with {type:"json"};

const root=new URL("../lib/useful-tools/conformance/",import.meta.url);
const concrete=JSON.parse(await readFile(new URL("concrete.json",root),"utf8"));
const stairs=JSON.parse(await readFile(new URL("stairs.json",root),"utf8"));
const near=(actual,expected,label)=>assert.ok(Math.abs(actual-expected)<1e-10,`${label}: ${actual} !== ${expected}`);

for(const fixture of concrete.cases){
  const result=calculateConcreteSection(fixture.section);
  assert.ok(Number.isFinite(result.baseM3),`${fixture.id} finite`);
  near(result.baseM3,fixture.expectedBaseM3,fixture.id);
}
const pour=calculateConcretePour(concrete.pourCase);
for(const [field,expected] of Object.entries(concrete.pourCase.expected)) near(pour[field],expected,`pour.${field}`);

assert.equal(stairs.profileId,profile.id,"stair fixture profile id");
for(const fixture of stairs.cases){
  const result=fixture.layout?{...fixture.layout,...evaluateStairProfile(fixture.layout,profile)}:selectRecommendedStair(fixture.input,profile);
  for(const [field,expected] of Object.entries(fixture.expect)){
    if(field==="checks"){
      for(const [id,checkExpected] of Object.entries(expected)){
        const check=result.checks.find(candidate=>candidate.id===id);
        assert.ok(check,`${fixture.id}.${id}`);
        for(const [checkField,checkValue] of Object.entries(checkExpected)) assert.equal(check[checkField],checkValue,`${fixture.id}.${id}.${checkField}`);
      }
      continue;
    }
    if(typeof expected==="number"){
      assert.ok(Number.isFinite(result[field]),`${fixture.id}.${field} finite`);
      near(result[field],expected,`${fixture.id}.${field}`);
    }else assert.equal(result[field],expected,`${fixture.id}.${field}`);
  }
  assert.equal(result.checks.length,profile.limits.length,`${fixture.id} named checks`);
  assert.ok(result.checks.every(check=>check.id&&check.article&&Number.isFinite(check.measured)),`${fixture.id} stable checks`);
}

console.log(`useful tools compatibility passed: ${concrete.cases.length+1} dormant broad concrete prototype and ${stairs.cases.length} governed stair fixtures`);
