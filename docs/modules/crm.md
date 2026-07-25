# Module — CRM

| Attribute | Value |
|-----------|--------|
| Status | **Current** (partial CRM) |
| Updated | 2026-07-25 |
| Code | `app/models/client.py`, `app/routes/clients.py`, `app/templates/clients/` |

## Purpose

Maintain client (customer / owner) records used across projects and commercial documents.

## Responsibilities

- Create, view, update client contact and company information
- Serve as parent for projects

## Owned data

- `clients` table / `Client` model

## Referenced data

- None owned by other modules beyond being referenced by `Project.client_id`

## Prohibited responsibilities

- Estimating line pricing
- Proposal legal/commercial snapshot ownership
- Job costing / invoicing

## Current implementation

- Client list/detail/forms via `clients_bp`
- Fields: name, company, email, phone, address, notes, created_at
- Cascade: deleting client cascades projects (SQLAlchemy relationship) — treat carefully

## Planned capabilities

- Fuller CRM (contacts, pipeline, activities) — **Future** unless Feature-Gated
- Explicit soft-delete / archive policy — **Open decision**

## Dependencies

- Consumed by Projects, and indirectly by Estimates/Proposals via project/client snapshot fields on proposals

## Invariants

- Every Project must have a Client (`client_id` non-null)

## Open decisions

- Soft delete vs hard delete policy
- Whether “CRM” expands beyond Clients

## Relevant tests

- Indirect via projects/estimates/proposals fixtures (dedicated client suite: **to be verified** / may be embedded)

## Relevant ADRs

- None yet
