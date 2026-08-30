# Module — Permit Intelligence

| Attribute | Value |
|-----------|--------|
| Status | **Proposed / Intended** — **not implemented**. Architecture **Accepted** (ADR-037/038/039). [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **IMPLEMENTATION NOT STARTED** (foundation only). |
| Updated | 2026-08-30 |
| Code | None |
| Architecture | [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · [jurisdiction-resolution.md](../architecture/jurisdiction-resolution.md) |
| Feature Gate | [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **APPROVED FOR IMPLEMENTATION** / **NOT STARTED** (foundation only; Pass 2 not this gate) |

## Purpose

Own the **project-tied Permit Intelligence** preflight/analysis capability and the **Permit & Approvals Report** snapshot. This is advisory project intelligence, not AHJ approval.

The capability lives on the `Project` hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md)). Projects remains the lifecycle owner; this module doc names the capability so ownership is not implicit (Rule 1).

## Intended owned records (when Feature-Gated)

- Preliminary Permit Profile (Pass 1)
- Project-specific analysis and Permit & Approvals Report snapshots (Pass 2)
- Recheck / stale flags against prior snapshots

Permit Rules Library records are **platform-governed sources**, not organization commercial intelligence.

## Referenced data (intended)

- Project location / resolved jurisdiction ([ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md))
- Plan / site-plan versions and reviewed measurements (Plan Intelligence, read-through)
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

**None.** No models, routes, or UI.

## Dependencies

- [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) for location / jurisdiction / preliminary profile (**approved; not started**)
- Later Feature Gate for bounded curated rules before a useful Pass 2 report
- Organization Brand Profile only when rendering customer-facing PDFs (not required for analysis)

## Related

- [modules/projects.md](projects.md)
- [modules/plan-intelligence.md](plan-intelligence.md)
- [modules/build.md](build.md)
- [modules/estimating.md](estimating.md)
