# Feature Gate FG-012: Internal Detailed Cost Breakdown + Customer Estimate Consistency

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-012` |
| Feature Name | Internal Detailed Cost Breakdown + Customer Estimate Consistency |
| Target Milestone | **None.** FG-012 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Estimating** (owner), with a bounded **Proposals** dependency because the existing Proposal is the customer-facing estimate |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Architecture | Existing `Estimate` / `EstimateVersion` / lines / `EstimatePricingSnapshot` (when present) remain the authoritative commercial source. No new estimate entity. No new document module. |
| Related ADRs | [ADR-001](../adr/ADR-001-proposal-snapshot-ownership.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** |
| Prerequisites | FG-008 / FG-009 / FG-010 / FG-011 **CLOSED / OPERATIONAL FOR UAT**. Roadmap item 9 read-only architecture assessment accepted 2026-08-30. |
| Approved baseline | `main` @ `2733e2f3b68b7320f08f093875e272532cd78885`. Alembic current/head `b4c5d6e7f8a9`. Last recorded full suite **264 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Architecture (read-only assessment 2026-08-30) | **Accepted by Joel** with the decisions recorded in this gate |
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| Implementation | **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** |
| Schema / Alembic | **NO** change (unchanged at `b4c5d6e7f8a9`) |
| New ADR | **None** |
| New module / customer-estimate entity | **None** |

This gate authorizes **outputs 1 and 2 only** of the future four-output package: an Estimating-owned internal detailed cost breakdown, and commercial consistency of the **existing Proposal** preview/PDF as the customer-facing estimate. It does **not** authorize QuickBooks, Ontario contract/warranty, a four-output renderer, Phase D, external AI, BUILD/MONITOR/LEARN, actual-cost capture, profitability, industry benchmarking, or contractor onboarding.

**FG-009 remains CLOSED / OPERATIONAL FOR UAT.** This gate consumes pricing snapshots read-only for methodology. It does not reopen named methods, optional-layer policy, or labour-in-basis rules.

---

## Purpose and business rationale

Internal and customer-facing estimate information must derive consistently from the same authoritative `EstimateVersion` (and `EstimatePricingSnapshot` when present). Today a snapshotted `TRUE_GROSS_MARGIN` or `COST_PLUS_MARKUP` version can be restacked by Proposal generation using the legacy markup/overhead/profit calculation, so customer totals can diverge from the frozen snapshot. The office Estimate Totals header can also present legacy stack labels when a snapshot is authoritative. The customer PDF can print Overhead/Profit rows that the customer preview does not.

FG-012 closes that consistency gap without inventing a second estimate, a second customer document family, or a new source of truth.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Internal and customer-facing estimate outputs can diverge from the same `EstimateVersion` / pricing snapshot. Estimators cannot rely on a defensible internal breakdown and a customer Proposal that share one commercial authority. |
| 2 | Who is the user? | Office estimators / chief estimator on the current unauthenticated office app. Internal breakdown is internal-only. Proposal preview/PDF remains customer-facing. |
| 3 | Which module owns it? | **Estimating** owns the internal breakdown and the authoritative estimate record. **Proposals** remains owner of the customer commercial snapshot, preview, and PDF. Pricing Engine and Labour Engine are consumed read-only. |
| 4 | What data does it own? | **No new durable records.** Estimating continues to own estimates/versions/lines. Proposals continues to own proposal snapshots. |
| 5 | What data does it reference? | `EstimatePricingSnapshot` (Pricing Engine, frozen method and customer total when present); `EstimateLabourSnapshot` (Labour Engine, display-only, not in selling-price basis); `CostItem` category where a line has a cost-item FK; `Project` identity. |
| 6 | What may implementation change? | Estimating office internal breakdown view/document for one `EstimateVersion`; Estimate Totals presentation when a snapshot is authoritative; Proposal create/recalc/preview/PDF so customer totals match the source version/snapshot and customer PDF does not leak Overhead/Profit; dedicated tests; governed docs. |
| 7 | What must implementation not change? | FG-009 methodology; labour-in-basis policy; Accepted proposal mutation; locked version/snapshot writes; historical estimate math; schemas; migrations; Phase D; external AI; QuickBooks; contracts; four-output renderer; TBD/PLACEHOLDER schema; new modules/entities. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated consistency tests; proposal/PDF non-leak tests; pricing/labour/proposal/estimate regressions; org-isolation; Accepted immutability; full suite. |
| 10 | Documentation? | This gate; `modules/estimating.md`; `modules/proposals.md`; feature-gate index; current-state; project-state-report; roadmap; session-handoff; chat-workflow-log; `architecture/project-document-package.md` outputs 1–2 boundary. |
| 11 | ADR required? | **No** for this bounded scope. ADR-001/002/025/030 already govern snapshot ownership, Accepted immutability, and named methods. **STOP** and return if implementation would need a new document module, a new customer-estimate entity, a generated-output registry, a new durable commercial-state model, ownership transfer, or a change to Proposal’s architectural role. |
| 12 | Migration? | **No.** If a schema change appears required, **STOP**. Do not create a migration. Return for governance review. |

---

## Architecture (binding)

### Authoritative source

Do **not** create a new authoritative estimate entity.

```text
Estimate
  → EstimateVersion
    → Estimate sections / line items
    → EstimatePricingSnapshot when present
    → version totals when no snapshot (legacy COST_PLUS_MARKUP_STACK)
```

`EstimateLabourSnapshot` is **related evidence**. It is **not** part of the selling-price basis.

Proposal remains an **independent customer commercial snapshot** derived from a **specific** `EstimateVersion`. It must not float with later estimate edits. Accepted proposals remain immutable ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)).

### Joel decision — customer estimate

The **existing Proposal** (preview + PDF) **is** the customer-facing estimate.

Do **not** create: a separate Customer Estimate entity; another customer-document family; a parallel estimate snapshot; a new document-output module.

FG-012 must make that existing output commercially consistent with its source `EstimateVersion` / `EstimatePricingSnapshot`.

### Joel decision — output scope

| Output | FG-012 |
|--------|--------|
| 1. Internal Detailed Cost Breakdown | **In scope** (Estimating-owned office view/document) |
| 2. Customer-Facing Estimate | **In scope** via existing Proposal architecture |
| 3. QuickBooks Estimate/Entry | **Out** — Future, separately gated |
| 4. Ontario Contract + Warranty | **Out** — Future, separately gated |

Do **not** create a generalized four-output renderer.

**Source-contract principle** (architecture only, for later outputs 3–4): every governed output must identify and derive from the authoritative `EstimateVersion` and, when present, its `EstimatePricingSnapshot`. FG-012 does not build a generated-output registry.

### Direct Cost rule

Internal Direct Cost **must** reconcile to:

```text
SUM OF EstimateLineItem.extended_cost
```

using the existing authoritative estimate calculation (waste already in `extended_cost`).

Do **not** add `EstimateLabourSnapshot` Direct Labour Cost to this basis. Do **not** change FG-009 commercial methodology.

### Pricing method consistency

Preserve:

- `TRUE_GROSS_MARGIN`
- `COST_PLUS_MARKUP`
- `COST_PLUS_MARKUP_STACK`
- legacy **no-snapshot** behaviour

If an `EstimatePricingSnapshot` exists: customer output must preserve the **frozen** method and commercial totals from that source. Proposal generation must **not** restack a `TRUE_GROSS_MARGIN` or `COST_PLUS_MARKUP` source using the legacy markup/overhead/profit calculation.

If no snapshot exists: preserve existing legacy `COST_PLUS_MARKUP_STACK` behaviour. Do **not** backfill old estimates into `TRUE_GROSS_MARGIN`.

### Customer total reconciliation

| Source | Customer grand total must equal |
|--------|----------------------------------|
| Snapshot present | `EstimatePricingSnapshot` customer total |
| No snapshot | Authoritative `EstimateVersion.total` under the existing legacy stack |

Tax follows stored snapshot/version treatment. Do **not** create a new tax engine.

ORG-001 policy remains: $65 CAD/man-hour labour reference; `TRUE_GROSS_MARGIN` 15%; Selling Price = Direct Cost / 0.85; CA-ON; HST 13%; optional overhead/profit/contingency layers **UNSPECIFIED** unless separately governed. Do not invent optional-layer policy.

### Customer information boundary

Customer preview/PDF must **not** expose: unit cost, extended/direct cost, internal markup, gross margin, internal labour cost, Labour Engine snapshot cost, internal profitability, or other internal commercial evidence.

Customer line tables remain **selling-price oriented**.

### Joel decision — customer PDF Overhead / Profit leak

Include correction of the current customer-PDF presentation inconsistency. The customer PDF must **not** expose internal Overhead / Profit rows merely because the legacy stack uses those calculation concepts.

This is a **presentation correction** within the consistency objective. Do not redesign the Proposal PDF generally.

### Joel decision — Estimate Totals header debt

When an `EstimatePricingSnapshot` is authoritative, internal estimate/output presentation must identify the **actual authoritative pricing method** rather than misleadingly presenting legacy Overhead / Profit percentage labels as though they govern the calculation.

This is **presentation reconciliation**. Do not reopen FG-009 methodology, change pricing policy, or change historical estimate math.

### Labour snapshot (Joel decision)

`EstimateLabourSnapshot` **may** be displayed on the internal breakdown as separate evidence.

If displayed, label it substantially as:

**LABOUR ENGINE SNAPSHOT — NOT INCLUDED IN SELLING-PRICE BASIS**

It may show already-stored calculated man-hours, direct labour cost, and other already-authorized snapshot evidence.

It must **not**: increase Direct Cost; alter selling price; duplicate CostItem Labour lines into the price basis; change Pricing Snapshot values; change Labour Engine policy; or imply that labour snapshot cost has been commercially applied.

Any future decision to include Labour Engine snapshot cost in the estimate basis requires **separate governance**.

### Allowance

Existing Allowance lines remain explicitly labeled. Preserve their existing authoritative commercial treatment. Do not invent allowance amounts.

### Joel decision — TBD / PLACEHOLDER

**DO NOT** add a durable TBD / PLACEHOLDER enum, column, table, schema state, or workflow under FG-012. No schema expansion is authorized for this issue.

Where unresolved amounts are already represented through Allowance, notes, or existing descriptions, preserve those explicit indications. Do not invent supplier/subcontract prices.

Machine-enforced TBD/PLACEHOLDER commercial state is **deferred** to separate governance. Residual / future product work.

### Source traceability

Both internal and customer outputs must be traceable to:

- `Estimate`
- `EstimateVersion`
- `EstimatePricingSnapshot` when present

Proposal must continue to snapshot its source rather than float with later `EstimateVersion` edits. Internal output must clearly identify the `EstimateVersion` it represents. Do **not** add a generated-output registry in FG-012.

### Immutability

Preserve: Accepted Proposal immutability; locked `EstimateVersion` protections; `EstimatePricingSnapshot` frozen method; `EstimateLabourSnapshot` evidence; historical customer documents; historical (no-snapshot) estimate behaviour.

An Accepted Proposal must **never** be silently regenerated or rewritten because its source estimate later changes.

### Tenant isolation

All reads remain organization-scoped. Cross-org access fails closed. ORG-001 commercial intelligence remains organization-specific.

---

## Ownership

| Record / concern | Owner | FG-012 |
|------------------|--------|--------|
| `Estimate` / `EstimateVersion` / sections / lines | Estimating | Authoritative source; internal breakdown |
| Internal Detailed Cost Breakdown view/document | **Estimating** | Implement |
| `EstimatePricingSnapshot` | Pricing Engine | Consume frozen method/totals; do not reopen FG-009 |
| `EstimateLabourSnapshot` | Labour Engine | Optional internal display; not in basis |
| `Proposal` / snapshot lines / preview / PDF | Proposals | Bounded consistency + PDF presentation fix |
| QuickBooks / contract-warranty | Future owners | Out of scope |
| Generated-output registry | — | Not authorized |

---

## Scope

### In (implementation, after a separate approved Cursor prompt)

- Estimating-owned internal office view/document for one `EstimateVersion` from stored facts
- Proposal create/recalc/preview/PDF totals equal the source version/snapshot customer total
- Customer PDF Overhead/Profit leak correction
- Estimate Totals / internal presentation of authoritative method when a snapshot governs
- Org-scoped reads; source identity on both outputs
- Dedicated tests and docs closure

### Out

- New module, Customer Estimate entity, parallel snapshot, or document-output module
- Outputs 3 and 4; four-output renderer; generated-output registry
- Schema / Alembic
- New ADR
- TBD/PLACEHOLDER durable state
- Labour-in-basis policy change
- FG-009 methodology / optional-layer invention
- Phase D; external AI; OCR; CAD; authentication
- BUILD; MONITOR; LEARN; actual-cost; profitability; industry benchmarking; historical-upload onboarding
- QuickBooks; Ontario contract/warranty
- Rewriting Accepted proposals; backfilling legacy versions to true GM

---

## Acceptance criteria

1. Internal and customer outputs derive from the same authoritative `EstimateVersion`.
2. Pricing Snapshot identity is preserved/traceable when present.
3. Internal Direct Cost = Σ `EstimateLineItem.extended_cost`.
4. Labour snapshot cost remains separate and explicitly not included in selling-price basis.
5. `TRUE_GROSS_MARGIN` customer output reconciles exactly to authoritative snapshot customer total.
6. `COST_PLUS_MARKUP` customer output reconciles to authoritative snapshot.
7. Legacy no-snapshot output preserves `COST_PLUS_MARKUP_STACK` behaviour.
8. Customer output does not leak internal Direct Cost, unit cost, GM, labour cost, or internal markup.
9. Customer PDF does not expose internal Overhead/Profit rows.
10. Internal presentation identifies the actual authoritative pricing method rather than misleading legacy stack labels when snapshot pricing governs.
11. Allowances remain explicit.
12. No invented supplier/subcontract pricing.
13. Tax reconciles to stored authoritative snapshot/version treatment.
14. Accepted proposals remain immutable.
15. Later estimate edits do not float historical proposals.
16. Cross-org access fails closed.
17. No schema change.
18. No migration.
19. No Phase D.
20. No external AI.
21. No QuickBooks.
22. No contract/warranty.
23. No four-output renderer.
24. No labour-in-basis policy change.
25. Dedicated tests and relevant regressions pass.
26. Full suite passes.
27. Documentation reconciled before closure.

---

## Test expectations (implementation prompt)

- Dedicated FG-012 tests: same version on both outputs; Direct Cost = Σ `extended_cost`; true-GM and cost-plus-markup proposal totals equal snapshot `customer_total`; no-snapshot proposal equals version stack total; customer HTML/PDF absence of unit_cost / GM / labour cost / Overhead/Profit labels; internal view shows method + Direct Cost; labour block labeled not-in-basis when shown; Allowance labeled; locked snapshot unchanged by generating outputs; Accepted proposal not mutated; cross-org 404.
- Regressions: `tests/test_pricing_engine.py`, `tests/test_estimate_builder.py`, `tests/test_proposal_immutability.py`, `tests/test_proposal_snapshots.py`, `tests/test_proposal_pdf.py`, `tests/test_proposal_preview.py`, labour, historical, change orders as relevant.
- Full suite (`./venv/bin/python -m pytest -q`). Last recorded baseline **264 passed**; count must not drop unexplained.
- Use labeled FG-009 UAT residue as synthetic evidence where appropriate. Do not create customer operating data. Do not alter ORG-001 operating policy rows.

---

## Likely implementation files (later — not this governance pass)

- Internal: Estimating templates/routes (e.g. `app/templates/estimates/`, `app/routes/estimates.py`); optional read-only renderer under `app/services/`
- Customer: `app/services/proposals.py`, `app/services/proposal_pdf.py`, proposal preview template only as required for totals consistency
- Presentation: `app/templates/estimates/version_detail.html` Estimate Totals header when snapshot is authoritative
- Tests: new dedicated suite; keep existing pricing/proposal/estimate tests

Do **not** change `migrations/`. Do **not** write Pricing Engine policy/methodology paths except read.

---

## Implementation boundaries

If implementation discovers a need for schema, a new owning module, a new customer-estimate entity, a generated-output registry, a new durable commercial-state model, ownership transfer, or a change to Proposal’s architectural role: **STOP**. Do not migrate. Return for ADR / governance review.

---

## Residual / future product work (explicitly not FG-012)

- Machine-enforced TBD / PLACEHOLDER commercial state
- Outputs 3–4 (QuickBooks; Ontario contract + warranty)
- Four-output renderer / generated-output registry
- Labour Engine snapshot cost in selling-price basis
- Optional overhead / profit / contingency layer policy
- Contractor historical-upload onboarding; industry benchmarking; actual-cost; profitability; MONITOR; LEARN

---

## Closure

Implementation 2026-08-30:

- Internal: `GET /estimates/<id>/versions/<version_id>/internal-breakdown` (`app/services/estimate_output.py`, `app/templates/estimates/internal_breakdown.html`)
- Customer: existing Proposal; named-method totals copy frozen `EstimatePricingSnapshot` (no markup/OH/profit restack); customer PDF Subtotal / Tax / Grand Total only
- Estimate Totals (version + estimate detail) show named method when a snapshot governs
- Dedicated tests `tests/test_estimate_output_consistency.py` **19 passed**; full suite **283 passed**
- Bounded synthetic UAT on labeled FG-009 residue + `PROP-FG012-UAT-GM` (Draft)

**PASS — FG-012 CLOSED / OPERATIONAL FOR UAT.**

**Next governed action:** **STOP DEVELOPMENT.** Do not begin another Feature Gate. Phase D **NOT STARTED / NOT AUTHORIZED**. External AI **NOT AUTHORIZED**.
