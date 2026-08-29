# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-008 APPROVED FOR IMPLEMENTATION** — **not implemented**; separate execution prompt required |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Parent of this approval commit: `e2bf33c9377c3990052ae4a3c5f695c8df5d041c`
   - FG-006 code: `690d755d9901e04eb783198f4b89071fbeaf472a`
   - Alembic: `e1b2c3d4e5f6`
   - Tests: **170 passed**, 64 warnings; historical ingestion **11 passed**
   - Product code in this package: **none**

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-008](feature-gates/FG-008-labour-engine-phase-b.md) **APPROVED FOR IMPLEMENTATION**; [labour-engine-phase-b-architecture.md](architecture/labour-engine-phase-b-architecture.md) **Approved**; [ADR-029](adr/ADR-029-canonical-labour-task-production-standard-and-calibration-lifecycle.md) **Accepted**; FG-006; FG-007; ADR-028 Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine **architecture approved, code not started**; pricing engine not started)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`).

7. **CURRENT MILESTONE:** FG-008 architecture approved. **Not a coded milestone. Implementation not started.**

8. **LAST AUTHORIZED DELTA:** Approve FG-008 architecture and ADR-029; commit documentation only. **No product implementation.**

9. **IMPLEMENTATION STATUS:** Labour Engine code **none**. Historical labour: `HistoricalLabourItem` in `app/models/historical_estimates.py` (120 rows, ORG-001).

10. **TEST / MIGRATION:** Alembic still `e1b2c3d4e5f6`. Product tests unchanged by design; re-run after docs (see stopping report).

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, 026, 027, 028, **029**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021, 025.

14. **FEATURE GATES:** FG-002–FG-007 approved & implemented (FG-001 Draft). **FG-008 APPROVED FOR IMPLEMENTATION, not implemented.**

15. **DELTA LEDGER (this session):** FG-008 architecture memorialized in new docs; SHA/ADR-028/M009 stale refs corrected where evidence supported.

16. **OPEN DECISIONS:** ORG-001 canonical task seed; actuals persistence timing (defer recommended); ADR-025 still open (not this gate). Implementation prompt not yet issued.

17. **KNOWN RISKS:** Historical `hourly_rate=0.13` vs $65-implied extended cost; material SKUs classified as labour; no quantity on labour rows so production rates cannot be reverse-engineered blindly; unauthenticated office app; org architecture §18 multiplier example superseded for labour by ADR-029.

18. **DEFERRED:** Crew Template; payroll burden; actuals write path; pricing engine; AI take-off; field/mobile; QuickBooks API; contracts.

19. **PROHIBITED NEXT:** Do not implement FG-008 until a separate execution prompt; do not migrate; do not change $65 policy; do not rewrite historical labour facts.

20. **NEXT AUTHORIZED ACTION:** A separately authorized bounded FG-008 **implementation** prompt. **No implementation from this handoff alone.**

21. **RESUME COMMANDS (Cursor Terminal):**

```bash
cd /Users/joelbrayman/Desktop/Brayman-Estimator
git status
git branch --show-current
git log -1 --oneline
git rev-parse HEAD
git rev-parse origin/main
./venv/bin/flask db current
./venv/bin/python -m pytest -q
./venv/bin/python -m pytest -q tests/test_historical_ingestion.py
```

22. **FRESH CHAT STARTUP:** Reconstruct from this file + current-state + project-state-report. Title chats `BRAYMAN — <Topic>`. Do not import AiRIA state. FG-008 architecture is approved; **implementation is not authorized** until a separate execution prompt.
