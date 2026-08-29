# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-008 IMPLEMENTED / VERIFIED** — live DB **not yet migrated** to `f2c3d4e5f6a7` |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - HEAD / `origin/main`: FG-008 implementation commit (confirm `git rev-parse HEAD`). Parent: `820f54afc179279d2435ad3a426b3037548bb45e`
   - FG-006 code: `690d755d9901e04eb783198f4b89071fbeaf472a`
   - Alembic graph head: `f2c3d4e5f6a7` (live `flask db current` still `e1b2c3d4e5f6` — upgrade not applied)
   - Tests: **192 passed**, 119 warnings; historical ingestion **11 passed**; FG-008 dedicated **22 passed**
   - Product code: FG-008 foundation **IMPLEMENTED / VERIFIED** on `main`

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **IMPLEMENTED / VERIFIED**; [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**; FG-006; FG-007; ADR-028 Accepted. ADR-025 remains **Proposed**.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B foundation **IMPLEMENTED / VERIFIED**; pricing engine not started)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (this commit; live DB not migrated).

7. **CURRENT MILESTONE:** FG-008 Labour Engine Phase B — **IMPLEMENTED / VERIFIED**. Live migrate not authorized.

8. **LAST AUTHORIZED DELTA:** FG-008 commit and push. **Do not apply live `flask db upgrade`.**

9. **IMPLEMENTATION STATUS:** Labour Engine Phase B foundation on `main`. Historical labour facts unchanged. Estimate selling-price math unchanged.

10. **TEST / MIGRATION:** Dedicated FG-008 22 passed; historical ingestion 11 passed; full suite 192 passed. Migration file `f2c3d4e5f6a7` on graph; live DB not upgraded.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, 026, 027, 028, **029**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021, 025.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-008 live DB not migrated.**

15. **DELTA LEDGER (this session):** Additive Labour Engine models/services/routes/UI/migration/tests; governed docs updated to IMPLEMENTED / VERIFIED; commit + push.

16. **OPEN DECISIONS:** Live Alembic upgrade authorization; ORG-001 canonical task seed contents; ADR-025 still open (not this gate).

17. **KNOWN RISKS:** Historical `hourly_rate=0.13` vs $65-implied extended cost; material SKUs classified as labour; no quantity on labour rows so production rates cannot be reverse-engineered blindly; unauthenticated office app; live DB not yet migrated.

18. **DEFERRED:** Crew Template; payroll burden; actuals write path; pricing engine; AI take-off; field/mobile; QuickBooks API; contracts.

19. **PROHIBITED NEXT:** Do not run live `flask db upgrade` without authorization; do not change $65 policy; do not rewrite historical labour facts; do not implement ADR-025; do not start another milestone.

20. **NEXT AUTHORIZED ACTION:** Separate governance authorization to apply migration `f2c3d4e5f6a7` to the live development/UAT database and perform post-migration smoke verification.

21. **RESUME COMMANDS (Cursor Terminal):**

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/flask db heads
./venv/bin/python -m pytest -q
./venv/bin/python -m pytest -q tests/test_historical_ingestion.py
./venv/bin/python -m pytest -q tests/test_labour_engine.py
```
