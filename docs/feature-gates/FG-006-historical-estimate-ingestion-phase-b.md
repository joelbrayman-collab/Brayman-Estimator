# Feature Gate FG-006: Historical Estimate Ingestion Engine (Phase B)

| Attribute | Value |
|-----------|-------|
| Feature Gate ID | `FG-006` |
| Feature Name | Historical Estimate Ingestion Engine — Phase B (Deterministic Ingestion & Persistence) |
| Target Milestone | Milestone 006 / Historical Ingestion Phase B |
| Governance Basis | `platform-constitution.md`, `architecture-principles.md`, `pricing-policy.md`, `ADR-024`, `ADR-025`, `ADR-028` |
| Prerequisite Gates | `FG-007` (M011 Organization Foundation & Project Commercial Context) **Satisfied** |
| Status | **APPROVED FOR IMPLEMENTATION** |
| Date | 2026-08-28 |

---

## 1. Executive Summary & Objective

This Feature Gate authorizes the deterministic, organization-aware ingestion of historical estimating workbooks into CalibAi's governed commercial evidence repository.

Phase A established the source manifest, forensic audit of the 20 Brayman source workbooks, template family classifications, and cell-level provenance models. Following the completion of Milestone 011 (`Organization` foundation and tenant isolation under `FG-007` / `ADR-028`), Phase B implements the database models, deterministic OpenXML parsing adapters, source-cell observation lineage, data quality flagging, human review workflow, and tenant query boundaries.

---

## 2. Twelve Governance Question Responses (platform-governance.md)

### 1. Does this feature advance the approved product vision?
**Yes.** Converts unstructured historical workbook evidence into structured, organization-owned commercial facts with full source-cell provenance, establishing the evidence base for future calibration.

### 2. Does this feature respect module boundaries and existing architecture?
**Yes.** All historical ingestion entities (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`) are organization-owned, self-contained, and completely separate from active estimating and cost library tables.

### 3. Does this change preserve historical commercial records?
**Yes.** Source workbooks remain 100% immutable outside Git (`~/Desktop/CalibAi Historical Estimates`). Extracted historical calculations retain their original formulas (e.g. Cost-Plus Markup) and are not rewritten to modern pricing policy.

### 4. What is the evidence class and tier for this data?
**Evidence Class: ORG-HISTORICAL.** Historical data is evidence, not automatic pricing truth. Ingestion assigns explicit evidence tiers (Tier A through Tier E) and review states.

### 5. Does this feature require database migrations?
**Yes.** One additive Alembic migration creating the historical ingestion tables, indexes, and unique constraints.

### 6. Are all records organization-owned with tenant query isolation?
**Yes.** Every root entity has a mandatory `organization_id` FK to `organizations.id`. All list, detail, and review queries filter strictly by the current organization.

### 7. Does this feature implement the Labour Engine or Pricing Engine?
**NO.** Phase B normalizes historical labour hours and material costs as raw evidence. It does not approve production rates, calculate standard crew productivities, apply pricing markups to current estimates, or train ML models.

### 8. Does this feature execute Excel macros or modify source files?
**NO.** A pure-Python deterministic OpenXML reader parses workbook XML directly without macro execution. Source files are read-only and SHA-256 verified before and after ingestion.

### 9. How is idempotency and re-ingestion handled?
**Deterministic idempotency.** `(organization_id, sha256_hash, ingestion_rule_version)` forms a unique key preventing duplicate ingestion.

### 10. How is cell-level provenance maintained?
Every extracted quantity, cost, labour hour, and total maintains a direct foreign key to a `HistoricalSourceObservation` capturing workbook name, sheet name, cell coordinate, raw formula, and displayed value.

### 11. What is the human review workflow?
Estimators can inspect workbook metadata, totals, template family, warnings, and source provenance, recording formal review decisions (`REVIEWED`, `ACCEPTED_AS_EVIDENCE`, `REJECTED`, `SUPERSEDED`, `REVIEW_REQUIRED`).

### 12. What are the acceptance criteria and test plan?
- 100% pass on dedicated ingestion test suite and full 159-test repository baseline.
- 20/20 SHA-256 hash match on source workbooks.
- Accurate extraction on regression anchors (Allen Jacques, Mike Pratt, Bob Milne, Julia Harish, Alberton Garage).
- Cross-tenant isolation verified with fail-closed 404s.

---

## 3. Approval

| Role | Name | Status | Date |
|------|------|--------|------|
| Product Owner | Joel Brayman | Approved | 2026-08-28 |
| Architectural Review | CalibAi Architecture | Approved | 2026-08-28 |
