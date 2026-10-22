import test from "node:test";
import assert from "node:assert/strict";
import profile from "../lib/useful-tools/profiles/ontario-residential-v1.json" with {type:"json"};
import {selectRecommendedStair} from "../lib/useful-tools/stairs.mjs";
import {createStairDiagramGeometry} from "../lib/useful-tools/stair-diagram-geometry.mjs";

const close=(actual,expected,tolerance=1e-9,message="")=>
  assert.ok(Math.abs(actual-expected)<=tolerance,`${message} expected ${expected}, received ${actual}`);

const benchmark=selectRecommendedStair({
  totalRise:{value:38,unit:"in"},
  availableRun:{value:44,unit:"in"},
},profile);

test("benchmark drawing preserves the governed 38 by 44 stair geometry",()=>{
  const drawing=createStairDiagramGeometry(benchmark);

  assert.equal(drawing.risers.length,5);
  assert.equal(drawing.treads.length,4);
  close(drawing.height/drawing.width,38/44,1e-12,"rendered rise/run ratio");
  close(drawing.angleDegrees,40.81508387488159,1e-12,"rendered stair angle");
  close(drawing.stringer.end.x-drawing.stringer.start.x,drawing.width,1e-12,"stringer run");
  close(drawing.stringer.end.y-drawing.stringer.start.y,drawing.height,1e-12,"stringer rise");
  close(drawing.stringer.angleDegrees,drawing.angleDegrees,1e-12,"stringer angle");
});

test("a materially different stair uses its own governed proportions",()=>{
  const result=selectRecommendedStair({
    totalRise:{value:112,unit:"in"},
    availableRun:{value:168,unit:"in"},
  },profile);
  const drawing=createStairDiagramGeometry(result);

  close(drawing.height/drawing.width,2/3,1e-12,"rendered rise/run ratio");
  close(drawing.angleDegrees,33.690067525979785,1e-12,"rendered stair angle");
  assert.equal(drawing.risers.length,result.riserCount);
  assert.equal(drawing.treads.length,result.treadCount);
});

test("equivalent Imperial and Metric results render identical physical geometry",()=>{
  const imperial=selectRecommendedStair({
    totalRise:{value:38,unit:"in"},
    availableRun:{value:44,unit:"in"},
  },profile);
  const metric=selectRecommendedStair({
    totalRise:{value:965.2,unit:"mm"},
    availableRun:{value:1117.6,unit:"mm"},
  },profile);

  const a=createStairDiagramGeometry(imperial);
  const b=createStairDiagramGeometry(metric);
  for(const key of ["left","top","right","bottom","width","height","treadWidth","riserHeight","angleDegrees"])
    close(b[key],a[key],1e-10,`unit-invariant ${key}`);
  assert.equal(b.risers.length,a.risers.length);
  assert.equal(b.treads.length,a.treads.length);
  for(const endpoint of ["start","end"]){
    close(b.stringer[endpoint].x,a.stringer[endpoint].x,1e-10,`unit-invariant stringer ${endpoint} x`);
    close(b.stringer[endpoint].y,a.stringer[endpoint].y,1e-10,`unit-invariant stringer ${endpoint} y`);
  }
});
