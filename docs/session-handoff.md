# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-008 CLOSED — OPERATIONAL FOR UAT** (post-UAT integrity stabilization completed) |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Product-code parent of this pass: `abf41ad7d5d69039b02f2cc6bf447bb0142181a2` (docs live-migration record). Implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head and live `flask db current`: `f2c3d4e5f6a7`
   - Tests after integrity stabilization: **195 passed**, 293 warnings; historical ingestion **11 passed**; FG-008 dedicated **25 passed**
   - Product code: FG-008 foundation **OPERATIONAL FOR UAT**; post-UAT integrity gaps closed

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-008](feature-gates/FG-008-labour-engine-phase-b.md); [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md); [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**. ADR-025 remains **Proposed**.

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

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated 2026-08-29; integrity stabilization this pass).

7. **CURRENT MILESTONE:** FG-008 — **CLOSED — OPERATIONAL FOR UAT**. This pass is **not** a new milestone. **Do not start the next milestone.**

8. **LAST AUTHORIZED DELTA:** Post-UAT integrity stabilization: `REVOKED` mapping lifecycle; archived-task rule-suggestion safety; unknown-org audit non-persist; live mapping 1 revoked; synthetic PRS 1 withdrawn.

9. **IMPLEMENTATION STATUS:** Labour Engine Phase B foundation **operational for UAT**. HistoricalLabourItem id 1 unchanged. Mapping 1 **REVOKED**. Task `UAT-FG008-001` **ARCHIVED**. PRS 1 **WITHDRAWN**. Candidate 1 **WITHDRAWN**. ORG-001 $65 unchanged. ORG-999 Organization does not exist. Original ORG-999 audit event id 16 preserved; ORG-001 reconciliation event id 23.

10. **TEST / MIGRATION:** Dedicated FG-008 **25 passed**; historical ingestion **11 passed**; full suite **195 passed**. No new migration. Live current = head = `f2c3d4e5f6a7`.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, 026, 027, 028, **029**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021, 025.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-008 closed for UAT operation.**

15. **DELTA LEDGER (this session):** Mapping `REVOKED`; rule suggestion joins ACTIVE tasks; unknown-org fail-closed without audit persist; live UAT reconciliation; tests 25/11/195; docs.

16. **OPEN DECISIONS:** ORG-001 canonical task seed contents; ADR-025 still open (not this gate).

17. **KNOWN RISKS:** Historical `hourly_rate=0.13` vs $65-implied extended cost; material SKUs classified as labour; unauthenticated office app. Preserved UAT audit event id 16 (`organization_id=ORG-999`) is a historical anomaly (SQLite did not enforce the FK). Synthetic UAT task remains archived.

18. **DEFERRED:** Crew Template; payroll burden; actuals write path; pricing engine; AI take-off; field/mobile; QuickBooks API; contracts.

19. **PROHIBITED NEXT:** Do not start Pricing Engine / ADR-025; do not rewrite historical labour facts; do not start another milestone from this handoff.

20. **NEXT AUTHORIZED ACTION:** **NONE.** Stop.

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
