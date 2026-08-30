# Architecture pin — Project Permit & Approvals Report

| Attribute | Value |
|-----------|--------|
| Status | **FUTURE / NOT IMPLEMENTED** — requirement pin only |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [project-document-package.md](project-document-package.md) · [testing/uat-reference-cases.md](../testing/uat-reference-cases.md) · [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) · [modules/projects.md](../modules/projects.md) |

**Current vs future:** The office app has **no** Permit & Approvals Report, Permit Intelligence, jurisdictional legal library, live regulatory lookup, or permit-report schema. Nothing below is implemented. This pin does **not** change [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) (**CLOSED / OPERATIONAL FOR UAT**). Next governed work is a separate Permit Intelligence architecture reconnaissance — not implementation.

---

## Purpose

CalibAi must eventually support a governed **PROJECT PERMIT & APPROVALS REPORT** generated **early** in the project lifecycle so permit, zoning, servicing, and other approval issues can affect **feasibility, scope, pricing, and contracting** before those decisions harden.

Inputs (intended):

```text
PROJECT ADDRESS / JURISDICTION
+ SITE / PROPERTY INFORMATION
+ PROJECT TYPE
+ PLANS / SITE PLAN
+ CURRENT GOVERNING MUNICIPAL / PROVINCIAL / STATE REQUIREMENTS
```

The report is an **ADVISORY PREFLIGHT**.

It does **not** replace:

- municipality / Authority Having Jurisdiction (AHJ)
- building official
- planner
- surveyor
- engineer
- septic authority
- conservation authority
- attorney or other regulated professional

**FINAL AUTHORITY** remains with the governing AHJ.

Do not treat ChatGPT, Cursor, or other tool research as an authoritative project permit determination.

---

## This pin does not authorize

- Permit Intelligence implementation
- jurisdictional legal-library implementation
- live regulatory AI
- web lookup inside the product
- automatic permit approval conclusions
- municipal submissions
- schema
- migration
- ADR
- Feature Gate

A **separate repository-first architecture reconnaissance** must verify and govern this capability **before** any implementation prompt.

---

## Intended assessment topics (where applicable)

Future reports should assess, where applicable:

- jurisdiction
- zoning
- permitted use
- building permit requirement
- lot area
- building footprint
- lot coverage
- setbacks
- height
- parking
- driveway / entrance
- grading
- drainage
- private well
- septic
- municipal servicing
- easements
- rights-of-way
- overhead services
- conservation / environmental approvals
- site plan control
- heritage
- development charges
- minor variance / rezoning indicators
- required engineering
- permit-document completeness

These are **topic headings for later architecture**, not a claim that every topic applies to every project.

---

## Intended status vocabulary (conceptual only)

Future status language should support concepts such as:

- PASS
- VERIFY
- POTENTIAL NON-CONFORMANCE
- ADDITIONAL APPROVAL LIKELY
- MISSING INFORMATION
- NOT APPLICABLE

**Do not treat these as final product enums under this pin.** Enums, labels, and fail-closed rules require the later reconnaissance / ADR / Feature Gate pass.

---

## Project document package

The Permit & Approvals Report is an **additional governed project document**. It is **not** one of the four estimate-derived commercial outputs (internal breakdown, customer estimate/Proposal, QuickBooks export, Ontario contract).

It must be retained with the project's other authoritative/generated documents and tied to:

- project
- address / jurisdiction
- plan / version reviewed
- site-plan version reviewed
- governing-rule source / version / effective date
- report generation date
- evidence / provenance

Later plan or by-law changes must **not** silently rewrite an earlier permit report. Supersede or generate a new version; keep history.

See [project-document-package.md](project-document-package.md).

---

## Freshness

Permit, zoning, legal, and regulatory information is **time-sensitive**.

Future architecture must preserve:

```text
CURRENT RULE LOOKUP
→ CITED / VERSIONED PERMIT ANALYSIS
→ PROJECT REPORT SNAPSHOT
→ IMMUTABLE HISTORY
```

The system must be able to identify when an older permit report requires **re-check** because:

- plans changed
- site plan changed
- project scope changed
- address / jurisdiction changed
- governing requirements changed

Current-rule lookup is **not** a license to mutate historical snapshots.

---

## Future UAT / architecture reference case — Mike Pratt Coach House

| Field | Value |
|-------|--------|
| Project | Mike Pratt Coach House |
| Address | 2562 Church Street, North Gower, Ontario |
| Status | **Future architecture / UAT reference only** — not an in-app project, not a permit determination |
| Recorded | 2026-08-30 |

Current **preliminary** review (outside this repository, not governed evidence) has already shown useful permit-preflight questions, including:

- coach-house footprint
- building height
- setbacks
- private servicing / septic
- rural grading-plan requirements
- zoning / site-plan submission completeness

That preliminary review is **not** an authoritative AHJ determination and **must not** be copied into product as facts.

Also see [testing/uat-reference-cases.md](../testing/uat-reference-cases.md). The existing 3415 Roger Stevens Road case remains the commercial/document-package UAT reference; this Church Street case is the **permit-preflight** reference.

---

## Intended ownership (to be confirmed in reconnaissance)

Not implemented. Tentative boundary for later governance:

| Concern | Likely owner (to be verified) |
|---------|-------------------------------|
| Project-tied report snapshot / history | Projects (lifecycle hub) |
| Plan / site-plan versions reviewed | Plan Intelligence |
| Governing municipal / provincial / state requirement sources | **Not implemented.** Not the Legal Content Gate for Ontario contract/warranty. Requires later reconnaissance. Must not invent law. |
| Commercial estimate outputs 1–4 | Unchanged — [project-document-package.md](project-document-package.md) |

Do **not** create a Permit Intelligence module, legal-library register, or schema from this pin.

---

## Related

- [project-document-package.md](project-document-package.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md) (Ontario contract/warranty templates — **distinct**; this pin does not authorize that library or live regulatory lookup)
- [testing/uat-reference-cases.md](../testing/uat-reference-cases.md)
- [modules/projects.md](../modules/projects.md)
- [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md)
- [organization-brand-profile.md](organization-brand-profile.md) — **FUTURE / NOT IMPLEMENTED** branding source for later generated reports
