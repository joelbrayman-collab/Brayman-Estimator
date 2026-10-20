// V1 internal acceptance: one synthetic job through its whole life, in a real browser, against a
// local office whose database was built by the real migrations (tests/e2e_office_server.py).
// Ben (office) estimates and issues a proposal → the customer accepts on the link → the contract is
// generated, sent, signed by the customer and countersigned → Ben schedules the work and assigns
// Kevin's crew → concrete request, supplier quote, purchase order and agreed delivery (Supplier Hub)
// → Kevin (field, 390 px phone) sees the work and delivery on Today / Week, records time and an
// observation → Ben approves the time → change order → punch list → project closed.
// Every transition is checked where it should show up. Synthetic data only.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

const repoRoot = path.resolve(fileURLToPath(new URL("../..", import.meta.url)));
const { chromium } = await import(
  pathToFileURL(path.join(repoRoot, "calculation-engines/concrete-slab-1.0.0/node_modules/playwright/index.mjs")).href
);
const python = process.env.E2E_PYTHON || path.join(repoRoot, "venv/bin/python");
const exe = process.env.E2E_BROWSER_EXECUTABLE;

const OFFICE = ["office@example.com", "office-test-password"];
const KEVIN = ["kevin.field@example.invalid", "field-test-password", "Kevin Field (synthetic crew)"];
const CLIENT = "E2E Lifecycle Client (not a customer)";
const JOB = "E2E Lifecycle Footing Job (not a customer)";
const SUPPLIER = "E2E Synthetic Concrete Supply";
const DANA = ["dana.dispatch@example.invalid", "Dana Dispatch (synthetic)", "Synthetic-supplier-pass-1"];

function freePort() {
  return new Promise((resolve, reject) => {
    const s = net.createServer();
    s.listen(0, "127.0.0.1", () => { const p = s.address().port; s.close((e) => (e ? reject(e) : resolve(p))); });
  });
}

function startOffice(port, mailRoot) {
  const child = spawn(python, [path.join(repoRoot, "tests/e2e_office_server.py")], {
    cwd: repoRoot,
    env: { ...process.env, E2E_OFFICE_PORT: String(port), E2E_LIFECYCLE: "1", E2E_MAIL_CAPTURE_ROOT: mailRoot },
    stdio: ["ignore", "pipe", "pipe"] });
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
  return { child, ready, log: () => out };
}

// Follow a link the way a person does (and fail if it is not there).
async function submitLink(who, locator) {
  await locator.waitFor();
  await who.submit(locator);
}

const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

// One person's browser: a context with page-error capture and the small helpers every step uses.
async function person(browser, base, viewport, pageErrors, label) {
  const ctx = await browser.newContext({ viewport });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => pageErrors.push(`${label}: ${e.message}`));
  page.on("response", (r) => { if (r.status() >= 500) pageErrors.push(`${label}: ${r.status()} ${r.url()}`); });
  const p = {
    ctx, page,
    flash: async () => (await page.locator(".flash, .alert, .field-flash, [role=alert]").filter({ visible: true }).allInnerTexts()).join(" | "),
    main: async () => page.locator("main").first().innerText(),
    body: async () => page.locator("body").innerText(),
    go: async (url) => { await page.goto(url.startsWith("http") ? url : `${base}${url}`); await page.waitForLoadState(); },
    submit: async (locator) => { await Promise.all([page.waitForLoadState(), locator.click()]); await page.waitForLoadState(); },
    noSideways: async (what) => {
      const overflow = await page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth");
      assert.ok(overflow <= 1, `${what} scrolls sideways on the phone (${overflow}px)`);
    },
    signIn: async (email, password, loginPath = "/login") => {
      await page.goto(`${base}${loginPath}`);
      await page.fill("#email, [name=email]", email);
      await page.fill("#password, [name=password]", password);
      await Promise.all([page.waitForLoadState(), page.locator("main form button[type=submit], form button[type=submit]").first().click()]);
      await page.waitForLoadState();
    },
  };
  return p;
}

test("one synthetic job from estimate to a closed project, office, customer, supplier and field", { timeout: 900000 }, async () => {
  const mailRoot = fs.mkdtempSync(path.join(os.tmpdir(), "e2e-lifecycle-mail-"));
  const port = process.env.E2E_BASE ? null : await freePort();
  const office = process.env.E2E_BASE
    ? { ready: Promise.resolve(), child: { kill() {} }, log: () => "" }
    : startOffice(port, mailRoot);
  const mailDir = process.env.E2E_MAIL_CAPTURE_ROOT || mailRoot;
  const base = process.env.E2E_BASE || `http://127.0.0.1:${port}`;
  const pageErrors = [];
  let browser;
  let ben;
  try {
    await office.ready;
    browser = await chromium.launch(exe ? { executablePath: exe, headless: true } : { channel: "chrome", headless: true });
    ben = await person(browser, base, { width: 1280, height: 900 }, pageErrors, "office");
    const { page } = ben;
    const today = new Date();
    const inDays = (n) => new Date(today.getTime() + n * 86400000);

    // ---------------------------------------------------------------- 1. estimate → issued proposal
    // (The estimating steps are proven figure by figure in contractor_workflow.mjs; here they only
    // bring the job to an issued proposal.)
    await ben.signIn(...OFFICE);
    await ben.go("/clients/new");
    await page.fill("[name=name]", CLIENT);
    await ben.submit(page.locator("main form button[type=submit]"));
    await ben.go("/projects/new");
    await page.fill("[name=name]", JOB);
    await page.selectOption("[name=client_id]", { label: CLIENT });
    await page.selectOption("[name=status]", "Estimating");
    for (const [f, v] of [["street", "12 Synthetic Concession"], ["municipality", "Merrickville"], ["province_state", "Ontario"],
                          ["postal_zip", "K0G 1N0"], ["country", "Canada"]]) await page.fill(`[name=${f}]`, v);
    await ben.submit(page.locator("main form button[type=submit]"));
    const projectId = page.url().match(/projects\/(\d+)\/setup/)[1];
    const hubUrl = `/projects/${projectId}`;
    await ben.go(`/projects/${projectId}/scope`);
    await page.selectOption("[name=work_element_template_id]", { label: "Foundation" });
    await page.selectOption("[name=delivery]", "INTERNAL");
    await ben.submit(page.getByRole("button", { name: "Add work" }));
    await ben.go(`/projects/${projectId}/plans/upload`);
    await page.setInputFiles("[name=plan_file]", { name: "e2e-lifecycle-site-plan.pdf", mimeType: "application/pdf",
      buffer: fs.readFileSync(path.join(repoRoot, "tests/fixtures/e2e/synthetic-site-plan.pdf")) });
    await ben.submit(page.getByRole("button", { name: "Upload" }));
    await ben.go(`/projects/${projectId}/setup`);
    await ben.submit(page.getByRole("link", { name: "Create estimate" }));
    await page.fill("[name=title]", "E2E lifecycle estimate");
    await ben.submit(page.locator("main form button[type=submit]"));
    const estimateId = page.url().match(/estimates\/(\d+)/)[1];
    await ben.go("/cost-library/new");
    await page.fill("[name=code]", "E2E-LC-CONC");
    await page.fill("[name=name]", "E2E lifecycle ready-mix 25 MPa");
    await page.selectOption("[name=category]", "Material");
    await page.fill("[name=unit]", "yd3");
    await page.fill("[name=unit_cost]", "250");
    await ben.submit(page.locator("main form button[type=submit]"));
    await ben.go(`/projects/${projectId}/setup`);
    await ben.submit(page.getByRole("link", { name: "Open footing quantities" }));
    const versionId = page.url().match(/versions\/(\d+)\/footing-quantities/)[1];
    const versionUrl = `/estimates/${estimateId}/versions/${versionId}`;
    await ben.go(versionUrl);
    await page.fill('form[action$="sections/new"] [name=name]', "Foundation");
    await ben.submit(page.locator('form[action$="sections/new"] button[type=submit]'));
    await ben.go(`${versionUrl}/footing-quantities`);
    for (const [f, v] of [["footing_length_1", "20"], ["footing_width_1", "2"], ["footing_thickness_1", "12"],
                          ["footing_count_1", "2"], ["waste_percent", "5"]]) await page.fill(`#${f}`, v);
    await ben.submit(page.locator("button[value=calculate]"));
    await ben.submit(page.locator("button[value=review]"));
    await page.selectOption("[name=target]", { label: "E2E lifecycle ready-mix 25 MPa (yd3)" });
    await ben.submit(page.getByRole("button", { name: "Add to estimate" }));
    await ben.go(`${versionUrl}/labour-hours`);
    await page.locator("tr", { hasText: "E2E lifecycle ready-mix 25 MPa" }).locator("input[name^=hours_]").fill("6");
    await ben.submit(page.getByRole("button", { name: "Save labour hours" }));
    await ben.go(`/projects/${projectId}/scope-delivery?version_id=${versionId}&estimate_id=${estimateId}`);
    await ben.submit(page.getByRole("button", { name: "Approve All Scope Routing" }));
    await ben.go("/proposal-templates/new");
    await page.fill("[name=name]", "E2E lifecycle proposal");
    await ben.submit(page.getByRole("button", { name: "Save Template" }));
    await ben.go(versionUrl);
    await ben.submit(page.locator('form[action$="approve-all-costing"] button[type=submit]'));
    await ben.submit(page.locator('form[action$="apply-org-pricing"] button[type=submit]'));
    await ben.go(versionUrl);
    await ben.submit(page.getByRole("button", { name: "Sign off estimate" }));
    assert.match(await ben.flash(), /Estimate signed off and locked/);
    const proposalUrl = page.url();
    const proposalId = proposalUrl.match(/proposals\/(\d+)/)[1];
    await page.fill("[data-proposal-send] [name=client_email]", "e2e.lifecycle.client@example.invalid");
    await ben.submit(page.getByRole("button", { name: "Send proposal to client" }));
    assert.match(await ben.flash(), /Proposal sent to/);
    const proposalLink = (await page.locator("[data-proposal-link-url]").inputValue()).replace(/^https?:\/\/[^/]+/, base);


    // ---------------------------------------------------------------- 2. the customer accepts on the link
    const customer = await person(browser, base, { width: 390, height: 844 }, pageErrors, "customer");
    await customer.go(proposalLink);
    await customer.noSideways("the proposal link");
    await customer.page.check("[name=accept]");
    await customer.page.fill("[name=confirmed_name]", "E2E Lifecycle Client");
    await customer.submit(customer.page.getByRole("button", { name: "Accept Proposal" }));
    assert.match(await customer.body(), /Proposal accepted/);
    await ben.go(proposalUrl);
    assert.match(await page.locator("[data-proposal-client-flow]").innerText(), /Accepted by E2E Lifecycle Client/);
    assert.match(await ben.main(), /STATUS\s+Accepted/i);
    assert.match(await ben.main(), /The contract was generated from this proposal/);
    await ben.go(hubUrl);
    assert.match(await page.locator("article", { hasText: "Related Proposals" }).innerText(), /PROP-\d{4}-\d{4} · Accepted/);

    // ---------------------------------------------------------------- 3. contract: sent, signed, countersigned
    await submitLink(ben, page.locator("#hub-contract-legal").getByRole("link", { name: "Review contract" }));
    const contractCard = page.locator("[id^=contract-snapshot-]").first();
    assert.match(await contractCard.innerText(), /Contract status Generated — not signed/);
    assert.match(await contractCard.innerText(), /Contract amount 1552\.42/);
    const sendContract = page.locator('form[action*="/send-for-signature"]');
    assert.equal(await sendContract.locator("[name=signer_name]").inputValue(), "E2E Lifecycle Client");
    await sendContract.locator("[name=signer_email]").fill("e2e.lifecycle.client@example.invalid");
    await ben.submit(sendContract.getByRole("button", { name: "Send contract for signature" }));
    assert.match(await ben.flash(), /Invitation issued/);
    const signLink = (await page.locator("[data-signing-invitation]").inputValue()).replace(/^https?:\/\/[^/]+/, base);
    await customer.go(signLink);
    await customer.noSideways("the contract signing page");
    await customer.page.check("[name=consent_accepted]");
    await customer.page.fill("[name=confirmed_signer_name]", "E2E Lifecycle Client");
    await customer.submit(customer.page.getByRole("button", { name: "Sign & Accept" }));
    assert.match(await customer.body(), /You have signed this document/);
    await ben.go(`/projects/${projectId}/contract`);
    assert.match(await page.locator("[data-signing-overlay]").innerText(), /SIGNED/);
    await ben.submit(page.getByRole("button", { name: "Countersign" }));
    assert.match(await ben.flash(), /Countersigned/);
    assert.match(await page.locator("[id^=contract-snapshot-]").first().innerText(), /Contract status Signed — executed/);
    const signed = await ben.ctx.request.get(`${base}${await page.getByRole("link", { name: "Download signed contract" }).getAttribute("href")}`);
    assert.equal(signed.status(), 200);
    assert.equal((await signed.body()).subarray(0, 5).toString(), "%PDF-");
    // The Project page tells Ben the contract is signed.
    await ben.go(hubUrl);
    assert.match(await page.locator("#hub-contract-legal").innerText(), /CTR-\d{4}-\d{4}\s*·\s*Signed — executed/);

    // ---------------------------------------------------------------- 4. schedule the work, assign Kevin's crew
    await ben.submit(page.getByRole("button", { name: "Build project work" }));
    assert.match(await ben.main(), /Current authorized labour: 6\.00/);
    await ben.go("/settings/crews/new");
    await page.fill("[name=name]", "E2E Footing Crew");
    await ben.submit(page.locator("main form button[type=submit]"));
    assert.match(await ben.flash(), /Crew saved/);
    await ben.submit(page.getByRole("link", { name: "E2E Footing Crew" }));
    await page.selectOption("[name=user_id]", { label: KEVIN[2] });
    await page.fill("[name=effective_from]", iso(inDays(-1)));
    await ben.submit(page.locator('form[action$="/members"] button[type=submit]'));
    assert.match(await ben.flash(), /Crew dates saved/);
    await ben.go(hubUrl);
    await submitLink(ben, page.locator("#hub-schedule").getByRole("link", { name: "Set dates" }).last());
    await page.selectOption("[name=project_work_element_id]", { label: "Foundation" });
    await page.selectOption("[name=project_work_activity_id]", { index: 1 });
    for (const f of ["scheduled_start", "element_scheduled_start"]) await page.fill(`[name=${f}]`, iso(today));
    for (const f of ["scheduled_end", "element_scheduled_end"]) await page.fill(`[name=${f}]`, iso(inDays(2)));
    await page.check("[name=confirm_element_adjustment]");
    await ben.submit(page.getByRole("button", { name: "Set dates" }));
    assert.match(await ben.flash(), /Schedule saved/);
    const labourRow = page.locator("#hub-schedule tr", { hasText: "Labour — E2E lifecycle ready-mix" });
    await submitLink(ben, labourRow.getByRole("link", { name: "Edit dates" }));
    await page.selectOption("[name=crew_id]", { label: "E2E Footing Crew" });
    await ben.submit(page.locator('form[action$="/assignments"] button[type=submit]'));
    assert.match(await ben.flash(), /Assignment saved/);
    assert.ok(page.url().includes(hubUrl), "assignment returns to the Project page");
    assert.match(await labourRow.innerText(), new RegExp(`${iso(today)}\\s+${iso(inDays(2))}\\s+E2E Footing Crew`));
    // Company Calendar (from the Project page) and Home show the scheduled job.
    await submitLink(ben, page.locator("#hub-schedule").getByRole("link", { name: "Company Calendar" }));
    await ben.go(`/schedule?project_id=${projectId}&view=week`);
    assert.match(await ben.main(), /Foundation/);
    await ben.go("/");
    assert.match(await page.locator(".home-briefing").innerText(), new RegExp(`${JOB.replace(/[()]/g, "\\$&")} — Foundation`));

    // ---------------------------------------------------------------- 5. Supplier Hub: concrete request → PO → agreed delivery
    await ben.go("/suppliers");
    const addSupplier = page.locator("[data-add-supplier]");
    await addSupplier.locator("[name=legal_name]").fill(SUPPLIER);
    await addSupplier.locator("[name=location_name]").fill("Synthetic plant");
    await ben.submit(addSupplier.locator("button"));
    assert.match(await ben.flash(), new RegExp(`${SUPPLIER} added`));
    const addSignIn = page.locator("[data-add-supplier-user]").first();
    await addSignIn.locator("[name=display_name]").fill(DANA[1]);
    await addSignIn.locator("[name=email]").fill(DANA[0]);
    await ben.submit(addSignIn.locator("button"));
    assert.match(await ben.flash(), /can now sign in to the Supplier Hub/);
    // Dana chooses her password from the captured email, then signs in to the Supplier Hub.
    const resetMail = fs.readdirSync(mailDir).filter((n) => n.includes("PASSWORD_RESET")).sort().pop();
    const resetUrl = fs.readFileSync(path.join(mailDir, resetMail), "utf8").match(/https?:\/\/\S+\/reset-password\/\S+/)[0]
      .replace(/^https?:\/\/[^/]+/, base);
    const dana = await person(browser, base, { width: 1280, height: 900 }, pageErrors, "supplier");
    await dana.go(resetUrl);
    await dana.page.fill("[name=password]", DANA[2]);
    await dana.page.fill("[name=confirm_password]", DANA[2]);
    await dana.submit(dana.page.locator("form button[type=submit]"));
    assert.match(await dana.body(), /Your password has been reset/);
    await dana.signIn(DANA[0], DANA[2], "/supplier/login");
    assert.match(dana.page.url(), /\/supplier\/\d+\/$/);

    // Ben reaches the job's supplier requests from the Project page and sends concrete on its own request.
    await ben.go(hubUrl);
    await submitLink(ben, page.locator("#hub-purchasing").getByRole("link", { name: /Supplier requests/ }));
    assert.ok(page.url().endsWith(`/projects/${projectId}/supplier-requests`), page.url());
    const concrete = page.locator("[data-new-concrete]");
    await concrete.locator("[name=volume_m3]").fill("2.4");
    await concrete.locator("[name=strength_mpa]").fill("25");
    await concrete.locator("[name=delivery_date]").fill(iso(inDays(1)));
    await concrete.locator("[name=delivery_window]").fill("7:00–9:00");
    await concrete.locator("[name=contractor_supplier_account_id]").selectOption({ label: SUPPLIER });
    await ben.submit(concrete.locator("button"));
    const sent = (await ben.flash()).match(/Concrete request (CON-\d{4}-\d{4}) sent to .+ \((SRQ-\d{4}-\d{4})\)/);
    assert.ok(sent, await ben.flash());
    const requestNo = sent[2];
    // Dana quotes it.
    await dana.go(dana.page.url());
    assert.match(await dana.main(), new RegExp(`${requestNo} · Brayman Construction · needed ${iso(inDays(1))}`));
    await dana.submit(dana.page.getByRole("link", { name: requestNo }).first());
    const quote = dana.page.locator("[data-concrete-quote]");
    await quote.locator("[name=quote_number]").fill("SYN-Q-1");
    await quote.locator("[name=price_per_m3]").fill("200");
    await quote.locator("[name=valid_until]").fill(iso(inDays(14)));
    await dana.submit(quote.getByRole("button", { name: "Return quote" }));
    assert.match(await dana.flash(), /Quote returned to the contractor/);
    // Ben approves the quote and places the order, following the scheduled footing work.
    await ben.go(`/projects/${projectId}/supplier-requests`);
    assert.match(await page.locator("[data-concrete-quote-returned]").innerText(), /2\.40 m³ at \$200 = \$480\.00/);
    await ben.submit(page.locator("[data-approve-quote] button"));
    assert.match(await ben.flash(), /Concrete quote approved/);
    const order = page.locator("[data-place-order]");
    await order.locator("[name=delivery_date]").fill(iso(inDays(1)));
    await order.locator("[name=delivery_window]").fill("7:00–9:00");
    await order.locator("[name=schedule_item_id]").selectOption({ label: `Labour — E2E lifecycle ready-mix 25 MPa (${iso(today)} – ${iso(inDays(2))})` });
    await order.locator("[name=site_contact]").fill(KEVIN[2]);
    // Supplier Native Signing (FG-041): Ben signs the order; the store signs when it confirms.
    await order.locator("[name=sign_consent]").check();
    await order.locator("[name=signer_name]").fill("Ben Synthetic");
    await ben.submit(order.getByRole("button", { name: "Sign and place order" }));
    const po = (await ben.flash()).match(/Purchase order (PO-\d{4}-\d{4}) signed and sent/)[1];
    assert.match(await page.locator("[data-po]").innerText(), /Waiting for the supplier to confirm/);
    // Dana confirms: the delivery is agreed.
    await dana.page.reload();
    assert.match(await dana.main(), new RegExp(`Purchase order ${po}`));
    const confirm = dana.page.locator("[data-confirm-order]");
    await confirm.locator("[name=sign_consent]").check();
    await confirm.locator("[name=signer_name]").fill("Dana Synthetic");
    await dana.submit(confirm.getByRole("button", { name: "Sign and confirm order" }));
    assert.match(await dana.flash(), new RegExp(`Order ${po} signed and confirmed`));
    await ben.go(`/projects/${projectId}/supplier-requests`);
    assert.match(await page.locator("[data-po]").innerText(), new RegExp(`agreed delivery ${iso(inDays(1))} 7:00–9:00\\. The order is agreed`));
    // The purchase order shows on the Project page, the deliveries list and the Company Calendar.
    await ben.go(hubUrl);
    assert.match(await page.locator("#hub-purchasing").innerText(), new RegExp(`${po}[\\s\\S]*${SUPPLIER}[\\s\\S]*\\$480\\.00[\\s\\S]*Confirmed[\\s\\S]*${iso(inDays(1))}`));
    await ben.go("/deliveries");
    assert.match(await ben.main(), new RegExp(`${po}\\s+Agreed`));
    await ben.go(`/schedule?project_id=${projectId}&view=week&date=${iso(inDays(1))}`);
    assert.match(await ben.main(), new RegExp(`Concrete · ${SUPPLIER} · ${JOB.replace(/[()]/g, "\\$&")} · 7:00–9:00`));

    // ---------------------------------------------------------------- 6. Kevin on a phone: his work, time and an observation
    const kevin = await person(browser, base, { width: 390, height: 844 }, pageErrors, "field");
    await kevin.signIn(KEVIN[0], KEVIN[1]);
    await kevin.go("/field/today");
    await kevin.noSideways("Field Today");
    let todayText = await kevin.main();
    assert.match(todayText, /My Work — Kevin/);
    assert.match(todayText, /Foundation — Labour — E2E lifecycle ready-mix 25 MPa\s+E2E Footing Crew/);
    assert.match(todayText, /12 Synthetic Concession/);
    await kevin.go("/field/week");
    await kevin.noSideways("Field Week");
    assert.match(await kevin.main(), new RegExp(`Delivery Concrete · ${SUPPLIER} · .+ · 7:00–9:00 · Agreed`));
    await kevin.go("/field/today");
    await kevin.submit(kevin.page.getByRole("link", { name: "Enter time" }).first());
    await kevin.noSideways("Field Time");
    await kevin.page.locator(".field-time-recent-btn").first().click(); // Scheduled today
    await kevin.page.fill("[name=hours]", "4");
    await kevin.page.fill("[name=worker_note]", "Formed both footings (synthetic)");
    await kevin.submit(kevin.page.locator("#field-time-form button[type=submit]"));
    assert.match(await kevin.flash(), /Time sent for approval/);
    await kevin.noSideways("Field My time");
    assert.match(await kevin.main(), /Foundation — Labour — E2E lifecycle ready-mix 25 MPa\s+4\.00 hours/);
    await kevin.go("/field/today");
    await kevin.submit(kevin.page.getByRole("link", { name: "Capture", exact: true }));
    await kevin.noSideways("Field Capture");
    await kevin.page.fill("#field-text", "Footing forms checked before the pour (synthetic observation)");
    await kevin.page.click("#field-save");
    await kevin.page.locator("#field-feedback", { hasText: "Saved" }).waitFor();
    await kevin.go("/field/today");
    assert.match(await kevin.main(), /Recent observations[\s\S]*Footing forms checked before the pour/);
    // The customer asks Kevin for a step in the footing: extra work, recorded on site.
    await kevin.submit(kevin.page.getByRole("link", { name: "Extra work" }));
    await kevin.noSideways("Field Extra work");
    await kevin.page.fill("[name=description]", "Customer asked for a step in the footing (synthetic)");
    await kevin.page.selectOption("[name=project_work_element_id]", { label: "Foundation" });
    await kevin.submit(kevin.page.getByRole("button", { name: "Record extra work" }));
    assert.match(await kevin.flash(), /Extra work recorded/);

    // Ben sees Kevin's time and observation on the Project page and approves the time.
    await ben.go(hubUrl);
    assert.match(await page.locator("#hub-time").innerText(), /Waiting for approval: 4\.00/);
    const observations = page.locator("article", { has: page.getByRole("heading", { name: "Field Observations" }) });
    assert.match(await observations.innerText(), /Kevin Field \(synthetic crew\)\s+text\s+Current/i);
    await submitLink(ben, observations.locator("tbody a").first());
    assert.match(await ben.main(), /Footing forms checked before the pour \(synthetic observation\)/);
    await ben.go(hubUrl);
    await submitLink(ben, page.locator("#hub-time").getByRole("link", { name: "Review time" }));
    const timeRow = page.locator("tr", { hasText: "Formed both footings (synthetic)" });
    await timeRow.locator("input[type=checkbox]").check();
    await ben.submit(page.getByRole("button", { name: "Approve selected" }));
    await ben.go(hubUrl);
    assert.match(await page.locator("#hub-time").innerText(), /Approved hours: 4\.00 · Waiting for approval: 0\.00/);

    // ---------------------------------------------------------------- 7. change order from Kevin's extra work, signed by the customer
    await submitLink(ben, page.getByRole("link", { name: "Open project work" }));
    const extraRow = page.locator("tr", { hasText: "Customer asked for a step in the footing" });
    await ben.submit(extraRow.getByRole("button", { name: "Create change order" }));
    assert.match(await ben.flash(), /Change order created from extra work/);
    const coUrl = page.url().split("?")[0].split("#")[0];
    await submitLink(ben, page.getByRole("link", { name: "Edit" }).first());
    await page.fill("[name=tax_percent]", "13");
    await ben.submit(page.locator("main form button[type=submit]").last());
    await ben.go(`${coUrl}?tab=items`);
    await page.fill("[name=description]", "Footing step, formed and placed");
    await page.fill("[name=quantity]", "1");
    await page.fill("[name=unit]", "ls");
    await page.fill("[name=unit_price]", "600");
    await ben.submit(page.getByRole("button", { name: "Add Item" }));
    assert.match(await ben.main(), /GRAND TOTAL\s+\$678\.00/);
    await page.locator('form[action$="/status"] select[name=status]').selectOption("Approved");
    await ben.submit(page.locator('form[action$="/status"] button[type=submit]'));
    const coSend = page.locator('form[action$="/send-for-signature"]');
    await coSend.locator("[name=signer_name]").fill("E2E Lifecycle Client");
    await coSend.locator("[name=signer_email]").fill("e2e.lifecycle.client@example.invalid");
    await ben.submit(coSend.getByRole("button", { name: "Send for Signature" }));
    assert.match(await ben.flash(), /Invitation issued/);
    const coLink = (await page.locator("[data-signing-invitation]").inputValue()).replace(/^https?:\/\/[^/]+/, base);
    await customer.go(coLink);
    await customer.noSideways("the change-order signing page");
    await customer.page.check("[name=consent_accepted]");
    await customer.page.fill("[name=confirmed_signer_name]", "E2E Lifecycle Client");
    await customer.submit(customer.page.getByRole("button", { name: "Sign & Accept" }));
    assert.match(await customer.body(), /You have signed this document/);
    await ben.go(coUrl);
    await ben.submit(page.getByRole("button", { name: "Countersign" }));
    assert.match(await ben.flash(), /Countersigned/);
    assert.match(await ben.main(), /CUSTOMER SIGNATURE\s+(SIGNED|EXECUTED)/i);
    await ben.go(hubUrl);
    let hub = await ben.main();
    assert.match(hub, /APPROVED\/INVOICED CO REVENUE DELTA\s+\$600\.00/i);
    assert.match(hub, /Related Change Orders[\s\S]*Customer asked for a step in the footing/);

    // ---------------------------------------------------------------- 8. closeout: customer walkthrough → punch list → closed
    await ben.submit(page.locator(`form[action="/projects/${projectId}/final-walkthrough/invite"] button`));
    const walkLink = (await page.locator(".walkthrough-copy-link input").inputValue()).replace(/^https?:\/\/[^/]+/, base);
    await customer.go(walkLink);
    await customer.noSideways("the customer walkthrough");
    await customer.page.fill("#item-0", "Touch up the edge of the footing step");
    await customer.submit(customer.page.locator("#walkthrough-form button[type=submit]"));
    await ben.go(hubUrl);
    const walkItem = page.locator("#hub-final-walkthrough li", { hasText: "Touch up the edge of the footing step" });
    await walkItem.locator("[name=work_source_type]").selectOption("CHANGE_ORDER");
    await walkItem.locator("[name=source_change_order_id]").selectOption({ index: 1 });
    await ben.submit(walkItem.locator("button[type=submit]").first());
    assert.match(await ben.flash(), /punch list/i);
    assert.match(await page.locator("#hub-punch-list").innerText(), /Touch up the edge of the footing step/);
    await ben.submit(page.locator(`form[action^="/projects/${projectId}/punch-list/"][action$="/complete"] button`).first());
    assert.match(await ben.flash(), /marked complete/);
    await submitLink(ben, page.getByRole("link", { name: "Close Project" }));
    await ben.submit(page.locator(`form[action="/projects/${projectId}/close"] button[type=submit]`));
    assert.match(await ben.flash(), /closed/i);
    assert.match(await ben.main(), /This Project is closed\.[\s\S]*Closed\s+Reopen Project/);
    // Closed: Field no longer offers the job or its work.
    await kevin.go("/field/projects");
    assert.doesNotMatch(await kevin.main(), /E2E Lifecycle Footing Job/);
    await kevin.go("/field/today");
    assert.match(await kevin.main(), /Nothing is scheduled for you today\./);
    assert.deepEqual(pageErrors, []);
  } catch (error) {
    if (ben) console.error(`\nFAILED AT ${ben.page.url()}\n${(await ben.main().catch(() => "")).slice(0, 3000)}`);
    if (pageErrors.length) console.error("page errors:", pageErrors);
    console.error(office.log().slice(-4000));
    throw error;
  } finally {
    await browser?.close();
    office.child.kill();
    fs.rmSync(mailRoot, { recursive: true, force: true });
  }
});
