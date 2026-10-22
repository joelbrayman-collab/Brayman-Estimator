import assert from "node:assert/strict";
import {execFileSync} from "node:child_process";
import {readFile} from "node:fs/promises";

const root = new URL("../", import.meta.url);
const read = path => readFile(new URL(path, root), "utf8");
const baseline = "e1107f32593b6270297ed0ce932e7cb899cebc63";
const baselineFile = path => execFileSync("git", ["show", `${baseline}:${path}`], {encoding:"utf8"});
const count = (source, needle) => source.split(needle).length - 1;
const stripHeroTool = source => source.replace(/<a className="hero-tool-link"[\s\S]*?<\/a>/, "<HERO_TOOL_LINK/>");

const home = await read("app/page.tsx");
assert.equal(count(home, 'href="/useful-tools/"'), 1, "Home must contain one Useful Tools hero link");
assert.match(home, /className="hero-tool-link"[^>]*href="\/useful-tools\/"[^>]*aria-label="Open Useful Tools"/);
assert.match(home, /<span>Useful Tools<\/span>/);
assert.equal(count(home, 'href="/employment-vs-entrepreneurship/"'), 0, "Home must not directly link the employment calculator");
assert.equal(stripHeroTool(home), stripHeroTool(baselineFile("app/page.tsx")), "Home changed outside the authorized hero tool link");

const landing = await read("app/useful-tools/page.tsx");
for (const route of ["/employment-vs-entrepreneurship/", "/useful-tools/concrete/", "/useful-tools/stairs/"]) {
  assert.equal(count(landing, route), 1, `${route} must appear exactly once on Useful Tools`);
}

for (const path of [
  "app/plan/page.tsx", "app/price/page.tsx", "app/contract/page.tsx",
  "app/build/page.tsx", "app/monitor/page.tsx", "app/learn/page.tsx",
  "app/site.tsx", "app/supplier-integration/page.tsx", "app/contractor-connection/page.tsx",
]) {
  const source = await read(path);
  assert.doesNotMatch(source, /\/useful-tools\//, `${path} gained an unauthorized Useful Tools link`);
  if (/app\/(plan|price|contract|build|monitor|learn)\/page\.tsx/.test(path)) {
    assert.equal(source, baselineFile(path), `${path} drifted from the frozen baseline`);
  }
}

console.log("useful tools route verification passed");
