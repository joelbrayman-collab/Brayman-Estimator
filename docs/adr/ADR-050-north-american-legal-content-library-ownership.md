# ADR-050 — North American Legal Content Library Ownership and Fail-Closed Boundary

| Field | Value |
|-------|--------|
| Title | ADR-050: North American Legal Content Library Ownership and Fail-Closed Boundary |
| Status | **Accepted** by Joel Brayman / ChatGPT Architect, 13 Sep 2026 (architecture / fail-closed ownership only). Does **not** authorize product code, schema, migration, legal drafting, or FG-024 Slice A implementation. |
| Date | 2026-09-12; Accepted 2026-09-13 |
| Related | [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) · [fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md) · [legal-content-and-templates.md](../governance/legal-content-and-templates.md) · [project-document-package.md](../architecture/project-document-package.md) · [ADR-037](ADR-037-project-location-and-jurisdiction-resolution.md) **Accepted** · [ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) **Accepted** · [ADR-039](ADR-039-permit-report-snapshot-immutability-and-workflow.md) **Accepted** · [ADR-002](ADR-002-accepted-proposal-immutability.md) **Accepted** · [ADR-040](ADR-040-organization-brand-profile.md) **Accepted** · [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **CLOSED** (presentation only) |

This ADR is the **ownership and fail-closed boundary** for the North American CONTRACT-stage legal-content library (FG-024 Slice A). It is the analogue of [ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) for permit rules: a distinct governed library, not a second jurisdiction resolver, and not a second contract system.

Accepting this ADR does **not** by itself authorize product code, Ontario/U.S. population, Family 05 legal approval, contract generation, or Native Signing. A later bounded Cursor prompt is required for Slice A product.

---

## Context

CalibraytAI already has:

- one jurisdiction **identity** resolver ([ADR-037](ADR-037-project-location-and-jurisdiction-resolution.md) / FG-015);
- a separate Permit Rules Library ([ADR-038](ADR-038-permit-intelligence-authority-and-rules-library.md) / FG-016);
- a Legal Content Gate that remains **empty** ([legal-content-and-templates.md](../governance/legal-content-and-templates.md));
- FG-022 Family 05 as an **APPROVED REUSABLE PRESENTATION MASTER** that is **COMMERCIAL_DRAFT / NOT LEGALLY APPROVED / NOT FOR EXECUTION**;
- V1-04 output 4 **NOT IMPLEMENTED**, supplied by V1-06 / FG-024, not by a second renderer.

Without this ADR, a later implementer could:

- hard-code Ontario as the product architecture of CONTRACT;
- treat Family 05 as an approved fallback contract;
- reuse Permit Rules as contract clauses;
- invent a second geo resolver;
- generate a generic “North American” contract when no approved package exists;
- let AI mark legal content APPROVED;
- collapse Native Signing process approval into template legal approval.

[FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md) already recorded the North American intent. FG-024 Q11 deferred library schema / package ownership to a later implementation prompt. This ADR is that ownership decision. It was **Accepted** 13 Sep 2026 as architecture only.

---

## Decision

**Accepted.** Architecture / fail-closed ownership only. Do **not** treat acceptance as Slice A product authorization.

### 1. One North American legal-content library; Ontario is first package, not product scope

The library is architected for **Canada (provinces and territories)** and the **United States (states)**. Population is incremental. Immediate population of all jurisdictions is forbidden.

Ontario is the **first expected Canadian package** and the first real-life UAT jurisdiction because ORG-001 / Brayman Construction operates in Ontario. Ontario is **not** the architectural scope of CONTRACT.

### 2. Legal Content Gate remains the approval authority

FG-024 **extends** the Legal Content Gate. It does **not** replace it.

AI or tools **cannot independently** set legal content to **APPROVED**. Approved versions are superseded, not silently overwritten. `APPROVED` and `ACTIVE` are not the same date.

### 3. One jurisdiction resolver; two independent content authorities

Reuse [ADR-037](ADR-037-project-location-and-jurisdiction-resolution.md). Do **not** create a second geo model.

| Domain | Authority |
|--------|-----------|
| Location / jurisdiction **identity** | Projects / one resolver |
| Permit **rules** content | Permit Rules Library / ADR-038 |
| Contract **legal** content | Legal Content Gate / FG-024 / this ADR |

A Project may select both permit rules and a contract package. The content authorities remain independent.

### 4. Fail closed. No generic North American fallback

CalibraytAI must **not** generate or present an apparently approved / jurisdiction-compliant contract when legal authority is insufficient, including:

- unsupported or unresolved jurisdiction;
- no counsel-approved package;
- draft / PROPOSED / COUNSEL REVIEW only;
- expired or SUPERSEDED without an ACTIVE replacement;
- unresolved effective-date conflict;
- required counsel review incomplete.

Family 05 must **not** be used as a fallback executable contract. Cross-jurisdiction substitution is prohibited.

### 5. Presentation is not legal approval

FG-022 owns visual / presentation masters. Organization Brand Profile / FG-017 owns brand presentation. Neither owns Legal Content Gate approval.

### 6. Native Signing is a separate process track

V1-07 owns signing **process**. It does not own template legal text. Contract signing remains behind the Legal Content Gate.

### 7. V1-04 does not own a second contract engine

V1-04 owns four-output **package completeness**. V1-06 / FG-024 supply output 4. Do not rebuild outputs 1–3. Do not create a second contract system.

### 8. Acceptance does not authorize product implementation

Accepting this ADR does **not** authorize product code, schema, migration, legal drafting, or Slice A implementation. A later bounded Cursor prompt is required.

---

## Alternatives Considered

- **Ontario-only hard-coded contract** — Rejected: FG-024 forbids a one-off; commercialization is Canada + United States.
- **Generic North American fallback template** — Rejected: fail-closed is mandatory; fallback would present false legal authority.
- **Reuse Permit Rules Library as contract clauses** — Rejected: ADR-038 already separated the domains.
- **Treat Family 05 as the V1 legal package** — Rejected: COMMERCIAL_DRAFT / NOT LEGALLY APPROVED.
- **Second jurisdiction resolver for contracts** — Rejected: ADR-037 is the one identity resolver.
- **No ADR; implement from FG-024 recording alone** — Rejected: FG-024 Q11 deferred schema/ownership; Constitution/governance require an ADR for this ownership and fail-closed control.

---

## Consequences

**Positive:** Durable ownership; North American architecture preserved; Ontario remains first UAT package; fail-closed is an ADR-level invariant; second contract system is forbidden.

**Negative:** Slice A product still cannot start until Joel issues a bounded implementation prompt. Ontario legal language remains BLOCKED on counsel (06D). Empty library means fail-closed by absence until a later product slice exists.

## Module Ownership Impact

CONTRACT stage owns library records and later generation snapshots. Legal Content Gate owns approval. Projects owns `ProjectLocation` / resolver identity (referenced, not taken). Permit Intelligence unchanged. Proposals unchanged (output 2). Estimating unchanged (outputs 1 and 3). Native Signing unchanged. FG-022 presentation unchanged.

## Data Ownership Impact

Future library packages, versioned content objects, provenance, and approval/activation states are **platform-governed legal content**, not org commercial intelligence. Generated project contract snapshots (Slice C, later) would be organization-scoped and project-tied. Do not pool one contractor’s generated contracts as another’s legal templates.

## Migration Impact

**Deferred.** None in this pass. A later authorized Slice A product prompt may require an **additive** migration for empty library tables. Do not write a revision from this ADR.

## Testing Impact

None in this pass. A later empty-library product slice must prove fail-closed when no ACTIVE package exists.

## Documentation Impact

[fg-024-slice-a-legal-content-library-preflight.md](../architecture/fg-024-slice-a-legal-content-library-preflight.md); [FG-024](../feature-gates/FG-024-north-american-contract-intelligence-and-legal-content-lifecycle.md); [legal-content-and-templates.md](../governance/legal-content-and-templates.md); [project-document-package.md](../architecture/project-document-package.md); this ADR index.

## Approval

| Role | Name | Date |
|------|------|------|
| Joel | Joel Brayman / ChatGPT Architect | 2026-09-13 |
| ChatGPT review | FG-024 Slice A documentation preflight (2026-09-12); final review / Accept | 2026-09-13 |
| Cursor implementation note | Drafted **Proposed** 2026-09-12 from ADR-000. **Accepted** 2026-09-13 documentation-only. No product code. No migration. |
