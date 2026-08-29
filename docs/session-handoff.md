# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-009 APPROVED FOR IMPLEMENTATION** — **not implemented**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT** |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Product-code baseline (unchanged): parent of docs commit is `ff5d856d52433832c8b3099cb5a17ba72fb73db3`
   - FG-008 implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head and live `flask db current`: `f2c3d4e5f6a7`
   - Tests: dedicated Labour Engine **25**; historical ingestion **11**; full suite **195**
   - Product code: **unchanged**. FG-008 foundation remains **OPERATIONAL FOR UAT**

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-009](feature-gates/FG-009-organization-calibrated-pricing-engine.md) **APPROVED FOR IMPLEMENTATION**; [organization-calibrated-pricing-engine-architecture.md](architecture/organization-calibrated-pricing-engine-architecture.md) **Approved**; [ADR-025](adr/ADR-025-pricing-policy-versus-estimate-markup-stack.md) **Accepted**; [ADR-030](adr/ADR-030-organization-owned-pricing-policy-and-estimate-pricing-snapshot.md) **Accepted**. FG-008 / ADR-029 remain implemented/Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010; AI take-off future)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B **OPERATIONAL FOR UAT**; Pricing Engine **approved, not implemented**)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated; integrity `ff5d856`).

7. **CURRENT MILESTONE:** No new coded milestone. FG-009 is **approved for implementation** and **has not started**.

8. **LAST AUTHORIZED DELTA:** Governance finalization: ADR-025/030 **Accepted**; FG-009 **APPROVED FOR IMPLEMENTATION**; contingency source vs pricing-treatment clarification. **No product code. No migration.**

9. **IMPLEMENTATION STATUS:** Pricing Engine **not implemented**. Live selling-price math remains line markup + overhead + compounding profit + tax. Change Orders still use a separate markup-on-subtotal formula. Labour snapshots still not wired into sell price.

10. **TEST / MIGRATION:** No new migration. Live current = head = `f2c3d4e5f6a7`. Tests: 25 / 11 / 195.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 017, 018, 019, 020, 022, 023, 024, **025**, 026, 027, 028, **029**, **030**.

13. **PROPOSED ADRs:** 001, 003–016 (except 002), 021.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-009 APPROVED FOR IMPLEMENTATION — not implemented.**

15. **DELTA LEDGER (this session):** Docs/governance only. Contingency visibility vs `INCLUDED_IN_MARGIN_BASIS` / `ADDED_AFTER_BASE_PRICING`. ADRs accepted. FG-009 approved. Stale “prepared / not approved” status lines updated.

16. **OPEN DECISIONS:** ORG-001 canonical labour task seed contents; exact additive pricing schema at implementation; ORG-001 contingency treatment selection (human-approved org policy, not hard-coded history).

17. **KNOWN RISKS:** Live estimate vs ORG-001 true-GM discrepancy until implementation; Change Order formula ≠ estimate stack (architecture records the defect; historical COs must not be rewritten); unauthenticated office app.

18. **DEFERRED:** Pricing Engine **implementation**; Crew Template; payroll burden; actuals write path; AI take-off; field/mobile; QuickBooks API; contracts; four-output product.

19. **PROHIBITED NEXT:** Do not implement FG-009 from this handoff without a **separate** bounded execution prompt. Do not rewrite historical labour facts or historical Change Orders.

20. **NEXT AUTHORIZED ACTION:** Issue a separately authorized bounded **FG-009 implementation** Cursor prompt.

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
