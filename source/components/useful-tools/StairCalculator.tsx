"use client";

import {useEffect,useMemo,useState} from "react";
import profile from "../../lib/useful-tools/profiles/ontario-residential-v1.json";
import {convertStairMeasurements,selectRecommendedStair} from "../../lib/useful-tools/stairs.mjs";
import {loadSavedCalculations,removeSavedCalculation,saveCalculation} from "../../lib/useful-tools/local-saves.mjs";
import {StairDiagram} from "./StairDiagram";
import {ToolActions} from "./ToolActions";

type UnitSystem="imperial"|"metric";
type SavedStair={id:string;toolVersion:number;calculatorType:string;name:string;unitSystem:UnitSystem;profileId:string;input:{totalRise:string;availableRun:string;width:string;treadThickness:string};output:unknown;savedAt:string};
const STORAGE_KEY="calibraytai.useful-tools.v1.stairs";
const checkLabels:Record<string,string>={"riser-height-min":"Minimum riser height","riser-height-max":"Maximum riser height","tread-run-min":"Minimum tread run","tread-run-max":"Maximum tread run"};

export function StairCalculator(){
  const [unitSystem,setUnitSystem]=useState<UnitSystem>("imperial");
  const [totalRise,setTotalRise]=useState("112");
  const [availableRun,setAvailableRun]=useState("168");
  const [width,setWidth]=useState("36");
  const [treadThickness,setTreadThickness]=useState("1.5");
  const [saved,setSaved]=useState<SavedStair[]>([]);
  useEffect(()=>{const loaded=loadSavedCalculations(window.localStorage,STORAGE_KEY);if(loaded.ok)setSaved(loaded.records as SavedStair[]);},[]);
  const unit=unitSystem==="metric"?"mm":"in";
  const calculated=useMemo(()=>{try{return {result:selectRecommendedStair({totalRise:{value:Number(totalRise),unit},availableRun:{value:Number(availableRun),unit}},profile),error:""};}catch(error){return {result:null,error:(error as Error).message};}},[totalRise,availableRun,unit]);
  const display=(metres:number)=>unitSystem==="metric"?`${(metres*1000).toFixed(1)} mm`:`${(metres/0.0254).toFixed(2)} in`;
  const displayInput=(value:string)=>`${value} ${unit}`;
  const switchUnits=(next:UnitSystem)=>{
    if(next===unitSystem)return;
    const converted=convertStairMeasurements({totalRise,availableRun,width,treadThickness},unitSystem,next);
    setTotalRise(converted.totalRise);setAvailableRun(converted.availableRun);setWidth(converted.width);setTreadThickness(converted.treadThickness);setUnitSystem(next);
  };
  const reset=()=>{setUnitSystem("imperial");setTotalRise("112");setAvailableRun("168");setWidth("36");setTreadThickness("1.5");};
  const save=()=>{if(!calculated.result)return {ok:false,error:"Complete the measurements before saving."};const record:SavedStair={id:crypto.randomUUID(),toolVersion:1,calculatorType:"stairs",name:"Stair calculation",unitSystem,profileId:profile.id,input:{totalRise,availableRun,width,treadThickness},output:calculated.result,savedAt:new Date().toISOString()};const savedResult=saveCalculation(window.localStorage,STORAGE_KEY,record);if(savedResult.ok)setSaved(savedResult.records as SavedStair[]);return savedResult;};
  const restore=(record:SavedStair)=>{setUnitSystem(record.unitSystem);setTotalRise(record.input.totalRise);setAvailableRun(record.input.availableRun);setWidth(record.input.width);setTreadThickness(record.input.treadThickness);};
  const remove=(id:string)=>{const removed=removeSavedCalculation(window.localStorage,STORAGE_KEY,id);if(removed.ok)setSaved(removed.records as SavedStair[]);};
  const summary=calculated.result?`CalibraytAI Stair Calculator\n${profile.label} — effective ${profile.effectiveDate}\n${calculated.result.riserCount} risers at ${display(calculated.result.riserHeightM)}\n${calculated.result.treadCount} treads at ${display(calculated.result.treadRunM)}\nAngle ${calculated.result.angleDegrees.toFixed(1)}°\nStringer ${display(calculated.result.stringerLengthM)}\nProfile checks: ${calculated.result.overallStatus.toUpperCase()}\nConfirm requirements with the authority having jurisdiction.`:"CalibraytAI Stair Calculator";
  return <section className="tool-calculator-section stair-calculator"><div className="tool-calculator-shell">
    <div className="tool-calculator-toolbar"><div className="tool-calculator-unit" aria-label="Measurement system"><button type="button" className={unitSystem==="imperial"?"active":""} onClick={()=>switchUnits("imperial")}>Imperial</button><button type="button" className={unitSystem==="metric"?"active":""} onClick={()=>switchUnits("metric")}>Metric</button></div><a href="/useful-tools/">All useful tools</a></div>
    <div className="tool-calculator-layout"><div className="tool-calculator-form"><fieldset className="tool-calculator-card"><legend>Stair measurements</legend><div className="tool-profile-badge"><span>Profile</span><strong>Ontario Residential — V1</strong><small>2024 Ontario Building Code · effective {profile.effectiveDate}</small></div><div className="tool-calculator-fields">
      {[["total-rise","Total rise",totalRise,setTotalRise],["available-run","Available run",availableRun,setAvailableRun],["stair-width","Stair width",width,setWidth],["tread-thickness","Tread thickness",treadThickness,setTreadThickness]].map(([id,label,value,setter])=><div className="tool-calculator-field" key={id as string}><label htmlFor={id as string}>{label as string}</label><div className="tool-calculator-input"><input id={id as string} inputMode="decimal" value={value as string} onChange={event=>(setter as (value:string)=>void)(event.target.value)}/><span>{unit}</span></div></div>)}
    </div>{calculated.error&&<p className="tool-input-error" role="alert">{calculated.error}</p>}<p className="tool-calculator-note dark-note">Width and tread thickness are recorded for layout reference. Ontario Residential — V1 evaluates rise and run only.</p></fieldset></div>
    <aside className="tool-calculator-output">{calculated.result&&<StairDiagram result={calculated.result} formatLength={display} treadThicknessLabel={displayInput(treadThickness)}/>}<div className="tool-calculator-results" aria-live="polite"><p className="eyebrow">STAIR LAYOUT</p>{calculated.error?<p className="tool-calculator-error" role="alert">{calculated.error}</p>:calculated.result&&<><div className="tool-calculator-primary-result"><span>Recommended layout</span><strong>{calculated.result.riserCount} risers</strong><small>{calculated.result.treadCount} treads</small></div><dl><div><dt>Risers</dt><dd>{calculated.result.riserCount}</dd></div><div><dt>Treads</dt><dd>{calculated.result.treadCount}</dd></div><div><dt>Exact rise</dt><dd>{display(calculated.result.riserHeightM)}</dd></div><div><dt>Exact run</dt><dd>{display(calculated.result.treadRunM)}</dd></div><div><dt>Stair angle</dt><dd>{calculated.result.angleDegrees.toFixed(1)}°</dd></div><div><dt>Stringer length</dt><dd>{display(calculated.result.stringerLengthM)}</dd></div></dl><h2 className="tool-check-title">Profile checks</h2><ul className="tool-checks">{calculated.result.checks.map(check=><li className={check.status} key={check.id}><span>{checkLabels[check.id]}</span><strong>{check.status==="pass"?"Within profile":"Outside profile"}</strong><small>{check.measured.toFixed(1)} mm · limit {check.limit} mm</small></li>)}</ul><p className="tool-calculator-note">This layout is guidance against the named profile, not permit approval. Confirm the complete stair design with the authority having jurisdiction.</p></>}
      <ToolActions onSave={save} onReset={reset} summary={summary}/></div>{saved.length>0&&<div className="tool-saved"><h2>Saved calculations</h2>{saved.map(record=><div className="tool-saved-row" key={record.id}><button type="button" onClick={()=>restore(record)}><strong>{record.name}</strong><span>{new Date(record.savedAt).toLocaleDateString("en-CA")}</span></button><button type="button" aria-label={`Remove ${record.name}`} onClick={()=>remove(record.id)}>Remove</button></div>)}</div>}</aside></div>
  </div></section>;
}
