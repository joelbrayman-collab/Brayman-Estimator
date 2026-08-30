# Feature Gate FG-017: Organization Brand Profile V1 — Identity, Logo Custody, and Proposal Brand Snapshot

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-017` |
| Feature Name | Organization Brand Profile V1 — Identity, Logo Custody, and Proposal Brand Snapshot |
| Target Milestone | **None.** FG-017 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Organization subsystem** owns Brand Profile and logo custody ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md); proposed [ADR-040](../adr/ADR-040-organization-brand-profile.md)). **Proposals** is the first consumer and owns the proposal issued-document brand snapshot ([modules/proposals.md](../modules/proposals.md)). |
| Date | 2026-08-30 |
| Status | **DRAFT FOR JOEL REVIEW / NOT APPROVED.** Does **not** authorize implementation, schema, migration, or product code. |
| Architecture | [organization-brand-profile.md](../architecture/organization-brand-profile.md) · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [project-document-package.md](../architecture/project-document-package.md) · [modules/proposals.md](../modules/proposals.md) |
| Related ADRs | [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Proposed / for Joel review** (must be **Accepted** before implementation) · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-001](../adr/ADR-001-proposal-snapshot-ownership.md) **Proposed** (do **not** accept as a side effect) · [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed** (do **not** accept) · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-016 **CLOSED / OPERATIONAL FOR UAT**. Live current = head `f8a9b0c1d2e3`. Architecture reconnaissance accepted 2026-08-30. **ADR-040 must be Accepted and this gate Approved before any implementation prompt.** |
| Approved baseline | **None.** This draft is not an implementation baseline. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **DRAFT FOR JOEL REVIEW / NOT APPROVED** |
| ADR-040 | **Proposed / for Joel review** — **not Accepted** |
| Implementation | **NOT AUTHORIZED** — not started |
| Schema / Alembic | **NOT AUTHORIZED** — no revision in this drafting pass. A later approved implementation would require **one** bounded additive revision. |
| Logo storage | **NOT AUTHORIZED** |
| Proposal renderer | **NOT AUTHORIZED** to change |
| Change Order / Permit / Contract / QuickBooks | **NOT IN THIS GATE** |

This gate, if later Approved, would establish **organization-owned contractor branding** and stop Issued/Accepted Proposal documents from floating with later template/logo changes. It is **not** a document-family rewrite, not Permit Intelligence, and not an app-shell redesign.

Drafting this file does **not** approve it. Committing this file does **not** approve it.

---

## Purpose

Create one governed Organization Brand Profile per contractor organization and use it as the single source for contractor identity on generated organization/customer documents, starting with Proposal.

```text
ORGANIZATION
→ ORGANIZATION BRAND PROFILE (current + history)
→ PROPOSAL RENDER (Draft/Ready: live current)
→ ISSUED / ACCEPTED PROPOSAL BRAND SNAPSHOT
→ IMMUTABLE DOCUMENT IDENTITY
```

Office success (only after later approval + implementation): an organization can set contractor name/address/contact/logo once; new Proposal drafts use that profile; Issued/Accepted Proposal preview/PDF keep the branding they were issued with even if the organization later changes its logo or address.

Success is **BRAND PROFILE V1 FOR PROPOSAL**, not branded Change Orders, not branded Permit Reports, and not CalibAi chrome redesign.

---

## Feature Gate answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What problem does this solve? | Contractor identity is duplicated (`Organization` vs `ProposalTemplate`), partly hardcoded (static Brayman logo), and mutable at PDF time for Accepted proposals. There is no org-owned logo store and no issued-document brand snapshot ([ADR-040](../adr/ADR-040-organization-brand-profile.md)). |
| 2 | Who is the user? | Office estimator / Joel on the **current unauthenticated office app**. Not field. Not the customer portal. |
| 3 | Which module owns it? | **Organization subsystem** owns Brand Profile + logo custody. **Proposals** consumes it and owns the proposal brand snapshot. Later consumers are named below; they are **not** implemented here. |
| 4 | What data does it own? | Organization-scoped Brand Profile (versioned identity/contact/colours + logo custody metadata and bytes). Proposal issued-document brand snapshot (Proposals-owned). Not `ProposalTemplate` clauses. Not Permit analysis. Not Change Order items. |
| 5 | What data does it reference? | `organizations` (tenant). `proposals` / `proposal_templates` (consume / stop using live company+logo for Issued/Accepted render). Logo bytes in private instance storage. |
| 6 | What may a later implementation change? | Organization Brand Profile models/services/office settings UX; logo upload/custody; Proposal preview/PDF to read Brand Profile (drafts) and snapshots (Issued/Accepted); one additive migration; dedicated tests; governed docs. **Only after this gate is Approved and an implementation prompt is issued.** |
| 7 | What must it not change? | CalibAi app-shell chrome; Permit analysis / FG-016 HTML/PDF remaining CalibAi-neutral; Change Order PDF/email/document family; Estimating lines/pricing; Internal Detailed Cost Breakdown branding; Plan Intelligence; labour/pricing engines; Material Catalogue; historical evidence; BUILD/MONITOR/LEARN; auth; QuickBooks; contracts; `branding_config` JSON; legal identifier invention; existing Issued/Accepted **commercial** snapshot fields except adding brand snapshot. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. They apply only to a later approved implementation. |
| 9 | Tests required? | See **Proposed tests**. None in this drafting pass. |
| 10 | Documentation? | This gate; ADR-040; Brand Profile pin; proposals module; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. Implementation docs only after approval. |
| 11 | ADR required? | **Yes — ADR-040.** Must be **Accepted** before implementation. This drafting pass leaves it **Proposed**. If implementation exposes an uncovered conflict: **STOP** — do not invent another ADR inside the implementation prompt. |
| 12 | Migration? | **YES — later, one bounded additive revision** in a separately authorized implementation prompt only. No destructive rewrite. Do **not** create the migration in this governance pass. Do **not** run `flask db upgrade` for this capability now. |

---

## Owner

| Concern | Owner |
|---------|--------|
| Brand Profile record, versioning, activation/supersession | **Organization subsystem** ([ADR-040](../adr/ADR-040-organization-brand-profile.md)) |
| Logo bytes and custody metadata | **Organization subsystem** (custody analogous to [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md); not Git) |
| Proposal Draft/Ready render from current Brand Profile | **Proposals** |
| Proposal Issued/Accepted brand snapshot + frozen render | **Proposals** |
| `ProposalTemplate` clauses / layout flags | **Proposals** (identity/logo/colours migrate off the template for rendering) |
| Change Order document branding | Future Change Order document-family gate — **not this gate** |
| Permit analysis snapshots | Projects / Permit Intelligence — **unchanged** ([ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md)) |
| Later customer-facing Permit PDF branding | Future permit-rendering gate consuming this **one** Brand Profile — **not this gate** |
| App-shell logo / favicon / titles | Platform chrome — **out of this gate** |
| Internal Detailed Cost Breakdown | Estimating ([FG-012](FG-012-estimate-output-consistency.md)) — **not a consumer in this gate** |

Do **not** create a second branding mechanism inside Permit Intelligence, Change Orders, contracts, or QuickBooks.

---

## Proposed first-gate scope

Keep this gate deliberately small. If later Approved, implementation may include **only**:

1. **Organization-scoped Brand Profile** — versioned contractor identity for document rendering (legal name, customer-facing name, address, phone, email, website; optional document colours currently on `ProposalTemplate`).
2. **Governed logo custody** — org-owned, app-managed private storage, validated files, controlled naming, replace via explicit action, prior bytes retained for snapshots. No remote URL-following.
3. **Tenant isolation** — Brand Profile, logo bytes, and snapshots never leak across organizations.
4. **Immutable issued-document branding snapshot architecture** — freeze identity+logo+colours on first transition to Proposal `Issued` or `Accepted`; re-render from snapshot thereafter.
5. **Proposal as first active consumer** — Draft/Ready preview/PDF use **current** Brand Profile, not live `ProposalTemplate` company/logo fields and not a floating static Brayman default.
6. **Stop historical float** — Issued/Accepted proposals no longer depend on live mutable company identity/logo. Existing Issued/Accepted rows receive a **one-time** snapshot at implementation so they stop floating.
7. **ProposalTemplate** — keep clauses/layout; stop using template company/logo/colour columns for Proposal rendering. Do not drop those columns in this gate (additive only).
8. **ORG-001 seed** — create a CURRENT Brand Profile from existing Organization identity. Logo seed may copy the current static Brayman asset into org custody as a transitional default; Git static is not the long-term SoR.
9. **Office settings UX** sufficient to view/edit/activate Brand Profile and upload a logo on the unauthenticated office app. Exact route is an implementation detail; do not redesign the whole settings product.
10. **Tests and documentation** as below.
11. **One additive Alembic revision** only if the **implementation** prompt authorizes it.

Exact table/column names are an implementation detail **after** approval. Do not design a second branding JSON blob.

---

## Future consumers (accounted for; not implemented)

Architecture must not block, and must not independently brand, these later surfaces:

| Consumer | This gate |
|----------|-----------|
| Change Orders (existing record + future document family) | Name the future consume+snapshot rule only. **Do not** change CO PDF, email, or schema. |
| Permit & Approvals Report | Analysis unchanged; current HTML/PDF stay CalibAi-neutral. Later customer-facing PDFs consume **this** Brand Profile. **No** Permit-logo system. |
| Contract | Legal Content Gate owns legal text. Future identity from Brand Profile. **Not implemented.** |
| Warranty | Same as Contract. **Not implemented.** |
| QuickBooks-facing exports | Consume Brand Profile where appropriate later. **Not implemented.** |
| Procurement / project reports | Consume Brand Profile later. **Not implemented.** |
| Internal Detailed Cost Breakdown | Not a first-gate consumer. Joel decision still open. **Not implemented.** |

---

## Non-goals

**DO NOT** include in this gate (draft or later implementation):

- Change Order document-family implementation, CO PDF rewrite, client email, field UX, or a second Change Order entity
- Permit analysis changes, new permit rules, or branded Permit HTML/PDF in this gate
- Phase D estimate mapping
- Supplier integration, Winchester POC, bulk supplier onboarding, ADR-008 acceptance
- QuickBooks implementation
- Ontario Contract / Warranty template implementation
- Auth / SaaS onboarding / public self-service
- BUILD / MONITOR / LEARN implementation
- External AI / runtime web lookup / remote logo fetch
- Word-template upload or arbitrary uncontrolled template redesign
- Per-module logo / header settings
- Implementing `branding_config` JSON because the older intended Organization table mentioned it
- CalibAi app-shell redesign (sidebar, favicon, product titles)
- Logo graphic redesign
- Inventing legal/corporate identifiers (business number, licence, registration)
- Reopening FG-012, FG-015, FG-016 product behaviour except Proposal brand consumption
- Dropping `ProposalTemplate` identity columns in the first implementation
- A new module

---

## Acceptance criteria

**These criteria apply only after Joel Approves this gate, Accepts ADR-040, and authorizes an implementation prompt.** They are **not** claimed complete by this draft.

1. ADR-040 is **Accepted** and this Feature Gate is **Approved** before code changes.
2. Each organization has at most one **CURRENT** Brand Profile; replacement supersedes rather than silently mutates.
3. Brand Profile stores the governed identity/contact fields required for Proposal document rendering, plus logo identity. No invented legal identifiers.
4. Logo upload is org-scoped, privately stored, validated, not in Git, not resolved via remote URL.
5. Organization A cannot read or render Organization B’s Brand Profile or logo.
6. Draft/Ready Proposal preview and PDF render contractor identity/logo from the **current** Brand Profile, not from live `ProposalTemplate` company/logo fields and not from a floating static default once a current profile exists.
7. On first transition to Issued or Accepted, the proposal stores an immutable brand snapshot; later Brand Profile or logo changes do not alter that proposal’s preview/PDF identity.
8. Issued → Accepted does not refresh branding from the live profile.
9. Existing Issued/Accepted proposals present at implementation receive a one-time snapshot and then no longer float.
10. `ProposalTemplate` remains usable for clauses/layout; identity/logo/colours are not the rendering source.
11. Change Order PDF behaviour is **unchanged**.
12. Permit HTML/PDF remain **neutral CalibAi**; analysis snapshots unchanged.
13. App-shell sidebar/favicon/titles **unchanged**.
14. One additive migration only; Alembic remains one graph head; no `flask db upgrade` in the governance/draft pass.
15. Dedicated tests plus full suite pass before implementation close.
16. Governed docs distinguish Current vs Intended; do not claim other document families were branded.

---

## Proposed tests

**None in this drafting pass.** A later implementation prompt must add dedicated tests that prove at least:

- Brand Profile create / activate / supersede (no in-place CURRENT mutation)
- Logo upload validation (type/size/path); rejection of remote URLs and traversal
- Bytes not committed to Git; org-prefixed private storage
- Cross-org isolation (profile, logo, snapshot)
- Draft/Ready Proposal uses current Brand Profile
- Issued snapshot freeze; subsequent profile/logo change does not change Issued/Accepted render
- Accepted commercial immutability ([ADR-002](../adr/ADR-002-accepted-proposal-immutability.md)) still holds
- Existing Issued/Accepted rows no longer float after one-time snapshot
- Change Order PDF still uses its current (pre-family) renderer — **regression, not a rewrite**
- Permit HTML/PDF remain CalibAi-neutral — **regression**
- App-shell chrome unchanged — **regression**
- Full suite `./venv/bin/python -m pytest -q` before close

Do not claim these tests exist until they are written and run.

---

## Schema / migration (later implementation only)

**This drafting pass: no migration, no models, no `flask db upgrade`.**

If later Approved, expect **one** additive revision covering approximately:

- organization-owned Brand Profile (versioned) and/or logo custody metadata
- private logo object identity (hash/key), not Git paths as SoR
- Proposal issued-document brand snapshot (structured fields + logo identity)

Do not drop `ProposalTemplate` columns. Do not implement `branding_config` JSON. Do not add Brand Profile columns onto Permit analysis tables. Exact names are **not** approved by this draft.

---

## Documentation (this drafting pass)

Record that ADR-040 is **Proposed** and FG-017 is **DRAFT / NOT APPROVED**. Do not describe Brand Profile as implemented or authorized for product work.

---

## Unresolved Joel decisions (do not invent)

1. Accept ADR-040 and Approve FG-017, or request changes.
2. Whether Internal Detailed Cost Breakdown should later consume Brand Profile (out of this gate either way until decided).
3. Whether Draft-before-CURRENT is required or CURRENT-on-save is enough.
4. Exact office navigation for Brand Profile settings.
5. Whether Issued-but-not-Accepted is the first freeze point (this draft: **yes**, first of Issued or Accepted).
6. Legal/corporate identifiers remain **out** unless Joel later authorizes them.

---

## Explicit stop conditions for a later implementation prompt

Stop and report if: ADR-040 is still Proposed; this gate is still not Approved; a second Alembic head appears; Permit/CO/app-shell work is requested inside the branding prompt; legal identifiers are invented; `branding_config` JSON is about to be added; remote URL logos are proposed.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | | **Pending** — **NOT APPROVED** |
| ChatGPT review | | **Pending** |
| Cursor implementation note | Docs-only draft. **No product implementation.** | 2026-08-30 |
