# ADR-012 — Plan Document Version Ownership

| Field | Value |
|-------|--------|
| Title | ADR-012: Plan Document Version Ownership |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [ADR-007](ADR-007-plan-and-estimate-version-ownership.md) · [plan-intelligence architecture](../architecture/plan-intelligence-and-automated-takeoff.md) · Milestone 005 |

## Context

Phase A introduces PDF upload and storage. Before richer revision workflows exist, ownership and lifecycle rules for drawing sets and revisions must be explicit so Phase A storage remains extensible and later phases do not silently mutate historical plan packages or estimates.

**Milestone 005 implements upload/storage only.** This ADR is documentation; revision UI/workflow is **not** implemented in Phase A.

## Decision

*(Proposed)*

1. **Plan Intelligence** owns drawing sets, revisions, uploaded plan files, and future sheet/take-off records derived from them.
2. A **Drawing Set** is the project-scoped container for related plan files (e.g. “IFC Bid Set”).
3. A **Revision** is an immutable snapshot of a drawing set’s file contents at a point in time (labels such as A, B, or cloud numbers are product-defined later).
4. Exactly one revision may be marked **active** per drawing set for new take-off work; prior revisions are **superseded** (readable, not silently overwritten).
5. Uploading replacement plans creates a **new revision** (or new drawing set), never in-place mutation of a superseded revision’s stored files.
6. **Estimate-to-revision linkage** (when take-off mapping exists): estimate versions may record which plan revision supplied quantities; changing the active revision does **not** rewrite estimate lines (ADR-006/007).
7. **Stale estimate detection** (future): if an estimate version was mapped from revision R1 and the active revision becomes R2, the product may warn “plan revision changed” — it must not auto-update quantities.
8. **Upload ownership:** files are stored under Plan Intelligence control (private storage, project-scoped); Estimating/Proposals do not own plan binaries.
9. **Revision numbering strategy:** human-visible revision labels are assigned at revision creation; internal ids are surrogate keys. Exact label rules are product-configurable later.
10. **Future comparison workflow:** diffing R1 vs R2 sheets/quantities is a later Feature Gate; storage must retain superseded revisions to enable it.
11. **Deletion vs archival:** prefer **archive** (soft-hide) over hard delete for revisions that have take-off or estimate links; hard delete only when no dependent commercial records exist and Joel-approved retention policy allows.
12. **Audit history:** upload, activate, supersede, archive, and download events are append-only.
13. **Version snapshots:** revision file sets are fixed at creation; metadata corrections (e.g. rename label) are audited and must not replace file bytes.

### Phase A implication

Phase A may store **plan documents** as project-scoped files without exposing Drawing Set / Revision UI. Schema and storage layout should remain compatible with introducing Drawing Set + Revision tables later without rewriting estimate ownership rules.

## Alternatives Considered

- Mutable single “current plans” folder per project — Rejected (breaks history and comparison).
- Estimating owns plan files — Rejected (Rule 1 / module ownership).
- Hard-delete on every re-upload — Rejected (destroys audit and future comparison).

## Consequences

Positive: clear lifecycle before code grows. Negative: Phase A UX is simpler than the full model; docs must prevent implementers from treating flat uploads as the final ownership model.

## Module Ownership Impact

Plan Intelligence owns plan documents and future drawing-set/revision records. Projects scopes them. Estimating references revisions later; does not own files.

## Data Ownership Impact

Plan file bytes and revision membership are Plan Intelligence–owned historical records.

## Migration Impact

Phase A: additive `plan_documents` (or equivalent) only. Drawing set / revision tables deferred to a later Feature Gate.

## Testing Impact

Phase A tests cover upload/storage/download/list. Revision workflow tests deferred.

## Documentation Impact

FG-002; plan-intelligence module; architecture Phase A notes; milestones.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Docs only in M005 for this ADR; Phase A upload does not implement revision workflow | |
