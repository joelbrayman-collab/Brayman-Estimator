# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-010 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT** |
| Updated | 2026-08-30 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Implementation HEAD: `9665295ace673a46a8c645ed0598e5e91d41931c` (`feat: implement FG-010 AI take-off foundation`)
   - Docs reconciliation commit: this live-migrate/UAT verification commit (parent `9665295`)
   - Working tree: clean after docs commit/push
   - FG-009 implementation: `8e11179fb5abb42a68805fe011e84c15e866ea04`
   - FG-008 implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head / live `flask db current`: `b4c5d6e7f8a9` (one head)
   - Tests: dedicated take-off **18**; Plan Intelligence combined **56**; Pricing Engine **33**; Labour Engine **25**; historical ingestion **11**; full suite **251**
   - Real external AI provider **not authorized**. Phase D **not started**.

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**; [ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md); [ADR-031](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted**. ADR-005/006/007/009/011 **Accepted**. ADR-010 **Proposed**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 / ADR-029 remain implemented/Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010 implemented; **M012 / FG-010 foundation OPERATIONAL FOR UAT**)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B **OPERATIONAL FOR UAT**; Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated; integrity `ff5d856`). FG-009 is **not a numbered milestone**; foundation is **CLOSED / OPERATIONAL FOR UAT**. M012 / FG-010 foundation is **LIVE-MIGRATED / UAT-SMOKE-VERIFIED**.

7. **CURRENT MILESTONE:** M012 / FG-010 **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**. **AI TAKE-OFF FOUNDATION OPERATIONAL FOR UAT.** **STOP DEVELOPMENT.** Real external AI provider **not authorized**. Phase D **not started**.

8. **LAST AUTHORIZED DELTA:** Apply `b4c5d6e7f8a9` to live development/UAT and perform bounded synthetic browser/UAT smoke. Docs-only reconciliation commit. No product-code changes. No external AI. No Phase D.

9. **IMPLEMENTATION STATUS:** AI take-off **foundation operational for UAT** (mock only). Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**. Labour Engine **FG-008 OPERATIONAL FOR UAT**.

10. **TEST / MIGRATION:** Graph head and live current `b4c5d6e7f8a9`. Tests: take-off **18** / Plan Intelligence combined **56** / Pricing **33** / Labour **25** / Historical **11** / full **251**.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 005, 006, 007, 009, 011, 017, 018, 019, 020, 022, 023, 024, **025**, 026, 027, 028, **029**, **030**, **031**.

13. **PROPOSED ADRs:** 001, 003, 004, 008, 010, 012–016, 021. ADR-010 remaining: OCR, CAD, **real external AI provider**.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-009 CLOSED / OPERATIONAL FOR UAT**. **FG-010 IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE-MIGRATED / UAT-SMOKE-VERIFIED**.

15. **DELTA LEDGER (this session):** Live `flask db upgrade` `a3b4c5d6e7f8` → `b4c5d6e7f8a9`. Synthetic FG-010 UAT + browser smoke. Docs-only reconciliation commit. No product-code changes.

16. **OPEN DECISIONS:** Real AI provider (not authorized); Phase D mapping later; actor-string reviewer identity until auth; ARCH-only eligibility; cancelled status modeled without cancel operation.

17. **KNOWN RISKS:** Unauthenticated office app; historical COs without snapshot remain markup-on-subtotal; Estimate Totals header still renders leftover stack percents even when a snapshot is authoritative (**separate UI maintenance**); synthetic FG-009 and FG-010 UAT residue remains in the live development/UAT DB.

18. **DEFERRED:** Estimate mapping (Phase D); Crew Template; payroll burden; actuals write path; field/mobile; QuickBooks API; contracts; four-output product; Project Hub; OCR/CAD; multi-trade extraction; real external AI provider.

19. **PROHIBITED NEXT:** Do not start Phase D. Do not enable an external AI provider. Do not start another milestone. Do not insert estimate lines. Do not reopen FG-009. Do not rewrite historical labour facts or historical Change Orders. Do not delete synthetic UAT audit history.

20. **NEXT AUTHORIZED ACTION:** **STOP DEVELOPMENT.** Run full Day-End Reconciliation / Repository / Documentation / Storage / Review Turnover audit before any further development.

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
./venv/bin/python -m pytest -q tests/test_takeoff.py
./venv/bin/python -m pytest -q tests/test_plan_upload.py tests/test_plan_indexing.py tests/test_sheet_intelligence.py tests/test_scale_measurement.py
./venv/bin/python -m pytest -q tests/test_pricing_engine.py
./venv/bin/python -m pytest -q tests/test_labour_engine.py
./venv/bin/python -m pytest -q tests/test_historical_ingestion.py
./venv/bin/python -m pytest -q
```

22. **SYNTHETIC FG-010 UAT RESIDUE (leave labeled; no archive/delete lifecycle):**
   - Client `FG-010 UAT Client` (id 3); Project `FG-010 UAT` / `FG-010-UAT` (id 3)
   - Documents: `FG-010-UAT-A-101.pdf` (searchable); `FG-010-UAT-no-text.pdf` (ineligible)
   - Runs 1–3 `succeeded` / `calibai-mock`; approved package #1 total **3**; COUNT measurement #1 (no scale)
   - Leftover suggested candidates on run 2 (4) and run 3 (3); run 3 UI smoke accepted candidate 9
   - PlanAuditEvent rows for the UAT project retained
