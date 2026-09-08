# Feature Gate FG-027: Automated Costing and Human Cost Approval V1

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-027` |
| Feature Name | Automated Costing and Human Cost Approval V1 |
| Target Milestone | **None.** FG-027 is the governing identifier for CalibAi **V1-02**. Do not assign a new M0xx number. Lifecycle home remains **PRICE**. Do not add a new top-level stage. |
| Module | **Estimating** owns costing approval and costing snapshots. **Pricing Engine consumes** the current approved costing. **Labour Engine** retains `EstimateLabourSnapshot`. No new module. |
| Date | 2026-09-08 |
| Status | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED.** **OFFICE UAT STOPPED / NOT PASS.** **NOT CLOSED.** **NOT OPERATIONAL FOR UAT.** Live current = heads **`a5b6c7d8e9f0`**. Architecture preflight remains complete. [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. |
| Architecture | [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** · [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md) **PREFLIGHT COMPLETE** · [ADR-025](../adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted** · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** · [ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md) **Accepted** · [ADR-007](../adr/ADR-007-plan-and-estimate-version-ownership.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [FG-009](FG-009-organization-calibrated-pricing-engine.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-008](FG-008-labour-engine-phase-b.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-012](FG-012-estimate-output-consistency.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-014](FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) **CLOSED / OPERATIONAL FOR UAT** · [FG-026](FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [v1-completion-register.md](../v1-completion-register.md) V1-02 · [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |
| Related ADRs | **[ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) Accepted**. Do **not** accept ADR-008 or ADR-010 from this gate. |
| Prerequisites | [FG-026](FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-009](FG-009-organization-calibrated-pricing-engine.md) **CLOSED**. Working CostItem / Assembly / Draft line edit exist. Live migrate + UAT require a **separate** authorized prompt. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED.** **OFFICE UAT STOPPED / NOT PASS.** **NOT CLOSED.** |
| Product code | `app/models/estimate_costing.py`; `app/services/estimate_costing.py`; Estimate version Costing Review; Pricing consume / stale |
| Schema / Alembic | Additive `a5b6c7d8e9f0` **applied live** (`f4a5b6c7d8e9` → `a5b6c7d8e9f0`). Live current = heads **`a5b6c7d8e9f0`**. |
| Approve All Costing | **IMPLEMENTED / LIVE.** Zero-cost BLOCK office UAT **PASS**. Full costing-approval UAT **STOPPED**. |
| Pricing consume / stale | **IMPLEMENTED / LIVE.** Office consume / stale UAT **NOT RUN** (stopped before Apply Pricing). |
| Labour-in-basis | **UNCHANGED** (`include_labour_snapshot_direct_cost=False`) |
| Supplier evidence | **NOT REQUIRED** |

```text
FG-027:
IMPLEMENTED / TESTED / COMMITTED / PUSHED / LIVE-MIGRATED
OFFICE UAT STOPPED / NOT PASS
NOT CLOSED
NOT OPERATIONAL FOR UAT
ADR-044 ACCEPTED
LIVE CURRENT = HEADS a5b6c7d8e9f0
APPROVE ALL = COSTING APPROVAL ONLY
DO NOT ACCEPT ADR-008
```

Joel authorized live migrate + bounded office UAT on **2026-09-08**. Live upgrade **PASS**. Office UAT **STOPPED** on EstimateLineItem **id 7** override-provenance defect (pre-FG-027 `library_unit_cost_reference` NULL). No product-code repair in that pass.

---

## Purpose

Insert a governed human **COSTING** approval boundary between working Draft `EstimateLineItem` direct costs and FG-009 Pricing Engine, so Brayman can operate a costed estimate and a BMR demo can show approved direct cost **before** selling price.

This gate must **not** duplicate Pricing Engine named methods, Labour Engine snapshots, Plan Intelligence mapping, Material Catalogue identity, or supplier workflow.

---

## Ownership (pinned)

| Concern | Owner |
|---------|--------|
| Working `EstimateLineItem` costs; Costing Review; Approve All Costing; `EstimateCostingSnapshot` + frozen line facts | **Estimating** |
| Named methods, org pricing policy, `EstimatePricingSnapshot`, Apply Pricing | **Pricing Engine** (consumes current approved costing) |
| `EstimateLabourSnapshot`, production / $/mh standards | **Labour Engine** (unchanged; out of V1-02 basis) |
| Takeoff package / FG-026 insertion citations | Plan Intelligence / Estimating insertion (**unchanged**) |
| Canonical material identity | Material Catalogue (read-only identity; not a cost source) |
| Supplier price snapshots | **Out of V1-02** (V1-03 / ADR-008 Proposed) |

---

## Required PRICE lifecycle (no new stage)

```text
ESTIMATE ITEMS
→ WORKING COSTING
→ EXCEPTION REVIEW
→ HUMAN COST CORRECTION / OVERRIDE
→ APPROVE ALL COSTING
→ APPROVED COSTING SNAPSHOT
→ APPLY PRICING
→ SELLING PRICE
```

**Approve All** means costing approval only. It does **not** approve takeoff mappings, apply Pricing automatically, approve customer selling price, approve supplier selection, or approve legal/customer documents.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Working line costs exist, but there is no human costing-approval freeze and no fail-closed contract that Pricing consume an approved direct-cost basis. FG-026 can insert a $0 Assembly line. Estimators can Apply org pricing on unreviewed $0 commercial lines. |
| 2 | Who is the user? | Office estimator/editor already authorized to edit a Draft EstimateVersion. Not Field Web. Not customers. No new RBAC. |
| 3 | Which module owns it? | **Estimating.** Pricing Engine consumes. Labour Engine unchanged. No new module. |
| 4 | What data does it own? | Later: Estimating-owned `EstimateCostingSnapshot` / frozen line rows; working-line override provenance columns. Not owned now. |
| 5 | What data does it reference? | `Estimate` / `EstimateVersion` / `EstimateSection` / `EstimateLineItem`; `CostItem` / `Assembly`; `Organization` / `Project` / `User` actor snapshot; `EstimatePricingSnapshot` (consumer FK later). Not labour snapshots as basis. Not CanonicalMaterial as cost. Not supplier tables (none exist). |
| 6 | What may it change? | When implementation is later authorized: additive costing snapshot schema; Costing Review on Estimate version; Approve All Costing; fail-closed / stale Pricing consume; working-line override reason. Existing Draft line-edit remains the working-cost editor. |
| 7 | What must it not change? | FG-026 insertion/citations; CostItem/Assembly library mutation from a project override; FG-009 named methods / tax / GM; `include_labour_snapshot_direct_cost=False`; labour standards; MaterialRequirement (absent); ADR-008; LEARN/ML; FG-024; remaining FG-025 surfaces; locked/issued recost. |
| 8 | What are the acceptance criteria? | See V1-02 required scope below. Implementation + tests + live migrate + UAT are **later**. This recording’s criterion is: ADR-044 Accepted, this gate recorded, preflight complete, no product code. |
| 9 | What tests are required? | Later implementation tests listed in this gate and the preflight. **No tests implemented now.** |
| 10 | What documentation must be updated? | This gate; preflight; ADR-044; ADR README; feature-gates README; V1 register; current-state; session-handoff; project-state-report; milestones; chat-workflow-log; roadmap; Estimating / Pricing Engine modules; architecture.md; CAR-001 subsequent status. |
| 11 | Does it require an ADR? | **Yes.** [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted** in this recording. |
| 12 | Does it require a database migration? | **Yes, later.** Additive proposed `a5b6c7d8e9f0` down_revision `f4a5b6c7d8e9`. **Not created in this pass.** |

---

## Approve All Costing semantics

Operates on **one** editable Draft EstimateVersion.

It **must**:

1. calculate/verify every included working line;
2. identify BLOCK conditions;
3. refuse approval while any blocking condition remains;
4. allow WARN conditions with explicit human visibility;
5. freeze line-level costing facts;
6. freeze approved direct-cost total;
7. record actor/time;
8. create the approved costing snapshot atomically.

It must **not**:

change takeoff provenance; change CostItem or Assembly library; create Labour standards; apply Pricing; create Proposal; change tax; change gross margin; create supplier evidence.

---

## Exception model (deterministic; not ML)

**BLOCK** (approval must not proceed):

- missing/zero CostItem commercial cost
- missing/zero Assembly rollup / unexplained $0 commercial Assembly line
- missing costing facts required to calculate extended cost
- invalid destination / non-editable EstimateVersion
- library-derived unit_cost changed without override reason
- any condition preventing a complete approved direct-cost total

**WARN** (visible; does not by itself block):

- Manual Custom (valid cost entered)
- Manual Allowance (valid cost entered)
- explicitly confirmed unit mismatch
- no supplier evidence
- canonical material unresolved
- historical-only evidence
- missing Labour Engine evidence where relevant (labour is not in basis)

**Inactive CostItem/Assembly:** fail-closed **refresh** from inactive library. Preserve already-copied Draft working values with **WARN** until the human decides. Do not silently rewrite the copied cost.

---

## V1-02 REQUIRED

- Costing Review on Draft EstimateVersion
- deterministic blocking/warnings
- working line cost editing (existing)
- override reason for library-derived cost changes
- Approve All Costing
- immutable version-level costing snapshot
- frozen line facts
- supersession/reapproval on the same Draft
- Pricing consumes current approved cost basis
- stale Pricing after recost
- labour snapshot **out** of basis
- no supplier requirement

## V1-02 MATURATION DURING BRAYMAN UAT

- richer exception-based review
- human-triggered refresh from library
- richer provenance
- historical suggestions (review-gated)
- stale-cost policy after dated evidence exists

## OUT OF V1-02

ML confidence; LEARN; supplier/BMR V1-03; ADR-008 implementation; MaterialRequirement; supplier SKU; labour-in-basis change; CostItem auto-update from historical data; office Labour Snapshot pin action; FG-024; FG-025 remaining surfaces; QuickBooks; contracts; Native Signing; Observation Delete; new PLAN / Permit / Field features.

---

## Required test plan (implemented)

Working CostItem cost; working Assembly cost; manual custom; manual allowance; zero-cost block; empty Assembly block; warnings do not block; manual override reason; version-level Approve All; frozen line facts; approved total; actor/time; recost same Draft; old costing snapshot preserved; supersession; locked version no recost; pricing cannot be current without approved costing; pricing becomes stale after recost; re-apply pricing after new costing approval; no Labour Snapshot basis change; no supplier requirement; no CostItem/Assembly mutation; transaction rollback. Dedicated file: `tests/test_estimate_costing_fg027.py`.

---

## Implementation authorization

**Product implementation authorized and executed 2026-09-08.** Live migrate + bounded office UAT authorized and executed the same date.

**Subsequent status (2026-09-08 live migrate + office UAT):** Live `flask db upgrade a5b6c7d8e9f0` **PASS**. Gitignored backup `instance/brayman_estimator-backup-before-fg027-a5b6c7d8e9f0.db`. Office UAT port **5016** against EstimateVersion **id 9**. Zero-cost BLOCK **PASS** (`MISSING_ASSEMBLY_COST`, `INCOMPLETE_DIRECT_COST_TOTAL`). Failed Approve All POST **PASS** (no snapshot). Working unit_cost on line **7** changed to **250** (extended **750**). Manual override provenance **FAIL**: `library_unit_cost_reference` remains **NULL** on the pre-FG-027 inserted line, so classification stayed `LIBRARY_ASSEMBLY`, override reason was not persisted, and Approve All became enabled without override evidence. UAT **STOPPED**. No Approve All snapshot. No Pricing apply. Assembly **id 2** and TakeoffPackage **id 1** unchanged. Gate **NOT CLOSED**. Product tests **not** rerun. Do **not** silently repair under the UAT prompt.

---

## Related

- [ADR-044](../adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md)
- [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md)
- [modules/estimating.md](../modules/estimating.md)
- [modules/pricing-engine.md](../modules/pricing-engine.md)
- [v1-completion-register.md](../v1-completion-register.md)
