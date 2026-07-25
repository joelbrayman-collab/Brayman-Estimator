# Module — Estimating

| Attribute | Value |
|-----------|--------|
| Status | **Current** (core implemented) |
| Updated | 2026-07-25 |
| Code | `app/models/cost_item.py`, `assembly.py`, `estimate.py`; `app/routes/cost_library.py`, `assemblies.py`, `estimates.py`; `app/services/estimates.py`, `estimate_builder.py` |

## Purpose

Build and version construction estimates from cost libraries and assemblies, scoped to a project.

## Responsibilities

- Cost item library
- Assemblies and assembly items
- Estimates and estimate versions
- Sections and line items
- Version status / locking for issued-like statuses

## Owned data

- `cost_items`
- `assemblies`, `assembly_items`
- `estimates`, `estimate_versions`, `estimate_sections`, `estimate_line_items`

## Referenced data

- `projects` (FK)
- Optionally referenced by proposals and change orders via estimate / estimate_version FKs

## Prohibited responsibilities

- Final client-facing proposal layout/PDF ownership (Proposals module)
- Project change order lifecycle ownership (Project Controls / Projects)
- Accounting integrations

## Current implementation

- Estimate statuses and version statuses defined in `app/models/estimate.py`
- `AUTO_LOCK_VERSION_STATUSES` locks versions when Issued/Accepted/Rejected/Superseded
- Builder service supports structured line construction
- UI under Estimating nav section

## Planned capabilities

- Historical estimating intelligence — **Future**
- Deeper productivity tooling — Feature Gate required

## Dependencies

- Projects (and thus Clients)
- Consumed by Proposals (snapshot source) and Change Orders (optional version link)

## Invariants

- Estimate belongs to a Project
- Versions are numbered per estimate; prefer supersession over silent overwrite (Rule 5)
- Locked versions are read-only in UI/service rules (verify on change)

## Open decisions

- When estimate header status vs version status diverge—canonical source of truth for “accepted bid”

## Relevant tests

- `tests/test_estimates.py`
- `tests/test_estimate_builder.py`
- `tests/test_assemblies.py`

## Relevant ADRs

- None yet
