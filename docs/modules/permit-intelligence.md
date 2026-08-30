# Module — Permit Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Pass 1 foundation Current (FG-015)** — **CLOSED / OPERATIONAL FOR UAT**. Pass 2 **[FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING**. Architecture **Accepted** (ADR-037/038/039). |
| Updated | 2026-08-30 |
| Code | Pass 1: `app/models/project.py` (`PermitProfile`, `ProjectLocation`), `app/services/permit_foundation.py`. Pass 2: `app/models/permit_intelligence.py`, `app/services/permit_intelligence.py`, `app/services/permit_report_pdf.py`, Hub panel in `app/templates/projects/detail.html`, report at `/projects/<id>/permit-report`. Platform rules: `permit_rules`. |
| Architecture | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [permit-rules-library.md](../architecture/permit-rules-library.md) · [permit-rules-ontario-ottawa-sources.md](../architecture/permit-rules-ontario-ottawa-sources.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) |
| Feature Gate | [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (not CLOSED). |

## Purpose

Own the **project-tied Permit Intelligence** preflight/analysis capability and the **Permit & Approvals Report** snapshot. This is advisory project intelligence, not AHJ approval.

The capability lives on the `Project` hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). Projects remains the lifecycle owner; this module doc names the capability so ownership is not implicit (Rule 1).

## Owned records

- Preliminary Permit Profile (Pass 1) — Projects-owned `permit_profiles`
- Project-specific analysis and Permit & Approvals Report snapshots (Pass 2) — `permit_analyses` / `permit_findings` (`SUBSTANTIVE_BOUNDED`)
- Recheck / stale flags against prior snapshots — location/context (FG-015) plus plan/site, facts, and rule supersession (FG-016)
- Reviewed project permit facts (not legal conclusions) — `project_permit_facts`

Permit Rules Library records are **platform-governed sources**, not organization commercial intelligence. V1: **10 APPROVED** Ontario / Ottawa coach-house rules.

## Referenced data

- Project location / resolved jurisdiction ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) — implemented (reuse; no second resolver)
- Plan / site-plan versions (Plan Intelligence, read-through; no mutation; no Phase D)
- Project type / commercial context (read-through; not mutated)

## Prohibited responsibilities

- Replacing the AHJ or issuing permits
- Live web lookup / external AI as regulatory truth
- Auto-creating estimate lines
- Generating contract legal language
- Owning BUILD post-issuance inspections
- Owning Ontario contract/warranty templates (Legal Content Gate)
- Mutating take-off evidence
- Phase D estimate mapping
- Approving regulatory content via AI
- National rules library
- Municipal submissions

## Current implementation

FG-015 Pass 1 remains `PRELIMINARY_FOUNDATION`. FG-016 Pass 2 is a **separate** substantive snapshot:

- Deterministic evaluation against APPROVED currently-effective rules
- Finding statuses: PASS, VERIFY, MISSING INFORMATION, POTENTIAL NON-CONFORMANCE, ADDITIONAL APPROVAL LIKELY, NOT APPLICABLE
- PASS = no issue identified against the governed checks performed — never AHJ / permit / zoning approved
- Office HTML report + optional neutral CalibAi PDF of the **same** snapshot
- Unsupported jurisdiction/use: **RULE COVERAGE NOT AVAILABLE** (no Ottawa fallback)
- Graph head `f8a9b0c1d2e3`; live current remains `e7f8a9b0c1d2`

## Dependencies

- [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) for location / jurisdiction / preliminary profile (**CLOSED / OPERATIONAL FOR UAT**)
- [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) for bounded curated Ontario / Ottawa rules + Mike Pratt POC (**IMPLEMENTED / LIVE MIGRATION PENDING**)

## Related

- [modules/projects.md](projects.md)
- [modules/plan-intelligence.md](plan-intelligence.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
