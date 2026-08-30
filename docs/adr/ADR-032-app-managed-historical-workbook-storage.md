# ADR-032 — App-Managed Immutable Historical Workbook Storage

| Field | Value |
|-------|--------|
| Title | ADR-032: App-Managed Immutable Historical Workbook Storage / Source Custody |
| Status | **Accepted** (governance; implementation under [FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) **not started**) |
| Date | 2026-08-30 |
| Related | [FG-006](../feature-gates/FG-006-historical-estimate-ingestion-phase-b.md) · [FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) · [historical-estimate-ingestion-architecture.md](../architecture/historical-estimate-ingestion-architecture.md) |

## Context

FG-006 Phase B ingested 20 Brayman workbooks from a **legacy controlled corpus** outside Git (`~/Desktop/CalibAi Historical Estimates`). `HistoricalSourceWorkbook` stores SHA-256, size, original filename, and a `source_file_path` pointer to that machine path. Bytes are not in the database and are not in app-managed storage.

FG-013 productizes office **UPLOAD PREVIOUS ESTIMATES**. Treating Joel’s Desktop folder as the product source of record would not scale, would not isolate tenants, and would not give the application recoverable custody of uploaded bytes.

Plan Intelligence already stores plan PDFs under private instance storage with SHA-256 identity and archive-over-delete. Historical uploads need an equivalent **workbook** custody rule without moving the existing Desktop corpus.

## Decision

### 1. Two custody regimes (do not conflate)

| Regime | What | Disposition |
|--------|------|-------------|
| **Legacy controlled corpus** | Existing ORG-001 Desktop evidence (`~/Desktop/CalibAi Historical Estimates`) and already-ingested FG-006 rows that point at it | **Leave in place.** Do **not** move, recopy, delete, rewrite, or path-mutate those files or their `source_file_path` values merely to conform to productized storage. |
| **Productized upload custody** | Workbooks received through the FG-013 office upload UX | App-managed private durable storage. Immutable source evidence. |

Git must **never** contain customer workbook bytes (legacy or productized).

### 2. Productized storage

New productized historical uploads **shall** use app-managed private durable storage.

Raw uploaded workbook bytes are **immutable source evidence**. They must:

- remain **outside Git**
- be **organization-scoped**
- live in **private app-managed storage**
- retain **SHA-256** identity
- retain **original filename** as metadata (not as a trusted filesystem path)
- never be **silently overwritten** or **silently replaced**
- be **recoverable** from durable metadata
- follow **archive / supersession** rather than silent deletion

A storage pattern substantially equivalent to:

```text
instance/historical_uploads/<organization_id>/<controlled-content-name>
```

is acceptable. Exact safe naming is an implementation detail (for example SHA-256 plus extension, or a generated id plus recorded original filename). **User filenames must not become trusted paths.**

### 3. Identity and immutability

- Compute SHA-256 **before** authoritative custody.
- Same organization + SHA-256 + ingestion version remains **idempotent** (FG-006 unique constraint). Duplicate uploads must not write a second byte object as if it were new content.
- Replacing bytes in place is **prohibited**. Archive or supersede the metadata record; do not mutate stored bytes.

### 4. Legacy corpus protection

The existing 20-workbook ORG-001 corpus must **not** be moved, recopied, deleted, rewritten, or path-mutated merely to conform to this architecture. FG-006 tests and UAT that read the Desktop folder remain valid. Productized uploads are an **additional** custody path.

### 5. Scope

This ADR does **not** authorize pooling customer workbooks across organizations, putting bytes in Git, a durable `UploadBatch` table, MONITOR/LEARN, or implementation without an FG-013 implementation prompt.

## Alternatives Considered

- **Keep Desktop folder as product SoR** — Rejected: not tenant-safe, not recoverable on another machine, not a product custody model.
- **Copy the 20-file corpus into instance storage now** — Rejected: unnecessary mutation of protected UAT evidence.
- **Store workbook bytes in SQLite BLOBs** — Rejected for V1: Plan Intelligence uses filesystem; hashes + paths are sufficient; BLOBs are a later option if evidence warrants.
- **Durable UploadBatch to own storage** — Rejected: multi-file UX does not require a batch entity ([FG-013](../feature-gates/FG-013-contractor-calibration-onboarding-historical-upload-ux.md)).

## Consequences

**Positive:** Product uploads have recoverable, org-scoped, immutable custody analogous to plan PDFs, without disturbing the sealed Desktop corpus.

**Negative:** Two path regimes exist until a later (separately gated) optional consolidation. Implementations must not “normalize” legacy paths as a drive-by.

## Module Ownership Impact

Historical ingestion / review owns productized workbook files and their metadata. Plan Intelligence continues to own plan PDFs. No ownership transfer.

## Data Ownership Impact

Productized bytes are organization-owned source evidence (ORG-HISTORICAL lineage). They are not ORG-APPROVED standards and not ORG-ACTUAL performance.

## Migration Impact

**Deferred** to the FG-013 **implementation** prompt. Additive schema for stored-name / archive fields and upload-attempt rows is authorized by FG-013; **this ADR does not create a migration.**

## Testing Impact

Future FG-013 tests must prove: bytes not in Git; org isolation; SHA identity; no in-place overwrite; legacy Desktop corpus untouched.

## Documentation Impact

This ADR; FG-013; historical-ingestion architecture; ADR index; current-state; session-handoff; chat-workflow-log.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | FG-013 complete governance pass | 2026-08-30 |
| Cursor implementation note | Documentation / governance only. FG-013 **not implemented**. No schema, migration, or product code. | 2026-08-30 |
