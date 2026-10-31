// Release-walk helpers for the estimate-to-project release (Joel, 30 Oct 2026). Kept apart from evidence_common.mjs,
// whose bytes are the proven helper (tests/test_release_tools.py).
// Gate 3 (Joel, 30 Oct 2026, decision 6): before the customer accepts, nothing is ordered until a person with
// Company Management or the owner records an Early Procurement Exception for that request. The walk records it on
// the page, as the office would, then the order form appears.
export async function recordEarlyException(pg, shareId = null, exposure = "5000") {
  const pending = pg.locator(shareId === null ? "[data-early-exception]" : `[data-early-exception="${shareId}"]`);
  if (await pending.count() === 0) return false;
  const form = pending.first();
  shareId = await form.getAttribute("data-early-exception");
  await form.locator("[name=reason]").fill("Supplier lead time before the customer signs (synthetic)");
  await form.locator("[name=financial_exposure]").fill(exposure);
  await form.locator("[name=approving_authority]").fill("Joel Brayman, owner (synthetic)");
  await Promise.all([pg.waitForLoadState(), form.locator("button[type=submit]").click()]);
  await pg.waitForLoadState();
  const text = (await pg.locator(".flash, .flash-stack .alert").allInnerTexts()).join(" | ");
  if (!/Early Procurement Exception #\d+ recorded/.test(text)) throw new Error(`the exception was not recorded: ${text}`);
  if (await pg.locator(`[data-place-order="${shareId}"]`).count() !== 1) throw new Error("the order form did not appear");
  return true;
}

// Projects list rows read "BC-YYYY-NNNN— Name" since the Brayman Project # (Joel, 30 Oct 2026): count the rows whose
// name is exactly this project's name, with or without its number.
export async function projectRows(pg, name) {
  return pg.locator(".projects-row-name").evaluateAll((rows, n) =>
    rows.filter((r) => r.textContent.replace(/^\s*[A-Z0-9-]+-\d{4}-\d{4}\s*—\s*/, "").trim() === n).length, name);
}
