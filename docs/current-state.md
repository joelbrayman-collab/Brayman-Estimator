# Current State — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Operational snapshot |
| Updated | 2026-07-25 |
| Evidence | Local repository inspection |

Keep short. Refresh often. Mark unverified facts explicitly.

## Baseline

| Field | Value |
|-------|--------|
| Branch | `main` |
| HEAD | `c59ec01` — Accepted proposal immutability (+ prior docs commits) |
| Pre-governance base | `7b8d5ca` |
| Remote | Confirm with `git status -sb` |
| Working tree | Uncommitted M004 docs + M005 Phase A code/docs (confirm `git status`) |
| App | Flask factory `app.create_app` |
| DB default | SQLite `brayman_estimator.db` under instance |
| Governance | Active — Constitution, ADRs, Feature Gates, Plan Intelligence Phase A |

## Implemented capabilities (evidenced)

- Clients, Projects, Cost Items, Assemblies
- Estimates with versions, sections, line items; locking for certain statuses
- Proposal templates; snapshot proposals; preview; PDF
- **Accepted proposal immutability** (service-layer guard)
- Change Orders (Project Controls)
- **Plan Intelligence Phase A** — project-scoped PDF upload, private storage, list/detail/download/delete, searchable flag
- Dashboard / branding / navigation

## Not implemented (strategic)

- Plan Intelligence Phases B–G (sheet/scale/take-off/AI/estimate mapping)
- Drawing Set / Revision workflow UI (ADR-012 docs only)
- Supplier catalogue / live pricing / procurement
- Purchase Orders, Job Costing, Reports, AI Assistant, Settings (nav placeholders)

## Migrations

- Alembic head: `f9c1a2b3d4e5` (`plan_documents`)
- Live DB revision: re-verify / upgrade per environment

## Tests

- Full suite: `./venv/bin/python -m pytest -q` → **97 passed**, 68 warnings (M005)
- Phase A: `tests/test_plan_upload.py` — 8 passed

## Known risks

- Hard-coded `SECRET_KEY`
- Proposal estimate FK ON DELETE model/migration mismatch
- Formal acceptance → project creation incomplete
- Future AI take-off risks (mitigated by Proposed ADR-005/006/011)
- Phase A hard-delete of plan files before archival policy exists (ADR-012)

## Current milestone

**Milestone 005 — FG-002 + Phase A PDF upload:** implemented in working tree; **pending Joel-directed commit**.

## Recommended next steps

1. Joel reviews/commits M004 + M005 work when ready.
2. Apply migration `f9c1a2b3d4e5` on each environment.
3. Feature-Gate Phase B before sheet/scale/manual take-off code.

## Related

- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [feature-gates/FG-002-plan-intelligence-phase-a.md](feature-gates/FG-002-plan-intelligence-phase-a.md)
- [adr/ADR-012-plan-document-version-ownership.md](adr/ADR-012-plan-document-version-ownership.md)
- [architecture/plan-intelligence-and-automated-takeoff.md](architecture/plan-intelligence-and-automated-takeoff.md)
- [platform-roadmap.md](platform-roadmap.md)
- [session-handoff.md](session-handoff.md)
- [project-state-report.md](project-state-report.md)
