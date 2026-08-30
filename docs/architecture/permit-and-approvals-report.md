# Architecture — Permit Intelligence and Permit & Approvals Report

| Attribute | Value |
|-----------|--------|
| Status | **Pass 2 FUTURE / NOT IMPLEMENTED.** Pass 1 foundation **Current (FG-015)** — **CLOSED / OPERATIONAL FOR UAT**. Architecture **Accepted** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)) |
| Date | 2026-08-30 |
| Product | The Estimator / CalibAi |
| Canonical record | This document |
| Related | [jurisdiction-resolution.md](jurisdiction-resolution.md) · [project-document-package.md](project-document-package.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md) · [modules/projects.md](../modules/projects.md) · [modules/permit-intelligence.md](../modules/permit-intelligence.md) · [organization-brand-profile.md](organization-brand-profile.md) · [change-order-document-family.md](change-order-document-family.md) |

**Current vs future:** [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) implemented Pass 1 foundation (structured location, deterministic jurisdiction resolution, versioned preliminary Permit Profile, Hub PLAN presentation). There is still **no** Permit Intelligence analysis engine, substantive Permit & Approvals Report, Permit Rules Library, live regulatory lookup, or PASS findings. [FG-014](../feature-gates/FG-014-material-catalogue-v1-dimensional-lumber-sheet-goods.md) remains **CLOSED / OPERATIONAL FOR UAT**. Live current = head `e7f8a9b0c1d2`.

---

## Engine vs report

**Permit Intelligence** is a **project capability** (analysis / preflight).

The **Permit & Approvals Report** is its governed **document output**.

Do **not** reduce Permit Intelligence to a PDF form.

---

## Authority

CalibAi: **advisory preflight / project intelligence**.

AHJ / municipality / regulated professional: **final authority**.

The report does **not** replace the municipality, building official, planner, surveyor, engineer, septic authority, conservation authority, attorney, or other regulated professional.

**PASS** means only: **no issue identified against the governed checks performed.**

**PASS** must never mean: permit approved, zoning approved, or AHJ approved.

Preserve explicit advisory labeling. Do not treat ChatGPT, Cursor, or other tool research as an authoritative project permit determination.

---

## Two-pass model

**Pass 1**

```text
LOCATION + PROJECT TYPE
→ PRELIMINARY PERMIT PROFILE
```

May run while location is **LOCATION INCOMPLETE** ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)).

**Pass 2**

```text
PLANS + SITE PLAN + PROJECT FACTS + GOVERNED REQUIREMENTS
→ PROJECT-SPECIFIC PERMIT INTELLIGENCE
→ PERMIT & APPROVALS REPORT
```

Plan / take-off work may proceed concurrently where permit findings are not material blockers.

---

## Ontario-first implementation (not universal architecture)

Architect globally. Implement later in bounded jurisdictions.

| Reference | Value |
|-----------|--------|
| First jurisdiction | Ontario |
| First municipal case | City of Ottawa / North Gower |
| Reference project | Mike Pratt Coach House, 2562 Church Street, North Gower, Ontario |

Do **not** hard-code Ottawa as the universal architecture. Do **not** attempt a national library in the first product gate.

The Church Street case is a **future architecture / UAT reference only** — not an in-app project and not a permit determination. Preliminary review outside this repository is **not** governed evidence. 3415 Roger Stevens Road remains the commercial/document-package UAT reference ([testing/uat-reference-cases.md](../testing/uat-reference-cases.md)).

---

## Permit Rules Library

A governed **Permit / Planning / Approval Rules Library** is required for meaningful analysis. It is **separate** from the Contract / Warranty Legal Content Gate.

Future governed rule evidence should support: jurisdiction; authority/source; rule category; citation/source location; effective-from; effective-to/superseded; reviewed/retrieved date; provenance; applicability; approval/review state.

Do **not** populate the library in this pass. Do **not** use live scraping. AI **cannot** mark regulatory content approved.

---

## Plan Intelligence relationship

Read-through only. Future analysis may consume reviewed plan/site facts with provenance: footprint, height, setbacks, site dimensions, project type/use evidence, plan/site-plan identity.

Does **not** authorize Phase D. Does **not** allow Permit Intelligence to mutate take-off evidence. Does **not** allow automatic estimate insertion ([ADR-006](../adr/ADR-006-human-approval-before-estimate-insertion.md)).

---

## Finding / workflow policy

Not every finding blocks estimating. Distinguish approximately (conceptual; **not** product enums):

- informational
- verify / missing information
- material risk / potential non-conformance
- blocking commercial commitment where genuinely warranted

A material feasibility issue must be capable of being surfaced **before final commercial commitment**.

---

## Estimating and contracts

Permit Intelligence may later **identify** scope/cost implications (survey, grading, septic, engineering, variance, entrance permit, conservation approval, municipal fees). Do **not** auto-create `EstimateLineItem` rows. Future user-controlled action may propose adding allowance/cost. Human authority remains required.

Findings may later **inform** contract assumptions, qualifications, exclusions, and conditions precedent. Do **not** generate legal language here.

---

## BUILD boundary

Future **BUILD** may own permit/inspection **operational** evidence after issuance (permit number, issued date, inspections, occupancy/final status) ([ADR-020](../adr/ADR-020-build-module-boundary.md)). Permit Intelligence remains the **preflight / analysis** capability. Do not implement BUILD from this architecture.

---

## Report snapshot / immutability

```text
CURRENT GOVERNING RULES
→ CITED / VERSIONED ANALYSIS
→ PROJECT PERMIT REPORT SNAPSHOT
→ IMMUTABLE HISTORY
```

A report must pin: project; organization; project location; jurisdiction; project type; plan/version; site-plan/version; rule/source versions; findings; missing information; recommended actions; generated_at; provenance.

Later changes create a new report/version. Never rewrite historical issued reports ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

---

## Staleness / recheck

Support **RECHECK REQUIRED / STALE** without silently rewriting the prior report.

Triggers include: location change; project type change; plan revision; site-plan revision; material site/design fact change; governing requirement change.

---

## Project document classification

The Permit & Approvals Report is a governed **core project document**. It is **not** one of the four estimate-derived commercial outputs and **not** a Change Order transaction document.

```text
CORE DOCUMENTS / PACKAGES
+
TRANSACTION DOCUMENT FAMILIES
```

Do not force arbitrary document numbering.

---

## Organization branding

Organization Brand Profile remains **FUTURE / NOT IMPLEMENTED**. It is **not** a prerequisite for Permit Intelligence data/analysis. When customer-facing permit PDFs are later rendered, they consume the one Brand Profile. Do not create separate Permit-logo configuration.

---

## Assessment topics (where applicable)

Future reports may assess, where applicable: jurisdiction; zoning; permitted use; building permit requirement; lot area; building footprint; lot coverage; setbacks; height; parking; driveway/entrance; grading; drainage; private well; septic; municipal servicing; easements; rights-of-way; overhead services; conservation/environmental approvals; site plan control; heritage; development charges; minor variance/rezoning indicators; required engineering; permit-document completeness.

These are topic headings, not a claim that every topic applies to every project.

---

## Recommended Feature Gates

**First:** [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT** — structured Project location; jurisdiction resolver foundation; project-tied preliminary Permit Profile; advisory labeling; snapshot/provenance foundation.

Explicitly **not** in FG-015: national rules library; live web lookup; external AI; automatic zoning conclusions; municipal submissions; comprehensive Building Code engine; Phase D; automatic estimate insertion; contract generation; Permit Rules Library population.

**Second (not opened):** Ontario / Ottawa Permit Rules + Mike Pratt POC — a genuinely useful governed Permit & Approvals Report against a **bounded curated** rule set.

---

## This architecture does not authorize (beyond FG-015)

[FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) authorizes **foundation only**. This document still does **not** authorize:

- Pass 2 Permit Intelligence analysis / Permit Rules Library population
- live web lookup / external AI
- automatic zoning or permit conclusions
- municipal submissions
- national rules library
- Phase D
- automatic estimate insertion
- contract generation
- BUILD implementation
- Organization Brand Profile implementation

---

## Ownership

| Concern | Owner |
|---------|--------|
| Project location | Projects ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) |
| Jurisdiction resolver | Reusable platform architecture; consumed by Permit Intelligence and later tax/contracts/geography |
| Permit Intelligence analysis + report snapshot | Projects (project capability) |
| Plan / site-plan versions reviewed | Plan Intelligence (read-through) |
| Permit Rules Library | Platform governed source; **not** the Legal Content Gate |
| Post-issuance permit/inspection operations | BUILD (future; [ADR-020](../adr/ADR-020-build-module-boundary.md)) |
| Commercial estimate outputs 1–4 | Unchanged |

---

## Related

- [jurisdiction-resolution.md](jurisdiction-resolution.md)
- [project-document-package.md](project-document-package.md)
- [governance/legal-content-and-templates.md](../governance/legal-content-and-templates.md)
- [testing/uat-reference-cases.md](../testing/uat-reference-cases.md)
- [modules/permit-intelligence.md](../modules/permit-intelligence.md)
- [modules/projects.md](../modules/projects.md)
- [plan-intelligence-and-automated-takeoff.md](plan-intelligence-and-automated-takeoff.md)
- [organization-brand-profile.md](organization-brand-profile.md)
- [change-order-document-family.md](change-order-document-family.md)
