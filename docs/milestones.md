# Milestone History — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Authoritative historical record |
| Updated | 2026-07-25 |
| Policy | **Append-only** |

## Purpose

Record completed and in-progress platform milestones so progress is recoverable without chat history.

## Numbering convention

- Format: `Milestone NNN` with zero-padded integers (`001`, `002`, …)
- Title: short human name
- Separate **planned** milestones (roadmap) from **recorded** entries here

## Required fields (each entry)

Milestone · Status · Branch · Base commit · Objective · Deliverables · Validation · Architectural findings · Open decisions · Next milestone · Commit · Date

## Rules

1. Entries are **append-only** (newest first under Completed / Recorded).
2. Completed entries are **not rewritten** except to correct factual errors (note the correction).
3. Distinguish **Planned** (may live primarily on the roadmap) from **Completed / Recorded** here.
4. “Completed pending baseline commit” means deliverables exist in the working tree awaiting Joel-approved commit.

---

## Recorded milestones

### Milestone 003 — Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Milestone | Accepted Proposal Immutability |
| Status | **Completed pending commit** |
| Branch | `main` |
| Base commit | `71e2754` (plus uncommitted M002 docs in tree) |
| Date | 2026-07-25 |
| Objective | Enforce service-layer immutability for `Accepted` proposals across all mutation paths; keep detail/preview/PDF read-only available. |
| Deliverables | `ensure_proposal_mutable` / `is_proposal_immutable` in `app/services/proposals.py`; route/UI read-only controls; `tests/test_proposal_immutability.py`; module/ADR updates. |
| Validation | Full pytest after implementation (record exact results in completion report). No migration. |
| Architectural findings | No section CRUD mutation API existed; line edit + update_proposal + recalculate + status were the mutation surfaces. |
| Open decisions | Void/supersede/revision workflow (ADR-004); whether other terminal statuses should hard-lock. |
| Next milestone | Formal acceptance workflow Feature Gate and/or Plan Intelligence Phase A Feature Gate (Joel sequencing). |
| Commit | Pending |

### Milestone 002 — Product Architecture Review and Next-Milestone Selection

| Field | Content |
|-------|---------|
| Milestone | Product Architecture Review and Next-Milestone Selection |
| Status | **Completed pending documentation commit** |
| Branch | `main` |
| Base commit | `71e2754` |
| Date | 2026-07-25 |
| Objective | Review Proposals module against roadmap; produce Feature Gate FG-001 and ADRs 001–004; recommend next implementation milestone without code changes. Extended same day with strategic Plan Intelligence / Supplier architecture, pillars, Phases A–G, ADR-005–010, and POC recommendation. |
| Deliverables | `docs/feature-gates/FG-001-proposals-module.md`; ADR-001–004; `docs/architecture/plan-intelligence-and-automated-takeoff.md`; `docs/architecture/supplier-catalogue-inventory-pricing.md`; ADR-005–010; roadmap pillars; module stubs for Plan Intelligence and Supplier Catalogue; cross-links. |
| Validation | Documentation-only; no application/migration/test file changes; internal doc links checked after edits. Full pytest not re-run (last verified: 78 passed, 43 warnings). |
| Architectural findings | Proposal Builder foundation already exists. Highest Proposals gap: Accepted without immutability. Strategic differentiator: PDF-first Plan Intelligence → reviewed take-off → estimate → supplier pricing → proposal/PO. No plan upload or supplier catalogue in code today. |
| Open decisions | Joel acceptance of ADRs 001–010; Milestone 003 vs Phase A POC sequencing; POC element confirmation. |
| Next milestone | **Milestone 003 — Accepted Proposal Immutability** (near-term) and/or Feature Gate for **Plan Intelligence Phase A** (strategic) — neither implementation-authorized until Joel approves |
| Commit | Pending |

### Milestone 001 — Platform Governance Foundation

| Field | Content |
|-------|---------|
| Milestone | Platform Governance Foundation |
| Status | **Completed** |
| Branch | `main` |
| Base commit | `7b8d5ca` |
| Date | 2026-07-25 |
| Objective | Establish repository-based governance, architecture documentation, development workflow, module ownership, Cursor rules, handoff process, and definition of done. |
| Deliverables | `docs/` governance tree (vision, architecture, principles, governance, workflow, standards, DoD, roadmap, current-state, session-handoff, chat-workflow-log, AiRIA lessons); `docs/modules/*`; `docs/adr` template; `AGENTS.md`; `.cursor/rules/*`; root `README.md` pointer; Constitution; milestone history; prompt library; project state report. Commit **`29d1ba9`** included **39** governance/documentation files only; **no** application, migration, or test files changed. |
| Validation | **78 tests passed**, 43 warnings; `git diff --check` clean; **171** internal links checked, **0** broken; no application, migration, or test files changed. |
| Architectural findings | Modular Flask application; estimate versioning and locking exist; proposal snapshots exist; disabled navigation placeholders for future modules; `project_controls` package exists; hard-coded development `SECRET_KEY` requires later cleanup; accepted-proposal immutability needs targeted product review. |
| Open decisions | Next product milestone (pending Product Architecture Review); authentication model; proposal acceptance → project creation; whether Project Controls needs a dedicated module document. |
| Next milestone | Milestone 002 — Product Architecture Review and Next-Milestone Selection |
| Commit | `29d1ba9` — *Complete Estimator governance baseline and prompt library* (record commit `71e2754` memorialized milestone) |
| Remote at record time | Subsequently pushed; tag `v0.1-governance-baseline` published |

---

## Milestone entry template

```markdown
### Milestone NNN — <Title>

| Field | Content |
|-------|---------|
| Milestone | |
| Status | Planned \| In progress \| Completed pending commit \| Completed |
| Branch | |
| Base commit | |
| Date | |
| Objective | |
| Deliverables | |
| Validation | |
| Architectural findings | |
| Open decisions | |
| Next milestone | |
| Commit | |
```

## Related

- [platform-roadmap.md](platform-roadmap.md) — forward-looking plan
- [project-state-report.md](project-state-report.md) — milestone-level state snapshot
- [session-handoff.md](session-handoff.md) — immediate session continuation
