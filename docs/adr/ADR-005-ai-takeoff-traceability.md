# ADR-005 — AI-Generated Take-Off Traceability

| Field | Value |
|-------|--------|
| Title | ADR-005: AI-Generated Take-Off Traceability |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) |

## Context

AI-assisted quantity extraction can invent or misread quantities. Constitution Articles 5–6 and Rules 5–6 require recoverable history for financially significant numbers.

## Decision

*(Proposed)* Every AI-generated take-off quantity must persist: model/version id, confidence, source citation (file, page, sheet, region), raw candidate value, and full audit trail of human adjustments. AI output is never the sole system of record for commercial quantities.

## Alternatives Considered

- Store only final numbers — Rejected (not auditable).
- Log only in application logs — Rejected (not durable product records).

## Consequences

Positive: defensibility and debugging. Negative: more storage and UI for citations.

## Module Ownership Impact

Plan Intelligence owns take-off candidates and citations; Estimating owns estimate lines after approved mapping.

## Data Ownership Impact

Take-off audit events are append-only.

## Migration Impact

Deferred until Phase A+ Feature Gate (new tables).

## Testing Impact

Tests must prove citation required before approval; adjustments audited.

## Documentation Impact

Plan Intelligence architecture; roadmap Phases C–D.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in this documentation sprint | |
