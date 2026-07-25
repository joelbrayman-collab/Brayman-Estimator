# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-07-25 |

Use repository evidence for **Completed**. Everything else is proposed until implemented and documented.

## Completed

(Evidenced on `main` as of `7b8d5ca`)

- Clients and Projects foundation
- Cost Items library
- Assemblies
- Estimates with versioning, sections, and line items
- Proposal templates
- Proposal creation from estimate versions with snapshot independence
- Proposal browser preview
- Proposal PDF generation (branding/logo support)
- Change Orders (Project Controls module)
- App shell branding and navigation structure

## Current Governance Sprint

*(Remains Current until the governance baseline is committed — do not move to Completed prematurely.)*

- Platform governance documentation foundation
- Architecture principles Rules 1–12
- Module ownership docs (CRM, Estimating, Proposals, Projects)
- ADR template
- AGENTS.md + Cursor rules
- Session handoff + chat workflow log
- Definition of done / Feature Gate
- Platform Constitution
- Milestone History
- Prompt Library
- Project State Report
- Governance baseline commit

## Next Recommended Milestone

**Joel to choose one** Feature-Gated item after governance approval. Candidates (not ordered):

- Formalize proposal acceptance workflow + immutability enforcement review
- Project creation from accepted proposal snapshot (Rule 4)
- Change Order audit trail
- Production configuration (secrets, deployment runbook)

## Near-Term

- Strengthen module service boundaries documentation vs code
- Auth / multi-user model clarification (Flask-Login present; depth to verify)
- Migration verification runbook (`flask db current` / upgrade)

## Future

(Provisional — not implemented unless noted)

- Proposal acceptance (productized workflow beyond status enum)
- Electronic signature
- Accepted proposal snapshots as project budget baselines
- Project creation from acceptance
- Project budgets
- Scheduling
- Daily reports
- Timesheets
- Purchasing / Purchase Orders (nav placeholder only today)
- QuickBooks integration
- Job costing (nav placeholder only today)
- Invoicing
- Historical estimating intelligence
- Reports module
- AI Assistant
- Settings

## Deferred

- Full ERP replacement
- Speculative AI price generation without human approval
- Silent overwrite of historical commercial records

## Decisions Required (Joel)

1. Confirm provisional platform sequence in [platform-vision.md](platform-vision.md).
2. Prioritize next product milestone after governance commit.
3. Auth model / multi-user requirements.
4. Whether Change Orders “audit trail” is next Project Controls priority.
5. Production hosting and secret management approach.
