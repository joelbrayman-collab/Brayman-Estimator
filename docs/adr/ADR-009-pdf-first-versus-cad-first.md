# ADR-009 — PDF-First versus CAD-First Ingestion

| Field | Value |
|-------|--------|
| Title | ADR-009: PDF-First versus CAD-First Ingestion |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) |

## Context

Builders receive PDF plan sets routinely; DWG/DXF capability is valuable but costly. Sequencing affects POC success.

## Decision

*(Proposed)* **PDF-first.** Phases A–F target PDF (searchable first, scanned later). **CAD (DWG/DXF) is Phase G** and requires a separate Feature Gate after PDF take-off is proven. Do not block PDF POC on CAD viewers or native CAD parsers.

## Alternatives Considered

- CAD-first — Rejected for time-to-learning and dependency risk.
- PDF and CAD in parallel from day one — Rejected as scope expansion.

## Consequences

Positive: faster validation. Negative: delayed CAD users; must communicate roadmap honestly.

## Module Ownership Impact

Plan Intelligence ingestion adapters ordered PDF → later CAD.

## Data Ownership Impact

None immediate.

## Migration Impact

None now.

## Testing Impact

POC tests use PDF fixtures only.

## Documentation Impact

Roadmap Phases A–G; Plan Intelligence architecture.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | No implementation in this documentation sprint | |
