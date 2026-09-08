# ADR-044 — Costing Approval, Snapshot Ownership, and Pricing Consumption Boundary

| Field | Value |
|-------|--------|
| Title | ADR-044: Costing Approval, Snapshot Ownership, and Pricing Consumption Boundary |
| Status | **Accepted** |
| Date | 2026-09-08 |
| Related | [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) · [ADR-030](ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) · [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) · [ADR-024](ADR-024-learn-recommendation-boundary.md) · [ADR-008](ADR-008-supplier-price-snapshotting.md) **Proposed** · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) · [FG-026](../feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) · [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) · [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md) |

This ADR does **not** authorize schema, migration, or product-code changes. [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) implementation requires a **separate** bounded execution prompt.

This ADR does **not** accept [ADR-008](ADR-008-supplier-price-snapshotting.md).

**Subsequent status (2026-09-08 live migrate + UAT):** Additive `a5b6c7d8e9f0` **applied live**. Office UAT **STOPPED / NOT PASS** on EstimateLineItem id 7 override provenance (`library_unit_cost_reference` NULL). Gate **NOT CLOSED**. ADR-044 itself stays **Accepted**.

**Subsequent status (2026-09-08 bounded legacy override-provenance repair):** Product SHA **`72949f99da2b56ec06e95e16e29fa194a6730bbd`**. NULL `library_unit_cost_reference` on a CostItem/Assembly Draft edit now freezes pre-edit working `unit_cost` as the line reference; a changed cost is `MANUAL_OVERRIDE`. No new migration. No live DB write. Gate remained **NOT CLOSED** until UAT continuation.

**Subsequent status (2026-09-08 office UAT continuation + close):** Remaining office UAT **PASS** on EstimateVersion **id 9**. Legacy override freeze **PASS**. Approve All / supersession / Pricing consume / STALE / re-apply **PASS**. [FG-027](../feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. ADR-044 stays **Accepted**. Do **not** accept ADR-008 from this close.

---

## Context

CalibAi V1-02 exists to insert a governed human **COSTING** approval boundary between working `EstimateLineItem` direct costs and the [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) Pricing Engine.

Today (repository evidence, 2026-09-08):

- Direct cost that Pricing Engine consumes is Σ `EstimateLineItem.extended_cost` (`version_line_direct_cost`).
- CostItem and Assembly library `unit_cost` is copied onto the line at insert. Later library edits do not rewrite existing lines.
- There is no costing-approval record, no costing snapshot, and no fail-closed requirement that pricing consume an approved cost basis.
- `apply_resolved_pricing_to_version` may run on any editable Draft. Default `include_labour_snapshot_direct_cost=False` remains in force.
- `EstimatePricingSnapshot` is unique per `EstimateVersion` and is **mutable on Draft** (implementation weaker than ADR-030’s “immutable” wording). `EstimateLabourSnapshot` is the stronger freeze pattern (`before_update` / `before_delete` always raise).
- FG-026 inserted UAT line id 7 has `unit_cost` 0 because Assembly id 2 has zero components. Mapping does not invent cost.

“Approve All” in V1-02 means **costing approval only**. It does not approve takeoff mappings, apply Pricing automatically, approve customer selling price, approve supplier selection, or approve legal/customer documents.

Lifecycle inside PRICE (no new top-level stage):

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

---

## Decision

A. **Estimating owns** costing approval and costing snapshots.

B. **Pricing Engine consumes** the current approved costing / direct-cost basis. It does **not** own costing approval. Do not use `EstimatePricingSnapshot` as the costing-approval record.

C. **Labour Engine retains** ownership of `EstimateLabourSnapshot`.

D. V1-02 does **not** include Labour Snapshot direct cost in the selling-price basis. Existing `include_labour_snapshot_direct_cost=False` remains unchanged.

E. Human costing approval is **mandatory** before governed Pricing application.

F. Approval is **EstimateVersion-level** with **frozen line-level costing facts**.

G. Working Draft `EstimateLineItem.unit_cost` remains editable before and after approval **while the version remains editable Draft**. Any costing-relevant change after approval **supersedes / invalidates** the prior costing approval.

H. Recosting an editable Draft creates a **new immutable costing snapshot on the same EstimateVersion**.

I. Recosting does **not** require a new EstimateVersion by itself.

J. Locked / Issued EstimateVersions **cannot recost**.

K. If an approved costing basis changes after Pricing was applied, the existing pricing result is **STALE**. Pricing must be **re-applied** before it may be treated as current.

L. Costing approval must preserve provenance and manual-override evidence (actor, time, source kind, reference/library cost, approved cost, reason).

M. Supplier evidence is **not required** for V1-02. V1-03 owns BMR/supplier workflow. ADR-008 remains Proposed.

N. Sophisticated ML confidence / LEARN is **not** part of V1-02 ([ADR-024](ADR-024-learn-recommendation-boundary.md)).

O. V1-02 deterministic exception status does **not** equal future AI confidence.

### Product policy (Joel / ChatGPT, 2026-09-08)

1. Approve All Costing is mandatory human authority before Pricing.
2. Costing snapshot ownership = **Estimating**.
3. Approval model = version-level + frozen line facts.
4. Labour snapshots remain **out** of default Pricing direct-cost basis.
5. Zero / missing CostItem or Assembly commercial cost **BLOCKS** approval. Do not approve an unexplained $0 commercial line.
6. Manual Custom / Allowance: **WARN, not BLOCK**, provided a valid cost has been entered.
7. Supplier evidence is not required.
8. Editing after costing approval is permitted only on editable Draft; any costing-relevant edit makes prior approved costing stale and requires new approval before Pricing may be current.
9. Recost / supersession = new immutable costing snapshot on the **same** Draft EstimateVersion.
10. Existing Pricing after recost becomes STALE; the user must explicitly re-apply Pricing.
11. Locked / Issued: **no recost**.
12. Office Labour Snapshot pin action is **out of V1-02**.
13. Stale CostItem age / effective-date policy is **out of V1-02** until a governed dated commercial-evidence model exists.
14. Manual library-cost override is allowed to an already-authorized Draft estimator/editor. Do not invent new RBAC. Require an override reason where a library-derived cost is changed. Preserve actor, timestamp, original/reference library cost, approved override cost, and reason. Do not mutate the CostItem/Assembly library when one project line is overridden.

### Working cost vs approved cost

| Layer | Meaning | Mutable? |
|-------|---------|----------|
| **WORKING DIRECT COST** | Current Draft `EstimateLineItem` quantity / unit / unit_cost / waste / extended_cost | Yes, on editable Draft |
| **APPROVED COSTING** | Immutable human-approved snapshot of that EstimateVersion’s direct-cost basis | No. Supersede by a new snapshot |
| **PRICING** | Separate later FG-009 action | Draft pricing snapshot remains FG-009-owned; becomes STALE if costing snapshot changes |

Do not replace EstimateLineItem working values with snapshot-only editing.

---

## Alternatives Considered

- **Reuse `EstimatePricingSnapshot` as the costing approval record** — Rejected. That snapshot is selling-price, unique per version, Draft-mutable, and owned by Pricing Engine.
- **Line-only approval without a version-level freeze** — Rejected. Pricing Engine prices a version. Partial line approval cannot produce a complete approved direct-cost total.
- **Require a new EstimateVersion on every recost** — Rejected for V1-02. Recost creates a new costing snapshot on the same editable Draft.
- **Include labour-snapshot direct cost in the pricing basis** — Rejected for V1-02. Would violate the FG-008/009 double-count protection unless a separate labour-in-basis decision is made later.
- **Require supplier evidence to approve costing** — Rejected. V1-03 / ADR-008.
- **JSON-only costing snapshot** — Rejected for financially significant line facts. Relational child rows are required. JSON may hold advisory warning lists.

---

## Consequences

- Later implementation requires an additive migration (Rule 7) for `EstimateCostingSnapshot`, frozen line rows, working-line override provenance columns, and a `costing_snapshot_id` on `EstimatePricingSnapshot`.
- Governed Apply Pricing must fail closed when no current approved costing snapshot exists.
- CostItem / Assembly library edits still must not rewrite approved costing (existing copy-at-insert already does this weakly; the snapshot makes it an explicit contract).
- FG-026 insertion/citation provenance remains PLAN-quantity provenance and is not a cost basis.
- Pricing named methods, tax, GM, and markup remain FG-009 / ADR-025 / ADR-030.

## Module Ownership Impact

| Concern | Owner |
|---------|--------|
| Working `EstimateLineItem` costs; costing approval; costing snapshots; Costing Review UI | **Estimating** |
| Named methods, org pricing policy, `EstimatePricingSnapshot`, Apply Pricing | **Pricing Engine** (consumes approved costing) |
| `EstimateLabourSnapshot`, labour standards | **Labour Engine** (unchanged; out of V1-02 basis) |
| Takeoff package / insertion citations | **Plan Intelligence** / Estimating insertion (FG-026 unchanged) |
| Canonical material identity | **Material Catalogue** (identity only; not a cost source) |
| Supplier price snapshots | **Not V1-02.** ADR-008 remains Proposed |

## Data Ownership Impact

Estimating owns approved costing facts. Pricing Engine records **which costing snapshot** it consumed. Labour snapshots remain Labour-owned and are not the costing freeze. Historical evidence remains evidence-only and must not auto-write CostItem `unit_cost`.

## Migration Impact

**Deferred.** Additive when FG-027 implementation is authorized. Proposed later revision and exact columns: [fg-027-costing-approval-preflight.md](../architecture/fg-027-costing-approval-preflight.md). Do **not** generate a revision from this ADR.

## Testing Impact

Deferred to FG-027 implementation. Required cases are listed in the Feature Gate and preflight. No tests in this governance pass.

## Documentation Impact

FG-027; costing-approval preflight; ADR index; Estimating and Pricing Engine module docs; V1 completion register; current-state / session-handoff / roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel | **2026-09-08** — ACCEPT the fourteen product-policy decisions and ownership pins in the authorized V1-02 ADR / Feature Gate / preflight prompt |
| ChatGPT review | Accepted as the costing-approval / snapshot / Pricing consumption boundary | 2026-09-08 |
| Cursor implementation note | **Accepted** as documentation. **No product code or migration.** Implementation **not** authorized. | 2026-09-08 |
