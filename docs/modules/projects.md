# Module — Projects

| Attribute | Value |
|-----------|--------|
| Status | **Current** (project records + change orders package). [FG-011](../feature-gates/FG-011-project-hub-ux.md) Project Hub UX **CLOSED / OPERATIONAL FOR UAT** |
| Updated | 2026-08-30 |
| Code | `app/models/project.py`, `app/routes/projects.py`, `app/services/project_hub.py`; Project Controls: `app/project_controls/` |
| Feature Gate | [FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **IMPLEMENTED / VERIFIED / COMMITTED / PUSHED / LIVE MIGRATION PENDING** (Hub PLAN Permit Report state + `/projects/<id>/permit-report`). |

## Purpose

Represent construction projects tied to clients; host estimating work; begin project controls (change orders). Long-term home for budgets, scheduling, purchasing, and job cost—**only when Feature-Gated**.

## Responsibilities (current)

- Project CRUD (name, number, address, status, description, client)
- Parent for estimates
- Change Orders lifecycle (draft → approval statuses) via `project_controls` package
- Project Hub UX at `/projects/<id>` ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**): identity, versioned commercial context, PLAN / PRICE / CONTRACT stored facts and links, existing Change Orders under BUILD; MONITOR / LEARN / field BUILD labeled Future. Read-only assembly in `app/services/project_hub.py`. No durable hub entity. [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) PLAN **PERMIT & APPROVALS** foundation state — **CLOSED / OPERATIONAL FOR UAT**. [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) extends the same panel with truthful Gate-2 state (report available, last analysis, plan/site basis, attention count, recheck yes/no) and the office HTML/PDF report.

## Owned data

- `projects`
- `project_locations` (1:1 civic location; FG-015)
- `permit_profiles` (versioned preliminary snapshots; FG-015)
- `permit_analyses`, `permit_findings`, `project_permit_facts` (FG-016 project-tied Pass 2; organization-scoped)
- `change_orders`, `change_order_items` (package-owned tables)

Platform-shared (not org-owned): `jurisdiction_definitions`, `jurisdiction_aliases`, `permit_rules`.

## Referenced data

- `clients` (required FK)
- Optional `estimate_versions` on change orders

## Prohibited responsibilities

- Owning proposal snapshot documents (Proposals)
- Owning cost library master data (Estimating)
- Owning Plan Intelligence / take-off / labour catalog / pricing-policy records (read/link only under FG-011)
- Full ERP/accounting
- Field-execution records (proposed **BUILD** module — [build.md](build.md); [ADR-020](../adr/ADR-020-build-module-boundary.md))
- Permit Intelligence / jurisdictional legal library / live regulatory lookup / in-product web lookup / automatic permit approval conclusions / municipal submissions — Pass 2 **[FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) IMPLEMENTED / LIVE MIGRATION PENDING**. Live lookup / municipal submissions remain **not authorized**. Foundation **CLOSED / OPERATIONAL FOR UAT**: [FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md). Architecture **Accepted**: [ADR-037](../adr/ADR-037-project-location-and-jurisdiction-resolution.md) / [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md) / [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md). Projects owns project location, project-tied resolution, the profile/snapshot relationship, and project-tied permit facts / report versions. Permit Rules Library is platform-governed, not org commercial intelligence.
- Organization Brand Profile / org-owned logo storage — **not authorized**. Pin only: [organization-brand-profile.md](../architecture/organization-brand-profile.md).
- Change Order document-family rewrite, client email, field-native UX, or a second Change Order entity — **not authorized**. Pin only: [change-order-document-family.md](../architecture/change-order-document-family.md). Existing Change Order business record remains authoritative.

## Current implementation

- Project statuses include default `Lead` (model default)
- Change Orders: statuses in `CHANGE_ORDER_STATUSES`; list/detail/PDF support in package
- Nav: Change Orders enabled; Purchase Orders & Job Costing **disabled placeholders**

## Planned capabilities

- Project Hub UX — **Current** ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**)
- Project creation from accepted proposal snapshot (Rule 4) — **Future** (not FG-011)
- Project budgets, scheduling, purchasing, job costing, invoicing — **Future**
- Change order audit trail UI — noted as future in template
- Project location / jurisdiction resolver / preliminary Permit Profile — **CLOSED / OPERATIONAL FOR UAT** ([FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md)). Preserve `Project.address`.
- Project Permit Intelligence Pass 2 / Permit & Approvals Report analysis — **IMPLEMENTED / LIVE MIGRATION PENDING** ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md); [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md); ADR-037/038/039).
- Change Order governed document family / preview-generate-email / field UX — **FUTURE / NOT IMPLEMENTED** pin ([change-order-document-family.md](../architecture/change-order-document-family.md)); not a Feature Gate; do not create a second Change Order entity

## Dependencies

- CRM Clients
- Estimating (child estimates)
- Proposals (future acceptance handoff)

## Invariants

- Project requires Client
- Financially significant change-order approvals should become auditable (Rule 6) — gap acknowledged
- `Project` is the CalibAi lifecycle hub ([ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**)
- BUILD references Change Orders; it does not replace them ([ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**)

## Open decisions

- Whether Project Controls becomes its own top-level module doc
- MONITOR implementation remains **not started**. Baseline governance is [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (composed frozen baseline; Project Gross Margin). Actuals and MONITOR UI are not implemented.

## Relevant tests

- `tests/test_permit_foundation_fg015.py`
- `tests/test_project_hub.py`
- `tests/test_change_orders.py`
- Project fixtures embedded across estimate/proposal tests

## Relevant ADRs

- [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**
- [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR not implemented)
