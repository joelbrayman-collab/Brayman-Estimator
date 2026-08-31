# ADR-040 — Organization Brand Profile

| Field | Value |
|-------|--------|
| Title | ADR-040: Organization Brand Profile, Logo Custody, and Issued-Document Brand Snapshots |
| Status | **Accepted** (2026-08-30; governing [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT**). Live current = head `a9b0c1d2e3f4`. Office UAT **PASSED** on port **5010**. |
| Date | 2026-08-30 |
| Related | [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) **CLOSED / OPERATIONAL FOR UAT** · [organization-brand-profile.md](../architecture/organization-brand-profile.md) · [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md) **Accepted** · [ADR-002](ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-019](ADR-019-calibai-lifecycle-and-project-hub.md) **Accepted** · [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-032](ADR-032-app-managed-historical-workbook-storage.md) **Accepted** · [ADR-020](ADR-020-build-module-boundary.md) **Accepted** · [modules/proposals.md](../modules/proposals.md) · [change-order-document-family.md](../architecture/change-order-document-family.md) · [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) · Constitution Article 5 |

---

## Problem

Contractor identity on generated customer documents is split and mutable:

- `Organization` holds `legal_name`, `display_name`, and `primary_address` only ([`app/models/organization.py`](../../app/models/organization.py)). That is **not** a Brand Profile.
- `ProposalTemplate` holds a second company block (`company_name`, `company_address`, `company_phone`, `company_email`, `company_website`, `logo_path`, colours). Those strings already diverge from ORG-001 (form default `"Brayman Construction Co."` vs seeded `Brayman Construction Inc.`).
- Proposal PDF/preview resolve logo and company lines from the **live** template (then a static Brayman asset). Accepted commercial lines are frozen ([ADR-002](ADR-002-accepted-proposal-immutability.md)); **visual/company identity at render time is not**.
- Change Order PDF uses a hardcoded static Brayman logo and does not read Organization or ProposalTemplate ([`app/project_controls/pdf.py`](../../app/project_controls/pdf.py)).
- Permit Report HTML/PDF correctly use a **neutral CalibAi** layout with **no** Brayman logo ([FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT**; [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

There is no organization-owned logo store, no tenant-safe branding source of truth, and no issued-document brand snapshot. A later logo or address change can rewrite historical Proposal PDFs.

## Context

[organization-brand-profile.md](../architecture/organization-brand-profile.md) pins Brand Profile as the future single branding source and forbids implementing `branding_config` JSON from [organization-and-calibration-architecture.md](../architecture/organization-and-calibration-architecture.md). Architecture reconnaissance (2026-08-30) was reviewed and accepted as the basis for this ADR. This ADR does **not** implement that pin.

`Organization` remains the tenant / legal-commercial root ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)). Do **not** create a second organization concept.

Constitution Article 5 and architecture Rule 3 forbid silent overwrite of accepted commercial records. Issued branding is part of that historical identity.

---

## Decision

**Accepted** 2026-08-30. Product implementation still requires a separate [FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) implementation prompt. This ADR does **not** create a migration.

Joel / ChatGPT locked the following FG-017 rules at acceptance:

- **CURRENT-on-save.** No separate Draft Brand Profile state.
- **Freeze at first ISSUED.** If a proposal reaches ACCEPTED with no Issued snapshot, freeze at ACCEPTED. Once frozen, never refresh; ISSUED → ACCEPTED keeps the identical snapshot.
- **App-shell chrome out.** Internal Detailed Cost Breakdown consumption **out** of FG-017.
- **Settings navigation:** use the existing Settings / organization architecture; do not add a new top-level module.
- **Legal identifiers out.** Do not implement `branding_config` JSON.

### 1. Organization relationship

- `Organization` remains the only tenant/legal-commercial root.
- Brand Profile is **organization-scoped** (one current profile per organization). It is not a second tenant, not a user, and not a project record.
- Organization identity fields (`legal_name`, `display_name`, `primary_address`) continue to describe the commercial tenant. Brand Profile is the **document-facing** identity used on generated organization/customer documents. They must not silently diverge after Brand Profile is current; exact sync rules are an implementation concern under FG-017, not a second source of contractor letterhead.

### 2. Brand Profile ownership

- **Owner:** Organization subsystem ([ADR-028](ADR-028-organization-foundation-and-project-commercial-context.md)).
- **First consumer:** Proposals (preview + PDF).
- **Later consumers (architecture only; not this ADR’s implementation):** Change Order document family; customer-facing Permit & Approvals Report rendering; Contract; Warranty; QuickBooks-facing exports; procurement / project reports.
- Document **structure / layout** remains CalibAi-governed. Brand Profile customizes **identity**, not arbitrary Word-template upload.

### 3. Contractor identity vs CalibAi product chrome

Brand Profile governs **contractor letterhead** on generated organization/customer documents.

It does **not** govern CalibAi application chrome in this capability:

- sidebar logo
- favicon
- HTML `<title>` / product UI identity
- “Brayman Construction Platform” / CalibAi office chrome

App-shell redesign is out of scope. Permit analysis reports may remain CalibAi-neutral until a later gated customer-facing permit PDF consumes Brand Profile ([ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md)).

### 4. Minimum Brand Profile fields (do not invent legal identifiers)

Anticipate and, under a later approved implementation, persist:

| Class | Fields |
|-------|--------|
| Legal / company identity | legal business name; customer-facing name where separately stored |
| Operating / contact | address; phone; email; website |
| Visual | organization-owned logo; optional document primary/accent colours currently living on `ProposalTemplate` |

Do **not** invent business numbers, licence numbers, registration identifiers, or other legal/corporate identifiers in this ADR. Those remain unresolved unless a later Legal Content Gate / Joel decision adds them.

Current `Organization.legal_name` / `display_name` / `primary_address` are **not** a complete Brand Profile.

Do **not** implement the conceptual `branding_config` JSON column from the intended Organization entity table.

### 5. Logo / asset custody

Logo bytes are organization-owned, privately app-managed, and **not** stored in Git as the source of truth.

Custody must:

- be **organization-scoped**
- live in **private instance storage** (pattern analogous to [ADR-032](ADR-032-app-managed-historical-workbook-storage.md) / plan uploads — exact path is an implementation detail)
- use **controlled naming** (user filenames are metadata, never trusted paths)
- **validate** file type, size, and that the path cannot escape the org prefix (no path traversal)
- **never follow remote URLs** as the source of truth (current Proposal PDF already refuses remote logo URLs; keep that rule)
- be **replaceable only through explicit organization action**
- retain prior bytes needed by issued-document snapshots (archive / supersede; **no silent in-place overwrite**)

The existing static file `app/static/branding/brayman-construction-logo.png` is **not** the long-term source of truth. A later implementation may seed ORG-001 custody from that asset; Git static branding must not remain the live letterhead resolver.

### 6. Tenant isolation

Brand Profile rows, logo bytes, and issued-document brand snapshots belonging to one organization must **never** be readable or renderable by another organization. Isolation tests are mandatory in any later implementation (same bar as FG-014 / FG-015 isolation).

Shared platform chrome (sidebar/favicon) is not tenant branding and is out of this ADR’s Brand Profile store.

### 7. Provenance, versioning, approval state

Brand Profile is versioned. A later implementation must record at least:

- organization
- version identity
- field values used for rendering
- logo identity (hash / custody key), not a mutable live path as the only record
- created_at / created_by (actor-string until auth exists)
- supersession relationship to the prior current version

**Approval / activation state:** one **CURRENT** Brand Profile per organization. V1 is **CURRENT-on-save**: saving identity or replacing a logo creates a **new** version that is immediately CURRENT; the prior CURRENT becomes **SUPERSEDED**. There is **no** Draft Brand Profile state. Silent in-place mutation of a CURRENT row is **prohibited** (new version + supersession instead).

There is no separate “Brand Profile approval board.” Saving is the activation event.

### 8. Immutable issued-document branding snapshots

```text
CURRENT ORGANIZATION BRAND PROFILE
→ DOCUMENT RENDER / ISSUE
→ ISSUED-DOCUMENT BRAND SNAPSHOT
→ IMMUTABLE HISTORY
```

Issued / Accepted customer-facing documents must preserve the branding **actually used when issued**. Later changes to name, address, contact, logo, or document colours must **not** rewrite:

- a Proposal Issued or Accepted earlier
- a later Accepted Change Order document (when that family is gated)
- a later customer-facing Permit PDF (when that rendering is gated)
- a later executed Contract / Warranty

**Proposal (first consumer):**

- `Draft` / `Ready` proposals with **no** brand snapshot render from the **current** Brand Profile.
- Freeze the Proposal Brand Snapshot when the proposal **first reaches Issued**.
- If a workflow reaches **Accepted** without an Issued snapshot, freeze at Accepted.
- Once frozen: never refresh from the live Brand Profile; Issued → Accepted must preserve the **identical** snapshot; later Brand Profile or logo changes must not alter that proposal’s preview/PDF identity.
- Existing Issued/Accepted proposals receive a one-time snapshot at implementation so they stop floating. That operation must not alter commercial lines, estimate/pricing snapshots, totals, acceptance state, or [ADR-002](ADR-002-accepted-proposal-immutability.md) commercial immutability.
- `ProposalTemplate` company/logo/colour columns are **not** dropped; they cease to be the authoritative identity source for the FG-017 Proposal rendering path.

### 9. ProposalTemplate relationship

`ProposalTemplate` remains Proposals-owned and org-scoped. It should retain:

- default clauses / narrative defaults
- layout and display-flag configuration
- other proposal-template concerns

Contractor company identity, contact block, logo, and document-facing colours **migrate to Brand Profile**. After a later approved implementation, Proposal rendering must not depend on live `company_name` / `company_address` / `company_phone` / `company_email` / `company_website` / `logo_path` / colour columns.

First implementation must be **additive**: do not drop those template columns in the first gate. They become unused for rendering. Cleanup/removal is a later gated change.

Do **not** create per-module logo settings.

### 10. Proposal migration / consumer strategy

Proposal is the **first** intended consumer because identity is duplicated there today, branding lives partly on the template, and Accepted PDFs can float.

First-gate product work (only if FG-017 is later Approved and an implementation prompt is issued): Brand Profile + logo custody + Proposal consume + Issued/Accepted snapshot. Not Change Order PDF rewrite. Not Permit PDF branding.

### 11. Change Order relationship

The existing Change Order **business record** remains authoritative ([change-order-document-family.md](../architecture/change-order-document-family.md)). Do **not** create a second Change Order entity.

Future Change Order **documents** must consume this **one** Brand Profile and snapshot branding when issued/accepted. Current office PDF hardcoded Brayman logo is **not** that family.

This ADR does **not** authorize Change Order document-family implementation, email, field UX, or CO PDF rewrite.

### 12. Permit Report relationship

Permit **analysis truth** is independent of branding ([ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md)). Branding must not change findings, rules, facts, or snapshot immutability of analysis.

Current FG-016 HTML/PDF stay **neutral CalibAi** until a later gate authorizes customer-facing permit rendering. That later rendering consumes this **one** Brand Profile and snapshots it. Do **not** create a second Permit-logo system.

This ADR does **not** authorize Permit analysis changes or branded permit PDF work.

### 13. Future Contract / Warranty relationship

Ontario Contract + Warranty remain under the Legal Content Gate. Legal template text is **not** Brand Profile. Future generated contract/warranty packages consume Brand Profile for **identity** (legal name, address, logo) only. This ADR does not implement contracts.

### 14. Future QuickBooks relationship

QuickBooks-facing exports, when later gated, consume Brand Profile **where appropriate** for contractor identity. This ADR does not implement QuickBooks or invent export schema.

### 15. Supersession / history behaviour

- Replacing Brand Profile creates a new version; prior CURRENT becomes SUPERSEDED.
- SUPERSEDED versions remain readable for snapshot reconstruction.
- Logo replacement archives prior bytes; snapshots keep the logo identity they were issued with.
- Do not rewrite historical issued-document snapshots when the current profile changes.
- Proposal void/supersede/revision (ADR-004) remains **Proposed** and out of this ADR. A later superseded **proposal** would snapshot branding at the new issue event; it would not mutate the prior proposal’s brand snapshot.

### 16. Security / path / file-validation expectations

Later implementation must:

- reject path traversal and cross-org prefix access
- reject remote URL fetch / SSRF-style logo resolution
- validate content type and size
- keep logo bytes out of Git
- not serve one organization’s logo at another organization’s document URL
- treat original filenames as untrusted

Exact validators are an implementation detail under a later approved Feature Gate.

### 17. Explicit non-goals of this ADR

This ADR does **not** authorize or decide:

- product implementation, schema, or migration (those require Accepted ADR + Approved FG-017 + implementation prompt)
- Change Order document family, email, or CO PDF rewrite
- Permit analysis changes or branded Permit PDF
- Phase D, supplier integration, QuickBooks, Ontario Contract/Warranty templates
- auth / SaaS onboarding, BUILD, MONITOR, LEARN
- external AI / runtime web lookup
- Word-template upload or per-module logo systems
- `branding_config` JSON
- CalibAi app-shell redesign or logo redesign
- invented legal/corporate identifiers
- Internal Detailed Cost Breakdown branding (**out of FG-017**; no decision made here about later internal-document branding)

---

## Alternatives Considered

- **Keep ProposalTemplate as branding source of truth** — Rejected: duplicates Organization identity, floats Accepted PDFs, cannot serve CO/Permit/Contract without per-module logos.
- **Implement intended `branding_config` JSON on Organization** — Rejected: the Brand Profile pin forbids that column as the branding design; structured org-owned profile + logo custody + snapshots are required for immutability and isolation.
- **Drive app-shell chrome from Brand Profile in the first capability** — Rejected for this ADR: contractor letterhead and CalibAi product chrome are different concerns; mixing them expands scope into UI redesign.
- **Require Brand Profile before Permit analysis (reopen FG-016)** — Rejected: [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md) already decided branding is document identity, not analysis truth.
- **Snapshot branding only in stored PDF bytes** — Rejected as the sole mechanism: re-renderable preview/PDF must remain historically true without depending on an irrecoverable blob; structured snapshot + logo identity is required. Stored PDF bytes may exist later but do not replace the snapshot rule.
- **Remote URL logos** — Rejected: mutable, tenant-unsafe, SSRF-prone; current Proposal PDF already refuses them.

---

## Consequences

**Positive:** Single governed branding source; tenant-safe logo custody; Issued/Accepted Proposal identity stops floating; later document families can consume one profile without per-module logo settings; Permit analysis remains unentangled.

**Negative:** First implementation will need additive schema, logo storage, Proposal renderer changes, and a one-time snapshot of existing Issued/Accepted proposals. Template company columns become debt until a later cleanup. CO PDF and Permit PDF remain inconsistently branded until later gates. App chrome stays Brayman/CalibAi-labelled independently of contractor letterhead.

---

## Module Ownership Impact

- **Organization subsystem** owns Brand Profile records and logo custody.
- **Proposals** consumes Brand Profile for preview/PDF and owns the **proposal** issued-document brand snapshot. Proposals does **not** own Brand Profile.
- **Project Controls / Projects** later consume Brand Profile for Change Order documents (not in the first gate).
- **Projects / Permit Intelligence** later consume Brand Profile for customer-facing permit rendering only (not analysis).
- No new module. No ownership transfer of `Organization`, `Proposal`, `ChangeOrder`, or permit analysis snapshots.

---

## Data Ownership Impact

- Brand Profile and logo bytes: organization-owned, versioned, supersede-in-place forbidden.
- Issued-document brand snapshots: historically protected records (Constitution Article 5; ADR-002 spirit).
- `ProposalTemplate` clause/layout data remains Proposals-owned.
- Permit analysis snapshots remain Projects/Permit Intelligence-owned and branding-independent.

---

## Migration Impact

**None in this acceptance pass.** No revision is created here.

[FG-017](../feature-gates/FG-017-organization-brand-profile-v1.md) implementation (separately authorized) requires **one** bounded additive Alembic revision. Designed revision id **`a9b0c1d2e3f4`** (down_revision `f8a9b0c1d2e3`). Exact schema is recorded on FG-017. Do not create that revision from this ADR.

---

## Testing Impact

None until an FG-017 implementation prompt. Dedicated tests are listed on FG-017.

---

## Documentation Impact

This ADR; FG-017; Brand Profile pin; indexes; current-state / session-handoff / roadmap / chat-workflow-log.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman | 2026-08-30 |
| ChatGPT review | Accept ADR-040 / Approve FG-017 / implementation reconnaissance | 2026-08-30 |
| Cursor implementation note | Docs-only acceptance. **No product implementation.** Reconnaissance recorded on FG-017. | 2026-08-30 |
