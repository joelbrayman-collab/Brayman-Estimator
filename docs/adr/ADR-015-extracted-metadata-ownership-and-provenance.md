# ADR-015 — Extracted Metadata Ownership and Provenance

| Field | Value |
|-------|--------|
| Title | ADR-015: Extracted Metadata Ownership and Provenance |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-005](ADR-005-ai-takeoff-traceability.md) · [ADR-006](ADR-006-human-approval-before-estimate-insertion.md) · [ADR-011](ADR-011-ai-confidence-threshold-policy.md) · [ADR-013](ADR-013-document-intelligence-layer-boundary.md) · [document-intelligence.md](../architecture/document-intelligence.md) |

## Context

Document Intelligence will extract and classify metadata (page text, suggested sheet numbers, disciplines, OCR later, AI later). Without clear ownership and provenance rules, implementers may overwrite human corrections, discard raw extractor output, or treat confidence as authority to change commercial records.

## Decision

*(Proposed)*

1. **Plan Intelligence owns** all Document Intelligence extraction outputs: metadata fields on Page/Sheet, processing attempts, processing results, and preserved raw extractor payloads.
2. **Human-corrected values** on Sheet/Page (sheet number, title, discipline, drawing status, scale, etc.) are the **product source of truth** for downstream take-off identity. Extractor suggestions never silently overwrite human corrections unless the user explicitly re-applies suggestions.
3. Each **Processing Attempt** records: target (document/page/sheet), extractor/toolchain name + version, started/finished timestamps, status (`queued` / `running` / `succeeded` / `failed` / `cancelled`), and error summary.
4. Each successful attempt stores a **Processing Result** that preserves **raw extraction output** (JSON or equivalent) immutably for that attempt, plus normalized fields derived from it.
5. Reprocessing creates a **new** attempt/result; it does not mutate prior raw payloads. Idempotency keying may skip duplicate work for the same `(target, extractor_version, content_checksum)` when configured.
6. **Confidence values** annotate suggestions only. They never authorize estimate create/update/delete (ADR-006/011).
7. Estimating does **not** own extraction metadata and must not store plan file bytes or raw extractor blobs.

## Alternatives Considered

- **Overwrite sheet fields in place with latest extraction** — Rejected (destroys human corrections and audit).  
- **Discard raw output; keep normalized fields only** — Rejected (blocks debugging, re-normalization, and provenance).  
- **Estimating owns commercialized metadata** — Rejected (ADR-007 ownership).

## Consequences

Positive: auditable reprocessing; safe human review; AI/OCR swappable behind versioned attempts.  
Negative: storage growth for raw payloads; retention policy needed later.

## Module Ownership Impact

Plan Intelligence (Document Intelligence layer) gains processing attempt/result ownership. Estimating unchanged.

## Data Ownership Impact

Raw and normalized extraction outputs are Plan Intelligence historical records.

## Migration Impact

Deferred to Feature-Gated implementation (recommended starting M007). Additive tables only.

## Testing Impact

Future: reprocess preserves prior raw results; human corrections not clobbered; failed attempts leave documents intact.

## Documentation Impact

FG-003; document-intelligence architecture; M006 readiness report.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M006 | |
