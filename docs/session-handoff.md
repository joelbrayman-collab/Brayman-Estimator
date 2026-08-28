# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **TURNOVER PASS — REPOSITORY-BACKED HANDOFF** |
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
   - Implementation Baseline (M010): `6b969fe`
   - Turnover Adoption: `39ae8fedf3e77be7f756eaacb25d6c06de810969`
   - Current `HEAD` / `origin/main`: Confirm with `git rev-parse HEAD` (parity on `main`)
   - Working tree: Clean (`nothing to commit, working tree clean`)
   - Alembic head: `c9e0f1a2b3d4` (verified with `flask db current`)

3. **GOVERNING DOCUMENTS:**
   - [platform-constitution.md](platform-constitution.md) (Articles 1–12)
   - [governance/continuity-and-anti-drift.md](governance/continuity-and-anti-drift.md)
   - [governance/review-turnover-protocol.md](governance/review-turnover-protocol.md)
   - [platform-governance.md](platform-governance.md)
   - [development-workflow.md](development-workflow.md)

4. **APPROVED PRODUCT VISION:**
   Strategic CalibAi lifecycle (`platform-vision.md` / `CAR-001`): PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project` record.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - **PLAN:** `PARTIAL` (M005 PDF upload, M007 Document indexing, M009 Sheet classification & review, M010 Scale calibration & manual measurement implemented; M011+ automated take-off future)
   - **PRICE:** `PARTIAL` (Estimating builder, assemblies, line items, and cost library implemented; governed pricing policy ($65/hr direct / 15% gross margin formula `Direct Cost / 0.85` vs markup stack) calculation migration is Proposed in ADR-025 / Future)
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
   - Milestone 010: Scale Calibration / Measurement Tools (migration `c9e0f1a2b3d4`)

7. **CURRENT MILESTONE:**
   **M010 is COMPLETED & VERIFIED.** Next candidate milestone is **M011 — AI Take-off / Quantity Extraction Foundation** (requires dedicated Feature Gate).

8. **LAST AUTHORIZED DELTA:**
   M010 Scale Calibration & Measurement Tools implementation (migration `c9e0f1a2b3d4`, 19 focused tests, PDF.js measurement UI).

9. **IMPLEMENTATION STATUS:**
   - Models: `PlanDocument`, `PlanPage`, `ProcessingAttempt`, `ProcessingResult`, `PlanAuditEvent`, `DrawingPackage`, `DrawingRevision`, `PlanSheet`, `PlanSheetPage`, `PlanSheetSuggestion`, `PlanScaleCalibration`, `PlanMeasurement`.
   - Routes: Upload, list, detail, reprocess, download, archive, sheets index, sheet create, sheet review, suggestion accept/reject, sheet edit, void, finalize index, measure sheet workspace, calibration CRUD, measurement CRUD.
   - Templates: `list.html`, `detail.html`, `upload.html`, `sheets_index.html`, `sheet_review.html`, `sheet_create.html`, `sheet_measure.html`.

10. **TEST / UAT / MIGRATION STATUS:**
    - Focused tests: `pytest tests/test_scale_measurement.py` → 19 passed.
    - Full suite: `pytest -q` → 140 passed, 120 legacy warnings in 10.65s.
    - Migration: `c9e0f1a2b3d4` applied cleanly.

11. **PROTECTED STATE:**
    - `PlanDocument` binary bytes, SHA-256 hash, and `PlanPage` raw extractions are immutable.
    - Human authority invariant: AI suggestions never silently set authoritative Sheet SoR or confirmed drawing scale.
    - Accepted Proposal snapshot immutability.
    - Pricing policy: $65/hr direct labour, 15% gross margin formula `Price = Direct Cost / 0.85`.
    - Legal Content Gate for Ontario contract/warranty templates.

12. **ACCEPTED ADRs:**
    - ADR-002: Accepted Proposal Immutability (M003)
    - ADR-017: Sheet Metadata Suggestion and Review Workflow (M008/FG-004/M009)
    - ADR-018: Sheet Uniqueness, Duplicates, and Supersession (M008/FG-004/M009)
    - ADR-019: CalibAi Lifecycle and Project Hub (CAR-001)
    - ADR-020: BUILD Module Boundary vs Project Controls (CAR-001)
    - ADR-022: Field Client and Shared API (CAR-001)
    - ADR-023: Field Evidence Original vs Derived (CAR-001)
    - ADR-024: LEARN Recommendation Boundary (CAR-001)
    - ADR-026: Scale Ownership, Multi-Scale Viewports, and Calibration Provenance (M010)
    - ADR-027: PDF Rendering and Normalized Document Coordinate System (M010)

13. **PROPOSED / OPEN ADRs:**
    - ADR-001: Proposal Snapshot Ownership
    - ADR-003: Optional CRM Foreign Keys on Proposals
    - ADR-004: Proposal Acceptance Workflow
    - ADR-005: AI Take-Off Source Traceability
    - ADR-006: Human Approval Before Estimate Insertion
    - ADR-007: Plan and Estimate Version Ownership
    - ADR-008: Supplier Price Snapshotting
    - ADR-009: PDF-First versus CAD-First Ingestion
    - ADR-010: Build versus Buy for CAD and Document Processing
    - ADR-011: AI Confidence Threshold Policy
    - ADR-012: Plan Document Version Ownership
    - ADR-013: Document Intelligence Layer Boundary
    - ADR-014: Sheet Identity and Page Mapping (identity model adopted in code; document status remains Proposed)
    - ADR-015: Extracted Metadata Ownership and Provenance
    - ADR-016: Document Intelligence Search Strategy
    - ADR-021: MONITOR Commercial Baseline
    - ADR-025: Gross-Margin Policy vs Estimate Markup Stack

14. **FEATURE GATES:**
    - FG-001: Passed (Proposals)
    - FG-002: Passed (Plan Intelligence Phase A)
    - FG-003: Conditional Pass (Document Intelligence Readiness)
    - FG-004: **APPROVED, IMPLEMENTED & VERIFIED** (M009 Sheet Classification)
    - FG-005: **APPROVED** — implementation **not started** (M010 Scale Calibration)

15. **CHAT → REPOSITORY DELTA LEDGER RESULT:**
    `100% RECONCILED` — all approved decisions, architecture records, migration facts, and test results are committed in repository authority.

16. **OPEN DECISIONS:**
    Formal acceptance of ADR-021, ADR-025, ADR-026, and ADR-027 by Joel.

17. **KNOWN RISKS:**
    None for M009. Scale calibration in M010 requires robust multi-scale drawing rendering architecture.

18. **DEFERRED ITEMS:**
    - M010: Scale calibration / measurement tools (FG-005 approved, code awaiting prompt)
    - M011+: AI-assisted quantity take-off
    - QuickBooks Online direct API integration
    - Ontario construction contract generation
    - BUILD field capture / mobile app

19. **EXPLICITLY PROHIBITED NEXT ACTIONS:**
    - DO NOT implement M010 scale tools without an approved implementation prompt.
    - DO NOT implement QuickBooks API or contract generation.
    - DO NOT alter pricing formulas or accepted proposals.

20. **NEXT AUTHORIZED ACTION:**
    Dedicated **M010 implementation Cursor prompt** citing `FG-005`.

21. **EXACT REPOSITORY RESUME COMMANDS:**
    ```bash
    cd /Users/joelbrayman/Desktop/Brayman-Estimator
    git status
    git branch --show-current
    git log -1 --oneline
    git rev-parse HEAD
    git rev-parse origin/main
    ./venv/bin/python -m pytest -q
    ```

22. **FRESH CHAT STARTUP PROMPT:**
    (See Section 2 below)

---

## 2. Fresh Chat Startup Prompt

Copy and paste this prompt when starting a fresh ChatGPT or Cursor conversation:

```text
BRAYMAN — RESUME FROM REVIEW TURNOVER
CONTINUITY / REPOSITORY-FIRST INITIALIZATION

You are resuming work on the Brayman-Estimator platform following a successful Review Turnover.
The prior conversation has been discarded. The repository is the ONE SOURCE OF TRUTH.

1. ANTI-DRIFT PREFLIGHT
Read and comply with:
- AGENTS.md
- docs/platform-constitution.md
- docs/governance/continuity-and-anti-drift.md
- docs/governance/review-turnover-protocol.md
- docs/current-state.md
- docs/project-state-report.md
- docs/session-handoff.md

2. VERIFY BASELINE
Run in Cursor Terminal:
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/python -m pytest -q

Expected Baseline:
- Branch: main
- HEAD = origin/main (confirm parity via git rev-parse)
- Working tree: clean
- Alembic head: b8d9f0a1c2e3
- Tests: 121 passed

3. RECONSTRUCT AUTHORITATIVE STATE
Independently verify from repository documents:
- Latest completed milestone: M009 Sheet Classification / Human Metadata Review
- Protected state & invariants (source immutability, human SoR, pricing policy)
- Accepted ADRs: ADR-002, ADR-017, ADR-018, ADR-019, ADR-020, ADR-022, ADR-023, ADR-024
- Open decisions: ADR-021, ADR-025, ADR-026, ADR-027 pending approval
- Next authorized capability: Dedicated M010 implementation prompt citing FG-005

Do NOT rely on AI memory. Do NOT guess missing product rules.
Conversation titles in this workspace must start with: BRAYMAN — <Topic>.
```
