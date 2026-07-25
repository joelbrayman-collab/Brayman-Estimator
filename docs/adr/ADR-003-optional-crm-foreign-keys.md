# ADR-003 — Optional CRM Foreign Keys on Proposals

| Field | Value |
|-------|--------|
| Title | ADR-003: Optional CRM Foreign Keys on Proposals |
| Status | **Proposed** |
| Date | 2026-07-25 |
| Related | [FG-001](../feature-gates/FG-001-proposals-module.md) · [ADR-001](ADR-001-proposal-snapshot-ownership.md) · [modules/crm.md](../modules/crm.md) |

## Context

Proposals store denormalized `client_*` and `project_*` snapshot strings. There are no `client_id` / `project_id` columns. CRM joins today depend on optional `estimate_id` → project → client, which can be nulled when sources are deleted. Product may want optional live FKs for navigation/reporting without replacing snapshot authority.

## Decision

*(Proposed for Joel approval)*

1. **Near term (Milestones 003–004):** Do **not** add CRM FKs. Snapshot strings remain the commercial record (ADR-001).
2. **If later approved:** Add **nullable** `client_id` and/or `project_id` on `proposals` for convenience joins only.
3. Snapshot columns remain **authoritative** for issued/accepted commercial content; FKs must not silently overwrite snapshot strings on CRM edits.
4. Backfill FKs from `estimate → project → client` where available; leave null when estimate FKs are cleared.
5. CRM module continues to own `clients`; Projects owns `projects`; Proposals references only.

## Alternatives Considered

- **Replace snapshot strings with live CRM fields** — Rejected: violates historical preservation.
- **Add FKs immediately in Milestone 003** — Rejected: expands scope; not required for immutability.
- **Never add FKs** — Acceptable long-term if reporting always goes through estimates; may hinder orphaned-proposal CRM navigation.

## Consequences

**Positive:** Avoids premature migration; keeps Milestone 003 focused.  
**Negative:** Harder to list proposals by client when estimate FKs are null.

## Module Ownership Impact

No ownership transfer. Optional references only.

## Data Ownership Impact

Snapshot strings remain owned commercial data; FKs are references.

## Migration Impact

**Deferred.** When approved: additive nullable FKs only; no drops; no estimate-table changes.

## Testing Impact

If implemented later: backfill cases; null FK with intact snapshot; CRM rename does not mutate accepted snapshot strings.

## Documentation Impact

FG-001, modules/proposals.md, modules/crm.md when implemented.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | |
| ChatGPT review | | |
| Cursor implementation note | Do not implement in Milestone 003 unless Joel explicitly expands scope | |
