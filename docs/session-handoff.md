# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-009 IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT** |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - HEAD / `origin/main`: FG-009 implementation commit (parent `41bfb2e`)
   - FG-008 implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head: `a3b4c5d6e7f8`
   - Live `flask db current`: `f2c3d4e5f6a7` (**not** upgraded)
   - Tests: dedicated Pricing Engine **33**; Labour Engine **25**; historical ingestion **11**; full suite **228**
   - Product code: FG-009 **committed and pushed**; **not live-migrated**

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**; [organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) **Approved**; [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [ADR-030](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**. FG-008 / ADR-029 remain implemented/Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B **OPERATIONAL FOR UAT**; Pricing Engine **FG-009 FOUNDATION IMPLEMENTED / NOT YET LIVE-MIGRATED**)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated; integrity `ff5d856`). FG-009 is **not a numbered milestone**; foundation is **IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**.

7. **CURRENT MILESTONE:** FG-009 committed and pushed; live migrate **not authorized**.

8. **LAST AUTHORIZED DELTA:** Commit and push the reviewed FG-009 implementation. **Do not apply live migration.**

9. **IMPLEMENTATION STATUS:** Pricing Engine **FG-009 FOUNDATION IMPLEMENTED / NOT YET LIVE-MIGRATED**. Versions without snapshots still use legacy `COST_PLUS_MARKUP_STACK`. Explicit human apply creates a snapshot (ORG-001 default policy is `TRUE_GROSS_MARGIN` 15% once migrated). New estimates are not auto-converted. Labour snapshot cost is not added to the estimate basis by default.

10. **TEST / MIGRATION:** Graph head `a3b4c5d6e7f8`. Live current `f2c3d4e5f6a7`. Tests: 33 / 25 / 11 / 228.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, **025**, 026, 027, 028, **029**, **030**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-009 IMPLEMENTED / VERIFIED / NOT YET LIVE-MIGRATED**.

15. **DELTA LEDGER (this session):** One implementation commit + push of reviewed FG-009 foundation. Live DB not migrated.

16. **OPEN DECISIONS:** ORG-001 canonical labour task seed contents; ORG-001 overhead/profit/contingency treatments remain `UNSPECIFIED` until a governed policy change; live-migrate timing; whether labour-snapshot Direct Labour Cost should enter the estimate basis without double-counting.

17. **KNOWN RISKS:** Live DB still on FG-008 head until authorized migrate; unauthenticated office app; historical COs without snapshot remain markup-on-subtotal.

18. **DEFERRED:** Live FG-009 migrate; Crew Template; payroll burden; actuals write path; AI take-off; field/mobile; QuickBooks API; contracts; four-output product.

19. **PROHIBITED NEXT:** Do not migrate live DB unless separately authorized. Do not start AI take-off or another milestone. Do not rewrite historical labour facts or historical Change Orders.

20. **NEXT AUTHORIZED ACTION:** Separate authorization to apply migration `a3b4c5d6e7f8` to the live development/UAT database and perform Pricing Engine UAT smoke verification.

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
./venv/bin/python -m pytest -q tests/test_pricing_engine.py
./venv/bin/python -m pytest -q tests/test_labour_engine.py
./venv/bin/python -m pytest -q tests/test_historical_ingestion.py
./venv/bin/python -m pytest -q
```
