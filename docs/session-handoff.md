# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **TURNOVER PASS — FG-006 HISTORICAL ESTIMATE INGESTION ENGINE PHASE B COMPLETE (AWAITING GOVERNANCE AUDIT / COMMIT)** |
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
   `Brayman-Estimator` (The Estimator) · Local path: `~/Desktop/Brayman-Estimator`

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Starting Pin HEAD: `cb38d932904bacc36b276ffe9cb93b4498d5f0dc`
   - Working tree: Changes staged/unstaged for FG-006 review (do not commit / do not push without approval)
   - Alembic head: `e1b2c3d4e5f6` (verified with `flask db current`)

3. **GOVERNING DOCUMENTS:**
   - [platform-constitution.md](platform-constitution.md) (Articles 1–12)
   - [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)
   - [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md)
   - [platform-governance.md](platform-governance.md)
   - [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md)
   - [architecture/historical-estimate-ingestion-architecture.md](architecture/historical-estimate-ingestion-architecture.md)
   - [architecture/historical-estimates-source-manifest.md](architecture/historical-estimates-source-manifest.md)
   - [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md)

4. **APPROVED PRODUCT VISION:**
   Strategic CalibAi lifecycle (`platform-vision.md` / `CAR-001`): PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - **ORGANIZATION & TENANCY:** `FOUNDATION IMPLEMENTED` (M011: `Organization`, `ORG-001` seed/backfill, tenant isolation, `ProjectCommercialContext` v1..vn, estimate immutability)
   - **HISTORICAL EVIDENCE INGESTION:** `PHASE B IMPLEMENTED` (FG-006: 20 source workbooks ingested into ORG-001, OpenXML parser, template classification Families A–E, cell provenance, data quality flags, human review workflow, 170 tests passing)
   - **PLAN:** `PARTIAL` (M005 PDF upload, M007 Document indexing, M009 Sheet classification & review, M010 Scale calibration & manual measurement implemented; M012+ automated take-off future)
   - **PRICE:** `PARTIAL` (Estimating builder, assemblies, line items, cost library, and Project Commercial Decision Gate implemented; pricing posture calculation effects future)
   - **CONTRACT:** `PARTIAL` (Proposals implemented with snapshot independence; Ontario construction contract & warranty templates governed/future)
   - **BUILD:** `PARTIAL` (Change Orders implemented in Project Controls; field mobile capture future)
   - **MONITOR:** `FUTURE` (ADR-021 Proposed)
   - **LEARN:** `FUTURE` (ADR-024 Accepted recommendation boundary; ML/recommendation implementation future)

6. **COMPLETED MILESTONES:**
   - Milestone 001: Platform Governance Foundation (`v0.1-governance-baseline`)
   - Milestone 005: Plan Intelligence Phase A Upload (`098647c`)
   - Milestone 007: Document Indexing & Deterministic Extraction (`cbefe7a`, migration `a7c8e9f0b1d2`)
   - Milestone 008: Sheet Intelligence Architecture Planning (`8c74e31`)
   - Milestone 009: Sheet Classification / Human Metadata Review (`5dc4b09`, migration `b8d9f0a1c2e3`)
   - Milestone 010: Scale Calibration / Measurement Tools (`6b969fe`, migration `c9e0f1a2b3d4`)
   - Milestone 011: Organization Foundation & Project Commercial Context (`cb38d93`, migration `d0a1b2c3d4e5`)
   - FG-006: Historical Estimate Ingestion Engine Phase B (Implementation complete, migration `e1b2c3d4e5f6`)

7. **LAST AUTHORIZED DELTA:**
   - FG-006 implementation completed strictly within FG-006 / Phase B boundaries.
   - Deterministic OpenXML parser (no macro execution), Template classifier (Families A–E), Family adapters.
   - Canonical models: `HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`.
   - Additive migration `e1b2c3d4e5f6`.
   - Controlled ingestion of 20 Brayman source workbooks into `ORG-001`.
   - 20/20 exact SHA-256 matches verified before and after ingestion.
   - 170 total tests passing (11 dedicated historical ingestion tests).
   - Direct ownership foreign keys on `Client`, `Project`, `CostItem`, `Assembly`, `ProposalTemplate`.
   - Tenant-safe query boundaries and fail-closed 404s.
   - Versioned `ProjectCommercialContext` model with 7 mandatory decision parameters.
   - Policy-driven justification engine (`ORGANIZATION_REASON_POLICIES`).
   - Project creation Commercial Decision Gate and context version editing UI.
   - Immutable `EstimateVersion.commercial_context_id` references.
   - Additive Alembic migration `d0a1b2c3d4e5` with deterministic legacy backfill.
   - Comprehensive test suite `tests/test_organization_foundation.py` (19 tests; 159/159 full suite pass).
   - Reconciled legacy backfill semantics: pre-M011 projects and estimate versions explicitly marked with `Legacy / Unknown` across all 7 parameters with UI notice "Legacy project — commercial context not recorded", preventing manufactured assumptions from contaminating future analytics. `Legacy / Unknown` is rejected if submitted on new projects or normal context edits.

8. **TEST / UAT / MIGRATION STATUS:**
   - Focused tests: `pytest tests/test_organization_foundation.py` → 19 passed.
   - Full suite: `pytest -q` → 159 passed, 64 legacy warnings in 12.14s.
   - Migration: `d0a1b2c3d4e5` applied cleanly to development database.

9. **PROTECTED STATE:**
   - Plan Intelligence geometry and coordinate transforms untouched.
   - Accepted Proposal snapshot immutability intact.
   - Existing pricing formulas and gross margin calculations untouched (no hidden multipliers applied from commercial posture in M011).
   - Historical workbook source files untouched.
