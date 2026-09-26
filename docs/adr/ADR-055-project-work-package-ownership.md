# ADR-055 — Project Work Package Ownership

| Field | Value |
|-------|--------|
| Title | ADR-055: Project Work Package Ownership |
| Status | Accepted |
| Date | 2026-09-26 |

## Context

The accepted product path is project, plans, confirmed scope, internal or subcontracted, then an estimate built underneath. Calculation engines stay infrastructure.

`ProjectWorkElement` is the later build and schedule breakdown. An estimate section is how the finished estimate is organized. `EstimateScopeDelivery` records delivery only after an estimate line already exists. None of those is the confirmed piece of project scope that exists before an estimate.

## Decision

Estimating owns `ProjectWorkPackage` (`project_work_packages`).

One row is one confirmed piece of project scope. It belongs to one organization and one project. Its work identity is an existing `WorkElementTemplate` from the work catalog, including the shared baseline. It does not create a second trade catalog.

Delivery is `INTERNAL` (Our crew) or `SUBCONTRACT` (Subcontractor). Mixed delivery is separate packages.

Source is contractor knowledge, or an optional plan document on the same project. A plan is not required.

Status may be `SUGGESTED`, `CONFIRMED`, or `RETIRED`. This slice only creates `CONFIRMED`. A person confirms it. Retire keeps the row. There is no destructive delete.

The row stores who confirmed it and when. The office page calls `confirm_package`. It does not own the rule. Delivery is stored as `INTERNAL` or `SUBCONTRACT`. The page labels those Our crew and Subcontractor. A plan reference is a `PlanDocument` on the project, not page state. The same service can later be called from another interface. This slice does not add an API, a phone app, or a public site.

The row does not store an engine, a cost, a labour rate, a margin, a subcontractor, an estimate section, or an estimate line.

Later, a confirmed internal package may feed a calculation and then the existing estimate mapper. Later, a confirmed subcontracted package may feed My Subcontractors and an RFQ. Later, the package may record which estimate section and lines it produced. Those links are not in this table yet.

## Alternatives Considered

- Reuse `ProjectWorkElement` — rejected. That object is downstream build and schedule work.
- Reuse an estimate section — rejected. A section is an estimate output.
- Reuse `EstimateScopeDelivery` — rejected. It requires an estimate line that does not exist yet.

## Consequences

Ben can name project work and who will do it while looking at uploaded plans, before any quantity or price exists. Later engines and RFQs have a human-confirmed spine. This slice does not calculate, price, or send anything.

## Module Ownership Impact

Estimating gains `ProjectWorkPackage`. Plan Intelligence still owns plan documents. The work catalog still owns work types and element templates. Project work structure still owns the build breakdown.

## Data Ownership Impact

`project_work_packages` is Estimating-owned. It references `organizations`, `projects`, `work_element_templates`, optional `plan_documents`, and optional `users`. It does not own those records.

## Migration Impact

Required in git: `k1f2a3b4c5d6` revises `j0e1f2a3b4c5`. Not applied to the Mac primary. Not applied to the hosted validation database. The Mac primary remains `h8c9d0e1f2a3`. The hosted validation database remains `j0e1f2a3b4c5`.

## Testing Impact

`tests/test_project_work_packages.py`. Current-head assertions point at `k1f2a3b4c5d6`. S16 identity remains `h8c9d0e1f2a3`.

## Documentation Impact

Estimating module, architecture, current-state, session-handoff, roadmap, workflow log, and the manual-impact log.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Product direction accepted through the Architect prompt | 2026-09-26 |
| ChatGPT review | PROJECT SCOPE — WORK PACKAGE FOUNDATION | 2026-09-26 |
| Cursor implementation note | Implemented. Not live-migrated. Not deployed. | 2026-09-26 |
