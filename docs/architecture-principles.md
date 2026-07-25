# Architecture Principles — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-07-25 |
| Change control | Changes require an ADR and Joel’s approval |

These rules are durable. Do not violate them for convenience.

---

**Rule 1 — Module ownership must be explicit.**  
Every capability belongs to a named module. Document ownership in `docs/modules/` before expanding scope.

**Rule 2 — One module must not directly assume ownership of another module’s records.**  
Cross-module use must go through documented service, adapter, or repository boundaries (see Rule 11).

**Rule 3 — Accepted proposals are immutable historical snapshots.**  
Once a proposal is Accepted (or otherwise locked by approved policy), its commercial snapshot must not be silently rewritten.

**Rule 4 — Projects created from proposals must reference or copy a defined acceptance snapshot rather than depend on a mutable proposal.**  
Project budgets and baselines must not float with later proposal edits. (*Intended invariant* — confirm implementation status in [architecture.md](architecture.md) / [modules/projects.md](modules/projects.md).)

**Rule 5 — Historical estimates, proposals, budgets, and financial records are versioned or superseded, not silently overwritten.**  
Prefer new versions, supersession statuses, or audited corrections.

**Rule 6 — Financially significant actions must be auditable.**  
Status changes, approvals, and money-affecting edits should leave a recoverable trail. Where audit UI is incomplete, document the gap; do not pretend completeness.

**Rule 7 — Database migrations must be intentional, reviewed, and limited to the approved feature.**  
No casual Alembic generation. No drive-by schema changes in unrelated work.

**Rule 8 — A feature is not complete until tests, documentation, roadmap, and handoff records are updated.**  
See [definition-of-done.md](definition-of-done.md).

**Rule 9 — Cursor implements approved requirements; it does not invent product policy.**  
If requirements conflict or are missing, stop and report.

**Rule 10 — Chat history is not the system of record. Repository documentation is the system of record.**  
Update `docs/` so the next session can recover without chat memory.

**Rule 11 — Cross-module access must use documented service, adapter, or repository boundaries where applicable.**  
Avoid reaching into another module’s private persistence patterns without an approved boundary.

**Rule 12 — Existing functionality must not be changed incidentally while implementing an unrelated feature.**  
Keep diffs scoped. No opportunistic refactors without approval.

---

## Amending these principles

1. Propose change via ADR (`docs/adr/`).  
2. Obtain Joel’s approval.  
3. Update this file, roadmap, and affected module docs.  
4. Record the decision in [chat-workflow-log.md](chat-workflow-log.md).
