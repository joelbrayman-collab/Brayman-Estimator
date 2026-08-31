# Module — BUILD

| Attribute | Value |
|-----------|--------|
| Status | **Proposed / Intended** — **not implemented** |
| Updated | 2026-08-31 |
| Code | None |
| ADR | [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** (boundary only). [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Proposed / FOR JOEL REVIEW** (field evidence / dual-surface architecture; **not Accepted**; does **not** authorize implementation). |
| CAR | [CAR-001](../architecture/CAR-001-calibai-product-architecture-reconciliation.md) |

## Purpose

Own **field-execution records** for a Project so CalibAi can connect BUILD to the same authoritative project record used for PLAN / PRICE / CONTRACT.

Two first-class surfaces share one BUILD system of record ([ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Proposed**): **desktop / office** (review, management, confirmation) and **field / iPhone** (fast capture). Neither is scaffolding for the other. Office HTML continues to call Flask services directly. Field Web (Item 12) consumes Shared API → the same services. A Proposed ADR is **not** implementation.

## Intended owned records (when Feature-Gated)

**First BUILD domain (ADR-042 Proposed, not implemented):** Field Capture Event; Original Payloads (`text` / `audio` / `image`); Derived Candidates (`PROPOSED` / `CONFIRMED` / `REJECTED`). Later BUILD may still expand toward daily execution, crews, labour capture, subcontractor activity, material use, deliveries, equipment, progress, schedule/task updates, RFIs/issues, inspections, and field documentation as separately gated. After permit **issuance**, BUILD may own operational evidence such as permit number, issued date, inspections, occupancy/final status — not the preflight analysis.

## Referenced data (intended)

- `projects` (lifecycle hub — [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md))
- Change Orders (Project Controls) — **reference only**
- Plan Intelligence documents/sheets — **reference only**
- Estimating lines/tasks — **reference only**; actuals must not rewrite approved estimates ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted**, [ADR-024](../adr/ADR-024-learn-recommendation-boundary.md))

## Prohibited responsibilities

- Owning Change Order commercial lifecycle (Project Controls)
- Owning estimates, cost library, or proposals
- Owning plan PDF binaries (Plan Intelligence)
- Silent AI write of labour/material/progress without human confirmation ([ADR-023](../adr/ADR-023-field-evidence-provenance.md))
- Owning Permit Intelligence preflight analysis ([permit-intelligence.md](permit-intelligence.md); [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md)). BUILD may later own **post-issuance** permit/inspection operational evidence only.

## Current implementation

**None.** No BUILD models, routes, or UI.

## Dependencies

- Authentication before field capture ([ADR-022](../adr/ADR-022-field-client-and-shared-api.md); [ADR-041](../adr/ADR-041-user-membership-and-office-authentication.md) **Accepted**; [FG-018](../feature-gates/FG-018-organization-authentication-actor-identity-and-membership-v1.md) **CLOSED / OPERATIONAL FOR UAT**; [FG-019](../feature-gates/FG-019-shared-api-foundation-v1.md) **CLOSED / OPERATIONAL FOR UAT**). Item 11 BUILD is **ELIGIBLE FOR SEPARATE GOVERNANCE / NOT AUTHORIZED**.
- Feature Gate + approved Cursor prompt before any code

## Related

- [ADR-042](../adr/ADR-042-build-field-evidence-and-iphone-first-capture.md) **Proposed / FOR JOEL REVIEW**
- [modules/projects.md](projects.md) (Change Orders)
- [modules/plan-intelligence.md](plan-intelligence.md)
- [modules/monitor.md](monitor.md) (comparison layer; does not own BUILD actuals)
