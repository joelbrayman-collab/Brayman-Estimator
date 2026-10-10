"use client";

import {useState} from "react";

type Props={onSave:()=>{ok:boolean;error?:string};onReset:()=>void;summary:string};

export function ToolActions({onSave,onReset,summary}:Props){
  const [status,setStatus]=useState("");
  const save=()=>{const result=onSave();setStatus(result.ok?"Calculation saved on this device.":result.error??"Calculation was not saved.");};
  const share=async()=>{try{if(navigator.share) await navigator.share({title:"CalibraytAI calculation",text:summary});else if(navigator.clipboard) await navigator.clipboard.writeText(summary);else throw new Error("unavailable");setStatus(navigator.share?"Share options opened.":"Summary copied.");}catch(error){if((error as Error).name!=="AbortError")setStatus("This calculation could not be shared on this device.");}};
  return <div className="tool-calculator-actions"><button type="button" className="btn primary" onClick={save}>Save</button><button type="button" className="btn" onClick={()=>window.print()}>Print</button><button type="button" className="btn" onClick={share}>Share</button><button type="button" className="btn" onClick={onReset}>Start New</button><span aria-live="polite">{status}</span></div>;
}

