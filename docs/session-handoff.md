# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-009 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT** |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - HEAD / `origin/main`: FG-009 implementation `8e11179fb5abb42a68805fe011e84c15e866ea04` plus docs-only live-migrate verification commit
   - FG-008 implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head: `a3b4c5d6e7f8`
   - Live `flask db current`: `a3b4c5d6e7f8` (one head)
   - Tests: dedicated Pricing Engine **33**; Labour Engine **25**; historical ingestion **11**; full suite **228**
   - Product code: FG-009 **committed and pushed**; **live-migrated**; **UAT-smoke-verified**. No product-code change in the live-migrate pass.

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; [organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) **Approved**; [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [ADR-030](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**. FG-008 / ADR-029 remain implemented/Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B **OPERATIONAL FOR UAT**; Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated; integrity `ff5d856`). FG-009 is **not a numbered milestone**; foundation is **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**.

7. **CURRENT MILESTONE:** FG-009 live-migrated and UAT-smoke-verified. **STOP.** Do not start AI take-off.

8. **LAST AUTHORIZED DELTA:** Apply `a3b4c5d6e7f8` to live development/UAT; bounded Pricing Engine UAT smoke; docs-only reconciliation.

9. **IMPLEMENTATION STATUS:** Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**. Versions without snapshots still use legacy `COST_PLUS_MARKUP_STACK`. Explicit human apply creates a snapshot (ORG-001 default policy is `TRUE_GROSS_MARGIN` 15%). New estimates are not auto-converted. Labour snapshot cost is not added to the estimate basis by default. ORG-001 optional overhead/profit/contingency layers remain `UNSPECIFIED`.

10. **TEST / MIGRATION:** Graph head and live current `a3b4c5d6e7f8`. Tests: 33 / 25 / 11 / 228.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, **025**, 026, 027, 028, **029**, **030**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-009 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**.

15. **DELTA LEDGER (this session):** Authorized `flask db upgrade` `f2c3d4e5f6a7` → `a3b4c5d6e7f8`. Synthetic UAT smoke (TRUE_GM / markup / legacy / COs / override / snapshot immutability). Docs-only reconciliation. No product-code change.

16. **OPEN DECISIONS:** ORG-001 canonical labour task seed contents; ORG-001 overhead/profit/contingency treatments remain `UNSPECIFIED` until a governed policy change; whether labour-snapshot Direct Labour Cost should enter the estimate basis without double-counting.

17. **KNOWN RISKS:** Unauthenticated office app; historical COs without snapshot remain markup-on-subtotal; Estimate Totals header still renders leftover stack percents even when a snapshot is authoritative; synthetic FG-009 UAT residue remains in the live development/UAT DB.

18. **DEFERRED:** Crew Template; payroll burden; actuals write path; AI take-off; field/mobile; QuickBooks API; contracts; four-output product; Project Hub.

19. **PROHIBITED NEXT:** Do not start AI take-off or another milestone. Do not rewrite historical labour facts or historical Change Orders. Do not treat synthetic `FG-009 UAT *` records as customer work. Do not change the ORG-001 TRUE_GM seed.

20. **NEXT AUTHORIZED ACTION:** FG-009 closure review, then prepare the next Feature Gate for AI Take-off / Quantity Extraction Foundation. **Do not start AI take-off in this handoff.**

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
