# Feature Gate FG-017: Organization Brand Profile V1 — Identity, Logo Custody, and Proposal Brand Snapshot

| Attribute | Value |
|-----------|--------|
| Feature Gate ID | `FG-017` |
| Feature Name | Organization Brand Profile V1 — Identity, Logo Custody, and Proposal Brand Snapshot |
| Target Milestone | **None.** FG-017 is the governing identifier. Do not assign a new M0xx number. |
| Module | **Organization subsystem** owns Brand Profile and logo custody ([ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md); [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted**). **Proposals** is the first consumer and owns the proposal issued-document brand snapshot ([modules/proposals.md](../modules/proposals.md)). |
| Date | 2026-08-30 |
| Status | **CLOSED / OPERATIONAL FOR UAT.** Live migrate applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. Office UAT **PASSED** on port **5010**. This is office UAT, not broader production validation. |
| Architecture | [organization-brand-profile.md](../architecture/organization-brand-profile.md) · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [project-document-package.md](../architecture/project-document-package.md) · [modules/proposals.md](../modules/proposals.md) |
| Related ADRs | [ADR-040](../adr/ADR-040-organization-brand-profile.md) **Accepted** · [ADR-028](../adr/ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-019](../adr/ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-039](../adr/ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-032](../adr/ADR-032-app-managed-historical-workbook-storage.md) **Accepted** · [ADR-020](../adr/ADR-020-build-module-boundary.md) **Accepted** · [ADR-001](../adr/ADR-001-proposal-snapshot-ownership.md) **Proposed** (do **not** accept as a side effect) · [ADR-004](../adr/ADR-004-proposal-acceptance-workflow.md) **Proposed** (do **not** accept) · [ADR-008](../adr/ADR-008-supplier-price-snapshotting.md) **Proposed** (do **not** accept) · [ADR-010](../adr/ADR-010-build-versus-buy-document-processing.md) **Proposed** (do **not** accept) |
| Prerequisites | FG-016 **CLOSED / OPERATIONAL FOR UAT**. ADR-040 **Accepted**. Implementation reconnaissance recorded below. Live migrate and office UAT authorized 2026-08-30. |
| Approved baseline | Implementation `00ca492e28118d75757e9a9c82384978b5decd92`. Live current = head **`a9b0c1d2e3f4`**. Dedicated tests **22 passed**. Full suite **423 passed** after live migrate / UAT. |

---

## Status

| Layer | State |
|-------|--------|
| Feature Gate (this document) | **CLOSED / OPERATIONAL FOR UAT** |
| ADR-040 | **Accepted** |
| Implementation | **IMPLEMENTED** — live migrate **APPLIED**; office UAT **PASSED** (port **5010**) |
| Schema / Alembic | Live current = graph head **`a9b0c1d2e3f4`**. One head. Applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. |
| Logo storage | **OPERATIONAL** (`instance/brand_logos/ORG-001/` for Brayman; isolation org not seeded) |
| Proposal renderer | Snapshot-or-current Brand Profile |
| Change Order / Permit / Contract / QuickBooks | **NOT IN THIS GATE** |

This gate establishes **organization-owned contractor branding** and stops Issued/Accepted Proposal documents from floating with later template/logo changes. It is **not** a document-family rewrite, not Permit Intelligence, and not an app-shell redesign.

This gate is **CLOSED / OPERATIONAL FOR UAT**. Live current = head `a9b0c1d2e3f4`. Office UAT **PASSED** on port **5010**. Do **not** claim broader production validation than office UAT.

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

Office success (only after a later implementation prompt): an organization can set contractor name/address/contact/logo once via Settings; new Proposal drafts use that profile; Issued/Accepted Proposal preview/PDF keep the branding they were issued with even if the organization later changes its logo or address.

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
| 6 | What may implementation change? | Organization Brand Profile models/services/office Settings UX; logo upload/custody; Proposal preview/PDF to read Brand Profile (unfrozen) and snapshots (frozen); **one** additive migration `a9b0c1d2e3f4` under the **implementation** prompt; dedicated tests; governed docs. **Only after a separate implementation prompt.** |
| 7 | What must it not change? | CalibAi app-shell chrome (sidebar logo/favicon/titles remain as they are, except enabling the existing Settings nav item); Permit analysis / FG-016 HTML/PDF remaining CalibAi-neutral; Change Order PDF/email/document family; Estimating lines/pricing; Internal Detailed Cost Breakdown; Plan Intelligence; labour/pricing engines; Material Catalogue; historical evidence; BUILD/MONITOR/LEARN; auth; QuickBooks; contracts; `branding_config` JSON; legal identifier invention; existing Issued/Accepted **commercial** snapshot fields except adding a brand snapshot. |
| 8 | Acceptance criteria? | See **Acceptance criteria** below. |
| 9 | Tests required? | See **Dedicated tests** and **Regression suite** in the implementation reconnaissance. None written in this pass. |
| 10 | Documentation? | This gate; ADR-040; Brand Profile pin; proposals module; indexes; current-state; session-handoff; project-state-report; roadmap; chat-workflow-log. |
| 11 | ADR required? | **Yes — ADR-040, now Accepted.** If implementation exposes an uncovered conflict: **STOP** — do not invent another ADR inside the implementation prompt. |
| 12 | Migration? | **YES — one bounded additive revision `a9b0c1d2e3f4`** in the implementation prompt only. No destructive rewrite. **Do not create it in this reconnaissance pass.** Do **not** run `flask db upgrade` now. |

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
4. **Immutable issued-document branding snapshot architecture** — freeze at first **Issued**; if Accepted is reached with no Issued snapshot, freeze at Accepted; re-render from snapshot thereafter.
5. **Proposal as first active consumer** — Draft/Ready preview/PDF use **current** Brand Profile, not live `ProposalTemplate` company/logo fields and not a floating static Brayman default.
6. **Stop historical float** — Issued/Accepted proposals no longer depend on live mutable company identity/logo. Existing Issued/Accepted rows receive a **one-time** snapshot at implementation so they stop floating.
7. **ProposalTemplate** — keep clauses/layout; stop using template company/logo/colour columns for Proposal rendering. Do not drop those columns in this gate (additive only).
8. **ORG-001 seed** — create a CURRENT Brand Profile from existing Organization identity. Logo seed may copy the current static Brayman asset into org custody as a transitional default; Git static is not the long-term SoR.
9. **Office Settings UX** — enable the existing sidebar Settings item; Brand Profile form at `/settings/...`. Do not create a new top-level module.
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
| Internal Detailed Cost Breakdown | **OUT OF SCOPE for FG-017.** No decision is made here about later internal-document branding. |

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

Apply only after a separate **implementation** prompt. Not claimed complete by this reconnaissance.

1. ADR-040 is **Accepted** (done) and this Feature Gate is **Approved** (done) before product code.
2. Each organization has at most one **CURRENT** Brand Profile; save/replace creates a new version (CURRENT-on-save; no Draft state).
3. Brand Profile stores governed identity/contact fields plus logo identity. No invented legal identifiers.
4. Logo upload is org-scoped, privately stored, validated, not in Git, not resolved via remote URL.
5. Organization A cannot read or render Organization B’s Brand Profile or logo.
6. Unfrozen Proposal preview/PDF (no snapshot yet: typically Draft/Ready) render from the **current** Brand Profile, not from live `ProposalTemplate` company/logo fields and not from a floating static Brayman default once a current profile exists.
7. Freeze at first **Issued**. If Accepted is reached with no Issued snapshot, freeze at **Accepted**. Later Brand Profile or logo changes do not alter that proposal’s preview/PDF identity.
8. Issued → Accepted preserves the identical snapshot.
9. Existing Issued/Accepted proposals present at implementation receive a one-time snapshot and then no longer float; commercial fields/totals/acceptance are untouched.
10. `ProposalTemplate` remains usable for clauses/layout; identity/logo/colours are not the FG-017 rendering source; columns are not dropped.
11. Change Order PDF behaviour is **unchanged**.
12. Permit HTML/PDF remain **neutral CalibAi**; analysis snapshots unchanged.
13. App-shell sidebar logo/favicon/titles **unchanged** except enabling the existing Settings nav item to Brand Profile.
14. One additive migration `a9b0c1d2e3f4`; Alembic remains one graph head.
15. Dedicated tests plus full suite pass before implementation close.
16. Governed docs distinguish Current vs Intended; do not claim other document families were branded.

---

## Approved implementation reconnaissance (2026-08-30)

**Status:** design recorded 2026-08-30; **implemented** in the FG-017 product pass; **live-migrated and office-UAT verified** 2026-08-30.

### A. Existing Organization model

[`app/models/organization.py`](../../app/models/organization.py): `id`, `legal_name`, `display_name`, `primary_address`, `default_region`, `currency`, `tax_jurisdiction`, `is_active`, timestamps. No phone, email, website, logo, or branding JSON.

[`app/services/organizations.py`](../../app/services/organizations.py): `DEFAULT_ORGANIZATION_ID = "ORG-001"`; `get_current_organization_id()`; `ensure_default_organization()`.

Live DB (read-only, 2026-08-30): `ORG-001` Brayman Construction Inc. / Brayman Construction / 411 St. John Street, Merrickville, Ontario K0G 1N0; `ORG-FG014-UAT` isolation org. Do **not** copy the Brayman static logo into the isolation org.

### B. Existing Proposal / ProposalTemplate

[`app/models/proposal.py`](../../app/models/proposal.py)

`PROPOSAL_STATUSES`: Draft, Ready, Issued, Accepted, Rejected, Expired, Cancelled, Superseded.

`ProposalTemplate` (org-scoped): `company_name`, `company_address`, `company_phone`, `company_email`, `company_website`, `logo_path`, `primary_color`, `accent_color`, plus clause/layout flags. **Keep all columns.**

`Proposal` has commercial/client/project snapshots and `issued_at`. **No** brand snapshot today. `issued_at` is set only when status is Issued at create or on transition **to** Issued ([`app/services/proposals.py`](../../app/services/proposals.py) `create_proposal` / `update_proposal`). Create-as-Accepted does **not** set `issued_at`.

[ADR-002](../adr/ADR-002-accepted-proposal-immutability.md) locks **Accepted** only (`ensure_proposal_mutable`). **Issued remains commercially mutable.** Brand freeze is a **separate** immutability layer.

### C. Current Proposal preview / PDF paths

- Preview: [`app/routes/proposals.py`](../../app/routes/proposals.py) `preview_proposal` → [`app/templates/proposals/preview.html`](../../app/templates/proposals/preview.html) using `template.company_*`, colours, and `resolve_preview_logo_url(template.logo_path)`.
- PDF: [`app/services/proposal_pdf.py`](../../app/services/proposal_pdf.py) `generate_proposal_pdf` reads live template company lines and `resolve_logo_filesystem_path(template.logo_path)`.

**Governed FG-017 path must stop using those live template fields.**

### D. Status transition points (freeze hooks)

| Event | Code | Freeze |
|-------|------|--------|
| Create with status Issued | `create_proposal` | Freeze in the same transaction after insert |
| Create with status Accepted | `create_proposal` (`issued_at` stays null) | Freeze at Accepted |
| `update_proposal` / `update_proposal_status` first transition **to Issued** | `update_proposal` status branch (~line 631) | Freeze |
| Transition **to Accepted** with no snapshot | same | Freeze at Accepted |
| Issued → Accepted with snapshot present | same | **Do not** rewrite snapshot |
| POST `/proposals/<id>/status` | `update_status` | via `update_proposal_status` |

Do not freeze Draft/Ready. Do not freeze commercial `ensure_proposal_mutable` (Accepted-only).

**Sticky snapshot rule:** if a snapshot row exists, preview/PDF **always** use it (even if status later returns to Draft — existing code allows Issued → Draft). Do **not** delete the snapshot. Do **not** invent an Issued commercial lock.

### E. Current logo resolution

[`app/services/proposal_pdf.py`](../../app/services/proposal_pdf.py):

- `DEFAULT_LOGO_STATIC_PATH = "branding/brayman-construction-logo.png"`
- `MAX_LOGO_BYTES = 5 * 1024 * 1024`
- `SUPPORTED_LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif"}`
- PDF: never follows remote URLs; static-folder relative paths only
- Preview `resolve_preview_logo_url`: **does** return `http://` / `https://` and absolute `/` paths — **must not** be used for Brand Profile

Change Order PDF ([`app/project_controls/pdf.py`](../../app/project_controls/pdf.py)) hardcodes the same static asset — **do not change**.

Template form `logo_path` is a free-text field, not an upload.

### F. Existing private storage to reuse

Reuse the **ADR-032 / FG-013** pattern in [`app/services/historical_ingestion/storage.py`](../../app/services/historical_ingestion/storage.py): org-segment regex, SHA-256 filename, no overwrite of mismatched bytes, `instance/` (already gitignored), resolve with traversal checks.

Do **not** store logos under `instance/historical_uploads/` or `instance/plan_uploads/` (wrong custody). New root: `instance/brand_logos/<organization_id>/<sha256><ext>`.

Plan PDF download ([`app/plan_intelligence/routes.py`](../../app/plan_intelligence/routes.py) `send_file`) is the pattern for a tenant-scoped logo response.

No Pillow in `requirements.txt`. Do **not** add it. Validate suffix + size + magic bytes.

### G. Proposed Brand Profile schema

Table `organization_brand_profiles`:

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | |
| `organization_id` | String(50) NOT NULL FK `organizations.id` | indexed |
| `version_number` | Integer NOT NULL | per-org, starting at 1 |
| `status` | String(20) NOT NULL | `CURRENT` \| `SUPERSEDED` only — **no DRAFT** |
| `legal_name` | String(255) NOT NULL | |
| `customer_facing_name` | String(255) NOT NULL | |
| `address` | String(255) | nullable |
| `phone` | String(50) | nullable |
| `email` | String(150) | nullable |
| `website` | String(180) | nullable |
| `primary_color` | String(20) | nullable; renderer default `#1f3a5f` if null |
| `accent_color` | String(20) | nullable; renderer default `#c79a2b` if null |
| `logo_sha256` | String(64) | nullable |
| `logo_extension` | String(8) | e.g. `.png` |
| `logo_byte_size` | Integer | |
| `logo_original_filename` | String(255) | untrusted metadata |
| `superseded_by_id` | Integer FK self | nullable |
| `created_at` | DateTime NOT NULL | |
| `created_by` | String(150) NOT NULL | actor-string (`HISTORICAL_UPLOAD_ACTOR` convention) |

Constraints:

- UNIQUE (`organization_id`, `version_number`)
- CHECK `status IN ('CURRENT', 'SUPERSEDED')`
- Partial UNIQUE index: one CURRENT per `organization_id` (`WHERE status = 'CURRENT'`) — SQLite supports this
- CURRENT-on-save: INSERT new row CURRENT, set prior CURRENT to SUPERSEDED + `superseded_by_id`. **No in-place UPDATE of identity/logo columns on CURRENT.**

Do **not** add `branding_config` JSON. Do **not** add legal/corporate identifier columns.

### H. Logo custody

| Concern | Design |
|---------|--------|
| Root | `instance/brand_logos/` (`BRAND_LOGO_ROOT` config override, same style as `HISTORICAL_UPLOAD_ROOT`) |
| Path | `<org_id>/<sha256><ext>` — org segment `[A-Za-z0-9._-]{1,50}` |
| Formats | `.png`, `.jpg`, `.jpeg`, `.gif` — **existing** `SUPPORTED_LOGO_SUFFIXES` |
| Size | **5 MiB** — existing `MAX_LOGO_BYTES` |
| Magic | PNG `\x89PNG`, JPEG `\xff\xd8\xff`, GIF `GIF87a`/`GIF89a` |
| Remote URL | reject |
| Traversal | reject `..`, absolute paths, extra segments |
| Replace | new version + new/same sha object; **never** overwrite bytes if existing sha file content differs |
| Git | `instance/` already ignored |
| Serve | org-scoped `send_file`; current logo vs snapshot logo as separate lookups |
| ORG-001 seed | copy `app/static/branding/brayman-construction-logo.png` into custody as transitional default |
| Other orgs | **do not** copy the Brayman static logo |

### I. Proposal Brand Snapshot

Table `proposal_brand_snapshots` (1:1, Proposals-owned):

| Column | Type | Notes |
|--------|------|--------|
| `id` | Integer PK | |
| `proposal_id` | Integer NOT NULL UNIQUE FK `proposals.id` | |
| `organization_id` | String(50) NOT NULL FK `organizations.id` | isolation |
| `source_brand_profile_id` | Integer FK `organization_brand_profiles.id` | provenance; nullable if seed had no profile (should not happen after ensure) |
| `freeze_trigger` | String(32) NOT NULL | `ISSUED` \| `ACCEPTED` \| `MIGRATION_BACKFILL` |
| denormalized identity | same strings/colours as profile | **copied**, not live |
| logo identity | sha256, extension, byte_size, original_filename | bytes remain on disk |
| `frozen_at` | DateTime NOT NULL | |
| `frozen_by` | String(150) NOT NULL | |

Enforcement: service refuses UPDATE/DELETE of a snapshot row once inserted. Rendering: snapshot if present, else CURRENT Brand Profile for the proposal’s org. Never `ProposalTemplate` company/logo/colours. Never static Brayman as a floating fallback for a non-seeded org.

Do **not** add snapshot columns onto `proposals` commercial fields.

### J. Existing Issued/Accepted proposals (live DB, read-only)

Verified `instance/brayman_estimator.db` 2026-08-30, no mutation:

| Status | Count |
|--------|------:|
| Draft | 1 (`PROP-FG012-UAT-GM` id 1) |
| Issued | **0** |
| Accepted | **0** |

Template id 1 (`FG-012 UAT Template`, ORG-001): `company_name` = `Brayman Construction Inc. (FG-012 UAT)`; address/phone/email/website/logo_path/colours **NULL**.

**Backfill algorithm (implementation/migration data step, not this pass):** for every proposal with status Issued or Accepted and no snapshot: copy the **CURRENT** Brand Profile of that proposal’s organization (via template.organization_id / project.organization_id). `freeze_trigger = MIGRATION_BACKFILL`. Do not read live `ProposalTemplate` company fields as SoR (they are being retired). Do not alter commercial columns. Tests will create Issued/Accepted rows and must prove the same algorithm.

Draft `PROP-FG012-UAT-GM` is **not** snapshotted.

### K. Migration plan (do not create now)

- File: `migrations/versions/a9b0c1d2e3f4_add_organization_brand_profile_fg017.py`
- `revision = "a9b0c1d2e3f4"`
- `down_revision = "f8a9b0c1d2e3"`
- Additive: create the two tables + indexes + checks
- **Schema only** in Alembic (no logo byte copy in SQL)
- Application `ensure_brand_profiles_for_existing_organizations()` after upgrade: version 1 CURRENT per org from `Organization.legal_name` / `display_name` / `primary_address`; ORG-001 logo copy into custody in the **same insert**
- Then backfill snapshots for any Issued/Accepted proposals
- Downgrade: drop the two tables only; do not delete `instance/brand_logos` bytes from Alembic (document leftover files)
- Do **not** drop `proposal_templates` identity columns
- Do **not** run `flask db upgrade` in this reconnaissance

### L. Implementation files (later prompt)

New:

- `app/models/brand_profile.py`
- `app/services/brand_profile.py`
- `app/services/brand_logo_storage.py`
- `app/routes/settings.py` (or equivalent under existing Settings; url prefix `/settings`)
- `app/templates/settings/brand_profile.html`
- `tests/test_brand_profile_fg017.py`
- `migrations/versions/a9b0c1d2e3f4_add_organization_brand_profile_fg017.py`

Change:

- `app/models/__init__.py`
- `app/models/organization.py` (relationship only)
- `app/__init__.py` (register settings blueprint; `BRAND_LOGO_MAX_BYTES` / `BRAND_LOGO_ROOT`)
- `app/navigation.py` (enable existing Settings item → settings brand endpoint; **no** new top-level Brand Profile item)
- `app/services/proposals.py` (freeze hooks in `create_proposal` / `update_proposal`)
- `app/services/proposal_pdf.py` (render from snapshot or CURRENT profile)
- `app/routes/proposals.py` (preview logo URL from brand service)
- `app/templates/proposals/preview.html` (identity from brand context, not template company_*)
- `app/services/organizations.py` if ensure is colocated
- governed docs after implementation

Do **not** change: `app/project_controls/pdf.py`, permit HTML/PDF, `app/templates/partials/sidebar.html` logo/favicon, `app/templates/base.html` favicon, Internal breakdown templates, `ProposalTemplate` columns.

### M. Dedicated tests

`tests/test_brand_profile_fg017.py` must prove:

- CURRENT-on-save supersession; no DRAFT; no in-place CURRENT mutation
- one CURRENT per org
- logo validation (type/size/magic); reject remote URL, traversal, cross-org path
- bytes under `instance/brand_logos/<org>/`; not in Git
- ORG-001 seed identity + transitional logo; isolation org **without** Brayman logo leak
- Draft/Ready render uses CURRENT profile, not template `company_name` / `logo_path`
- first Issued freezes; later profile/logo change does not change Issued PDF/preview
- Draft → Accepted with no Issued snapshot freezes at Accepted
- Issued → Accepted keeps identical snapshot
- Accepted commercial immutability still holds
- backfill helper for Issued/Accepted does not change totals/status/lines
- snapshot present ⇒ render from snapshot even if status later set to Draft
- Change Order PDF still contains existing product-name/static-logo behaviour
- Permit HTML/PDF remain CalibAi-neutral (existing fixtures)

### N. Regression suite

Run focused then full:

- `tests/test_proposal_immutability.py`
- `tests/test_proposal_preview.py` (will need Brand Profile instead of template company assertions)
- `tests/test_proposal_pdf.py` (same)
- `tests/test_proposals.py`
- `tests/test_proposal_snapshots.py`
- `tests/test_change_orders.py`
- `tests/test_permit_intelligence_fg016.py` (or current FG-016 filename)
- `./venv/bin/python -m pytest -q`

### O. Security / isolation

- Org-prefix storage and query filters
- No remote logo fetch (close preview HTTP(S) path for this renderer)
- Path traversal rejection
- Untrusted original filename
- Snapshot/logo routes 404 across orgs
- Do not serve Git static Brayman as fallback for a foreign org

### P. Rollback / failure

- Alembic downgrade drops tables only
- Failed logo upload does not mutate CURRENT
- Failed freeze aborts the status transaction (no Issued without snapshot)
- Duplicate sha store is idempotent if bytes match; refuse if they do not

### Q. Conflicts with existing code

1. Preview `resolve_preview_logo_url` allows http(s) — do not use it for FG-017.
2. Issued is commercially mutable; brand snapshot is not — two layers.
3. Issued → Draft is currently allowed — snapshot stays sticky.
4. Tests assert template `Brayman Construction Co.` in preview/PDF — those tests must move to Brand Profile fields.
5. Settings nav item exists but `enabled: False` / `endpoint: None` — enable it; do not add a new sidebar module.
6. Header Settings button is a separate disabled control — **leave it** (not a new settings product).

### R. Unresolved (stop rather than invent)

1. Whether a later gate brands Internal Detailed Cost Breakdown — **out of FG-017**.
2. Whether Issued → Draft should be prohibited — **not decided**; sticky snapshot is the FG-017 rule.
3. Whether template form should hide retired company/logo fields — keep fields for compatibility; optional notice only if it stays a small copy change.
4. Legal identifiers remain out.
5. Colour hex validation strictness beyond “string(20) + existing renderer parse” — reuse `_parse_color` in `proposal_pdf.py`; do not invent a new colour system.

No repository constraint requires a Draft Brand Profile state.

### S. Recommended implementation sequence

1. Additive migration `a9b0c1d2e3f4` (schema only).
2. Models + logo storage + brand_profile service + ensure-seed.
3. Freeze hooks in `create_proposal` / `update_proposal`.
4. Preview + PDF consume snapshot-or-current.
5. Enable Settings nav + Brand Profile office form + logo upload + org-scoped logo route.
6. Dedicated tests, then regressions, then full suite.
7. Docs close. **Do not** live-migrate unless a later prompt says so.

---

## Live migrate and office UAT (2026-08-30)

Authorized separately from implementation. Product code was not changed in this pass.

| Item | Result |
|------|--------|
| Starting HEAD / `origin/main` | `00ca492e28118d75757e9a9c82384978b5decd92` |
| Alembic | Applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. Current = head = `a9b0c1d2e3f4`. One graph head. |
| Initialization | `ensure_brand_profiles_for_existing_organizations()` created **2** CURRENT profiles. `backfill_proposal_brand_snapshots()` created **0** (no Issued/Accepted rows existed). Draft `PROP-FG012-UAT-GM` was **not** snapshotted. |
| Organizations | `ORG-001` Brayman Construction Inc. / Brayman Construction / 411 St. John Street, Merrickville, Ontario K0G 1N0. `ORG-FG014-UAT` isolation org. Exactly one CURRENT each. Version 1 seed; no invented phone/email/website/legal identifiers. |
| ORG-001 logo | Copied governed static Brayman PNG into `instance/brand_logos/ORG-001/948f96e08827f18d77b47538f65c8b98b45caaf9c981adccba0189976948efe9.png` (80007 bytes; SHA matches). |
| Isolation logo | `ORG-FG014-UAT` CURRENT has **no** logo; no Brayman file under that org path. |
| Office UAT port | **5010** |
| Settings | `/settings/brand-profile` shows ORG-001 identity; logo via `/settings/brand-logo`; no filesystem path/SHA leak; Settings in existing nav; no new top-level module; header Settings remains disabled (`Settings (coming soon)`). Sidebar still uses static chrome logo. |
| CURRENT-on-save | Phone `FG017-UAT` created v2 CURRENT (v1 SUPERSEDED). Later `FG017-UAT-POST-ISSUE` created v3. Restore via governed `save_brand_profile` created v4 CURRENT with empty phone (original identity + same logo). No in-place identity/logo UPDATE. Exactly one CURRENT throughout. |
| Draft/Ready | Existing Draft `PROP-FG012-UAT-GM` and UAT `PROP-FG017-UAT-ISSUE` preview/PDF used CURRENT Brand Profile (`Brayman Construction`, address, then-current phone). Template `company_name` `Brayman Construction Inc. (FG-012 UAT)` did **not** render. Logo `/proposals/<id>/brand-logo`. HTML and PDF agreed. |
| Issued freeze | `PROP-FG017-UAT-ISSUE` (id 2) → Issued created **one** snapshot `freeze_trigger=ISSUED` from CURRENT v2 (phone `FG017-UAT`, Brayman logo SHA). Totals `$132.94` unchanged. |
| Post-freeze profile change | After v3 CURRENT phone `FG017-UAT-POST-ISSUE`, Issued/Accepted preview+PDF of id 2 still showed `FG017-UAT` and **not** `POST-ISSUE`. Draft id 1 followed CURRENT. |
| Issued → Accepted | Status Accepted; snapshot count remained **1**; trigger remained `ISSUED`; phone remained `FG017-UAT`. ADR-002 lock: edit/status mutation refused. UI: “Accepted — locked.” Totals unchanged. |
| Accepted without Issued | Office POST created `PROP-FG017-UAT-ACCEPT-DIRECT` (id 3) as Accepted. Snapshot `freeze_trigger=ACCEPTED` from then-CURRENT v3 (phone `FG017-UAT-POST-ISSUE`). `issued_at` null. Later restore did not refresh it. |
| Cross-org | Isolation proposal `PROP-FG017-UAT-ISO` (id 4, Draft, project 4). ORG-001 HTTP GET detail/preview/logo/PDF → **404**. Isolation render context is `FG-014 UAT Isolation Org Ltd.` with **no** logo and **no** Brayman name. Isolation `/brand-logo` fail-closed 404 (no static Brayman fallback). Template `SHOULD-NOT-RENDER Isolation Template Co.` was not used as identity. |
| Tests | Dedicated **22 passed**. Focused regressions **97 passed** (119 with dedicated). Full suite **`./venv/bin/python -m pytest -q` → 423 passed**. |
| Protected non-goals | Change Order PDF still hardcoded static Brayman / `Brayman Construction Platform`. Permit HTML/PDF untouched (CalibAi-neutral). No Phase D, supplier, QuickBooks, contract, auth, BUILD/MONITOR/LEARN, external AI, chrome redesign, or legal-identifier invention. |

Labeled UAT residue (leave labeled; do not invent cleanup): Brand Profile versions 1–4 on ORG-001 (v4 CURRENT, empty phone, original identity); isolation CURRENT v1; proposals ids 2–4 (`PROP-FG017-UAT-ISSUE` Accepted, `PROP-FG017-UAT-ACCEPT-DIRECT` Accepted, `PROP-FG017-UAT-ISO` Draft); estimate `EST-FG017-UAT-ISO`; template `FG-017 UAT Isolation Template`.

---

## Explicit stop conditions for the implementation prompt

Stop and report if: a second Alembic head appears; Permit/CO/app-shell logo work is requested; legal identifiers are invented; `branding_config` JSON is about to be added; remote URL logos are proposed; Draft Brand Profile state is about to be added; Internal breakdown branding is pulled in; template identity columns are dropped.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Accept ADR-040 / Approve FG-017 / implementation reconnaissance | 2026-08-30 |
| Cursor implementation note | Product implementation + revision `a9b0c1d2e3f4` + 22 dedicated tests. Live migrate **NOT RUN**. **NOT CLOSED.** | 2026-08-30 |
| Cursor live-migrate / office UAT | Applied `f8a9b0c1d2e3` → `a9b0c1d2e3f4`. Ensure + backfill. Office UAT port **5010**. Full suite **423 passed**. **CLOSED / OPERATIONAL FOR UAT.** | 2026-08-30 |
