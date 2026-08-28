# ADR-024 — LEARN Recommendation Boundary

| Field | Value |
|-------|--------|
| Title | ADR-024: LEARN Recommendation Boundary |
| Status | **Accepted** (boundary; no ML/recommendation implementation in CAR-001) |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [pricing-policy.md](../pricing-policy.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) · [ADR-017](ADR-017-sheet-metadata-suggestion-and-review-workflow.md) |

## Context

CalibAi’s learning principle is that every project makes the next project smarter. Historical actuals and AI recommendations must never silently rewrite approved pricing or estimating policy.

## Decision

1. LEARN **consumes** historical project results and may produce **review-gated** intelligence (suggestions).
2. LEARN **must not silently modify**: pricing policy, cost library, approved estimates, or historical actuals.
3. **Human approval remains authoritative** before any LEARN output becomes estimating/pricing SoR.
4. Early V1 may capture structured project results only. Sophisticated recommendation/ML is later and separately Feature-Gated.
5. No LEARN/ML implementation in CAR-001.

## Alternatives Considered

- **Auto-update cost library from job actuals** — Rejected: silent policy/price mutation.
- **LEARN owns the cost book** — Rejected: Estimating owns `cost_items` / assemblies.
- **Confidence threshold auto-applies factors** — Rejected: same class as ADR-011 (thresholds gate review UX, not write).

## Consequences

**Positive:** Institutional memory can grow without corrupting the bid book.  
**Negative:** LEARN value depends on later review UX and MONITOR actuals.

## Module Ownership Impact

LEARN is **not** assigned a top-level module document in CAR-001. It must not take ownership of Estimating masters or pricing-policy.md.

## Data Ownership Impact

Historical actuals remain owned by their source modules (BUILD/MONITOR when they exist). LEARN reads; it does not become SoR by inference.

## Migration Impact

None in CAR-001.

## Testing Impact

None in CAR-001.

## Documentation Impact

CAR-001; pricing-policy.md (cross-link); roadmap.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-28 |
| ChatGPT review | Reconciliation reviewed by Joel | 2026-08-28 |
| Cursor implementation note | Docs/governance only (CAR-001 adoption) | 2026-08-28 |
