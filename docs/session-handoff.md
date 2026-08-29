# Session Handoff & Review Turnover Package — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **FG-010 APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 remains **CLOSED — OPERATIONAL FOR UAT** |
| Updated | 2026-08-29 |
| Protocol | [docs/governance/review-turnover-protocol.md](governance/review-turnover-protocol.md) |
| Complements | [current-state.md](current-state.md) · [chat-workflow-log.md](chat-workflow-log.md) · [project-state-report.md](project-state-report.md) · [milestones.md](milestones.md) |

---

## 1. Authoritative package

1. **PROJECT / REPOSITORY:** `Brayman-Estimator` (The Estimator). Path: `~/Desktop/Brayman-Estimator`.

2. **VERIFIED BASELINE:**
   - Branch: `main`
   - Parent HEAD: `bc37463a15dbb3a97e6250686ba5b0a4d78f1955` (FG-009 live-migrate verification)
   - This pass: FG-010 **governance approval documentation commit** (see git log)
   - FG-009 implementation: `8e11179fb5abb42a68805fe011e84c15e866ea04`
   - FG-008 implementation: `0569f25e7ff496ab637d52437d48cf815522afa1`
   - Alembic graph head: `a3b4c5d6e7f8`
   - Live `flask db current`: `a3b4c5d6e7f8` (one head)
   - Tests: Plan Intelligence suites **51**; Pricing Engine **33**; Labour Engine **25**; historical ingestion **11**; full suite **228**
   - Product code: **unchanged**. Real external AI provider **not authorized**.

3. **GOVERNING DOCUMENTS:** Constitution; continuity/anti-drift; Review Turnover Protocol; platform-governance; [FG-010](feature-gates/FG-010-ai-takeoff-quantity-extraction-foundation.md) **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**; [ai-takeoff-quantity-extraction-foundation.md](architecture/ai-takeoff-quantity-extraction-foundation.md) **Approved**; [ADR-031](adr/ADR-031-versioned-extraction-run-takeoff-package-and-candidate-provenance.md) **Accepted**. ADR-005/006/007/009/011 **Accepted**. ADR-010 **Proposed**. FG-009 remains **CLOSED / OPERATIONAL FOR UAT**. FG-008 / ADR-029 remain implemented/Accepted.

4. **APPROVED PRODUCT VISION:** PLAN → PRICE → CONTRACT → BUILD → MONITOR → LEARN on one `Project`. No rename. Office and field complementary. CalibAi owns methodology; each organization owns commercial intelligence.

5. **CURRENT CALIBAI LIFECYCLE STATE:**
   - ORGANIZATION: foundation implemented (M011)
   - HISTORICAL EVIDENCE: Phase B implemented (FG-006)
   - PLAN: partial (M005–M010 implemented; **M012 / FG-010 APPROVED FOR IMPLEMENTATION — not implemented**)
   - PRICE: partial (builder + commercial gate; Labour Engine Phase B **OPERATIONAL FOR UAT**; Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**)
   - CONTRACT: partial (proposals; Ontario templates future)
   - BUILD: partial (change orders; field capture future)
   - MONITOR: future (ADR-021 Proposed)
   - LEARN: future (ADR-024 boundary accepted; no ML)

6. **COMPLETED CODED MILESTONES:** M001, M005, M007, M008 (docs), M009 (`5dc4b09`), M010 (`6b969fe`), M011 (`cb38d93`), FG-006 (`690d755`), FG-008 (`0569f25`; live-migrated; integrity `ff5d856`). FG-009 is **not a numbered milestone**; foundation is **CLOSED / OPERATIONAL FOR UAT**.

7. **CURRENT MILESTONE:** M012 / FG-010 **APPROVED FOR IMPLEMENTATION** / **NOT IMPLEMENTED**. **STOP.** Requires a **separate** bounded implementation prompt. Real external AI provider **not authorized**.

8. **LAST AUTHORIZED DELTA:** Governance approval documentation: FG-010 approved; ADR-005/006/007/009/011/031 Accepted; ADR-010 remains Proposed; COUNT-without-scale clarification; provider-not-authorized condition. No product code. No migration.

9. **IMPLEMENTATION STATUS:** AI take-off **not implemented**. Pricing Engine **FG-009 FOUNDATION OPERATIONAL FOR UAT**. Labour Engine **FG-008 OPERATIONAL FOR UAT**.

10. **TEST / MIGRATION:** Graph head and live current `a3b4c5d6e7f8`. Tests: 51 (Plan Intelligence combined) / 33 / 25 / 11 / 228.

11. **PROTECTED STATE:** Constitution 1–12; Accepted proposals; PlanDocument/source workbook immutability; human authority; $65 / 15% ORG-001 policy; Legal Content Gate; ORG isolation; historical labour as evidence only; no cross-org pooling.

12. **ACCEPTED ADRs:** 002, 005, 006, 007, 009, 011, 017, 018, 019, 020, 022, 023, 024, **025**, 026, 027, 028, **029**, **030**, **031**.

13. **PROPOSED ADRs:** 001, 003, 004, 008, 010, 012–016, 021. ADR-010 remaining: OCR, CAD, **real external AI provider**.

14. **FEATURE GATES:** FG-002–FG-008 approved & implemented (FG-001 Draft). **FG-009 CLOSED / OPERATIONAL FOR UAT**. **FG-010 APPROVED FOR IMPLEMENTATION** — **NOT IMPLEMENTED**.

15. **DELTA LEDGER (this session):** Docs-only governance approval. COUNT is dimensionless (authorized M010 count/scale correction in a later implementation prompt only). No `app/` or `migrations/` changes.

16. **OPEN DECISIONS:** Separate FG-010 implementation prompt; real AI provider (not authorized); confidence band UI cut-points; Phase D mapping later. Unrelated FG-009 debt: ORG-001 overhead/profit/contingency `UNSPECIFIED`; labour-snapshot Direct Labour Cost not in estimate basis by default.

17. **KNOWN RISKS:** Unauthenticated office app; historical COs without snapshot remain markup-on-subtotal; Estimate Totals header still renders leftover stack percents even when a snapshot is authoritative (**separate UI maintenance**); synthetic FG-009 UAT residue remains in the live development/UAT DB.

18. **DEFERRED:** Estimate mapping (Phase D); Crew Template; payroll burden; actuals write path; field/mobile; QuickBooks API; contracts; four-output product; Project Hub; OCR/CAD; multi-trade extraction; real external AI provider.

19. **PROHIBITED NEXT:** Do not implement FG-010 in this handoff. Do not generate Alembic, add a provider SDK, send plans to an external model, or insert estimate lines. Do not reopen FG-009. Do not rewrite historical labour facts or historical Change Orders.

20. **NEXT AUTHORIZED ACTION:** Issue a **separate** bounded FG-010 implementation prompt for the provider-neutral AI Take-off foundation. **Do not implement until that prompt is issued.**

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
