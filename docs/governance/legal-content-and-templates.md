# Legal Content and Template Governance

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-08-30 |
| Implementation | Template registers and approval workflow **not implemented** |

## Purpose

Govern Ontario construction contract language, statutory/consumer wording, warranty obligations, and legal templates. The Estimator may **not** invent or silently alter legal obligations.

## Legal Content Gate

| Rule | Detail |
|------|--------|
| Governed provenance | Ontario contract clauses, statutory/consumer wording, warranty language, and legal templates require **separately governed template provenance and approval** |
| AI / tool generation | AI or tool generation **cannot independently** set legal content to **APPROVED** |
| Human approval | Legal templates reach production use only after explicit governed approval |
| No silent edits | Approved template versions are superseded — not silently overwritten |

**August 2026 scope:** Record governance only. **Do not draft substantive Ontario contract language** in documentation or implementation tasks unless Joel explicitly authorizes template authoring under separate legal review.

## Ontario construction contract register (governed — empty until approved)

| Field | Policy |
|-------|--------|
| Template identity | Versioned register entry (ID, title, jurisdiction, effective date) |
| Source | Approved legal/commercial source — not ad hoc AI output |
| Approval state | Follows contract/warranty progression ([project-document-package.md](../architecture/project-document-package.md)) |
| Estimate linkage | Generated only from **APPROVED** estimate with provenance preserved |
| Attachment | Applicable warranty document attached as schedule |

**Register status:** No production templates registered in repository as of 2026-08-25. Future entries live in this governance track (implementation TBD).

## Warranty template register (governed — empty until approved)

Warranty language is **governed content**.

| Rule | Detail |
|------|--------|
| Templates required | Approved/versioned warranty templates must exist **before production use** |
| No invention | The Estimator may not invent or silently alter warranty obligations |
| Contract package | Applicable warranty document **must** attach to the Ontario construction contract package |
| Versioning | Supersede prior approved versions explicitly |

**Register status:** No production warranty templates registered in repository as of 2026-08-25.

## Not this pin — Permit & Approvals Report

**Status:** **FUTURE / NOT IMPLEMENTED.** Canonical record: [permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md).

This Legal Content Gate governs **Ontario construction contract and warranty templates**. It does **not** own municipal/provincial/state zoning, permit, servicing, or AHJ requirement sources.

The Permit & Approvals Report pin does **not** authorize:

- jurisdictional legal-library implementation
- live regulatory AI
- in-product web lookup
- automatic permit approval conclusions
- municipal submissions
- schema, migration, ADR, or a Feature Gate

Do not treat ChatGPT or other tool research as an authoritative permit determination. Preliminary research on the Mike Pratt Coach House reference case is **not** governed legal content.

## Contract and warranty progression states

Shared lifecycle states (see [project-document-package.md](../architecture/project-document-package.md)):

PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED

Generation alone does not mean final or sent.

## Open decisions (Joel / legal)

1. Template storage location and format (repository vs controlled document store)
2. Approval authority for legal template versions
3. Ontario-specific statutory clause set and update process
4. E-signature provider boundary (Future)

## Related

- [architecture/project-document-package.md](../architecture/project-document-package.md)
- [architecture/permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) — **FUTURE / NOT IMPLEMENTED**; not this Legal Content Gate
- [platform-governance.md](../platform-governance.md)
- [platform-constitution.md](../platform-constitution.md) — Articles 5, 8, 9
