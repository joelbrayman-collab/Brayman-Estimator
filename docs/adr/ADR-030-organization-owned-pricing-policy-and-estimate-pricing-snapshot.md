# ADR-030 — Organization-Owned Pricing Policy and Estimate Pricing Snapshot

| Field | Value |
|-------|--------|
| Title | ADR-030: Organization-Owned Versioned Pricing Policy and Estimate Pricing Snapshot |
| Status | **Accepted** |
| Date | 2026-08-29 |
| Related | [ADR-025](ADR-025-pricing-policy-versus-estimate-markup-stack.md) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) · [ADR-002](ADR-002-accepted-proposal-immutability.md) · [FG-009](../feature-gates/FG-009-organization-calibrated-pricing-engine.md) · [organization-calibrated-pricing-engine-architecture.md](../architecture/organization-calibrated-pricing-engine-architecture.md) · [ADR-029](ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) |

This ADR does **not** authorize schema or calculation-code changes. FG-009 implementation requires a **separate** bounded execution prompt.

---

## Context

ADR-025 (**Accepted**) decides that CalibAi must support **named pricing methods** (true gross margin, cost-plus markup, and the existing markup/overhead/profit stack) without mixing formulas.

That decision is insufficient alone. Live estimates store **percents**, not a policy identity. `ProjectCommercialContext` (M011) pins commercial **strategy** (`pricing_posture`, `execution_risk`, …) but does **not** select a pricing method or freeze rates. Proposal snapshots freeze **results** of the current stack, not a named policy. Change Orders can apply a different formula.

Labour Engine (ADR-029) already established the pattern: organization-owned versioned standards + immutable estimate snapshots. Pricing needs the same durability for commercial policy.

Historical estimates show more than one contingency treatment (internal reserve not in customer price; customer-priced contingency included in pre-tax sell). Those examples must not become a hidden universal formula.

## Decision

1. Each organization owns a **versioned, supersedable pricing policy** record (conceptual `OrganizationPricingPolicy`): method type, rates, overhead treatment, profit treatment, **contingency source/purpose and pricing treatment**, tax/jurisdiction treatment, effective dates, approval status (`ORG-APPROVED` vs provisional), provenance, `approved_by` / `approved_at`.
2. Contingency architecture **separates**:
   - **Source / purpose** (why the reserve exists — org-defined; not a silent cost multiplier).
   - **Customer visibility:** `INTERNAL_RESERVE` (tracked internally, not customer priced) | `CUSTOMER_PRICED` | `NOT_APPLIED`.
   - **Pricing treatment** (required when customer-priced): `INCLUDED_IN_MARGIN_BASIS` (participates in the named method’s cost/basis before GM or markup) | `ADDED_AFTER_BASE_PRICING` (added after the named method computes base pre-tax sell).
   The system **must know** whether contingency participates in the pricing formula. No hidden default. No historical example is universal policy. ORG-001 selects treatment through human-approved org policy.
3. Overhead and profit treatment are **explicit org-policy fields**. They must not be equated with gross margin. `TRUE_GROSS_MARGIN` must not silently re-apply `COST_PLUS_MARKUP_STACK` compounding. `COST_PLUS_MARKUP_STACK` may retain line markup, then overhead, then compounded profit as the **named** legacy method.
4. Each `EstimateVersion` that uses the engine must receive an **immutable pricing snapshot** (conceptual `EstimatePricingSnapshot`) sufficient to reproduce: policy type and version; Direct Cost basis; target GM or markup parameters; legacy stack parameters where applicable; contingency source/visibility/pricing treatment; overhead treatment; profit treatment; Pricing Posture snapshot; Execution Risk snapshot/reference; tax policy/rate; resolution source; override reason; provenance.
5. **Resolution order** (first match), reconciled with M011 (`EstimateVersion.commercial_context_id` pins context; it does not currently select rates): estimate-specific approved override → optional commercial-context policy/version pointer → active ORG-APPROVED org policy → organization default → CalibAi BASELINE (flagged, requires review, never silent Brayman values) → provisional legacy/current-stack fallback requiring review.
6. **Change Orders** linked to an estimate version **inherit that version’s pricing snapshot**. A different method/rate requires a separately approved override with reason. Do **not** treat `EstimateVersion.overhead_percent` as `ChangeOrder.markup_percent` without explicit policy semantics. **Do not recalculate or rewrite historical Change Orders.**
7. AI may explain and suggest **candidates**. AI must not approve policy, set ORG-APPROVED, or alter snapshots.
8. Field inventory is **not** frozen as exact columns. Implementation must use the **minimum durable set** needed for (1)–(7); do not invent unused columns.

## Alternatives Considered

- **Fold persistence into ADR-025 only** — Rejected. ADR-025 is the method-math decision; snapshots/resolution/contingency treatment are a second durable decision (same split as ADR-029 vs labour math identities).
- **Continue storing only percents on `EstimateVersion`** — Rejected as the long-term contract. Percents without method identity allow 15% markup to be re-read as 15% GM.
- **Re-resolve live org policy on every open** — Rejected for issued/accepted versions (Constitution Article 5).
- **Change Orders always use current org policy** — Rejected as the default; causes base bid vs CO economics drift. Inherit snapshot unless overridden.
- **Customer-priced contingency always added after base pricing (outside margin basis)** — **Rejected as a universal rule.** Treatment must be explicit (`INCLUDED_IN_MARGIN_BASIS` vs `ADDED_AFTER_BASE_PRICING`).

## Consequences

- Implementation will require an additive migration (Rule 7) when FG-009 is executed.
- Legacy versions can be snapshotted as `COST_PLUS_MARKUP_STACK` from existing columns without changing totals.
- Four-output package can later read one snapshot; customer outputs still must not expose internal mechanics.
- Contingency and overhead cannot silently collapse into Direct Cost or into the GM rate.

## Module Ownership Impact

Pricing Engine owns policy records and snapshot contract. Estimating hosts the estimate version FK. Proposals continue to own customer commercial snapshots (ADR-002) and must not contradict the estimate pricing snapshot. Project Controls own Change Order lifecycle and must consume the snapshot.

## Data Ownership Impact

Organization-scoped policy and snapshots. No cross-org pooling. Historical ingestion tables remain evidence-only. Historical Change Orders remain historical facts.

## Migration Impact

**Deferred.** Additive when implementation is authorized. None in this governance pass.

## Testing Impact

Deferred to FG-009 implementation: resolution order, snapshot immutability, org isolation, CO inheritance, contingency treatment variants, legacy classification without recalc, historical CO non-rewrite.

## Documentation Impact

FG-009; pricing-engine architecture; ADR index.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel | **2026-08-29** — ACCEPT (subject to contingency source vs pricing-treatment clarification, adopted herein) |
| ChatGPT review | Accepted with FG-009 architecture and contingency clarification | 2026-08-29 |
| Cursor implementation note | **Accepted** as documentation. **No product code or migration.** Implementation not authorized. | 2026-08-29 |
