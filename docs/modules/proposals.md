# Module — Proposals

| Attribute | Value |
|-----------|--------|
| Status | **Current** (engine + snapshot + PDF) |
| Updated | 2026-07-25 |
| Code | `app/models/proposal.py`; `app/routes/proposals.py`, `proposal_templates.py`; `app/services/proposals.py`, `proposal_pdf.py` |

## Purpose

Produce client-facing proposals from estimate versions using templates, preserving commercial snapshots independent of later estimate edits.

## Responsibilities

- Proposal templates (branding, default clauses, display flags)
- Proposal records and status lifecycle (`Draft` … `Accepted` …)
- Snapshot sections/lines at creation (`build_proposal_snapshot`)
- Browser preview and PDF generation

## Owned data

- `proposal_templates`
- `proposals`, `proposal_sections`, `proposal_line_items`
- Snapshot commercial fields on `Proposal` (client/project names, markups, totals, etc.)

## Referenced data

- `estimates` / `estimate_versions` (nullable FKs; may clear if version deleted while keeping snapshot — covered by tests)
- Template FK required

## Prohibited responsibilities

- Owning live estimate structure
- Project budget ledger (Projects / future Job Costing)
- Electronic signature providers (Future)

## Current implementation

- Status enum includes `Accepted` (`PROPOSAL_STATUSES`)
- Snapshot independence verified in `tests/test_proposal_snapshots.py` and related proposal tests
- PDF uses snapshot after estimate changes (`tests/test_proposal_pdf.py`)

## Planned capabilities

- Formal acceptance workflow / e-signature — **Future**
- Immutable enforcement hardening for Accepted records — review against Rule 3
- Project creation from acceptance snapshot — Rule 4 / Projects module

## Dependencies

- Estimating (source versions)
- Templates for presentation defaults

## Invariants

- Proposal commercial lines are snapshot data, not live estimate lines
- Accepted proposals must not be silently rewritten (Rule 3) — enforce in services as product hardens

## Open decisions

- Exact Accepted immutability rules (which fields freeze)
- Acceptance → Project creation process owner

## Relevant tests

- `tests/test_proposals.py`
- `tests/test_proposal_snapshots.py`
- `tests/test_proposal_preview.py`
- `tests/test_proposal_pdf.py`

## Relevant ADRs

- None yet (immutability/acceptance ADR recommended before major acceptance workflow work)
