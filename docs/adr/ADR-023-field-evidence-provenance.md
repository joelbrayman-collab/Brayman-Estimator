# ADR-023 — Field Evidence Provenance

| Field | Value |
|-------|--------|
| Title | ADR-023: Field Evidence — Original versus Derived Records |
| Status | **Accepted** (provenance rules; no voice/photo implementation in CAR-001) |
| Date | 2026-08-28 |
| Related | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) · [ADR-015](ADR-015-extracted-metadata-ownership-and-provenance.md) · [ADR-017](ADR-017-sheet-metadata-suggestion-and-review-workflow.md) · [ADR-020](ADR-020-build-module-boundary.md) |

## Context

Future voice and photo capture must remain auditable. Plan Intelligence already established: original payloads preserved, processing attempts/results, human confirmation as system of record, archive rather than silent overwrite (ADR-015/017; M007 models).

## Decision

1. Future voice/photo (and similar) field capture must preserve **ORIGINAL OBSERVATION** plus **SEPARATE DERIVED STRUCTURED RECORDS**.
2. Reuse Plan Intelligence provenance principles: original preserved; checksum/provenance where applicable; derived AI output separate; **human confirmation before** authoritative business records; archive/version rather than silent overwrite.
3. Generative AI must not modify, replace, or approximate an approved original master (continuity protocol protected-asset rule).
4. Do not overload `PlanDocument` (PDF-specific) for photos without a later ADR. A sibling field-evidence record is the expected extension when Feature-Gated.
5. **No voice or photo implementation** in CAR-001. Voice AI and photo AI remain separately Feature-Gated and outside V1.

## Alternatives Considered

- **Store only AI transcription/labels, discard original** — Rejected: loses evidence.
- **Write derived facts onto the original file/row** — Rejected: silent mutation.
- **Auto-create labour/material records from voice without confirmation** — Rejected: same class of control as ADR-006/017.

## Consequences

**Positive:** Field intelligence can be added later without corrupting evidence.  
**Negative:** Capture pipelines are more records than a single “note” blob.

## Module Ownership Impact

BUILD owns the field-observation event when implemented (ADR-020). Plan Intelligence keeps plan PDFs. Derived commercial records still require the owning module’s confirmation rules (Estimating must not be auto-written).

## Data Ownership Impact

Original observation vs derived records are distinct. Human-confirmed derived records become SoR for those facts.

## Migration Impact

None in CAR-001.

## Testing Impact

None in CAR-001.

## Documentation Impact

CAR-001; modules/build.md.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-28 |
| ChatGPT review | Reconciliation reviewed by Joel | 2026-08-28 |
| Cursor implementation note | Docs/governance only (CAR-001 adoption) | 2026-08-28 |
