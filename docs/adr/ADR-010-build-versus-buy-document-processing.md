# ADR-010 — Build versus Buy for CAD and Document-Processing Components

| Field | Value |
|-------|--------|
| Title | ADR-010: Build versus Buy for CAD and Document-Processing Components |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · [supplier architecture](../architecture/supplier-catalogue-inventory-pricing.md) |

## Context

PDF rendering, OCR, CAD parsing, and measurement UX are specialized. Building everything in-house can stall the product; buying can create lock-in and data-residency issues.

## Decision

*(Proposed)*

1. Before Phase B/C implementation spend, Joel reviews a short **build-vs-buy** options memo for: PDF render/viewer, OCR (if scanned), measurement overlay, and (later) CAD.
2. Default bias for POC Phase A–B: **minimize new dependencies**; use simplest PDF storage + metadata first; add viewers/OCR only under Feature Gate.
3. No dependency may be added to `requirements.txt` without Feature Gate + this ADR acceptance for that component class.
4. Prefer vendors that allow **export of citations/coordinates** into Estimator-owned records (ADR-005).

## Alternatives Considered

- Always build — High risk of delay.
- Always buy full take-off suite — Risk of opaque quantities and weak ownership.

## Consequences

Positive: conscious spend. Negative: decision latency before Phase B.

## Module Ownership Impact

Plan Intelligence integrates adapters; Estimating remains independent.

## Data Ownership Impact

Estimator-owned DB remains system of record for quantities/citations.

## Migration Impact

None until a component is chosen.

## Testing Impact

Adapter contract tests when a buy decision ships.

## Documentation Impact

Update this ADR with the chosen option when decided.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No dependencies or code in this documentation sprint | |
