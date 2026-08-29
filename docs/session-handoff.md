# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-008 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED** |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Product-code HEAD / `origin/main` at upgrade: `0569f25e7ff496ab637d52437d48cf815522afa1`. Parent: `820f54afc179279d2435ad3a426b3037548bb45e`
   - FG-006 code: `690d755d9901e04eb783198f4b89071fbeaf472a`
   - Alembic graph head and live `flask db current`: `f2c3d4e5f6a7`
   - Tests after live migrate: **192 passed**, 119 warnings; historical ingestion **11 passed**; FG-008 dedicated **22 passed**
   - Product code: FG-008 foundation **IMPLEMENTED / VERIFIED** on `main`; live development/UAT **migrated** and **UAT-smoke-verified**

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **LIVE-MIGRATED**; [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**; FG-006; FG-007; ADR-028 Accepted. ADR-025 remains **Proposed**.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B foundation **OPERATIONAL FOR UAT**; pricing engine not started)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live development/UAT migrated 2026-08-29).

7. **CURRENT MILESTONE:** FG-008 Labour Engine Phase B — **COMPLETE for this gate** (live-migrated, UAT-smoke-verified). **Do not start the next milestone.**

8. **LAST AUTHORIZED DELTA:** Apply committed migration `f2c3d4e5f6a7` to live development/UAT, smoke-verify, regression-test, documentation-only reconciliation.

9. **IMPLEMENTATION STATUS:** Labour Engine Phase B foundation **operational for UAT**. Historical labour facts unchanged (120 items; `hourly_rate=0.13` cluster still 43). Estimate selling-price math unchanged. No live estimate versions existed for snapshot UAT; snapshot immutability covered by automated tests.

10. **TEST / MIGRATION:** Dedicated FG-008 22 passed; historical ingestion 11 passed; full suite 192 passed (post-upgrade). Live current = head = `f2c3d4e5f6a7`.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, 026, 027, 028, **029**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021, 025.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-008 live-migrated.**

15. **DELTA LEDGER (this session):** Live `flask db upgrade` `e1b2c3d4e5f6` → `f2c3d4e5f6a7`; UAT smoke; post-migration 22/11/192; docs-only reconciliation. No product code.

16. **OPEN DECISIONS:** ORG-001 canonical task seed contents; ADR-025 still open (not this gate).

17. **KNOWN RISKS:** Historical `hourly_rate=0.13` vs $65-implied extended cost; material SKUs classified as labour; no quantity on labour rows so production rates cannot be reverse-engineered blindly; unauthenticated office app. Leftover UAT labour records identified in the live-migration stopping report (archived task `UAT-FG008-001`; one ACCEPTED mapping to that UAT task; DRAFT synthetic production standard; WITHDRAWN candidate; one resolution audit row keyed `ORG-999` with no Organization row).

18. **DEFERRED:** Crew Template; payroll burden; actuals write path; pricing engine; AI take-off; field/mobile; QuickBooks API; contracts.

19. **PROHIBITED NEXT:** Do not start Pricing Engine / ADR-025; do not rewrite historical labour facts; do not treat UAT synthetic records as operating Brayman standards; do not start another milestone from this handoff.

20. **NEXT AUTHORIZED ACTION:** **NONE from this prompt.** Stop. Next coded work requires a new Joel-authorized Feature Gate / Cursor prompt (Pricing Engine remains blocked).

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
