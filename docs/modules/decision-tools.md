# Module — Decision Tools

| Attribute | Value |
|-----------|--------|
| Status | **Partial Current** — Employment vs Entrepreneurship Decision Tool **IMPLEMENTED IN WORKING TREE / NOT COMMITTED** ([FG-039](../feature-gates/FG-039-employment-vs-entrepreneurship-decision-tool.md)) |
| Updated | 2026-09-24 |
| Code | `app/services/business_owner_assessment.py`, `app/services/business_owner_assessment_pdf.py`, `app/routes/business_owner_assessment.py`, `app/templates/decision_tools/`, `app/static/css/business-owner-assessment.css`, `app/static/js/business-owner-assessment.js` |
| Feature Gates | [FG-039](../feature-gates/FG-039-employment-vs-entrepreneurship-decision-tool.md) |
| Tests | `tests/test_business_owner_assessment_fg039.py` |

## Purpose

Neutral PLAN decision tools that expose economics and practical requirements. They do **not** own commercial records, take-off packages, or CRM. They do **not** decide for the user.

## Current implementation

### Employment vs Entrepreneurship Decision Tool

Internal / working name: **Business Owner Assessment**.

Public branded route (login-exempt, shareable by link):

`/decision-tools/employment-vs-entrepreneurship`

Office navigation: Plan → Employment vs Entrepreneurship.

Guided progression:

TODAY → BUSINESS → MARKET → COSTS → RESULTS

Startup & Transition Cash is a compact section inside COSTS.

Core baseline:

- employment economic value (wages plus user-supplied benefits / retirement / other compensation)
- entrepreneurship economic value
- difference
- effective owner hourly return
- break-even selling rate
- What Has to Be True

Practical completeness:

- Startup & Transition Cash (floored at zero)
- Downside Stress Test (three independent 10% cases)
- Total Owner Workload
- Cash Available to Owner before personal income tax (same residual as entrepreneurship economic value)
- Download Results PDF (same `calculate()` result as the screen; ReportLab format-only renderer; optional scenario name; no DB persistence)

Trade/profile defaults are **starting assumptions only**. User-entered values override them. A helper/employee is optional.

## Explicit exclusions

Tax engines; financing; depreciation/CCA; multi-year forecast; accounting statements; Monte Carlo; business valuation; CRM; bookkeeping; business-plan generator; recommendation / winner / score / traffic-light; cloud save; scenario history; email delivery.

## Ownership boundary

This module does **not** own Plan Intelligence drawings/take-off, Estimating estimates, Proposals, or Project Controls records. Calculation is stateless. No schema. No migration.
