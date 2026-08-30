# Module — Permit Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Pass 1 foundation Current (FG-015)** — **LIVE MIGRATION PENDING**. Pass 2 **not implemented**. Architecture **Accepted** (ADR-037/038/039). |
| Updated | 2026-08-30 |
| Code | Pass 1 records are **Projects-owned**: `app/models/project.py` (`PermitProfile`, `ProjectLocation`), `app/services/permit_foundation.py`, Hub panel in `app/templates/projects/detail.html`. Platform definitions: `app/models/jurisdiction.py`, `app/services/jurisdiction.py`. No Pass 2 analysis module. |
| Architecture | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) |
| Feature Gate | [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED** — **LIVE MIGRATION PENDING** (foundation only; Pass 2 not this gate). **Not CLOSED.** |

## Purpose

Own the **project-tied Permit Intelligence** preflight/analysis capability and the **Permit & Approvals Report** snapshot. This is advisory project intelligence, not AHJ approval.

The capability lives on the `Project` hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). Projects remains the lifecycle owner; this module doc names the capability so ownership is not implicit (Rule 1).

## Intended owned records (when Feature-Gated)

- Preliminary Permit Profile (Pass 1) — **implemented as Projects-owned `permit_profiles`**
- Project-specific analysis and Permit & Approvals Report snapshots (Pass 2) — **not implemented**
- Recheck / stale flags against prior snapshots — **Gate-1 location/context recheck implemented**; plan/rule recheck is Gate 2

Permit Rules Library records are **platform-governed sources**, not organization commercial intelligence. **Not populated.**

## Referenced data (intended)

- Project location / resolved jurisdiction ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md)) — **implemented**
- Plan / site-plan versions and reviewed measurements (Plan Intelligence, read-through) — **not consumed in V1**
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

## Current implementation

FG-015 Pass 1 foundation only:

- Versioned `PermitProfile` snapshots (`PRELIMINARY_FOUNDATION`), advisory **PRELIMINARY / FOUNDATION ONLY**
- Plan/site review = `NOT_PERFORMED`; substantive analysis = `NOT_AVAILABLE`
- No findings, no PASS, no zoning conclusions
- No Permit Rules Library tables or seed
- Live schema apply **pending** (`e7f8a9b0c1d2` is graph head; live current `d6e7f8a9b0c1`)

## Dependencies

- [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) for location / jurisdiction / preliminary profile (**implemented; live migration pending**)
- Later Feature Gate for bounded curated rules before a useful Pass 2 report
- Organization Brand Profile only when rendering customer-facing PDFs (not required for analysis)

## Related

- [modules/projects.md](projects.md)
- [modules/plan-intelligence.md](plan-intelligence.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
