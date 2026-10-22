import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";

const read=path=>readFile(new URL(`../${path}`,import.meta.url),"utf8");

test("useful tools renders each calculator as one compact row with an open action",async()=>{
  const source=await read("app/useful-tools/page.tsx");
  assert.ok(source.includes('className="tools-list"'));
  assert.ok(source.includes('className="tools-row"'));
  assert.ok(source.includes("tools-open"));
  assert.ok(source.includes(">Open</a>"));
});
