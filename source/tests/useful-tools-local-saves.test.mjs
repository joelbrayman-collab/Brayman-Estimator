import assert from "node:assert/strict";
import test from "node:test";
import {loadSavedCalculations,removeSavedCalculation,saveCalculation} from "../lib/useful-tools/local-saves.mjs";

class MemoryStorage{
  data=new Map();
  getItem(key){return this.data.get(key)??null;}
  setItem(key,value){this.data.set(key,value);}
  removeItem(key){this.data.delete(key);}
}

const key="calibraytai.useful-tools.v1.concrete";
const record=(id,savedAt)=>({id,toolVersion:1,calculatorType:"concrete",name:id,unitSystem:"imperial",input:{},output:{},savedAt});

test("round trips saves in stable most-recent-first order",()=>{
  const storage=new MemoryStorage();
  assert.equal(saveCalculation(storage,key,record("old","2026-09-26T10:00:00Z")).ok,true);
  assert.equal(saveCalculation(storage,key,record("new","2026-09-26T11:00:00Z")).ok,true);
  const loaded=loadSavedCalculations(storage,key);
  assert.equal(loaded.ok,true);
  assert.deepEqual(loaded.records.map(item=>item.id),["new","old"]);
});

test("removes one saved calculation",()=>{
  const storage=new MemoryStorage();
  saveCalculation(storage,key,record("a","2026-09-26T10:00:00Z"));
  saveCalculation(storage,key,record("b","2026-09-26T11:00:00Z"));
  assert.equal(removeSavedCalculation(storage,key,"a").ok,true);
  assert.deepEqual(loadSavedCalculations(storage,key).records.map(item=>item.id),["b"]);
});

test("recovers explicitly from corrupt storage",()=>{
  const storage=new MemoryStorage();
  storage.setItem(key,"not json");
  const result=loadSavedCalculations(storage,key);
  assert.equal(result.ok,false);
  assert.deepEqual(result.records,[]);
  assert.equal(result.error,"Saved calculations could not be read on this device.");
});

test("does not throw when storage is unavailable",()=>{
  assert.doesNotThrow(()=>loadSavedCalculations(null,key));
  assert.equal(loadSavedCalculations(null,key).ok,false);
  assert.equal(saveCalculation(null,key,record("a","2026-09-26T10:00:00Z")).ok,false);
});

test("reports quota failures instead of claiming success",()=>{
  const storage={getItem(){return "[]";},setItem(){throw new DOMException("full","QuotaExceededError");}};
  const result=saveCalculation(storage,key,record("a","2026-09-26T10:00:00Z"));
  assert.equal(result.ok,false);
  assert.match(result.error,/could not be saved/i);
});
