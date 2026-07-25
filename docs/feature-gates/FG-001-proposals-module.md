# Feature Gate — Proposals Module (Product Architecture Review)

| Attribute | Value |
|-----------|--------|
| ID | FG-001 |
| Module | Proposals |
| Milestone | Milestone 002 — Product Architecture Review |
| Status | **Draft for Joel approval** (documentation only; no implementation authorized) |
| Date | 2026-07-25 |
| Base commit | `71e2754` (`main`) |
| Related ADRs | [ADR-001](../adr/ADR-001-proposal-snapshot-ownership.md) · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) · [ADR-003](../adr/ADR-003-optional-crm-foreign-keys.md) · [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) |
| Module doc | [modules/proposals.md](../modules/proposals.md) |

## Purpose

Record an accurate Feature Gate for the **existing** Proposals module: what is complete, what is missing, technical debt, and which **single** next implementation milestone should follow — without inventing greenfield tables or authorizing code changes.

---

## Feature Gate answers (governance checklist)

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Establishes a governed baseline of the Proposals module so future work (immutability, acceptance, project creation) is Feature-Gated against real code, not chat memory. |
| 2 | Who is the user? | Joel (product owner); estimators / proposal authors creating client-facing proposals from estimate versions. |
| 3 | Which module owns it? | **Proposals** (`docs/modules/proposals.md`). Estimating owns live estimate structure; Projects owns project records / future budgets. |
| 4 | What data does it own? | `proposal_templates`, `proposals`, `proposal_sections`, `proposal_line_items`, including denormalized snapshot commercial and narrative fields on `Proposal`. |
| 5 | What data does it reference? | `estimates`, `estimate_versions` (nullable FKs); optional `estimate_line_items` via `source_line_item_id` (SET NULL); live `Client`/`Project` only at snapshot time (no FKs today). |
| 6 | What may it change? | **This Feature Gate / Milestone 002:** documentation and ADRs only. **Future implementation milestones:** only what that milestone’s approved Cursor prompt allows. |
| 7 | What must it not change? | Estimate builder tables/behaviour; Discovery Search (N/A to this repo); unrelated modules; schema/migrations unless a later Feature-Gated milestone explicitly approves them. |
| 8 | What are the acceptance criteria? | See Definition of Done below for Milestone 002 docs; for the **recommended next implementation milestone**, see § Recommended next milestone. |
| 9 | What tests are required? | Milestone 002: none beyond proving no app change. Next implementation: see ADR-002 / recommended milestone test plan. Existing suite last verified at governance baseline: **78 passed**, 43 warnings (not re-run for this docs-only task). |
| 10 | What documentation must be updated? | This Feature Gate; ADRs 001–004; `modules/proposals.md`; `milestones.md`; `platform-roadmap.md`; `project-state-report.md`; `session-handoff.md`; `chat-workflow-log.md`; ADR index. |
| 11 | Does it require an ADR? | **Yes** — four Proposed ADRs listed above. |
| 12 | Does it require a database migration? | **No** for Milestone 002. ADR-002/003 may defer or require later migrations only after Joel accepts those ADRs and a separate implementation Feature Gate. |

---

## Current implementation (verified)

Authoritative code paths: `app/models/proposal.py`; `app/services/proposals.py`, `proposal_pdf.py`; `app/routes/proposals.py`, `proposal_templates.py`; templates under `app/templates/proposals/` and `proposal_templates/`.

### Completed capabilities

| Capability | Evidence |
|------------|----------|
| Proposal templates (CRUD, default/active, branding, default clauses, display flags) | Models + `proposal_templates` routes/services; tests in `test_proposals.py` |
| Create proposal from estimate version | `create_proposal` + route under estimate version |
| Header snapshot (client/project/estimate identity, money, narrative, flags) | `build_proposal_snapshot` |
| Section/line snapshot independent of later estimate edits | `snapshot_estimate_version_content`; `test_proposal_snapshots.py` |
| Edit proposal metadata/narrative/display flags | `update_proposal` + edit route |
| Edit snapshot line items + recalculate totals | `update_proposal_line_item` / `recalculate_proposal` |
| Status lifecycle including `Accepted` (enum present) | `PROPOSAL_STATUSES`; status route |
| Browser preview from snapshot | preview route + `test_proposal_preview.py` |
| PDF generation from snapshot | `generate_proposal_pdf` + `test_proposal_pdf.py` |
| Nullable estimate FKs so snapshot can outlive source | Migration `d4e7a1c92f30`; tests clear FKs before delete |

### Missing / incomplete capabilities (vs roadmap & vision)

| Gap | Notes |
|-----|--------|
| **Accepted immutability enforcement** | **Done in Milestone 003** — `ensure_proposal_mutable` |
| **Formal acceptance workflow** | No dedicated accept action, acceptance record, signature, or audit event — status change only; void/supersede deferred |
| **Project / budget creation from accepted proposal** | Roadmap Future / Rule 4; Projects module owns project records |
| **Electronic signature** | Explicitly Future |
| **Rich proposal structural editor** | No add/remove/reorder proposal sections/lines beyond editing existing lines (product decision required) |
| **Re-snapshot from estimate** | Not supported after create (may be correct; needs product confirmation) |
| **User / Company entities** | No User or Company models; issuer branding on template only |
| **Live CRM FKs on proposals** | No `client_id` / `project_id`; CRM join relies on estimate path or snapshot strings |

### Technical debt

| Item | Severity | Recommendation |
|------|----------|----------------|
| Model declares `ondelete="SET NULL"` on `Proposal.estimate_id` / `estimate_version_id`; migrations do not create ON DELETE SET NULL | Medium | ADR hygiene migration later **or** document manual clear as the contract (do not “fix casually”) |
| Waste % baked into proposal `unit_cost` at snapshot; no proposal `waste_percent` column | Low / design | Keep unless audit needs change (ADR-001) |
| Empty `app/repositories/` placeholder unused by Proposals | Low | Do not invent a repository layer without Feature Gate |
| Accepted status without freeze | **High** (governance) | Next implementation milestone (ADR-002) |
| Hard-coded development `SECRET_KEY` | High (platform) | Separate production-config milestone — out of Proposals scope |
| Estimate header status vs version status vs proposal status alignment | Medium | Clarify in acceptance ADR / product rules |

---

## Comparison to platform roadmap

| Roadmap item | Status vs code |
|--------------|----------------|
| Proposal templates | **Done** |
| Proposal from estimate + snapshot independence | **Done** |
| Browser preview | **Done** |
| PDF generation | **Done** |
| Formalize acceptance + immutability review | **Not done** (this Feature Gate + ADR-002/004 prepare it) |
| Project creation from accepted proposal | **Not done** (blocked on acceptance + Projects ownership) |
| E-signature | **Future** |

---

## Recommended implementation sequence

1. **Joel accepts ADRs 001–004** (or amends them).  
2. **Milestone 003 — Accepted Proposal Immutability** (recommended next — see below).  
3. Milestone 004 — Formal Proposal Acceptance Workflow (ADR-004), after immutability.  
4. Milestone 005 — Project creation / budget baseline from accepted snapshot (Projects + Proposals boundary; Rule 4).  
5. Optional later: CRM FK backfill (ADR-003), rich structural editor, production secrets.

---

## Recommended next implementation milestone

### Milestone 003 — Accepted Proposal Immutability

| Field | Content |
|-------|---------|
| Objective | Enforce that proposals in `Accepted` (and optionally other terminal statuses) cannot be silently rewritten; align services/routes/UI with Constitution Article 5 and architecture Rule 3. |
| Module owner | Proposals |
| Depends on | Joel acceptance of **ADR-002** (and confirmation of ADR-001 snapshot ownership) |
| Migration | Prefer **none**; behaviour/service enforcement only unless ADR-002 requires audit columns |
| Must not change | Estimate builder schema/behaviour; unrelated modules; acceptance→project creation (defer to later milestone) |
| Primary ADR | [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) |
| Prompt template | `docs/prompts/cursor-feature-template.md` |

**Why this first:** Highest governance risk in the current Proposals module; builds on existing code; smallest safe product slice; unblocks trustworthy acceptance and later project-from-proposal work.

**Not approved for Cursor implementation until** Joel marks this Feature Gate / Milestone 003 prompt as approved.

---

## Definition of Done — Milestone 002 (this task)

- [x] Feature Gate document created (this file)
- [x] Required ADRs drafted (001–004, Status: Proposed)
- [x] Current Proposal implementation accurately documented
- [x] Missing functionality clearly identified
- [x] Technical debt documented
- [x] Recommended implementation sequence provided
- [ ] Joel approval of ADRs / next milestone (pending)
- [ ] Commit of documentation (explicit Joel request only)

---

## Approval

| Role | Decision | Date |
|------|----------|------|
| Joel | Pending | |
| ChatGPT review | Pending | |
| Implementation authorized? | **No** — docs/ADRs only | 2026-07-25 |
