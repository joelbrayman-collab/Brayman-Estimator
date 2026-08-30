# Feature Gate FG-013: Contractor Calibration Onboarding / Historical Estimate Upload UX

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-013` |
| Feature Name | Contractor Calibration Onboarding / Historical Estimate Upload UX |
| Target Milestone | **None.** FG-013 is the governing identifier. Do not assign a new M0xx number. |
| Module | Historical ingestion / review (FG-006 engine). Labour Engine and Pricing Engine are **not** owners. |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT** |
| Architecture | Productize office upload UX on FG-006. App-managed immutable workbook custody ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**). Durable per-file upload attempts. **No** durable `UploadBatch`. |
| Related ADRs | [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md) **Accepted** · [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR **out of scope**) · [ADR-029](../adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted** (do not auto-write) · [ADR-030](../adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted** (do not auto-write) |
| Prerequisites | [FG-006](FG-006-historical-estimate-ingestion-phase-b.md) **APPROVED, IMPLEMENTED & VERIFIED**. FG-008–FG-012 **CLOSED / OPERATIONAL FOR UAT**. |
| Approved baseline | Product: `974136bb2ac7d2f61acf71b53f81a2ae55f132b1`. Alembic **current = head = `c5d6e7f8a9b0`**. Last recorded full suite **310 passed**. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| Implementation | **DONE** — office multi-file upload, ADR-032 custody, per-file attempts. Browser multi-file UAT **passed**. |
| Schema / Alembic | Additive revision **`c5d6e7f8a9b0`** (`historical_upload_attempts`). **Live current = head = `c5d6e7f8a9b0`.** Migration **VERIFIED APPLIED**; **not** applied by the 2026-08-30 reconciliation/UAT pass. |
| Storage ADR | [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** (productized path implemented; legacy Desktop corpus untouched) |
| Durable `UploadBatch` | **NO** |

This gate does **not** authorize authentication, Phase D, external AI, QuickBooks, MONITOR, LEARN, actuals, profitability, industry benchmarking, supplier integration, or a second `flask db upgrade`.

---

## Purpose

Office users must be able to **UPLOAD PREVIOUS ESTIMATES** (about 20–25 representative recent files as **guidance**, not a quota) so the organization accumulates **ORG-HISTORICAL** evidence for later calibration review.

Upload success is **HISTORICAL EVIDENCE LOADED** / **CALIBRATION REVIEW READY**. It is **not** COST MODEL COMPLETE and must **not** silently create ORG-APPROVED standards.

---

## LOCKED — Multi-file / folder upload

**Do not weaken.** Users must **not** be required to upload estimates one at a time.

One user action may load many workbooks through:

- multi-select
- multi-file drag-and-drop
- folder select/drop **where the browser/client supports it** (then process supported files individually)

If folder APIs are unavailable, fall back to multi-file select and drop. Lack of folder APIs must not force a one-file-at-a-time workflow.

```text
ONE USER UPLOAD ACTION
  → MANY WORKBOOKS
  → INDIVIDUAL PER-FILE VALIDATION / INGESTION / RESULT
  → COMBINED USER RESULTS SUMMARY
```

Each workbook remains an **independent transaction / evidence unit**. A failed, duplicate, unsupported, or quarantined file must **not** prevent processing of the other valid files.

Recommended count: approximately **20–25** representative recent estimates. **No mandatory count.** Do not require exactly 25.

| UX | Database |
|----|----------|
| Multi-file / folder: **YES** | Durable `UploadBatch`: **NO** |

Do **not** create a durable `UploadBatch` merely because many files are chosen in one action. Combined results may be request-scoped. Durable facts are **per file**.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Office users cannot load a representative historical corpus without admin/dev `ingest_workbook_file` against an external folder. |
| 2 | Who is the user? | Office estimator / Joel on the **current unauthenticated office app**. Self-serve contractor onboarding is **not** this gate. |
| 3 | Which module owns it? | Historical ingestion / review (`app/routes/historical_estimates.py`, FG-006 models/services). Labour Engine and Pricing Engine must not gain ownership of uploads. |
| 4 | What data does it own? | Productized workbook bytes (ADR-032); additive **per-file upload-attempt/outcome** records; existing FG-006 historical evidence when ingest succeeds. |
| 5 | What data does it reference? | `organizations`; FG-006 historical tables. Must not write labour/pricing/material/subcontract **standards**. |
| 6 | What may implementation change? | Office upload UX; per-file ingest; app-managed storage; additive schema + **one** approved migration under the **implementation** prompt; review UI TIER_A wording; dedicated tests; governed docs. |
| 7 | What must it not change? | Legacy Desktop corpus paths/files; FG-006 adapter families as the parse engine (extend, do not duplicate); MONITOR/LEARN/BUILD actuals; FG-008/009 approved standards; Phase D; auth product; Git contents of customer bytes. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated upload/attempt/isolation/security tests; mixed multi-file outcomes; idempotent SHA; regressions (historical, labour, pricing); full suite before closure. |
| 10 | Documentation? | This gate; ADR-032; historical-ingestion architecture; feature-gate and ADR indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. |
| 11 | ADR required? | **Yes** — [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted**. |
| 12 | Migration? | **YES — one bounded additive revision `c5d6e7f8a9b0`.** Live apply **VERIFIED APPLIED** (provenance: prior interrupted live-migrate/UAT work; **not** this reconciliation pass). No destructive historical-data migration. No `UploadBatch` table. |

---

## Approved architecture

### Source custody ([ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md))

Productized uploads use **app-managed private durable storage**. Pattern equivalent to:

```text
instance/historical_uploads/<organization_id>/<controlled-content-name>
```

Exact naming is implementation detail. User filenames are metadata only — **not** trusted paths.

Bytes: outside Git; org-scoped; SHA-256 identity; original filename metadata; no silent overwrite/replace; recoverable from durable metadata; archive/supersede rather than silent delete.

**Legacy ORG-001 Desktop corpus:** do **not** move, recopy, delete, rewrite, or path-mutate.

### Durable per-file upload attempts

Approve the **smallest** additive structure needed so that “this file was received and then ingested / duplicate / unsupported / quarantined / failed” is durable provenance.

Potential facts (do not over-design; do not store secrets or uncontrolled exception dumps):

- organization
- original filename, extension, byte size
- SHA-256 where computed
- received timestamp
- actor string under the current office model
- outcome/status
- validation/failure reason
- `HistoricalSourceWorkbook` reference when applicable
- retained-storage reference where applicable
- minimal archive state if required

Each file owns its attempt/outcome. **No** durable batch parent.

### Schema / migration (implemented; live **VERIFIED APPLIED**)

| Authorization | Governance pass | Implementation pass | Reconciliation / UAT pass |
|---------------|-----------------|---------------------|---------------------------|
| SCHEMA CHANGE | YES — additive only | **`historical_upload_attempts`** | Unchanged |
| MIGRATION | YES — one bounded additive revision | **`c5d6e7f8a9b0`** (down_revision `b4c5d6e7f8a9`) | **Not re-run** |
| Live development/UAT apply | Must not | Not applied in implementation commit | **Already present** before reconciliation; verified `current = head = c5d6e7f8a9b0` |

Optional additive columns on `HistoricalSourceWorkbook` were **not** required. Storage path lives on the attempt and on `HistoricalSourceWorkbook.source_file_path` for ingested/quarantined productized files. No destructive rewrite of existing 20 ingested rows.

Implemented surfaces: `app/services/historical_ingestion/upload.py`, `app/services/historical_ingestion/storage.py`, `app/services/historical_ingestion/upload_validation.py`, `POST /historical-estimates/upload`, `app/models/historical_estimates.py` (`HistoricalUploadAttempt`).

### Formats

**V1 input:** `.xlsx` and `.xlsm` that are **valid OpenXML** only.

Do **not** support `.xls`, CSV, PDF, or other formats under FG-013.

Macros and formulas must **not** execute (retain FG-006 XML reader behaviour).

### Unknown layout — quarantine

**UNKNOWN / LOW-CONFIDENCE contractor workbook → QUARANTINE / REVIEW REQUIRED.**

Do **not** silently present generic Family E extraction as a confident successful parse. Valid OpenXML bytes may be preserved even when extraction is uncertain. No AI spreadsheet interpretation. No generalized mapper in FG-013. Known FG-006 adapters remain available for matching families.

### Security / size

Configurable per-file maximum: **25 MB** (bind to app config, analogous to plan upload).

Implementation must bind:

- extension allowlist
- OpenXML/ZIP structure validation (`xl/workbook.xml` or equivalent)
- compressed/uncompressed ZIP safety limits
- no macro execution; no formula execution
- safe filenames; path-traversal prevention
- `Content-Type` not trusted alone
- SHA-256 before authoritative custody
- private storage; organization isolation; fail-closed cross-org
- per-file failure isolation
- idempotent duplicate SHA (same org + hash + ingestion version)

### Office before auth

**Controlled office historical upload: AUTHORIZED TO PROCEED BEFORE AUTHENTICATION** under the existing office operating model.

This does **not** authorize contractor signup, public upload, self-service multi-tenant onboarding, or user accounts.

**SELF-SERVICE CONTRACTOR ONBOARDING: REQUIRES AUTHENTICATION.**

### Archive / delete

Raw evidence must not be silently overwritten or deleted after custody. Prefer **ARCHIVE / SUPERSEDE**. Do not alter the legacy Desktop corpus.

### TIER_A terminology

Do **not** use “Actual completed job” in a way that confuses ORG-HISTORICAL with ORG-ACTUAL.

Approved meaning:

> **TIER_A** = estimate associated with a completed project
> **TIER_A historical estimate evidence IS NOT ORG-ACTUAL project-performance evidence.**

UI wording may follow repository style; a concise equivalent is: **Estimate associated with a completed project**. Implementation must update review labels (including the FG-006 review form) accordingly. **Do not change that label in this governance pass** (product code prohibited here).

### Human review

Preserve FG-006 review. Upload success does **not** bypass review.

**ACCEPTED AS EVIDENCE** = accepted **ORG-HISTORICAL** evidence, **not** an approved operating standard.

### Calibration candidates — exclude

FG-013 **ends at reviewed historical evidence**. Do **not** automatically create `LabourCalibrationCandidate`, `ProductionRateStandard`, `DirectLabourCostRateStandard`, `OrganizationPricingPolicy`, or material/subcontract standards.

### User language

Approve: **UPLOAD PREVIOUS ESTIMATES**, **HISTORICAL EVIDENCE LOADED**, **CALIBRATION REVIEW READY**, **ACCEPTED AS EVIDENCE**.

Do **not** claim **COST MODEL COMPLETE** merely because files were uploaded.

### Material / subcontract / pricing

Historical material and subcontract rows remain **evidence only**. No calibration engines in FG-013.

Historical pricing/markup remains historical. Do **not** convert it into current `OrganizationPricingPolicy` or silently apply `TRUE_GROSS_MARGIN`.

### Out of scope

Industry benchmarking; ORG-ACTUAL; BUILD actuals; Project Gross Margin; MONITOR; LEARN; Phase D (**NOT AUTHORIZED**); external AI (**NOT AUTHORIZED**); QuickBooks.

### Tenant

All attempts, source workbooks, normalized evidence, and reviews are organization-scoped. Cross-org access **fails closed**. No customer-data pooling.

---

## Acceptance criteria

Implementation is incomplete until:

1. Multi-file and (where supported) folder UX; no one-at-a-time requirement; no mandatory file count.
2. App-managed immutable storage per ADR-032; legacy Desktop corpus untouched.
3. Durable per-file upload outcomes; **no** `UploadBatch`.
4. Additive schema + **one** implementation-authorized Alembic revision only.
5. `.xlsx` / `.xlsm` valid OpenXML only; unknown layout quarantined; no fake Family E confidence.
6. 25 MB configurable limit; ZIP/OpenXML security; no macro/formula execution.
7. Org isolation; per-file transaction/failure isolation; idempotent duplicate SHA.
8. Human review preserved; no standards auto-created.
9. TIER_A wording clarified as above.
10. Archive/supersession; no silent delete of custodied bytes.
11. No auth/self-service product; no benchmarking; no actuals/profitability; no Phase D/external AI.
12. Dedicated tests, listed regressions, and **full suite** before claiming closure.

---

## Explicit non-goals

- Implement in the 2026-08-30 **governance** pass (completed separately)
- Create the migration in the governance pass (created in the **implementation** pass as `c5d6e7f8a9b0`; live apply verified later, not by the implementation commit)
- Durable `UploadBatch`
- Moving the 20-file Desktop corpus
- Auto-approval of organization standards
- Self-serve multi-org onboarding / User model
- Industry norms, MONITOR, LEARN, BUILD actuals, QuickBooks, Phase D, real external AI

---

## Live migration provenance (2026-08-30 reconciliation)

**Do not claim the reconciliation/UAT pass performed `flask db upgrade`.**

| Fact | Record |
|------|--------|
| Revision | `c5d6e7f8a9b0` |
| Down revision | `b4c5d6e7f8a9` |
| Live current / head | `c5d6e7f8a9b0` / `c5d6e7f8a9b0` (one head) |
| When applied | **Already present** in the live development/UAT DB **before** the 2026-08-30 migration-state reconciliation session |
| Exact prior operator/timestamp | **Unknown** — prior FG-013 live-migrate/UAT work was interrupted |
| This reconciliation pass | **Did not** run `flask db upgrade` |
| Durable statement | **MIGRATION VERIFIED APPLIED.** Provenance: prior interrupted FG-013 live-migrate/UAT work. **Not applied by this reconciliation pass.** |

Table `historical_upload_attempts` exists with expected columns and indexes. No `upload_batches` table.

## Browser / UAT evidence (2026-08-30)

Local Flask **port 5004**. Labeled synthetic files only (`instance/fg013_uat_artifacts/`, gitignored). Protected Desktop corpus **untouched** (20/20 SHA-256 match).

| Criterion | Result |
|-----------|--------|
| Multi-file (one action) | **PASS** — 6 files in one `POST /historical-estimates/upload` |
| Combined summary | **PASS** — FILES RECEIVED 6 · LOADED 3 · DUPLICATES 0 · REVIEW REQUIRED 1 · UNSUPPORTED 1 · FAILED 1 |
| Drag/drop OS files | **NOT LIVE-BROWSER VERIFIED** — automation cannot drive OS file drag; dropzone handlers exist in `index.html` |
| Folder select/drop | **NOT LIVE-BROWSER VERIFIED — IMPLEMENTATION/AUTOMATED COVERAGE ONLY** (`webkitdirectory` present; native folder picker not driven) |
| Mixed outcomes / isolation | **PASS** — one bad file did not stop others; no durable `UploadBatch` |
| Duplicate / idempotency | **PASS** — re-upload identical SHA → DUPLICATE; still one workbook for that SHA; stored bytes unchanged |
| Storage / ADR-032 | **PASS** — `instance/historical_uploads/ORG-001/<sha256>.xlsx|.xlsm`; outside Git; original filename metadata |
| Unknown layout | **PASS** — `FG-013-UAT-unknown-adhoc.xlsx` QUARANTINED / REVIEW REQUIRED; UI: “Automated extraction is not reliable” |
| Known family | **PASS** — Family A synthetic `.xlsx`/`.xlsm` HISTORICAL EVIDENCE LOADED |
| Review / TIER_A | **PASS** — ACCEPTED AS EVIDENCE option; **TIER_A — Estimate associated with a completed project**; copy distinguishes evidence vs approved standard |
| Standard-mutation | **PASS** — labour candidates/standards and pricing policies unchanged (1 / 1 / 1 / 2) |
| Org isolation | **PASS** — live residue `ORG-001` only; dedicated tests fail-closed for ORG-002 |
| Security smoke | **PASS** — `.csv` UNSUPPORTED; malformed OpenXML FAILED; ZIP/size/path primarily covered by dedicated tests |

### Synthetic UAT residue (leave labeled)

- Attempts 1–7 on `historical_upload_attempts` (outcomes INGESTED ×3, QUARANTINED, UNSUPPORTED, FAILED, DUPLICATE)
- Productized workbooks/estimates ids **21–24** (`FG-013-UAT-recognized-slab.xlsx`, `-b.xlsx`, `.xlsm`, `unknown-adhoc.xlsx`)
- Stored files under `instance/historical_uploads/ORG-001/`
- Labeled generators under `instance/fg013_uat_artifacts/` (not Git)

Legacy 20 Desktop workbooks / 20 path rows / 120 labour items **unchanged**.
