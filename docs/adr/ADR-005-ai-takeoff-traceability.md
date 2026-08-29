# ADR-005 — AI Take-Off Source Traceability

| Field | Value |
|-------|--------|
| Title | ADR-005: AI Take-Off Source Traceability |
| Status | **Accepted** (2026-08-29; FG-010 / M012) |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · [ADR-031](ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) · [FG-010](../feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) · Milestone 004 |

## Context

AI-assisted and manual take-off quantities must remain commercially and legally defensible. Constitution Articles 5–6 and Rules 5–6 require recoverable history. Milestone 004 requires every estimate quantity from Plan Intelligence to be traceable to file, sheet, page, revision, region, confidence, reviewer, approval time, and corrections.

## Decision

*(Accepted — 2026-08-29 with FG-010.)*

1. Every take-off quantity persists a **citation bundle**: uploaded file id, drawing set, revision, sheet number/name, page index, region geometry, extraction method, AI model/version (if AI), confidence, reviewer, approval timestamp, and correction history.
2. Citations are **first-class data**, not optional comments or log-only events.
3. When quantities are inserted into an estimate, the insert audit retains a snapshot link to that citation bundle.
4. AI output is never the sole system of record for commercial quantities.

## Alternatives Considered

- Store only final numbers — Rejected (not auditable).
- Log only in application logs — Rejected (not durable product records).

## Consequences

Positive: defensibility and debugging. Negative: more storage and UI for citations.

## Module Ownership Impact

Plan Intelligence owns take-off candidates and citations; Estimating owns estimate lines after approved mapping.

## Data Ownership Impact

Take-off audit events and citations are append-only / versioned per package rules.

## Migration Impact

Deferred until Phase A+ Feature Gate (new tables).

## Testing Impact

Tests must prove citation required before approval; adjustments audited; insert retains link.

## Documentation Impact

Plan Intelligence architecture §5; module doc; Milestone 004 readiness report.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Approved with FG-010 | 2026-08-29 |
| ChatGPT review | Approved with FG-010 | 2026-08-29 |
| Cursor implementation note | Docs/governance only (2026-08-29). Product implementation not authorized by this acceptance. |

---

## 2026-08-29 acceptance (FG-010 / M012)

M012 citations attach to `TakeoffExtractionRun`, `TakeoffCandidate`, and `TakeoffPackage` / `TakeoffPackageItem`. Geometry uses ADR-027 normalized `[0,1]`. Future estimate-line citation linkage remains **Phase D**. This ADR does **not** imply M012 creates estimate lines.
