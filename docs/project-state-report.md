# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-08-28 |

Update this report at every **completed milestone** and major interruption point.
Distinguish from:

- [session-handoff.md](session-handoff.md) — immediate session continuation
- [milestones.md](milestones.md) — historical milestone record
- [current-state.md](current-state.md) — detailed verified product/repo snapshot

---

# PART A — Standard Project State Report Template

| Field | Content |
|-------|---------|
| Report date | |
| Repository | |
| Current branch | |
| Base commit | |
| Latest completed milestone | |
| Current milestone | |
| Product status | |
| Architecture status | |
| Implemented capabilities | |
| Incomplete work | |
| Database and migration status | |
| Test status | |
| Documentation status | |
| Security or technical risks | |
| Decisions made | |
| Decisions pending | |
| Uncommitted work | |
| Next approved milestone | |
| Exact resume commands | |
| Documents to read first | |
| Approved next Cursor prompt location or summary | |
| Commit status | |

---

# PART B — Current Baseline Report

| Field | Content |
|-------|---------|
| Report date | 2026-08-28 |
| Repository | Brayman-Estimator (The Estimator) |
| Current branch | `main` |
| Current commit / `origin/main` | `690d755d9901e04eb783198f4b89071fbeaf472a` (exact parity on `origin/main`) |
| August governance reconciliation | `0fdf0d4` — *Document August 2026 governance reconciliation and product requirements.* |
| State closure | `ee100ac` — *docs: close August governance reconciliation state* |
| M011 Implementation Commit | `cb38d93` — *feat: implement M011 organization foundation and commercial context* |
| FG-006 Implementation Commit | `690d755` — *feat: implement FG-006 historical estimate ingestion engine phase b* |
| Latest completed milestone | **FG-006** — Historical Estimate Ingestion Engine Phase B (migration `e1b2c3d4e5f6`; 170 total tests passed, 11 dedicated ingestion tests) |
| Current milestone | **None active / turnover state** (FG-006 completed, verified, and pushed) |
| Product status | Operational on `main`: CRM, Estimating, Proposals (+ Accepted immutability), Change Orders, Plan upload (M005), Document Indexing (M007), Sheet Classification / Review (M009), Scale Calibration & Manual Measurement Tools (M010), Organization Foundation & Project Commercial Context (M011), Historical Estimate Ingestion Engine Phase B (FG-006). CalibAi V1 / BUILD / field / four-output package / QuickBooks API / Ontario contract / Labour Engine / Pricing Engine **not implemented**. |
| Architecture status | CAR-001 approved. Organization Foundation (M011 / FG-007 / ADR-028) + Historical Estimate Ingestion (FG-006) implemented and verified. Review Turnover Protocol governing. |
| Implemented capabilities | Phase A PDF upload/storage; page indexing; deterministic extraction; processing provenance; archive-over-delete; relational search; Sheet entities, page mappings, suggestions, human review workflow (accept/edit/reject/void), uniqueness validation, office review UI; 2-point drawing scale calibration, preset scales, viewport calibrations, NTS flagging; manual linear, polyline, polygon area (Shoelace) / perimeter, and count measurements; normalized document coordinate transforms; interactive PDF.js viewer; `Organization` entity (`ORG-001` seeded/backfilled), tenant query isolation, versioned `ProjectCommercialContext` with 7 mandatory parameters, Commercial Decision Gate, immutable `EstimateVersion.commercial_context_id` references; deterministic OpenXML parser (zero macros), template classifier (Families A–E), family adapters, normalized historical evidence models (`HistoricalSourceWorkbook`, `HistoricalEstimate`, `HistoricalSourceObservation`, `HistoricalCostLineItem`, `HistoricalLabourItem`, `HistoricalSubcontractItem`, `HistoricalDataQualityFlag`, `HistoricalEstimateReviewDecision`), cell provenance tracking, and human review UI (`/historical-estimates/`). |
| Incomplete work | Automated AI quantity take-off (M012+); four-output document package; QuickBooks integration; Ontario contract/warranty generation; BUILD field capture; Labour Engine Phase B (BLOCKED / NOT STARTED); Organization-Calibrated Pricing Engine (BLOCKED / NOT STARTED). |
| Database and migration status | Current Alembic head `e1b2c3d4e5f6` (FG-006 Historical Estimate Ingestion Engine Phase B) |
| Test status | **170 passed**, 64 legacy warnings in 24.49s (`pytest -q`); **11 passed** in dedicated historical ingestion suite |
| Documentation status | Reconciled and current: FG-004, FG-005, FG-006, FG-007 approved & implemented; ADR-002, ADR-017, ADR-018, ADR-019, ADR-020, ADR-022, ADR-023, ADR-024, ADR-026, ADR-027, ADR-028 Accepted; Review Turnover Protocol active; working tree clean |
| Decisions made | M009 implemented; M010 implemented; M011 / FG-007 implemented; FG-006 implemented & verified; 20 Brayman historical workbooks ingested into ORG-001 with 20/20 SHA-256 exact hashes verified; Review Turnover Protocol adopted; CAR-001 adopted; ADR-028 Accepted |
| Decisions pending | None active. Next candidate: Labour Engine Phase B architecture / Feature Gate preparation (STATUS: NOT STARTED; REQUIRES SEPARATE GOVERNANCE AUTHORIZATION). |
| Uncommitted work | None (clean working tree) |
| Next approved milestone | **NONE** |
| Next candidate milestone | **Labour Engine Phase B Feature Gate / architecture** (STATUS: NOT STARTED; REQUIRES SEPARATE GOVERNANCE AUTHORIZATION) |
| Documents to read first | [current-state.md](current-state.md) → [session-handoff.md](session-handoff.md) → [feature-gates/FG-006-historical-estimate-ingestion-phase-b.md](feature-gates/FG-006-historical-estimate-ingestion-phase-b.md) → [feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md](feature-gates/FG-007-m011-organization-foundation-and-project-commercial-context.md) → [architecture/organization-and-calibration-architecture.md](architecture/organization-and-calibration-architecture.md) |
| Approved next Cursor prompt location or summary | None approved (governance turnover state) |
| Commit status | Parity on `main` at `690d755d9901e04eb783198f4b89071fbeaf472a` |
| Governance baseline | FG-006 verified; Review Turnover protocol governing; no unapproved code |

### Resume commands (Cursor Terminal)

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/python -m pytest -q
```
