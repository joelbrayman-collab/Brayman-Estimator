"use client";

// DORMANT BROAD CONCRETE PROTOTYPE
// Retained for historical compatibility only. It is not imported by the public
// Concrete route and is not the governed Concrete calculation authority.

import {useEffect,useMemo,useState} from "react";
import {calculateConcretePour,UsefulToolsValidationError} from "../../lib/useful-tools/concrete.mjs";
import {fromCubicMetres} from "../../lib/useful-tools/units.mjs";
import {loadSavedCalculations,removeSavedCalculation,saveCalculation} from "../../lib/useful-tools/local-saves.mjs";
import {ConcreteDiagram} from "./ConcreteDiagram";
import {ToolActions} from "./ToolActions";

const shapes=[
  ["slab","Slab / pad"],["footing","Footing"],["wall","Wall"],["round-column","Round column"],
  ["post-hole","Tube / post hole"],["curb","Curb"],["concrete-stairs","Concrete stairs"],
] as const;
type Shape=typeof shapes[number][0];
type UnitSystem="imperial"|"metric";
type SectionState={id:string;name:string;type:Shape;quantity:string;length:string;width:string;thickness:string;height:string;diameter:string;treadRun:string;riserHeight:string;riserCount:string};
type SavedConcrete={id:string;toolVersion:number;calculatorType:string;name:string;unitSystem:UnitSystem;input:{sections:SectionState[];wastePercent:string;orderIncrement:string;bagYield:string;truckCapacity:string};output:unknown;savedAt:string};
const STORAGE_KEY="calibraytai.useful-tools.v1.concrete";

const freshSection=(id=crypto.randomUUID?.()??String(Date.now())):SectionState=>({id,name:"",type:"slab",quantity:"1",length:"20",width:"24",thickness:"4",height:"8",diameter:"12",treadRun:"10",riserHeight:"7.5",riserCount:"5"});
const dimensions:Record<Shape,Array<keyof SectionState>>={
  slab:["length","width","thickness"],footing:["length","width","thickness"],wall:["length","height","thickness"],
  "round-column":["diameter","height"],"post-hole":["diameter","height"],curb:["length","width","height"],
  "concrete-stairs":["width","treadRun","riserHeight","riserCount"],
};
const labels:Record<string,string>={length:"Length",width:"Width",thickness:"Thickness",height:"Height / depth",diameter:"Diameter",treadRun:"Tread run",riserHeight:"Riser height",riserCount:"Riser count"};

function measurement(value:string,field:string,system:UnitSystem){
  const thin=field==="thickness"||field==="riserHeight";
  return {value:Number(value),unit:system==="metric"?(thin?"mm":"m"):(thin?"in":"ft")};
}

export function ConcreteCalculator(){
  const [unitSystem,setUnitSystem]=useState<UnitSystem>("imperial");
  const [sections,setSections]=useState<SectionState[]>([freshSection("section-1")]);
  const [wastePercent,setWastePercent]=useState("10");
  const [orderIncrement,setOrderIncrement]=useState("0.25");
  const [bagYield,setBagYield]=useState("");
  const [truckCapacity,setTruckCapacity]=useState("");
  const [saved,setSaved]=useState<SavedConcrete[]>([]);

  useEffect(()=>{const loaded=loadSavedCalculations(window.localStorage,STORAGE_KEY);if(loaded.ok)setSaved(loaded.records as SavedConcrete[]);},[]);

  const update=(id:string,field:keyof SectionState,value:string)=>setSections(current=>current.map(section=>section.id===id?{...section,[field]:value}:section));
  const input=useMemo(()=>({
    sections:sections.map(section=>{
      const built:any={type:section.type,quantity:Number(section.quantity),name:section.name};
      for(const field of dimensions[section.type]) built[field]=field==="riserCount"?Number(section[field]):measurement(section[field],field,unitSystem);
      return built;
    }),
    wastePercent:Number(wastePercent),orderIncrementM3:Number(orderIncrement),
    ...(bagYield?{bagYieldM3:Number(bagYield)}:{}),...(truckCapacity?{truckCapacityM3:Number(truckCapacity)}:{}),
  }),[sections,unitSystem,wastePercent,orderIncrement,bagYield,truckCapacity]);

  const calculated=useMemo(()=>{try{return {result:calculateConcretePour(input),error:""};}catch(error){return {result:null,error:error instanceof UsefulToolsValidationError?error.issues[0]?.message:"Check the measurements entered."};}},[input]);
  const format=(value:number)=>value.toLocaleString("en-CA",{maximumFractionDigits:3});
  const reset=()=>{setSections([freshSection()]);setUnitSystem("imperial");setWastePercent("10");setOrderIncrement("0.25");setBagYield("");setTruckCapacity("");};
  const save=()=>{if(!calculated.result)return {ok:false,error:"Complete the measurements before saving."};const record:SavedConcrete={id:crypto.randomUUID(),toolVersion:1,calculatorType:"concrete",name:sections[0].name||"Concrete calculation",unitSystem,input:{sections,wastePercent,orderIncrement,bagYield,truckCapacity},output:calculated.result,savedAt:new Date().toISOString()};const result=saveCalculation(window.localStorage,STORAGE_KEY,record);if(result.ok)setSaved(result.records as SavedConcrete[]);return result;};
  const restore=(record:SavedConcrete)=>{setUnitSystem(record.unitSystem);setSections(record.input.sections);setWastePercent(record.input.wastePercent);setOrderIncrement(record.input.orderIncrement);setBagYield(record.input.bagYield);setTruckCapacity(record.input.truckCapacity);};
  const remove=(id:string)=>{const result=removeSavedCalculation(window.localStorage,STORAGE_KEY,id);if(result.ok)setSaved(result.records as SavedConcrete[]);};
  const summary=calculated.result?`CalibraytAI Concrete Calculator\nBase volume: ${format(calculated.result.baseM3)} m³\nAdjusted volume: ${format(calculated.result.adjustedM3)} m³\nRecommended order: ${format(calculated.result.recommendedOrderM3)} m³`:"CalibraytAI Concrete Calculator";

  return <section className="tool-calculator-section"><div className="tool-calculator-shell">
    <div className="tool-calculator-toolbar"><div className="tool-calculator-unit" aria-label="Measurement system"><button type="button" className={unitSystem==="imperial"?"active":""} onClick={()=>setUnitSystem("imperial")}>Imperial</button><button type="button" className={unitSystem==="metric"?"active":""} onClick={()=>setUnitSystem("metric")}>Metric</button></div><a href="/useful-tools/">All useful tools</a></div>
    <div className="tool-calculator-layout"><div className="tool-calculator-form">
      {sections.map((section,index)=><fieldset className="tool-calculator-card" key={section.id}><legend>Section {index+1}</legend>
        <div className="tool-calculator-field full"><label htmlFor={`${section.id}-name`}>Section name <span>optional</span></label><input id={`${section.id}-name`} value={section.name} onChange={event=>update(section.id,"name",event.target.value)} placeholder="Garage slab"/></div>
        <div className="tool-calculator-field full"><label htmlFor={`${section.id}-shape`}>Shape</label><select id={`${section.id}-shape`} value={section.type} onChange={event=>update(section.id,"type",event.target.value as Shape)}>{shapes.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></div>
        <div className="tool-calculator-fields">{dimensions[section.type].map(field=><div className="tool-calculator-field" key={field}><label htmlFor={`${section.id}-${field}`}>{labels[field]}</label><div className="tool-calculator-input"><input inputMode="decimal" id={`${section.id}-${field}`} value={section[field]} onChange={event=>update(section.id,field,event.target.value)}/><span>{field==="riserCount"?"":unitSystem==="metric"?((field==="thickness"||field==="riserHeight")?"mm":"m"):((field==="thickness"||field==="riserHeight")?"in":"ft")}</span></div></div>)}</div>
        <div className="tool-calculator-field"><label htmlFor={`${section.id}-quantity`}>Quantity</label><input inputMode="numeric" id={`${section.id}-quantity`} value={section.quantity} onChange={event=>update(section.id,"quantity",event.target.value)}/></div>
        {sections.length>1&&<button className="tool-calculator-remove" type="button" onClick={()=>setSections(current=>current.filter(item=>item.id!==section.id))}>Remove section</button>}
      </fieldset>)}
      <button className="btn tool-calculator-add" type="button" onClick={()=>setSections(current=>[...current,freshSection()])}>Add section</button>
      <div className="tool-calculator-card tool-calculator-options"><h2>Pour options</h2><div className="tool-calculator-fields">
        <div className="tool-calculator-field"><label htmlFor="waste">Waste allowance</label><div className="tool-calculator-input"><input id="waste" inputMode="decimal" value={wastePercent} onChange={event=>setWastePercent(event.target.value)}/><span>%</span></div></div>
        <div className="tool-calculator-field"><label htmlFor="increment">Order increment</label><div className="tool-calculator-input"><input id="increment" inputMode="decimal" value={orderIncrement} onChange={event=>setOrderIncrement(event.target.value)}/><span>m³</span></div></div>
        <div className="tool-calculator-field"><label htmlFor="bags">Bag yield <span>optional</span></label><div className="tool-calculator-input"><input id="bags" inputMode="decimal" value={bagYield} onChange={event=>setBagYield(event.target.value)}/><span>m³</span></div></div>
        <div className="tool-calculator-field"><label htmlFor="truck">Truck capacity <span>optional</span></label><div className="tool-calculator-input"><input id="truck" inputMode="decimal" value={truckCapacity} onChange={event=>setTruckCapacity(event.target.value)}/><span>m³</span></div></div>
      </div></div>
    </div><aside className="tool-calculator-output"><ConcreteDiagram shape={sections[0].type} measurement={unitSystem}/><div className="tool-calculator-results" aria-live="polite">
      <p className="eyebrow">CALCULATED POUR</p>{calculated.error?<p className="tool-calculator-error" role="alert">{calculated.error}</p>:calculated.result&&<><div className="tool-calculator-primary-result"><span>Recommended order</span><strong>{format(calculated.result.recommendedOrderM3)} m³</strong><small>{format(fromCubicMetres(calculated.result.recommendedOrderM3,"yd3"))} Cubic yards</small></div><dl><div><dt>Base volume</dt><dd>{format(calculated.result.baseM3)} m³</dd></div><div><dt>Waste volume</dt><dd>{format(calculated.result.wasteM3)} m³</dd></div><div><dt>Adjusted volume</dt><dd>{format(calculated.result.adjustedM3)} m³</dd></div><div><dt>Cubic metres</dt><dd>{format(calculated.result.adjustedM3)}</dd></div><div><dt>Cubic yards</dt><dd>{format(fromCubicMetres(calculated.result.adjustedM3,"yd3"))}</dd></div>{calculated.result.bagCount!==undefined&&<div><dt>Bags</dt><dd>{calculated.result.bagCount}</dd></div>}{calculated.result.truckCount!==undefined&&<div><dt>Truckloads</dt><dd>{calculated.result.truckCount}</dd></div>}</dl><p className="tool-calculator-note">Supplier capacities and final order quantities should be confirmed before ordering.</p></>}
      <ToolActions onSave={save} onReset={reset} summary={summary}/>
    </div>{saved.length>0&&<div className="tool-saved"><h2>Saved calculations</h2>{saved.map(record=><div className="tool-saved-row" key={record.id}><button type="button" onClick={()=>restore(record)}><strong>{record.name}</strong><span>{new Date(record.savedAt).toLocaleDateString("en-CA")}</span></button><button type="button" aria-label={`Remove ${record.name}`} onClick={()=>remove(record.id)}>Remove</button></div>)}</div>}</aside></div>
  </div></section>;
}
