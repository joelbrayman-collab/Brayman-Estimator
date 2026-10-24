// Screenshots for contractor modules 13 (Guided Estimating) and 14 (the calculators' three choices) of the Training
// & Acceptance Centre (23 Oct 2026).
//
// Starts the local training site (tests/training_page_server.py: real migrations, TRAINING_ENVIRONMENT on, the
// synthetic training company from app/training/environment.py), signs in as Ben (training) and does what the lessons
// in app/training/guided_estimating_lessons.py teach, on the real pages: a new home 'Lakeview New Home (training)'
// for Jordan Avery (training). Each picture is saved to app/static/training/shots/c13-*.png or c14-*.png (desktop
// 1280 x 900, phone 390 x 844), then shrunk to stay under ~330 KB. Synthetic data only. Any response of 500 or
// more, or a page JavaScript error, fails the walk.
//
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/opt/pw-browsers/chromium \
//      node --test --test-concurrency=1 tools/training/capture_guided_estimating_shots.mjs
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import test, { after, afterEach, before } from "node:test";
import { REPO, freePort, launch } from "../release/evidence_common.mjs";

const SHOTS = path.join(REPO, "app/static/training/shots");
const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
const PY = path.join(REPO, "venv/bin/python");
const HOME = "Lakeview New Home (training) BB";
const GARAGE = "Rivera Garage (training) BB";
const CUSTOMER = "Jordan Avery (training)";
const SCOPE = {
  site_prep: "SUBCONTRACTED", excavation: "SUBCONTRACTED", footings_foundation: "INTERNAL", framing: "INTERNAL",
  roofing: "SUBCONTRACTED", windows_doors: "INTERNAL", siding: "SUBCONTRACTED", electrical: "SUBCONTRACTED",
  plumbing: "SUBCONTRACTED", hvac: "SUBCONTRACTED", insulation: "SUBCONTRACTED", drywall: "SUBCONTRACTED",
  interior_finishes: "INTERNAL", final_cleanup: "INTERNAL",
};
let browser, server, base, facts;
const serverErrors = [];
const pageErrors = [];
const saved = [];
const sessions = {};
const W = {};

before(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const port = await freePort();
  server = spawn(PY, [path.join(REPO, "tests/training_page_server.py")], {
    cwd: REPO, env: { ...process.env, TRAINING_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("training site did not start\n" + out)), 240000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("training site exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => {
  for (const s of Object.values(sessions)) await s.ctx.close().catch(() => {});
  await browser?.close();
  server?.kill();
  shrink();
  console.log(`GUIDED_SHOTS=${saved.length} SERVER_ERRORS=${serverErrors.length} PAGE_ERRORS=${pageErrors.length}`);
  for (const name of saved) console.log(`SHOT ${name}`);
});
afterEach(() => {
  assert.deepEqual(serverErrors, [], "no response of 500 or more");
  assert.deepEqual(pageErrors, [], "no page JavaScript error");
});

let broken = "";
function step(name, fn) {
  test(name, async (t) => {
    if (broken) { t.skip(`after "${broken}" failed`); return; }
    try { await fn(t); } catch (e) { broken = name; throw e; }
  });
}
async function ben(viewport = DESK) {
  const id = `ben-${viewport.width}`;
  if (sessions[id]) return sessions[id];
  const phone = viewport.width <= 500;
  const ctx = await browser.newContext({ viewport, ...(phone ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  pg.on("pageerror", (e) => pageErrors.push(`${pg.url()}: ${e}`));
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  sessions[id] = { ctx, pg };
  await go(pg, "/login");
  await pg.fill("input[name=email]", facts.people.ben.email);
  await pg.fill("input[name=password]", facts.people.ben.password);
  await submit(pg, pg.locator("form button[type=submit]").first());
  assert.doesNotMatch(pg.url(), /\/login/);
  return sessions[id];
}
async function go(pg, url) {
  const r = await pg.goto(url.startsWith("http") ? url : `${base}${url}`);
  await pg.waitForLoadState();
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
const pathOf = (pg) => new URL(pg.url()).pathname;
async function shot(pg, name, focus) {
  assert.match(name, /^c1[34]-[a-z0-9-]+$/);
  if (pg.viewportSize().width <= 500) {
    const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
    assert.ok(over <= 1, `${name}: sideways scroll ${over}px`);
  }
  if (focus) {
    const el = focus.first();
    await el.waitFor({ state: "attached" });
    await el.evaluate((e) => e.scrollIntoView({ block: "center", inline: "nearest" }));
  } else {
    await pg.evaluate(() => window.scrollTo(0, 0));
  }
  await pg.waitForTimeout(150);
  await pg.screenshot({ path: path.join(SHOTS, `${name}.png`) });
  saved.push(`${name}.png`);
}
function shrink() {
  if (!saved.length) return;
  const r = spawnSync(PY, ["-c",
    "import os,sys\nfrom PIL import Image\nroot=sys.argv[1]\nfor n in sys.argv[2:]:\n p=os.path.join(root,n)\n" +
    " if os.path.getsize(p)<=330000: continue\n im=Image.open(p).convert('RGB')\n" +
    " im.quantize(colors=256,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).save(p,optimize=True)\n" +
    " if os.path.getsize(p)>330000:\n  w,h=im.size;im.resize((int(w*0.8),int(h*0.8)),Image.LANCZOS).quantize(colors=128).save(p,optimize=True)\n",
    SHOTS, ...new Set(saved)]);
  if (r.status !== 0) console.log(String(r.stderr));
}
async function press(pg, selector) { await submit(pg, pg.locator(selector).first()); }
async function openStage(pg, key) {
  await go(pg, `/projects/${W.project}/guided`);
  await submit(pg, pg.locator(`[data-stage="${key}"] a.ge-step-link`));
}
async function commercial(pg) {
  for (const [name, value] of [["pricing_posture", "Fair Market"], ["execution_risk", "Normal"], ["schedule_condition", "Normal"],
    ["site_condition", "Normal"], ["estimate_stage", "Preliminary"], ["delivery_model", "Mixed"]]) {
    await pg.selectOption(`select[name=${name}]`, value);
  }
}
async function fillFooting(pg) {
  for (const [i, length] of [[0, "120"], [1, "40"]]) {
    await pg.locator("input[name=footing_length]").nth(i).fill(length);
    await pg.locator("input[name=footing_width]").nth(i).fill("2");
    await pg.locator("input[name=footing_thickness]").nth(i).fill("10");
  }
  await pg.fill("input[name=waste_percent]", "5");
  await press(pg, 'form[data-trade-form] button[value="calculate"]');
}
async function recordQuote(pg, name, code, reference, amount) {
  const form = pg.locator("form[data-record-quote]");
  if (!(await form.isVisible())) await pg.locator("#quote > summary").click();
  await form.locator("input[name=subcontractor_legal_name]").fill(name);
  await form.locator("input[name=subcontractor_code]").fill(code);
  await form.locator("input[name=quote_reference]").fill(reference);
  await form.locator("input[name=amount]").fill(amount);
  await form.locator("input[name=quote_date]").fill("2026-10-20");
  await form.locator("input[name=included_scope]").fill("Supply and install");
  await submit(pg, form.locator("button[data-save-quote]"));
}
async function allowance(pg, amount) {
  const box = pg.locator("[data-allowance-zero]");
  if (!(await box.getAttribute("open"))) await box.locator("summary").click();
  await box.locator("input[name=amount]").fill(amount);
  await box.locator("form[data-allowance-form] input[name=reason]").fill("The quote is still to come");
  await submit(pg, box.locator("button[data-approve-allowance]"));
}

// ================================================================== Module 13
step("c13: Start New Estimate, the new home, its type and role", async () => {
  const { pg } = await ben();
  await go(pg, "/");
  await shot(pg, "c13-home-start", pg.locator("a[data-home-start-estimate]"));
  await submit(pg, pg.locator("a[data-home-start-estimate]"));
  await shot(pg, "c13-start-page");
  await submit(pg, pg.locator("a[data-new-project-estimate]"));
  await pg.fill("input[name=name]", HOME);
  await pg.selectOption("select[name=client_id]", { label: CUSTOMER });
  await pg.selectOption("select[data-guided-project-type]", "NEW_HOME");
  await pg.check('input[name=contractor_role][value="GENERAL_CONTRACTOR"]');
  await commercial(pg);
  await shot(pg, "c13-new-project-type", pg.locator("[data-guided-start-fields]"));
  await submit(pg, pg.locator("form.form-panel button[type=submit]"));
  assert.match(pathOf(pg), /\/guided\/scope$/);
  W.project = Number(pathOf(pg).split("/")[2]);
  await shot(pg, "c13-scope-empty", pg.locator('[data-stage-row="site_prep"]'));
});

step("c13: choose who does each stage and finalize", async () => {
  const { pg } = await ben();
  for (const [key, value] of Object.entries(SCOPE)) {
    await pg.locator(`[data-stage-row="${key}"] > fieldset.ge-choice input[value="${value}"]`).check();
  }
  await shot(pg, "c13-scope-chosen", pg.locator('[data-stage-row="footings_foundation"]'));
  await pg.locator('[data-parts="framing"] > summary').click();
  await shot(pg, "c13-scope-parts", pg.locator('[data-parts="framing"]'));
  await pg.locator('[data-parts="framing"] > summary').click();
  await press(pg, "button[data-scope-finalize]");
  assert.equal(pathOf(pg), `/projects/${W.project}/guided`);
  await shot(pg, "c13-workflow");
});

step("c13: an internal stage through its calculator, the review and labour", async () => {
  const { pg } = await ben();
  await openStage(pg, "footings_foundation");
  await shot(pg, "c13-stage-internal", pg.locator("[data-internal-tools]"));
  await submit(pg, pg.locator('a[data-tool="calculator:footing"]'));
  await fillFooting(pg);
  await pg.waitForFunction(() => document.querySelector("[data-link-stage]")?.value);
  await shot(pg, "c13-footing-calculator", pg.locator("[data-result-options]"));
  await pg.click("[data-link-button]");
  await pg.waitForSelector("[data-link-status]:not([hidden]) a");
  await shot(pg, "c13-footing-add", pg.locator("[data-link-status]"));
  await submit(pg, pg.locator("[data-link-status] a"));
  await shot(pg, "c13-calc-send", pg.locator("[data-send-to-review]"));
  await press(pg, "button[data-send-review]");
  const form = pg.locator("form[action*='/confirm']").first();
  await form.locator("select[name=target]").selectOption({ label: "Ready-mix concrete 25 MPa (training) (yd3)" });
  await shot(pg, "c13-review-confirm", form);
  await submit(pg, form.locator("button[type=submit]"));
  await submit(pg, pg.locator("a[data-back-to-stage]"));
  await pg.locator("[data-stage-labour] input[name^=hours_]").first().fill("40");
  await press(pg, "button[data-save-labour]");
  await shot(pg, "c13-stage-labour", pg.locator("[data-stage-lines]"));
  await press(pg, "button[data-confirm-routing]");
  await press(pg, "button[data-nav-complete-next]");
  await shot(pg, "c13-stage-complete");
});

step("c13: a subcontracted stage, waiting, quotes, select and use the cost", async () => {
  const { pg } = await ben();
  await openStage(pg, "electrical");
  await pg.fill("textarea[data-scope-description]", "Wire the house to code, panel and fixtures (training)");
  await press(pg, "button[data-setup-subcontract]");
  await shot(pg, "c13-sub-setup", pg.locator("[data-subcontract]"));
  await press(pg, "button[data-quote-requested]");
  await shot(pg, "c13-sub-waiting");
  await recordQuote(pg, "Sparks Electric (training)", "SPARKS-TRN", "EL-9", "24500");
  await recordQuote(pg, "Bright Wire (training)", "BRIGHT-TRN", "EL-10", "26100");
  await shot(pg, "c13-sub-quotes", pg.locator("[data-quotes]"));
  await press(pg, 'button[data-select-quote="EL-9"]');
  await shot(pg, "c13-sub-use-cost", pg.locator("[data-suggested-cost]"));
  await press(pg, "button[data-use-quote-cost]");
  await press(pg, "button[data-nav-complete-next]");
});

step("c13: missing cost, an allowance, Save & Exit and Resume", async () => {
  const { pg } = await ben();
  await openStage(pg, "hvac");
  await press(pg, "button[data-nav-complete-next]");
  await shot(pg, "c13-missing");
  await allowance(pg, "16000");
  await shot(pg, "c13-allowance", pg.locator("[data-allowance-zero]"));
  await press(pg, "button[data-nav-complete-next]");
  await openStage(pg, "windows_doors");
  await press(pg, "button[data-nav-save-exit]");
  await shot(pg, "c13-resume", pg.locator("[data-hub-guided]"));
});

step("c13: the internal cost estimate and the pricing gate", async () => {
  const { pg } = await ben();
  await go(pg, `/projects/${W.project}/guided/internal-cost`);
  await shot(pg, "c13-internal-cost");
  await go(pg, `/projects/${W.project}/guided/pricing`);
  await shot(pg, "c13-pricing-blocked");
});

step("c13: every stage resolved, costing approved, pricing applied, proposal prepared", async () => {
  const { pg } = await ben();
  for (const key of Object.keys(SCOPE)) {
    await go(pg, `/projects/${W.project}/guided`);
    if ((await pg.locator(`[data-stage="${key}"]`).getAttribute("data-status")) === "COMPLETE") continue;
    await openStage(pg, key);
    await allowance(pg, "1000");
    await press(pg, "button[data-nav-complete-next]");
  }
  await go(pg, `/projects/${W.project}/guided/pricing`);
  await press(pg, "button[data-approve-costing]");
  await press(pg, "button[data-apply-pricing]");
  await shot(pg, "c13-pricing-priced", pg.locator("[data-pricing-snapshot]"));
  await submit(pg, pg.locator("a[data-create-proposal]"));
  await shot(pg, "c13-proposal");
});

// ================================================================== Module 14
step("c14: Use Result Only and Add to Existing Project", async () => {
  const { pg } = await ben();
  await go(pg, "/calculators/concrete");
  await pg.fill("#length", "24"); await pg.fill("#width", "24"); await pg.fill("#slab_thickness", "4"); await pg.fill("#waste_percent", "5");
  await pg.click("button.cc-calculate");
  await pg.waitForSelector("[data-concrete-result]:not([hidden])");
  await shot(pg, "c14-concrete-result", pg.locator("[data-result-options]"));
  await pg.click("[data-use-result-only]");
  await shot(pg, "c14-use-only", pg.locator("[data-option-use-only]"));
  await pg.selectOption("[data-link-select]", String(W.project));
  await pg.waitForSelector("[data-stage-wrap]:not([hidden])");
  await pg.locator("[data-link-stage]").selectOption({ label: "Footings & foundation" });
  await pg.click("[data-link-button]");
  await pg.waitForSelector("[data-link-status]:not([hidden]) a");
  await shot(pg, "c14-add-existing", pg.locator("[data-link-project]"));
  await submit(pg, pg.locator("[data-link-status] a"));
  await press(pg, "button[data-send-review]");
  await shot(pg, "c14-send-review");
});

step("c14: Create New Project, Cancel back to the same result, then the new project", async () => {
  const { pg } = await ben();
  await go(pg, "/calculators/concrete");
  await pg.fill("#length", "24"); await pg.fill("#width", "24"); await pg.fill("#slab_thickness", "4"); await pg.fill("#waste_percent", "5");
  await pg.click("button.cc-calculate");
  await pg.waitForSelector("[data-concrete-result]:not([hidden])");
  await submit(pg, pg.locator("[data-new-project-button]"));
  await shot(pg, "c14-new-project", pg.locator("[data-carry-banner]"));
  await submit(pg, pg.locator("a[data-carry-cancel]"));
  await pg.waitForSelector("[data-concrete-result]:not([hidden])");
  await shot(pg, "c14-cancel-back", pg.locator("[data-carry-restored]"));
  await submit(pg, pg.locator("[data-new-project-button]"));
  await pg.fill("input[name=name]", GARAGE);
  await pg.selectOption("select[name=client_id]", { label: CUSTOMER });
  await pg.selectOption("select[data-guided-project-type]", "GARAGE_OUTBUILDING");
  await pg.check('input[name=contractor_role][value="SELECTED_PORTIONS"]');
  await commercial(pg);
  await submit(pg, pg.locator("form.form-panel button[type=submit]"));
  for (const row of await pg.locator("[data-stage-row]").all()) {
    await row.locator(":scope > fieldset.ge-choice input[value='INTERNAL']").check();
  }
  await press(pg, "button[data-scope-finalize]");
  await shot(pg, "c14-waiting", pg.locator("[data-waiting-calculations]"));
});

step("c14: the three choices on the iPhone", async () => {
  const { pg } = await ben(PHONE);
  await go(pg, "/useful-calculators/footing");
  await fillFooting(pg);
  await shot(pg, "c14-phone-options", pg.locator("[data-result-options]"));
});
