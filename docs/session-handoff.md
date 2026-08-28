# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **TURNOVER PASS — POST-FG-006 GOVERNANCE & STATE RECONCILIATION COMPLETE** |
| Updated | 2026-08-28 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) (`Review Turnover`) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative Review Turnover Package

```text
============================================================
REVIEW TURNOVER PACKAGE — BRAYMAN ESTIMATOR
============================================================
```

1. **PROJECT / REPOSITORY:**
   - Name: `Brayman-Estimator` (The Estimator)
   - Local Path: `~/Desktop/Brayman-Estimator`
   - Git Root: `~/Desktop/Brayman-Estimator`

2. **VERIFIED BASELINE:**
   - Current Branch: `main`
   - Authoritative HEAD Commit: `690d755d9901e04eb783198f4b89071fbeaf472a`
   - `origin/main` Parity: Exact (`690d755d9901e04eb783198f4b89071fbeaf472a`)
   - Working Tree: Clean
   - Alembic Migration Head: `e1b2c3d4e5f6` (FG-006 Historical Estimate Ingestion Engine Phase B)
   - Test Baseline: **170 passed**, 64 legacy warnings (`./venv/bin/python -m pytest -q`)
   - Dedicated Historical Ingestion Suite: **11 passed** (`./venv/bin/python -m pytest tests/test_historical_ingestion.py -q`)

3. **GOVERNING DOCUMENTS:**
   - [platform-constitution.md](platform-constitution.md) (Articles 1–12)
   - [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)
   - [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md)
   - [platform-governance.md](platform-governance.md)
   - [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md)
   - [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)
   - [adr/ADR-028-organization-foundation-and-project-commercial-context.md](adr/ADR-028-organization-foundation-and-project-commercial-context.md)
   - [architecture/historical-estimate-ingestion-architecture.md](architecture/historical-estimate-ingestion-architecture.md)
   - [architecture/historical-estimates-source-manifest.md](architecture/historical-estimates-source-manifest.md)
   - [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md)

4. **APPROVED PRODUCT VISION & LIFECYCLE:**
   - Strategic CalibAi lifecycle (`platform-vision.md` / `CAR-001`): PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - **ORGANIZATION & TENANCY:** `FOUNDATION IMPLEMENTED` (M011 / FG-007: `Organization`, `ORG-001` seed/backfill, tenant query isolation with fail-closed 404s, versioned `ProjectCommercialContext` v1..vn, estimate immutability, migration `d0a1b2c3d4e5`).
   - **HISTORICAL EVIDENCE INGESTION:** `PHASE B IMPLEMENTED` (FG-006: 20 source workbooks ingested into ORG-001, deterministic OpenXML parser, template classification Families A–E, cell provenance, data quality flags, human review workflow, migration `e1b2c3d4e5f6`, 170 tests passing).
   - **PLAN:** `PARTIAL` (M005 PDF upload, M007 Document indexing, M009 Sheet classification & review, M010 Scale calibration & manual measurement tools implemented; M012+ automated take-off future).
   - **PRICE:** `PARTIAL` (Estimating builder, assemblies, line items, cost library, and Project Commercial Decision Gate implemented; pricing posture calculation effects future).
   - **CONTRACT:** `PARTIAL` (Proposals implemented with snapshot independence; Ontario construction contract & warranty templates governed/future).
   - **BUILD:** `PARTIAL` (Change Orders implemented in Project Controls; field mobile capture future).
   - **MONITOR:** `FUTURE` (ADR-021 Proposed).
   - **LEARN:** `FUTURE` (ADR-024 Accepted recommendation boundary; ML/recommendation implementation future).

6. **COMPLETED MILESTONES:**
   - Milestone 001: Platform Governance Foundation (`v0.1-governance-baseline`)
   - Milestone 005: Plan Intelligence Phase A Upload (`098647c`)
   - Milestone 007: Document Indexing & Deterministic Extraction (`cbefe7a`, migration `a7c8e9f0b1d2`)
   - Milestone 008: Sheet Intelligence Architecture Planning (`8c74e31`)
   - Milestone 009: Sheet Classification / Human Metadata Review (`5dc4b09`, migration `b8d9f0a1c2e3`)
   - Milestone 010: Scale Calibration / Measurement Tools (`6b969fe`, migration `c9e0f1a2b3d4`)
   - Milestone 011 / FG-007: Organization Foundation & Project Commercial Context (`cb38d93`, migration `d0a1b2c3d4e5`)
   - FG-006: Historical Estimate Ingestion Engine Phase B (`690d755`, migration `e1b2c3d4e5f6`)

7. **HISTORICAL EVIDENCE CORPUS & INGESTION METRICS:**
   - **Source Directory:** `~/Desktop/CalibAi Historical Estimates` (External to Git, read-only).
   - **Workbook Integrity:** 20 / 20 workbooks verified with exact SHA-256 cryptographic hashes; zero mutations before or after ingestion.
   - **Tenant Scoping:** All historical evidence strictly owned by Organization `ORG-001` (Brayman Construction Inc.) with tenant-isolated queries.
   - **Parser Engine:** Pure Python deterministic OpenXML zip reader executing zero macros or VBA scripts.
   - **Template Families:**
     - Family A (Slab-on-Grade / TES): 9 workbooks
     - Family B (Standard ICF Foundation): 5 workbooks
     - Family C (Extended Multi-Trade ICF): 1 workbook
     - Family D (Comprehensive Build Package): 1 workbook
     - Family E (Ad-hoc / Standalone Flat Sheet): 4 workbooks
   - **Ingestion Database Population:**
     - 20 Source Workbooks (`historical_source_workbooks`)
     - 20 Historical Estimates (`historical_estimates`)
     - 661 Material / Cost Line Items (`historical_cost_line_items`)
     - 120 Labour Items (`historical_labour_items`)
     - 7 Subcontract / Package Items (`historical_subcontract_items`)
     - 664 Source-Cell Observations (`historical_source_observations`)
     - 19 Quality Flags (`historical_data_quality_flags`)
   - **Cell Provenance:** 100% of line items and commercial totals trace to exact source cells (workbook, sheet, cell coordinate, formula, displayed value).
   - **Human Review:** Dedicated `/historical-estimates/` interface supporting review decisions (`REVIEWED`, `ACCEPTED_AS_EVIDENCE`, `REJECTED`, `SUPERSEDED`, `REVIEW_REQUIRED`).
   - **Commercial Evidence Anchors & Contingency Semantics:**
     - **Mike Pratt (`HIST-EST-0014`):** Direct cost $534,436.10, GC work / markup $60,492.01, contingency $25,896.80, selling price before tax $620,824.91, grand total with 13% HST $701,532.15. Contingency is distinctly captured and not conflated with markup.
     - **Julia Harish (`HIST-EST-0008`):** Direct cost $85,152.40, markup $12,772.86, contingency $4,257.62 (retained as internal reserve, excluded from customer selling-price rollup), pre-tax selling price $97,925.26, grand total with 13% HST $110,655.54.
     - **Allen Jacques (`HIST-EST-0002`):** Direct cost $30,976.00, markup $4,646.40, selling price before tax $35,622.40, grand total with 13% HST $40,253.31.

8. **PROTECTED STATE & BLOCKING INVARIANTS:**
   - **Labour Engine Phase B:** **BLOCKED / NOT STARTED**. Historical labour hours and costs are persisted as raw evidence only; no productivity curves, standardized crew rates, or automated labour recommendations are active.
   - **Organization-Calibrated Pricing Engine:** **BLOCKED / NOT STARTED**. Existing pricing formulas and gross margin calculations remain untouched. Commercial context posture settings do not alter base estimating math.
   - **Tenant Isolation:** Cross-organization learning, data pooling, or cross-tenant benchmarking is strictly prohibited.
   - **Workbook Immutability:** Historical source files remain read-only outside Git.
   - **Active Data Integrity:** Active estimating, cost library, proposal snapshots, and change orders remain completely unmutated.

9. **NEXT GOVERNED CANDIDATE:**
   - Candidate: Labour Engine Phase B architecture / Feature Gate preparation.
   - Status: **NOT STARTED — REQUIRES SEPARATE GOVERNANCE AUTHORIZATION**.
   - Rule: No coding, schema changes, or milestone execution may begin without explicit Joel approval of a dedicated Feature Gate and approved Cursor prompt.
