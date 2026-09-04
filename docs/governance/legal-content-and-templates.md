# Legal Content and Template Governance

| Attribute | Value |
|-----------|--------|
| Status | **Governing** |
| Updated | 2026-09-04 |
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

**Subsequent status (2026-09-03):** Recovered Allen Jacques document **05** (`Ontario Construction Contract COMMERCIAL_DRAFT`) is an **approved presentation reference** only. It does **not** populate this register, does **not** authorize production contract use, customer execution, or Native Signing. See [approved-document-presentation-reference-baseline.md](../architecture/approved-document-presentation-reference-baseline.md).

**Subsequent status (2026-09-04):** Approved presentation **source custody CLOSED**. Durable exact ZIP is outside Git. That custody closure does **not** populate this register, does **not** approve Document 05 legal content, and does **not** authorize production contract use, customer execution, or Native Signing.

**Subsequent status (2026-09-04, FG-022):** [FG-022](../feature-gates/FG-022-reusable-approved-document-template-family-v1.md) **APPROVED / IMPLEMENTATION NOT STARTED** authorizes later project-neutral **presentation** extraction only. Family 05 reusable V1 treatment is **PROJECT-NEUTRAL PRESENTATION / COMMERCIAL-DRAFT REFERENCE** and must remain **COMMERCIAL DRAFT — NOT FOR EXECUTION**. FG-022 does **not** populate this register, does **not** approve contract or warranty language, and does **not** authorize execution or Native Signing.

## Warranty template register (governed — empty until approved)

Warranty language is **governed content**.

| Rule | Detail |
|------|--------|
| Templates required | Approved/versioned warranty templates must exist **before production use** |
| No invention | The Estimator may not invent or silently alter warranty obligations |
| Contract package | Applicable warranty document **must** attach to the Ontario construction contract package |
| Versioning | Supersede prior approved versions explicitly |

**Register status:** No production warranty templates registered in repository as of 2026-08-25.

## Not this gate — Permit Intelligence / Permit Rules Library

**Status:** Permit Rules Library is a **separate** governed source from this Legal Content Gate. Architecture **Accepted**: [ADR-038](../adr/ADR-038-permit-intelligence-authority-and-rules-library.md). Canonical V1 pin: [permit-rules-library.md](../architecture/permit-rules-library.md). [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) **CLOSED / OPERATIONAL FOR UAT** populated a bounded Ontario / Ottawa coach-house corpus. This gate still does **not** own municipal/provincial zoning or permit rules.

This Legal Content Gate governs **Ontario construction contract and warranty templates**. It does **not** own municipal/provincial/state zoning, permit, servicing, or AHJ requirement sources. The Permit Rules Library is a **separate** governed source.

[FG-015](../feature-gates/FG-015-permit-foundation-v1-project-location-jurisdiction-preliminary-permit-profile.md) and this Legal Content Gate do **not** authorize:

- jurisdictional rules-library population (that belongs to [FG-016](../feature-gates/FG-016-ontario-ottawa-permit-intelligence-poc.md) implementation, not this Legal Content Gate)
- live regulatory AI
- in-product web lookup
- automatic permit approval conclusions
- municipal submissions
- treating permit findings as contract clauses

Do not treat ChatGPT or other tool research as an authoritative permit determination. Preliminary research on the Mike Pratt Coach House reference case is **not** governed legal content. AI cannot mark regulatory content approved.

## Contract and warranty progression states

Shared lifecycle states (see [project-document-package.md](../architecture/project-document-package.md)):

PROPOSED → APPROVED → GENERATED → VERIFIED → SENT FOR SIGNATURE → SIGNED → SUPERSEDED

Generation alone does not mean final or sent.

## Open decisions (Joel / legal)

1. Template storage location and format (repository vs controlled document store)
2. Approval authority for legal template versions
3. Ontario-specific statutory clause set and update process
4. E-signature provider boundary (Future). **Subsequent status (2026-09-01):** Native Signing reconnaissance is **complete** ([contract-esignature-and-signed-change-order.md](../architecture/contract-esignature-and-signed-change-order.md)). Recommendation **NATIVE V1**. Counsel process-review specification **PREPARED** ([native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md)) — **DRAFT FOR ONTARIO COUNSEL REVIEW / NOT LEGAL APPROVAL**. **Development may proceed under separate governance. Production activation / real customer use is blocked pending counsel process approval.** This Legal Content Gate for Contract/Warranty **templates** is **unchanged** and remains in force. Native signing must never bypass approved Contract/Warranty templates or human approval before send. Change Orders are the intended first signing use case. Contract signing remains later and behind this gate.

## Related

- [legal/native-signing-process-counsel-review.md](../legal/native-signing-process-counsel-review.md) — signing **process** draft for counsel; **not** template approval
- [architecture/project-document-package.md](../architecture/project-document-package.md)
- [architecture/permit-and-approvals-report.md](../architecture/permit-and-approvals-report.md) — **FUTURE / NOT IMPLEMENTED**; not this Legal Content Gate
- [platform-governance.md](../platform-governance.md)
- [platform-constitution.md](../platform-constitution.md) — Articles 5, 8, 9
