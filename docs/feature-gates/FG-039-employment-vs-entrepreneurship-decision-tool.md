# Feature Gate FG-039: Employment vs Entrepreneurship Decision Tool

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-039` |
| Feature Name | Employment vs Entrepreneurship Decision Tool (Business Owner Assessment) |
| Target Milestone | **None.** FG-039 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Decision Tools** (PLAN decision tool). Does **not** take ownership of Plan Intelligence take-off records, Estimating commercial records, or CRM. |
| Date | 2026-09-24 |
| Status | **OPEN / AUTHORIZED BY APPROVED CURSOR PROMPT / IMPLEMENTED IN WORKING TREE / NOT COMMITTED** |
| Architecture | Stateless calculation. No durable records. No schema. No migration. No live DB writes. |
| Related ADRs | **None.** If implementation would require a durable assessment record, tax engine, financing model, or recommendation engine: **STOP**. |
| Prerequisites | PKG-F14 **CLOSED**. Repository Alembic **`h8c9d0e1f2a3`**. Live Alembic **`g7b8c9d0e1f2`**. LIVE S16 **NOT APPLIED**. |
| Approved baseline | `main` @ `3b193949eabd326bbce33043b2b60a1a290c7c6f`. Approved standalone prototype: `CalibraytAI_Business_Owner_App.html` (ChatGPT; not a repository artifact). This gate installs that approved calculator into CalibraytAI. Do **not** invent a different calculator. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **OPEN / AUTHORIZED** |
| Implementation | **IMPLEMENTED IN WORKING TREE / NOT COMMITTED** |
| Schema / Alembic | **NO** change. Repository head remains **`h8c9d0e1f2a3`**. Live remains **`g7b8c9d0e1f2`**. |
| New ADR | **None** |
| Durable records | **None** |

This gate authorizes a **neutral PLAN decision tool** comparing employment economics with entrepreneurship / business-ownership economics, plus four practical-completeness layers: Startup & Transition Cash, Downside Stress Test, Total Owner Workload, and Cash Available to Owner before personal income tax.

It does **not** authorize a business-plan application, tax engine, financing model, multi-year forecast, recommendation engine, CRM, bookkeeping, or F07/F15.

**Do not invent FG-036.** FG-036 remains unused.

---

## Purpose and business rationale

Someone comparing employment with entrepreneurship needs a clear economic and workload picture. The tool exposes:

- employment economic value
- entrepreneurship economic value and cash available to the owner
- the difference
- cash required to make the transition
- total owner hours
- what has to be true to match employment economics
- three independent 10% downside cases

The tool does **not** decide. The user decides.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | People comparing employment with entrepreneurship lack a neutral, shareable economic and workload picture. Salary alone is incomplete. Entrepreneurship needs selling rate, productive hours, overhead, helper labour where used, transition cash, and downside sensitivity. |
| 2 | Who is the user? | Anyone comparing employment with entrepreneurship: currently employed, considering leaving employment, already self-employed, or comparing an employment opportunity with business ownership. Generic public user. Not Josh-specific. Not construction-only. |
| 3 | Which module owns it? | **Decision Tools** (`app/services/business_owner_assessment.py`, `app/routes/business_owner_assessment.py`). PLAN decision tool. Plan Intelligence does **not** own it. Estimating does **not** own it. |
| 4 | What data does it own? | **No durable records.** Inputs exist only for the in-session calculation. Defaults are documented starting assumptions. |
| 5 | What data does it reference? | None of the office commercial records. Trade/profile defaults are starting assumptions only. User-entered values override defaults. |
| 6 | What may implementation change? | Calculation engine; public branded route/template/CSS/JS; login exemption for this blueprint; office nav link; dedicated tests; governed docs. |
| 7 | What must implementation not change? | Schemas; migrations; live DB; F07; F15; PKG-F14 sealed generators; tax/financing/depreciation/CCA/loan models; recommendation/winner/score/traffic-light output; CalibraytAI logo assets; V1 scores; recovery stash. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | Dedicated engine + HTTP tests covering employment, business, What Has to Be True, startup cash, stress, workload, owner cash, neutrality, validation, and Results PDF reconciliation. Focused then full suite. |
| 10 | Documentation? | This gate; `modules/decision-tools.md`; feature-gate index; architecture; current-state; session-handoff; chat-workflow-log; roadmap next-action; Manual Impact seven questions. Do **not** rescore V1. Do **not** write the User Guide. |
| 11 | ADR required? | **No.** Stateless calculator. **STOP** if a durable assessment record, tax engine, or recommendation engine appears required. |
| 12 | Migration? | **No.** If a schema change appears required, **STOP**. Do not create a migration. |

---

## Acceptance criteria

1. Guided progression TODAY → BUSINESS → MARKET → COSTS → RESULTS is preserved. Startup & Transition Cash is a compact COSTS section, not a replacement of that structure.
2. Employment economic value includes wages plus user-supplied benefits / retirement / other compensation.
3. Business engine works for a solo owner and for owner + helper. Helper is optional.
4. Entrepreneurship economic value equals cash available to the owner before personal income tax (same residual; no second conflicting engine).
5. Results show difference, owner productive/admin/total hours, effective owner hourly return, break-even selling rate, utilization/productivity requirements, helper economics where used, and What Has to Be True.
6. Transition cash = startup/setup + working capital + personal runway − existing usable assets, floored at zero.
7. Three independent downside cases from base inputs: 10% fewer productive hours; 10% lower realized rate; 10% higher operating costs. Base case is not mutated. Cases are not combined.
8. Required total owner hours = required productive hours/week + expected admin hours/week.
9. No NaN / Infinity / undefined in outputs. Legitimate negative entrepreneurship-vs-employment differences are shown.
10. No recommendation, winner, best/worse, decision score, risk score, star rating, or traffic-light.
11. Approved CalibraytAI logo V2 only. Generic copy only.
12. No schema, no migration, no live DB mutation.
13. Download Results PDF uses the same `calculate()` result object as the screen. ReportLab renderer formats that object only. Optional scenario name; fallback title when blank. No DB persistence. Start over / new scenario is a separate action.

---

## Explicit exclusions

Personal tax; corporate tax; salary/dividend planning; depreciation; CCA; loan amortization; equipment financing; multi-year forecast; balance sheet; cash-flow statement; full accounting income statement; Monte Carlo; probability weighting; business valuation; exit valuation; retirement planning; pension actuarial modelling; CRM; bookkeeping; AR/AP; business-plan generator; recommendation score; winner; risk rating; traffic light.

---

## Provenance

Approved calculator created in ChatGPT as standalone `CalibraytAI_Business_Owner_App.html` before repository installation. Absence of that HTML file from the repository does **not** authorize a redesign. This gate plus the 24 Sep 2026 Cursor prompt are the authoritative product specification for installing that calculator.
