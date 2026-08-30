# Feature Gate FG-013: Contractor Calibration Onboarding / Historical Estimate Upload UX

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-013` |
| Feature Name | Contractor Calibration Onboarding / Historical Estimate Upload UX |
| Status | **DRAFT FOR JOEL REVIEW** — **IMPLEMENTATION NOT AUTHORIZED** |
| Prerequisite | [FG-006](FG-006-historical-estimate-ingestion-phase-b.md) **APPROVED, IMPLEMENTED & VERIFIED** |
| Related | [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR not in this gate) · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) |
| Date | 2026-08-30 |
| Implementation | **Not started.** Do not implement uploads, schema, or authentication under this draft. |

## Purpose

Productize an office **UPLOAD PREVIOUS ESTIMATES** workflow on the existing FG-006 ingestion/review engine. Historical evidence must never silently become ORG-APPROVED standards.

This document is **not** a complete approved Feature Gate. Remaining twelve-question answers, schema/ADR decisions, and implementation authority remain **open** except where a subsection is marked **LOCKED**.

---

## LOCKED — Multi-file / folder upload (2026-08-30)

Joel decision. This invariant is **binding** on any later FG-013 approval or implementation prompt. It does **not** authorize implementation by itself.

### Product rule

The contractor / office user must **not** be required to upload historical estimates one at a time.

FG-013 must support a **single user action** for loading multiple historical estimates.

### Required UX

- Select **multiple** supported estimate workbooks at once.
- Drag-and-drop **multiple** supported estimate workbooks at once.
- Where supported by the browser / client implementation, allow selection or drag-and-drop of a **folder** containing estimate workbooks and process the supported files within it **individually**.
- If the browser / client cannot offer folder pick or folder drop, fall back to multi-file select and multi-file drop. Folder support is required **where the client can provide it**; lack of folder APIs must not force a one-file-at-a-time workflow.
- Guidance may recommend approximately **20–25** representative recent estimates. There is **no** fixed file-count requirement. Do not require exactly 25.

### Processing model

Each workbook remains an **independent evidence / transaction unit**.

```text
ONE USER UPLOAD ACTION
  → MANY WORKBOOKS
  → INDIVIDUAL PER-FILE VALIDATION / INGESTION / RESULT
  → COMBINED USER RESULTS SUMMARY
```

A failed, unsupported, duplicate, or quarantined workbook must **not** prevent the remaining valid workbooks from being processed.

### Durable batch vs UX (do not conflate)

| Decision | Meaning |
|----------|---------|
| **NO durable `UploadBatch`** | Database architecture: do not create a batch table merely to support multi-file or folder UX. |
| **YES multi-file / folder UX** | Product UX: one user action may submit many workbooks. |

`NO DURABLE UploadBatch` refers **only** to database architecture. It does **not** mean files must be uploaded individually. Do **not** create a durable `UploadBatch` merely to support multi-file or folder UX.

Request-scoped (or equivalent ephemeral) combined results are sufficient for the summary. Per-file durable records remain `HistoricalSourceWorkbook` / `HistoricalEstimate` (and any later additive attempt rows, if separately approved).

### Non-goals of this locked section

- Does not authorize FG-013 implementation.
- Does not decide schema / migration / storage ADR.
- Does not authorize authentication, self-serve multi-org onboarding, industry benchmarking, actuals, MONITOR, LEARN, or Phase D.
- Does not require a durable batch entity.

---

## Feature Gate answers (PROPOSED — not approved except the locked UX above)

The 2026-08-30 architecture assessment recommended office upload on FG-006, quarantine for unknown layouts, no auto calibration-candidate creation, and office upload before auth / self-serve after auth. Those recommendations are **not** converted into approved gate answers by this draft except the locked multi-file / folder UX.

| # | Question | Draft answer (proposed) |
|---|----------|-------------------------|
| 1 | What problem does this solve? | Office users cannot load a representative historical corpus without admin/dev `ingest_workbook_file` against an external folder. |
| 2 | Who is the user? | Office estimator / Joel on the unauthenticated office app (self-serve contractor onboarding requires auth later). |
| 3 | Which module owns it? | Historical ingestion / review (`app/routes/historical_estimates.py`, FG-006 models/services). Labour Engine and Pricing Engine are not owners. |
| 4 | What data does it own? | No new commercial SoR. Reuses FG-006 historical evidence. App-managed source bytes TBD. |
| 5 | What data does it reference? | `organizations`; FG-006 historical tables; must not write labour/pricing standards. |
| 6 | What may it change? | Office upload UX; per-file ingest loop; results summary. Schema only if a later approved prompt says so. |
| 7 | What must it not change? | FG-006 adapters as the ingestion engine (extend, do not duplicate); MONITOR; LEARN auto-writes; FG-008/009 standards; Phase D; auth. |
| 8 | What are the acceptance criteria? | Include the **LOCKED** multi-file / folder UX. Remaining criteria TBD when Joel approves the gate. |
| 9 | What tests are required? | Multi-file mixed outcomes; folder expansion where testable; one failure does not block others. Details TBD at approval. |
| 10 | What documentation must be updated? | This gate; current-state; session-handoff; chat-workflow-log; historical ingestion docs as needed. |
| 11 | Does it require an ADR? | **Proposed YES** (app-managed byte custody vs FG-006 Desktop folder). Not created. Not approved by this draft. |
| 12 | Does it require a database migration? | **UNDETERMINED.** No durable `UploadBatch`. Failed-attempt durability TBD. **No migration in this documentation pass.** |

---

## Explicit non-goals (until a later approved implementation prompt)

- Implement uploads or folder picking in product code
- Create `UploadBatch` or any schema/migration
- Create a storage ADR
- Authentication / self-serve onboarding
- Industry benchmarking, actuals, profitability, MONITOR, LEARN, Phase D
- Auto-approve organization standards from uploaded files
