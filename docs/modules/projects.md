# Module — Projects

| Attribute | Value |
|-----------|--------|
| Status | **Current** (project records + change orders package) |
| Updated | 2026-08-28 |
| Code | `app/models/project.py`, `app/routes/projects.py`; Project Controls: `app/project_controls/` |

## Purpose

Represent construction projects tied to clients; host estimating work; begin project controls (change orders). Long-term home for budgets, scheduling, purchasing, and job cost—**only when Feature-Gated**.

## Responsibilities (current)

- Project CRUD (name, number, address, status, description, client)
- Parent for estimates
- Change Orders lifecycle (draft → approval statuses) via `project_controls` package

## Owned data

- `projects`
- `change_orders`, `change_order_items` (package-owned tables)

## Referenced data

- `clients` (required FK)
- Optional `estimate_versions` on change orders

## Prohibited responsibilities

- Owning proposal snapshot documents (Proposals)
- Owning cost library master data (Estimating)
- Full ERP/accounting
- Field-execution records (proposed **BUILD** module — [build.md](build.md); [ADR-020](../adr/ADR-020-build-module-boundary.md))

## Current implementation

- Project statuses include default `Lead` (model default)
- Change Orders: statuses in `CHANGE_ORDER_STATUSES`; list/detail/PDF support in package
- Nav: Change Orders enabled; Purchase Orders & Job Costing **disabled placeholders**

## Planned capabilities

- Project creation from accepted proposal snapshot (Rule 4) — **Future / Next candidate**
- Project budgets, scheduling, purchasing, job costing, invoicing — **Future**
- Change order audit trail UI — noted as future in template

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
- Budget / MONITOR baseline source of truth after acceptance ([ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Proposed**)

## Relevant tests

- `tests/test_change_orders.py`
- Project fixtures embedded across estimate/proposal tests

## Relevant ADRs

- [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted**
- [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted**
- [ADR-021](../adr/ADR-021-monitor-commercial-baseline.md) **Proposed**
