# QuickBooks Integration — Architecture

| Attribute | Value |
|-----------|--------|
| Status | **Intended V1 Option A implemented. Slices A+B live-migrated and bounded office UAT PASS. Slice C implemented and atomically repaired in repository / not live-migrated / office UAT not run.** Option B live API remains **POST-V1**. |
| Updated | 2026-09-11 |
| Implementation | Slices A+B+C in `app/services/estimate_quickbooks.py`, `app/routes/estimate_quickbooks.py`. Hub PRICE `/projects/<id>/quickbooks-entry`. A+B migration **`e9f0a1b2c3d4` applied live**. Slice C events **`f0a1b2c3d4e5`** and occupancy **`f1a2b3c4d5e6` not applied live**. |

## Purpose

Define the architecture boundary for handing an **approved customer estimate** to QuickBooks without bypassing human review or the authoritative CalibraytAI estimate record.

## Joel V1 decision (2026-09-10)

| Option | Meaning | V1 status |
|--------|---------|-----------|
| **A.** Governed QuickBooks-ready output / controlled human-entry workflow | Internal office HTML/PDF pair a human uses to type a QuickBooks Estimate | **SELECTED.** Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Slice C **IMPLEMENTED / ATOMIC ENTERED REPAIR TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN**. |
| **B.** Live QuickBooks Online API | OAuth / SDK / auto-post | **POST-V1 / NOT AUTHORIZED** unless Joel separately reverses |

Distinguish:

| Term | Meaning |
|------|---------|
| QuickBooks-ready | Artifacts a human can use to type a QuickBooks Estimate |
| QuickBooks-importable | A file QuickBooks will ingest without typing — **not claimed in V1** |
| Manual QuickBooks entry | Human types from the sheet into QuickBooks |
| Live QuickBooks integration | API — Option B / POST-V1 |

Do **not** claim CSV, IIF, Excel, SDK, or API compatibility.

## Current state

- No QuickBooks Online API, OAuth, IIF, or CSV export exists in the application.
- Outputs 1–2 exist ([FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT**). Output 3 Slices A+B are **live-migrated / bounded office UAT PASS** ([FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) **OVERALL NOT CLOSED**). Slice C is **implemented and atomically repaired in the repository / not live-migrated / office UAT not run**.
- Family 04 **QuickBooks Estimate / Entry Sheet** is an **INTERNAL ENTRY REFERENCE** reusable master ([FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md)). Not a customer deliverable. Not an API.
- [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT / OVERALL NOT CLOSED**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Canonical UAT project **id 26**.
- [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md) **Accepted** by Joel Brayman, 10 Sep 2026.

## Source of truth

CalibraytAI remains the authoritative commercial record. QuickBooks is an **accounting destination**, not the estimating source of truth.

## Governed Option A pipeline

```text
Estimator authoritative record
  → CURRENT costing snapshot (FG-027)
  → CURRENT pricing snapshot (FG-009) consuming that costing snapshot
  → Issued or Accepted Proposal (output 2) matching those frozen totals
  → human review of QuickBooks-ready pair
  → ISSUED frozen office artifacts (output 3)
  → human types QuickBooks Estimate
  → optional human “entered in QuickBooks” confirmation
```

Download is **not** proof of entry. CalibraytAI cannot verify QuickBooks acceptance without an integration.

## Output 3 (V1)

A **controlled pair** of **internal office** artifacts ([fg-032-quickbooks-option-a-preflight.md](fg-032-quickbooks-option-a-preflight.md)):

1. **Sales-estimate entry sheet** (Family 04) — customer selling lines + tax from frozen pricing / Proposal.
2. **Planned cost-classification companion** — approved direct cost from the costing snapshot; class from frozen FG-031 routing. Not in Family 04.

Do **not** leak companion internals into the customer Proposal/PDF or Supplier Package.

Estimating / output layer owns the package. Proposals keep the customer PDF. Pricing Engine keeps pricing snapshots.

## Amounts

- Selling totals copy frozen pricing / Proposal. Do **not** recompute `Direct Cost / 0.85` at export.
- Direct-cost amounts copy the CURRENT costing snapshot. Routing classifies; it does not prove the amount.
- Supplier price and subcontract quotes remain evidence, not automatic cost authority.
- ISSUED artifacts must not float.

## Prohibited in unauthorized work

- Implementing QuickBooks API clients, OAuth, or SDK
- Auto-creating or auto-sending QuickBooks estimates
- Claiming CSV / IIF / Excel import
- Treating QuickBooks as the authoritative commercial record
- Invoices, bills, purchase orders, payroll, payments, banking, or actual-cost sync under this pin
- Implementing FG-032 product code from architecture recording alone

## Related

- [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md)
- [ADR-049](../adr/ADR-049-quickbooks-ready-output-ownership-and-snapshot.md)
- [fg-032-quickbooks-option-a-preflight.md](fg-032-quickbooks-option-a-preflight.md)
- [project-document-package.md](project-document-package.md)
- [pricing-policy.md](../pricing-policy.md)
- [v1-completion-register.md](../v1-completion-register.md)
- [platform-roadmap.md](../platform-roadmap.md)
