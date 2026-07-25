# Milestone 004 — Plan Intelligence Architecture Readiness Report

| Attribute | Value |
|-----------|--------|
| Status | Documentation complete |
| Date | 2026-07-25 |
| Milestone | Milestone 004 — Plan Intelligence & Automated Take-Off Architecture |
| HEAD at start | `c59ec01` |

## Files inspected

- `AGENTS.md`, Constitution, architecture principles, architecture.md
- `platform-roadmap.md`, `milestones.md`, `platform-governance.md`, `development-workflow.md`
- `modules/*`, `adr/*`, `current-state.md`, `project-state-report.md`
- Existing stub architecture: `architecture/plan-intelligence-and-automated-takeoff.md`
- `.cursor/rules/*`
- Confirmed: no plan-intelligence application code in `app/`

## Files created

- `docs/architecture/M004-plan-intelligence-readiness-report.md` (this file)
- `docs/adr/ADR-011-ai-confidence-threshold-policy.md`

## Files updated

- `docs/modules/plan-intelligence.md` — full module charter
- `docs/architecture/plan-intelligence-and-automated-takeoff.md` — pipeline, model, review, traceability, mapping, POC
- `docs/adr/ADR-005-ai-takeoff-traceability.md` — strengthened as source-traceability ADR
- `docs/adr/ADR-006-human-approval-before-estimate-insertion.md` — aligned to M004
- `docs/adr/README.md`
- `docs/architecture/README.md`
- `docs/platform-roadmap.md`
- `docs/milestones.md`
- `docs/README.md`
- `docs/current-state.md`
- `docs/project-state-report.md`
- `docs/session-handoff.md`
- `docs/chat-workflow-log.md`

## Major architectural decisions (Proposed)

| Decision | ADR / doc |
|----------|-----------|
| PDF-first ingestion; CAD later | ADR-009 |
| Human approval required before estimate insert | ADR-006 |
| Full source citation bundles | ADR-005 |
| Confidence thresholds gate review intensity, not auto-insert | ADR-011 |
| Exclusive ownership: Plan Intelligence vs Estimating | ADR-007 |
| Plan Intelligence feeds estimate builder; does not replace it | Architecture §6 |
| Proposals remain downstream of Estimating | Architecture §1 |

### ADR numbering note (Task 7)

Task 7 requested ADR-005…008 with specific titles. Those numbers were **already assigned**:

| Requested title | Canonical ADR used |
|-----------------|-------------------|
| PDF-first vs CAD-first | **ADR-009** (existing) |
| Human approval before estimate insertion | **ADR-006** (updated) |
| Source traceability | **ADR-005** (updated) |
| AI confidence threshold | **ADR-011** (new; ADR-008 remains Supplier Price Snapshotting) |

## Risks

- AI false positives/negatives
- Incorrect scale
- Scope creep across trades/formats
- Premature CAD/BIM investment
- Auth identity gaps for “reviewer” until auth model decided
- Storage/retention of plan PDFs

## Open questions (Joel)

1. Confirm interior door count as POC element (or substitute one assembly).
2. Set numeric confidence thresholds before Phase C.
3. Auth model for reviewer attribution.
4. Object storage / retention policy.
5. Sequencing: Plan Intelligence Phase A Feature Gate vs other product work.
6. Build-vs-buy for PDF viewer / measurement (ADR-010).

## Future milestones (suggested)

1. Feature Gate + implement **Phase A** (PDF upload/storage/register)
2. Phase B — sheet index, scale confirm, manual measure
3. Phase C — narrow AI extraction + ADR-011 thresholds
4. Phase D — mapping into estimate assemblies
5. Parallel later: Supplier Phase E (separate program)

## Recommended implementation order

1. Accept/amend ADR-005, 006, 007, 009, 011
2. Feature Gate Phase A only
3. POC path to one approved door count → one estimate line
4. Expand vocabulary only after POC success metrics met

## Technical debt introduced

**None in application code** (docs only). Documentation debt: keep ADR index and roadmap in sync when Phase A Feature Gate is written.

## Assumptions

- No plan-intelligence code exists today (verified by prior inspections / roadmap).
- Estimating and Proposals remain the commercial engines downstream.
- Milestone 003 Accepted immutability remains in force for proposals.
- Technology choices (OCR vendor, model provider) deferred to ADR-010 / Feature Gates.

## Definition of Done (Milestone 004)

| Criterion | Met |
|-----------|-----|
| No application code changed | ✓ |
| No migrations created | ✓ |
| No tests modified | ✓ |
| No dependencies added | ✓ |
| Complete Plan Intelligence architecture document | ✓ |
| Processing pipeline documented | ✓ |
| Human review documented | ✓ |
| Source traceability documented | ✓ |
| Estimate mapping documented | ✓ |
| Four ADR topics covered (via 005/006/009/011) | ✓ |
| Docs updated consistently | ✓ |
| Narrow POC recommended | ✓ |
| No commits created | ✓ (at report authorship; Joel commits separately) |
