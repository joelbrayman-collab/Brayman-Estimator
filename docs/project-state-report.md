# Project State Report — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative milestone-level state |
| Updated | 2026-09-09 |

Update this report at every **completed milestone** and major interruption point.
Distinguish from:

- [session-handoff.md](session-handoff.md) — immediate session continuation
- [milestones.md](milestones.md) — historical milestone record
- [current-state.md](current-state.md) — detailed verified product/repo snapshot

---

# PART A — Standard Project State Report Template

| Field | Content |
|-------|---------|
| Report date | |
| Repository | |
| Current branch | |
| Base commit | |
| Latest completed milestone | |
| Current milestone | |
| Product status | |
| Architecture status | |
| Implemented capabilities | |
| Incomplete work | |
| Database and migration status | |
| Test status | |
| Documentation status | |
| Security or technical risks | |
| Decisions made | |
| Decisions pending | |
| Uncommitted work | |
| Next approved milestone | |
| Exact resume commands | |
| Documents to read first | |
| Approved next Cursor prompt location or summary | |
| Commit status | |

---

# PART B — Current Baseline Report

| Field | Content |
|-------|---------|
| Report date | 2026-09-09 |
| Repository | Brayman-Estimator (The Estimator / CalibraytAI) |
| Current branch | `main` |
| Current commit / `origin/main` | *Pinned after FG-028 Slices 1–2 commit.* Parent was FG-027 pin **`3e15aeea065f74aae2a9036e1709ae5e76948e4e`**. Live current = heads **`a5b6c7d8e9f0`**. |
| Latest completed **coded** milestone on `main` | **FG-028 Slices 1–2** product-identity transition (not a V1 package). Prior: **FG-027 CLOSED / OPERATIONAL FOR UAT.** V1-02 **COMPLETE**. |
| Current milestone | [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — V1 readiness **45%**; **2 / 11** COMPLETE (V1-01, V1-02); BMR DEMO READY **NO**; BRAYMAN REAL-LIFE UAT READY **NO**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **SLICES 1–2 IMPLEMENTED / SLICE 3 HELD / NOT CLOSED**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. [ADR-044](adr/ADR-044-costing-approval-snapshot-ownership-and-pricing-consumption-boundary.md) **Accepted**. [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. |
| Product status | Current product **CalibraytAI** (formerly CalibAi). Office chrome remains **Brayman Construction Platform**. FG-027 costing approval is **CLOSED / OPERATIONAL FOR UAT**. Observation Delete remains **QUEUED / NOT AUTHORIZED / NOT IMPLEMENTED / NON-BLOCKING**. Four-output outputs 3–4 / QuickBooks API / Ontario contract **not implemented**. |
| Architecture status | CAR-001 approved. [ADR-045](adr/ADR-045-calibraytai-product-identity-and-former-name-preservation.md) **Accepted**. FG-008 through FG-023 **CLOSED** (FG-021 subject to SESSION-EXPIRY deferred exception). [FG-026](feature-gates/FG-026-plan-price-phase-d-takeoff-to-estimate-mapping-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-027](feature-gates/FG-027-automated-costing-and-human-cost-approval-v1.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **NOT CLOSED** (Slice 3 held). [FG-025](feature-gates/FG-025-contractor-facing-ux-language-and-terminology-standardization.md) **SLICE 1–5 IMPLEMENTED / NOT CLOSED**. [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) **FUTURE / RECORDED / NOT IMPLEMENTATION-AUTHORIZED**. ADR-008 / ADR-010 **Proposed**. Real external AI provider **not authorized**. |
| Implemented capabilities | FG-028 Slices 1–2 visible product identity + current-authority docs. FG-027 costing approval + Pricing consume/stale **live-migrated and office-UAT-verified**. Prior coded baseline unchanged. |
| Incomplete work | FG-028 Slice 3 logo asset. Website identity **EXTERNAL**. V1-03 / BMR supplier workflow **NOT AUTHORIZED**. FG-025 remaining surfaces **NOT AUTHORIZED**. Observation Delete (**QUEUED / NOT AUTHORIZED**); Native Signing **production activation**; Project Closeout; [FG-024](feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); four-output outputs 3–4; QuickBooks; Ontario contract/warranty templates; supplier/Winchester POC. |
| Database and migration status | Repository head = live current **`a5b6c7d8e9f0`**. **No new revision** in FG-028. No live DB mutation. |
| Test status | Dedicated FG-028 **9 passed**. Focused Field/Hub/Permit/Brand/Labour **117 passed**. Full suite **661 passed** (pre-rename baseline **652** + 9 dedicated). |
| Documentation status | [governance/product-identity.md](governance/product-identity.md) **GOVERNING** for current vs former name. [v1-completion-register.md](v1-completion-register.md) **GOVERNING** — readiness **45%**. [FG-028](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) **NOT CLOSED**. |
| Decisions made (this implementation) | 2026-09-09 Joel authorized CalibAi → CalibraytAI Slices 1–2. Slice 3 held. V1 percentages unchanged. |
| Decisions pending | Slice 3 Joel-approved lettering asset. Website external pass. V1-03 authorization. Remaining Joel decisions in [v1-completion-register.md](v1-completion-register.md) §13 except #2. FG-025 remaining-surface authorization. FG-024. Observation Delete. Ontario counsel answers. |
| Uncommitted work | FG-028 Slices 1–2 in progress until commit. |
| Next approved milestone | **STOP.** Do **not** begin V1-03. FG-028 Slice 3 waits on Joel asset. Website is external. |
| Next candidate milestone | V1-03 / BMR supplier workflow — **NOT AUTHORIZED until a separate prompt**. |
| Documents to read first | [governance/product-identity.md](governance/product-identity.md) → [session-handoff.md](session-handoff.md) → [v1-completion-register.md](v1-completion-register.md) → [feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md](feature-gates/FG-028-calibai-to-calibraytai-product-identity-transition.md) |
| Approved next Cursor prompt location or summary | **STOP.** Slice 3 / website / V1-03 require separate authorization. |
| Commit status | *Pinned after commit.* Live current = heads `a5b6c7d8e9f0`. |
| Governance baseline | V1 register GOVERNING / 45% / 2 of 11 COMPLETE; FG-028 Slices 1–2 implemented / Slice 3 held / NOT CLOSED; ADR-045 Accepted; FG-027 CLOSED / OPERATIONAL FOR UAT; live current = heads a5b6c7d8e9f0 |

### Resume commands (Cursor Terminal)

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
```
