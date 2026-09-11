# ADR-049 — QuickBooks-Ready Output Ownership, Snapshot, and Human-Entry Boundary

| Field | Value |
|-------|--------|
| Title | ADR-049: QuickBooks-Ready Output Ownership, Snapshot, and Human-Entry Boundary |
| Status | **Accepted** by Joel Brayman, 10 Sep 2026. [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) Slices A+B **LIVE-MIGRATED / BOUNDED OFFICE UAT PASS / OPERATIONAL FOR UAT**. Slice C **IMPLEMENTED / ATOMIC ENTERED REPAIR TESTED / COMMITTED / PUSHED / NOT LIVE-MIGRATED / OFFICE UAT NOT RUN**. Product SHA **`70e571140e12377aa5bd009b598530576401113b`**. Product parent **`010f6d641a756ceb2ab67475a284d3b8426c7b20`**. Live current **`e9f0a1b2c3d4`**. Repository head **`f1a2b3c4d5e6`**. Gate **NOT CLOSED**. |
| Date | 2026-09-10 |
| Related | [FG-032](../feature-gates/FG-032-quickbooks-ready-output-entry-v1.md) · [fg-032-quickbooks-option-a-preflight.md](../architecture/fg-032-quickbooks-option-a-preflight.md) · [quickbooks-integration.md](../architecture/quickbooks-integration.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-044](ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [ADR-048](ADR-048-scope-delivery-make-buy-and-procurement-routing-ownership-boundary.md) **Accepted** · [FG-012](../feature-gates/FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-031](../feature-gates/FG-031-scope-delivery-make-buy-procurement-routing-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** |

This ADR is the **ownership and freeze boundary** for V1-05 Option A: a governed QuickBooks-ready output and controlled human-entry workflow. Joel authorized FG-032 Slices A+B implementation on **10 Sep 2026** and Slice C implementation on **11 Sep 2026**. It does **not** authorize CSV/IIF/Excel generation or a live QuickBooks API. It does **not** accept [ADR-008](ADR-008-supplier-price-snapshotting.md). Slice C live migration and office UAT remain **not run**. This ADR is **not closed**.

Joel selected Option A on **2026-09-10**. Option B (live QuickBooks Online API) remains **POST-V1** unless Joel separately changes that decision.

---

## Context

CalibraytAI already has:

- one authoritative `Estimate` / `EstimateVersion` record;
- human-approved `EstimateCostingSnapshot` (FG-027 / ADR-044);
- `EstimatePricingSnapshot` with frozen pre-tax selling price, tax percent, tax amount, and customer total (FG-009 / ADR-030);
- customer Proposal snapshot + PDF as output 2 (FG-012 / ADR-002);
- FG-031 frozen routing copied onto costing snapshot lines at Costing Approval;
- Family 04 **QuickBooks Estimate / Entry Sheet** as an **INTERNAL ENTRY REFERENCE** reusable master (FG-022), not a QuickBooks API and not a customer deliverable.

No QuickBooks client, OAuth, IIF, or CSV export exists in application code. Slice C append-only `estimate_quickbooks_entry_events` exists in the repository and is **not** live-migrated.

Without this ADR, a later implementer could:

- treat QuickBooks as the commercial source of truth;
- auto-post or claim import compatibility without evidence;
- recompute selling price from current 15% policy instead of frozen snapshots;
- leak internal cost/routing into the customer Proposal;
- collapse sales-estimate entry and planned cost classification into one ambiguous artifact;
- invent a split of hybrid line amounts that the costing snapshot does not store.

Existing [quickbooks-integration.md](../architecture/quickbooks-integration.md) already pins Estimator authority, human review, and no auto-send. It does **not** pin artifact ownership, freeze identity, sales vs cost-class pair, or manual-entry confirmation. Those are this ADR.

---

## Decision

**Accepted.** FG-032 Slices A+B implement Estimating-owned freeze tables, review/issue, and private HTML/PDF artifacts. Slice C (`estimate_quickbooks_entry_events`, ENTERED/REVERSED/CORRECTED, plus unique occupancy lock) is **implemented in the repository** and **not live-migrated**.

### 1. CalibraytAI remains the commercial source of truth

QuickBooks is an **accounting destination**. The QuickBooks-ready artifact references frozen CalibraytAI records. It must not take ownership of `EstimateLineItem`, costing snapshots, pricing snapshots, Proposal, Scope Delivery, supplier price, subcontract quote evidence, or PLAN.

### 2. Option A is QuickBooks-ready manual entry, not import or API

V1 Option A produces **QuickBooks-ready** internal office artifacts a human can use to type a QuickBooks Estimate.

It is **not**:

- QuickBooks-importable (no CSV / IIF / Excel / SDK claim);
- live QuickBooks integration (Option B / POST-V1);
- invoices, bills, purchase orders, payroll, payments, banking, or actual-cost sync.

Family 04 title **QUICKBOOKS ESTIMATE / ENTRY SHEET** and header **INTERNAL ENTRY REFERENCE** confirm a **manual-entry** presentation, not an import file. The verification PDF (opened 2026-09-10) stores no project amounts on the master.

### 3. Output 3 is a controlled pair

V1 output 3 is **C: a controlled pair**:

| Artifact | Audience | Source of amounts | Family 04 |
|----------|----------|-------------------|-----------|
| **A. Sales-estimate entry sheet** | Internal office / accounting | Frozen customer selling lines + tax from CURRENT `EstimatePricingSnapshot` reconciled to Issued/Accepted Proposal | Yes — presentation master |
| **B. Planned cost-classification companion** | Internal office only | Approved direct cost from CURRENT `EstimateCostingSnapshot`; planned class from frozen FG-031 routing on costing snapshot lines | No — not in Family 04 |

Do **not** put internal cost class, routing enums, supplier price, subcontract quote amounts, or margin on artifact A. Do **not** put selling price or tax on artifact B as a second selling total.

Invoices, vendor bills, deposits, and payment schedules are **out of V1**.

### 4. Estimating owns the QuickBooks-ready package; Proposals and Pricing keep their records

| Concern | Owner |
|---------|--------|
| QuickBooks-ready package identity, freeze, PDF/HTML generation, review, supersession, entry-confirmation records | **Estimating / output layer** (same pattern as FG-012 internal breakdown) |
| Customer Proposal / PDF | **Proposals** (unchanged) |
| Pricing snapshot / tax arithmetic | **Pricing Engine** (consumed, not rewritten) |
| Costing snapshot | **Estimating** (consumed, not rewritten) |
| Scope Delivery | **Estimating** (consumed via costing freeze; not rewritten) |
| QuickBooks Online | **None in V1** |

Estimating does **not** become an accounting system. It owns the **handoff artifact**, not QuickBooks.

### 5. Amounts come from frozen snapshots, not live policy

- Selling totals and tax copy from the CURRENT `EstimatePricingSnapshot` that consumed the CURRENT costing snapshot. Do **not** recompute `Direct Cost / 0.85` at export.
- Direct-cost amounts copy from CURRENT `EstimateCostingSnapshot` lines. Routing classifies; it does not prove the amount.
- Supplier price and subcontract quoted amounts remain **evidence**, not automatic cost authority.
- After ISSUED, historical artifacts must not float when working lines, tax policy, or customer data later change.

### 6. Hybrid lines must not be double-counted

A line may be `CONTRACTOR_PURCHASED` + `SUBCONTRACT` (hybrid). V1 reports the **one** approved `extended_cost` once, with both frozen dimensions. Do **not** invent a material/labour split. Split allocation is **MISSING** and **FUTURE**.

`UNRESOLVED` routing on a non-Allowance line **BLOCKS** generation (already blocks Costing Approval). Allowance exception remains as in FG-031.

### 7. Explicit human review and explicit entry confirmation

No AI or deterministic rule may silently approve costing, approve pricing, select a QuickBooks account or tax code, mark an output entered, overwrite an ISSUED artifact, or post to QuickBooks.

Download is **not** proof of entry. “Entered in QuickBooks” is a separate human record. CalibraytAI cannot verify QuickBooks acceptance without an integration.

### 8. Regeneration supersedes; it does not edit history

Correction of an ISSUED package creates a new package and SUPERSEDES the prior one. ISSUED bytes are immutable. Recost or reprice that changes CURRENT snapshot identity makes an unissued DRAFT stale and **BLOCKS** issue until regenerated from the new CURRENT pins.

---

## Alternatives Considered

- **A. Sales-estimate entry only** — Rejected as the sole V1 output. Family 04 is the sales-entry sheet, but FG-031 exists specifically so QuickBooks can consume planned cost class without contaminating the customer estimate. Dropping the companion would leave V1-05 unable to support job/cost-class setup.
- **B. Internal cost/budget entry only** — Rejected. The four-output commitment and Family 04 are a QuickBooks **Estimate / Entry** of customer commercial values.
- **Live API in V1 (Option B)** — Rejected by Joel 2026-09-10. POST-V1.
- **Claim CSV/IIF import** — Rejected. No repository evidence of a supported QuickBooks import contract.
- **Let Proposals own the QB PDF** — Rejected. Proposal is the customer-facing estimate and must stay delivery-blind. Internal entry is Estimating/output, like internal breakdown.
- **Accept this ADR in the recording pass** — Rejected at recording. Joel accepted this ADR on **10 Sep 2026** with FG-032 Slices A+B implementation authorization.

---

## Consequences

Positive: V1 can hand a human a frozen sales-entry sheet plus a private cost-class companion without pretending QuickBooks was updated.

Negative: Office users still type into QuickBooks. Duplicate-entry risk is controlled by confirmation records, not by API idempotency. Layout of Family 04 still needs implementation-time visual mapping.

## Module Ownership Impact

Estimating gains ownership of the future QuickBooks-ready package records. Proposals, Pricing Engine, PLAN, Supplier Catalogue, and MONITOR do not gain those records. Estimating’s existing prohibition on “accounting integrations” is narrowed: it may own the **ready artifact**; it still must not own QuickBooks.

## Data Ownership Impact

New Estimating-owned freeze tables (names in the preflight; not created now). Copied facts only. Source snapshots remain owned by their current modules.

## Migration Impact

Additive revision **`e9f0a1b2c3d4`** revises **`d8e9f0a1b2c3`** (Slices A+B; **applied live** 2026-09-11). Additive revision **`f0a1b2c3d4e5`** revises **`e9f0a1b2c3d4`** (Slice C events; **not applied live**). Additive revision **`f1a2b3c4d5e6`** revises **`f0a1b2c3d4e5`** (active ENTERED occupancy; **not applied live**). One graph head **`f1a2b3c4d5e6`**. Live current **`e9f0a1b2c3d4`**.

## Testing Impact

Focused FG-032 tests plus FG-009 / FG-012 / FG-027 / FG-029 / FG-031 / Proposal / authorization regression. Live migration and bounded office UAT **PASS** 2026-09-11 for Slices A+B. Slice C confirmation-not-from-download is implemented in tests. Concurrent ENTERED occupancy enforcement is tested with independent sessions. Slice C live migrate and office UAT **NOT RUN**.

## Documentation Impact

FG-032; Option A preflight; quickbooks-integration.md; project-document-package.md; estimating module; indexes; V1 register **status text only** (no rescore).

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Option A **direction** approved 2026-09-10. This ADR **Accepted** 10 Sep 2026 with FG-032 Slices A+B implementation authorization. | 2026-09-10 |
| ChatGPT review | Architecture recording, then corrected Issued vs Accepted freeze, then implementation prompt. | 2026-09-10 |
| Cursor implementation note | **Accepted.** Slices A+B implemented as authorized. Slice C implemented 11 Sep 2026. Atomic ENTERED occupancy repair 11 Sep 2026. Live Slice C migration **not** run. Slice C office UAT **not** run. | 2026-09-11 |
