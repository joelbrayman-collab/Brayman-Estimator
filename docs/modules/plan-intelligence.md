# Module — Plan Intelligence (proposed)

| Attribute | Value |
|-----------|--------|
| Status | **Future** — not implemented |
| Updated | 2026-07-25 |
| Code | None |
| Architecture | [../architecture/plan-intelligence-and-automated-takeoff.md](../architecture/plan-intelligence-and-automated-takeoff.md) |

## Purpose

Ingest construction plans, support classification/scale/measurement, produce source-traceable take-off quantities, and hand reviewed quantities to Estimating only after human approval.

## Owned data (intended)

Plan documents, sheets, measurements, take-off versions, citations, review audit events.

## Referenced data

Projects (scope); Estimating assemblies/cost items (mapping targets only).

## Prohibited responsibilities

- Owning live estimate lines
- Silent estimate mutation
- Supplier catalogue ownership
- Proposal PDF ownership

## Relevant ADRs

ADR-005, ADR-006, ADR-007, ADR-009, ADR-010 (all Proposed).
