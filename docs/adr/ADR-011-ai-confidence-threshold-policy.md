# ADR-011 — AI Confidence Threshold Policy

| Field | Value |
|-------|--------|
| Title | ADR-011: AI Confidence Threshold Policy |
| Status | **Accepted** (2026-08-29; FG-010 / M012) |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · ADR-005 · ADR-006 · Milestone 004 |

## Context

AI detections will vary in quality. Without a confidence policy, reviewers may rubber-stamp low-quality candidates or the product may be tempted toward auto-insert. Milestone 004 requires a documented threshold policy. (Requested in Task 7 as “ADR-008”; **ADR-008 is already assigned** to Supplier Price Snapshotting, so this decision is **ADR-011**.)

## Decision

*(Accepted — 2026-08-29 with FG-010.)*

1. Every AI-generated candidate exposes a numeric confidence and reason codes.
2. Joel sets initial numeric threshold(s) before Phase C implementation (placeholder until product sets values).
3. Candidates **below** threshold cannot be included in batch-approve; they require explicit per-item review (accept/adjust/reject).
4. Candidates **at or above** threshold may be batch-approved **only after** human initiates batch approve — never auto-inserted into estimates (ADR-006 still governs insertion).
5. Thresholds are configuration, versioned, and audited when changed.
6. Manual measurements are not blocked by AI thresholds.

## Alternatives Considered

- No thresholds; human reviews everything equally — Acceptable for tiny POC; insufficient as trades expand.
- Auto-insert above threshold — Rejected (conflicts with ADR-006).

## Consequences

Positive: focuses reviewer attention. Negative: threshold tuning required; false negatives increase manual work.

## Module Ownership Impact

Plan Intelligence owns confidence scoring and threshold config.

## Data Ownership Impact

Threshold version recorded on review/approval events.

## Migration Impact

Deferred to Feature-Gated Phase C+.

## Testing Impact

Below-threshold batch-approve blocked; above-threshold still requires human approve; insert still requires ADR-006 path.

## Documentation Impact

Plan Intelligence architecture §4; module risks; readiness report.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved with FG-010 | 2026-08-29 |
| ChatGPT review | Approved with FG-010 | 2026-08-29 |
| Cursor implementation note | Docs/governance only (2026-08-29). Product implementation not authorized by this acceptance. |

---

## 2026-08-29 acceptance clarification (FG-010 / M012)

Confidence is **advisory evidence only**. Human review is authoritative.

V1 stores numeric confidence `[0.0, 1.0]` plus an advisory band (`LOW` / `MEDIUM` / `HIGH`). Exact band cut-points are not universal commercial policy; if used for UI display they must be explicit/configured and provenance-visible.

**No confidence threshold may silently auto-approve a candidate.** Confidence never auto-accepts, never auto-creates an approved package, never auto-inserts an estimate quantity, and never auto-prices work. Batch-approve remains an explicit human command over listed items and still does not insert estimates (ADR-006).
