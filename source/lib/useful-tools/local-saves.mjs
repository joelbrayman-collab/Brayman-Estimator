const failure = error => ({ok:false,error,records:[]});

export function loadSavedCalculations(storage,key){
  if(!storage) return failure("Saved calculations are unavailable on this device.");
  try{
    const raw=storage.getItem(key);
    if(!raw) return {ok:true,records:[]};
    const parsed=JSON.parse(raw);
    if(!Array.isArray(parsed)) return failure("Saved calculations could not be read on this device.");
    return {ok:true,records:[...parsed].sort((a,b)=>String(b.savedAt).localeCompare(String(a.savedAt)))};
  }catch{return failure("Saved calculations could not be read on this device.");}
}

export function saveCalculation(storage,key,record){
  if(!storage) return {ok:false,error:"This calculation could not be saved on this device."};
  try{
    const loaded=loadSavedCalculations(storage,key);
    const records=loaded.ok?loaded.records:[];
    const next=[record,...records.filter(item=>item.id!==record.id)].sort((a,b)=>String(b.savedAt).localeCompare(String(a.savedAt)));
    storage.setItem(key,JSON.stringify(next));
    return {ok:true,records:next};
  }catch{return {ok:false,error:"This calculation could not be saved on this device."};}
}

export function removeSavedCalculation(storage,key,id){
  if(!storage) return {ok:false,error:"This saved calculation could not be removed."};
  try{
    const loaded=loadSavedCalculations(storage,key);
    if(!loaded.ok) return {ok:false,error:loaded.error};
    const records=loaded.records.filter(item=>item.id!==id);
    storage.setItem(key,JSON.stringify(records));
    return {ok:true,records};
  }catch{return {ok:false,error:"This saved calculation could not be removed."};}
}

