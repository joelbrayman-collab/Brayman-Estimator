// Release evidence for company Documents (31 Oct 2026), in a real browser against tests/documents_page_server.py
// (temporary database and document folder; synthetic owner, office member, Field-only crew member, subcontractor
// Acme Framing, supplier account, another organization). Synthetic data only.
//
// Checks: the office member opens Documents from the menu; uploads a WSIB clearance on the subcontractor; the
// suggested type is WSIB clearance and the expiry found in the file is offered to confirm; after Save the document
// page shows it confirmed, the inline PDF preview and history; What needs your attention lists "expires" with a link
// to that document; a renewal uploaded as a new version keeps version 1 in the history and the reminder goes away;
// the Company library search finds it; the Field-only crew member is sent to Field from every office Documents
// page and opens only their job's documents; phone width has no sideways scrolling; no 5xx.
// Run: EVIDENCE_REPO=$PWD EVIDENCE_EXECUTABLE=/path/to/chromium node --test tools/release/evidence_documents.mjs
import assert from "node:assert/strict";
import path from "node:path";
import { spawn } from "node:child_process";
import test, { after, before } from "node:test";
import { REPO, freePort, launch } from "./evidence_common.mjs";

const PHONE = { width: 390, height: 844 };
const DESK = { width: 1280, height: 900 };
let browser, server, base, facts;
const serverErrors = [];

before(async () => {
  const port = await freePort();
  server = spawn(path.join(REPO, "venv/bin/python"), [path.join(REPO, "tests/documents_page_server.py")], {
    cwd: REPO, env: { ...process.env, DOCUMENTS_PAGE_PORT: String(port) }, stdio: ["ignore", "pipe", "pipe"] });
  let out = "";
  server.stdout.on("data", (c) => (out += c)); server.stderr.on("data", (c) => (out += c));
  await new Promise((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("office did not start\n" + out)), 120000);
    const poll = () => {
      if (out.includes(`READY ${port}`)) { clearTimeout(t); return resolve(); }
      if (server.exitCode !== null) { clearTimeout(t); return reject(new Error("office exited\n" + out)); }
      setTimeout(poll, 100);
    };
    poll();
  });
  facts = JSON.parse(out.split("FACTS ")[1].split("\n")[0]);
  base = `http://127.0.0.1:${port}`;
  browser = await launch();
});
after(async () => {
  await browser?.close(); server?.kill();
  console.log(`DOCUMENTS SERVER_ERRORS=${serverErrors.length}`);
});

async function session(viewport = DESK) {
  const ctx = await browser.newContext({ viewport, ...(viewport.width < 500 ? { isMobile: true, hasTouch: true } : {}) });
  ctx.setDefaultTimeout(15000);
  const pg = await ctx.newPage();
  pg.on("response", (r) => { if (r.status() >= 500) serverErrors.push(`${r.status()} ${r.url()}`); });
  return { ctx, pg };
}
async function go(pg, url) {
  const r = await pg.goto(`${base}${url}`);
  await pg.waitForLoadState();
  return r;
}
async function submit(pg, locator) {
  await Promise.all([pg.waitForNavigation(), locator.click()]);
  await pg.waitForLoadState();
}
async function signIn(pg, [email, password]) {
  await go(pg, "/login");
  await pg.fill("#email", email);
  await pg.fill("#password", password);
  await submit(pg, pg.locator("button[type=submit]"));
}
const pathOf = (pg) => new URL(pg.url()).pathname;
async function noSideways(pg, label) {
  const over = await pg.evaluate("document.documentElement.scrollWidth - window.innerWidth");
  assert.ok(over <= 1, `${label}: page scrolls sideways by ${over}px`);
}

test("office: upload a WSIB clearance, confirm its expiry, see it in attention, renew it", async () => {
  const { ctx, pg } = await session();
  await signIn(pg, facts.staff);
  await go(pg, "/");
  // Task-First navigation (31 Oct 2026, merged with Documents): the sidebar has six primary items and More; the
  // company library's Documents link is on the More page. Same check: one step from the menu.
  await submit(pg, pg.locator('a[href="/more"]').first());
  const menu = pg.locator('main a[href="/documents"]').first();
  assert.equal(await menu.count(), 1, "Documents is in the menu (More)");
  await submit(pg, menu);
  assert.equal(pathOf(pg), "/documents");
  assert.equal(await pg.locator("[data-documents-library]").count(), 1);

  await go(pg, `/subcontractors/${facts.sub_id}/documents`);
  await submit(pg, pg.locator("[data-documents-upload]"));
  await pg.setInputFiles("[data-documents-file]", facts.wsib_pdf);
  await submit(pg, pg.locator("[data-documents-upload-form] button[type=submit]"));
  assert.equal(await pg.locator('[data-documents-suggested="WSIB_CLEARANCE"]').count(), 1, "type suggested");
  assert.equal(await pg.locator("[data-documents-type]").inputValue(), "WSIB_CLEARANCE");
  const expiry = pg.locator(`input[name=confirm_date][value="EXPIRES|${facts.expires}"]`);
  assert.equal(await expiry.count(), 1, "the expiry date found in the file is offered");
  await expiry.check();
  await submit(pg, pg.locator("[data-documents-save]"));
  assert.match(pathOf(pg), /^\/documents\/[0-9a-f]{32}$/);
  const documentPath = pathOf(pg);
  assert.equal(await pg.locator('[data-confirmed-date="EXPIRES"]').count(), 1, "expiry confirmed");
  assert.equal(await pg.locator('[data-document-preview="pdf"]').count(), 1, "PDF shown inline");
  const pdf = await pg.request.get(`${base}${documentPath}/file`);
  assert.equal(pdf.status(), 200); assert.equal(pdf.headers()["content-type"], "application/pdf");

  await go(pg, "/operations/attention");
  const item = pg.locator(`[data-attention-kind="documents"] a[href="${documentPath}"]`).first();
  assert.equal(await item.count(), 1, "What needs your attention links to the document");
  assert.match(await pg.locator('[data-attention-kind="documents"]').first().innerText(), /expires/);

  await go(pg, documentPath);
  await pg.setInputFiles("[data-document-new-version] input[type=file]", facts.renewal_pdf);
  await pg.fill("[data-document-new-version] input[name=note]", "Renewed (synthetic)");
  await submit(pg, pg.locator("[data-document-new-version] button[type=submit]"));
  assert.equal(await pg.locator('[data-version="1"]').count(), 1, "version 1 kept");
  assert.equal(await pg.locator('[data-version="2"]').count(), 1);
  await go(pg, "/operations/attention");
  assert.equal(await pg.locator(`[data-attention-kind="documents"] a[href="${documentPath}"]`).count(), 0,
    "the renewal starts its own dates: the old reminder is gone");

  await go(pg, "/documents?q=clearance");
  assert.ok(await pg.locator(`a[href="${documentPath}"]`).count() >= 1, "search finds it");
  await ctx.close();
});

test("phone: the library and a document page do not scroll sideways", async () => {
  const { ctx, pg } = await session(PHONE);
  await signIn(pg, facts.staff);
  await go(pg, "/documents");
  await noSideways(pg, "library");
  await go(pg, `/subcontractors/${facts.sub_id}/documents`);
  await noSideways(pg, "subcontractor documents");
  await go(pg, "/equipment");
  await noSideways(pg, "equipment");
  await ctx.close();
});

test("field-only crew: office Documents pages send them to Field; their job's documents open", async () => {
  const { ctx, pg } = await session(PHONE);
  await signIn(pg, facts.crew);
  for (const url of ["/documents", `/subcontractors/${facts.sub_id}/documents`, `/projects/${facts.project_id}/documents`,
                     "/equipment", "/documents/upload"]) {
    await go(pg, url);
    assert.equal(pathOf(pg), "/field/today", `${url} redirects to Field`);
  }
  await go(pg, `/field/projects/${facts.project_id}`);
  assert.equal(await pg.locator("[data-field-documents-link]").count(), 1);
  await submit(pg, pg.locator("[data-field-documents-link]"));
  assert.equal(pathOf(pg), `/field-documents/projects/${facts.project_id}`);
  await noSideways(pg, "job documents");
  await ctx.close();
});

test("no server errors", () => {
  assert.deepEqual(serverErrors, []);
});
