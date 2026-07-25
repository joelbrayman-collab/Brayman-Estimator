# Platform Roadmap — The Estimator

| Attribute | Value |
|-----------|--------|
| Status | Planning |
| Updated | 2026-07-25 |

Use repository evidence for **Completed**. Everything else is proposed until implemented and documented.

## Completed

(Evidenced on `main`)

**Product (as of `7b8d5ca` and later merges on main):**

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

**Governance (completed at `29d1ba9`):**

- Platform Governance Foundation (Milestone 001)
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
- Governance baseline commit (`29d1ba9` — *Complete Estimator governance baseline and prompt library*; 39 governance/documentation files; no app/migration/test changes)

## Current

- **Product Architecture Review**
- Review implemented workflows against product vision
- Identify risks and gaps
- Select and Feature-Gate **one** next product milestone

*(No specific product feature is approved for implementation until Feature Gate is completed.)*

## Next Recommended Milestone

**Joel to choose one** Feature-Gated item after Product Architecture Review. Candidates (not ordered; **not approved**):

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
2. Prioritize next product milestone after Product Architecture Review.
3. Auth model / multi-user requirements.
4. Whether Change Orders “audit trail” is next Project Controls priority.
5. Production hosting and secret management approach.
6. Push `29d1ba9` to `origin/main` when ready.
