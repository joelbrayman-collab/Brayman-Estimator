# Module — Projects

| Attribute | Value |
|-----------|--------|
| Status | **Current** (project records + change orders package). [FG-011](../feature-gates/FG-011-project-hub-ux.md) Project Hub UX **CLOSED / OPERATIONAL FOR UAT** |
| Updated | 2026-08-30 |
| Code | `app/models/project.py`, `app/routes/projects.py`, `app/services/project_hub.py`; Project Controls: `app/project_controls/` |
| Feature Gate | [FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT** |

## Purpose

Represent construction projects tied to clients; host estimating work; begin project controls (change orders). Long-term home for budgets, scheduling, purchasing, and job cost—**only when Feature-Gated**.

## Responsibilities (current)

- Project CRUD (name, number, address, status, description, client)
- Parent for estimates
- Change Orders lifecycle (draft → approval statuses) via `project_controls` package
- Project Hub UX at `/projects/<id>` ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**): identity, versioned commercial context, PLAN / PRICE / CONTRACT stored facts and links, existing Change Orders under BUILD; MONITOR / LEARN / field BUILD labeled Future. Read-only assembly in `app/services/project_hub.py`. No durable hub entity.

## Owned data

- `projects`
- `change_orders`, `change_order_items` (package-owned tables)

## Referenced data

- `clients` (required FK)
- Optional `estimate_versions` on change orders

## Prohibited responsibilities

- Owning proposal snapshot documents (Proposals)
- Owning cost library master data (Estimating)
- Owning Plan Intelligence / take-off / labour catalog / pricing-policy records (read/link only under FG-011)
- Full ERP/accounting
- Field-execution records (proposed **BUILD** module — [build.md](build.md); [ADR-020](../adr/ADR-020-build-module-boundary.md))
- Permit Intelligence / jurisdictional legal library / live regulatory lookup / in-product web lookup / automatic permit approval conclusions / municipal submissions — **not authorized**. The Project Permit & Approvals Report is a **FUTURE / NOT IMPLEMENTED** pin only ([permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md)). Projects is the tentative future owner of the project-tied snapshot; that ownership is **not confirmed as implemented** and must be verified in a later reconnaissance. This pin does not expand FG-011.

## Current implementation

- Project statuses include default `Lead` (model default)
- Change Orders: statuses in `CHANGE_ORDER_STATUSES`; list/detail/PDF support in package
- Nav: Change Orders enabled; Purchase Orders & Job Costing **disabled placeholders**

## Planned capabilities

- Project Hub UX — **Current** ([FG-011](../feature-gates/FG-011-project-hub-ux.md) **CLOSED / OPERATIONAL FOR UAT**)
- Project creation from accepted proposal snapshot (Rule 4) — **Future** (not FG-011)
- Project budgets, scheduling, purchasing, job costing, invoicing — **Future**
- Change order audit trail UI — noted as future in template
- Project Permit & Approvals Report — **FUTURE / NOT IMPLEMENTED** pin ([permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md)); not a Feature Gate

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

- `tests/test_project_hub.py`
- `tests/test_change_orders.py`
- Project fixtures embedded across estimate/proposal tests

## Relevant ADRs

- [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**
- [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Accepted** (MONITOR not implemented)
