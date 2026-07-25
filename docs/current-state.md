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
| Branch | `milestone-005-plan-intelligence-phase-a` |
| HEAD | `098647c` — Phase A PDF upload/storage |
| Pre-governance base | `7b8d5ca` |
| Remote | Confirm with `git status -sb` (branch may be unpushed) |
| Working tree | May include uncommitted Milestone 006 documentation |
| App | Flask factory `app.create_app` |
| DB default | SQLite `brayman_estimator.db` under instance |
| Governance | Active — FG-002 Phase A; FG-003 Document Intelligence architecture PASS |

## Implemented capabilities (evidenced)

- Clients, Projects, Cost Items, Assemblies
- Estimates with versions, sections, line items; locking for certain statuses
- Proposal templates; snapshot proposals; preview; PDF
- Accepted proposal immutability
- Change Orders (Project Controls)
- **Plan Intelligence Phase A** — project-scoped PDF upload, private storage, list/detail/download/delete, searchable flag
- Dashboard / branding / navigation

## Not implemented (strategic)

- Document Intelligence code (packages, sheets, search) — **architecture only (M006)**
- Plan Intelligence take-off / AI / OCR / CAD
- Supplier catalogue / live pricing / procurement
- Purchase Orders, Job Costing, Reports, AI Assistant, Settings (nav placeholders)

## Migrations

- Alembic head: `f9c1a2b3d4e5` (`plan_documents`)
- Live DB revision: re-verify / upgrade per environment

## Tests

- Full suite at M005: **97 passed**, 68 warnings
- M006: docs only — suite not required to re-run for this milestone

## Known risks

- Hard-coded `SECRET_KEY`
- Proposal estimate FK ON DELETE model/migration mismatch
- Phase A hard-delete vs future archival (ADR-012) — debt for M007
- Auth / multi-user still open
- Future AI take-off risks (ADR-005/006/011 Proposed)

## Current milestone

**Milestone 006 — Document Intelligence architecture:** FG-003 **PASS**; docs complete; **no code**; pending Joel-directed commit.

## Recommended next steps

1. Joel reviews FG-003, ADR-013, ADR-014, M006 readiness report.
2. Commit M006 docs when directed.
3. Feature-Gate **M007** (Drawing Package & Revision) before any Document Intelligence code.

## Related

- [feature-gates/FG-003-document-intelligence-readiness.md](feature-gates/FG-003-document-intelligence-readiness.md)
- [architecture/document-intelligence.md](architecture/document-intelligence.md)
- [architecture/M006-document-intelligence-readiness-report.md](architecture/M006-document-intelligence-readiness-report.md)
- [modules/plan-intelligence.md](modules/plan-intelligence.md)
- [platform-roadmap.md](platform-roadmap.md)
- [session-handoff.md](session-handoff.md)
- [project-state-report.md](project-state-report.md)
