import {toMetres} from "./units.mjs";

export function convertStairMeasurements(values,fromSystem,toSystem){
  if(fromSystem===toSystem) return {...values};
  const factor=fromSystem==="imperial"&&toSystem==="metric"?25.4:1/25.4;
  const precision=toSystem==="metric"?1:3;
  return Object.fromEntries(Object.entries(values).map(([key,value])=>{
    const numeric=Number(value);
    if(!Number.isFinite(numeric)||String(value).trim()==="") return [key,value];
    return [key,String(Number((numeric*factor).toFixed(precision)))];
  }));
}

function positiveMeasurement(measurement,name){
  const value=toMetres(Number(measurement?.value),measurement?.unit);
  if(!Number.isFinite(value)||value<=0) throw new RangeError(`${name} must be greater than zero.`);
  return value;
}

function geometry(totalRiseM,totalRunM,riserCount){
  const treadCount=riserCount-1;
  const riserHeightM=totalRiseM/riserCount;
  const treadRunM=totalRunM/treadCount;
  return {riserCount,treadCount,riserHeightM,treadRunM,totalRiseM,totalRunM,
    stringerLengthM:Math.hypot(totalRiseM,totalRunM),
    angleDegrees:Math.atan2(totalRiseM,totalRunM)*180/Math.PI};
}

export function calculateStairCandidates(input){
  const totalRiseM=positiveMeasurement(input.totalRise,"Total rise");
  const totalRunM=positiveMeasurement(input.availableRun,"Available run");
  const preferred=Number(input.preferredRiserHeightM)||0.175;
  const centre=Math.max(2,Math.round(totalRiseM/preferred));
  const min=Math.max(2,centre-8);
  const max=Math.min(2000,centre+8);
  const candidates=[];
  for(let count=min;count<=max;count++) candidates.push(geometry(totalRiseM,totalRunM,count));
  return candidates;
}

const CHECKS=[
  ["riser-height-min","minRiserHeightMm","riserHeightM",(value,limit)=>value>=limit],
  ["riser-height-max","maxRiserHeightMm","riserHeightM",(value,limit)=>value<=limit],
  ["tread-run-min","minTreadRunMm","treadRunM",(value,limit)=>value>=limit],
  ["tread-run-max","maxTreadRunMm","treadRunM",(value,limit)=>value<=limit],
];

export function evaluateStairProfile(layout,profile){
  const indexed=new Map(profile.limits.map(limit=>[limit.field,limit]));
  const checks=CHECKS.map(([id,field,measurement,predicate])=>{
    const rule=indexed.get(field);
    if(!rule) throw new RangeError(`Profile is missing ${field}.`);
    const measured=layout[measurement]*1000;
    return {id,field,measured,limit:rule.value,unit:rule.unit,article:rule.article,
      status:predicate(measured,rule.value)?"pass":"fail"};
  });
  return {checks,overallStatus:checks.every(check=>check.status==="pass")?"pass":"fail"};
}

function distanceFromPreferred(layout,profile){
  const limits=Object.fromEntries(profile.limits.map(limit=>[limit.field,limit.value]));
  const riseMid=(limits.minRiserHeightMm+limits.maxRiserHeightMm)/2;
  const runMid=(limits.minTreadRunMm+limits.maxTreadRunMm)/2;
  return Math.abs(layout.riserHeightM*1000-riseMid)/(limits.maxRiserHeightMm-limits.minRiserHeightMm)+
    Math.abs(layout.treadRunM*1000-runMid)/(limits.maxTreadRunMm-limits.minTreadRunMm);
}

export function selectRecommendedStair(input,profile){
  const evaluated=calculateStairCandidates(input).map(layout=>({...layout,...evaluateStairProfile(layout,profile)}));
  evaluated.sort((a,b)=>{
    const failuresA=a.checks.filter(check=>check.status==="fail").length;
    const failuresB=b.checks.filter(check=>check.status==="fail").length;
    return failuresA-failuresB||distanceFromPreferred(a,profile)-distanceFromPreferred(b,profile)||a.riserCount-b.riserCount;
  });
  return evaluated[0];
}
