import test from "node:test";
import assert from "node:assert/strict";
import profile from "../lib/useful-tools/profiles/ontario-residential-v1.json" with {type:"json"};
import {calculateStairCandidates,evaluateStairProfile,selectRecommendedStair} from "../lib/useful-tools/stairs.mjs";
import * as stairTools from "../lib/useful-tools/stairs.mjs";

const metric={totalRise:{value:2800,unit:"mm"},availableRun:{value:4000,unit:"mm"}};

test("unit toggles preserve the same physical stair measurements",()=>{
  assert.equal(typeof stairTools.convertStairMeasurements,"function");
  const metricValues=stairTools.convertStairMeasurements({totalRise:"112",availableRun:"168",width:"36",treadThickness:"1.5"},"imperial","metric");
  assert.deepEqual(metricValues,{totalRise:"2844.8",availableRun:"4267.2",width:"914.4",treadThickness:"38.1"});
  assert.deepEqual(stairTools.convertStairMeasurements(metricValues,"metric","imperial"),{totalRise:"112",availableRun:"168",width:"36",treadThickness:"1.5"});
});

test("stair geometry is internally consistent",()=>{
  const result=selectRecommendedStair(metric,profile);
  assert.equal(result.treadCount,result.riserCount-1);
  assert.equal(result.riserHeightM,result.totalRiseM/result.riserCount);
  assert.equal(result.treadRunM,result.totalRunM/result.treadCount);
  assert.ok(Math.abs(result.stringerLengthM-Math.hypot(result.totalRiseM,result.totalRunM))<1e-12);
  assert.ok(Math.abs(result.angleDegrees-Math.atan2(result.totalRiseM,result.totalRunM)*180/Math.PI)<1e-12);
});

test("equivalent imperial and metric inputs produce the same canonical result",()=>{
  const a=selectRecommendedStair(metric,profile);
  const b=selectRecommendedStair({totalRise:{value:2800/25.4,unit:"in"},availableRun:{value:4000/25.4,unit:"in"}},profile);
  for(const key of ["riserCount","treadCount","riserHeightM","treadRunM","totalRiseM","totalRunM","stringerLengthM","angleDegrees"])
    assert.ok(Math.abs(a[key]-b[key])<1e-10,key);
});

test("candidate generation returns integer layouts",()=>{
  const candidates=calculateStairCandidates(metric);
  assert.ok(candidates.length>3);
  assert.ok(candidates.every(item=>Number.isInteger(item.riserCount)&&item.treadCount===item.riserCount-1));
});

test("each approved boundary reports exact, inside and outside status",()=>{
  const make=(riseMm,runMm)=>({riserCount:15,treadCount:14,riserHeightM:riseMm/1000,treadRunM:runMm/1000,totalRiseM:15*riseMm/1000,totalRunM:14*runMm/1000,stringerLengthM:1,angleDegrees:30});
  const scenarios=[
    ["minRiserHeightMm",125,126,124,"riser-height-min"],
    ["maxRiserHeightMm",200,199,201,"riser-height-max"],
    ["minTreadRunMm",255,256,254,"tread-run-min"],
    ["maxTreadRunMm",355,354,356,"tread-run-max"],
  ];
  for(const [field,exact,inside,outside,id] of scenarios){
    const baseRise=field.includes("Riser")?exact:175;
    const baseRun=field.includes("Tread")?exact:280;
    for(const [value,status] of [[exact,"pass"],[inside,"pass"],[outside,"fail"]]){
      const checks=evaluateStairProfile(make(field.includes("Riser")?value:baseRise,field.includes("Tread")?value:baseRun),profile);
      const check=checks.checks.find(item=>item.id===id);
      assert.equal(check.status,status,`${field} ${value}`);
      assert.equal(check.limit,exact);
      assert.equal(check.measured,value);
      assert.equal(check.unit,"mm");
      assert.equal(check.article,profile.limits.find(item=>item.field===field).article);
      assert.equal(checks.overallStatus,status);
    }
  }
});

test("insufficient run returns a recommendation with explicit failed checks",()=>{
  const result=selectRecommendedStair({totalRise:{value:3,unit:"m"},availableRun:{value:1,unit:"m"}},profile);
  assert.equal(result.overallStatus,"fail");
  assert.ok(result.checks.some(check=>check.status==="fail"));
});

test("invalid geometry is rejected",()=>{
  assert.throws(()=>calculateStairCandidates({totalRise:{value:0,unit:"m"},availableRun:{value:2,unit:"m"}}),/greater than zero/);
});
