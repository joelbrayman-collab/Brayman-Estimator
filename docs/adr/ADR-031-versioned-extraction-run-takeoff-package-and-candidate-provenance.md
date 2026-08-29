# ADR-031 — Versioned Extraction Run, Reviewed Take-off Package, and Candidate Provenance

| Field | Value |
|-------|--------|
| Title | ADR-031: Versioned AI Extraction Run, Reviewed Take-off Package, and Candidate Provenance |
| Status | **Accepted** (2026-08-29; FG-010 / M012) |
| Date | 2026-08-29 |
| Related | [ADR-005](ADR-005-ai-takeoff-traceability.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) · [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) · [ADR-011](ADR-011-ai-confidence-threshold-policy.md) · [ADR-012](ADR-012-plan-document-version-ownership.md) · [ADR-027](ADR-027-pdf-rendering-and-normalized-coordinate-system.md) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) · [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) · [ai-takeoff architecture](../architecture/ai-takeoff-quantity-extraction-foundation.md) |

## Context

ADR-005 requires a citation bundle. ADR-007 assigns take-off versions to Plan Intelligence. Neither specifies the **durable records** for an extraction attempt, a reviewable candidate, and an immutable approved package, nor how reruns and drawing revisions must not float prior approvals.

FG-008/FG-009 already established the product pattern: append-only runs/events, human review, immutable snapshots (`EstimateLabourSnapshot`, `EstimatePricingSnapshot`). Take-off needs the same pattern in PLAN.

## Decision

*(Accepted — 2026-08-29 with FG-010.)*

1. Plan Intelligence owns three additive record kinds: **extraction run**, **take-off candidate**, **take-off package** (plus frozen package items).
2. Geometry uses the **existing** ADR-027 normalized `[0,1]` coordinate system. No second coordinate model.
3. An approved take-off package is **immutable**. Reruns and new drawing revisions create **new** runs/packages; they do not mutate approved packages.
4. AI candidate count, human-reviewed count, approved package quantity, and estimate line quantity are **distinct**. Package approval does not insert estimate lines (ADR-006).
5. All take-off rows include `organization_id` and `project_id` and fail closed across orgs (ADR-028).
6. Audit is append-only via extended `PlanAuditEvent` event types, not a parallel log.
7. **COUNT is dimensionless.** A count candidate / reviewed count must **not** require dimensional scale merely to count discrete objects. Future FG-010 implementation **may** permit `measurement_type = count` (AI candidates and, where the implementation prompt includes it, manual count) **without** confirmed dimensional calibration. This authorization applies **only** to count. Linear, polyline, area, and perimeter **must** continue to fail closed unless the governing scale/viewport calibration is valid (ADR-026). Current M010 code still requires calibration even for manual count — that is a **narrow authorized correction** for the FG-010 implementation prompt, not a weakening of dimensional rules.
8. Provider/model/version/config hash are stored; schema is vendor-agnostic. This ADR does **not** select an external AI provider. **Real external AI provider integration is not authorized** by FG-010 approval.
9. This ADR does **not** govern estimate insertion, pricing, or labour standards.

## Alternatives Considered

- Reuse `PlanMeasurement` as AI candidates — Rejected (manual measurement SoR would mix with AI suggestions; current M010 count still requires calibration until the authorized COUNT correction).
- Reuse `ProcessingAttempt` as the extraction run — Rejected (text-index attempts are a different pipeline).
- Auto-insert approved package into Estimating — Rejected (ADR-006; Phase D).
- New module “AI Take-off” — Rejected (Rule 1; FG-005 already kept measurement inside Plan Intelligence).

## Consequences

Positive: citations, rerun safety, PLAN/PRICE split, org isolation. Negative: more entities for reviewers; mapping deferred.

## Module Ownership Impact

Plan Intelligence owns runs, candidates, packages. Estimating unchanged until a later mapping gate. Labour Engine and Pricing Engine unchanged.

## Data Ownership Impact

New additive tables; existing plan/sheet/measurement tables not rewritten. Historical approved packages versioned, not overwritten.

## Migration Impact

Deferred until a **separate** FG-010 implementation prompt. Additive only. This ADR acceptance does not generate a migration.

## Testing Impact

See FG-010 test plan. None in this documentation pass.

## Documentation Impact

FG-010; take-off architecture; Plan Intelligence module; ADR index; roadmap/handoff.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved with FG-010 | 2026-08-29 |
| ChatGPT review | Approved with FG-010 | 2026-08-29 |
| Cursor implementation note | Docs/governance only (2026-08-29). Product implementation **not** authorized by this acceptance. Real external AI provider integration **not** authorized. |
