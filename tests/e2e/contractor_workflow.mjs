// V1 internal acceptance: the contractor's daily estimating workflow, end to end, in a real
// browser against a local office whose database was built by the real migrations.
// Sign in → Home → client → project → drawings → scope → estimate → company cost → footing
// calculation → review and confirm → site allowance → labour hours → scope routing →
// proposal blocked before approval → costing approval → pricing → proposal issued → PDF.
// Every figure is checked against a hand calculation. Synthetic data only.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import net from "node:net";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(fileURLToPath(new URL("../..", import.meta.url)));
const { chromium } = await import(
  pathToFileURL(path.join(repoRoot, "calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs")).href
);
const python = process.env.E2E_PYTHON || path.join(repoRoot, "venv/bin/python");

function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close((e) => (e ? reject(e) : resolve(p))); });
  });
}

function startOffice(port) {
  const child = spawn(python, [path.join(repoRoot, "tests/e2e_office_server.py")], {
    cwd: repoRoot, env: { ...process.env, E2E_OFFICE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  child.stdout.on("data", (c) => (out += c)); child.stderr.on("data", (c) => (out += c));
  const ready = new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 120000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (child.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  return { child, ready };
}

const money = (text) => Number(String(text).replace(/[^0-9.-]/g, ""));
const exe = process.env.E2E_BROWSER_EXECUTABLE;

test("the contractor estimates a footing job from sign-in to an issued proposal", { timeout: 600000 }, async () => {
  // E2E_BASE points at an office that is already running (development only).
  const port = process.env.E2E_BASE ? null : await freePort();
  const office = process.env.E2E_BASE ? { ready: Promise.resolve(), child: { kill() {} } } : startOffice(port);
  const base = process.env.E2E_BASE || `http://127.0.0.1:${port}`;
  let browser;
  const pageErrors = [];
  try {
    await office.ready;
    browser = await chromium.launch(exe ? { executablePath: exe, headless: true } : { channel: "chrome", headless: true });

    // Home on a phone: Company Calendar sits immediately below Start New Project.
    const phone = await browser.newPage({ viewport: { width: 390, height: 844 } });
    await phone.goto(`${base}/login`);
    await phone.fill("#email", "office@example.com");
    await phone.fill("#password", "office-test-password");
    await phone.getByRole("button", { name: "Sign in" }).click();
    await phone.waitForURL(`${base}/`);
    for (const width of [390, 1280]) {
      await phone.setViewportSize({ width, height: 900 });
      await phone.waitForTimeout(500); // let the side menu finish its width change
      const start = await phone.locator("a.home-start").boundingBox();
      const cal = await phone.locator("a.home-calendar").boundingBox();
      assert.ok(cal.y >= start.y + start.height - 1 && cal.y - (start.y + start.height) <= 16, `calendar below start at ${width}px`);
      assert.ok(Math.abs(cal.x - start.x) <= 1, `calendar aligned with start at ${width}px`);
      const overflow = await phone.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
      assert.ok(overflow <= 1, `home scrolls sideways at ${width}px`);
    }
    await phone.close();

    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => pageErrors.push(e.message));
    const flash = async () => (await page.locator(".flash, .alert, [role=alert]").allInnerTexts()).join(" | ");
    const submit = async (locator) => { await Promise.all([page.waitForLoadState(), locator.click()]); await page.waitForLoadState(); };

    await page.goto(`${base}/login`);
    await page.fill("#email", "office@example.com");
    await page.fill("#password", "office-test-password");
    await submit(page.getByRole("button", { name: "Sign in" }));

    // Client, then Start New Project from Home.
    await page.goto(`${base}/clients/new`);
    await page.fill("[name=name]", "E2E Synthetic Client (not a customer)");
    await submit(page.locator("main form button[type=submit]"));
    assert.match(await flash(), /Client created/);
    await page.goto(`${base}/`);
    await submit(page.locator("a.home-start"));
    await page.fill("[name=name]", "E2E Synthetic Footing Job (not a customer)");
    await page.selectOption("[name=client_id]", { label: "E2E Synthetic Client (not a customer)" });
    await page.selectOption("[name=status]", "Estimating");
    for (const [f, v] of [["street", "8 Synthetic Road"], ["municipality", "Ottawa"], ["province_state", "Ontario"],
                          ["postal_zip", "K1A 0A1"], ["country", "Canada"]]) await page.fill(`[name=${f}]`, v);
    await submit(page.locator("main form button[type=submit]"));
    const projectId = page.url().match(/projects\/(\d+)\/setup/)[1];

    // Construction information, saved, then found again after leaving the page (save and resume).
    await page.goto(`${base}/projects/${projectId}/construction`);
    await page.selectOption("[name=project_document_status]", "preliminary_construction_drawing");
    await page.selectOption("[name=measurement_system]", "imperial");
    await page.fill("[name=level_name_0]", "Main deck");
    await page.fill("[name=level_elevation_0]", "3");
    await page.selectOption("[name=member_role_0]", "beam");
    await page.fill("[name=member_size_0]", "2x10");
    await page.fill("[name=member_length_0]", "12");
    await page.selectOption("[name=member_length_unit_0]", "ft");
    await page.fill("[name=member_count_0]", "4");
    await page.selectOption("[name=support_kind_0]", "footing");
    await page.fill("[name=support_count_0]", "6");
    await submit(page.locator("button[name=form_action][value=save]"));
    assert.doesNotMatch(await page.locator("main").innerText(), /was not saved/);
    await page.goto(`${base}/`);
    await page.goto(`${base}/projects/${projectId}/construction`);
    assert.equal(await page.inputValue("[name=level_name_0]"), "Main deck");
    assert.equal(await page.inputValue("[name=member_size_0]"), "2x10");
    assert.equal(await page.inputValue("[name=member_count_0]"), "4");
    assert.equal(await page.inputValue("[name=measurement_system]"), "imperial");

    // A drawing on the project: upload, then it is listed with the project's plans.
    const planPdf = (await import("node:fs")).readFileSync(path.join(repoRoot, "tests/fixtures/e2e/synthetic-site-plan.pdf"));
    await page.goto(`${base}/projects/${projectId}/plans/upload`);
    await page.setInputFiles("[name=plan_file]", { name: "e2e-synthetic-site-plan.pdf", mimeType: "application/pdf", buffer: planPdf });
    await page.fill("[name=notes]", "Synthetic plan for the end-to-end walk");
    await submit(page.getByRole("button", { name: "Upload" }));
    await page.goto(`${base}/projects/${projectId}/plans`);
    assert.match(await page.locator("main").innerText(), /e2e-synthetic-site-plan\.pdf/);

    // Continue setup: the uploaded drawing counts, then scope (Foundation by our crew, Site work by our crew).
    await page.goto(`${base}/projects/${projectId}/setup`);
    assert.match(await page.locator("main").innerText(), /A current drawing is on the project\./);
    await submit(page.getByRole("link", { name: "Open scope of work" }));
    for (const work of ["Foundation", "Site work"]) {
      await page.selectOption("[name=work_element_template_id]", { label: work });
      await page.selectOption("[name=delivery]", "INTERNAL");
      await submit(page.getByRole("button", { name: "Add work" }));
    }
    await page.goto(`${base}/projects/${projectId}/setup`);
    const setup = await page.locator("main").innerText();
    assert.match(setup, /A governed footing calculation is available\./);
    assert.match(setup, /allowances or subcontract costs/); // Site work stays contractor-entered
    await submit(page.getByRole("link", { name: "Create estimate" }));
    await page.fill("[name=title]", "E2E footing estimate");
    await submit(page.locator("main form button[type=submit]"));
    const estimateId = page.url().match(/estimates\/(\d+)/)[1];

    // The company's own concrete cost (What we pay).
    await page.goto(`${base}/cost-library/new`);
    await page.fill("[name=code]", "E2E-CONC-25");
    await page.fill("[name=name]", "E2E ready-mix concrete 25 MPa");
    await page.selectOption("[name=category]", "Material");
    await page.fill("[name=unit]", "yd3");
    await page.fill("[name=unit_cost]", "250");
    await submit(page.locator("main form button[type=submit]"));

    // Continue setup now opens the footing quantities for this estimate.
    await page.goto(`${base}/projects/${projectId}/setup`);
    await submit(page.getByRole("link", { name: "Open footing quantities" }));
    const versionId = page.url().match(/versions\/(\d+)\/footing-quantities/)[1];
    const versionUrl = `${base}/estimates/${estimateId}/versions/${versionId}`;
    await page.goto(versionUrl);
    await page.fill('form[action$="sections/new"] [name=name]', "Foundation and site");
    await submit(page.locator('form[action$="sections/new"] button[type=submit]'));
    await page.goto(`${versionUrl}/footing-quantities`);
    // Two footings 20 ft × 2 ft × 12 in = 80 ft³ = 2.963 yd³; +5 % = 84 ft³ = 3.111 yd³.
    for (const [f, v] of [["footing_length_1", "20"], ["footing_width_1", "2"], ["footing_thickness_1", "12"],
                          ["footing_count_1", "2"], ["waste_percent", "5"]]) await page.fill(`#${f}`, v);
    await submit(page.locator("button[value=calculate]"));
    assert.match(await page.locator("[data-order-volume]").innerText(), /3\.111 yd³/);
    await submit(page.locator("button[value=review]"));
    assert.match(await page.locator("main").innerText(), /Concrete\s+3\.111\s+yd³/);
    await page.selectOption("[name=target]", { label: "E2E ready-mix concrete 25 MPa (yd3)" });
    await submit(page.getByRole("button", { name: "Add to estimate" }));
    assert.match(await flash(), /Quantity added to the estimate/);

    // Site work (decision 1): a contractor-entered allowance; no earthwork formula.
    await page.goto(versionUrl);
    const custom = page.locator("form").filter({ has: page.locator("select[name=line_type]") }).first();
    await custom.locator("[name=line_type]").selectOption("Allowance");
    await custom.locator("[name=code]").fill("E2E-SITE");
    await custom.locator("[name=description]").fill("Excavation and backfill allowance");
    await custom.locator("[name=quantity]").fill("1");
    await custom.locator("[name=unit]").fill("ls");
    await custom.locator("[name=unit_cost]").fill("1500");
    await submit(custom.getByRole("button", { name: "Add Line" }));

    // Labour hours (decision 2) at the saved company rate: 6 h × $65 = $390.
    await page.goto(`${versionUrl}/labour-hours`);
    assert.match(await page.locator("main").innerText(), /Company labour rate 65/);
    const concreteRow = page.locator("tr", { hasText: "E2E ready-mix concrete 25 MPa" });
    await concreteRow.locator("input[name^=hours_]").fill("6");
    await submit(page.getByRole("button", { name: "Save labour hours" }));
    assert.match(await flash(), /Labour saved at Company labour rate 65/);

    // Who supplies and who does the work: the suggestions are confirmed by the contractor.
    await page.goto(`${base}/projects/${projectId}/scope-delivery?version_id=${versionId}&estimate_id=${estimateId}`);
    await submit(page.getByRole("button", { name: "Approve All Scope Routing" }));

    // A proposal prepared now cannot be issued (decision 3).
    await page.goto(versionUrl);
    await submit(page.getByRole("link", { name: "Create Proposal" }));
    if (page.url().includes("/proposal-templates/new")) {
      await page.fill("[name=name]", "E2E standard proposal");
      await submit(page.getByRole("button", { name: "Save Template" }));
      await page.goto(versionUrl);
      await submit(page.getByRole("link", { name: "Create Proposal" }));
    }
    await submit(page.locator("main form button[type=submit]").last());
    const earlyId = page.url().match(/proposals\/(\d+)/)[1];
    // Joel, 17 Oct 2026: a proposal goes to the client only from a signed-off estimate, as a link.
    assert.match(await page.locator("[data-proposal-client-flow]").innerText(),
      /To send this proposal: Sign off the estimate first\. Approve the estimate's costing/);

    // Costing approval records the signed-in person (SEC-03); then the company pricing policy.
    await page.goto(versionUrl);
    assert.match(await page.locator("main").innerText(), /Approving as Office Test User/);
    await submit(page.locator('form[action$="approve-all-costing"] button[type=submit]'));
    assert.match(await flash(), /Costing approved/);
    await submit(page.locator('form[action$="apply-org-pricing"] button[type=submit]'));
    assert.match(await flash(), /pricing policy applied/i);
    // Direct cost 3.111 × 250 = 777.75 + 1,500 + 390 = 2,667.75; 15 % gross margin → ÷ 0.85 = 3,138.53;
    // HST 13 % = 408.01; customer total 3,546.54.
    const totals = await page.locator("main").innerText();
    assert.match(totals, /DIRECT COST BASIS\s+\$2667\.75/i);
    assert.match(totals, /PRE-TAX SELLING PRICE\s+\$3138\.53/i);
    assert.match(totals, /TAX \(13\.00%\)\s+\$408\.01/i);
    assert.match(totals, /CUSTOMER TOTAL\s+\$3546\.54/i);

    // Ben signs off the estimate: it locks, and a proposal is built from it with the current prices.
    await page.goto(versionUrl);
    await submit(page.getByRole("button", { name: "Sign off estimate" }));
    assert.match(await flash(), /Estimate signed off and locked/);
    const proposalUrl = page.url();
    assert.ok(!proposalUrl.endsWith(`/proposals/${earlyId}`), "a new proposal, not the early draft");
    // The early draft still carries its old prices and cannot be sent.
    await page.goto(`${base}/proposals/${earlyId}`);
    await page.fill("[data-proposal-send] [name=client_email]", "e2e.client@example.invalid");
    await submit(page.getByRole("button", { name: "Send proposal to client" }));
    assert.match(await flash(), /copied before the current pricing/);
    // The proposal goes to the client as a link.
    await page.goto(proposalUrl);
    await page.fill("[data-proposal-send] [name=client_email]", "e2e.client@example.invalid");
    await submit(page.getByRole("button", { name: "Send proposal to client" }));
    assert.match(await flash(), /Proposal sent to/);
    const clientLink = await page.locator("[data-proposal-link-url]").inputValue();
    const proposalText = await page.locator("main").innerText();
    assert.ok(proposalText.includes("3546.54") || proposalText.includes("3,546.54"), "proposal total");

    // The job's documents page now offers the customer proposal.
    await page.goto(`${base}/projects/${projectId}/workflow-documents`);
    const docs = await page.locator("main").innerText();
    assert.match(docs, /Client Construction Proposal/);
    assert.match(docs, /Internal Detailed Cost Breakdown/);

    // The customer document.
    const pdf = await ctx.request.get(`${proposalUrl}/pdf`);
    assert.equal(pdf.status(), 200);
    assert.equal(pdf.headers()["content-type"], "application/pdf");
    assert.equal((await pdf.body()).subarray(0, 5).toString(), "%PDF-");

    // The customer opens the link, ticks the box and accepts; the contract is generated for one office Send click.
    const customer = await browser.newContext();
    const customerPage = await customer.newPage();
    await customerPage.goto(clientLink.replace(/^https?:\/\/[^/]+/, base));
    await customerPage.check("[name=accept]");
    await customerPage.fill("[name=confirmed_name]", "E2E Synthetic Client");
    await customerPage.getByRole("button", { name: "Accept Proposal" }).click();
    await customerPage.waitForLoadState();
    assert.match(await customerPage.locator("body").innerText(), /Proposal accepted/);
    await customer.close();
    await page.goto(proposalUrl);
    assert.match(await page.locator("[data-proposal-client-flow]").innerText(), /Accepted by E2E Synthetic Client/);
    // The sign-off already locked the estimate, so the hub shows the committed baseline at once.
    await page.goto(`${base}/projects/${projectId}`);
    assert.equal(await page.locator("[data-lock-baseline]").count(), 0);
    let hub = await page.locator("main").innerText();
    assert.match(hub, /ORIGINAL ESTIMATED DIRECT COST\s+\$2667\.75/i);
    assert.match(hub, /ORIGINAL ESTIMATED PRE-TAX SELLING PRICE\s+\$3138\.53/i);
    assert.match(hub, /ORIGINAL ESTIMATED GM\s+15\.00%/i);

    // Project work from the contractor's labour hours, then dates, time and actual cost.
    await submit(page.getByRole("button", { name: "Build project work" }));
    assert.match(await page.locator("main").innerText(), /Current authorized labour: 6\.00/);
    const today = new Date();
    const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    const later = new Date(today.getTime() + 2 * 86400000);
    await page.goto(`${base}/schedule/items/new?project_id=${projectId}&next=hub`);
    await page.selectOption("[name=project_work_element_id]", { label: "Foundation and site" });
    await page.selectOption("[name=project_work_activity_id]", { index: 1 });
    await page.fill("[name=scheduled_start]", iso(today));
    await page.fill("[name=scheduled_end]", iso(later));
    await page.fill("[name=element_scheduled_start]", iso(today));
    await page.fill("[name=element_scheduled_end]", iso(later));
    await page.check("[name=confirm_element_adjustment]");
    await submit(page.getByRole("button", { name: "Set dates" }));
    assert.doesNotMatch(await flash(), /Schedule the work item first/);
    await page.goto(`${base}/`);
    assert.match(await page.locator(".home-briefing").innerText(), /E2E Synthetic Footing Job/);
    await submit(page.locator("a.home-calendar"));
    assert.match(await page.locator("main").innerText(), /E2E Synthetic Footing Job|Foundation and site/);

    await page.goto(`${base}/time/new?project_id=${projectId}&next=hub`);
    await page.selectOption("[name=project_work_element_id]", { label: "Foundation and site" });
    await page.selectOption("[name=project_work_activity_id]", { index: 1 });
    await page.fill("[name=hours]", "4");
    await submit(page.getByRole("button", { name: "Send time" }));
    await page.goto(`${base}/projects/${projectId}`);
    const actual = page.locator(`form[action="/projects/${projectId}/direct-cost-actuals"]`);
    await actual.locator("[name=cost_class]").selectOption("material");
    await actual.locator("[name=amount]").fill("800");
    await actual.locator("[name=incurred_on]").fill(iso(today));
    await submit(actual.locator("button[type=submit]"));

    // A change order the customer approved: $600 more, before tax.
    await page.goto(`${base}/project-controls/change-orders/new?project_id=${projectId}&next=hub`);
    await page.fill("[name=title]", "E2E extra footing step");
    await page.fill("[name=tax_percent]", "13");
    await page.fill("[name=description]", "Customer asked for a step in the footing");
    await submit(page.getByRole("button", { name: "Create Change Order" }));
    const coUrl = page.url().split("?")[0];
    await page.goto(`${coUrl}?tab=items`);
    await page.fill("[name=description]", "Footing step, formed and placed");
    await page.fill("[name=unit_price]", "600");
    await submit(page.getByRole("button", { name: "Add Item" }));
    await page.locator('form[action$="/status"] select[name=status]').selectOption("Approved");
    await submit(page.locator('form[action$="/status"] button[type=submit]'));
    await page.goto(`${base}/projects/${projectId}`);
    hub = await page.locator("main").innerText();
    assert.match(hub, /APPROVED\/INVOICED CO REVENUE DELTA\s+\$600\.00/i);
    assert.match(hub, /ACTUAL DIRECT COST TO DATE\s+\$800\.00/i);
    assert.match(hub, /Waiting for approval: 4\.00/);

    // Closeout: a punch list item for the change order, completed, then the project is closed.
    const punch = page.locator(`form[action="/projects/${projectId}/punch-list"]`);
    await punch.locator("[name=description]").fill("Patch the footing step corner");
    await punch.locator("[name=work_source_type]").selectOption("CHANGE_ORDER");
    await punch.locator("[name=source_change_order_id]").selectOption({ index: 1 });
    await submit(punch.getByRole("button", { name: "Add Punch List Item" }));
    assert.match(await flash(), /Punch List item added/);
    await submit(page.locator(`form[action^="/projects/${projectId}/punch-list/"][action$="/complete"] button`).first());
    assert.match(await flash(), /marked complete/);
    await page.goto(`${base}/projects/${projectId}/close`);
    await submit(page.locator(`form[action="/projects/${projectId}/close"] button[type=submit]`));
    const closed = await flash();
    assert.ok(/closed/i.test(closed), closed);

    assert.deepEqual(pageErrors, []);
    assert.equal(money("$3,546.54"), 3546.54);
  } finally {
    await browser?.close();
    office.child.kill();
  }
});
