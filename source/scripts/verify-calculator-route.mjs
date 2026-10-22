import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const calculatorPath = new URL(
  "../public/employment-vs-entrepreneurship/index.html",
  import.meta.url,
);

const html = await readFile(calculatorPath, "utf8");

for (const step of ["today", "business", "market", "costs", "results"]) {
  assert.match(html, new RegExp(`id=['\"]${step}['\"]`), `missing ${step} step`);
}

for (const trade of ["Masonry", "Electrical", "Plumbing", "Custom"]) {
  assert.match(html, new RegExp(`data-t=['\"]${trade}['\"]`), `missing ${trade} trade`);
}

assert.match(html, /function calc\(\)/, "missing calculator function");
assert.match(
  html,
  /This is a comparison of the assumptions you entered—not a recommendation about whether to start a business\./,
  "missing neutral result language",
);
assert.match(
  html,
  /class=['\"]site-return['\"][^>]*href=['\"]\/['\"]|href=['\"]\/['\"][^>]*class=['\"]site-return['\"]/, 
  "missing return path to CalibraytAI",
);
assert.match(html, /\.site-return\{margin-left:auto/, "missing return-link styling");
assert.match(html, /@media\(max-width:760px\)/, "missing tablet layout");
assert.match(html, /@media\(max-width:480px\)/, "missing phone layout");
assert.match(html, /\.nav\{overflow:auto/, "step navigation cannot scroll on narrow screens");

const route = "/employment-vs-entrepreneurship/";
const contractorPage = await readFile(
  new URL("../app/contractor-connection/page.tsx", import.meta.url),
  "utf8",
);
assert.equal(
  contractorPage.split(route).length - 1,
  1,
  "Contractor Connection must contain exactly one calculator link",
);
const homePage = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
assert.equal(
  homePage.split("/useful-tools/").length - 1,
  1,
  "Home hero must contain exactly one Useful Tools link",
);
assert.match(homePage, /className="hero-tool-link"/, "Home hero calculator button is missing");
assert.equal(
  homePage.split(route).length - 1,
  0,
  "Home must not restore the former direct Employment calculator link",
);

for (const frozenPath of [
  "plan/page.tsx",
  "price/page.tsx",
  "contract/page.tsx",
  "build/page.tsx",
  "monitor/page.tsx",
  "learn/page.tsx",
  "site.tsx",
  "supplier-integration/page.tsx",
]) {
  const source = await readFile(new URL(`../app/${frozenPath}`, import.meta.url), "utf8");
  assert.doesNotMatch(source, /\/employment-vs-entrepreneurship\//, `${frozenPath} changed`);
}

console.log("calculator route verification passed");
